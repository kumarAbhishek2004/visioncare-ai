# ==============================================================================
# VisionCare AI: High-Performance Python Backend for Hugging Face Spaces
# 16GB RAM · 2 vCPUs · CPU PyTorch · Port 7860
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    APP_HOME=/home/user/app

# Install system dependencies for OpenCV and image operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces security: non-root user with UID 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $APP_HOME

# Install PyTorch CPU first for fast image layer caching
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML engine, API gateway, and pretrained weights
COPY --chown=user:user ml/ ./ml/
COPY --chown=user:user backend/ ./backend/
COPY --chown=user:user pretrained/ ./pretrained/

# Expose standard port for Hugging Face Spaces
EXPOSE 7860

# Health check to ensure service readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Launch ASGI server on $PORT (defaults to 7860 on Hugging Face Spaces)
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
