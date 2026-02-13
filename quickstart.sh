#!/bin/bash

# Quick Setup and Run Script for JobRadar v2

echo "🚀 JobRadar v2 - Quick Start"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the 'JOB tool' directory"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    # Activate and install
    source venv/bin/activate
    
    echo "⬆️  Upgrading pip..."
    pip install --upgrade pip --quiet
    
    echo "📥 Installing core dependencies (this may take a minute)..."
    pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl fake-useragent cloudscraper lxml --quiet
    
    echo "✅ Setup complete!"
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

echo ""
echo "🌐 Starting JobRadar v2..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📍 Dashboard: http://localhost:5000"
echo "  🎯 Ready to scan 16+ job sites!"
echo ""
echo "  Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the app
python app.py
