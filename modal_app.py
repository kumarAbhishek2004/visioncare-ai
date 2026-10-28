"""
==============================================================================
VisionCare AI: Modal.com Production Serverless Deployment
==============================================================================
Features:
- 8 GB RAM · 2 Dedicated vCPUs · CPU PyTorch
- Lightning-fast cold start (~2s)
- Permanent 24/7 public HTTPS endpoint
- 100% Free under Modal's $30/month monthly grant
==============================================================================
"""

import os
import modal

from dotenv import load_dotenv

# Load local .env for secret hydration
load_dotenv()

# 1. Initialize Modal App
app = modal.App("visioncare-radiology")

# 2. Build production Debian container image
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "curl")
    .pip_install(
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        index_url="https://download.pytorch.org/whl/cpu"
    )
    .pip_install(
        "fastapi>=0.115.0",
        "uvicorn>=0.31.0",
        "pydantic>=2.10.0",
        "pydantic-settings>=2.7.0",
        "python-multipart>=0.0.20",
        "opencv-python-headless>=4.8.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
        "openai>=1.50.0",
        "httpx>=0.27.0",
        "python-dotenv>=1.0.0",
        "reportlab>=4.0.0"
    )
    .add_local_dir("ml", remote_path="/root/ml")
    .add_local_dir("backend", remote_path="/root/backend")
    .add_local_dir("pretrained", remote_path="/root/pretrained")
)

# Build secrets list safely from .env so no credentials are committed to Git
secrets_dict = {
    "CORS_ALLOW_ALL": "true",
    "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b"),
    "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"),
}
for key in ["GROQ_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
    val = os.getenv(key)
    if val:
        secrets_dict[key] = val

# 3. Define the FastAPI ASGI web application with 8 GB RAM
@app.function(
    image=image,
    memory=8192,  # 8 GB RAM (eliminates all 512MB memory limits)
    cpu=2.0,      # 2 dedicated vCPUs for fast inference
    timeout=120,
    secrets=[
        modal.Secret.from_dict(secrets_dict)
    ]
)
@modal.asgi_app()
def fastapi_app():
    import sys
    # Add application root to Python import path
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    os.chdir("/root")

    from backend.app.main import app as web_app
    return web_app
