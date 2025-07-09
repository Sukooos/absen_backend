from fastapi import APIRouter
from app.api.v1.endpoints import auth, attendance, users

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(users.router, prefix="/users", tags=["Users"]) 