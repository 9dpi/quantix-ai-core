@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    QUANTIX AI CORE - QUICK RESTORE
echo ==========================================
echo.
echo Please follow these steps:
echo 1. Open the 'QUANTIX_BACKUP_DATA' folder.
echo 2. Find the folder named 'Backup_YYYYMMDD_HHMM' you want to restore.
echo 3. Copy ALL files from inside that folder.
echo 4. Paste them here (in the root of Quantix_AI_Core).
echo.
echo [+] Note: Paste 'heartbeat_audit.jsonl' into 'backend/'
echo [+] Note: Paste '.env' into 'backend/'
echo.
echo This tool is just a reminder of the locations. 
echo Moving files manually is safer for non-tech users
echo to avoid overwriting wrong versions.
echo.
echo Press any key to open the Backup Folder...
pause >nul
explorer "QUANTIX_BACKUP_DATA"
