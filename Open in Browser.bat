@echo off
echo Opening Factory Brain in browser...
echo.
echo If server is not running, run "Run Factory Brain.bat" first
echo.
start http://localhost:8000
start http://localhost:8000/api/v1/health
start http://localhost:8000/docs
echo.
echo Opened:
echo   - http://localhost:8000
echo   - http://localhost:8000/api/v1/health
echo   - http://localhost:8000/docs
echo.
timeout /t 3
