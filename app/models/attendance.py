from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.database import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class AttendanceType(str, enum.Enum):
    """Enum for attendance types"""
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class AttendanceStatus(str, enum.Enum):
    """Enum for attendance verification status"""
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    MANUAL = "manual"


class Attendance(Base, TimestampMixin, UUIDMixin):
    """Attendance model for tracking user check-ins and check-outs"""
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    attendance_time = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    attendance_type = Column(Enum(AttendanceType), nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.VERIFIED, nullable=False)
    confidence_score = Column(Float, nullable=True)
    location = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="attendances")

    def __repr__(self):
        return f"<Attendance {self.id}: {self.user_id} - {self.attendance_type} at {self.attendance_time}>" 