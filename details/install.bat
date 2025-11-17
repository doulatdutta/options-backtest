@echo off
REM Options Backtesting Platform - Installation Script for Windows
REM Run this file to set up the project

echo ========================================
echo Options Backtesting Platform Setup
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)
echo.

echo [2/5] Creating virtual environment...
python -m venv venv
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate
echo.

echo [4/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
echo.

echo [5/5] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Edit config/credentials.json with your Upstox API credentials
echo 2. Run: streamlit run app.py
echo 3. Open browser at http://localhost:8501
echo.
echo Happy backtesting!
pause
