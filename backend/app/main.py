"""
========================================================================================
VisionCare AI: FastAPI Main Application Gateway
========================================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Explainable AI-Assisted Radiology Workstation & Decision Support API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "pipeline": "ACTIVE"
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to VisionCare AI Radiology Workstation API.",
        "documentation": "/docs",
        "health": "/health"
    }
