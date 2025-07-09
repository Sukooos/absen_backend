from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.attendance import AttendanceType, AttendanceStatus


class AttendanceBase(BaseModel):
    """Base schema for attendance"""
    attendance_type: AttendanceType = Field(..., description="Type of attendance record")
    notes: Optional[str] = Field(None, max_length=500)


class AttendanceCreate(AttendanceBase):
    """Schema for creating attendance records"""
    user_id: int
    attendance_time: Optional[datetime] = None
    status: Optional[AttendanceStatus] = AttendanceStatus.VERIFIED
    confidence_score: Optional[float] = None
    location: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None


class AttendanceVerify(BaseModel):
    """Schema for verifying attendance with face recognition"""
    face_image: str = Field(..., description="Base64 encoded image")
    attendance_type: AttendanceType = Field(..., description="Type of attendance record")
    location: Optional[str] = Field(None, description="Location coordinates or description")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('face_image')
    def validate_face_image(cls, v):
        """Validate face image is provided"""
        if not v:
            raise ValueError('Face image is required')
        return v


class AttendanceResponse(BaseModel):
    """Schema for attendance response"""
    id: int
    uuid: str
    user_id: int
    attendance_time: datetime
    attendance_type: AttendanceType
    status: AttendanceStatus
    confidence_score: Optional[float] = None
    location: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class AttendanceUpdate(BaseModel):
    """Schema for updating attendance records"""
    attendance_time: Optional[datetime] = None
    attendance_type: Optional[AttendanceType] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = Field(None, max_length=500)


class DailyAttendance(BaseModel):
    """Schema for daily attendance summary"""
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    break_time: Optional[int] = None  # Break time in minutes
    work_time: Optional[int] = None   # Work time in minutes
    status: str = "present"           # present, absent, late, etc.


class AttendanceStatistics(BaseModel):
    """Schema for attendance statistics"""
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    average_work_hours: float
    total_work_hours: float
    daily_records: List[DailyAttendance]
    month: int
    year: int 