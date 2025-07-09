from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.v1.face_recognition_service import FaceRecognitionService
from app.api.v1.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
import base64
from datetime import datetime, timezone

router = APIRouter()

class AttendanceVerify(BaseModel):
    face_image: str  # Base64 encoded image

@router.post("/verify-attendance")
async def verify_attendance(
    attendance: AttendanceVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.face_encoding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registered face found for this user"
        )

    try:
        # Decode base64 image
        image_data = base64.b64decode(attendance.face_image)
        
        # Initialize face recognition service
        face_service = FaceRecognitionService()
        
        # Preprocess the new image
        processed_image = face_service.preprocess_image(image_data)
        
        # Verify face
        is_match, confidence = face_service.verify_face(
            stored_encoding=current_user.face_encoding.tobytes(),
            new_image_data=processed_image
        )

        if not is_match:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Face verification failed"
            )

        # Here you would typically record the attendance in your database
        # For this example, we'll just return a success message
        return {
            "status": "success",
            "message": "Attendance verified successfully",
            "timestamp": datetime.now(timezone.utc),
            "confidence": confidence
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing face verification: {str(e)}"
        )

@router.get("/attendance-history")
async def get_attendance_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Here you would typically query your attendance records
    # For this example, we'll just return a placeholder
    return {
        "message": "Attendance history feature will be implemented soon",
        "user_id": current_user.id
    }
