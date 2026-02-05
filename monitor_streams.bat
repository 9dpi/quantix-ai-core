@echo off
title 🌐 Quantix Decoupled-Cloud Monitor (v3.3.5)
setlocal enabledelayedexpansion

echo #################################################
echo #                                               #
echo #      QUANTIX AI CORE - MONITOR V3.3.5         #
echo #        Mode: Decoupled-Cloud (Railway)        #
echo #                                               #
echo #################################################
echo.

:: 1. Kiểm tra thư mục cần thiết
echo [1/4] Checking Local Environment...
if not exist logs mkdir logs
if not exist backend (
    echo [ERROR] Folder 'backend' not found!
    echo Please run this file from the project root.
    pause
    exit /b
)
echo [OK] Project structure verified.

:: 2. Kiểm tra API Server Online
echo.
echo [2/4] Checking Cloud API Status...
set "URL=https://quantixaicore-production.up.railway.app/"
echo Requesting: %URL%

:: Ghi thẳng vào file để tránh lỗi ký tự đặc biệt
curl.exe -s --max-time 15 %URL% > logs\api_resp.tmp

findstr /I "online" logs\api_resp.tmp > nul
if %errorlevel% equ 0 (
    echo [OK] API Server is ONLINE.
) else (
    echo [FAIL] API Server is UNREACHABLE or ERROR 502.
    echo [INFO] Server Response:
    type logs\api_resp.tmp
    echo.
)

:: 3. Chạy chẩn đoán Database & Invariants
echo.
echo [3/4] Running Deep Diagnostics (Supabase)...
if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment (.venv) not found!
    pause
    exit /b
)

:: Xóa log cũ
echo. > logs\latest_diag.tmp

:: Chạy script chẩn đoán
pushd backend
..\.venv\Scripts\python.exe diagnose_production.py >> ..\logs\latest_diag.tmp 2>&1
popd

echo --------------------------------------------------------
type logs\latest_diag.tmp
echo --------------------------------------------------------

:: 4. Kết luận
echo.
echo [4/4] System Verdict:
findstr /C:"SYSTEM_VERDICT=FAIL" logs\latest_diag.tmp > nul
if %errorlevel% equ 0 (
    echo [CRITICAL] VERDICT: FAIL - Check invariants!
) else (
    echo [OK] VERDICT: PASS - Cloud Truth is intact.
)

echo.
echo Audit log saved to: logs\monitor_history.log
date /t >> logs\monitor_history.log
time /t >> logs\monitor_history.log
type logs\latest_diag.tmp >> logs\monitor_history.log
echo.
echo Done. Press any key to exit.
pause > nul
