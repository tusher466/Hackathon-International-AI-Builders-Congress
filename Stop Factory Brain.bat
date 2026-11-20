@echo off
title Factory Brain - Stop Server
color 0C
echo ============================================================
echo   Stopping Factory Brain Server
echo ============================================================
echo.

echo Checking port 8000...
netstat -ano | findstr :8000
echo.

echo Attempting to kill Python processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo Also killing all Python uvicorn processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq FactoryBrain*" >nul 2>&1
:: Safer: kill by command line contains uvicorn
wmic process where "name='python.exe' and CommandLine like '%%uvicorn%%'" delete >nul 2>&1

echo.
echo Checking if port 8000 is now free...
netstat -ano | findstr :8000
if %errorlevel% equ 0 (
    echo WARNING: Port 8000 still in use
) else (
    echo SUCCESS: Port 8000 is free
)

echo.
echo Done.
pause
