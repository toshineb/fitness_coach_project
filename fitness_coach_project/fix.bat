@echo off
REM Quick Fix Script for Fitness Coach AI (Windows)
REM Reinstalls dependencies and verifies setup

echo ======================================================================
echo FITNESS COACH AI - QUICK FIX SCRIPT (WINDOWS)
echo ======================================================================
echo.

echo Step 1: Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
echo.

echo Step 2: Installing MediaPipe (may take a moment)...
pip uninstall mediapipe -y >nul 2>&1
pip install --upgrade mediapipe
echo.

echo Step 3: Installing all dependencies from requirements.txt...
pip install -r requirements.txt --upgrade
echo.

echo Step 4: Running diagnostic to verify setup...
python diagnose.py
echo.

echo If all checks pass, you can now run:
echo   python run_app.py
echo.
echo ======================================================================
pause
