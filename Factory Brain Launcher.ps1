# Factory Brain - Full Stack PowerShell Launcher
# Double-click this file (or right-click Run with PowerShell) to start full project

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Factory Brain - AI Operations Layer - Full Stack" -ForegroundColor Cyan
Write-Host "  Merged Backend + Frontend - PowerShell Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "Working directory: $scriptDir" -ForegroundColor Yellow

# Check Python
Write-Host "`n[1/4] Checking Python..." -ForegroundColor Yellow
$pythonCmd = $null
try {
    $null = Get-Command "py" -ErrorAction Stop
    $pyVersion = & py -3.12 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = "py -3.12"
        Write-Host "Found Python: $pyVersion via py launcher" -ForegroundColor Green
    }
} catch {}
if (-not $pythonCmd) {
    try {
        $null = Get-Command "python" -ErrorAction Stop
        $pyVersion = & python --version 2>&1
        $pythonCmd = "python"
        Write-Host "Found Python: $pyVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Python not found. Install Python 3.11+ from https://www.python.org/" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check frontend dist
Write-Host "`n[2/4] Checking frontend build..." -ForegroundColor Yellow
$frontendDist = Join-Path $scriptDir "frontend\dist\index.html"
$legacyDist = Join-Path $scriptDir "Fontend\dist\index.html"
if (Test-Path $frontendDist) {
    Write-Host "Frontend dist found at frontend\dist" -ForegroundColor Green
} elseif (Test-Path $legacyDist) {
    Write-Host "Frontend dist found at Fontend\dist (legacy)" -ForegroundColor Green
} else {
    Write-Host "Frontend dist NOT found - Building..." -ForegroundColor Yellow
    $frontendPath = Join-Path $scriptDir "frontend"
    if (Test-Path (Join-Path $frontendPath "package.json")) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        Set-Location $frontendPath
        & npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "npm install failed" -ForegroundColor Red
            Set-Location $scriptDir
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Host "Building..." -ForegroundColor Yellow
        & npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Build failed" -ForegroundColor Red
            Set-Location $scriptDir
            Read-Host "Press Enter to exit"
            exit 1
        }
        Set-Location $scriptDir
        Write-Host "Copying to legacy folder..." -ForegroundColor Yellow
        if (Test-Path "frontend\dist") {
            if (Test-Path "Fontend\dist") { Remove-Item -Recurse -Force "Fontend\dist" }
            Copy-Item -Recurse -Force "frontend\dist" "Fontend\dist"
        }
    } else {
        Write-Host "frontend folder not found, API only mode" -ForegroundColor Yellow
    }
}

# Check models
Write-Host "`n[3/4] Checking ML models..." -ForegroundColor Yellow
$modelsPath = Join-Path $scriptDir "models\anomaly_secom.joblib"
if (-not (Test-Path $modelsPath)) {
    Write-Host "Models not found - Training..." -ForegroundColor Yellow
    & $pythonCmd.Split()[0] $pythonCmd.Split()[1..2] scripts\train_models.py --models-dir ./models
} else {
    Write-Host "Models found" -ForegroundColor Green
}

# Start server
Write-Host "`n[4/4] Starting server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend will serve:" -ForegroundColor Cyan
Write-Host "  - Frontend UI at: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Health at: http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host "  - Swagger Docs at: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - WebSocket at: ws://localhost:8000/ws/live" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser in 5 seconds..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start browser opener job
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:8000"
    Write-Host "Browser opened"
} | Out-Null

# Run uvicorn
Write-Host "Starting uvicorn..." -ForegroundColor Green
# Build command
$cmdParts = $pythonCmd.Split()
if ($cmdParts.Count -eq 1) {
    & $cmdParts[0] -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level info
} else {
    & $cmdParts[0] $cmdParts[1] -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level info
}

Write-Host "`nServer stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
