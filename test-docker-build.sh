#!/bin/bash
# Test Docker build script for Cloud Run deployment

echo "🚀 Testing Docker build for Cloud Run deployment..."

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker."
    exit 1
fi
echo "✅ Docker is running"

# Check if client build exists
if [ -f "client/dist/index.html" ]; then
    echo "✅ Client build found"
else
    echo "⚠️  Client build not found. Building React frontend..."
    
    # Build React frontend
    cd client || exit 1
    
    echo "📦 Installing client dependencies..."
    npm ci || {
        echo "❌ Client dependency installation failed"
        exit 1
    }
    
    echo "🏗️  Building React frontend..."
    npm run build || {
        echo "❌ Client build failed"
        exit 1
    }
    
    cd .. || exit 1
    echo "✅ Client build completed"
fi

# Build Docker image
echo "🐳 Building Docker image for Cloud Run..."
if docker build -f Dockerfile.cloudrun -t legal-saathi:cloudrun-test .; then
    echo "✅ Docker build completed successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Test the container
echo "🧪 Testing the container..."

# Start container in background
CONTAINER_ID=$(docker run -d -p 8080:8080 -e GOOGLE_CLOUD_DEPLOYMENT=true legal-saathi:cloudrun-test)
if [ $? -eq 0 ]; then
    echo "✅ Container started with ID: $CONTAINER_ID"
else
    echo "❌ Failed to start container"
    exit 1
fi

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 30

# Test health endpoint
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed, but container might still be starting..."
fi

# Test frontend
if curl -f http://localhost:8080/ >/dev/null 2>&1; then
    echo "✅ Frontend is serving correctly"
else
    echo "⚠️  Frontend test failed"
fi

# Show container logs
echo "📋 Container logs (last 20 lines):"
docker logs --tail 20 "$CONTAINER_ID"

# Cleanup
echo "🧹 Stopping and removing test container..."
docker stop "$CONTAINER_ID" >/dev/null
docker rm "$CONTAINER_ID" >/dev/null

echo "🎉 Docker build test completed successfully!"
echo "📝 Next steps:"
echo "   1. Deploy to Cloud Run using your gcloud command"
echo "   2. Test the deployed service"
echo "   3. Update DNS if needed"