@echo off
REM Job Scraper Tool - Setup Script for Windows

echo 🔍 Job Scraper Tool - Setup
echo ==============================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ✅ Setup complete!
    echo.
    echo 🚀 To start the application:
    echo    1. Run: run.bat
    echo    2. Open http://localhost:5000 in your browser
    echo.
    echo 📖 Read QUICKSTART.md for detailed instructions
) else (
    echo.
    echo ❌ Installation failed!
    echo Try installing packages manually:
    echo    pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl
)

pause
