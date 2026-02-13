#!/bin/bash

# Job Scraper Tool - Run Script

echo "🚀 Starting Job Scraper Tool..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "Run setup.sh first: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" &> /dev/null; then
    echo "❌ Dependencies not installed!"
    echo "Run setup.sh first: ./setup.sh"
    exit 1
fi

# Run the application
echo "✅ All checks passed!"
echo "🌐 Starting server at http://localhost:5000"
echo "📊 Dashboard will open in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
