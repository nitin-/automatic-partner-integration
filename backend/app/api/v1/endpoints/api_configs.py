from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
import structlog

from ....core.database import get_db
from ....models.api_config import APIConfig
from ....models.lender import Lender
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_api_config(
    api_config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API configuration"""
    try:
        # Validate lender exists
        lender_id = api_config_data.get("lender_id")
        if not lender_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="lender_id is required"
            )
        
        lender_result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = lender_result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        # Create API config
        api_config = APIConfig(**api_config_data)
        db.add(api_config)
        await db.commit()
        await db.refresh(api_config)
        
        logger.info("API config created successfully", config_id=api_config.id, lender_id=lender_id)
        
        return ResponseModel(
            message="API configuration created successfully",
            data={
                "id": api_config.id,
                "name": api_config.name,
                "lender_id": api_config.lender_id,
                "endpoint_path": api_config.endpoint_path,
                "method": api_config.method
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create API config", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API configuration"
        )


@router.get("/", response_model=ResponseModel)
async def get_api_configs(
    pagination: PaginationParams = Depends(),
    lender_id: Optional[int] = Query(None, description="Filter by lender ID"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of API configurations"""
    try:
        query = select(APIConfig).options(selectinload(APIConfig.lender))
        
        if lender_id:
            query = query.where(APIConfig.lender_id == lender_id)
        
        if method:
            query = query.where(APIConfig.method == method.upper())
        
        if is_active is not None:
            query = query.where(APIConfig.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(APIConfig, pagination.sort_by, APIConfig.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(APIConfig.created_at.desc())
        
        result = await db.execute(query)
        api_configs = result.scalars().all()
        
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="API configurations retrieved successfully",
            data={
                "api_configs": [
                    {
                        "id": config.id,
                        "name": config.name,
                        "description": config.description,
                        "lender_id": config.lender_id,
                        "lender_name": config.lender.name if config.lender else None,
                        "endpoint_path": config.endpoint_path,
                        "method": config.method,
                        "is_active": config.is_active,
                        "version": config.version,
                        "created_at": config.created_at
                    }
                    for config in api_configs
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
        logger.error("Failed to retrieve API configs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API configurations"
        )


@router.get("/{config_id}", response_model=ResponseModel)
async def get_api_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific API configuration"""
    try:
        result = await db.execute(
            select(APIConfig).options(selectinload(APIConfig.lender)).where(APIConfig.id == config_id)
        )
        api_config = result.scalar_one_or_none()
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API configuration with ID {config_id} not found"
            )
        
        return ResponseModel(
            message="API configuration retrieved successfully",
            data={
                "id": api_config.id,
                "name": api_config.name,
                "description": api_config.description,
                "lender_id": api_config.lender_id,
                "lender": {
                    "id": api_config.lender.id,
                    "name": api_config.lender.name,
                    "base_url": str(api_config.lender.base_url)
                } if api_config.lender else None,
                "endpoint_path": api_config.endpoint_path,
                "method": api_config.method,
                "headers": api_config.headers,
                "query_params": api_config.query_params,
                "request_body_schema": api_config.request_body_schema,
                "response_schema": api_config.response_schema,
                "success_codes": api_config.success_codes,
                "requires_auth": api_config.requires_auth,
                "auth_parameters": api_config.auth_parameters,
                "rate_limit": api_config.rate_limit,
                "retry_config": api_config.retry_config,
                "validation_rules": api_config.validation_rules,
                "data_mapping": api_config.data_mapping,
                "is_active": api_config.is_active,
                "is_deprecated": api_config.is_deprecated,
                "version": api_config.version,
                "created_at": api_config.created_at,
                "updated_at": api_config.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve API config", config_id=config_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API configuration"
        )


@router.put("/{config_id}", response_model=ResponseModel)
async def update_api_config(
    config_id: int,
    api_config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update an API configuration"""
    try:
        result = await db.execute(
            select(APIConfig).where(APIConfig.id == config_id)
        )
        api_config = result.scalar_one_or_none()
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API configuration with ID {config_id} not found"
            )
        
        # Update fields
        for field, value in api_config_data.items():
            if hasattr(api_config, field):
                setattr(api_config, field, value)
        
        await db.commit()
        await db.refresh(api_config)
        
        logger.info("API config updated successfully", config_id=config_id)
        
        return ResponseModel(
            message="API configuration updated successfully",
            data={
                "id": api_config.id,
                "name": api_config.name,
                "lender_id": api_config.lender_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update API config", config_id=config_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API configuration"
        )


@router.delete("/{config_id}", response_model=ResponseModel)
async def delete_api_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an API configuration"""
    try:
        result = await db.execute(
            select(APIConfig).where(APIConfig.id == config_id)
        )
        api_config = result.scalar_one_or_none()
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API configuration with ID {config_id} not found"
            )
        
        await db.delete(api_config)
        await db.commit()
        
        logger.info("API config deleted successfully", config_id=config_id)
        
        return ResponseModel(
            message="API configuration deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete API config", config_id=config_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API configuration"
        )
