@echo off
REM Optimized Google Cloud Run Deployment Script for LegalSaathi (Windows)
REM This script deploys the application with optimized settings for fast startup

echo 🚀 Starting optimized Google Cloud Run deployment...

REM Configuration
set PROJECT_ID=legal-saathi-project
set SERVICE_NAME=legal-saathi
set REGION=us-central1
set MEMORY=2Gi
set CPU=2
set MAX_INSTANCES=10
set TIMEOUT=300
set CONCURRENCY=100

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: gcloud CLI is not installed
    echo Please install gcloud CLI: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

REM Set project
echo 📋 Setting project to: %PROJECT_ID%
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo 🔧 Enabling required Google Cloud APIs...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

REM Clean up local files before deployment
echo 🧹 Cleaning up unnecessary files...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .venv rmdir /s /q .venv
del /q *.log 2>nul
del /q *.db 2>nul
if exist "client\node_modules" rmdir /s /q "client\node_modules"
del /q "client\.env" 2>nul
del /q "client\npx" 2>nul
del /q "client\void" 2>nul
del /q "client\void'" 2>nul
del /q "client\{" 2>nul

REM Build and deploy with optimized settings
echo 🏗️ Building and deploying to Google Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --dockerfile Dockerfile.cloudrun ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory %MEMORY% ^
    --cpu %CPU% ^
    --max-instances %MAX_INSTANCES% ^
    --timeout %TIMEOUT% ^
    --concurrency %CONCURRENCY% ^
    --set-env-vars GOOGLE_CLOUD_DEPLOYMENT=true ^
    --set-env-vars PORT=8080 ^
    --set-env-vars TRANSFORMERS_OFFLINE=1 ^
    --set-env-vars HF_HUB_OFFLINE=1 ^
    --execution-environment gen2 ^
    --cpu-boost ^
    --session-affinity

REM Get the service URL
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo ✅ Deployment completed successfully!
echo 🌐 Service URL: %SERVICE_URL%
echo 🔍 Health check: %SERVICE_URL%/health
echo 📊 Admin dashboard: %SERVICE_URL%/admin

echo 🎉 Google Cloud Run deployment completed!
echo.
echo 📋 Deployment Summary:
echo    Service: %SERVICE_NAME%
echo    Region: %REGION%
echo    Memory: %MEMORY%
echo    CPU: %CPU%
echo    Max Instances: %MAX_INSTANCES%
echo    URL: %SERVICE_URL%

pause