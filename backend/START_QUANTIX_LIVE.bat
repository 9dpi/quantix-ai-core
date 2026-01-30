@echo off
TITLE Quantix AI Core - Launcher
COLOR 0A

echo ===============================================================================
echo   QUANTIX AI CORE v2 - LIVE SYSTEM LAUNCHER
echo ===============================================================================
echo.
echo   [1] Activating Python 3.11 Virtual Environment...
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo   [ERROR] Virtual environment not found! Please run setup first.
    pause
    exit
)

echo   [2] Starting SIGNAL WATCHER (The Goalkeeper)...
start "Quantix Watcher (Do Not Close)" cmd /k "color 0B && title Quantix Watcher && echo Starting Watcher... && python run_signal_watcher.py"

echo   [3] Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo   [4] Starting CONTINUOUS ANALYZER (The Striker)...
start "Quantix Analyzer (Do Not Close)" cmd /k "color 0E && title Quantix Analyzer && echo Starting Live Analyzer... && python -m quantix_core.engine.continuous_analyzer"

echo.
echo ===============================================================================
echo   ✅ SYSTEM STARTED SUCCESSFULLY
echo   ---------------------------------------------------------------------------
echo   - Watcher window: Monitor active trades (TP/SL)
echo   - Analyzer window: Scanning market for new signals
echo.
echo   ⚠️  DO NOT CLOSE THE POPUP WINDOWS! (Minimize them is OK)
echo ===============================================================================
pause
