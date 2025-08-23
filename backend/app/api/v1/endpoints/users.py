from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import structlog

from ....core.database import get_db
from ....models.user import User
from ....schemas.common import ResponseModel, PaginationParams, PaginationInfo

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    try:
        # Check if user with same email already exists
        email = user_data.get("email")
        if email:
            existing_user = await db.execute(
                select(User).where(User.email == email)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email '{email}' already exists"
                )
        
        # Check if username already exists
        username = user_data.get("username")
        if username:
            existing_user = await db.execute(
                select(User).where(User.username == username)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with username '{username}' already exists"
                )
        
        # Hash password if provided
        if "password" in user_data:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
        
        # Create user
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("User created successfully", user_id=user.id, email=user.email)
        
        return ResponseModel(
            message="User created successfully",
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/", response_model=ResponseModel)
async def get_users(
    pagination: PaginationParams = Depends(),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of users"""
    try:
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(User, pagination.sort_by, User.created_at)
            if pagination.sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        else:
            query = query.order_by(User.created_at.desc())
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        pages = (total + pagination.size - 1) // pagination.size
        
        return ResponseModel(
            message="Users retrieved successfully",
            data={
                "users": [
                    {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "company": user.company,
                        "api_quota": user.api_quota,
                        "api_usage": user.api_usage,
                        "last_login_at": user.last_login_at,
                        "created_at": user.created_at
                    }
                    for user in users
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
        logger.error("Failed to retrieve users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=ResponseModel)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return ResponseModel(
            message="User retrieved successfully",
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "company": user.company,
                "api_quota": user.api_quota,
                "api_usage": user.api_usage,
                "preferences": user.preferences,
                "last_login_at": user.last_login_at,
                "failed_login_attempts": user.failed_login_attempts,
                "locked_until": user.locked_until,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=ResponseModel)
async def update_user(
    user_id: int,
    user_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update a user"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Check for email conflict if email is being updated
        if "email" in user_data and user_data["email"] != user.email:
            existing_user = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email '{user_data['email']}' already exists"
                )
        
        # Check for username conflict if username is being updated
        if "username" in user_data and user_data["username"] != user.username:
            existing_user = await db.execute(
                select(User).where(User.username == user_data["username"])
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with username '{user_data['username']}' already exists"
                )
        
        # Hash password if provided
        if "password" in user_data:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
        
        # Update fields
        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info("User updated successfully", user_id=user_id)
        
        return ResponseModel(
            message="User updated successfully",
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        await db.delete(user)
        await db.commit()
        
        logger.info("User deleted successfully", user_id=user_id)
        
        return ResponseModel(
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.patch("/{user_id}/toggle-status", response_model=ResponseModel)
async def toggle_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Toggle status
        user.is_active = not user.is_active
        await db.commit()
        await db.refresh(user)
        
        status_text = "activated" if user.is_active else "deactivated"
        logger.info(f"User {status_text}", user_id=user.id, email=user.email)
        
        return ResponseModel(
            message=f"User {status_text} successfully",
            data={
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Failed to toggle user status", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle user status"
        )
