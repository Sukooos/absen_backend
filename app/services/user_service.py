from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
import base64

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.services.face_recognition_service import FaceRecognitionService
from app.core.logger import logger


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """Get a user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get all users with filtering options"""
        query = db.query(User)
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        # Apply active status filter if provided
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        
        face_encoding = None
        if user_data.face_image:
            try:
                face_service = FaceRecognitionService()
                face_encoding = face_service.process_face_image(user_data.face_image)
            except Exception as e:
                logger.error(f"Error processing face image: {str(e)}")
                # Continue without face encoding
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            face_encoding=face_encoding,
            is_active=user_data.is_active,
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
    def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
        """Update user information"""
        # Update fields if provided
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.is_superuser is not None:
            user.is_superuser = user_data.is_superuser
        
        # Process face image if provided
        if user_data.face_image:
            try:
                face_service = FaceRecognitionService()
                face_encoding = face_service.process_face_image(user_data.face_image)
                if face_encoding:
                    user.face_encoding = face_encoding
            except Exception as e:
                logger.error(f"Error processing face image: {str(e)}")
                # Continue without updating face encoding
        
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"User updated: {user.username}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return False
        
        try:
            db.delete(user)
            db.commit()
            logger.info(f"User deleted: ID {user_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user: {str(e)}")
            raise
    
    @staticmethod
    def get_user_with_attendance(db: Session, user_id: int):
        """Get user with recent attendance records"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return None
        
        # Attendance records are loaded via relationship
        # We can limit the number of records if needed
        
        return user 