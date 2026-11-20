@echo off
title Factory Brain - Full Stack Launcher
color 0A
echo ============================================================
echo   Factory Brain - AI Operations Layer - Full Stack
echo   Merged Backend + Frontend - One Click Launcher
echo ============================================================
echo.

:: Change to script directory
cd /d "%~dp0"
echo Working directory: %CD%
echo.

:: Check Python
echo [1/4] Checking Python...
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python not found. Please install Python 3.11 or 3.12
        echo Download from https://www.python.org/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python
    )
) else (
    set PYTHON_CMD=py -3.12
)
echo Python found: %PYTHON_CMD%
%PYTHON_CMD% --version

:: Check frontend dist
echo.
echo [2/4] Checking frontend build...
if exist "frontend\dist\index.html" (
    echo Frontend dist found at frontend\dist
) else if exist "Fontend\dist\index.html" (
    echo Frontend dist found at Fontend\dist (legacy)
) else (
    echo Frontend dist NOT found - Building...
    if exist "frontend\package.json" (
        echo Installing frontend dependencies...
        cd frontend
        call npm install
        if %errorlevel% neq 0 (
            echo ERROR: npm install failed
            cd ..
            pause
            exit /b 1
        )
        echo Building frontend...
        call npm run build
        if %errorlevel% neq 0 (
            echo ERROR: frontend build failed
            cd ..
            pause
            exit /b 1
        )
        cd ..
        echo Copying to legacy folder...
        if exist "frontend\dist" (
            if exist "Fontend\dist" rmdir /s /q "Fontend\dist"
            xcopy /s /e /i /y "frontend\dist" "Fontend\dist" >nul
        )
    ) else (
        echo WARNING: frontend folder not found, will run API only mode
    )
)

:: Check models
echo.
echo [3/4] Checking ML models...
if not exist "models\anomaly_secom.joblib" (
    echo Models not found - Training (takes ~30 sec)...
    %PYTHON_CMD% scripts\train_models.py --models-dir ./models
    if %errorlevel% neq 0 (
        echo WARNING: Model training failed, will auto-train on startup
    )
) else (
    echo Models found
)

:: Start server in background and open browser
echo.
echo [4/4] Starting server...
echo.
echo Backend will serve:
echo   - Frontend UI at: http://localhost:8000
echo   - API Health at: http://localhost:8000/api/v1/health
echo   - Swagger Docs at: http://localhost:8000/docs
echo   - WebSocket at: ws://localhost:8000/ws/live
echo.
echo Opening browser in 5 seconds...
echo Press Ctrl+C to stop server
echo.

:: Start browser opener in background after delay
start /B cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8000 && echo Browser opened at http://localhost:8000"

:: Run uvicorn in foreground (blocks, shows logs)
echo Starting uvicorn server...
echo.
%PYTHON_CMD% -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level info

:: If uvicorn exits, pause
echo.
echo Server stopped.
pause
