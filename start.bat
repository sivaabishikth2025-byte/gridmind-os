@echo off
echo ============================================
echo   GridMind OS - Starting All Services
echo ============================================

echo.
echo [1/4] Starting Docker infrastructure (optional)...
docker compose up -d 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   Docker not available - using SQLite + in-memory fallback
)

echo.
echo [2/4] Starting Grid Simulator on :8001...
start "GridMind Simulator" cmd /k "cd /d %~dp0simulator && python -m uvicorn main:app --host 0.0.0.0 --port 8001"

timeout /t 3 /nobreak >nul

echo [3/4] Starting Backend API on :8100...
start "GridMind Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload"

timeout /t 5 /nobreak >nul

echo [4/4] Starting Frontend on :3002...
start "GridMind Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   GridMind OS is starting!
echo ============================================
echo   Command Center: http://localhost:3002
echo   API Docs:       http://localhost:8100/docs
echo   Simulator:      http://localhost:8001/docs
echo ============================================
pause
