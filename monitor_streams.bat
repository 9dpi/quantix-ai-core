@echo off
title 🌐 Quantix All-on-Cloud Monitor (v3.2)
setlocal enabledelayedexpansion

:: ========================================================
:: QUANTIX STREAM MONITOR - CLOUD EDITION
:: Architecture : All-on-Cloud (Railway + Supabase)
:: Version      : 3.2
:: Fail Policy  : FAIL-CLOSED
:: Purpose      : Protect system truth & invariants
:: ========================================================

echo.
echo    #################################################
echo    #                                               #
echo    #      QUANTIX AI CORE - CLOUD MONITOR V3.2     #
echo    #          Architecture: All-on-Cloud           #
echo    #          Fail Policy : FAIL-CLOSED            #
echo    #                                               #
echo    #################################################
echo.

:: Ensure logs directory exists
if not exist logs mkdir logs

:: ========================================================
:: 0. Declare Pipeline Context (AUDIT IMPORTANT)
:: ========================================================
echo PIPELINE_MODE=PRODUCTION
echo ARCH_VERSION=3.2
echo FAIL_POLICY=FAIL_CLOSED
echo.

:: ========================================================
:: 1. Check Local Safeguard (Architectural Invariant)
:: ========================================================
echo [1/4] Checking Local Safeguard...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV > task_check.tmp
findstr /I "python.exe" task_check.tmp > nul
if %errorlevel% equ 0 (
    echo [WARN] Local Python processes detected!
    echo [WARN] This violates ALL-ON-CLOUD invariant.
    echo [WARN] Recommended: taskkill /F /IM python.exe
) else (
    echo [OK] Local miners are OFF. Cloud-only flow confirmed.
)
del task_check.tmp

:: ========================================================
:: 2. Run Production Diagnostics & Telemetry
:: ========================================================
echo.
echo [2/4] Fetching Cloud Health & Telemetry...

:: Clear current diag log
echo. > logs\latest_diag.tmp

cd backend
echo Running System Diagnostics...
..\.venv\Scripts\python.exe diagnose_production.py >> ..\logs\latest_diag.tmp 2>&1
echo. >> ..\logs\latest_diag.tmp
echo Running Detailed Telemetry Report... >> ..\logs\latest_diag.tmp
..\.venv\Scripts\python.exe check_detailed_telemetry.py >> ..\logs\latest_diag.tmp 2>&1
cd ..

:: ========================================================
:: 3. Display Integrated Diagnostic Output
:: ========================================================
echo.
echo [3/4] Integrated Diagnostic Output:
echo --------------------------------------------------------
type logs\latest_diag.tmp
echo --------------------------------------------------------

:: ========================================================
:: 4. Invariant Verdict Check (Machine-Readable)
:: ========================================================
echo.
echo [4/4] Evaluating System Verdict...

:: Expect diagnose_production.py to emit:
:: SYSTEM_VERDICT=PASS | FAIL_INVARIANT | FAIL_SAFETY

findstr /C:"SYSTEM_VERDICT=FAIL" logs\latest_diag.tmp > nul
if %errorlevel% equ 0 (
    echo [CRITICAL] SYSTEM VERDICT: FAIL
    echo [CRITICAL] One or more architectural invariants breached.
) else (
    echo [OK] SYSTEM VERDICT: PASS
    echo [OK] All Quantix invariants satisfied.
)

:: ========================================================
:: Persistent Audit Log (Immutable History)
:: ========================================================
echo.
echo Writing audit history to logs\monitor_history.log...

echo ======================================================== >> logs\monitor_history.log
echo [%date% %time%] Integrated Diagnostic Run (v3.2) >> logs\monitor_history.log
echo PIPELINE_MODE=PRODUCTION >> logs\monitor_history.log
echo ARCH_VERSION=3.2 >> logs\monitor_history.log
echo FAIL_POLICY=FAIL_CLOSED >> logs\monitor_history.log
echo. >> logs\monitor_history.log
type logs\latest_diag.tmp >> logs\monitor_history.log
echo. >> logs\monitor_history.log

:: ========================================================
:: Footer
:: ========================================================
echo.
echo [INFO] Full audit history saved to: logs\monitor_history.log
echo [RULE] Monitor protects TRUTH, not performance.
echo.
pause
