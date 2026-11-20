@echo off
title Factory Brain - Dev Mode (Backend + Frontend Separate)
color 0B
echo ============================================================
echo   Factory Brain - Dev Mode
echo   Backend at :8000 + Frontend Dev Server at :3000
echo ============================================================
echo.

cd /d "%~dp0"

:: Check if frontend exists
if not exist "frontend\package.json" (
    echo ERROR: frontend\package.json not found
    pause
    exit /b 1
)

echo Starting Backend in new window...
start "FactoryBrain Backend :8000" cmd /k "cd /d %~dp0 && py -3.12 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server in new window...
start "FactoryBrain Frontend :3000" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Both servers starting...
echo   Backend : http://localhost:8000
echo   Frontend Dev : http://localhost:3000 (proxies API to backend)
echo.
echo Opening browsers in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:8000
start http://localhost:3000

echo.
echo Dev mode running in separate windows.
echo Close those windows or press Ctrl+C in them to stop.
echo.
pause
