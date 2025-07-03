from fastapi import FastAPI
from app.api.v1 import absensi

app = FastAPI(
    title="Absensi API",
    version="1.0.0",
)

app.include_router(absensi.router, prefix="/api/v1/absensi", tags=["absensi"])