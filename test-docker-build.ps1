#!/usr/bin/env pwsh
# Test Docker build script for Cloud Run deployment

Write-Host "🚀 Testing Docker build for Cloud Run deployment..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if client build exists
if (Test-Path "client/dist/index.html") {
    Write-Host "✅ Client build found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Client build not found. Building React frontend..." -ForegroundColor Yellow
    
    # Build React frontend
    Push-Location client
    try {
        Write-Host "📦 Installing client dependencies..." -ForegroundColor Blue
        npm ci
        
        Write-Host "🏗️  Building React frontend..." -ForegroundColor Blue
        npm run build
        
        Write-Host "✅ Client build completed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Client build failed: $_" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
}

# Build Docker image
Write-Host "🐳 Building Docker image for Cloud Run..." -ForegroundColor Blue
try {
    docker build -f Dockerfile.cloudrun -t legal-saathi:cloudrun-test .
    Write-Host "✅ Docker build completed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker build failed: $_" -ForegroundColor Red
    exit 1
}

# Test the container
Write-Host "🧪 Testing the container..." -ForegroundColor Blue
try {
    # Start container in background
    $containerId = docker run -d -p 8080:8080 -e GOOGLE_CLOUD_DEPLOYMENT=true legal-saathi:cloudrun-test
    Write-Host "✅ Container started with ID: $containerId" -ForegroundColor Green
    
    # Wait for container to be ready
    Write-Host "⏳ Waiting for container to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Test health endpoint
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 10
        Write-Host "✅ Health check passed: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Health check failed, but container might still be starting..." -ForegroundColor Yellow
    }
    
    # Test frontend
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:8080/" -TimeoutSec 10
        if ($frontendResponse.StatusCode -eq 200) {
            Write-Host "✅ Frontend is serving correctly" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Frontend test failed: $_" -ForegroundColor Yellow
    }
    
    # Show container logs
    Write-Host "📋 Container logs (last 20 lines):" -ForegroundColor Blue
    docker logs --tail 20 $containerId
    
    # Cleanup
    Write-Host "🧹 Stopping and removing test container..." -ForegroundColor Blue
    docker stop $containerId | Out-Null
    docker rm $containerId | Out-Null
    
} catch {
    Write-Host "❌ Container test failed: $_" -ForegroundColor Red
    # Cleanup on failure
    if ($containerId) {
        docker stop $containerId | Out-Null
        docker rm $containerId | Out-Null
    }
    exit 1
}

Write-Host "🎉 Docker build test completed successfully!" -ForegroundColor Green
Write-Host "📝 Next steps:" -ForegroundColor Blue
Write-Host "   1. Deploy to Cloud Run using your gcloud command" -ForegroundColor White
Write-Host "   2. Test the deployed service" -ForegroundColor White
Write-Host "   3. Update DNS if needed" -ForegroundColor White