from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import structlog

from ....core.database import get_db
from ....models.lender import Lender
from ....schemas.lender import LenderCreate, LenderUpdate, LenderResponse, LenderList
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo, MasterSourceFieldCreate, MasterSourceFieldUpdate, MasterSourceFieldResponse, CustomTargetFieldCreate, CustomTargetFieldUpdate, CustomTargetFieldResponse
from ....models.field_mapping import FieldMapping, TransformationType, DataType, MasterSourceField, CustomTargetField
from ....models.integration import IntegrationSequence, Integration, IntegrationType, AuthenticationType, IntegrationLog, IntegrationStatus
from ....models.deployed_api import DeployedIntegration
from ....services.integration_runner import IntegrationRunner
from .auth import get_current_user
from sqlalchemy import update

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ResponseModel[LenderResponse], status_code=status.HTTP_201_CREATED)
async def create_lender(
    lender_data: LenderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lender"""
    try:
        # Check if lender with same name already exists
        existing_lender = await db.execute(
            select(Lender).where(Lender.name == lender_data.name)
        )
        if existing_lender.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lender with name '{lender_data.name}' already exists"
            )
        
        # Create new lender - convert HttpUrl fields to strings
        lender_dict = lender_data.model_dump()
        
        # Convert HttpUrl fields to strings for SQLAlchemy
        if lender_dict.get('base_url'):
            lender_dict['base_url'] = str(lender_dict['base_url'])
        if lender_dict.get('openapi_spec_url'):
            lender_dict['openapi_spec_url'] = str(lender_dict['openapi_spec_url'])
        if lender_dict.get('documentation_url'):
            lender_dict['documentation_url'] = str(lender_dict['documentation_url'])
        if lender_dict.get('support_url'):
            lender_dict['support_url'] = str(lender_dict['support_url'])
        
        lender = Lender(**lender_dict)
        db.add(lender)
        await db.commit()
        await db.refresh(lender)
        
        logger.info("Lender created successfully", lender_id=lender.id, lender_name=lender.name)
        
        return ResponseModel(
            message="Lender created successfully",
            data=LenderResponse.model_validate(lender)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create lender", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lender"
        )


@router.get("/", response_model=ResponseModel[LenderList])
async def get_lenders(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by lender name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    auth_type: Optional[str] = Query(None, description="Filter by authentication type"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of lenders with optional filtering"""
    try:
        # Build query
        query = select(Lender)
        
        # Apply filters
        if search:
            query = query.where(
                Lender.name.ilike(f"%{search}%") | 
                Lender.description.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.where(Lender.is_active == is_active)
        
        if auth_type:
            query = query.where(Lender.auth_type == auth_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(Lender, pagination.sort_by, Lender.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(Lender.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        lenders = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + pagination.size - 1) // pagination.size
        pagination_info = PaginationInfo(
            page=pagination.page,
            size=pagination.size,
            total=total,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )
        
        return ResponseModel(
            message="Lenders retrieved successfully",
            data=LenderList(
                lenders=[LenderResponse.model_validate(lender) for lender in lenders],
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pages
            ),
            pagination=pagination_info
        )
        
    except Exception as e:
        logger.error("Failed to retrieve lenders", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lenders"
        )


@router.get("/{lender_id}", response_model=ResponseModel[LenderResponse])
async def get_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific lender by ID"""
    try:
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        return ResponseModel(
            message="Lender retrieved successfully",
            data=LenderResponse.model_validate(lender)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve lender", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lender"
        )


@router.put("/{lender_id}", response_model=ResponseModel[LenderResponse])
async def update_lender(
    lender_id: int,
    lender_data: LenderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a lender"""
    try:
        # Get existing lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        # Check for name conflict if name is being updated
        if lender_data.name and lender_data.name != lender.name:
            existing_lender = await db.execute(
                select(Lender).where(Lender.name == lender_data.name)
            )
            if existing_lender.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Lender with name '{lender_data.name}' already exists"
                )
        
        # Update lender fields
        update_data = lender_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lender, field, value)
        
        await db.commit()
        await db.refresh(lender)
        
        logger.info("Lender updated successfully", lender_id=lender.id, lender_name=lender.name)
        
        return ResponseModel(
            message="Lender updated successfully",
            data=LenderResponse.model_validate(lender)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update lender", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lender"
        )


@router.delete("/{lender_id}", response_model=ResponseModel)
async def delete_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a lender"""
    try:
        # Get existing lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        # Check if lender has associated configurations
        if lender.api_configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete lender with associated API configurations"
            )
        
        # Delete lender
        await db.delete(lender)
        await db.commit()
        
        logger.info("Lender deleted successfully", lender_id=lender_id, lender_name=lender.name)
        
        return ResponseModel(
            message="Lender deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete lender", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lender"
        )


@router.patch("/{lender_id}/toggle-status", response_model=ResponseModel[LenderResponse])
async def toggle_lender_status(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle lender active status"""
    try:
        # Get existing lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        # Toggle status
        lender.is_active = not lender.is_active
        await db.commit()
        await db.refresh(lender)
        
        status_text = "activated" if lender.is_active else "deactivated"
        logger.info(f"Lender {status_text}", lender_id=lender.id, lender_name=lender.name)
        
        return ResponseModel(
            message=f"Lender {status_text} successfully",
            data=LenderResponse.model_validate(lender)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to toggle lender status", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle lender status"
        )


# -----------------------------
# Field Mappings for a Lender
# -----------------------------

@router.get("/{lender_id}/field-mappings", response_model=ResponseModel)
async def get_field_mappings(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(FieldMapping).where(FieldMapping.lender_id == lender_id).order_by(FieldMapping.id.asc())
        )
        mappings = result.scalars().all()
        return ResponseModel(
            message="Field mappings retrieved successfully",
            data=[{
                "id": m.id,
                "name": m.name,
                "source_field": m.source_field,
                "target_field": m.target_field,
                "transformation_type": m.transformation_type.value if m.transformation_type else "none",
                "transformation_config": m.transformation_config,
                "is_required": m.is_required,
                "is_active": m.is_active,
                "validation_rules": m.validation_rules,
                "default_value": m.default_value,
                "fallback_value": m.fallback_value,
            } for m in mappings]
        )
    except Exception as e:
        logger.error("Failed to retrieve field mappings", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve field mappings")


@router.get("/{lender_id}/api-response-fields", response_model=ResponseModel)
async def get_api_response_fields(
    lender_id: int,
    limit: int = Query(50, ge=1, le=200, description="Number of recent API responses to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get unique fields from saved API responses for field mapping"""
    try:
        from ....models.integration import IntegrationLog, Integration
        
        # Get recent successful API responses for this lender
        result = await db.execute(
            select(IntegrationLog.response_data)
            .join(Integration)
            .where(
                Integration.lender_id == lender_id,
                IntegrationLog.response_status < 400,  # Only successful responses
                IntegrationLog.response_data.isnot(None)
            )
            .order_by(IntegrationLog.created_at.desc())
            .limit(limit)
        )
        
        response_logs = result.scalars().all()
        
        if not response_logs:
            return ResponseModel(
                message="No API response data found for this lender",
                data={"fields": [], "total_responses": 0}
            )
        
        # Extract unique fields from all responses
        all_fields = set()
        field_counts = {}
        
        for response_data in response_logs:
            if isinstance(response_data, dict):
                _extract_fields_recursive(response_data, "", all_fields, field_counts)
        
        # Convert to sorted list with field counts
        field_list = [
            {
                "field": field,
                "count": field_counts.get(field, 0),
                "frequency": (field_counts.get(field, 0) / len(response_logs)) * 100
            }
            for field in sorted(all_fields)
        ]
        
        return ResponseModel(
            message="API response fields retrieved successfully",
            data={
                "fields": field_list,
                "total_responses": len(response_logs),
                "unique_fields_count": len(all_fields)
            }
        )
        
    except Exception as e:
        logger.error("Failed to retrieve API response fields", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve API response fields")


@router.get("/{lender_id}/request-fields", response_model=ResponseModel)
async def get_request_fields(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get unique fields from step request configurations for field mapping"""
    try:
        from ....models.integration import Integration, IntegrationSequence
        
        # Get all integration steps for this lender
        result = await db.execute(
            select(Integration)
            .where(
                Integration.lender_id == lender_id,
                Integration.is_sequence_step == True
            )
            .order_by(Integration.sequence_order.asc())
        )
        
        integrations = result.scalars().all()
        
        if not integrations:
            return ResponseModel(
                message="No integration steps found for this lender",
                data={"fields": [], "total_steps": 0}
            )
        
        # Extract unique fields from request schemas and templates
        all_fields = set()
        field_counts = {}
        field_sources = {}  # Track which step each field comes from
        
        for integration in integrations:
            step_name = integration.name
            request_schema = integration.request_schema or {}
            
            # Extract fields from request_schema template
            if isinstance(request_schema, dict):
                template = request_schema.get("template", {})
                if isinstance(template, dict):
                    _extract_fields_recursive(template, "", all_fields, field_counts, step_name, field_sources)
                
                # Extract fields from query_params
                query_params = request_schema.get("query_params", {})
                if isinstance(query_params, dict):
                    _extract_fields_recursive(query_params, "", all_fields, field_counts, step_name, field_sources)
            
            # Extract fields from depends_on_fields
            depends_on_fields = integration.depends_on_fields or {}
            if isinstance(depends_on_fields, dict):
                for field in depends_on_fields.values():
                    if field:
                        all_fields.add(field)
                        field_counts[field] = field_counts.get(field, 0) + 1
                        if field not in field_sources:
                            field_sources[field] = []
                        field_sources[field].append(f"{step_name} (dependency)")
        
        # Convert to sorted list with field counts and sources
        field_list = [
            {
                "field": field,
                "count": field_counts.get(field, 0),
                "frequency": (field_counts.get(field, 0) / len(integrations)) * 100,
                "sources": field_sources.get(field, [])
            }
            for field in sorted(all_fields)
        ]
        
        return ResponseModel(
            message="Request fields retrieved successfully",
            data={
                "fields": field_list,
                "total_steps": len(integrations),
                "unique_fields_count": len(all_fields)
            }
        )
        
    except Exception as e:
        logger.error("Failed to retrieve request fields", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve request fields")


@router.get("/{lender_id}/request-fields-test", response_model=ResponseModel)
async def get_request_fields_test(lender_id: int):
    """Test endpoint for request fields without database dependency"""
    return ResponseModel(
        message="Request fields test endpoint working",
        data={
            "fields": [
                {
                    "field": "customer_name",
                    "count": 1,
                    "frequency": 100.0,
                    "sources": ["Sample Step 1"]
                },
                {
                    "field": "email_address", 
                    "count": 1,
                    "frequency": 100.0,
                    "sources": ["Sample Step 1"]
                }
            ],
            "total_steps": 1,
            "unique_fields_count": 2
        }
    )


@router.get("/{lender_id}/simple-test")
async def simple_test(lender_id: int):
    """Simple test endpoint"""
    return {"message": "Simple test working", "lender_id": lender_id}


@router.get("/{lender_id}/db-test")
async def db_test(lender_id: int, db: AsyncSession = Depends(get_db)):
    """Test database connection"""
    try:
        # Simple query to test database connection
        result = await db.execute(select(Lender).where(Lender.id == lender_id))
        lender = result.scalar_one_or_none()
        
        if lender:
            return {"message": "Database connection working", "lender_name": lender.name}
        else:
            return {"message": "Database connection working", "lender_not_found": True}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}


def _extract_fields_recursive(data: dict, prefix: str, all_fields: set, field_counts: dict, step_name: str = "", field_sources: dict = None):
    """Recursively extract field names from nested JSON data"""
    for key, value in data.items():
        field_path = f"{prefix}.{key}" if prefix else key
        all_fields.add(field_path)
        field_counts[field_path] = field_counts.get(field_path, 0) + 1
        
        # Track source if provided
        if field_sources is not None:
            if field_path not in field_sources:
                field_sources[field_path] = []
            field_sources[field_path].append(step_name)
        
        if isinstance(value, dict):
            _extract_fields_recursive(value, field_path, all_fields, field_counts, step_name, field_sources)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Handle array of objects
            for item in value[:3]:  # Limit to first 3 items to avoid excessive recursion
                if isinstance(item, dict):
                    _extract_fields_recursive(item, f"{field_path}[]", all_fields, field_counts, step_name, field_sources)


@router.post("/{lender_id}/field-mappings", response_model=ResponseModel)
async def save_field_mappings(
    lender_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    try:
        mappings = payload.get("mappings", [])
        # Replace strategy: delete old, insert new
        await db.execute(delete(FieldMapping).where(FieldMapping.lender_id == lender_id))
        for item in mappings:
            fm = FieldMapping(
                lender_id=lender_id,
                name=item.get("name") or item.get("source_field") or "Mapping",
                source_field=item.get("source_field", ""),
                target_field=item.get("target_field", ""),
                transformation_type=TransformationType(item.get("transformation_type", "none")),
                transformation_config=item.get("transformation_config"),
                is_required=bool(item.get("is_required", False)),
                is_active=bool(item.get("is_active", True)),
                validation_rules=item.get("validation_rules"),
                default_value=item.get("default_value"),
                fallback_value=item.get("fallback_value"),
            )
            db.add(fm)
        await db.commit()
        return ResponseModel(message="Field mappings saved successfully")
    except Exception as e:
        await db.rollback()
        logger.error("Failed to save field mappings", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to save field mappings")


# -------------------------------------
# Integration Sequences for a Lender (Multiple sequences support)
# -------------------------------------

@router.get("/{lender_id}/integration-sequences", response_model=ResponseModel)
async def get_integration_sequences(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all integration sequences for a lender"""
    try:
        # Get all sequences for the lender
        seq_result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.lender_id == lender_id
            ).order_by(IntegrationSequence.created_at.desc())
        )
        sequences = seq_result.scalars().all()
        
        # For each sequence, get its steps
        sequences_with_steps = []
        for sequence in sequences:
            steps_result = await db.execute(
                select(Integration).where(
                    Integration.parent_sequence_id == sequence.id,
                    Integration.status != IntegrationStatus.INACTIVE
                ).order_by(Integration.sequence_order.asc())
            )
            steps = steps_result.scalars().all()
            
            sequences_with_steps.append({
                "id": sequence.id,
                "name": sequence.name,
                "description": sequence.description,
                "sequence_type": sequence.sequence_type,
                "execution_mode": sequence.execution_mode,
                "condition_config": sequence.condition_config,
                "stop_on_error": sequence.stop_on_error,
                "retry_failed_steps": sequence.retry_failed_steps,
                "is_active": sequence.is_active,
                "created_at": sequence.created_at,
                "updated_at": sequence.updated_at,
                "steps": [
                    {
                        "id": step.id,
                        "name": step.name,
                        "integration_type": step.integration_type,
                        "api_endpoint": step.api_endpoint,
                        "http_method": step.http_method,
                        "sequence_order": step.sequence_order,
                        "auth_type": step.auth_type,
                        "auth_config": step.auth_config,
                        "depends_on_fields": step.depends_on_fields,
                        "output_fields": step.output_fields,
                        "is_active": step.status == IntegrationStatus.ACTIVE,
                        "timeout_seconds": step.timeout_seconds,
                        "retry_count": step.retry_count,
                        "retry_delay_seconds": step.retry_delay_seconds,
                        "rate_limit_per_minute": step.rate_limit_per_minute,
                        "request_headers": step.request_headers,
                        "request_schema": step.request_schema
                    } for step in steps
                ]
            })
        
        return ResponseModel(
            message=f"Retrieved {len(sequences_with_steps)} integration sequences for lender {lender_id}",
            data=sequences_with_steps
        )
    except Exception as e:
        logger.error(f"Failed to retrieve integration sequences for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integration sequences")

@router.get("/{lender_id}/integration-sequences/{sequence_id}", response_model=ResponseModel)
async def get_integration_sequence(
    lender_id: int,
    sequence_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific integration sequence for a lender"""
    try:
        # Get the specific sequence
        seq_result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.id == sequence_id,
                IntegrationSequence.lender_id == lender_id
            )
        )
        sequence = seq_result.scalar_one_or_none()
        
        if not sequence:
            raise HTTPException(status_code=404, detail="Integration sequence not found")
        
        # Get steps for this sequence
        steps_result = await db.execute(
            select(Integration).where(
                Integration.parent_sequence_id == sequence.id,
                Integration.status != IntegrationStatus.INACTIVE
            ).order_by(Integration.sequence_order.asc())
        )
        steps = steps_result.scalars().all()
        
        sequence_data = {
            "id": sequence.id,
            "name": sequence.name,
            "description": sequence.description,
            "sequence_type": sequence.sequence_type,
            "execution_mode": sequence.execution_mode,
            "condition_config": sequence.condition_config,
            "stop_on_error": sequence.stop_on_error,
            "retry_failed_steps": sequence.retry_failed_steps,
            "is_active": sequence.is_active,
            "created_at": sequence.created_at,
            "updated_at": sequence.updated_at,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "integration_type": step.integration_type,
                    "api_endpoint": step.api_endpoint,
                    "http_method": step.http_method,
                    "sequence_order": step.sequence_order,
                    "auth_type": step.auth_type,
                    "auth_config": step.auth_config,
                    "depends_on_fields": step.depends_on_fields,
                    "output_fields": step.output_fields,
                    "is_active": step.status == IntegrationStatus.ACTIVE,
                    "timeout_seconds": step.timeout_seconds,
                    "retry_count": step.retry_count,
                    "retry_delay_seconds": step.retry_delay_seconds,
                    "rate_limit_per_minute": step.rate_limit_per_minute,
                    "request_headers": step.request_headers,
                    "request_schema": step.request_schema
                } for step in steps
            ]
        }
        
        return ResponseModel(
            message=f"Retrieved integration sequence {sequence.name} for lender {lender_id}",
            data=sequence_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve integration sequence {sequence_id} for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integration sequence")

@router.post("/{lender_id}/integration-sequences", response_model=ResponseModel)
async def create_integration_sequence(
    lender_id: int,
    sequence_payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new integration sequence for a lender"""
    try:
        # Basic payload validation
        name = (sequence_payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Sequence name is required")

        steps = sequence_payload.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise HTTPException(status_code=400, detail="At least one step is required")

        execution_mode = sequence_payload.get("execution_mode", "sequential")
        if execution_mode not in ("sequential", "parallel", "conditional"):
            raise HTTPException(status_code=400, detail="Invalid execution_mode")

        # Create new sequence
        sequence = IntegrationSequence(
            lender_id=lender_id,
            name=name,
            description=sequence_payload.get("description"),
            sequence_type=sequence_payload.get("sequence_type", "lead_submission"),
            execution_mode=execution_mode,
            condition_config=sequence_payload.get("condition_config"),
            stop_on_error=bool(sequence_payload.get("stop_on_error", True)),
            retry_failed_steps=bool(sequence_payload.get("retry_failed_steps", False)),
            is_active=True,
        )
        
        db.add(sequence)
        await db.flush()  # Get the sequence ID
        
        # Create integration steps
        for index, step in enumerate(steps):
            integration = Integration(
                lender_id=lender_id,
                parent_sequence_id=sequence.id,
                name=step.get("name", f"Step {index + 1}"),
                integration_type=step.get("integration_type", "LEAD_SUBMISSION"),
                api_endpoint=step.get("api_endpoint", ""),
                http_method=step.get("http_method", "POST"),
                sequence_order=step.get("sequence_order", index + 1),
                auth_type=step.get("auth_type", "NONE"),
                auth_config=step.get("auth_config", {}),
                depends_on_fields=step.get("depends_on_fields", {}),
                output_fields=step.get("output_fields", []),
                is_sequence_step=True,
                status=IntegrationStatus.ACTIVE if step.get("is_active", True) else IntegrationStatus.INACTIVE,
                timeout_seconds=step.get("timeout_seconds"),
                retry_count=step.get("retry_count"),
                retry_delay_seconds=step.get("retry_delay_seconds"),
                rate_limit_per_minute=step.get("rate_limit_per_minute"),
                request_headers=step.get("request_headers"),
                request_schema=step.get("request_schema")
            )
            db.add(integration)
        
        await db.commit()
        
        return ResponseModel(
            message=f"Successfully created integration sequence '{name}' for lender {lender_id}",
            data={"sequence_id": sequence.id, "name": sequence.name}
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create integration sequence for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create integration sequence")

@router.put("/{lender_id}/integration-sequences/{sequence_id}", response_model=ResponseModel)
async def update_integration_sequence(
    lender_id: int,
    sequence_id: int,
    sequence_payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing integration sequence for a lender"""
    try:
        # Get the existing sequence
        seq_result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.id == sequence_id,
                IntegrationSequence.lender_id == lender_id
            )
        )
        sequence = seq_result.scalar_one_or_none()
        
        if not sequence:
            raise HTTPException(status_code=404, detail="Integration sequence not found")

        # Basic payload validation
        name = (sequence_payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Sequence name is required")

        steps = sequence_payload.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise HTTPException(status_code=400, detail="At least one step is required")

        execution_mode = sequence_payload.get("execution_mode", "sequential")
        if execution_mode not in ("sequential", "parallel", "conditional"):
            raise HTTPException(status_code=400, detail="Invalid execution_mode")

        # Update sequence
        sequence.name = name
        sequence.description = sequence_payload.get("description")
        sequence.sequence_type = sequence_payload.get("sequence_type", sequence.sequence_type)
        sequence.execution_mode = execution_mode
        sequence.condition_config = sequence_payload.get("condition_config")
        sequence.stop_on_error = bool(sequence_payload.get("stop_on_error", sequence.stop_on_error))
        sequence.retry_failed_steps = bool(sequence_payload.get("retry_failed_steps", sequence.retry_failed_steps))
        sequence.is_active = bool(sequence_payload.get("is_active", sequence.is_active))

        # Get existing integrations for this sequence
        existing_integrations_result = await db.execute(
            select(Integration).where(Integration.parent_sequence_id == sequence.id)
        )
        existing_integrations = {intg.id: intg for intg in existing_integrations_result.scalars().all()}
        
        # Track which integrations we've processed
        processed_integration_ids = set()
        
        # Update or create steps
        for index, step in enumerate(steps):
            step_id = step.get("id")
            
            if step_id and step_id in existing_integrations:
                # Update existing step
                integration = existing_integrations[step_id]
                integration.name = step.get("name", f"Step {index + 1}")
                integration.integration_type = step.get("integration_type", "LEAD_SUBMISSION")
                integration.api_endpoint = step.get("api_endpoint", "")
                integration.http_method = step.get("http_method", "POST")
                integration.sequence_order = step.get("sequence_order", index + 1)
                integration.auth_type = step.get("auth_type", "NONE")
                integration.auth_config = step.get("auth_config", {})
                integration.depends_on_fields = step.get("depends_on_fields", {})
                integration.output_fields = step.get("output_fields", [])
                integration.is_active = step.get("is_active", True)
                integration.timeout_seconds = step.get("timeout_seconds")
                integration.retry_count = step.get("retry_count")
                integration.retry_delay_seconds = step.get("retry_delay_seconds")
                integration.rate_limit_per_minute = step.get("rate_limit_per_minute")
                integration.request_headers = step.get("request_headers")
                integration.request_schema = step.get("request_schema")
                
                processed_integration_ids.add(step_id)
            else:
                # Create new step
                integration = Integration(
                    lender_id=lender_id,
                    parent_sequence_id=sequence.id,
                    name=step.get("name", f"Step {index + 1}"),
                    integration_type=step.get("integration_type", "LEAD_SUBMISSION"),
                    api_endpoint=step.get("api_endpoint", ""),
                    http_method=step.get("http_method", "POST"),
                    sequence_order=step.get("sequence_order", index + 1),
                    auth_type=step.get("auth_type", "NONE"),
                    auth_config=step.get("auth_config", {}),
                    depends_on_fields=step.get("depends_on_fields", {}),
                    output_fields=step.get("output_fields", []),
                    is_sequence_step=True,
                    is_active=step.get("is_active", True),
                    timeout_seconds=step.get("timeout_seconds"),
                    retry_count=step.get("retry_count"),
                    retry_delay_seconds=step.get("retry_delay_seconds"),
                    rate_limit_per_minute=step.get("rate_limit_per_minute"),
                    request_headers=step.get("request_headers"),
                    request_schema=step.get("request_schema")
                )
                db.add(integration)
        
        # Deactivate steps that are no longer in the sequence
        for integration_id, integration in existing_integrations.items():
            if integration_id not in processed_integration_ids:
                integration.is_active = False
        
        await db.commit()
        
        return ResponseModel(
            message=f"Successfully updated integration sequence '{name}' for lender {lender_id}",
            data={"sequence_id": sequence.id, "name": sequence.name}
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update integration sequence {sequence_id} for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update integration sequence")

@router.delete("/{lender_id}/integration-sequences/{sequence_id}", response_model=ResponseModel)
async def delete_integration_sequence(
    lender_id: int,
    sequence_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an integration sequence for a lender"""
    try:
        # Get the sequence
        seq_result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.id == sequence_id,
                IntegrationSequence.lender_id == lender_id
            )
        )
        sequence = seq_result.scalar_one_or_none()
        
        if not sequence:
            raise HTTPException(status_code=404, detail="Integration sequence not found")

        # Get all integrations (steps) for this sequence
        integrations_result = await db.execute(
            select(Integration).where(Integration.parent_sequence_id == sequence.id)
        )
        integrations = integrations_result.scalars().all()
        
        # Delete all integration logs for these integrations
        for integration in integrations:
            await db.execute(
                delete(IntegrationLog).where(IntegrationLog.integration_id == integration.id)
            )
        
        # Delete all integrations (steps) for this sequence
        await db.execute(
            delete(Integration).where(Integration.parent_sequence_id == sequence.id)
        )
        
        # Delete deployed integrations that reference this sequence
        # Note: This is a soft delete to preserve deployment history
        deployed_integrations_result = await db.execute(
            select(DeployedIntegration).where(DeployedIntegration.lender_id == lender_id)
        )
        deployed_integrations = deployed_integrations_result.scalars().all()
        
        for deployed in deployed_integrations:
            try:
                # Check if this deployment references the sequence being deleted
                sequence_config = deployed.sequence_config
                if sequence_config and sequence_config.get('id') == sequence_id:
                    # Mark as inactive but don't delete to preserve history
                    deployed.status = 'inactive'
            except Exception:
                # If there's an error parsing the config, mark as inactive
                deployed.status = 'inactive'
        
        # Finally, delete the sequence itself
        await db.delete(sequence)
        
        await db.commit()
        
        logger.info(f"Successfully deleted integration sequence {sequence_id} and all associated data for lender {lender_id}")
        
        return ResponseModel(
            message=f"Successfully deleted integration sequence '{sequence.name}' and all associated data for lender {lender_id}",
            data={"sequence_id": sequence_id, "name": sequence.name}
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete integration sequence {sequence_id} for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete integration sequence")

# Keep the old endpoint for backward compatibility (deprecated)
@router.get("/{lender_id}/integration-sequence", response_model=ResponseModel)
async def get_integration_sequence_deprecated(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the first active integration sequence for a lender (deprecated - use /integration-sequences instead)"""
    try:
        seq_result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.lender_id == lender_id, 
                IntegrationSequence.is_active == True
            ).order_by(IntegrationSequence.created_at.desc())
        )
        sequence = seq_result.scalar_one_or_none()
        
        if not sequence:
            return ResponseModel(message="No integration sequence configured", data=None)
            
        steps_result = await db.execute(
            select(Integration).where(
                Integration.parent_sequence_id == sequence.id,
                Integration.status != IntegrationStatus.INACTIVE
            ).order_by(Integration.sequence_order.asc())
        )
        steps = steps_result.scalars().all()
        
        return ResponseModel(
            message=f"Retrieved integration sequence for lender {lender_id}",
            data={
                "id": sequence.id,
                "name": sequence.name,
                "description": sequence.description,
                "sequence_type": sequence.sequence_type,
                "execution_mode": sequence.execution_mode,
                "condition_config": sequence.condition_config,
                "stop_on_error": sequence.stop_on_error,
                "retry_failed_steps": sequence.retry_failed_steps,
                "is_active": sequence.is_active,
                "steps": [
                    {
                        "id": step.id,
                        "name": step.name,
                        "integration_type": step.integration_type,
                        "api_endpoint": step.api_endpoint,
                        "http_method": step.http_method,
                        "sequence_order": step.sequence_order,
                        "auth_type": step.auth_type,
                        "auth_config": step.auth_config,
                        "depends_on_fields": step.depends_on_fields,
                        "output_fields": step.output_fields,
                        "is_active": step.status == IntegrationStatus.ACTIVE,
                        "timeout_seconds": step.timeout_seconds,
                        "retry_count": step.retry_count,
                        "retry_delay_seconds": step.retry_delay_seconds,
                        "rate_limit_per_minute": step.rate_limit_per_minute,
                        "request_headers": step.request_headers,
                        "request_schema": step.request_schema
                    } for step in steps
                ]
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve integration sequence for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integration sequence")

@router.post("/{lender_id}/integration-sequence", response_model=ResponseModel)
async def save_integration_sequence_deprecated(
    lender_id: int,
    sequence_payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Save integration sequence for a lender (deprecated - use /integration-sequences instead)"""
    try:
        # Basic payload validation
        name = (sequence_payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Sequence name is required")

        steps = sequence_payload.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise HTTPException(status_code=400, detail="At least one step is required")

        execution_mode = sequence_payload.get("execution_mode", "sequential")
        if execution_mode not in ("sequential", "parallel", "conditional"):
            raise HTTPException(status_code=400, detail="Invalid execution_mode")

        # Upsert sequence
        seq_result = await db.execute(
            select(IntegrationSequence).where(IntegrationSequence.lender_id == lender_id)
        )
        sequence = seq_result.scalar_one_or_none()
        
        if not sequence:
            sequence = IntegrationSequence(
                lender_id=lender_id,
                name=name or "Sequence",
                description=sequence_payload.get("description"),
                sequence_type=sequence_payload.get("sequence_type", "lead_submission"),
                execution_mode=execution_mode,
                condition_config=sequence_payload.get("condition_config"),
                stop_on_error=bool(sequence_payload.get("stop_on_error", True)),
                retry_failed_steps=bool(sequence_payload.get("retry_failed_steps", False)),
                is_active=True,
            )
            db.add(sequence)
            await db.flush()
        else:
            sequence.name = name or sequence.name
            sequence.description = sequence_payload.get("description")
            sequence.sequence_type = sequence_payload.get("sequence_type", sequence.sequence_type)
            sequence.execution_mode = execution_mode
            sequence.condition_config = sequence_payload.get("condition_config")
            sequence.stop_on_error = bool(sequence_payload.get("stop_on_error", sequence.stop_on_error))
            sequence.retry_failed_steps = bool(sequence_payload.get("retry_failed_steps", sequence.retry_failed_steps))
            sequence.is_active = True

        # Get existing integrations for this sequence
        existing_integrations_result = await db.execute(
            select(Integration).where(Integration.parent_sequence_id == sequence.id)
        )
        existing_integrations = {intg.id: intg for intg in existing_integrations_result.scalars().all()}
        
        # Track which integrations we've processed
        processed_integration_ids = set()
        
        # Update or create steps
        for index, step in enumerate(steps):
            step_id = step.get("id")
            
            if step_id and step_id in existing_integrations:
                # Update existing step
                integration = existing_integrations[step_id]
                integration.name = step.get("name", f"Step {index + 1}")
                integration.integration_type = step.get("integration_type", "LEAD_SUBMISSION")
                integration.api_endpoint = step.get("api_endpoint", "")
                integration.http_method = step.get("http_method", "POST")
                integration.sequence_order = step.get("sequence_order", index + 1)
                integration.auth_type = step.get("auth_type", "NONE")
                integration.auth_config = step.get("auth_config", {})
                integration.depends_on_fields = step.get("depends_on_fields", {})
                integration.output_fields = step.get("output_fields", [])
                integration.is_active = step.get("is_active", True)
                integration.timeout_seconds = step.get("timeout_seconds")
                integration.retry_count = step.get("retry_count")
                integration.retry_delay_seconds = step.get("retry_delay_seconds")
                integration.rate_limit_per_minute = step.get("rate_limit_per_minute")
                integration.request_headers = step.get("request_headers")
                integration.request_schema = step.get("request_schema")
                
                processed_integration_ids.add(step_id)
            else:
                # Create new step
                integration = Integration(
                    lender_id=lender_id,
                    parent_sequence_id=sequence.id,
                    name=step.get("name", f"Step {index + 1}"),
                    integration_type=step.get("integration_type", "LEAD_SUBMISSION"),
                    api_endpoint=step.get("api_endpoint", ""),
                    http_method=step.get("http_method", "POST"),
                    sequence_order=step.get("sequence_order", index + 1),
                    auth_type=step.get("auth_type", "NONE"),
                    auth_config=step.get("auth_config", {}),
                    depends_on_fields=step.get("depends_on_fields", {}),
                    output_fields=step.get("output_fields", []),
                    is_sequence_step=True,
                    is_active=step.get("is_active", True),
                    timeout_seconds=step.get("timeout_seconds"),
                    retry_count=step.get("retry_count"),
                    retry_delay_seconds=step.get("retry_delay_seconds"),
                    rate_limit_per_minute=step.get("rate_limit_per_minute"),
                    request_headers=step.get("request_headers"),
                    request_schema=step.get("request_schema")
                )
                db.add(integration)
        
        # Deactivate steps that are no longer in the sequence
        for integration_id, integration in existing_integrations.items():
            if integration_id not in processed_integration_ids:
                integration.is_active = False
        
        await db.commit()
        
        return ResponseModel(
            message=f"Successfully saved integration sequence for lender {lender_id}",
            data={"sequence_id": sequence.id, "name": sequence.name}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save integration sequence for lender {lender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save integration sequence")


@router.post("/{lender_id}/test-integration", response_model=ResponseModel)
async def test_integration_endpoint(
    lender_id: int,
    test_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        runner = IntegrationRunner()
        result = await runner.run(db, lender_id, test_data or {}, mode="test")
        if current_user:
            result["triggered_by_user_id"] = current_user.id
        return ResponseModel(message="Integration test executed", data=result)
    except Exception as e:
        logger.error("Integration test failed", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Integration test failed")


# -------------------------------------
# Run logs for a Lender
# -------------------------------------

@router.get("/{lender_id}/runs", response_model=ResponseModel)
async def list_runs(
    lender_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    from ....models.integration import IntegrationLog
    try:
        subq = select(Integration.id).where(Integration.lender_id == lender_id).subquery()
        # distinct run ids ordered by latest time
        result = await db.execute(
            select(IntegrationLog.request_id, func.max(IntegrationLog.created_at).label("ts"))
            .where(IntegrationLog.integration_id.in_(select(subq.c.id)))
            .group_by(IntegrationLog.request_id)
            .order_by(func.max(IntegrationLog.created_at).desc())
            .limit(limit)
        )
        rows = result.all()
        runs = [
            {"run_id": r[0], "last_at": r[1].isoformat() if r[1] else None}
            for r in rows
        ]
        return ResponseModel(message="Runs listed", data=runs)
    except Exception as e:
        logger.error("Failed to list runs", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list runs")


@router.get("/{lender_id}/runs/{run_id}", response_model=ResponseModel)
async def get_run(
    lender_id: int,
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    from ....models.integration import IntegrationLog
    try:
        subq = select(Integration.id).where(Integration.lender_id == lender_id).subquery()
        result = await db.execute(
            select(IntegrationLog)
            .where(
                IntegrationLog.request_id == run_id,
                IntegrationLog.integration_id.in_(select(subq.c.id)),
            )
            .order_by(IntegrationLog.step_order.asc())
        )
        logs = result.scalars().all()
        data = [
            {
                "integration_id": log.integration_id,
                "sequence_id": log.sequence_id,
                "step_order": log.step_order,
                "request_id": log.request_id,
                "request_headers": log.request_headers,
                "request_data": log.request_data,
                "response_status": log.response_status,
                "response_data": log.response_data,
                "created_at": log.created_at.isoformat() if getattr(log, 'created_at', None) else None,
            }
            for log in logs
        ]
        return ResponseModel(message="Run retrieved", data=data)
    except Exception as e:
        logger.error("Failed to retrieve run", lender_id=lender_id, run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve run")


# -------------------------------------
# Mapping transformation test
# -------------------------------------

@router.post("/field-mappings/test", response_model=ResponseModel)
async def test_field_mapping(payload: dict):
    try:
        mapping = payload.get("mapping") or {}
        test_data = payload.get("test_data") or {}
        source = mapping.get("source_field")
        value = test_data.get(source)
        # Simple transformation samples
        ttype = mapping.get("transformation_type", "none")
        tcfg = mapping.get("transformation_config") or {}
        if ttype == "format_phone" and isinstance(value, str):
            digits = ''.join([c for c in value if c.isdigit()])
            if len(digits) == 10:
                value = f"(+91) {digits[0:5]} {digits[5:]}" if tcfg.get("country") == "IN" else f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
        elif ttype == "format_date" and isinstance(value, str):
            # passthrough demo
            value = value
        elif ttype == "split_name" and isinstance(value, str):
            parts = value.split(" ")
            value = {"first_name": parts[0], "last_name": parts[-1] if len(parts) > 1 else ""}

        return ResponseModel(message="Mapping test ok", data={"result": value})
    except Exception as e:
        logger.error("Mapping transform test failed", error=str(e))
        raise HTTPException(status_code=500, detail="Mapping transform test failed")


# -------------------------------------
# Custom Target Fields Management
# -------------------------------------

@router.get("/{lender_id}/custom-target-fields", response_model=ResponseModel[List[CustomTargetFieldResponse]])
async def get_custom_target_fields(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get custom target fields for a lender"""
    try:
        result = await db.execute(
            select(CustomTargetField)
            .where(CustomTargetField.lender_id == lender_id)
            .order_by(CustomTargetField.id.asc())
        )
        fields = result.scalars().all()
        
        return ResponseModel(
            message="Custom target fields retrieved successfully",
            data=[CustomTargetFieldResponse.model_validate(field) for field in fields]
        )
        
    except Exception as e:
        logger.error("Failed to retrieve custom target fields", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve custom target fields"
        )


@router.post("/{lender_id}/custom-target-fields", response_model=ResponseModel[CustomTargetFieldResponse], status_code=status.HTTP_201_CREATED)
async def create_custom_target_field(
    lender_id: int,
    field_data: CustomTargetFieldCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom target field for a lender"""
    try:
        # Verify lender exists
        lender_result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        if not lender_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lender not found"
            )
        
        # Check if field with same name already exists for this lender
        existing_field = await db.execute(
            select(CustomTargetField).where(
                CustomTargetField.lender_id == lender_id,
                CustomTargetField.name == field_data.name
            )
        )
        if existing_field.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Custom target field with name '{field_data.name}' already exists for this lender"
            )
        
        # Create new field
        field = CustomTargetField(**field_data.model_dump())
        field.lender_id = lender_id
        db.add(field)
        await db.commit()
        await db.refresh(field)
        
        logger.info("Custom target field created successfully", field_id=field.id, field_name=field.name, lender_id=lender_id)
        
        return ResponseModel(
            message="Custom target field created successfully",
            data=CustomTargetFieldResponse.model_validate(field)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create custom target field", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create custom target field"
        )


@router.put("/{lender_id}/custom-target-fields/{field_id}", response_model=ResponseModel[CustomTargetFieldResponse])
async def update_custom_target_field(
    lender_id: int,
    field_id: int,
    field_data: CustomTargetFieldUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing custom target field"""
    try:
        # Get existing field
        result = await db.execute(
            select(CustomTargetField).where(
                CustomTargetField.id == field_id,
                CustomTargetField.lender_id == lender_id
            )
        )
        field = result.scalar_one_or_none()
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom target field not found"
            )
        
        # Update field with provided data
        update_data = field_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(field, key, value)
        
        await db.commit()
        await db.refresh(field)
        
        logger.info("Custom target field updated successfully", field_id=field.id, field_name=field.name, lender_id=lender_id)
        
        return ResponseModel(
            message="Custom target field updated successfully",
            data=CustomTargetFieldResponse.model_validate(field)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update custom target field", field_id=field_id, lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update custom target field"
        )


@router.delete("/{lender_id}/custom-target-fields/{field_id}", response_model=ResponseModel)
async def delete_custom_target_field(
    lender_id: int,
    field_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom target field"""
    try:
        # Get existing field
        result = await db.execute(
            select(CustomTargetField).where(
                CustomTargetField.id == field_id,
                CustomTargetField.lender_id == lender_id
            )
        )
        field = result.scalar_one_or_none()
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom target field not found"
            )
        
        # Check if field is used in any mappings
        mapping_count = await db.execute(
            select(func.count(FieldMapping.id)).where(FieldMapping.target_field == field.name)
        )
        count = mapping_count.scalar()
        
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete field '{field.name}' as it is used in {count} field mapping(s)"
            )
        
        # Delete field
        await db.delete(field)
        await db.commit()
        
        logger.info("Custom target field deleted successfully", field_id=field_id, field_name=field.name, lender_id=lender_id)
        
        return ResponseModel(message="Custom target field deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete custom target field", field_id=field_id, lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete custom target field"
        )


# -------------------------------------
# Enhanced Request Fields with Custom Fields
# -------------------------------------

@router.get("/{lender_id}/enhanced-request-fields", response_model=ResponseModel)
async def get_enhanced_request_fields(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get request fields from step configurations plus custom target fields"""
    try:
        from ....models.integration import Integration, IntegrationSequence
        
        # Get all integration steps for this lender
        result = await db.execute(
            select(Integration)
            .where(
                Integration.lender_id == lender_id,
                Integration.is_sequence_step == True
            )
            .order_by(Integration.sequence_order.asc())
        )
        
        integrations = result.scalars().all()
        
        # Get custom target fields for this lender
        custom_fields_result = await db.execute(
            select(CustomTargetField)
            .where(
                CustomTargetField.lender_id == lender_id,
                CustomTargetField.is_active == True
            )
            .order_by(CustomTargetField.id.asc())
        )
        custom_fields = custom_fields_result.scalars().all()
        
        # Extract fields from step configurations
        all_fields = set()
        field_counts = {}
        field_sources = {}
        
        for integration in integrations:
            step_name = integration.name
            request_schema = integration.request_schema or {}
            
            # Extract fields from request_schema template
            if isinstance(request_schema, dict):
                template = request_schema.get("template", {})
                if isinstance(template, dict):
                    _extract_fields_recursive(template, "", all_fields, field_counts, step_name, field_sources)
                
                # Extract fields from query_params
                query_params = request_schema.get("query_params", {})
                if isinstance(query_params, dict):
                    _extract_fields_recursive(query_params, "", all_fields, field_counts, step_name, field_sources)
            
            # Extract fields from depends_on_fields
            depends_on_fields = integration.depends_on_fields or {}
            if isinstance(depends_on_fields, dict):
                for field in depends_on_fields.values():
                    if field:
                        all_fields.add(field)
                        field_counts[field] = field_counts.get(field, 0) + 1
                        if field not in field_sources:
                            field_sources[field] = []
                        field_sources[field].append(f"{step_name} (dependency)")
        
        # Add custom fields
        for custom_field in custom_fields:
            field_name = custom_field.name
            all_fields.add(field_name)
            field_counts[field_name] = field_counts.get(field_name, 0) + 1
            if field_name not in field_sources:
                field_sources[field_name] = []
            field_sources[field_name].append(f"Custom Field: {custom_field.display_name}")
        
        # Convert to sorted list with field counts and sources
        field_list = [
            {
                "field": field,
                "count": field_counts.get(field, 0),
                "frequency": (field_counts.get(field, 0) / max(len(integrations), 1)) * 100,
                "sources": field_sources.get(field, []),
                "is_custom": any(cf.name == field for cf in custom_fields)
            }
            for field in sorted(all_fields)
        ]
        
        return ResponseModel(
            message="Enhanced request fields retrieved successfully",
            data={
                "fields": field_list,
                "total_steps": len(integrations),
                "custom_fields_count": len(custom_fields),
                "unique_fields_count": len(all_fields)
            }
        )
        
    except Exception as e:
        logger.error("Failed to retrieve enhanced request fields", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve enhanced request fields")


# -------------------------------------
# Sequence Testing with Mapped Values
# -------------------------------------

@router.post("/{lender_id}/test-sequence-with-mappings", response_model=ResponseModel)
async def test_sequence_with_mappings(
    lender_id: int,
    test_data: dict,
    sequence_id: Optional[int] = Query(None, description="Specific sequence ID to test"),
    db: AsyncSession = Depends(get_db)
):
    """Test integration sequence using field mappings"""
    try:
        # Get field mappings for this lender
        mappings_result = await db.execute(
            select(FieldMapping).where(
                FieldMapping.lender_id == lender_id,
                FieldMapping.is_active == True
            )
        )
        field_mappings = list(mappings_result.scalars().all())
        
        # Get master source fields for validation
        master_fields_result = await db.execute(
            select(MasterSourceField).where(MasterSourceField.is_active == True)
        )
        master_fields = {field.name: field for field in master_fields_result.scalars().all()}
        
        # Validate test data against master source fields
        validated_data = {}
        missing_required_fields = []
        
        for mapping in field_mappings:
            source_field = mapping.source_field
            if source_field in test_data:
                validated_data[source_field] = test_data[source_field]
            elif mapping.is_required:
                if source_field in master_fields and master_fields[source_field].default_value:
                    validated_data[source_field] = master_fields[source_field].default_value
                else:
                    missing_required_fields.append(source_field)
        
        if missing_required_fields:
            return ResponseModel(
                success=False,
                message=f"Missing required fields: {', '.join(missing_required_fields)}",
                data={
                    "missing_fields": missing_required_fields,
                    "provided_fields": list(test_data.keys()),
                    "mapped_fields": [m.source_field for m in field_mappings if m.is_active]
                }
            )
        
        # Run the integration sequence with mapped data
        integration_runner = IntegrationRunner()
        
        if sequence_id:
            # Test specific sequence
            result = await integration_runner.run(
                db=db,
                lender_id=lender_id,
                input_payload=validated_data,
                mode="test",
                sequence_id=sequence_id
            )
        else:
            # Test first active sequence
            result = await integration_runner.run(
                db=db,
                lender_id=lender_id,
                input_payload=validated_data,
                mode="test"
            )
        
        return ResponseModel(
            message="Sequence test completed successfully",
            data={
                "test_data": validated_data,
                "field_mappings_applied": len(field_mappings),
                "sequence_result": result
            }
        )
        
    except Exception as e:
        logger.error("Failed to test sequence with mappings", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to test sequence with mappings")
