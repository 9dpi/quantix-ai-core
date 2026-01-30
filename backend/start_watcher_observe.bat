@echo off
echo ============================================================
echo GATE 3 - SIGNAL WATCHER (OBSERVE MODE)
echo ============================================================
echo.
echo Setting environment variables...
set WATCHER_OBSERVE_MODE=true
set WATCHER_CHECK_INTERVAL=60
echo   WATCHER_OBSERVE_MODE=%WATCHER_OBSERVE_MODE%
echo   WATCHER_CHECK_INTERVAL=%WATCHER_CHECK_INTERVAL%
echo.
echo Starting watcher...
echo.
python run_signal_watcher.py
