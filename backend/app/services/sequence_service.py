import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models.integration import Integration, IntegrationSequence, IntegrationStatus
from ..models.field_mapping import FieldMapping
from .integration_service import IntegrationService
from .transformer import DataTransformer

logger = structlog.get_logger()


class SequenceService:
    """Service for handling multi-step API integration sequences"""
    
    def __init__(self):
        self.integration_service = IntegrationService()
        self.transformer = DataTransformer()
    
    async def execute_sequence(
        self,
        db: AsyncSession,
        sequence_id: int,
        initial_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a complete integration sequence"""
        try:
            # Get sequence and steps
            sequence = await self._get_sequence(db, sequence_id)
            steps = await self._get_sequence_steps(db, sequence_id)
            
            if not sequence or not sequence.is_active:
                raise ValueError(f"Sequence {sequence_id} not found or inactive")
            
            if not steps:
                raise ValueError(f"No steps found for sequence {sequence_id}")
            
            # Execute sequence based on mode
            if sequence.execution_mode == "sequential":
                return await self._execute_sequential(db, sequence, steps, initial_data, user_id)
            elif sequence.execution_mode == "parallel":
                return await self._execute_parallel(db, sequence, steps, initial_data, user_id)
            elif sequence.execution_mode == "conditional":
                return await self._execute_conditional(db, sequence, steps, initial_data, user_id)
            else:
                raise ValueError(f"Unsupported execution mode: {sequence.execution_mode}")
                
        except Exception as e:
            logger.error(
                "Sequence execution failed",
                sequence_id=sequence_id,
                error=str(e)
            )
            raise
    
    async def _execute_sequential(
        self,
        db: AsyncSession,
        sequence: IntegrationSequence,
        steps: List[Integration],
        initial_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute steps sequentially, passing data between steps"""
        results = {
            'sequence_id': sequence.id,
            'sequence_name': sequence.name,
            'execution_mode': 'sequential',
            'steps': [],
            'final_result': None,
            'success': True,
            'error': None
        }
        
        current_data = initial_data.copy()
        
        for step in steps:
            try:
                # Transform data for this step
                field_mappings = await self._get_field_mappings(db, step.lender_id)
                transformed_data = self.transformer.transform_data(current_data, field_mappings)
                
                # Add dependencies from previous steps
                if step.depends_on_fields:
                    for field_name, source_step in step.depends_on_fields.items():
                        if source_step in current_data:
                            transformed_data[field_name] = current_data[source_step]
                
                # Execute step
                step_result = await self.integration_service._make_api_call(
                    step, 
                    await self.integration_service._prepare_request(step, transformed_data)
                )
                
                # Extract output fields
                if step.output_fields and step_result.get('success'):
                    response_data = step_result.get('data', {})
                    for output_field in step.output_fields:
                        if output_field in response_data:
                            current_data[output_field] = response_data[output_field]
                
                # Log step result
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'input_data': transformed_data,
                    'output_data': step_result.get('data'),
                    'success': step_result.get('success'),
                    'error': step_result.get('error'),
                    'duration_ms': step_result.get('duration_ms')
                }
                results['steps'].append(step_log)
                
                # Check if we should stop on error
                if not step_result.get('success') and sequence.stop_on_error:
                    results['success'] = False
                    results['error'] = f"Step {step.name} failed: {step_result.get('error')}"
                    break
                
            except Exception as e:
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'input_data': transformed_data,
                    'success': False,
                    'error': str(e)
                }
                results['steps'].append(step_log)
                
                if sequence.stop_on_error:
                    results['success'] = False
                    results['error'] = f"Step {step.name} failed: {str(e)}"
                    break
        
        results['final_result'] = current_data
        return results
    
    async def _execute_parallel(
        self,
        db: AsyncSession,
        sequence: IntegrationSequence,
        steps: List[Integration],
        initial_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute steps in parallel"""
        results = {
            'sequence_id': sequence.id,
            'sequence_name': sequence.name,
            'execution_mode': 'parallel',
            'steps': [],
            'final_result': {},
            'success': True,
            'error': None
        }
        
        # Create tasks for parallel execution
        tasks = []
        for step in steps:
            task = self._execute_step_parallel(db, step, initial_data, user_id)
            tasks.append(task)
        
        # Execute all steps in parallel
        step_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, step_result in enumerate(step_results):
            step = steps[i]
            
            if isinstance(step_result, Exception):
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'success': False,
                    'error': str(step_result)
                }
                results['success'] = False
            else:
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'input_data': step_result.get('input_data'),
                    'output_data': step_result.get('output_data'),
                    'success': step_result.get('success'),
                    'error': step_result.get('error'),
                    'duration_ms': step_result.get('duration_ms')
                }
                
                # Collect output data
                if step_result.get('success') and step.output_fields:
                    response_data = step_result.get('output_data', {})
                    for output_field in step.output_fields:
                        if output_field in response_data:
                            results['final_result'][output_field] = response_data[output_field]
            
            results['steps'].append(step_log)
        
        return results
    
    async def _execute_conditional(
        self,
        db: AsyncSession,
        sequence: IntegrationSequence,
        steps: List[Integration],
        initial_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute steps based on conditions"""
        results = {
            'sequence_id': sequence.id,
            'sequence_name': sequence.name,
            'execution_mode': 'conditional',
            'steps': [],
            'final_result': None,
            'success': True,
            'error': None
        }
        
        current_data = initial_data.copy()
        condition_config = sequence.condition_config or {}
        
        for step in steps:
            try:
                # Check if step should be executed
                if not self._should_execute_step(step, current_data, condition_config):
                    step_log = {
                        'step_id': step.id,
                        'step_name': step.name,
                        'step_order': step.sequence_order,
                        'skipped': True,
                        'reason': 'Condition not met'
                    }
                    results['steps'].append(step_log)
                    continue
                
                # Execute step (similar to sequential)
                field_mappings = await self._get_field_mappings(db, step.lender_id)
                transformed_data = self.transformer.transform_data(current_data, field_mappings)
                
                if step.depends_on_fields:
                    for field_name, source_step in step.depends_on_fields.items():
                        if source_step in current_data:
                            transformed_data[field_name] = current_data[source_step]
                
                step_result = await self.integration_service._make_api_call(
                    step,
                    await self.integration_service._prepare_request(step, transformed_data)
                )
                
                if step.output_fields and step_result.get('success'):
                    response_data = step_result.get('data', {})
                    for output_field in step.output_fields:
                        if output_field in response_data:
                            current_data[output_field] = response_data[output_field]
                
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'input_data': transformed_data,
                    'output_data': step_result.get('data'),
                    'success': step_result.get('success'),
                    'error': step_result.get('error'),
                    'duration_ms': step_result.get('duration_ms')
                }
                results['steps'].append(step_log)
                
                if not step_result.get('success') and sequence.stop_on_error:
                    results['success'] = False
                    results['error'] = f"Step {step.name} failed: {step_result.get('error')}"
                    break
                
            except Exception as e:
                step_log = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'step_order': step.sequence_order,
                    'success': False,
                    'error': str(e)
                }
                results['steps'].append(step_log)
                
                if sequence.stop_on_error:
                    results['success'] = False
                    results['error'] = f"Step {step.name} failed: {str(e)}"
                    break
        
        results['final_result'] = current_data
        return results
    
    async def _execute_step_parallel(
        self,
        db: AsyncSession,
        step: Integration,
        initial_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a single step for parallel execution"""
        try:
            field_mappings = await self._get_field_mappings(db, step.lender_id)
            transformed_data = self.transformer.transform_data(initial_data, field_mappings)
            
            step_result = await self.integration_service._make_api_call(
                step,
                await self.integration_service._prepare_request(step, transformed_data)
            )
            
            return {
                'input_data': transformed_data,
                'output_data': step_result.get('data'),
                'success': step_result.get('success'),
                'error': step_result.get('error'),
                'duration_ms': step_result.get('duration_ms')
            }
            
        except Exception as e:
            return {
                'input_data': {},
                'output_data': None,
                'success': False,
                'error': str(e),
                'duration_ms': 0
            }
    
    def _should_execute_step(
        self,
        step: Integration,
        current_data: Dict[str, Any],
        condition_config: Dict[str, Any]
    ) -> bool:
        """Check if step should be executed based on conditions"""
        step_conditions = condition_config.get(str(step.id), {})
        
        if not step_conditions:
            return True  # No conditions, execute by default
        
        for field, condition in step_conditions.items():
            field_value = current_data.get(field)
            
            if condition.get('type') == 'equals':
                if field_value != condition.get('value'):
                    return False
            elif condition.get('type') == 'not_equals':
                if field_value == condition.get('value'):
                    return False
            elif condition.get('type') == 'exists':
                if field_value is None or field_value == '':
                    return False
            elif condition.get('type') == 'greater_than':
                if not (isinstance(field_value, (int, float)) and field_value > condition.get('value')):
                    return False
            elif condition.get('type') == 'less_than':
                if not (isinstance(field_value, (int, float)) and field_value < condition.get('value')):
                    return False
        
        return True
    
    async def _get_sequence(self, db: AsyncSession, sequence_id: int) -> Optional[IntegrationSequence]:
        """Get sequence by ID"""
        result = await db.execute(
            select(IntegrationSequence).where(IntegrationSequence.id == sequence_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_sequence_steps(self, db: AsyncSession, sequence_id: int) -> List[Integration]:
        """Get steps for a sequence ordered by sequence_order"""
        result = await db.execute(
            select(Integration)
            .where(
                Integration.parent_sequence_id == sequence_id,
                Integration.status != IntegrationStatus.INACTIVE
            )
            .order_by(Integration.sequence_order)
        )
        return result.scalars().all()
    
    async def _get_field_mappings(self, db: AsyncSession, lender_id: int) -> List[FieldMapping]:
        """Get active field mappings for lender"""
        result = await db.execute(
            select(FieldMapping).where(
                FieldMapping.lender_id == lender_id,
                FieldMapping.is_active == True
            )
        )
        return result.scalars().all()
    
    async def create_sample_sequence(
        self,
        db: AsyncSession,
        lender_id: int,
        sequence_type: str = "lead_submission"
    ) -> Dict[str, Any]:
        """Create a sample integration sequence"""
        sample_sequence = {
            'name': f'Sample {sequence_type.title()} Sequence',
            'description': f'Automated sequence for {sequence_type}',
            'sequence_type': sequence_type,
            'execution_mode': 'sequential',
            'lender_id': lender_id,
            'steps': [
                {
                    'name': 'Step 1: Validate Lead',
                    'integration_type': 'lead_submission',
                    'api_endpoint': 'https://api.lender.com/validate',
                    'http_method': 'POST',
                    'sequence_order': 1,
                    'auth_type': 'api_key',
                    'output_fields': ['validation_id', 'status']
                },
                {
                    'name': 'Step 2: Submit Lead',
                    'integration_type': 'lead_submission',
                    'api_endpoint': 'https://api.lender.com/submit',
                    'http_method': 'POST',
                    'sequence_order': 2,
                    'auth_type': 'api_key',
                    'depends_on_fields': {'validation_id': 'validation_id'},
                    'output_fields': ['lead_id', 'status']
                },
                {
                    'name': 'Step 3: Confirm Submission',
                    'integration_type': 'status_check',
                    'api_endpoint': 'https://api.lender.com/confirm',
                    'http_method': 'GET',
                    'sequence_order': 3,
                    'auth_type': 'api_key',
                    'depends_on_fields': {'lead_id': 'lead_id'},
                    'output_fields': ['confirmation_id', 'final_status']
                }
            ]
        }
        
        return sample_sequence
