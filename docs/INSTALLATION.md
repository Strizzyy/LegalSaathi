# LegalSaathi Installation Guide
*Complete Setup Instructions for Development and Production*

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [Development Setup](#development-setup)
6. [Production Deployment](#production-deployment)
7. [Docker Deployment](#docker-deployment)
8. [Cloud Run Deployment](#cloud-run-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Stable internet connection for AI services

### Required Software
- **Python**: 3.8 or higher (3.12 recommended)
- **Node.js**: 16.0 or higher (18+ recommended)
- **npm**: 8.0 or higher (comes with Node.js)
- **Git**: Latest version for version control

### Optional Tools
- **uv**: Fast Python package manager (recommended)
- **Docker**: For containerized deployment
- **Make**: For using Makefile commands (Linux/macOS)

---

## Quick Start

### Automated Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/your-repo/legal-saathi-document-advisor.git
cd legal-saathi-document-advisor

# Run automated setup
python setup.py
```

This script will:
- Install Python dependencies
- Install frontend dependencies
- Create environment files
- Verify configuration
- Start development servers

### Manual Quick Start
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd client
npm install
cd ..

# 3. Set up environment variables
cp .env.example .env
cp client/.env.local.example client/.env.local

# 4. Start development servers
# Terminal 1 - Backend
python main.py

# Terminal 2 - Frontend
cd client
npm run dev
```

---

## Detailed Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/your-repo/legal-saathi-document-advisor.git
cd legal-saathi-document-advisor
```

### Step 2: Python Environment Setup

#### Option A: Using uv (Recommended)
```bash
# Install uv if not already installed
pip install uv

# Create virtual environment and install dependencies
uv sync
```

#### Option B: Using pip and venv
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Frontend Setup
```bash
cd client
npm install
cd ..
```

### Step 4: Environment Configuration
```bash
# Copy environment templates
cp .env.example .env
cp client/.env.local.example client/.env.local

# Edit configuration files (see Configuration section)
```

---

## Configuration

### Backend Configuration (.env)

Create a `.env` file in the root directory with the following variables:

```env
# API Keys
GROQ_API_KEY=your-groq-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=google-cloud-credentials.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us-central1

# Firebase Configuration
FIREBASE_ADMIN_CREDENTIALS_PATH=firebase-admin-credentials.json

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
ANONYMOUS_RATE_LIMIT=5
AUTHENTICATED_RATE_LIMIT=15

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_ANALYSIS=3600
CACHE_TTL_TRANSLATION=86400
CACHE_TTL_SPEECH=21600

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Neo4j Configuration (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

### Frontend Configuration (client/.env.local)

Create a `client/.env.local` file with Firebase configuration:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=your-app-id

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

### Google Cloud Credentials

#### 1. Google Cloud Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable required APIs:
   - Gemini API
   - Document AI API
   - Vision API
   - Translation API
   - Speech-to-Text API
   - Text-to-Speech API
   - Natural Language AI API
   - Vertex AI API
4. Create a service account with appropriate permissions
5. Download the JSON key file as `google-cloud-credentials.json`

#### 2. Firebase Admin SDK
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing project
3. Go to Project Settings > Service Accounts
4. Generate new private key
5. Download the JSON file as `firebase-admin-credentials.json`

#### 3. API Keys
- **Groq API**: Sign up at [Groq Console](https://console.groq.com/)
- **Gemini API**: Get key from [Google AI Studio](https://makersuite.google.com/)

---

## Development Setup

### Starting Development Servers

#### Using Makefile (Linux/macOS)
```bash
make dev
```

#### Manual Start
```bash
# Terminal 1 - Backend Server
python main.py

# Terminal 2 - Frontend Development Server
cd client
npm run dev
```

### Development URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Docs**: http://localhost:8000/redoc

### Development Tools

#### Code Quality
```bash
# Python linting and formatting
pip install black flake8 mypy
black .
flake8 .
mypy .

# Frontend linting and formatting
cd client
npm run lint
npm run format
```

#### Testing
```bash
# Backend tests
pytest

# Frontend tests
cd client
npm test
```

### Hot Reload
Both frontend and backend support hot reload:
- **Frontend**: Vite provides instant HMR
- **Backend**: FastAPI auto-reloads on file changes

---

## Production Deployment

### Environment Preparation
```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false

# Install production dependencies only
pip install --no-dev -r requirements.txt
```

### Build Frontend
```bash
cd client
npm run build
cd ..
```

### Production Server
```bash
# Install production server
pip install gunicorn

# Start production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Nginx Configuration (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build
```bash
# Build Docker image
docker build -t legal-saathi .

# Run container
docker run -d \
  --name legal-saathi \
  -p 8000:8000 \
  --env-file .env \
  legal-saathi
```

### Docker Configuration

#### Dockerfile
The project includes optimized Dockerfiles:
- `Dockerfile`: Standard deployment
- `Dockerfile.cloudrun`: Optimized for Google Cloud Run

#### docker-compose.yml
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./google-cloud-credentials.json:/app/google-cloud-credentials.json
      - ./firebase-admin-credentials.json:/app/firebase-admin-credentials.json
    restart: unless-stopped

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/your-password
    volumes:
      - neo4j_data:/data
    restart: unless-stopped

volumes:
  neo4j_data:
```

---

## Cloud Run Deployment

### Prerequisites
- Google Cloud SDK installed
- Docker installed
- Google Cloud project with billing enabled

### Deployment Steps

#### 1. Build and Push Container
```bash
# Configure Docker for Google Cloud
gcloud auth configure-docker

# Build container for Cloud Run
docker build -f Dockerfile.cloudrun -t gcr.io/YOUR_PROJECT_ID/legal-saathi .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/legal-saathi
```

#### 2. Deploy to Cloud Run
```bash
gcloud run deploy legal-saathi \
  --image gcr.io/YOUR_PROJECT_ID/legal-saathi \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production
```

#### 3. Set Environment Variables
```bash
# Set required environment variables
gcloud run services update legal-saathi \
  --set-env-vars GROQ_API_KEY=your-key \
  --set-env-vars GEMINI_API_KEY=your-key \
  --set-env-vars GOOGLE_CLOUD_PROJECT_ID=your-project-id
```

### Cloud Run Configuration
The application includes Cloud Run optimizations:
- Startup probes for health checks
- Graceful shutdown handling
- Resource optimization
- Automatic scaling configuration

---

## Troubleshooting

### Common Issues

#### 1. Python Dependencies
**Error**: `ModuleNotFoundError`
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

#### 2. Node.js Dependencies
**Error**: `Module not found` or `npm ERR!`
**Solution**:
```bash
cd client
rm -rf node_modules package-lock.json
npm install
```

#### 3. Environment Variables
**Error**: `KeyError` or missing configuration
**Solution**:
- Verify `.env` file exists and has correct values
- Check file permissions
- Ensure no trailing spaces in values

#### 4. Google Cloud Authentication
**Error**: `DefaultCredentialsError`
**Solution**:
```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Or authenticate with gcloud
gcloud auth application-default login
```

#### 5. Firebase Authentication
**Error**: `Firebase Admin SDK not initialized`
**Solution**:
- Verify `firebase-admin-credentials.json` exists
- Check Firebase project configuration
- Ensure service account has correct permissions

#### 6. Port Conflicts
**Error**: `Address already in use`
**Solution**:
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
export PORT=8001
```

### Performance Issues

#### Slow Startup
- Check internet connection for AI service initialization
- Verify Google Cloud credentials are valid
- Consider using optimized startup manager

#### Memory Issues
- Increase system memory allocation
- Use Docker with memory limits
- Monitor memory usage with system tools

### Getting Help

#### Log Files
Check log files for detailed error information:
- `legal_saathi.log`: Application logs
- Browser console: Frontend errors
- Docker logs: `docker logs container-name`

#### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

#### Support Channels
- **Documentation**: Check docs/ directory
- **GitHub Issues**: Report bugs and feature requests
- **Community Forum**: User discussions and help
- **Email Support**: support@legalsaathi.com

---

## Advanced Configuration

### Custom AI Models
Configure custom AI model endpoints:
```env
# Custom Gemini endpoint
GEMINI_API_ENDPOINT=https://your-custom-endpoint.com

# Custom model parameters
GEMINI_MODEL_NAME=gemini-pro-custom
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=2048
```

### Caching Configuration
Advanced caching settings:
```env
# Redis cache (optional)
REDIS_URL=redis://localhost:6379
CACHE_BACKEND=redis

# Cache TTL settings (seconds)
CACHE_TTL_ANALYSIS=3600      # 1 hour
CACHE_TTL_TRANSLATION=86400  # 24 hours
CACHE_TTL_SPEECH=21600       # 6 hours
CACHE_TTL_EMBEDDINGS=604800  # 7 days
```

### Monitoring and Logging
```env
# Logging configuration
LOG_FORMAT=json
LOG_FILE=legal_saathi.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
```

### Security Configuration
```env
# Security settings
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_COOKIES=true
CSRF_PROTECTION=true

# Rate limiting
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_STRATEGY=sliding-window
```

---

## Maintenance

### Regular Updates
```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update frontend dependencies
cd client
npm update
```

### Database Maintenance
```bash
# Neo4j maintenance (if using)
# Backup database
docker exec neo4j-container neo4j-admin backup --to=/backups

# Clean up old data
# Run cleanup scripts as needed
```

### Log Rotation
Set up log rotation to prevent disk space issues:
```bash
# Linux logrotate configuration
sudo nano /etc/logrotate.d/legal-saathi
```

### Health Monitoring
Set up monitoring for production:
- Health check endpoints: `/health`, `/api/health/ready`
- Performance metrics: `/api/health/metrics`
- Error tracking and alerting

---

*Last Updated: November 2024*
*Version: 2.0.0*