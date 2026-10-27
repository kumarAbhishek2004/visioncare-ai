import os
import sys
import uvicorn

# Ensure project root is in sys.path regardless of current working directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if __name__ == "__main__":
    print(f"[*] VisionCare AI: Starting backend server from {ROOT_DIR} ...")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir=ROOT_DIR
    )
