from fastapi import APIRouter, UploadFile, File
from app.services.v1.absensi_service import verify_face

router = APIRouter()

@router.post("/verify-face/")
async def verify_face_endpoint(img1: UploadFile = File(...), img2: UploadFile = File(...)):
    result = await verify_face(img1, img2)
    return result
