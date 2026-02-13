@echo off
REM Quick Setup and Run Script for JobRadar v2

echo =============================
echo   JobRadar v2 - Quick Start
echo =============================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: Please run this script from the 'JOB tool' directory
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    
    REM Activate and install
    call venv\Scripts\activate.bat
    
    echo Upgrading pip...
    python -m pip install --upgrade pip --quiet
    
    echo Installing core dependencies (this may take a minute)...
    pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl fake-useragent cloudscraper lxml --quiet
    
    echo Setup complete!
) else (
    echo Virtual environment found
    call venv\Scripts\activate.bat
)

echo.
echo Starting JobRadar v2...
echo ================================
echo.
echo   Dashboard: http://localhost:5000
echo   Ready to scan 16+ job sites!
echo.
echo   Press Ctrl+C to stop the server
echo.
echo ================================
echo.

REM Run the app
python app.py

pause
