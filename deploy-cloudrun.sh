#!/bin/bash

# Cloud Run Deployment Script for Legal Saathi
# Optimized for fast deployment and testing

echo "========================================"
echo "Legal Saathi Cloud Run Deployment"
echo "========================================"

# Set deployment configuration
PROJECT_ID="legal-saathi-209a4"
SERVICE_NAME="legal-saathi"
REGION="us-central1"
MEMORY="2Gi"
CPU="2"
MAX_INSTANCES="10"
TIMEOUT="300"

echo ""
echo "🚀 Starting Cloud Run deployment..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Memory: $MEMORY"
echo "CPU: $CPU"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK."
    echo "Download from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ Error: Not authenticated with gcloud. Please run:"
    echo "gcloud auth login"
    exit 1
fi

# Set the project
echo "🎯 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the client first
echo "📦 Building React frontend..."
cd client
if [ -d "node_modules" ]; then
    echo "Node modules found, running build..."
else
    echo "Installing dependencies..."
    npm install
fi
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Error: Frontend build failed"
    cd ..
    exit 1
fi
cd ..
echo "✅ Frontend build completed"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --max-instances $MAX_INSTANCES \
    --timeout $TIMEOUT \
    --set-env-vars GOOGLE_CLOUD_DEPLOYMENT=true

if [ $? -ne 0 ]; then
    echo "❌ Error: Deployment failed"
    exit 1
fi

# Get the service URL
echo ""
echo "🌐 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo ""
echo "========================================"
echo "✅ Deployment completed successfully!"
echo "========================================"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Health Check: $SERVICE_URL/health"
echo "📋 API Docs: $SERVICE_URL/docs"
echo "🔍 Detailed Health: $SERVICE_URL/api/health/detailed"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
echo "Waiting 30 seconds for service to be ready..."
sleep 30

echo "Testing health endpoint..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️ Health check failed - service may still be starting up"
fi

echo ""
echo "📋 Deployment Summary:"
echo "- Service: $SERVICE_NAME"
echo "- Region: $REGION"
echo "- URL: $SERVICE_URL"
echo "- Memory: $MEMORY"
echo "- CPU: $CPU"
echo "- Max Instances: $MAX_INSTANCES"
echo ""
echo "🎉 Deployment complete! Your Legal Saathi app is now live on Cloud Run."
echo ""