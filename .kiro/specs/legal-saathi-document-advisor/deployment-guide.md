# LegalSaathi Free Deployment Guide

## Free Deployment Options

### Option 1: Railway (Recommended)
**Why Railway**: Simple deployment, generous free tier, automatic HTTPS, good for demos

#### Setup Steps
1. **Prepare Repository**
```bash
# Create requirements.txt
pip freeze > requirements.txt

# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Deploy to Railway**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

3. **Environment Variables**
```bash
railway variables set GOOGLE_CLOUD_PROJECT=your-project-id
railway variables set GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
railway variables set FLASK_ENV=production
```

### Option 2: Render
**Why Render**: Excellent free tier, automatic deployments, built-in monitoring

#### Setup Steps
1. **Create render.yaml**
```yaml
services:
  - type: web
    name: legalsaathi
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
      - key: GOOGLE_CLOUD_PROJECT
        fromDatabase:
          name: google-project-id
          property: connectionString
```

2. **Deploy via GitHub**
- Connect GitHub repository
- Auto-deploy on push to main branch
- Set environment variables in dashboard

### Option 3: Google Cloud Run (Free Tier)
**Why Cloud Run**: Native Google Cloud integration, serverless scaling

#### Setup Steps
1. **Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
```

2. **Deploy to Cloud Run**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/legalsaathi
gcloud run deploy --image gcr.io/PROJECT-ID/legalsaathi --platform managed
```

### Option 4: Heroku (Limited Free Tier)
**Why Heroku**: Simple deployment, good for prototypes

#### Setup Steps
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set GOOGLE_CLOUD_PROJECT=your-project-id

# Deploy
git push heroku main
```

## Google Cloud AI Setup (Free Tier)

### 1. Create Google Cloud Project
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and create project
gcloud init
gcloud projects create your-project-id
gcloud config set project your-project-id
```

### 2. Enable Required APIs
```bash
# Enable necessary APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable translate.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. Create Service Account
```bash
# Create service account
gcloud iam service-accounts create legalsaathi-service \
    --description="LegalSaathi AI Service Account" \
    --display-name="LegalSaathi Service"

# Grant necessary roles
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:legalsaathi-service@your-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:legalsaathi-service@your-project-id.iam.gserviceaccount.com" \
    --role="roles/cloudtranslate.user"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=legalsaathi-service@your-project-id.iam.gserviceaccount.com
```

### 4. Free Tier Limits
- **Vertex AI**: 20 requests per minute, 1000 requests per day
- **Translate API**: 500,000 characters per month
- **Cloud Run**: 2 million requests per month
- **Cloud Build**: 120 build-minutes per day

## Environment Configuration

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/legalsaathi.git
cd legalsaathi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export FLASK_ENV="development"

# Run application
python app.py
```

### Production Environment Variables
```bash
# Required for all deployments
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Optional optimizations
WORKERS=1
THREADS=8
TIMEOUT=30
MAX_CONTENT_LENGTH=16777216  # 16MB file limit
```

## Cost Optimization Strategies

### 1. API Usage Optimization
```python
# Implement caching for common analyses
import functools
from datetime import datetime, timedelta

@functools.lru_cache(maxsize=100)
def analyze_common_clause(clause_hash):
    # Cache frequently analyzed clauses
    pass

# Batch processing for multiple documents
def batch_analyze_documents(documents):
    # Process multiple documents in single API call
    pass
```

### 2. Request Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

@app.route('/analyze')
@limiter.limit("5 per minute")
def analyze_document():
    # Rate limited endpoint
    pass
```

### 3. Fallback Strategies
```python
# Local model fallback when API limits reached
def analyze_with_fallback(text):
    try:
        return google_cloud_analysis(text)
    except QuotaExceededError:
        return local_model_analysis(text)
    except Exception as e:
        return basic_rule_based_analysis(text)
```

## Monitoring & Analytics (Free Tools)

### 1. Google Cloud Monitoring
```python
from google.cloud import monitoring_v3

def track_api_usage():
    client = monitoring_v3.MetricServiceClient()
    # Track API calls, response times, error rates
```

### 2. Application Performance
```python
import logging
from datetime import datetime

# Simple logging for performance tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def log_analysis_metrics(doc_type, processing_time, risk_level):
    logging.info(f"Analysis: {doc_type}, Time: {processing_time}s, Risk: {risk_level}")
```

### 3. User Analytics (Privacy-Compliant)
```python
# Track usage without storing personal data
def track_usage_stats():
    stats = {
        'document_type': request.form.get('doc_type'),
        'analysis_time': time.time() - start_time,
        'risk_level': analysis_result.risk_level,
        'timestamp': datetime.utcnow(),
        'user_agent': request.headers.get('User-Agent')
    }
    # Store aggregated stats only
```

## Security Configuration

### 1. HTTPS Enforcement
```python
from flask_talisman import Talisman

# Force HTTPS in production
if app.config['ENV'] == 'production':
    Talisman(app, force_https=True)
```

### 2. Input Validation
```python
from werkzeug.utils import secure_filename
import bleach

def validate_document_input(text):
    # Sanitize input
    clean_text = bleach.clean(text, strip=True)
    
    # Validate length
    if len(clean_text) > 50000:  # 50KB limit
        raise ValueError("Document too large")
    
    return clean_text
```

### 3. API Key Security
```python
import os
from cryptography.fernet import Fernet

# Encrypt API keys in environment
def decrypt_api_key():
    key = os.environ.get('ENCRYPTION_KEY')
    encrypted_key = os.environ.get('ENCRYPTED_API_KEY')
    
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()
```

## Troubleshooting Common Issues

### 1. Google Cloud Authentication
```bash
# Check authentication
gcloud auth list
gcloud config list

# Re-authenticate if needed
gcloud auth application-default login
```

### 2. API Quota Issues
```python
# Handle quota exceeded gracefully
from google.api_core.exceptions import ResourceExhausted

try:
    result = vertex_ai_client.predict(...)
except ResourceExhausted:
    # Switch to fallback model or queue for later
    return fallback_analysis(document)
```

### 3. Memory Issues on Free Tiers
```python
# Optimize memory usage
import gc

def analyze_large_document(text):
    # Process in chunks
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    results = []
    
    for chunk in chunks:
        result = analyze_chunk(chunk)
        results.append(result)
        gc.collect()  # Force garbage collection
    
    return combine_results(results)
```

## Performance Optimization

### 1. Caching Strategy
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=3600)  # Cache for 1 hour
def analyze_standard_clause(clause_text):
    return ai_analysis(clause_text)
```

### 2. Async Processing
```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

async def analyze_document_async(document):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, 
            google_cloud_analysis, 
            document
        )
    return result
```

### 3. Database Optimization (if using)
```python
# Use SQLite for simple caching
import sqlite3

def cache_analysis_result(doc_hash, result):
    conn = sqlite3.connect('cache.db')
    conn.execute(
        "INSERT OR REPLACE INTO analysis_cache VALUES (?, ?, ?)",
        (doc_hash, result, datetime.utcnow())
    )
    conn.commit()
    conn.close()
```

## Backup & Recovery

### 1. Configuration Backup
```bash
# Backup environment variables
env | grep -E "(GOOGLE|FLASK)" > .env.backup

# Backup service account key
cp key.json key.json.backup
```

### 2. Application State
```python
# Simple state persistence
import pickle

def save_application_state():
    state = {
        'analysis_cache': analysis_cache,
        'user_sessions': active_sessions,
        'performance_metrics': metrics
    }
    with open('app_state.pkl', 'wb') as f:
        pickle.dump(state, f)

def restore_application_state():
    try:
        with open('app_state.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return default_state()
```

## Scaling Preparation

### 1. Database Migration Path
```python
# Prepare for PostgreSQL migration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local.db')

if DATABASE_URL.startswith('postgres'):
    # PostgreSQL configuration
    pass
else:
    # SQLite configuration
    pass
```

### 2. Microservices Preparation
```python
# Separate analysis service
class AnalysisService:
    def __init__(self, config):
        self.config = config
    
    def analyze(self, document):
        # Isolated analysis logic
        pass

# API endpoint for microservice
@app.route('/api/v1/analyze', methods=['POST'])
def api_analyze():
    service = AnalysisService(app.config)
    return service.analyze(request.json)
```

This deployment guide provides multiple free options and scales from development to production while maintaining cost efficiency and performance.