@echo off
REM Cloud Run Deployment Script for Legal Saathi
REM Optimized for fast deployment and testing

echo ========================================
echo Legal Saathi Cloud Run Deployment
echo ========================================

REM Set deployment configuration
set PROJECT_ID=legal-saathi-209a4
set SERVICE_NAME=legal-saathi
set REGION=us-central1
set MEMORY=2Gi
set CPU=2
set MAX_INSTANCES=10
set TIMEOUT=300

echo.
echo 🚀 Starting Cloud Run deployment...
echo Project: %PROJECT_ID%
echo Service: %SERVICE_NAME%
echo Region: %REGION%
echo Memory: %MEMORY%
echo CPU: %CPU%
echo.

REM Check if gcloud is installed
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: gcloud CLI not found. Please install Google Cloud SDK.
    echo Download from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if user is authenticated
echo 🔐 Checking authentication...
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Not authenticated with gcloud. Please run:
    echo gcloud auth login
    pause
    exit /b 1
)

REM Set the project
echo 🎯 Setting project to %PROJECT_ID%...
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo 🔧 Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

REM Build the client first
echo 📦 Building React frontend...
cd client
if exist "node_modules" (
    echo Node modules found, running build...
) else (
    echo Installing dependencies...
    npm install
)
npm run build
if %errorlevel% neq 0 (
    echo ❌ Error: Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ Frontend build completed

REM Deploy to Cloud Run
echo 🚀 Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory %MEMORY% ^
    --cpu %CPU% ^
    --max-instances %MAX_INSTANCES% ^
    --timeout %TIMEOUT% ^
    --set-env-vars GOOGLE_CLOUD_DEPLOYMENT=true

if %errorlevel% neq 0 (
    echo ❌ Error: Deployment failed
    pause
    exit /b 1
)

REM Get the service URL
echo.
echo 🌐 Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo.
echo ========================================
echo ✅ Deployment completed successfully!
echo ========================================
echo.
echo 🌐 Service URL: %SERVICE_URL%
echo 📊 Health Check: %SERVICE_URL%/health
echo 📋 API Docs: %SERVICE_URL%/docs
echo 🔍 Detailed Health: %SERVICE_URL%/api/health/detailed
echo.

REM Test the deployment
echo 🧪 Testing deployment...
echo Waiting 30 seconds for service to be ready...
timeout /t 30 /nobreak >nul

echo Testing health endpoint...
curl -f "%SERVICE_URL%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Health check passed
) else (
    echo ⚠️ Health check failed - service may still be starting up
)

echo.
echo 📋 Deployment Summary:
echo - Service: %SERVICE_NAME%
echo - Region: %REGION%
echo - URL: %SERVICE_URL%
echo - Memory: %MEMORY%
echo - CPU: %CPU%
echo - Max Instances: %MAX_INSTANCES%
echo.
echo 🎉 Deployment complete! Your Legal Saathi app is now live on Cloud Run.
echo.

pause