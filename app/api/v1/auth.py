from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from app.database.database import get_db
from app.services.v1.auth_service import AuthService
from app.services.v1.face_recognition_service import FaceRecognitionService
from pydantic import BaseModel
import base64
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    face_image: Optional[str] = None  # Base64 encoded image

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    face_encoding = None
    if user.face_image:
        try:
            # Decode base64 image
            image_data = base64.b64decode(user.face_image)
            
            # Initialize face recognition service
            face_service = FaceRecognitionService()
            
            # Preprocess and extract face encoding
            processed_image = face_service.preprocess_image(image_data)
            face_encoding = face_service.extract_face_encoding(processed_image)
            
            if face_encoding is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No face detected in the image"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing face image: {str(e)}"
            )

    # Create new user
    user_db = AuthService.create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password,
        face_encoding=face_encoding.tobytes() if face_encoding is not None else None
    )

    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user 