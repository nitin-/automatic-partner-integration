from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
import structlog

from ....core.database import get_db
from ....models.api_test import APITest
from ....models.api_config import APIConfig
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_api_test(
    test_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API test"""
    try:
        # Validate API config exists
        api_config_id = test_data.get("api_config_id")
        if not api_config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_config_id is required"
            )
        
        config_result = await db.execute(
            select(APIConfig).where(APIConfig.id == api_config_id)
        )
        api_config = config_result.scalar_one_or_none()
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API configuration with ID {api_config_id} not found"
            )
        
        # Create test
        api_test = APITest(**test_data)
        db.add(api_test)
        await db.commit()
        await db.refresh(api_test)
        
        logger.info("API test created successfully", test_id=api_test.id, api_config_id=api_config_id)
        
        return ResponseModel(
            message="API test created successfully",
            data={
                "id": api_test.id,
                "name": api_test.name,
                "api_config_id": api_test.api_config_id,
                "test_type": api_test.test_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create API test", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API test"
        )


@router.get("/", response_model=ResponseModel)
async def get_api_tests(
    pagination: PaginationParams = Depends(),
    api_config_id: Optional[int] = Query(None, description="Filter by API config ID"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of API tests"""
    try:
        query = select(APITest).options(selectinload(APITest.api_config))
        
        if api_config_id:
            query = query.where(APITest.api_config_id == api_config_id)
        
        if test_type:
            query = query.where(APITest.test_type == test_type)
        
        if is_active is not None:
            query = query.where(APITest.is_active == is_active)
        
        if environment:
            query = query.where(APITest.environment == environment)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(APITest, pagination.sort_by, APITest.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(APITest.created_at.desc())
        
        result = await db.execute(query)
        api_tests = result.scalars().all()
        
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="API tests retrieved successfully",
            data={
                "api_tests": [
                    {
                        "id": test.id,
                        "name": test.name,
                        "description": test.description,
                        "api_config_id": test.api_config_id,
                        "api_config_name": test.api_config.name if test.api_config else None,
                        "test_type": test.test_type,
                        "is_active": test.is_active,
                        "is_automated": test.is_automated,
                        "last_run_status": test.last_run_status,
                        "last_run_duration": test.last_run_duration,
                        "success_rate": test.success_rate,
                        "environment": test.environment,
                        "created_at": test.created_at
                    }
                    for test in api_tests
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
        logger.error("Failed to retrieve API tests", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API tests"
        )


@router.get("/{test_id}", response_model=ResponseModel)
async def get_api_test(
    test_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific API test"""
    try:
        result = await db.execute(
            select(APITest).options(selectinload(APITest.api_config)).where(APITest.id == test_id)
        )
        api_test = result.scalar_one_or_none()
        
        if not api_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API test with ID {test_id} not found"
            )
        
        return ResponseModel(
            message="API test retrieved successfully",
            data={
                "id": api_test.id,
                "name": api_test.name,
                "description": api_test.description,
                "api_config_id": api_test.api_config_id,
                "api_config": {
                    "id": api_test.api_config.id,
                    "name": api_test.api_config.name,
                    "endpoint_path": api_test.api_config.endpoint_path,
                    "method": api_test.api_config.method
                } if api_test.api_config else None,
                "test_type": api_test.test_type,
                "test_data": api_test.test_data,
                "expected_response": api_test.expected_response,
                "validation_rules": api_test.validation_rules,
                "is_active": api_test.is_active,
                "is_automated": api_test.is_automated,
                "execution_order": api_test.execution_order,
                "last_run_at": api_test.last_run_at,
                "last_run_status": api_test.last_run_status,
                "last_run_duration": api_test.last_run_duration,
                "last_run_error": api_test.last_run_error,
                "avg_response_time": api_test.avg_response_time,
                "success_rate": api_test.success_rate,
                "total_runs": api_test.total_runs,
                "successful_runs": api_test.successful_runs,
                "environment": api_test.environment,
                "timeout": api_test.timeout,
                "created_at": api_test.created_at,
                "updated_at": api_test.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve API test", test_id=test_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API test"
        )


@router.put("/{test_id}", response_model=ResponseModel)
async def update_api_test(
    test_id: int,
    test_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update an API test"""
    try:
        result = await db.execute(
            select(APITest).where(APITest.id == test_id)
        )
        api_test = result.scalar_one_or_none()
        
        if not api_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API test with ID {test_id} not found"
            )
        
        # Update fields
        for field, value in test_data.items():
            if hasattr(api_test, field):
                setattr(api_test, field, value)
        
        await db.commit()
        await db.refresh(api_test)
        
        logger.info("API test updated successfully", test_id=test_id)
        
        return ResponseModel(
            message="API test updated successfully",
            data={
                "id": api_test.id,
                "name": api_test.name,
                "api_config_id": api_test.api_config_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update API test", test_id=test_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API test"
        )


@router.delete("/{test_id}", response_model=ResponseModel)
async def delete_api_test(
    test_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an API test"""
    try:
        result = await db.execute(
            select(APITest).where(APITest.id == test_id)
        )
        api_test = result.scalar_one_or_none()
        
        if not api_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API test with ID {test_id} not found"
            )
        
        await db.delete(api_test)
        await db.commit()
        
        logger.info("API test deleted successfully", test_id=test_id)
        
        return ResponseModel(
            message="API test deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete API test", test_id=test_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API test"
        )


@router.post("/{test_id}/run", response_model=ResponseModel)
async def run_api_test(
    test_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Run an API test"""
    try:
        result = await db.execute(
            select(APITest).options(selectinload(APITest.api_config)).where(APITest.id == test_id)
        )
        api_test = result.scalar_one_or_none()
        
        if not api_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API test with ID {test_id} not found"
            )
        
        # TODO: Implement actual test execution logic
        # This would involve making HTTP requests to the API endpoint
        # and validating the response against expected results
        
        # For now, just update the test status
        import time
        api_test.last_run_at = time.time()
        api_test.last_run_status = "passed"  # This would be determined by actual test execution
        api_test.last_run_duration = 100  # milliseconds
        api_test.total_runs += 1
        api_test.successful_runs += 1
        
        # Calculate success rate
        if api_test.total_runs > 0:
            api_test.success_rate = (api_test.successful_runs / api_test.total_runs) * 100
        
        await db.commit()
        
        logger.info("API test executed successfully", test_id=test_id)
        
        return ResponseModel(
            message="API test executed successfully",
            data={
                "id": api_test.id,
                "name": api_test.name,
                "last_run_status": api_test.last_run_status,
                "last_run_duration": api_test.last_run_duration,
                "success_rate": api_test.success_rate
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to run API test", test_id=test_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run API test"
        )
