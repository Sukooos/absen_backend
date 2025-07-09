from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import base64

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.config import settings
from app.core.logger import logger


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get a user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = AuthService.get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate, face_encoding: Optional[bytes] = None) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            position=user_data.position,
            employee_id=user_data.employee_id,
            phone=user_data.phone,
            address=user_data.address,
            profile_picture=user_data.profile_picture,
            additional_data=user_data.additional_data,
            face_encoding=face_encoding,
            is_active=True,
            is_superuser=user_data.is_superuser if hasattr(user_data, 'is_superuser') else False
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"User created: {user_data.username}")
            return db_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    @staticmethod
    def update_user_password(db: Session, user: User, new_password: str) -> User:
        """Update user password"""
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"Password updated for user: {user.username}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating password: {str(e)}")
            raise
    
    @staticmethod
    def update_user_face(db: Session, user: User, face_encoding: bytes) -> User:
        """Update user face encoding"""
        user.face_encoding = face_encoding
        
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"Face encoding updated for user: {user.username}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating face encoding: {str(e)}")
            raise
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> Optional[User]:
        """Deactivate a user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_active = False
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"User deactivated: {user.username}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating user: {str(e)}")
            raise
    
    @staticmethod
    def reactivate_user(db: Session, user_id: int) -> Optional[User]:
        """Reactivate a user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_active = True
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"User reactivated: {user.username}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error reactivating user: {str(e)}")
            raise 