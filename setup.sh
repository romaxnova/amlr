#!/bin/bash

# AML Research Tool Setup Script

echo "🧬 AML Research Tool Setup"
echo "=========================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data exports

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your XAI_API_KEY"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your XAI_API_KEY"
echo "2. Run: source venv/bin/activate"
echo "3. Initialize database: python run.py --init"
echo "4. Start web server: python run.py"
echo ""
echo "Or run everything at once:"
echo "  source venv/bin/activate && python run.py --init && python run.py"
