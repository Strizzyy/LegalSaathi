@echo off
REM Legal Saathi Deployment Script for Render (Windows)
REM This script prepares the application for deployment

echo 🚀 Preparing Legal Saathi for Render deployment...

REM Check if we're in the right directory
if not exist "main.py" (
    echo ❌ Error: main.py not found. Please run this script from the project root directory.
    exit /b 1
)

REM Check if client directory exists
if not exist "client" (
    echo ❌ Error: client directory not found.
    exit /b 1
)

echo ✅ Project structure verified

REM Check Python dependencies
echo 📦 Checking Python dependencies...
if not exist "requirements.txt" (
    echo ❌ Error: requirements.txt not found.
    exit /b 1
)

REM Install Python dependencies locally for testing
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Check Node.js and npm
echo 📦 Checking Node.js setup...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Node.js not found. Please install Node.js 18 or higher.
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: npm not found. Please install npm.
    exit /b 1
)

REM Build frontend
echo 🏗️ Building frontend...
cd client
npm ci
npm run build
cd ..

echo ✅ Frontend built successfully

REM Test FastAPI import
echo 🧪 Testing FastAPI application...
python -c "import main; print('✅ FastAPI app imports successfully')"
if errorlevel 1 (
    echo ❌ Error: FastAPI app failed to import
    exit /b 1
)

REM Check environment variables
echo 🔧 Checking environment variables...
if not exist ".env" (
    echo ⚠️ Warning: .env file not found. Make sure to set environment variables in Render.
) else (
    echo ✅ .env file found
)

REM Check for Google Cloud credentials
if not exist "google-cloud-credentials.json" (
    echo ⚠️ Warning: google-cloud-credentials.json not found. Make sure to upload it to Render.
) else (
    echo ✅ Google Cloud credentials file found
)

echo.
echo 🎉 Deployment preparation complete!
echo.
echo 📋 Next steps for Render deployment:
echo 1. Push your code to GitHub/GitLab
echo 2. Connect your repository to Render
echo 3. Use the render.yaml file for configuration
echo 4. Set the following environment variables in Render:
echo    - GROQ_API_KEY
echo    - GEMINI_API_KEY (optional, for fallback)
echo    - GOOGLE_CLOUD_PROJECT_ID
echo    - GOOGLE_CLOUD_LOCATION
echo    - DOCUMENT_AI_PROCESSOR_ID
echo    - NEO4J_URI (if using Neo4j)
echo    - NEO4J_USERNAME (if using Neo4j)
echo    - NEO4J_PASSWORD (if using Neo4j)
echo    - NEO4J_DATABASE (if using Neo4j)
echo 5. Upload google-cloud-credentials.json as a secret file
echo 6. Deploy!
echo.
echo 🔗 Health check will be available at: https://your-app.onrender.com/health

pause