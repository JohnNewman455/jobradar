#!/bin/bash

# Job Scraper Tool - Startup script with JobSpy (Python 3.12)
# This version uses JobSpy library for Indeed, LinkedIn, ZipRecruiter, Glassdoor

echo "🚀 Starting Job Scraper Tool with JobSpy..."
echo ""

# Check if venv312 exists
if [ ! -d "venv312" ]; then
    echo "❌ Python 3.12 virtual environment not found!"
    echo "   Creating it now..."
    /opt/homebrew/bin/python3.12 -m venv venv312
    
    echo "📦 Installing dependencies..."
    source venv312/bin/activate
    pip install python-jobspy flask pandas openpyxl flask-cors beautifulsoup4
    echo ""
else
    echo "✅ Python 3.12 virtual environment found"
    source venv312/bin/activate
fi

echo ""
echo "🌐 Starting server on http://localhost:5001"
echo "   Press Ctrl+C to stop"
echo ""

# Run the app
python app.py
