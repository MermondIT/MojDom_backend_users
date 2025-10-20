"""
MòjDom API - Main application entry point
FastAPI application for real estate rental mobile app
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.routers import api, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title="MòjDom API",
    description="API for real estate rental mobile application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(public.router, prefix="/public", tags=["public"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": settings.app_name, "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True
    )
