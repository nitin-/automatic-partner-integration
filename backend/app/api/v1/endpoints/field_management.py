from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
import structlog

from ....core.database import get_db
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo, MasterSourceFieldCreate, MasterSourceFieldUpdate, MasterSourceFieldResponse
from ....models.field_mapping import MasterSourceField, FieldMapping

logger = structlog.get_logger()
router = APIRouter()


@router.get("/master-source-fields", response_model=ResponseModel[List[MasterSourceFieldResponse]])
async def get_master_source_fields(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by field name or display name"),
    field_type: Optional[str] = Query(None, description="Filter by field type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of master source fields with optional filtering"""
    try:
        # Build query
        query = select(MasterSourceField)
        
        # Apply filters
        if search:
            query = query.where(
                MasterSourceField.name.ilike(f"%{search}%") | 
                MasterSourceField.display_name.ilike(f"%{search}%")
            )
        
        if field_type:
            query = query.where(MasterSourceField.field_type == field_type)
        
        if is_active is not None:
            query = query.where(MasterSourceField.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
        
        # Execute query
        result = await db.execute(query)
        fields = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="Master source fields retrieved successfully",
            data=[MasterSourceFieldResponse.model_validate(field) for field in fields],
            pagination=PaginationInfo(
                page=pagination.page,
                size=pagination.size,
                total=total,
                pages=pages,
                has_next=pagination.page < pages,
                has_prev=pagination.page > 1
            )
        )
        
    except Exception as e:
        logger.error("Failed to retrieve master source fields", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve master source fields"
        )


@router.post("/master-source-fields", response_model=ResponseModel[MasterSourceFieldResponse], status_code=status.HTTP_201_CREATED)
async def create_master_source_field(
    field_data: MasterSourceFieldCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new master source field"""
    try:
        # Check if field with same name already exists
        existing_field = await db.execute(
            select(MasterSourceField).where(MasterSourceField.name == field_data.name)
        )
        if existing_field.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Master source field with name '{field_data.name}' already exists"
            )
        
        # Create new field
        field = MasterSourceField(**field_data.model_dump())
        db.add(field)
        await db.commit()
        await db.refresh(field)
        
        logger.info("Master source field created successfully", field_id=field.id, field_name=field.name)
        
        return ResponseModel(
            message="Master source field created successfully",
            data=MasterSourceFieldResponse.model_validate(field)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create master source field", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create master source field"
        )


@router.put("/master-source-fields/{field_id}", response_model=ResponseModel[MasterSourceFieldResponse])
async def update_master_source_field(
    field_id: int,
    field_data: MasterSourceFieldUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing master source field"""
    try:
        # Get existing field
        result = await db.execute(
            select(MasterSourceField).where(MasterSourceField.id == field_id)
        )
        field = result.scalar_one_or_none()
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master source field not found"
            )
        
        # Update field with provided data
        update_data = field_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(field, key, value)
        
        await db.commit()
        await db.refresh(field)
        
        logger.info("Master source field updated successfully", field_id=field.id, field_name=field.name)
        
        return ResponseModel(
            message="Master source field updated successfully",
            data=MasterSourceFieldResponse.model_validate(field)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update master source field", field_id=field_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update master source field"
        )


@router.delete("/master-source-fields/{field_id}", response_model=ResponseModel)
async def delete_master_source_field(
    field_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a master source field"""
    try:
        # Get existing field
        result = await db.execute(
            select(MasterSourceField).where(MasterSourceField.id == field_id)
        )
        field = result.scalar_one_or_none()
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master source field not found"
            )
        
        # Check if field is used in any mappings
        mapping_count = await db.execute(
            select(func.count(FieldMapping.id)).where(FieldMapping.source_field == field.name)
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
        
        logger.info("Master source field deleted successfully", field_id=field_id, field_name=field.name)
        
        return ResponseModel(message="Master source field deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete master source field", field_id=field_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete master source field"
        )
