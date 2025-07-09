from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to models"""
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)


class UUIDMixin:
    """Mixin for adding a UUID field to models"""
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)


class SoftDeleteMixin:
    """Mixin for adding soft delete capability to models"""
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """Mark record as deleted"""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None 