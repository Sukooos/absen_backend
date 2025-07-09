from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from fastapi_pagination import Page, paginate

from app.database.database import get_db
from app.services.user_service import UserService
from app.core.security import get_current_active_user, get_current_active_superuser
from app.schemas.user import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserWithAttendance
)
from app.models.user import User
from app.core.logger import logger

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user information
    """
    try:
        updated_user = UserService.update_user(
            db=db, 
            user=current_user,
            user_data=user_data
        )
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user information"
        )


@router.get("/me/detailed", response_model=UserWithAttendance)
async def get_current_user_detailed(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed user information including recent attendance
    """
    try:
        user_id = getattr(current_user, "id")
        return UserService.get_user_with_attendance(db, user_id)
    except Exception as e:
        logger.error(f"Error retrieving detailed user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving detailed user information"
        )


# Admin endpoints
@router.get("/", response_model=Page[UserResponse])
async def get_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all users (admin only)
    """
    users = UserService.get_users(
        db=db,
        search=search,
        is_active=is_active
    )
    return paginate(users)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new user (admin only)
    """
    # Check if username already exists
    if UserService.get_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if UserService.get_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        user = UserService.create_user(db=db, user_data=user_data)
        return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., description="The ID of the user"),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user by ID (admin only)
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    user_id: int = Path(..., description="The ID of the user to update"),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user information (admin only)
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        updated_user = UserService.update_user(db=db, user=user, user_data=user_data)
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int = Path(..., description="The ID of the user to delete"),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete user (admin only)
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if getattr(user, "id") == getattr(current_user, "id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )
    
    UserService.delete_user(db, user_id)
    return None 