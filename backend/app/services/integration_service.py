import httpx
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models.integration import Integration, IntegrationLog, IntegrationStatus, AuthenticationType
from ..models.field_mapping import FieldMapping
from ..models.lender import Lender
from .transformer import DataTransformer

logger = structlog.get_logger()


class IntegrationService:
    """Service for handling API integrations with lenders"""
    
    def __init__(self):
        self.transformer = DataTransformer()
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def submit_lead(
        self,
        db: AsyncSession,
        lender_id: int,
        lead_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit lead to a specific lender"""
        try:
            # Get lender and integration
            lender = await self._get_lender(db, lender_id)
            integration = await self._get_lead_integration(db, lender_id)
            
            if not integration or integration.status != IntegrationStatus.ACTIVE:
                raise ValueError(f"No active lead integration found for lender {lender_id}")
            
            # Get field mappings
            field_mappings = await self._get_field_mappings(db, lender_id)
            
            # Transform data according to mappings
            transformed_data = self.transformer.transform_data(lead_data, field_mappings)
            
            # Prepare request
            request_id = str(uuid.uuid4())
            request_data = await self._prepare_request(integration, transformed_data)
            
            # Make API call
            response = await self._make_api_call(integration, request_data)
            
            # Log the integration
            await self._log_integration(
                db, integration, request_id, request_data, response, lead_data.get('lead_id'), user_id
            )
            
            return {
                'success': True,
                'request_id': request_id,
                'lender_name': lender.name,
                'response': response,
                'transformed_data': transformed_data
            }
            
        except Exception as e:
            logger.error(
                "Lead submission failed",
                lender_id=lender_id,
                error=str(e),
                lead_data=lead_data
            )
            raise
    
    async def check_lead_status(
        self,
        db: AsyncSession,
        lender_id: int,
        lead_reference: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check lead status with a lender"""
        try:
            # Get status check integration
            integration = await self._get_status_integration(db, lender_id)
            
            if not integration or integration.status != IntegrationStatus.ACTIVE:
                raise ValueError(f"No active status integration found for lender {lender_id}")
            
            # Prepare status check request
            request_id = str(uuid.uuid4())
            request_data = await self._prepare_status_request(integration, lead_reference)
            
            # Make API call
            response = await self._make_api_call(integration, request_data)
            
            # Log the integration
            await self._log_integration(
                db, integration, request_id, request_data, response, lead_reference, user_id
            )
            
            return {
                'success': True,
                'request_id': request_id,
                'lead_reference': lead_reference,
                'response': response
            }
            
        except Exception as e:
            logger.error(
                "Status check failed",
                lender_id=lender_id,
                lead_reference=lead_reference,
                error=str(e)
            )
            raise
    
    async def test_integration(
        self,
        db: AsyncSession,
        integration_id: int,
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test an integration with sample data"""
        try:
            # Get integration
            result = await db.execute(
                select(Integration).where(Integration.id == integration_id)
            )
            integration = result.scalar_one_or_none()
            
            if not integration:
                raise ValueError(f"Integration {integration_id} not found")
            
            # Get field mappings
            field_mappings = await self._get_field_mappings(db, integration.lender_id)
            
            # Transform test data
            transformed_data = self.transformer.transform_data(test_data, field_mappings)
            
            # Prepare request
            request_data = await self._prepare_request(integration, transformed_data)
            
            # Make test API call
            response = await self._make_api_call(integration, request_data, is_test=True)
            
            return {
                'success': True,
                'integration_name': integration.name,
                'transformed_data': transformed_data,
                'response': response
            }
            
        except Exception as e:
            logger.error(
                "Integration test failed",
                integration_id=integration_id,
                error=str(e)
            )
            raise
    
    async def _get_lender(self, db: AsyncSession, lender_id: int) -> Lender:
        """Get lender by ID"""
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise ValueError(f"Lender {lender_id} not found")
        
        return lender
    
    async def _get_lead_integration(self, db: AsyncSession, lender_id: int) -> Optional[Integration]:
        """Get lead submission integration for lender"""
        result = await db.execute(
            select(Integration).where(
                Integration.lender_id == lender_id,
                Integration.integration_type == "lead_submission",
                Integration.status == IntegrationStatus.ACTIVE
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_status_integration(self, db: AsyncSession, lender_id: int) -> Optional[Integration]:
        """Get status check integration for lender"""
        result = await db.execute(
            select(Integration).where(
                Integration.lender_id == lender_id,
                Integration.integration_type == "status_check",
                Integration.status == IntegrationStatus.ACTIVE
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_field_mappings(self, db: AsyncSession, lender_id: int) -> List[FieldMapping]:
        """Get active field mappings for lender"""
        result = await db.execute(
            select(FieldMapping).where(
                FieldMapping.lender_id == lender_id,
                FieldMapping.is_active == True
            )
        )
        return result.scalars().all()
    
    async def _prepare_request(
        self, 
        integration: Integration, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare request data for API call"""
        request_data = {
            'data': data,
            'headers': integration.request_headers or {},
            'method': integration.http_method,
            'url': integration.api_endpoint
        }
        
        # Add authentication
        auth_headers = await self._get_auth_headers(integration)
        request_data['headers'].update(auth_headers)
        
        return request_data
    
    async def _prepare_status_request(
        self, 
        integration: Integration, 
        lead_reference: str
    ) -> Dict[str, Any]:
        """Prepare status check request"""
        request_data = {
            'data': {'lead_reference': lead_reference},
            'headers': integration.request_headers or {},
            'method': integration.http_method,
            'url': integration.api_endpoint
        }
        
        # Add authentication
        auth_headers = await self._get_auth_headers(integration)
        request_data['headers'].update(auth_headers)
        
        return request_data
    
    async def _get_auth_headers(self, integration: Integration) -> Dict[str, str]:
        """Get authentication headers based on integration config"""
        auth_config = integration.auth_config or {}
        
        if integration.auth_type == AuthenticationType.API_KEY:
            api_key = auth_config.get('api_key')
            header_name = auth_config.get('header_name', 'X-API-Key')
            return {header_name: api_key}
        
        elif integration.auth_type == AuthenticationType.BEARER_TOKEN:
            token = auth_config.get('token')
            return {'Authorization': f'Bearer {token}'}
        
        elif integration.auth_type == AuthenticationType.BASIC_AUTH:
            username = auth_config.get('username')
            password = auth_config.get('password')
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {'Authorization': f'Basic {credentials}'}
        
        return {}
    
    async def _make_api_call(
        self, 
        integration: Integration, 
        request_data: Dict[str, Any],
        is_test: bool = False
    ) -> Dict[str, Any]:
        """Make API call to lender"""
        start_time = datetime.now()
        
        try:
            # Prepare request
            method = request_data['method']
            url = request_data['url']
            headers = request_data['headers']
            data = request_data['data']
            
            # Make request
            if method.upper() == 'GET':
                response = await self.client.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = await self.client.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = await self.client.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'duration_ms': duration_ms,
                'success': response.status_code < 400
            }
            
            # Handle errors
            if not result['success']:
                result['error'] = self._extract_error_message(response_data, integration)
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'status_code': None,
                'headers': {},
                'data': None,
                'duration_ms': duration_ms,
                'success': False,
                'error': str(e)
            }
    
    def _extract_error_message(self, response_data: Any, integration: Integration) -> str:
        """Extract error message from response using error mapping"""
        error_mapping = integration.error_mapping or {}
        
        if isinstance(response_data, dict):
            # Try to extract error code/message from response
            error_code = response_data.get('error_code') or response_data.get('code')
            error_message = response_data.get('error_message') or response_data.get('message')
            
            if error_code and error_code in error_mapping:
                return error_mapping[error_code]
            elif error_message:
                return error_message
        
        return "Unknown error occurred"
    
    async def _log_integration(
        self,
        db: AsyncSession,
        integration: Integration,
        request_id: str,
        request_data: Dict[str, Any],
        response: Dict[str, Any],
        lead_id: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """Log integration request/response"""
        try:
            log_entry = IntegrationLog(
                integration_id=integration.id,
                request_id=request_id,
                request_data=request_data.get('data'),
                request_headers=request_data.get('headers'),
                response_status=response.get('status_code'),
                response_data=response.get('data'),
                response_headers=response.get('headers'),
                duration_ms=response.get('duration_ms'),
                error_message=response.get('error'),
                lead_id=lead_id,
                user_id=user_id
            )
            
            db.add(log_entry)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log integration: {e}")
            await db.rollback()
    
    async def get_integration_stats(
        self,
        db: AsyncSession,
        lender_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get integration statistics"""
        try:
            # Build query
            query = select(IntegrationLog)
            
            if lender_id:
                # Get logs for specific lender
                result = await db.execute(
                    select(IntegrationLog)
                    .join(Integration)
                    .where(Integration.lender_id == lender_id)
                )
            else:
                # Get all logs
                result = await db.execute(query)
            
            logs = result.scalars().all()
            
            # Calculate stats
            total_requests = len(logs)
            successful_requests = len([log for log in logs if log.response_status and log.response_status < 400])
            failed_requests = total_requests - successful_requests
            
            avg_response_time = 0
            if logs:
                response_times = [log.duration_ms for log in logs if log.duration_ms]
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
            
            return {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'avg_response_time_ms': avg_response_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get integration stats: {e}")
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0,
                'avg_response_time_ms': 0
            }
