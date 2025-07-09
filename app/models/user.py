from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class User(Base, TimestampMixin, UUIDMixin):
    """User model for authentication and identification"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    position = Column(String(100), nullable=True)
    employee_id = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    additional_data = Column(JSON, nullable=True)
    face_encoding = Column(LargeBinary, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>" 