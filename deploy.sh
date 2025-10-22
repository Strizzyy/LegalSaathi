#!/bin/bash

# Legal Saathi Deployment Script for Render
# This script prepares the application for deployment

echo "🚀 Preparing Legal Saathi for Render deployment..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if client directory exists
if [ ! -d "client" ]; then
    echo "❌ Error: client directory not found."
    exit 1
fi

echo "✅ Project structure verified"

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected. Consider activating one."
fi

# Install Python dependencies locally for testing
echo "📦 Installing Python dependencies..."
if command -v uv >/dev/null 2>&1; then
    uv sync
else
    echo "⚠️  uv not found, using pip..."
    pip install -r requirements.txt
fi

# Check Node.js and npm
echo "📦 Checking Node.js setup..."
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found. Please install Node.js 18 or higher."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found. Please install npm."
    exit 1
fi

# Build frontend
echo "🏗️  Building frontend..."
cd client
npm ci
npm run build
cd ..

echo "✅ Frontend built successfully"

# Test FastAPI import
echo "🧪 Testing FastAPI application..."
python -c "import main; print('✅ FastAPI app imports successfully')" || {
    echo "❌ Error: FastAPI app failed to import"
    exit 1
}

# Check environment variables
echo "🔧 Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to set environment variables in Render."
else
    echo "✅ .env file found"
fi

# Check for Google Cloud credentials
if [ ! -f "google-cloud-credentials.json" ]; then
    echo "⚠️  Warning: google-cloud-credentials.json not found. Make sure to upload it to Render."
else
    echo "✅ Google Cloud credentials file found"
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next steps for Render deployment:"
echo "1. Push your code to GitHub/GitLab"
echo "2. Connect your repository to Render"
echo "3. Use the render.yaml file for configuration"
echo "4. Set the following environment variables in Render:"
echo "   - GROQ_API_KEY"
echo "   - GEMINI_API_KEY (optional, for fallback)"
echo "   - GOOGLE_CLOUD_PROJECT_ID"
echo "   - GOOGLE_CLOUD_LOCATION"
echo "   - DOCUMENT_AI_PROCESSOR_ID"
echo "   - NEO4J_URI (if using Neo4j)"
echo "   - NEO4J_USERNAME (if using Neo4j)"
echo "   - NEO4J_PASSWORD (if using Neo4j)"
echo "   - NEO4J_DATABASE (if using Neo4j)"
echo "5. Upload google-cloud-credentials.json as a secret file"
echo "6. Deploy!"
echo ""
echo "🔗 Health check will be available at: https://your-app.onrender.com/health"