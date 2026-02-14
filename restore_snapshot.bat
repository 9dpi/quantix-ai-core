@echo off
TITLE Quantix AI Core - Snapshot Restore
COLOR 0E

echo ================================================================================
echo   QUANTIX AI CORE - SNAPSHOT RESTORE UTILITY
echo ================================================================================
echo.
echo WARNING: This will restore a previous snapshot and overwrite current files!
echo.

REM List available snapshots
echo Available snapshots:
echo.
dir /B /AD snapshots\Quantix_Snapshot_*
echo.

set /p SNAPSHOT_NAME="Enter snapshot folder name (e.g., Quantix_Snapshot_20260214_090000): "

if not exist "snapshots\%SNAPSHOT_NAME%" (
    echo.
    echo ERROR: Snapshot not found!
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   RESTORE CONFIRMATION
echo ================================================================================
echo.
echo You are about to restore: %SNAPSHOT_NAME%
echo.
echo This will:
echo - Backup current backend to backend_backup_%date:~-4%%date:~-10,2%%date:~-7,2%
echo - Restore backend code from snapshot
echo - Restore configuration files
echo.
set /p CONFIRM="Type 'YES' to confirm restore: "

if not "%CONFIRM%"=="YES" (
    echo.
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Creating backup of current system...
set BACKUP_DIR=backend_backup_%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
xcopy /E /I /Y backend "%BACKUP_DIR%" >nul

echo [2/5] Stopping services (if running)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Quantix*" 2>nul

echo [3/5] Restoring backend code...
xcopy /E /I /Y "snapshots\%SNAPSHOT_NAME%\backend" backend

echo [4/5] Restoring configuration files...
copy /Y "snapshots\%SNAPSHOT_NAME%\.env" . 2>nul
copy /Y "snapshots\%SNAPSHOT_NAME%\Procfile" . 2>nul
copy /Y "snapshots\%SNAPSHOT_NAME%\Dockerfile" . 2>nul

echo [5/5] Verifying restore...
if exist "backend\quantix_core\engine\continuous_analyzer.py" (
    echo ✓ Core files restored successfully
) else (
    echo ✗ ERROR: Core files missing!
    echo Restore may have failed. Check %BACKUP_DIR% for backup.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   RESTORE COMPLETED SUCCESSFULLY
echo ================================================================================
echo.
echo Snapshot restored: %SNAPSHOT_NAME%
echo Current backup saved to: %BACKUP_DIR%
echo.
echo NEXT STEPS:
echo 1. Review restored files
echo 2. Check .env configuration
echo 3. Run: pip install -r requirements.txt (if needed)
echo 4. Restart services: START_QUANTIX_LIVE.bat
echo.
pause
