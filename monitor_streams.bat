@echo off
title 🌐 Quantix Decoupled-Cloud Monitor (v3.3.7)
setlocal enabledelayedexpansion

:top
cls
echo #################################################
echo #                                               #
echo #      QUANTIX AI CORE - MONITOR V3.3.7         #
echo #        Mode: Decoupled-Cloud (Railway)        #
echo #                                               #
echo #################################################
echo.

:: 1. Kiểm tra môi trường
echo [1/4] Checking Local Environment...
if not exist logs mkdir logs
if not exist backend echo [ERROR] Folder 'backend' missing! && pause && exit /b
echo [OK] Project structure verified.

:: 2. Kiểm tra API Server
echo.
echo [2/4] Checking Cloud API Status...
set "URL=https://quantixapiserver-production.up.railway.app/"
:: Ghi thẳng kết quả vào file để tránh lỗi hiển thị JSON
curl.exe -s --max-time 15 %URL% > logs\api_resp.tmp

findstr /I "online" logs\api_resp.tmp > nul
if !errorlevel! equ 0 (
    echo [OK] API Server is ONLINE.
) else (
    echo [FAIL] API Server is UNREACHABLE or ERROR.
    echo [INFO] Content:
    type logs\api_resp.tmp
    echo.
)

:: 3. Chạy chẩn đoán sâu và báo cáo chi tiết
echo.
echo [3/4] Running Detailed Diagnostics...
if not exist .venv\Scripts\python.exe echo [ERROR] .venv missing! && pause && exit /b

:: Khởi tạo file log sạch
echo ======================================================== > logs\latest_diag.tmp
echo QUANTIX SYSTEM AUDIT LOG - !date! !time! >> logs\latest_diag.tmp
echo ======================================================== >> logs\latest_diag.tmp

:: Chạy chẩn đoán gốc (Bản cập nhật 3.3.7 có ID chi tiết)
pushd backend
echo [DIAGNOSE] >> ..\logs\latest_diag.tmp
..\.venv\Scripts\python.exe diagnose_production.py >> ..\logs\latest_diag.tmp 2>&1

echo. >> ..\logs\latest_diag.tmp
echo [DETAILED TELEMETRY] >> ..\logs\latest_diag.tmp
..\.venv\Scripts\python.exe check_detailed_telemetry.py >> ..\logs\latest_diag.tmp 2>&1

echo. >> ..\logs\latest_diag.tmp
echo [LIFECYCLE MONITORING] >> ..\logs\latest_diag.tmp
..\.venv\Scripts\python.exe check_signal_lifecycle.py >> ..\logs\latest_diag.tmp 2>&1

echo. >> ..\logs\latest_diag.tmp
echo [TODAY SIGNALS] >> ..\logs\latest_diag.tmp
..\.venv\Scripts\python.exe check_today_signals.py >> ..\logs\latest_diag.tmp 2>&1
popd

echo.
echo --------------------------------------------------------
type logs\latest_diag.tmp
echo --------------------------------------------------------

:: 4. Kết luận
echo.
echo [4/4] System Verdict:
findstr /C:"SYSTEM_VERDICT=FAIL" logs\latest_diag.tmp > nul
if !errorlevel! equ 0 (
    echo [CRITICAL] VERDICT: FAIL - Stuck signals or DB issues detected.
) else (
    echo [OK] VERDICT: PASS - System is healthy.
)

echo.
echo Audit log saved to: logs\monitor_history.log
echo -------------------------------------------------------- >> logs\monitor_history.log
type logs\latest_diag.tmp >> logs\monitor_history.log

echo.
echo Press any key to refresh (Auto-refresh in 60s)...
timeout /t 60 > nul
goto :top

