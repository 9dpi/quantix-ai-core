@echo off
TITLE Quantix Validation Layer - Production Observer [Phase 4]
COLOR 0A

echo ================================================================================
echo   PEPPERSTONE VALIDATION LAYER — PRODUCTION OBSERVER   [Phase 4]
echo ================================================================================
echo.
echo   Architecture : PASSIVE OBSERVER (zero impact on main system)
echo   Deploy mode  : %VALIDATOR_FEED%
echo.
echo   Feed options (set VALIDATOR_FEED env or choose below):
echo     1. binance_proxy  — Binance REST API proxy [DEFAULT, always works]
echo     2. mt5_api        — MetaTrader 5 real Pepperstone feed [Recommended Phase 2A]
echo     3. ctrader_api    — cTrader Open API [Phase 2B stub]
echo.
echo ================================================================================

:: ── Choose feed if not set via environment ──────────────────────────────────
if not defined VALIDATOR_FEED (
    echo.
    set /p FEED_CHOICE="  Select feed [1/2/3, default=1]: "
    if "%FEED_CHOICE%"=="2" (
        set VALIDATOR_FEED=mt5_api
    ) else if "%FEED_CHOICE%"=="3" (
        set VALIDATOR_FEED=ctrader_api
    ) else (
        set VALIDATOR_FEED=binance_proxy
    )
)

echo.
echo   [+] Feed source     : %VALIDATOR_FEED%
echo   [+] Spread buffer   : %SPREAD_BUFFER_PIPS% pips  (default: 0.3)
echo.
echo   [*] Running pre-deploy health check...
echo.

cd backend

:: ── Phase 4.1 Pre-deploy health check ────────────────────────────────────────
python health_check_pre_deploy.py --quick
if errorlevel 1 (
    echo.
    echo ================================================================================
    echo   [!] HEALTH CHECK FAILED — Review issues above before running production.
    echo   [!] Re-run: python backend/health_check_pre_deploy.py
    echo ================================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   [+] Health check PASSED — Starting validator in production mode...
echo ================================================================================
echo.
echo   Press Ctrl+C to stop gracefully.
echo.

:: ── Launch validator with selected feed ──────────────────────────────────────
python run_pepperstone_validator.py --feed %VALIDATOR_FEED%

pause
