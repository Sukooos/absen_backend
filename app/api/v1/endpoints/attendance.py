from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, date
from fastapi_pagination import Page, paginate

from app.database.database import get_db
from app.services.attendance_service import AttendanceService
from app.services.face_recognition_service import FaceRecognitionService
from app.core.security import get_current_active_user
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceVerify,
    AttendanceStatistics
)
from app.models.user import User
from app.models.attendance import AttendanceType, AttendanceStatus
from app.core.logger import logger

router = APIRouter()


@router.post("/verify", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def verify_attendance(
    attendance_data: AttendanceVerify,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user attendance with face recognition and record it
    """
    if not current_user.face_encoding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registered face found for this user"
        )

    try:
        # Verify face
        face_service = FaceRecognitionService()
        is_match, confidence = face_service.verify_face_from_base64(
            stored_encoding=current_user.face_encoding,
            base64_image=attendance_data.face_image
        )

        if not is_match:
            logger.warning(f"Face verification failed for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Face verification failed"
            )

        # Create attendance record
        attendance = AttendanceService.create_attendance(
            db=db,
            user_id=current_user.id,
            attendance_type=attendance_data.attendance_type,
            confidence_score=confidence,
            location=attendance_data.location,
            device_info=attendance_data.device_info,
            ip_address=attendance_data.ip_address
        )
        
        return attendance
    except Exception as e:
        logger.error(f"Error processing attendance verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing attendance verification: {str(e)}"
        )


@router.get("/history", response_model=Page[AttendanceResponse])
async def get_attendance_history(
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    attendance_type: Optional[AttendanceType] = Query(None, description="Filter by attendance type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get attendance history for the current user with filtering options
    """
    try:
        attendances = AttendanceService.get_user_attendances(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            attendance_type=attendance_type
        )
        
        return paginate(attendances)
    except Exception as e:
        logger.error(f"Error retrieving attendance history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving attendance history"
        )


@router.get("/statistics", response_model=AttendanceStatistics)
async def get_attendance_statistics(
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get attendance statistics for the current user
    """
    try:
        # Default to current month if not specified
        if month is None or year is None:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
            
        stats = AttendanceService.get_attendance_statistics(
            db=db,
            user_id=current_user.id,
            month=month,
            year=year
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error retrieving attendance statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving attendance statistics"
        )


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance(
    attendance_id: int = Path(..., description="The ID of the attendance record"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific attendance record by ID
    """
    attendance = AttendanceService.get_attendance_by_id(db, attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Ensure user can only access their own attendance records
    if attendance.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attendance record"
        )
    
    return attendance


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: int = Path(..., description="The ID of the attendance record to delete"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete an attendance record (admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete attendance records"
        )
    
    attendance = AttendanceService.get_attendance_by_id(db, attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    AttendanceService.delete_attendance(db, attendance_id)
    return None 