@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURATION ---
set BACKUP_DIR=QUANTIX_BACKUP_DATA
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set TARGET_FOLDER=%BACKUP_DIR%\Backup_%TIMESTAMP%

echo ==========================================
echo    QUANTIX AI CORE - QUICK BACKUP
echo ==========================================
echo.
echo [+] Creating backup in: %TARGET_FOLDER%
mkdir "%TARGET_FOLDER%"

:: 1. Copy Config
echo [+] Saving Configuration (.env)...
copy "backend\.env" "%TARGET_FOLDER%\" >nul

:: 2. Copy Learning Data
echo [+] Saving Learning Data (Logs)...
copy "backend\heartbeat_audit.jsonl" "%TARGET_FOLDER%\" >nul
copy "dashboard\learning_data.json" "%TARGET_FOLDER%\" >nul

:: 3. Copy Launchers
echo [+] Saving Launchers...
copy "*.bat" "%TARGET_FOLDER%\" >nul

echo.
echo ==========================================
echo ✅ BACKUP COMPLETE!
echo Location: %TARGET_FOLDER%
echo.
echo Instructions for Restore:
echo To restore, copy the files inside this folder
echo back to the root of your Quantix project.
echo ==========================================
pause
