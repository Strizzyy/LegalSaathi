#!/bin/bash

# Optimized Google Cloud Run Deployment Script for LegalSaathi
# This script deploys the application with optimized settings for fast startup

set -e

echo "🚀 Starting optimized Google Cloud Run deployment..."

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"legal-saathi-project"}
SERVICE_NAME="legal-saathi"
REGION="us-central1"
MEMORY="2Gi"
CPU="2"
MAX_INSTANCES="10"
TIMEOUT="300"
CONCURRENCY="100"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project if provided
if [ ! -z "$PROJECT_ID" ]; then
    echo "📋 Setting project to: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Clean up local files before deployment
echo "🧹 Cleaning up unnecessary files..."
rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
rm -f *.log *.db
rm -rf .pytest_cache/ .venv/ node_modules/
rm -f client/node_modules/ client/.env client/npx client/void client/void' client/{

# Build and deploy with optimized settings
echo "🏗️ Building and deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --dockerfile Dockerfile.cloudrun \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --max-instances $MAX_INSTANCES \
    --timeout $TIMEOUT \
    --concurrency $CONCURRENCY \
    --set-env-vars GOOGLE_CLOUD_DEPLOYMENT=true \
    --set-env-vars PORT=8080 \
    --set-env-vars TRANSFORMERS_OFFLINE=1 \
    --set-env-vars HF_HUB_OFFLINE=1 \
    --execution-environment gen2 \
    --cpu-boost \
    --session-affinity

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Health check: $SERVICE_URL/health"
echo "📊 Admin dashboard: $SERVICE_URL/admin"

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Health check passed!"
else
    echo "⚠️ Health check failed - service may still be starting up"
    echo "Please wait a few moments and check: $SERVICE_URL/health"
fi

echo "🎉 Google Cloud Run deployment completed!"
echo ""
echo "📋 Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Memory: $MEMORY"
echo "   CPU: $CPU"
echo "   Max Instances: $MAX_INSTANCES"
echo "   URL: $SERVICE_URL"
echo ""
echo "🔧 To update environment variables:"
echo "   gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars KEY=VALUE"
echo ""
echo "📊 To view logs:"
echo "   gcloud logs tail --follow --resource-type=cloud_run_revision --resource-labels=service_name=$SERVICE_NAME"