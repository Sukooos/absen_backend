from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import calendar

from app.models.attendance import Attendance, AttendanceType, AttendanceStatus
from app.schemas.attendance import AttendanceCreate, AttendanceStatistics, DailyAttendance
from app.core.logger import logger


class AttendanceService:
    """Service for attendance operations"""
    
    @staticmethod
    def create_attendance(
        db: Session,
        user_id: int,
        attendance_type: AttendanceType,
        confidence_score: Optional[float] = None,
        location: Optional[str] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Attendance:
        """Create a new attendance record"""
        db_attendance = Attendance(
            user_id=user_id,
            attendance_time=datetime.utcnow(),
            attendance_type=attendance_type,
            status=AttendanceStatus.VERIFIED,
            confidence_score=confidence_score,
            location=location,
            device_info=device_info,
            ip_address=ip_address,
            notes=notes
        )
        
        try:
            db.add(db_attendance)
            db.commit()
            db.refresh(db_attendance)
            logger.info(f"Attendance created for user {user_id}: {attendance_type}")
            return db_attendance
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating attendance: {str(e)}")
            raise
    
    @staticmethod
    def get_attendance_by_id(db: Session, attendance_id: int) -> Optional[Attendance]:
        """Get attendance by ID"""
        return db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    @staticmethod
    def get_user_attendances(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        attendance_type: Optional[AttendanceType] = None
    ) -> List[Attendance]:
        """Get attendance records for a user with filtering options"""
        query = db.query(Attendance).filter(Attendance.user_id == user_id)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(func.date(Attendance.attendance_time) >= start_date)
        if end_date:
            query = query.filter(func.date(Attendance.attendance_time) <= end_date)
        
        # Apply attendance type filter if provided
        if attendance_type:
            query = query.filter(Attendance.attendance_type == attendance_type)
        
        # Order by attendance time descending (most recent first)
        query = query.order_by(Attendance.attendance_time.desc())
        
        return query.all()
    
    @staticmethod
    def get_attendance_statistics(
        db: Session,
        user_id: int,
        month: int,
        year: int
    ) -> AttendanceStatistics:
        """Get attendance statistics for a user for a specific month"""
        # Get the number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Create date range for the month
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        
        # Get all attendance records for the month
        attendances = AttendanceService.get_user_attendances(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group attendances by date
        attendance_by_date = {}
        for attendance in attendances:
            att_date = attendance.attendance_time.date()
            if att_date not in attendance_by_date:
                attendance_by_date[att_date] = []
            attendance_by_date[att_date].append(attendance)
        
        # Initialize statistics
        total_days = days_in_month
        present_days = len(attendance_by_date)
        absent_days = total_days - present_days
        late_days = 0
        total_work_hours = 0
        daily_records = []
        
        # Process each day in the month
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            
            # Skip future dates
            if current_date > datetime.now().date():
                continue
                
            # Skip weekends (optional, based on requirements)
            if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                continue
                
            daily_record = DailyAttendance(date=current_date)
            
            if current_date in attendance_by_date:
                day_attendances = attendance_by_date[current_date]
                
                # Find check-in and check-out times
                check_in = next((a for a in day_attendances if a.attendance_type == AttendanceType.CHECK_IN), None)
                check_out = next((a for a in day_attendances if a.attendance_type == AttendanceType.CHECK_OUT), None)
                
                if check_in:
                    daily_record.check_in = check_in.attendance_time
                    
                    # Check if late (e.g., after 9:00 AM)
                    if check_in.attendance_time.hour > 9 or (check_in.attendance_time.hour == 9 and check_in.attendance_time.minute > 0):
                        late_days += 1
                        daily_record.status = "late"
                
                if check_out:
                    daily_record.check_out = check_out.attendance_time
                    
                # Calculate work time if both check-in and check-out exist
                if check_in and check_out:
                    work_minutes = (check_out.attendance_time - check_in.attendance_time).total_seconds() / 60
                    
                    # Subtract break time if available
                    break_start = next((a for a in day_attendances if a.attendance_type == AttendanceType.BREAK_START), None)
                    break_end = next((a for a in day_attendances if a.attendance_type == AttendanceType.BREAK_END), None)
                    
                    if break_start and break_end:
                        break_minutes = (break_end.attendance_time - break_start.attendance_time).total_seconds() / 60
                        daily_record.break_time = int(break_minutes)
                        work_minutes -= break_minutes
                    
                    daily_record.work_time = int(work_minutes)
                    total_work_hours += work_minutes / 60
            else:
                daily_record.status = "absent"
            
            daily_records.append(daily_record)
        
        # Calculate average work hours
        working_days = max(1, present_days)  # Avoid division by zero
        average_work_hours = total_work_hours / working_days
        
        return AttendanceStatistics(
            total_days=total_days,
            present_days=present_days,
            absent_days=absent_days,
            late_days=late_days,
            average_work_hours=round(average_work_hours, 2),
            total_work_hours=round(total_work_hours, 2),
            daily_records=daily_records,
            month=month,
            year=year
        )
    
    @staticmethod
    def update_attendance(
        db: Session,
        attendance_id: int,
        attendance_time: Optional[datetime] = None,
        attendance_type: Optional[AttendanceType] = None,
        status: Optional[AttendanceStatus] = None,
        notes: Optional[str] = None
    ) -> Optional[Attendance]:
        """Update an attendance record"""
        attendance = AttendanceService.get_attendance_by_id(db, attendance_id)
        if not attendance:
            return None
        
        if attendance_time is not None:
            attendance.attendance_time = attendance_time
        if attendance_type is not None:
            attendance.attendance_type = attendance_type
        if status is not None:
            attendance.status = status
        if notes is not None:
            attendance.notes = notes
        
        try:
            db.commit()
            db.refresh(attendance)
            logger.info(f"Attendance updated: {attendance_id}")
            return attendance
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating attendance: {str(e)}")
            raise
    
    @staticmethod
    def delete_attendance(db: Session, attendance_id: int) -> bool:
        """Delete an attendance record"""
        attendance = AttendanceService.get_attendance_by_id(db, attendance_id)
        if not attendance:
            return False
        
        try:
            db.delete(attendance)
            db.commit()
            logger.info(f"Attendance deleted: {attendance_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting attendance: {str(e)}")
            raise 