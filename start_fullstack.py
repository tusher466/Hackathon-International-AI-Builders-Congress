#!/usr/bin/env python3
"""
Full-stack launcher for Factory Brain merged project.
- Checks frontend dist exists, builds if missing (requires npm)
- Trains models if missing
- Ingests docs if vector store empty
- Starts uvicorn with frontend serving
"""
import pathlib
import subprocess
import sys
import os

ROOT = pathlib.Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
FONTEND_DIST = ROOT / "Fontend" / "dist"
FRONTEND_DIST = FRONTEND_DIR / "dist"

def check_frontend():
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        print(f"✅ Frontend dist found at {FRONTEND_DIST}")
        return True
    if FONTEND_DIST.exists() and (FONTEND_DIST / "index.html").exists():
        print(f"✅ Legacy frontend dist found at {FONTEND_DIST}")
        return True
    print("⚠️ Frontend dist not found, attempting to build...")
    if not FRONTEND_DIR.exists():
        print("❌ frontend/ folder not found, cannot build")
        return False
    # Try npm build
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    try:
        print("Running npm install in frontend/")
        subprocess.run([npm_cmd, "install"], cwd=FRONTEND_DIR, check=True)
        print("Running npm run build in frontend/")
        subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR, check=True)
        print("✅ Frontend built")
        return True
    except Exception as e:
        print(f"❌ Frontend build failed: {e}")
        print("Continuing without frontend (API only mode)")
        return False

def check_models():
    models_dir = ROOT / "models"
    if not models_dir.exists() or not any(models_dir.glob("*.joblib")):
        print("⚠️ Models not found, training synthetic models...")
        try:
            subprocess.run([sys.executable, "scripts/train_models.py", "--models-dir", "./models"], cwd=ROOT, check=True)
            print("✅ Models trained")
        except Exception as e:
            print(f"⚠️ Auto-train failed (will auto-train on startup): {e}")
    else:
        print(f"✅ Models found in {models_dir}")

def main():
    print("=== Factory Brain Full-Stack Launcher ===")
    check_frontend()
    check_models()
    
    print("\n🚀 Starting backend (serves frontend at http://localhost:8000)...")
    print("   API health: http://localhost:8000/api/v1/health")
    print("   Docs: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    print("")
    
    # Run uvicorn
    try:
        import uvicorn
        uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
    except ImportError:
        print("uvicorn not installed, trying python -m uvicorn")
        subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()
