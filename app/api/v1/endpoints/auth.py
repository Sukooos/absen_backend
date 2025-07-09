from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Any
from pydantic import EmailStr
from datetime import datetime, timezone
from jose import jwt, JWTError

from app.database.database import get_db
from app.services.auth_service import AuthService
from app.services.face_recognition_service import FaceRecognitionService
from app.core.security import (
    get_current_active_user, 
    create_access_token, 
    create_refresh_token,
    verify_password,
    create_password_reset_token,
    verify_password_reset_token
)
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenPayload,
    PasswordReset,
    PasswordChange,
    FaceLoginRequest,
    LoginResponse,
    UserInfo
)
from app.schemas.user import UserResponse, MobileUserResponse
from app.models.user import User
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

@router.post("/login-json", response_model=LoginResponse)
async def login_json(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON compatible login endpoint for frontend applications
    """
    # Get user by email
    email = login_data.email
    user = AuthService.get_user_by_email(db, email)
    
    if not user or not verify_password(login_data.password, getattr(user, "hashed_password")):
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Check if user is active
    is_active = getattr(user, "is_active")
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    setattr(user, "last_login", datetime.now(timezone.utc))
    db.commit()
    
    # Create user info
    user_info = UserInfo(
        id=getattr(user, "id"),
        name=getattr(user, "name") or "",
        email=getattr(user, "email"),
        username=getattr(user, "username"),
        is_active=getattr(user, "is_active"),
        position=getattr(user, "position"),
        employee_id=getattr(user, "employee_id"),
        phone=getattr(user, "phone"),
        address=getattr(user, "address"),
        profile_picture=getattr(user, "profile_picture"),
        additional_data=getattr(user, "additional_data"),
        last_login=getattr(user, "last_login")
    )
    
    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
        "token_type": "bearer",
        "user": user_info,
        "message": "Login successful",
        "status": "success"
    }

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user with username, email, password and optional face image
    """
    # Check if username already exists
    if AuthService.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if AuthService.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    face_encoding = None
    if user_data.face_image:
        try:
            # Process face image
            face_service = FaceRecognitionService()
            face_encoding = face_service.process_face_image(user_data.face_image)
            
            if face_encoding is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No face detected in the image"
                )
        except Exception as e:
            logger.error(f"Error processing face image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing face image: {str(e)}"
            )

    # Create new user
    try:
        user = AuthService.create_user(
            db=db,
            user_data=user_data,
            face_encoding=face_encoding
        )
        
        # Create access token
        access_token = create_access_token(user.username)
        refresh_token = create_refresh_token(user.username)
        
        # Update last login
        setattr(user, "last_login", datetime.now(timezone.utc))
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    Uses email as the login identifier instead of username
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we'll treat it as email
    email = form_data.username
    
    # Authenticate with email instead of username
    user = AuthService.get_user_by_email(db, email)
    
    if not user or not verify_password(form_data.password, getattr(user, "hashed_password")):
        logger.warning(f"Failed login attempt for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    is_active = getattr(user, "is_active")
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    setattr(user, "last_login", datetime.now(timezone.utc))
    db.commit()
    
    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
        "token_type": "bearer"
    }


@router.post("/face-login", response_model=Token)
async def face_login(
    login_data: FaceLoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Login using face recognition
    """
    # Get user by username or email
    user = None
    if login_data.username:
        user = AuthService.get_user_by_username(db, login_data.username)
    elif login_data.email:
        user = AuthService.get_user_by_email(db, login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    face_encoding = getattr(user, "face_encoding")
    if not face_encoding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face registered for this user"
        )
    
    is_active = getattr(user, "is_active")
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    try:
        # Verify face
        face_service = FaceRecognitionService()
        is_match, confidence = face_service.verify_face(
            stored_encoding=getattr(user, "face_encoding"),
            new_image_data=bytes(login_data.face_image, 'utf-8')
        )
        
        if not is_match:
            logger.warning(f"Failed face login attempt for user: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Face verification failed"
            )
        
        # Update last login
        setattr(user, "last_login", datetime.now(timezone.utc))
        db.commit()
        
        return {
            "access_token": create_access_token(user.username),
            "refresh_token": create_refresh_token(user.username),
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error in face login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing face verification"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        username: str = str(sub)
        
        user = AuthService.get_user_by_username(db, username)
        is_active = user and getattr(user, "is_active")
        if not user or not is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return {
            "access_token": create_access_token(username),
            "refresh_token": create_refresh_token(username),
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    email: EmailStr = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset for user (sends email with reset token)
    """
    user = AuthService.get_user_by_email(db, email)
    if user:
        # In a real app, send an email with reset token
        # For this example, we'll just log it
        reset_token = create_password_reset_token(email)
        logger.info(f"Password reset requested for {email}. Token: {reset_token}")
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password(
    password_data: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset password using reset token
    """
    try:
        email = verify_password_reset_token(password_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        user = AuthService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        AuthService.update_user_password(db, user, password_data.new_password)
        return {"message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error resetting password"
        )


@router.post("/password-change", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change user password (requires authentication)
    """
    if not verify_password(password_data.current_password, getattr(current_user, "hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    AuthService.update_user_password(db, current_user, password_data.new_password)
    return {"message": "Password updated successfully"} 


@router.post("/validate-token")
async def validate_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    Validate access token and return user information if valid
    Accepts token from Authorization header in format 'Bearer {token}'
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"success": False, "message": "Missing or invalid authorization header"}
    
    # Extract token from header
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub = payload.get("sub")
        token_type = payload.get("type")
        
        if sub is None or token_type != "access":
            return {"success": False, "message": "Invalid token"}
        
        username: str = str(sub)
            
        user = AuthService.get_user_by_username(db, username)
        if not user:
            return {"success": False, "message": "User not found"}
        
        is_active = getattr(user, "is_active")
        if not is_active:
            return {"success": False, "message": "User account is disabled"}
        
        # Create user info matching mobile app expectations
        user_info = {
            "id": getattr(user, "id"),
            "name": getattr(user, "name") or "",
            "email": getattr(user, "email"),
            "username": getattr(user, "username"),
            "is_active": getattr(user, "is_active"),
            "position": getattr(user, "position"),
            "employee_id": getattr(user, "employee_id"),
            "phone": getattr(user, "phone"),
            "address": getattr(user, "address"),
            "profile_picture": getattr(user, "profile_picture"),
            "additional_data": getattr(user, "additional_data"),
        }
        
        return {
            "success": True,
            "message": "Token is valid",
            "data": {
                "user": user_info
            }
        }
        
    except JWTError:
        return {"success": False, "message": "Invalid token"} 

