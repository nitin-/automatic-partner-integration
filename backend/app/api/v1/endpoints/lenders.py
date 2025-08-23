from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import structlog

from ....core.database import get_db
from ....models.lender import Lender
from ....schemas.lender import LenderCreate, LenderUpdate, LenderResponse, LenderList
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo
from ....models.field_mapping import FieldMapping, TransformationType, DataType
from ....models.integration import IntegrationSequence, Integration, IntegrationType, AuthenticationType
from sqlalchemy import delete
from ....services.integration_runner import IntegrationRunner
from .auth import get_current_user

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
# Integration Sequence for a Lender
# -------------------------------------

@router.get("/{lender_id}/integration-sequence", response_model=ResponseModel)
async def get_integration_sequence(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        seq_result = await db.execute(
            select(IntegrationSequence).where(IntegrationSequence.lender_id == lender_id, IntegrationSequence.is_active == True)
        )
        sequence = seq_result.scalar_one_or_none()
        if not sequence:
            return ResponseModel(message="No integration sequence configured", data=None)
        steps_result = await db.execute(
            select(Integration).where(Integration.parent_sequence_id == sequence.id).order_by(Integration.sequence_order.asc())
        )
        steps = steps_result.scalars().all()
        return ResponseModel(
            message="Integration sequence retrieved successfully",
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
                        "id": s.id,
                        "name": s.name,
                        "integration_type": s.integration_type.value if s.integration_type else None,
                        "api_endpoint": s.api_endpoint,
                        "http_method": s.http_method,
                        "sequence_order": s.sequence_order,
                        "auth_type": s.auth_type.value if s.auth_type else None,
                        "auth_config": s.auth_config,
                        "request_headers": s.request_headers,
                        "request_schema": s.request_schema,
                        "depends_on_fields": s.depends_on_fields or {},
                        "output_fields": s.output_fields or [],
                        "is_active": True,
                    }
                    for s in steps
                ],
            }
        )
    except Exception as e:
        logger.error("Failed to retrieve integration sequence", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve integration sequence")


@router.post("/{lender_id}/integration-sequence", response_model=ResponseModel)
async def save_integration_sequence(
    lender_id: int,
    sequence_payload: dict,
    db: AsyncSession = Depends(get_db)
):
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

        # Replace steps
        await db.execute(delete(Integration).where(Integration.parent_sequence_id == sequence.id))
        for index, step in enumerate(steps):
            step_name = (step.get("name") or f"Step {index+1}").strip()
            http_method = (step.get("http_method") or "POST").upper()
            api_endpoint = (step.get("api_endpoint") or "").strip()

            if http_method not in ("GET","POST","PUT","PATCH","DELETE"):
                raise HTTPException(status_code=400, detail=f"Invalid http_method for step {index+1}")
            if not api_endpoint or not (api_endpoint.startswith("http://") or api_endpoint.startswith("https://") or api_endpoint.startswith("/")):
                raise HTTPException(status_code=400, detail=f"Invalid api_endpoint for step {index+1}")

            # Dependency constraints
            depends_on_fields = step.get("depends_on_fields", {}) or {}
            if execution_mode == "parallel" and len(depends_on_fields) > 0:
                raise HTTPException(status_code=400, detail=f"Dependencies are not allowed in parallel mode (step {index+1})")
            if execution_mode == "sequential" and index == 0 and len(depends_on_fields) > 0:
                raise HTTPException(status_code=400, detail=f"First step cannot have dependencies in sequential mode")

            try:
                integration_type = IntegrationType(step.get("integration_type", "lead_submission"))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid integration_type for step {index+1}")

            try:
                auth_type = AuthenticationType(step.get("auth_type", "api_key"))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid auth_type for step {index+1}")

            db.add(
                Integration(
                    lender_id=lender_id,
                    name=step_name,
                    description=None,
                    integration_type=integration_type,
                    api_endpoint=api_endpoint,
                    http_method=http_method,
                    sequence_order=step.get("sequence_order", index + 1),
                    parent_sequence_id=sequence.id,
                    is_sequence_step=True,
                    auth_type=auth_type,
                    auth_config=step.get("auth_config"),
                    depends_on_fields=depends_on_fields,
                    output_fields=step.get("output_fields", []),
                    request_headers=step.get("request_headers"),
                    request_schema=step.get("request_schema"),
                    timeout_seconds=step.get("timeout_seconds", 30),
                    retry_count=step.get("retry_count", 3),
                    retry_delay_seconds=step.get("retry_delay_seconds", 5),
                    rate_limit_per_minute=step.get("rate_limit_per_minute"),
                )
            )

        await db.commit()
        return ResponseModel(message="Integration sequence saved successfully")
    except Exception as e:
        await db.rollback()
        logger.error("Failed to save integration sequence", lender_id=lender_id, error=str(e))
        if isinstance(e, HTTPException):
            raise e
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
