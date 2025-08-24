import httpx
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from ..models.deployed_api import DeployedAPI, DeployedIntegration
from ..models.lender import Lender
from ..models.field_mapping import FieldMapping
from ..services.integration_runner import IntegrationRunner
from ..services.transformer import DataTransformer


class RuntimeExecutor:
    """Service for executing deployed APIs and integrations"""
    
    def __init__(self):
        self.integration_runner = IntegrationRunner()
        self.transformer = DataTransformer()
    
    async def execute_step(
        self, 
        db: AsyncSession, 
        step_id: str, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a deployed step API"""
        try:
            # 1. Look up step configuration from database
            deployed_api = await self._get_deployed_api(db, step_id)
            if not deployed_api:
                raise ValueError(f"Deployed API with ID {step_id} not found")
            
            if deployed_api.status != "active":
                raise ValueError(f"Deployed API {step_id} is not active (status: {deployed_api.status})")
            
            # 2. Extract step configuration
            step_config = deployed_api.step_config
            
            # 3. Get field mappings for this lender
            field_mappings = await self._get_field_mappings(db, deployed_api.lender_id)
            
            # 4. Apply field mappings and transformations
            processed_data = await self._apply_field_mappings(
                request_data, 
                step_config, 
                field_mappings
            )
            
            # 5. Execute the step based on its type
            result = await self._execute_step_logic(step_config, processed_data)
            
            # 6. Update execution metrics
            await self._update_execution_metrics(db, deployed_api.id, success=True)
            
            return {
                "success": True,
                "step_id": step_id,
                "step_name": deployed_api.step_name,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Update error metrics only if deployed_api exists
            if 'deployed_api' in locals() and deployed_api is not None:
                try:
                    await self._update_execution_metrics(db, deployed_api.id, success=False, error=str(e))
                except Exception as metric_error:
                    # Log metric update error but don't fail the main execution
                    print(f"Failed to update execution metrics: {metric_error}")
            
            return {
                "success": False,
                "step_id": step_id,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }
    
    async def execute_integration(
        self, 
        db: AsyncSession, 
        integration_id: str, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a deployed integration sequence"""
        try:
            # 1. Look up integration configuration from database
            deployed_integration = await self._get_deployed_integration(db, integration_id)
            if not deployed_integration:
                raise ValueError(f"Deployed integration with ID {integration_id} not found")
            
            if deployed_integration.status != "active":
                raise ValueError(f"Deployed integration {integration_id} is not active (status: {deployed_integration.status})")
            
            # 2. Extract configuration
            sequence_config = deployed_integration.sequence_config
            field_mappings = deployed_integration.field_mappings
            
            # 3. Execute the integration sequence using existing IntegrationRunner
            result = await self.integration_runner.run(
                db=db,
                lender_id=deployed_integration.lender_id,
                input_payload=request_data,
                mode="production"
            )
            
            # 4. Update execution metrics
            await self._update_integration_execution_metrics(db, deployed_integration.id, success=True)
            
            return {
                "success": True,
                "integration_id": integration_id,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Update error metrics only if deployed_integration exists
            if 'deployed_integration' in locals() and deployed_integration is not None:
                try:
                    await self._update_integration_execution_metrics(db, deployed_integration.id, success=False, error=str(e))
                except Exception as metric_error:
                    # Log metric update error but don't fail the main execution
                    print(f"Failed to update integration execution metrics: {metric_error}")
            
            return {
                "success": False,
                "integration_id": integration_id,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }
    
    async def _get_deployed_api(self, db: AsyncSession, step_id: str) -> Optional[DeployedAPI]:
        """Get deployed API configuration from database"""
        result = await db.execute(
            select(DeployedAPI).where(DeployedAPI.id == step_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_deployed_integration(self, db: AsyncSession, integration_id: str) -> Optional[DeployedIntegration]:
        """Get deployed integration configuration from database"""
        result = await db.execute(
            select(DeployedIntegration).where(DeployedIntegration.id == integration_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_field_mappings(self, db: AsyncSession, lender_id: int) -> List[FieldMapping]:
        """Get field mappings for a lender"""
        result = await db.execute(
            select(FieldMapping).where(
                FieldMapping.lender_id == lender_id,
                FieldMapping.is_active == True
            )
        )
        return list(result.scalars().all())
    
    async def _apply_field_mappings(
        self, 
        request_data: Dict[str, Any], 
        step_config: Dict[str, Any], 
        field_mappings: List[FieldMapping]
    ) -> Dict[str, Any]:
        """Apply field mappings to request data"""
        if not field_mappings:
            return request_data
        
        processed_data = request_data.copy()
        
        for mapping in field_mappings:
            if mapping.is_active:
                # Apply transformation based on mapping configuration
                source_value = self._get_nested_value(processed_data, mapping.source_field)
                if source_value is not None:
                    transformed_value = self.transformer.transform_data(
                        source_value, 
                        mapping.transformation_type, 
                        mapping.transformation_config
                    )
                    self._set_nested_value(processed_data, mapping.target_field, transformed_value)
        
        return processed_data
    
    async def _execute_step_logic(self, step_config: Dict[str, Any], processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual step logic based on step configuration"""
        step_type = step_config.get("integration_type", "LEAD_SUBMISSION")
        
        if step_type == "LEAD_SUBMISSION":
            return await self._execute_http_request(step_config, processed_data)
        elif step_type == "DATA_TRANSFORM":
            return await self._execute_data_transform(step_config, processed_data)
        else:
            # Default to HTTP request
            return await self._execute_http_request(step_config, processed_data)
    
    async def _execute_http_request(self, step_config: Dict[str, Any], processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request step"""
        try:
            # Extract HTTP configuration
            api_endpoint = step_config.get("api_endpoint")
            http_method = step_config.get("http_method", "POST").upper()
            headers = step_config.get("request_headers", {})
            auth_config = step_config.get("auth_config", {})
            timeout = step_config.get("timeout_seconds", 30)
            
            # Prepare request data
            request_data = processed_data
            if step_config.get("request_schema"):
                # Merge with request schema if provided
                request_data = {**step_config.get("request_schema", {}), **processed_data}
            
            # Add authentication headers
            auth_headers = await self._get_auth_headers(auth_config)
            headers.update(auth_headers)
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=timeout) as client:
                if http_method == "GET":
                    response = await client.get(api_endpoint, headers=headers, params=request_data)
                elif http_method == "POST":
                    response = await client.post(api_endpoint, headers=headers, json=request_data)
                elif http_method == "PUT":
                    response = await client.put(api_endpoint, headers=headers, json=request_data)
                elif http_method == "PATCH":
                    response = await client.patch(api_endpoint, headers=headers, json=request_data)
                elif http_method == "DELETE":
                    response = await client.delete(api_endpoint, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {http_method}")
                
                # Process response
                response_data = {}
                if response.headers.get("content-type", "").startswith("application/json"):
                    response_data = response.json()
                else:
                    response_data = {"content": response.text}
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "success": response.status_code < 400
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def _execute_data_transform(self, step_config: Dict[str, Any], processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data transformation step"""
        try:
            # Extract transformation configuration
            transformation_config = step_config.get("request_schema", {})
            
            # Apply transformation
            transformed_data = self.transformer.transform_data(
                processed_data,
                transformation_config.get("type", "passthrough"),
                transformation_config
            )
            
            return {
                "success": True,
                "transformed_data": transformed_data,
                "original_data": processed_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_auth_headers(self, auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers based on auth configuration"""
        headers = {}
        auth_type = auth_config.get("auth_type", "NONE")
        
        if auth_type == "BEARER_TOKEN":
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "API_KEY":
            key_name = auth_config.get("key_name", "X-API-Key")
            key_value = auth_config.get("key_value")
            if key_value:
                headers[key_name] = key_value
        elif auth_type == "BASIC_AUTH":
            username = auth_config.get("username")
            password = auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    async def _update_execution_metrics(
        self, 
        db: AsyncSession, 
        step_id: str, 
        success: bool, 
        error: str = None
    ):
        """Update execution metrics for a deployed API"""
        update_data = {
            "last_executed_at": datetime.utcnow(),
            "execution_count": DeployedAPI.execution_count + 1
        }
        
        if success:
            update_data["error_count"] = DeployedAPI.error_count
        else:
            update_data["error_count"] = DeployedAPI.error_count + 1
            update_data["last_error"] = error
        
        await db.execute(
            update(DeployedAPI)
            .where(DeployedAPI.id == step_id)
            .values(**update_data)
        )
        await db.commit()
    
    async def _update_integration_execution_metrics(
        self, 
        db: AsyncSession, 
        integration_id: str, 
        success: bool, 
        error: str = None
    ):
        """Update execution metrics for a deployed integration"""
        update_data = {
            "last_executed_at": datetime.utcnow(),
            "execution_count": DeployedIntegration.execution_count + 1
        }
        
        if success:
            update_data["error_count"] = DeployedIntegration.error_count
        else:
            update_data["error_count"] = DeployedIntegration.error_count + 1
            update_data["last_error"] = error
        
        await db.execute(
            update(DeployedIntegration)
            .where(DeployedIntegration.id == integration_id)
            .values(**update_data)
        )
        await db.commit()
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set nested value in dictionary using dot notation"""
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
