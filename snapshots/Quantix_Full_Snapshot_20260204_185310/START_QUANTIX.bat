@echo off
title QUANTIX AI CORE - CONTROL CENTER
echo ===================================================
echo    🚀 QUANTIX AI CORE: ACTIVATING SYSTEMS...
echo ===================================================
echo.
echo [+] Core Mode: Phase 3 Learning
echo [+] Polling Interval: 120s
echo.
start "MINER_ENGINE" cmd /k "cd /d backend && echo [MINER] Starting Heartbeat... && python -m quantix_core.api.main"
timeout /t 3 >nul
start "AUTO_EXECUTOR" cmd /k "cd /d ..\Quantix_MPV\quantix-live-execution && echo [AUTO] Starting Scheduler... && python auto_scheduler.py"
echo.
echo [CHECK] All windows launched.
echo [CHECK] View results at: https://9dpi.github.io/quantix-ai-core/dashboard/
echo.
echo Press any key to close this Control Center window...
pause >nul