from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# Base User Schema
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: Optional[bool] = True
    position: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    face_image: Optional[str] = None  # Base64 encoded image
    is_superuser: Optional[bool] = False
    
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


# Schema for updating a user
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=80)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    position: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    face_image: Optional[str] = None  # Base64 encoded image
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength if provided"""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


# Schema for user response
class UserResponse(UserBase):
    id: int
    uuid: str
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    has_face_encoding: bool = False
    
    class Config:
        orm_mode = True
        from_attributes = True


# Schema for mobile app response
class MobileUserResponse(BaseModel):
    id: int
    name: str
    email: str
    position: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


# Schema for attendance in user response
class AttendanceBrief(BaseModel):
    id: int
    attendance_time: datetime
    attendance_type: str
    status: str
    
    class Config:
        orm_mode = True
        from_attributes = True


# Schema for user with attendance
class UserWithAttendance(UserResponse):
    attendances: List[AttendanceBrief] = []
    
    class Config:
        orm_mode = True
        from_attributes = True 