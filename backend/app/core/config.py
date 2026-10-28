"""
========================================================================================
VisionCare AI: Backend Configuration Settings
========================================================================================
"""

import os
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "VisionCare AI - Radiology Workstation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://visioncare-ai.vercel.app",
        "https://visioncare-ai-oqot.onrender.com",
        "*"
    ]

    # Directories
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    PRETRAINED_DIR: str = os.path.join(BASE_DIR, "pretrained")
    STORAGE_DIR: str = os.path.join(BASE_DIR, "backend", "storage")

    # API Keys & LLM Configuration
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "")  # Custom endpoint for OSS models (OpenRouter, Groq, Ollama, vLLM)
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-oss-120b")

    class Config:
        case_sensitive = True
        extra = "ignore"



settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
