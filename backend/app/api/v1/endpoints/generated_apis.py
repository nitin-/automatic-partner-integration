from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any
import structlog

from ....core.database import get_db
from ....models.generated_api import GeneratedAPI
from ....models.lender import Lender
from ....services.api_generator import APIGenerator
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo

logger = structlog.get_logger()
router = APIRouter()


@router.post("/generate", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
async def generate_api_client(
    background_tasks: BackgroundTasks,
    lender_id: int,
    template_id: Optional[int] = Query(None, description="Template ID to use for generation"),
    language: str = Query("python", description="Programming language"),
    framework: str = Query("fastapi", description="Framework"),
    config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate API client for a lender"""
    try:
        # Validate lender exists
        lender_result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = lender_result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        # Add generation task to background
        background_tasks.add_task(
            _generate_api_client_task,
            lender_id,
            template_id,
            language,
            framework,
            config
        )
        
        logger.info(
            "API generation task queued",
            lender_id=lender_id,
            lender_name=lender.name,
            language=language,
            framework=framework
        )
        
        return ResponseModel(
            message="API generation task queued successfully",
            data={
                "lender_id": lender_id,
                "lender_name": lender.name,
                "language": language,
                "framework": framework,
                "status": "queued"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to queue API generation", lender_id=lender_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue API generation"
        )


async def _generate_api_client_task(
    lender_id: int,
    template_id: Optional[int],
    language: str,
    framework: str,
    config: Optional[Dict[str, Any]]
):
    """Background task for API generation"""
    from ...core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            generator = APIGenerator()
            generated_api = await generator.generate_api_client(
                db=db,
                lender_id=lender_id,
                template_id=template_id,
                language=language,
                framework=framework,
                config=config
            )
            
            # Validate generated API
            is_valid = await generator.validate_generated_api(generated_api)
            generated_api.is_valid = is_valid
            generated_api.test_status = "passed" if is_valid else "failed"
            
            await db.commit()
            
            logger.info(
                "API generation completed",
                generated_api_id=generated_api.id,
                is_valid=is_valid
            )
            
        except Exception as e:
            logger.error(
                "API generation task failed",
                lender_id=lender_id,
                error=str(e)
            )


@router.get("/", response_model=ResponseModel)
async def get_generated_apis(
    pagination: PaginationParams = Depends(),
    lender_id: Optional[int] = Query(None, description="Filter by lender ID"),
    language: Optional[str] = Query(None, description="Filter by language"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    is_valid: Optional[bool] = Query(None, description="Filter by validation status"),
    test_status: Optional[str] = Query(None, description="Filter by test status"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of generated APIs with optional filtering"""
    try:
        # Build query
        query = select(GeneratedAPI).options(
            selectinload(GeneratedAPI.lender)
        )
        
        # Apply filters
        if lender_id:
            query = query.where(GeneratedAPI.lender_id == lender_id)
        
        if language:
            query = query.where(GeneratedAPI.language == language)
        
        if framework:
            query = query.where(GeneratedAPI.framework == framework)
        
        if is_valid is not None:
            query = query.where(GeneratedAPI.is_valid == is_valid)
        
        if test_status:
            query = query.where(GeneratedAPI.test_status == test_status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(GeneratedAPI, pagination.sort_by, GeneratedAPI.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(GeneratedAPI.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        generated_apis = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="Generated APIs retrieved successfully",
            data={
                "generated_apis": [
                    {
                        "id": api.id,
                        "name": api.name,
                        "description": api.description,
                        "version": api.version,
                        "language": api.language,
                        "framework": api.framework,
                        "file_path": api.file_path,
                        "file_size": api.file_size,
                        "is_valid": api.is_valid,
                        "test_status": api.test_status,
                        "generation_time": api.generation_time,
                        "created_at": api.created_at,
                        "lender": {
                            "id": api.lender.id,
                            "name": api.lender.name
                        } if api.lender else None
                    }
                    for api in generated_apis
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
        logger.error("Failed to retrieve generated APIs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve generated APIs"
        )


@router.get("/{generated_api_id}", response_model=ResponseModel)
async def get_generated_api(
    generated_api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific generated API by ID"""
    try:
        result = await db.execute(
            select(GeneratedAPI).options(
                selectinload(GeneratedAPI.lender)
            ).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated API with ID {generated_api_id} not found"
            )
        
        return ResponseModel(
            message="Generated API retrieved successfully",
            data={
                "id": generated_api.id,
                "name": generated_api.name,
                "description": generated_api.description,
                "version": generated_api.version,
                "template_id": generated_api.template_id,
                "generation_config": generated_api.generation_config,
                "file_path": generated_api.file_path,
                "file_size": generated_api.file_size,
                "file_hash": generated_api.file_hash,
                "language": generated_api.language,
                "framework": generated_api.framework,
                "dependencies": generated_api.dependencies,
                "is_valid": generated_api.is_valid,
                "validation_errors": generated_api.validation_errors,
                "test_status": generated_api.test_status,
                "is_deployed": generated_api.is_deployed,
                "deployment_url": generated_api.deployment_url,
                "last_deployed_at": generated_api.last_deployed_at,
                "generation_time": generated_api.generation_time,
                "complexity_score": generated_api.complexity_score,
                "created_at": generated_api.created_at,
                "updated_at": generated_api.updated_at,
                "lender": {
                    "id": generated_api.lender.id,
                    "name": generated_api.lender.name,
                    "base_url": str(generated_api.lender.base_url)
                } if generated_api.lender else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve generated API", generated_api_id=generated_api_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve generated API"
        )


@router.get("/{generated_api_id}/download")
async def download_generated_api(
    generated_api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download generated API file"""
    try:
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated API with ID {generated_api_id} not found"
            )
        
        # Read file content
        try:
            with open(generated_api.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated file not found"
            )
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={generated_api.name.replace(' ', '_')}.{generated_api.language}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download generated API", generated_api_id=generated_api_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download generated API"
        )


@router.post("/{generated_api_id}/validate", response_model=ResponseModel)
async def validate_generated_api(
    generated_api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Validate generated API code"""
    try:
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated API with ID {generated_api_id} not found"
            )
        
        # Validate the generated API
        generator = APIGenerator()
        is_valid = await generator.validate_generated_api(generated_api)
        
        # Update validation status
        generated_api.is_valid = is_valid
        generated_api.test_status = "passed" if is_valid else "failed"
        await db.commit()
        
        return ResponseModel(
            message="Generated API validation completed",
            data={
                "id": generated_api.id,
                "is_valid": is_valid,
                "test_status": generated_api.test_status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to validate generated API", generated_api_id=generated_api_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate generated API"
        )


@router.delete("/{generated_api_id}", response_model=ResponseModel)
async def delete_generated_api(
    generated_api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a generated API"""
    try:
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated API with ID {generated_api_id} not found"
            )
        
        # Delete file if it exists
        try:
            import os
            if os.path.exists(generated_api.file_path):
                os.remove(generated_api.file_path)
        except Exception as e:
            logger.warning("Failed to delete generated file", file_path=generated_api.file_path, error=str(e))
        
        # Delete database record
        await db.delete(generated_api)
        await db.commit()
        
        logger.info("Generated API deleted successfully", generated_api_id=generated_api_id)
        
        return ResponseModel(
            message="Generated API deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete generated API", generated_api_id=generated_api_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete generated API"
        )
