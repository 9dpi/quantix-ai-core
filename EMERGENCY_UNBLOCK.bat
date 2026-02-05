@echo off
title 🛠️ Quantix Emergency Unblocker (v1.0)
setlocal enabledelayedexpansion

:top
cls
echo #################################################
echo #                                               #
echo #     QUANTIX AI - EMERGENCY UNBLOCKER          #
echo #     Tool for Clearing Stuck Cloud Signals     #
echo #                                               #
echo #################################################
echo.

:: 1. Kiểm tra môi trường
if not exist .venv\Scripts\python.exe (
    echo [ERROR] .venv missing! Please run from project root.
    pause
    exit /b
)

echo [1/2] Checking for stuck signals on Cloud...
echo -------------------------------------------------
pushd backend
..\.venv\Scripts\python.exe unblock_pipeline_logic.py > ..\logs\unblock_check.tmp
popd

set "STUCK_FOUND=0"
for /f "tokens=1,2,3,4 delims=|" %%a in (logs\unblock_check.tmp) do (
    if "%%a"=="STUCK" (
        set "STUCK_FOUND=1"
        echo [!] DETECTED: %%c (ID: %%b)
        echo     Reason: %%d
        echo.
    )
)

if "!STUCK_FOUND!"=="0" (
    echo [OK] Pipeline is CLEAN. No stuck signals detected.
    echo.
    echo Scan complete. Press any key to refresh...
    pause > nul
    goto :top
)

:: 2. Xử lý
echo -------------------------------------------------
echo [2/2] STUCK SIGNALS CAUSING BLOCKAGE!
echo.
echo [1] CLEAR ALL (Force close all stuck signals)
echo [2] RE-SCAN (Refresh status)
echo [3] EXIT
echo.
set /p choice="Choose action (1-3): "

if "%choice%"=="1" (
    echo.
    echo Executing Emergency Clear...
    pushd backend
    ..\.venv\Scripts\python.exe unblock_pipeline_logic.py --clear-all
    popd
    echo.
    echo Unblock complete. Returning to monitor...
    timeout /t 3 > nul
    goto :top
)

if "%choice%"=="2" goto :top
if "%choice%"=="3" exit /b

goto :top
