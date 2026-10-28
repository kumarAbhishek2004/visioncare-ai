"""
========================================================================================
VisionCare AI: FastAPI Main Application Gateway
========================================================================================
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.app.core.config import settings
from backend.app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Explainable AI-Assisted Radiology Workstation & Decision Support API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware: allow web deployments (e.g. Vercel, Netlify) to access the API smoothly
cors_origins = list(settings.CORS_ORIGINS)
allow_all = "*" in cors_origins or os.environ.get("CORS_ALLOW_ALL", "true").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "pipeline": "ACTIVE"
    }


@app.get("/api", tags=["System"])
def api_info():
    return {
        "message": "Welcome to VisionCare AI Radiology Workstation API.",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/", tags=["Workstation"], include_in_schema=False)
@app.get("/workstation", tags=["Workstation"], include_in_schema=False)
def serve_workstation():
    html_path = os.path.join(os.path.dirname(__file__), "static", "workstation.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return JSONResponse({"message": "VisionCare AI Workstation API ready."})
