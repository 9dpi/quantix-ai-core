@echo off
SETLOCAL EnableDelayedExpansion
title Quantix AI Core - Global Audit System v3.8
color 0B

SET RESULT_FILE=audit_result.txt

echo ======================================================= > %RESULT_FILE%
echo    📊 QUANTIX AI CORE - GLOBAL AUDIT REPORT           >> %RESULT_FILE%
echo    Date: %DATE% %TIME%                                >> %RESULT_FILE%
echo ======================================================= >> %RESULT_FILE%
echo. >> %RESULT_FILE%

echo [*] Starting Global Audit (Online + Local)...

:: Step 1: Online Production Audit (Via API Gateway)
echo [1/5] Auditing Online Production (Railway)...
echo --- [1/5] ONLINE PRODUCTION (RAILWAY) --- >> %RESULT_FILE%
python backend/audit_online.py >> %RESULT_FILE% 2>&1
echo. >> %RESULT_FILE%

:: Step 2: Internal Health Check (Direct DB Access)
echo [2/5] Checking Database and Infrastructure...
echo --- [2/5] DATABASE INTEGRITY --- >> %RESULT_FILE%
python backend/internal_health_check.py >> %RESULT_FILE% 2>&1
echo. >> %RESULT_FILE%

:: Step 3: Global Signal Audit
echo [3/5] Auditing Today's Signals (All Sources)...
echo --- [3/5] RECENT SIGNALS --- >> %RESULT_FILE%
python backend/check_signals_today.py >> %RESULT_FILE% 2>&1
echo. >> %RESULT_FILE%

:: Step 4: Heartbeat Verification
echo [4/5] Verifying Service Heartbeats...
echo --- [4/5] SYSTEM HEARTBEATS --- >> %RESULT_FILE%
python backend/check_heartbeats.py >> %RESULT_FILE% 2>&1
echo. >> %RESULT_FILE%

:: Step 5: Stuck Pipeline Scan
echo [5/5] Scanning for Stuck Pipelines...
echo --- [5/5] PIPELINE INTEGRITY --- >> %RESULT_FILE%
python backend/check_stuck.py >> %RESULT_FILE% 2>&1
echo. >> %RESULT_FILE%

echo ======================================================= >> %RESULT_FILE%
echo    ✅ GLOBAL AUDIT COMPLETED AT %TIME%                 >> %RESULT_FILE%
echo ======================================================= >> %RESULT_FILE%

:: Display the results
type %RESULT_FILE%

echo.
echo 💾 Report saved to: %RESULT_FILE%
echo.

