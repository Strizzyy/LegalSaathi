# Legal Saathi - Render Deployment Guide

This guide will help you deploy Legal Saathi Document Advisor to Render.com.

## Prerequisites

- GitHub or GitLab account
- Render.com account
- Google Cloud Platform account (for AI services)
- API keys for required services

## Pre-Deployment Checklist

### 1. Run Deployment Script

**Windows:**
```bash
deploy.bat
```

**Linux/Mac:**
```bash
./deploy.sh
```

This script will:
- ✅ Verify project structure
- ✅ Install Python dependencies
- ✅ Build the React frontend
- ✅ Test FastAPI application import
- ✅ Check for required files

### 2. Verify Files

Ensure these files are present:
- `render.yaml` - Render deployment configuration
- `requirements.txt` - Python dependencies
- `main.py` - FastAPI application entry point
- `client/dist/` - Built React frontend (created by deployment script)
- `google-cloud-credentials.json` - Google Cloud service account key

## Deployment Steps

### Step 1: Push to Repository

1. Commit all changes to your Git repository:
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub/GitLab repository
4. Select your Legal Saathi repository

### Step 3: Configure Service

Render will automatically detect the `render.yaml` file. Verify these settings:

- **Name:** `legalsaathi-document-advisor`
- **Environment:** `Python`
- **Build Command:** (Auto-detected from render.yaml)
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2`
- **Plan:** Free (or upgrade as needed)

### Step 4: Set Environment Variables

In the Render dashboard, go to Environment and add these variables:

#### Required Variables:
```
ENVIRONMENT=production
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_CLOUD_LOCATION=us
GOOGLE_APPLICATION_CREDENTIALS=./google-cloud-credentials.json
```

#### Optional Variables (if using these services):
```
GEMINI_API_KEY=your_gemini_api_key (fallback service)
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
```

### Step 5: Upload Secret Files

1. In Render dashboard, go to "Secret Files"
2. Upload `google-cloud-credentials.json` with filename `google-cloud-credentials.json`

### Step 6: Deploy

1. Click "Create Web Service"
2. Render will start building and deploying your application
3. Monitor the build logs for any issues

## Post-Deployment

### Health Check

Once deployed, verify your application is running:
- Health endpoint: `https://your-app.onrender.com/health`
- API documentation: `https://your-app.onrender.com/docs`
- Frontend: `https://your-app.onrender.com/`

### Expected Health Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "services": {
    "translation": true,
    "file_processing": true,
    "document_analysis": true,
    "google_document_ai": true,
    "google_natural_language": true,
    "google_speech": true,
    "export": true
  },
  "cache": {
    "size": 0,
    "status": "operational"
  }
}
```

## Troubleshooting

### Common Issues:

#### 1. Build Fails - Node.js Issues
- Ensure Node.js 18+ is specified in render.yaml
- Check that `client/package.json` has correct dependencies

#### 2. Python Import Errors
- Verify all dependencies are in `requirements.txt`
- Check that all Python files are properly committed

#### 3. Google Cloud Services Not Working
- Verify `google-cloud-credentials.json` is uploaded as a secret file
- Check that `GOOGLE_CLOUD_PROJECT_ID` is set correctly
- Ensure Google Cloud APIs are enabled in your GCP project

#### 4. Environment Variables Not Set
- Double-check all required environment variables in Render dashboard
- Ensure sensitive values are marked as "secret"

#### 5. Frontend Not Loading
- Verify the build command completed successfully
- Check that `client/dist` directory was created during build
- Ensure static file serving is working in `main.py`

### Logs and Debugging

1. Check build logs in Render dashboard
2. Monitor application logs for runtime errors
3. Use the health endpoint to verify service status
4. Test API endpoints using the `/docs` interface

## Performance Optimization

### For Production:

1. **Upgrade Render Plan:** Consider upgrading from Free tier for better performance
2. **Enable Caching:** The application includes built-in caching for API responses
3. **Monitor Resources:** Use Render's metrics to monitor CPU and memory usage
4. **Database:** Consider upgrading to a dedicated database service for Neo4j

### Environment-Specific Settings:

The application automatically adjusts based on the `ENVIRONMENT` variable:
- `production`: Optimized for performance and security
- `development`: Includes debug features and verbose logging

## Security Considerations

1. **API Keys:** Never commit API keys to your repository
2. **Secret Files:** Use Render's secret file feature for credentials
3. **CORS:** The application is configured for production CORS settings
4. **Rate Limiting:** Built-in rate limiting is enabled for all API endpoints

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Render's documentation
3. Check application logs in the Render dashboard
4. Verify all environment variables and secret files are correctly configured

## Updates and Maintenance

To update your deployment:
1. Make changes to your code
2. Commit and push to your repository
3. Render will automatically redeploy
4. Monitor the deployment in the Render dashboard

---

**Note:** This deployment configuration supports the full Legal Saathi feature set including:
- Document analysis with AI
- Multi-language translation
- Speech-to-text and text-to-speech
- PDF and Word export functionality
- Real-time AI clarification chat
- Document comparison tools