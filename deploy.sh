#!/bin/bash

# LegalSaathi Production Deployment Script
# Supports multiple free hosting platforms

set -e

echo "🚀 LegalSaathi Production Deployment Script"
echo "============================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create it with your API keys."
    exit 1
fi

# Check if Google Cloud credentials exist
if [ ! -f google-cloud-credentials.json ]; then
    echo "❌ Error: google-cloud-credentials.json not found."
    echo "Please download your Google Cloud service account key and save it as google-cloud-credentials.json"
    exit 1
fi

# Function to deploy to Render
deploy_to_render() {
    echo "📦 Deploying to Render.com (Free Tier)"
    
    # Check if render.yaml exists
    if [ ! -f render.yaml ]; then
        echo "❌ render.yaml not found"
        exit 1
    fi
    
    echo "✅ Render configuration ready"
    echo "📋 Next steps:"
    echo "1. Push your code to GitHub"
    echo "2. Connect your GitHub repo to Render"
    echo "3. Render will automatically deploy using render.yaml"
    echo "4. Set environment variables in Render dashboard"
    
    echo ""
    echo "🔑 Required Environment Variables for Render:"
    echo "- GROQ_API_KEY"
    echo "- GEMINI_API_KEY" 
    echo "- GOOGLE_TRANSLATE_API_KEY"
    echo "- GOOGLE_CLOUD_PROJECT_ID"
    echo "- GOOGLE_CLOUD_LOCATION"
    echo "- DOCUMENT_AI_PROCESSOR_ID (optional)"
}

# Function to deploy to Railway
deploy_to_railway() {
    echo "🚂 Deploying to Railway (Free Tier)"
    
    # Install Railway CLI if not present
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    echo "🔐 Login to Railway (this will open your browser)"
    railway login
    
    echo "📦 Creating new Railway project"
    railway init
    
    echo "🔧 Setting up environment variables"
    echo "Please set the following variables in Railway dashboard:"
    echo "- GROQ_API_KEY"
    echo "- GEMINI_API_KEY"
    echo "- GOOGLE_TRANSLATE_API_KEY" 
    echo "- GOOGLE_CLOUD_PROJECT_ID"
    echo "- GOOGLE_CLOUD_LOCATION"
    
    echo "🚀 Deploying to Railway"
    railway up
}

# Function to deploy to Heroku
deploy_to_heroku() {
    echo "🟣 Deploying to Heroku (Free Tier - if available)"
    
    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        echo "❌ Heroku CLI not found. Please install it first."
        echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    echo "🔐 Login to Heroku"
    heroku login
    
    echo "📦 Creating Heroku app"
    read -p "Enter app name (or press Enter for auto-generated): " app_name
    
    if [ -z "$app_name" ]; then
        heroku create
    else
        heroku create $app_name
    fi
    
    echo "🔧 Setting up environment variables"
    heroku config:set FLASK_ENV=production
    
    echo "Please set the following config vars in Heroku dashboard:"
    echo "- GROQ_API_KEY"
    echo "- GEMINI_API_KEY"
    echo "- GOOGLE_TRANSLATE_API_KEY"
    echo "- GOOGLE_CLOUD_PROJECT_ID"
    echo "- GOOGLE_CLOUD_LOCATION"
    
    echo "🚀 Deploying to Heroku"
    git add .
    git commit -m "Deploy to Heroku" || true
    git push heroku main
}

# Function to deploy with Docker
deploy_with_docker() {
    echo "🐳 Building Docker container"
    
    # Build Docker image
    docker build -t legalsaathi-app .
    
    echo "✅ Docker image built successfully"
    echo "🚀 Running container locally for testing"
    
    # Run container
    docker run -d \
        --name legalsaathi-container \
        -p 5000:5000 \
        --env-file .env \
        -v $(pwd)/google-cloud-credentials.json:/app/google-cloud-credentials.json:ro \
        legalsaathi-app
    
    echo "✅ Container running on http://localhost:5000"
    echo "🔍 Check logs with: docker logs legalsaathi-container"
    echo "🛑 Stop with: docker stop legalsaathi-container"
}

# Function to run local development server
run_local() {
    echo "💻 Starting local development server"
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo "📦 Creating virtual environment"
        python -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate || source .venv/Scripts/activate
    
    # Install dependencies
    echo "📦 Installing dependencies"
    pip install -r requirements.txt
    
    # Run the application
    echo "🚀 Starting LegalSaathi on http://localhost:5000"
    python app.py
}

# Function to run tests
run_tests() {
    echo "🧪 Running test suite"
    
    # Activate virtual environment
    source .venv/bin/activate || source .venv/Scripts/activate
    
    # Install test dependencies
    pip install pytest pytest-cov
    
    # Run tests
    pytest tests/ -v --cov=. --cov-report=html
    
    echo "✅ Tests completed. Coverage report available in htmlcov/"
}

# Function to check system health
health_check() {
    echo "🏥 Performing system health check"
    
    # Check if server is running
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Server is healthy"
        curl -s http://localhost:5000/health | python -m json.tool
    else
        echo "❌ Server health check failed"
        echo "Make sure the server is running on http://localhost:5000"
    fi
}

# Main menu
echo ""
echo "Select deployment option:"
echo "1) Deploy to Render.com (Recommended - Free)"
echo "2) Deploy to Railway (Free)"
echo "3) Deploy to Heroku (Free tier limited)"
echo "4) Build and run with Docker"
echo "5) Run local development server"
echo "6) Run tests"
echo "7) Health check"
echo "8) Exit"

read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        deploy_to_render
        ;;
    2)
        deploy_to_railway
        ;;
    3)
        deploy_to_heroku
        ;;
    4)
        deploy_with_docker
        ;;
    5)
        run_local
        ;;
    6)
        run_tests
        ;;
    7)
        health_check
        ;;
    8)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process completed!"
echo "📚 Check the documentation for post-deployment steps."
echo "🔗 Demo: https://your-app-url.com/demo"
echo "📊 Analytics: https://your-app-url.com/analytics"