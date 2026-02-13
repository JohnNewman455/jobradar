#!/bin/bash

# Job Scraper Tool - Setup Script

echo "🔍 Job Scraper Tool - Setup"
echo "=============================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8 or higher from https://www.python.org/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 To start the application:"
    echo "   1. Activate virtual environment: source venv/bin/activate"
    echo "   2. Run the app: python app.py"
    echo "   3. Open http://localhost:5000 in your browser"
    echo ""
    echo "📖 Read QUICKSTART.md for detailed instructions"
else
    echo ""
    echo "❌ Installation failed!"
    echo "Try installing packages manually:"
    echo "   pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl"
fi
