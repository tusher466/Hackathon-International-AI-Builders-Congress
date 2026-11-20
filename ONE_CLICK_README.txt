Factory Brain - One Click Launcher - WINDOWS

To run full project in localhost with ONE CLICK:

1. Double-click: "Run Factory Brain.bat"
   - This will:
     * Check python and frontend build
     * Build frontend if dist missing
     * Train ML models if missing
     * Start backend server at http://localhost:8000
     * Backend serves BOTH frontend UI + API (single port)
     * Auto-opens browser to http://localhost:8000 after 5 seconds

2. Wait for console showing:
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000

3. Browser opens:
   - Frontend UI: http://localhost:8000
   - API: http://localhost:8000/api/v1/health
   - Docs: http://localhost:8000/docs

OTHER ONE-CLICK FILES:

- "Run Dev Mode.bat"
  * Starts backend at :8000 in new window
  * Starts frontend vite dev server at :3000 in new window
  * Frontend at :3000 proxies API to backend :8000
  * Good for development (hot reload)

- "Factory Brain Launcher.ps1"
  * PowerShell version of Run Factory Brain.bat
  * Right-click -> Run with PowerShell
  * More robust, colored output

- "Open in Browser.bat"
  * Just opens browser to localhost:8000 (server must already be running)

- "Stop Factory Brain.bat"
  * Kills processes on port 8000
  * Use if port already in use error

- "start_fullstack.py"
  * Python launcher: python start_fullstack.py
  * Same as .bat but python version

REQUIREMENTS:

- Python 3.11 or 3.12 installed and in PATH (check: py --version or python --version)
- Node.js + npm installed for frontend build (only needed first time)
  * Download from https://nodejs.org/
- If frontend/dist already exists, Node.js not required for running

FIRST TIME SETUP:

If you have never run before:
1. Double-click "Run Factory Brain.bat"
2. It will install frontend deps (npm install) and build (npm run build) - takes 1-2 minutes
3. It will train models (30 sec)
4. Then server starts

AFTER FIRST TIME:

Just double-click "Run Factory Brain.bat" again - it will start immediately (2-3 sec) because dist and models exist.

TROUBLESHOOTING:

- "Python not found": Install Python from python.org and check "Add to PATH"
- "Port 8000 already in use": Run "Stop Factory Brain.bat" then run again
- "Frontend dist not found": Run "Run Factory Brain.bat" will auto-build, or manually cd frontend && npm run build
- "No module named fastapi": Run pip install -r requirements.txt or py -3.12 -m pip install -r requirements.txt
- Browser shows "Demo data badge": Backend not reachable, check server console, fallback to mock mode. Ensure backend at :8000 is running.

PORTS:

- Merged mode: Single port 8000 serves everything
- Dev mode: Backend 8000 + Frontend 3000 (two ports)

STOPPING:

- Press Ctrl+C in the black console window
- Or double-click "Stop Factory Brain.bat"
- Or run in cmd: taskkill /F /IM python.exe

