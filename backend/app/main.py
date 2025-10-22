"""
LetterOn Server - FastAPI Application Entry Point
Purpose: Main application setup, middleware, route registration
Testing: uvicorn app.main:app --reload
AWS Deployment: Entry point for ECS/Lambda deployment

This is the main FastAPI application that:
- Configures CORS and middleware
- Registers all API routes
- Sets up background tasks for reminder scheduling
- Provides health check endpoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from app.settings import settings
from app.utils.logger import setup_logging
from app.services.reminder_scheduler import start_reminder_scheduler, stop_reminder_scheduler

# Import API routers
from app.api import auth, letters, chat, search, reminders


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events.
    Starts the reminder scheduler on startup and stops it on shutdown.
    """
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Start reminder scheduler
    if settings.environment != "test":
        start_reminder_scheduler()
        logger.info("Reminder scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down application")
    if settings.environment != "test":
        stop_reminder_scheduler()
        logger.info("Reminder scheduler stopped")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for LetterOn - AI-powered physical letter management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error messages."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Register API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(letters.router, prefix="/letters", tags=["Letters"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])


# Log registered routes on startup
@app.on_event("startup")
async def log_routes():
    """Log all registered routes for debugging."""
    if settings.debug:
        logger.debug("Registered routes:")
        for route in app.routes:
            if hasattr(route, "methods"):
                logger.debug(f"  {', '.join(route.methods)} {route.path}")


# For AWS Lambda deployment (optional)
# Uncomment if deploying to Lambda with Mangum
# from mangum import Mangum
# handler = Mangum(app)
