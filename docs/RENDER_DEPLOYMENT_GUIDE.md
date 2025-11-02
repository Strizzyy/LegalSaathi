# Render.com Deployment Guide for LegalSaathi

## Overview

This guide walks you through deploying the LegalSaathi application on Render.com with the updated FastAPI backend and React frontend.

## Prerequisites

- Render.com account
- GitHub repository with your code
- Google Cloud Platform account with API keys
- Environment variables configured

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your repository has the updated files:
- ✅ `render.yaml` (updated for FastAPI)
- ✅ `requirements.txt` (FastAPI dependencies)
- ✅ `main.py` (FastAPI application)
- ✅ `client/` directory with React app
- ✅ `google-cloud-credentials.json` (if using service account)

### 2. Update Environment Variables

In your Render.com dashboard, configure these environment variables:

#### Required Variables
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
```

#### Optional Variables
```bash
ENVIRONMENT=production
GOOGLE_APPLICATION_CREDENTIALS=./google-cloud-credentials.json
```

### 3. Configure Google Cloud Services

#### Enable Required APIs
1. Go to Google Cloud Console
2. Enable these APIs:
   - Gemini API (AI Platform)
   - Document AI API
   - Translation API
   - Speech-to-Text API
   - Text-to-Speech API
   - Natural Language API

#### Create Service Account (Recommended)
1. Go to IAM & Admin > Service Accounts
2. Create new service account
3. Grant these roles:
   - AI Platform User
   - Document AI API User
   - Cloud Translation API User
   - Speech API User
4. Download JSON key file
5. Rename to `google-cloud-credentials.json`
6. Place in your repository root

### 4. Deploy to Render

#### Option A: Using render.yaml (Recommended)

1. Connect your GitHub repository to Render
2. Render will automatically detect `render.yaml`
3. Review the configuration:

```yaml
services:
  - type: web
    name: legalsaathi-document-advisor
    env: python
    plan: free
    buildCommand: |
      # Install Node.js and build frontend
      curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
      sudo apt-get install -y nodejs
      cd client && npm ci && npm run build && cd ..
      # Install Python dependencies
      pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: GEMINI_API_KEY
        sync: false            
      - key: GOOGLE_CLOUD_PROJECT_ID
        sync: false
      - key: GOOGLE_CLOUD_LOCATION
        sync: false
      - key: DOCUMENT_AI_PROCESSOR_ID
        sync: false
      - key: GOOGLE_APPLICATION_CREDENTIALS
        value: ./google-cloud-credentials.json
    healthCheckPath: /health
```

4. Click "Deploy"

#### Option B: Manual Configuration

1. Create new Web Service
2. Connect GitHub repository
3. Configure build settings:
   - **Build Command**: 
     ```bash
     curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash- && sudo apt-get install -y nodejs && cd client && npm ci && npm run build && cd .. && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
     ```

### 5. Configure Environment Variables in Render Dashboard

1. Go to your service dashboard
2. Click "Environment" tab
3. Add each environment variable:

```
ENVIRONMENT = production
GEMINI_API_KEY = [your-api-key]
GOOGLE_CLOUD_PROJECT_ID = [your-project-id]
GOOGLE_CLOUD_LOCATION = us-central1
DOCUMENT_AI_PROCESSOR_ID = [your-processor-id]
GOOGLE_APPLICATION_CREDENTIALS = ./google-cloud-credentials.json
```

### 6. Verify Deployment

#### Check Health Endpoints
1. Visit `https://your-app.onrender.com/health`
2. Should return:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-01T00:00:00Z",
     "version": "2.0.0"
   }
   ```

#### Test API Endpoints
1. Visit `https://your-app.onrender.com/docs`
2. Test document analysis endpoint
3. Verify Google Cloud services are working

#### Check Frontend
1. Visit `https://your-app.onrender.com`
2. Upload a test document
3. Verify all features work

## Troubleshooting Common Issues

### Build Failures

#### Node.js Installation Issues
```bash
# If Node.js installation fails, try:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash-
sudo apt-get install -y nodejs
```

#### Python Dependencies Issues
```bash
# If pip install fails, try:
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Runtime Issues

#### Google Cloud Authentication
```python
# Check if credentials are loaded
import os
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Verify service account file exists
import json
with open("google-cloud-credentials.json") as f:
    creds = json.load(f)
    print("Project ID:", creds.get("project_id"))
```

#### API Key Issues
```python
# Verify API keys are loaded
import os
print("GEMINI_API_KEY exists:", bool(os.getenv("GEMINI_API_KEY")))
print("PROJECT_ID:", os.getenv("GOOGLE_CLOUD_PROJECT_ID"))
```

### Performance Issues

#### Memory Optimization
```python
# In main.py, reduce workers if memory issues:
# startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

#### Timeout Issues
```yaml
# Add timeout configuration to render.yaml:
services:
  - type: web
    # ... other config
    healthCheckPath: /health
    healthCheckTimeout: 30
```

## Monitoring and Maintenance

### Health Monitoring
- Use `/health` endpoint for basic health checks
- Use `/api/health/detailed` for service-specific status
- Monitor logs in Render dashboard

### Performance Monitoring
- Check response times in Render metrics
- Monitor memory and CPU usage
- Set up alerts for service failures

### Log Analysis
```bash
# Common log patterns to watch for:
# - "GEMINI_API_KEY not found" - API key issue
# - "Failed to initialize" - Service initialization problem
# - "HTTP 500" - Server errors
# - "Rate limit exceeded" - API quota issues
```

## Scaling Considerations

### Horizontal Scaling
```yaml
# Update render.yaml for more workers:
startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
```

### Vertical Scaling
- Upgrade to paid Render plan for more resources
- Consider using Render's autoscaling features

### Database Considerations
- Current setup uses local file storage
- For production scale, consider:
  - PostgreSQL for structured data
  - Redis for caching
  - Cloud storage for file uploads

## Security Best Practices

### Environment Variables
- Never commit API keys to repository
- Use Render's environment variable encryption
- Rotate API keys regularly

### File Upload Security
- Validate file types and sizes
- Scan uploaded files for malware
- Use temporary storage for processing

### API Security
- Implement rate limiting (already configured)
- Add authentication for sensitive endpoints
- Monitor for unusual usage patterns

## Cost Optimization

### Free Tier Limitations
- 750 hours/month (sufficient for most use cases)
- Sleeps after 15 minutes of inactivity
- Limited to 512MB RAM

### Paid Plan Benefits
- No sleep mode
- More memory and CPU
- Custom domains
- Priority support

### API Cost Management
```python
# Monitor Google Cloud API usage:
# - Set up billing alerts
# - Implement caching to reduce API calls
# - Use batch processing where possible
```

## Backup and Recovery

### Code Backup
- Repository is backed up on GitHub
- Use GitHub releases for version management

### Data Backup
```python
# Backup user data and cache:
import shutil
import datetime

def backup_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.make_archive(f"backup_{timestamp}", "zip", "data/")
```

### Disaster Recovery
1. Keep render.yaml updated
2. Document all environment variables
3. Test deployment process regularly
4. Have rollback plan ready

## Support and Resources

### Render Documentation
- [Render Docs](https://render.com/docs)
- [Python on Render](https://render.com/docs/deploy-fastapi)
- [Environment Variables](https://render.com/docs/environment-variables)

### Google Cloud Documentation
- [AI Platform](https://cloud.google.com/ai-platform/docs)
- [Document AI](https://cloud.google.com/document-ai/docs)
- [Translation API](https://cloud.google.com/translate/docs)

### Getting Help
- Render Community Forum
- GitHub Issues for code problems
- Google Cloud Support for API issues

## Conclusion

Following this guide should result in a successful deployment of LegalSaathi on Render.com. The application will be accessible at your Render URL and ready to process legal documents using Google Cloud AI services.

Remember to:
- Monitor your Google Cloud API usage and costs
- Keep your dependencies updated
- Regularly check application health and performance
- Have a backup and recovery plan in place