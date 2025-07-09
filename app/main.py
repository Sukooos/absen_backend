from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import add_pagination
from loguru import logger
import time
import os
from app.api.v1.router import api_router
from app.core.config import settings
from app.database.database import init_db

# Configure logger
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time} {level} {message}",
    backtrace=True,
    diagnose=True,
)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request processing time middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            logger.info(f"Request processed in {process_time:.4f}s: {request.method} {request.url}")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed in {process_time:.4f}s: {request.method} {request.url} - {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    # Global exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()}
        )

    # Include all routers
    app.include_router(api_router)

    # Add pagination support
    add_pagination(app)

    # Create startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up application...")
        # Create database tables
        init_db()
        logger.info("Database initialized")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application...")

    return app

app = create_app()

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Attendance System API",
        "version": settings.PROJECT_VERSION,
        "documentation": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )