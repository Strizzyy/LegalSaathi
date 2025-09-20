#!/bin/bash

# Build script for LegalSaathi React + Flask application

set -e

echo "🚀 Building LegalSaathi Application..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

# Build React frontend
echo "📦 Building React frontend..."
cd client

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

# Build the React app
echo "🔨 Building React app..."
npm run build

cd ..

# React build stays in client/dist for separate serving
echo "✅ React build completed in client/dist/"

# Install Python dependencies if needed
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv .venv
fi

echo "📥 Installing Python dependencies..."
source .venv/bin/activate 2>/dev/null || .venv\Scripts\activate
pip install -r requirements.txt

echo "✅ Build completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "   • Development: uv run python app.py"
echo "   • Production: gunicorn --bind 0.0.0.0:5000 app:app"
echo "   • Frontend dev: cd client && npm run dev"
echo ""
echo "🌐 The app will be available at:"
echo "   • Backend: http://localhost:5000"
echo "   • Frontend dev: http://localhost:3000"