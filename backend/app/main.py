"""
========================================================================================
VisionCare AI: FastAPI Main Application Gateway
========================================================================================
"""

import os
import torch

# Bound PyTorch CPU threads for predictable performance in cloud environments
torch.set_num_threads(2)

def trim_memory():
    """Forces Linux kernel to release free heap pages back to the OS."""
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass

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

frontend_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "out"))
if os.path.exists(frontend_out):
    next_assets = os.path.join(frontend_out, "_next")
    if os.path.exists(next_assets):
        app.mount("/_next", StaticFiles(directory=next_assets), name="next_assets")
    samples_dir = os.path.join(frontend_out, "samples")
    if os.path.exists(samples_dir):
        app.mount("/samples", StaticFiles(directory=samples_dir), name="samples")


@app.api_route("/health", methods=["GET", "HEAD"], tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "pipeline": "ACTIVE"
    }


@app.api_route("/api", methods=["GET", "HEAD"], tags=["System"])
def api_info():
    return {
        "message": "Welcome to VisionCare AI Radiology Workstation API.",
        "documentation": "/docs",
        "health": "/health"
    }


@app.api_route("/", methods=["GET", "HEAD"], tags=["Workstation"], include_in_schema=False)
@app.api_route("/workstation", methods=["GET", "HEAD"], tags=["Workstation"], include_in_schema=False)
def serve_workstation():
    frontend_index = os.path.join(frontend_out, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index, media_type="text/html")
    html_path = os.path.join(os.path.dirname(__file__), "static", "workstation.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return JSONResponse({"message": "VisionCare AI Workstation API ready."})
