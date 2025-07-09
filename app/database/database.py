from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from decouple import config
from loguru import logger
from contextlib import contextmanager
from typing import Generator

# Load environment variables
DATABASE_URL = config("DATABASE_URL", default="mysql+pymysql://root:@localhost:3306/attendance_db")
DB_POOL_SIZE = config("DB_POOL_SIZE", cast=int, default=5)
DB_MAX_OVERFLOW = config("DB_MAX_OVERFLOW", cast=int, default=10)
DB_POOL_TIMEOUT = config("DB_POOL_TIMEOUT", cast=int, default=30)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    str(DATABASE_URL),
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def init_db() -> None:
    """Initialize database tables"""
    try:
        # Import all models here to ensure they are registered with Base
        from app.models.user import User
        from app.models.attendance import Attendance
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db() -> Generator:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_transaction():
    """Context manager for database transactions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction error: {str(e)}")
        raise
    finally:
        db.close() 