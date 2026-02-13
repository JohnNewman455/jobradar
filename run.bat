@echo off
REM Job Scraper Tool - Run Script for Windows

echo 🚀 Starting Job Scraper Tool...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ⚠️  Virtual environment not found!
    echo Run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
echo ✅ All checks passed!
echo 🌐 Starting server at http://localhost:5000
echo 📊 Dashboard will open in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
