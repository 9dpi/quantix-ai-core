@echo off
TITLE Quantix AI Core - Snapshot Creator
COLOR 0A

echo ================================================================================
echo   QUANTIX AI CORE - SYSTEM SNAPSHOT CREATOR
echo ================================================================================
echo.

REM Get current timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Create snapshot directory
set SNAPSHOT_DIR=snapshots\Quantix_Snapshot_%TIMESTAMP%
echo [1/6] Creating snapshot directory: %SNAPSHOT_DIR%
mkdir "%SNAPSHOT_DIR%" 2>nul

echo.
echo [2/6] Copying backend code...
xcopy /E /I /Y backend "%SNAPSHOT_DIR%\backend" /EXCLUDE:snapshot_exclude.txt

echo.
echo [3/6] Copying configuration files...
copy /Y .env "%SNAPSHOT_DIR%\" 2>nul
copy /Y Procfile "%SNAPSHOT_DIR%\" 2>nul
copy /Y Dockerfile "%SNAPSHOT_DIR%\" 2>nul
copy /Y runtime.txt "%SNAPSHOT_DIR%\" 2>nul
copy /Y requirements.txt "%SNAPSHOT_DIR%\" 2>nul

echo.
echo [4/6] Copying documentation...
copy /Y *.md "%SNAPSHOT_DIR%\" 2>nul
copy /Y backend\quantix_core\engine\*.txt "%SNAPSHOT_DIR%\docs\" 2>nul
copy /Y backend\quantix_core\engine\*.md "%SNAPSHOT_DIR%\docs\" 2>nul

echo.
echo [5/6] Creating snapshot manifest...
echo QUANTIX AI CORE SNAPSHOT > "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo ========================= >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo Created: %date% %time% >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo Timestamp: %TIMESTAMP% >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo. >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo CONTENTS: >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo - Backend source code (quantix_core) >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo - Configuration files (.env, Procfile, etc) >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo - Documentation (Rules.txt, Confidence.md) >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo - Requirements and runtime specs >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo. >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo RESTORE INSTRUCTIONS: >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 1. Stop all running services >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 2. Backup current backend folder >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 3. Copy snapshot backend to main directory >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 4. Restore .env file >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 5. Run: pip install -r requirements.txt >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"
echo 6. Restart services >> "%SNAPSHOT_DIR%\SNAPSHOT_INFO.txt"

echo.
echo [6/6] Compressing snapshot (optional)...
echo Note: Manual compression recommended for large snapshots
echo You can use 7-Zip or WinRAR to compress: %SNAPSHOT_DIR%

echo.
echo ================================================================================
echo   SNAPSHOT CREATED SUCCESSFULLY
echo ================================================================================
echo.
echo Location: %SNAPSHOT_DIR%
echo.
echo To restore this snapshot:
echo 1. Navigate to the snapshot directory
echo 2. Read SNAPSHOT_INFO.txt for instructions
echo 3. Copy files back to main directory
echo.
pause
