from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Any, Union
from datetime import datetime
from app.schemas.user import UserBase


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)
    face_image: Optional[str] = None  # Base64 encoded image
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class UserInfo(BaseModel):
    """Schema for user information in login response"""
    id: int
    name: str
    email: str
    username: Optional[str] = None
    is_active: Optional[bool] = None
    position: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    additional_data: Optional[dict] = None
    last_login: Optional[datetime] = None


class LoginResponse(BaseModel):
    """Schema for login response with user information"""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserInfo
    message: str = "Login successful"
    status: str = "success"


class TokenPayload(BaseModel):
    """Schema for token payload"""
    sub: Optional[Union[str, Any]] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class PasswordReset(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
    
    @validator('new_password')
    def passwords_match(cls, v, values):
        """Ensure new password is different from current password"""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v


class FaceLoginRequest(BaseModel):
    """Schema for face login"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    face_image: str  # Base64 encoded image
    
    @validator('face_image')
    def validate_face_image(cls, v):
        """Validate face image is provided"""
        if not v:
            raise ValueError('Face image is required')
        return v
    
    @validator('username', 'email')
    def validate_identifier(cls, v, values):
        """Ensure either username or email is provided"""
        if not v and 'username' not in values and 'email' not in values:
            raise ValueError('Either username or email must be provided')
        return v 