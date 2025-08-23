from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import structlog

from ....core.database import get_db
from ....models.api_template import APITemplate
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_api_template(
    template_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API template"""
    try:
        # Check if template with same name already exists
        name = template_data.get("name")
        if name:
            existing_template = await db.execute(
                select(APITemplate).where(APITemplate.name == name)
            )
            if existing_template.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Template with name '{name}' already exists"
                )
        
        # Create template
        template = APITemplate(**template_data)
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info("API template created successfully", template_id=template.id, template_name=template.name)
        
        return ResponseModel(
            message="API template created successfully",
            data={
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type,
                "category": template.category
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create API template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API template"
        )


@router.get("/", response_model=ResponseModel)
async def get_api_templates(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None, description="Filter by category"),
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_system_template: Optional[bool] = Query(None, description="Filter by system template"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of API templates"""
    try:
        query = select(APITemplate)
        
        if category:
            query = query.where(APITemplate.category == category)
        
        if template_type:
            query = query.where(APITemplate.template_type == template_type)
        
        if is_active is not None:
            query = query.where(APITemplate.is_active == is_active)
        
        if is_system_template is not None:
            query = query.where(APITemplate.is_system_template == is_system_template)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(APITemplate, pagination.sort_by, APITemplate.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(APITemplate.created_at.desc())
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="API templates retrieved successfully",
            data={
                "templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "template_type": template.template_type,
                        "file_extension": template.file_extension,
                        "is_system_template": template.is_system_template,
                        "is_active": template.is_active,
                        "version": template.version,
                        "usage_count": template.usage_count,
                        "last_used_at": template.last_used_at,
                        "created_at": template.created_at
                    }
                    for template in templates
                ],
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": pages
            },
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
        logger.error("Failed to retrieve API templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API templates"
        )


@router.get("/{template_id}", response_model=ResponseModel)
async def get_api_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific API template"""
    try:
        result = await db.execute(
            select(APITemplate).where(APITemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API template with ID {template_id} not found"
            )
        
        return ResponseModel(
            message="API template retrieved successfully",
            data={
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "template_type": template.template_type,
                "template_content": template.template_content,
                "variables": template.variables,
                "dependencies": template.dependencies,
                "file_extension": template.file_extension,
                "is_system_template": template.is_system_template,
                "is_active": template.is_active,
                "version": template.version,
                "parent_template_id": template.parent_template_id,
                "usage_count": template.usage_count,
                "last_used_at": template.last_used_at,
                "created_at": template.created_at,
                "updated_at": template.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve API template", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API template"
        )


@router.put("/{template_id}", response_model=ResponseModel)
async def update_api_template(
    template_id: int,
    template_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update an API template"""
    try:
        result = await db.execute(
            select(APITemplate).where(APITemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API template with ID {template_id} not found"
            )
        
        # Check for name conflict if name is being updated
        if "name" in template_data and template_data["name"] != template.name:
            existing_template = await db.execute(
                select(APITemplate).where(APITemplate.name == template_data["name"])
            )
            if existing_template.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Template with name '{template_data['name']}' already exists"
                )
        
        # Update fields
        for field, value in template_data.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        await db.commit()
        await db.refresh(template)
        
        logger.info("API template updated successfully", template_id=template_id)
        
        return ResponseModel(
            message="API template updated successfully",
            data={
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update API template", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API template"
        )


@router.delete("/{template_id}", response_model=ResponseModel)
async def delete_api_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an API template"""
    try:
        result = await db.execute(
            select(APITemplate).where(APITemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API template with ID {template_id} not found"
            )
        
        # Prevent deletion of system templates
        if template.is_system_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete system templates"
            )
        
        await db.delete(template)
        await db.commit()
        
        logger.info("API template deleted successfully", template_id=template_id)
        
        return ResponseModel(
            message="API template deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete API template", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API template"
        )


@router.get("/categories", response_model=ResponseModel)
async def get_template_categories(db: AsyncSession = Depends(get_db)):
    """Get list of available template categories"""
    try:
        result = await db.execute(
            select(APITemplate.category).distinct().where(APITemplate.category.isnot(None))
        )
        categories = [row[0] for row in result.fetchall()]
        
        return ResponseModel(
            message="Template categories retrieved successfully",
            data={"categories": categories}
        )
        
    except Exception as e:
        logger.error("Failed to retrieve template categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template categories"
        )
