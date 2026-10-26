"""
========================================================================================
VisionCare AI: API v1 Router Registration
========================================================================================
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import analyze

api_router = APIRouter()
api_router.include_router(analyze.router, prefix="/studies", tags=["Radiology Studies"])
