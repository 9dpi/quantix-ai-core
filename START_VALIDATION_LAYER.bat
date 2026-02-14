@echo off
TITLE Quantix Validation Layer - Pepperstone Observer
COLOR 0B

echo ================================================================================
echo   PEPPERSTONE VALIDATION LAYER - INDEPENDENT OBSERVER
echo ================================================================================
echo.
echo This layer runs in parallel with the main Quantix system.
echo It validates signals using Pepperstone feed and logs discrepancies.
echo.
echo Status: PASSIVE OBSERVER (Does not affect production)
echo.
echo Press Ctrl+C to stop.
echo.
echo ================================================================================
echo.

cd backend
python run_pepperstone_validator.py

pause
