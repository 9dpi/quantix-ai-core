@echo off
title 🛠️ Quantix Emergency Control (v3.1)
setlocal enabledelayedexpansion

:: ========================================================
:: QUANTIX EMERGENCY CONTROL
:: Mode        : MANUAL RECOVERY ONLY
:: Architecture: All-on-Cloud
:: RULE        : Use ONLY when diagnostics FAIL
:: ========================================================

:: --------------------------------------------------------
:: SAFETY PRE-CHECK (MANDATORY)
:: --------------------------------------------------------
cls
echo Verifying system state before enabling EMERGENCY MODE...
echo.

if not exist logs\latest_diag.tmp (
    echo [ABORT] No diagnostic snapshot found.
    echo [ABORT] Run Cloud Monitor first.
    pause
    exit
)

findstr /C:"SYSTEM_VERDICT=PASS" logs\latest_diag.tmp > nul
if %errorlevel% equ 0 (
    echo [DENY] SYSTEM_VERDICT=PASS
    echo [DENY] Emergency control is NOT permitted.
    echo [RULE] Emergency is only allowed when invariants FAIL.
    pause
    exit
)

echo [OK] Diagnostic indicates system anomaly.
echo [OK] Emergency mode unlocked.
timeout /t 2 > nul

:menu
cls
echo.
echo    #################################################
echo    #                                               #
echo    #      QUANTIX AI CORE - EMERGENCY CONTROL      #
echo    #          Version: 3.1 (All-on-Cloud)           #
echo    #          MODE: MANUAL RECOVERY ONLY            #
echo    #                                               #
echo    #################################################
echo.
echo    [1] CHECK STATUS   - View active signals/locks
echo    [2] UNBLOCK GLOBAL - Force-close WAITING/ENTRY
echo    [3] NUKE ZOMBIES   - Clear PREPARED residuals
echo    [4] FULL RESET    - UNBLOCK + NUKE (LAST RESORT)
echo    [5] EXIT
echo.

set /p choice="Select Protocol (1-5): "

:: --------------------------------------------------------
:: 1. STATUS (READ-ONLY)
:: --------------------------------------------------------
if "%choice%"=="1" (
    echo [EXEC] Status Diagnostic...
    cd backend
    ..\.venv\Scripts\python.exe emergency_unblock.py status
    cd ..
    pause
    goto menu
)

:: --------------------------------------------------------
:: 2. UNBLOCK
:: --------------------------------------------------------
if "%choice%"=="2" (
    echo.
    echo [DANGER] Force-closing ALL live signals.
    set /p confirm="Type UNBLOCK to confirm: "
    if /I "!confirm!"=="UNBLOCK" (
        echo [%date% %time%] EMERGENCY UNBLOCK >> logs\emergency.log
        cd backend
        ..\.venv\Scripts\python.exe emergency_unblock.py unblock
        cd ..
    )
    pause
    goto menu
)

:: --------------------------------------------------------
:: 3. NUKE ZOMBIES
:: --------------------------------------------------------
if "%choice%"=="3" (
    echo.
    echo [DANGER] Clearing PREPARED phase residuals.
    set /p confirm="Type NUKE to confirm: "
    if /I "!confirm!"=="NUKE" (
        echo [%date% %time%] EMERGENCY NUKE >> logs\emergency.log
        cd backend
        ..\.venv\Scripts\python.exe emergency_unblock.py nuke
        cd ..
    )
    pause
    goto menu
)

:: --------------------------------------------------------
:: 4. FULL RESET (EXTREME)
:: --------------------------------------------------------
if "%choice%"=="4" (
    echo.
    echo [CRITICAL] FULL RESET WILL REWRITE SYSTEM STATE.
    set /p confirm="Type FULL RESET to proceed: "
    if /I "!confirm!"=="FULL RESET" (
        echo [%date% %time%] EMERGENCY FULL RESET >> logs\emergency.log
        cd backend
        ..\.venv\Scripts\python.exe emergency_unblock.py all
        cd ..
    )
    pause
    goto menu
)

if "%choice%"=="5" exit

echo [!] Invalid choice.
pause
goto menu
