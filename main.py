"""
FastAPI main application for Legal Saathi Document Advisor
Replaces Flask app.py with modern async architecture and MVC pattern
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import json
import tempfile

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks, Header

# Setup Google Cloud credentials from environment variable in production
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
    # Create a temporary file to store the credentials
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON', '{}'))
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import ValidationError

# Configure logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_saathi.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Import models
from models.document_models import (
    DocumentAnalysisRequest, DocumentAnalysisResponse,
    AnalysisStatusResponse, ErrorResponse, SuccessResponse
)
from models.translation_models import (
    TranslationRequest, TranslationResponse,
    ClauseTranslationRequest, ClauseTranslationResponse,
    SupportedLanguagesResponse as TranslationLanguagesResponse,
    DocumentSummaryTranslationRequest, DocumentSummaryTranslationResponse,
    SummarySectionTranslationRequest, SummarySectionTranslationResponse,
    EnhancedSupportedLanguagesResponse, TranslationUsageStats
)
from models.speech_models import (
    SpeechToTextRequest, SpeechToTextResponse,
    TextToSpeechRequest, TextToSpeechResponse,
    SupportedLanguagesResponse as SpeechLanguagesResponse
)
from models.ai_models import (
    ClarificationRequest, ClarificationResponse,
    ConversationSummaryResponse, HealthCheckResponse
)
from models.comparison_models import (
    DocumentComparisonRequest, DocumentComparisonResponse,
    ComparisonSummaryResponse
)
from models.support_models import (
    SupportTicketRequest, SupportTicketResponse,
    ExpertsListResponse, TicketStatusResponse,
    SupportTicket
)

# Import controllers
from controllers.document_controller import DocumentController
from controllers.translation_controller import TranslationController
from controllers.speech_controller import SpeechController
from controllers.health_controller import HealthController
from controllers.ai_controller import AIController
from controllers.comparison_controller import ComparisonController
from controllers.export_controller import ExportController
from controllers.email_controller import EmailController
from controllers.support_controller import router as support_router
from controllers.auth_controller import AuthController
from controllers.insights_controller import router as insights_router
from controllers.vision_controller import VisionController
from controllers.cost_controller import get_cost_router
from controllers.expert_queue_router import router as expert_queue_router
from controllers.expert_review_email_controller import router as expert_review_email_router

# Import services for cleanup
from services.cache_service import CacheService
from middleware.firebase_auth_middleware import FirebaseAuthMiddleware, UserBasedRateLimiter

# Configure logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_saathi.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import optimized startup manager (with error handling)
try:
    from services.startup_manager import optimized_lifespan, get_startup_manager
    OPTIMIZED_STARTUP_AVAILABLE = True
    logger.info("Optimized startup manager loaded successfully")
except ImportError as e:
    logger.warning(f"Optimized startup manager not available: {e}")
    OPTIMIZED_STARTUP_AVAILABLE = False

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize cache service for cleanup
cache_service = CacheService()

# Initialize user-based rate limiter
user_rate_limiter = UserBasedRateLimiter()


# Fallback lifespan function for backward compatibility
@asynccontextmanager
async def fallback_lifespan(app: FastAPI):
    """Fallback lifespan function when optimized startup is not available"""
    # Startup
    logger.info("🚀 Starting Legal Saathi FastAPI application (fallback mode)")
    
    try:
        logger.info("🔧 Initializing core services...")
        logger.info("✅ Basic services initialized successfully")
        logger.info("🌟 Legal Saathi is ready to serve requests!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Legal Saathi FastAPI application")
    
    try:
        cache_service.clear_expired_cache()
        logger.info("🧹 Cleanup completed successfully")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")


# Choose lifespan function based on availability and environment
is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'

if OPTIMIZED_STARTUP_AVAILABLE:
    selected_lifespan = optimized_lifespan
    if is_cloud_run:
        logger.info("Using optimized service initialization for Cloud Run deployment")
    else:
        logger.info("Using optimized service initialization for local/development")
else:
    selected_lifespan = fallback_lifespan
    logger.info("Using fallback service initialization")

# Create FastAPI application
app = FastAPI(
    title="Legal Saathi Document Advisor API",
    description="AI-powered legal document analysis platform with FastAPI backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=selected_lifespan
)

# Add Firebase authentication middleware
try:
    app.add_middleware(FirebaseAuthMiddleware)
    logger.info("Firebase authentication middleware added")
except Exception as e:
    logger.warning(f"Firebase authentication middleware failed to initialize: {e}")
    logger.info("Application will run without Firebase authentication")

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://legalsaathi-document-advisor.onrender.com",
        "null"  # Allow file:// protocol for local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize controllers using optimized service manager
# Controllers are now initialized through the optimized service manager
# This provides better error handling, dependency management, and performance monitoring

def get_controller(service_name: str):
    """Get controller from optimized service manager with fallback"""
    startup_manager = get_startup_manager()
    controller = startup_manager.get_service(service_name)
    if controller is None:
        logger.warning(f"Controller {service_name} not available from service manager")
    return controller

# Get controllers from service manager (will be None until services are initialized)
document_controller = None
translation_controller = None
speech_controller = None
health_controller = None
ai_controller = None
comparison_controller = None
export_controller = None
email_controller = None
auth_controller = None
vision_controller = None

# Helper function to get controllers dynamically
# Initialize controllers directly to avoid startup manager issues
_controllers = {}

def get_initialized_controller(service_name: str):
    """Get initialized controller or create fallback"""
    # Use cached controllers to avoid re-initialization
    if service_name in _controllers:
        return _controllers[service_name]
    
    # Direct initialization for immediate functionality
    try:
        if service_name == 'document':
            controller = DocumentController()
        elif service_name == 'translation':
            controller = TranslationController()
        elif service_name == 'speech':
            controller = SpeechController()
        elif service_name == 'health':
            controller = HealthController()
        elif service_name == 'ai':
            controller = AIController()
        elif service_name == 'comparison':
            controller = ComparisonController()
        elif service_name == 'export':
            controller = ExportController()
        elif service_name == 'email':
            controller = EmailController()
        elif service_name == 'auth':
            controller = AuthController()
        elif service_name == 'vision':
            controller = VisionController()
        else:
            logger.warning(f"Unknown service: {service_name}")
            return None
        
        # Cache the controller
        _controllers[service_name] = controller
        logger.info(f"Successfully initialized {service_name} controller")
        return controller
        
    except Exception as e:
        logger.error(f"Failed to create controller for {service_name}: {e}")
        return None

# Include routers
app.include_router(support_router)
app.include_router(insights_router)
app.include_router(get_cost_router())
app.include_router(expert_queue_router)
app.include_router(expert_review_email_router)

# Include expert portal router
try:
    from controllers.expert_portal_router import router as expert_portal_router
    app.include_router(expert_portal_router)
    logger.info("Expert portal router included successfully")
except ImportError as e:
    logger.warning(f"Expert portal router not available: {e}")
except Exception as e:
    logger.error(f"Failed to include expert portal router: {e}")


# Middleware for request logging and performance monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and add performance monitoring with Cloud Run optimizations"""
    start_time = time.time()
    
    # Log request (reduced verbosity for Cloud Run)
    if not request.url.path.startswith("/health"):  # Skip health check logs
        logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)
    
    # Add optimized cache headers based on content type
    if request.url.path.startswith("/api/"):
        # API responses - short cache for dynamic content
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    elif request.url.path.startswith("/assets/"):
        # Static assets - long cache with versioning
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # 1 year
    elif request.url.path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2")):
        # Static files - medium cache
        response.headers["Cache-Control"] = "public, max-age=86400"  # 1 day
    elif request.url.path in ["/", "/index.html"]:
        # HTML files - no cache for SPA routing
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    
    # Add security headers for Cloud Run
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Log response (reduced verbosity for Cloud Run)
    if not request.url.path.startswith("/health") and process_time > 1.0:  # Only log slow requests
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "error_code": str(exc.status_code),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_code": "500",
            "timestamp": datetime.now().isoformat()
        }
    )


# Authentication endpoints
@app.post("/api/auth/verify-token")
async def verify_token(token_request: dict):
    """Verify Firebase ID token"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import FirebaseTokenRequest
    request = FirebaseTokenRequest(token=token_request.get('token', ''))
    return await controller.verify_token(request)


@app.post("/api/auth/register")
async def register_user(registration_request: dict):
    """Register a new user account"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import UserRegistrationRequest
    request = UserRegistrationRequest(**registration_request)
    return await controller.register_user(request)


@app.get("/api/auth/user-info")
async def get_user_info(request: Request):
    """Get current user information"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    return await controller.get_user_info(request)


@app.post("/api/auth/refresh-token")
async def refresh_token(refresh_request: dict):
    """Refresh Firebase token"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import RefreshTokenRequest
    request = RefreshTokenRequest(refresh_token=refresh_request.get('refresh_token', ''))
    return await controller.refresh_token(request)


@app.get("/api/auth/current-user")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    return await controller.get_current_user(request)


@app.put("/api/auth/profile")
async def update_user_profile(request: Request, update_data: dict):
    """Update user profile"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    return await controller.update_user_profile(request, update_data)


@app.delete("/api/auth/account")
async def delete_user_account(request: Request):
    """Delete user account"""
    controller = get_initialized_controller('auth')
    if not controller:
        return {"success": False, "error": "Authentication service not available"}
    return await controller.delete_user_account(request)


# Health check endpoints
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Basic health check endpoint"""
    controller = get_initialized_controller('health')
    if controller:
        return await controller.health_check()
    else:
        # Fallback health check
        return HealthCheckResponse(
            status="degraded",
            timestamp=datetime.now(),
            services={"health_controller": False},
            cache={"status": "unavailable"}
        )


@app.get("/api/health/ready")
async def check_backend_ready():
    """Check if backend is fully initialized and ready for requests"""
    if OPTIMIZED_STARTUP_AVAILABLE:
        startup_manager = get_startup_manager()
        critical_ready = startup_manager.are_critical_services_ready()
        startup_complete = startup_manager.is_startup_complete()
        
        # For frontend compatibility: if critical services are ready, consider initialization complete
        # This allows the frontend to start working while background services continue loading
        initialization_complete = critical_ready or startup_manager.service_manager.is_initialization_complete()
        
        return {
            'ready': critical_ready,
            'ready_for_requests': critical_ready,  # This is what the dev script looks for
            'startup_complete': startup_complete,
            'initialization_complete': initialization_complete,  # This is what the frontend looks for
            'status': startup_manager.get_startup_status(),
            'timestamp': datetime.now().isoformat()
        }
    else:
        # Fallback response
        return {
            'ready': True,
            'ready_for_requests': True,  # This is what the dev script looks for
            'startup_complete': True,
            'initialization_complete': True,  # This is what the frontend looks for
            'status': {'mode': 'fallback', 'optimized_startup': False},
            'timestamp': datetime.now().isoformat()
        }


@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with service information"""
    controller = get_initialized_controller('health')
    if controller:
        return await controller.detailed_health_check()
    elif OPTIMIZED_STARTUP_AVAILABLE:
        # Fallback to service manager health status
        startup_manager = get_startup_manager()
        return startup_manager.get_health_status()
    else:
        # Basic fallback response
        return {
            'overall_status': 'healthy',
            'mode': 'fallback',
            'optimized_startup': False,
            'timestamp': datetime.now().isoformat()
        }


@app.get("/api/health/metrics")
async def service_metrics():
    """Get service performance metrics"""
    controller = get_initialized_controller('health')
    if controller:
        return await controller.service_metrics()
    elif OPTIMIZED_STARTUP_AVAILABLE:
        # Fallback to service manager metrics
        startup_manager = get_startup_manager()
        return startup_manager.get_performance_metrics()
    else:
        # Basic fallback metrics
        return {
            'mode': 'fallback',
            'optimized_startup': False,
            'timestamp': datetime.now().isoformat()
        }


@app.get("/api/health/startup-performance")
async def get_startup_performance():
    """Get detailed startup performance metrics from optimized service manager"""
    if OPTIMIZED_STARTUP_AVAILABLE:
        startup_manager = get_startup_manager()
        return {
            'startup_status': startup_manager.get_startup_status(),
            'performance_metrics': startup_manager.get_performance_metrics(),
            'health_status': startup_manager.get_health_status(),
            'timestamp': datetime.now().isoformat()
        }
    else:
        return {
            'mode': 'fallback',
            'optimized_startup': False,
            'message': 'Optimized startup performance metrics not available',
            'timestamp': datetime.now().isoformat()
        }


# Document analysis endpoints
@app.post("/api/analyze", response_model=DocumentAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_document(request: Request, analysis_request: DocumentAnalysisRequest):
    """Analyze legal document text"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.analyze_document(analysis_request)


@app.post("/api/analyze/file", response_model=DocumentAnalysisResponse)
@limiter.limit("5/minute")
async def analyze_document_file(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_expertise_level: str = Form("beginner")
):
    """Analyze uploaded document file"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    
    # Get user ID from request (set by auth middleware)
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    return await controller.analyze_document_file(
        file=file,
        document_type=document_type,
        user_expertise_level=user_expertise_level,
        user_id=user_id
    )


@app.post("/api/analyze/async")
@limiter.limit("5/minute")
async def start_async_analysis(request: Request, analysis_request: DocumentAnalysisRequest):
    """Start async document analysis"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.start_async_analysis(analysis_request)


@app.get("/api/analysis/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """Get status of ongoing analysis"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.get_analysis_status(analysis_id)


@app.get("/api/analysis/{analysis_id}/clauses")
async def get_paginated_clauses(
    analysis_id: str,
    page: int = 1,
    page_size: int = 10,
    risk_filter: str = None,
    sort_by: str = "risk_score"
):
    """Get paginated clause results with filtering and sorting"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.get_paginated_clauses(
        analysis_id=analysis_id,
        page=page,
        page_size=page_size,
        risk_filter=risk_filter,
        sort_by=sort_by
    )


@app.get("/api/analysis/{analysis_id}/search")
async def search_clauses(
    analysis_id: str,
    q: str,
    fields: str = None
):
    """Search within analyzed clauses"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.search_clauses(
        analysis_id=analysis_id,
        search_query=q,
        search_fields=fields
    )


@app.get("/api/analysis/{analysis_id}/clauses/{clause_id}")
async def get_clause_details(analysis_id: str, clause_id: str):
    """Get detailed information for a specific clause"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.get_clause_details(
        analysis_id=analysis_id,
        clause_id=clause_id
    )


@app.post("/api/analysis/{analysis_id}/export")
async def export_analysis(analysis_id: str, format: str = "pdf"):
    """Export analysis results"""
    controller = get_initialized_controller('document')
    if not controller:
        raise HTTPException(status_code=503, detail="Document analysis service not available")
    return await controller.export_analysis(analysis_id, format)


# Vision API endpoints for image processing
@app.post("/api/vision/extract-text")
@limiter.limit("10/minute")
async def extract_text_from_image(
    request: Request,
    file: UploadFile = File(...),
    preprocess: bool = True
):
    """Extract text from uploaded image using Vision API"""
    controller = get_initialized_controller('vision')
    if not controller:
        raise HTTPException(status_code=503, detail="Vision API service not available")
    
    # Get user ID from request (set by auth middleware)
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    return await controller.extract_text_from_image(
        file=file,
        user_id=user_id,
        preprocess=preprocess
    )


@app.post("/api/vision/analyze-document")
@limiter.limit("5/minute")
async def analyze_image_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form("general_contract"),
    user_expertise_level: str = Form("beginner")
):
    """Analyze legal document from image using Vision API + document analysis"""
    controller = get_initialized_controller('vision')
    if not controller:
        raise HTTPException(status_code=503, detail="Vision API service not available")
    
    # Get user ID from request (set by auth middleware)
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    return await controller.analyze_image_document(
        file=file,
        document_type=document_type,
        user_expertise_level=user_expertise_level,
        user_id=user_id
    )


@app.post("/api/vision/analyze-multiple-documents")
@limiter.limit("3/minute")
async def analyze_multiple_image_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    document_type: str = Form("general_contract"),
    user_expertise_level: str = Form("beginner")
):
    """Analyze multiple legal document images using Vision API + document analysis"""
    controller = get_initialized_controller('vision')
    if not controller:
        raise HTTPException(status_code=503, detail="Vision API service not available")
    
    # Get user ID from request (set by auth middleware)
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    return await controller.analyze_multiple_image_documents(
        files=files,
        document_type=document_type,
        user_expertise_level=user_expertise_level,
        user_id=user_id
    )


@app.get("/api/vision/status")
async def get_vision_service_status():
    """Get status of Vision API services"""
    controller = get_initialized_controller('vision')
    if not controller:
        return {
            "success": False,
            "error": "Vision API service not available",
            "dual_vision_service": {"enabled": False},
            "vision_api": {"enabled": False},
            "document_ai": {"enabled": False}
        }
    
    return await controller.get_vision_service_status()


@app.get("/api/vision/supported-formats")
async def get_vision_supported_formats():
    """Get list of supported file formats for Vision API"""
    if not vision_controller:
        return {
            "success": False,
            "error": "Vision API service not available",
            "supported_formats": {"images": [], "documents": []}
        }
    
    return await vision_controller.get_supported_formats()


# Translation endpoints
@app.post("/api/translate", response_model=TranslationResponse)
@limiter.limit("20/minute")
async def translate_text(request: Request, translation_request: TranslationRequest):
    """Translate text to target language"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.translate_text(translation_request)


@app.post("/api/translate/clause", response_model=ClauseTranslationResponse)
@limiter.limit("15/minute")
async def translate_clause(request: Request, clause_request: ClauseTranslationRequest):
    """Translate legal clause with context"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.translate_clause(clause_request)


@app.get("/api/translate/languages", response_model=TranslationLanguagesResponse)
async def get_translation_languages():
    """Get supported languages for translation"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.get_supported_languages()


# Document Summary Translation endpoints
@app.post("/api/translate/document-summary", response_model=DocumentSummaryTranslationResponse)
@limiter.limit("10/minute")
async def translate_document_summary(request: Request, summary_request: DocumentSummaryTranslationRequest):
    """Translate complete document summary with all sections"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.translate_document_summary(summary_request)


@app.post("/api/translate/summary-section", response_model=SummarySectionTranslationResponse)
@limiter.limit("20/minute")
async def translate_summary_section(request: Request, section_request: SummarySectionTranslationRequest):
    """Translate individual summary section with legal context"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.translate_summary_section(section_request)


@app.get("/api/translate/languages/enhanced", response_model=EnhancedSupportedLanguagesResponse)
async def get_enhanced_translation_languages():
    """Get enhanced supported languages with metadata for document summary translation"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.get_enhanced_supported_languages()


@app.get("/api/translate/usage-stats", response_model=TranslationUsageStats)
async def get_translation_usage_stats(user_id: str = None):
    """Get translation usage statistics for monitoring"""
    controller = get_initialized_controller('translation')
    if not controller:
        raise HTTPException(status_code=503, detail="Translation service not available")
    return await controller.get_translation_usage_stats(user_id)


# Speech endpoints
@app.post("/api/speech/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    request: Request,
    audio_file: UploadFile = File(...),
    language_code: str = Form("en-US"),
    enable_punctuation: bool = Form(True)
):
    """Convert speech to text with enhanced validation and rate limiting"""
    return await speech_controller.speech_to_text(
        request=request,
        audio_file=audio_file,
        language_code=language_code,
        enable_punctuation=enable_punctuation
    )


@app.post("/api/speech/text-to-speech")
async def text_to_speech(request: Request, tts_request: TextToSpeechRequest):
    """Convert text to speech with enhanced caching and rate limiting"""
    controller = get_initialized_controller('speech')
    if not controller:
        raise HTTPException(status_code=503, detail="Speech service not available")
    return await controller.text_to_speech(request, tts_request)


@app.post("/api/speech/text-to-speech/info", response_model=TextToSpeechResponse)
async def text_to_speech_info(request: Request, tts_request: TextToSpeechRequest):
    """Get text-to-speech metadata without audio"""
    controller = get_initialized_controller('speech')
    if not controller:
        raise HTTPException(status_code=503, detail="Speech service not available")
    return await controller.get_text_to_speech_info(request, tts_request)


@app.get("/api/speech/languages", response_model=SpeechLanguagesResponse)
async def get_speech_languages():
    """Get supported languages for speech services"""
    return await speech_controller.get_supported_languages()


@app.get("/api/speech/usage-stats")
async def get_speech_usage_stats(request: Request):
    """Get speech service usage statistics for current user"""
    return await speech_controller.get_usage_stats(request)


# Admin verification function for cost monitoring endpoints
async def _verify_admin_access(token: str) -> bool:
    """Verify admin access for cost monitoring endpoints - INTERNAL USE ONLY"""
    try:
        # Get auth controller from service manager
        controller = get_initialized_controller('auth')
        if not controller:
            logger.error("Auth controller not initialized")
            return False
        
        # Use Firebase authentication with admin role checking
        is_admin = await controller.verify_admin_access(token)
        return is_admin
        
    except Exception as e:
        logger.error(f"Error verifying admin access: {e}")
        return False


# ADMIN-ONLY Cost monitoring and analytics endpoints (INTERNAL USE ONLY)
@app.get("/api/admin/costs/analytics")
@limiter.limit("30/minute")
async def get_cost_analytics(request: Request, days: int = 30, authorization: str = Header(None)):
    """Get comprehensive cost analytics and usage patterns - ADMIN ONLY"""
    # SECURITY: Verify admin access with Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "")
    if not await _verify_admin_access(token):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.cost_monitoring_service import cost_monitor
        analytics = await cost_monitor.get_cost_analytics(days=days)
        
        return {
            "success": True,
            "analytics": {
                "daily_cost": analytics.daily_cost,
                "monthly_cost": analytics.monthly_cost,
                "service_breakdown": analytics.service_breakdown,
                "usage_trends": analytics.usage_trends,
                "optimization_suggestions": analytics.optimization_suggestions
            },
            "period_days": days,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost analytics: {str(e)}")

@app.get("/api/admin/costs/quotas")
@limiter.limit("60/minute")
async def get_quota_status(request: Request, authorization: str = Header(None)):
    """Get API usage statistics for all services - ADMIN ONLY"""
    # SECURITY: Verify admin access with Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "")
    if not await _verify_admin_access(token):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.quota_manager import quota_manager
        
        # Get API usage statistics instead of quota status
        usage_data = await quota_manager.get_api_usage_stats()
        
        return {
            "success": True,
            "quotas": usage_data.get("usage_stats", {}),
            "summary": usage_data.get("summary", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting API usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API usage stats: {str(e)}")

@app.get("/api/admin/costs/usage")
@limiter.limit("60/minute")
async def get_api_usage_stats(request: Request, days: int = 7, authorization: str = Header(None)):
    """Get API usage statistics - ADMIN ONLY"""
    # SECURITY: Verify admin access with Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "")
    if not await _verify_admin_access(token):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.cost_monitoring_service import cost_monitor
        usage_stats = await cost_monitor.get_api_usage_stats(days=days)
        
        return {
            "success": True,
            "usage_stats": usage_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting API usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API usage stats: {str(e)}")

@app.get("/api/admin/costs/health")
async def get_cost_monitoring_health(authorization: str = Header(None)):
    """Get health status of cost monitoring components - ADMIN ONLY"""
    logger.info(f"Admin health check request - Authorization header: {authorization is not None}")
    
    # SECURITY: Verify admin access with Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Admin health check failed: No authorization header")
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "")
    logger.info(f"Admin health check - Token length: {len(token)}")
    
    admin_access = await _verify_admin_access(token)
    logger.info(f"Admin access result: {admin_access}")
    
    if not admin_access:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.cost_monitoring_service import cost_monitor
        health_status = await cost_monitor.get_health_status()
        
        return {
            "success": True,
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cost monitoring health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@app.post("/api/admin/costs/optimize")
@limiter.limit("20/minute")
async def optimize_request(request: Request, request_data: dict, authorization: str = Header(None)):
    """Optimize request for cost efficiency - ADMIN ONLY"""
    # SECURITY: Verify admin access with Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "")
    if not await _verify_admin_access(token):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.cost_monitoring_service import cost_monitor
        optimization_result = await cost_monitor.optimize_request(request_data)
        
        return {
            "success": True,
            "optimization": optimization_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error optimizing request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize request: {str(e)}")

# AI clarification endpoints
@app.post("/api/ai/clarify", response_model=ClarificationResponse)
@limiter.limit("15/minute")
async def get_ai_clarification(request: Request, clarification_request: ClarificationRequest):
    """Get AI-powered clarification"""
    try:
        logger.info(f"Received clarification request: {clarification_request.question[:50] if clarification_request.question else 'No question'}...")
        
        controller = get_initialized_controller('ai')
        if not controller:
            logger.warning("AI controller not available, providing fallback response")
            return ClarificationResponse(
                success=True,
                response="I'm currently experiencing technical difficulties with my AI services. However, I can see you're asking about your legal document. For the most accurate analysis, I recommend reviewing the specific clauses you're concerned about and considering consultation with a legal professional for detailed guidance.",
                conversation_id="fallback",
                confidence_score=25,
                response_quality="fallback",
                processing_time=0.1,
                fallback=True,
                error_type="AIServiceUnavailable",
                service_used="fallback_handler",
                timestamp=datetime.now()
            )
        
        result = await controller.get_clarification(clarification_request)
        logger.info(f"AI clarification result: success={result.success}, service_used={result.service_used}")
        
        # If AI service failed, return a proper fallback response
        if not result.success and not result.response:
            logger.warning("AI service returned empty response, providing fallback")
            return ClarificationResponse(
                success=True,
                response="I'm currently experiencing technical difficulties with my AI services. However, I can see you're asking about your legal document. For the most accurate analysis, I recommend reviewing the specific clauses you're concerned about and considering consultation with a legal professional for detailed guidance.",
                conversation_id=result.conversation_id or "fallback",
                confidence_score=25,
                response_quality="fallback",
                processing_time=result.processing_time,
                fallback=True,
                error_type="AIServiceUnavailable",
                service_used="fallback_handler",
                timestamp=datetime.now()
            )
        
        return result
    except ValidationError as e:
        logger.error(f"Validation error in clarification: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Clarification endpoint error: {e}")
        # Return a proper error response instead of raising
        return ClarificationResponse(
            success=False,
            response=f"AI clarification service error: {str(e)}",
            conversation_id="error",
            confidence_score=0,
            response_quality="error",
            processing_time=0.0,
            fallback=True,
            error_type=type(e).__name__,
            service_used="error_handler",
            timestamp=datetime.now()
        )


@app.get("/api/ai/health")
async def get_ai_health():
    """Get AI service health status"""
    try:
        # Test a simple clarification request
        test_request = ClarificationRequest(
            question="Test question for health check",
            user_expertise_level="beginner"
        )
        result = await ai_controller.get_clarification(test_request)
        
        return {
            "success": True,
            "ai_service_available": result.success,
            "service_used": result.service_used,
            "fallback_mode": result.fallback,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "ai_service_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/ai/rag-clarify")
@limiter.limit("10/minute")
async def get_rag_enhanced_clarification(request: Request, rag_request: dict):
    """Get RAG-enhanced clarification for user queries"""
    try:
        query = rag_request.get('query', '')
        analysis_id = rag_request.get('analysis_id', '')
        
        if not query or not analysis_id:
            raise HTTPException(status_code=400, detail="Both 'query' and 'analysis_id' are required")
        
        # Use document service for RAG-enhanced clarification
        from services.document_service import document_service
        
        result = await document_service.get_rag_enhanced_clarification(query, analysis_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG-enhanced clarification failed: {e}")
        return {
            "success": False,
            "response": f"RAG-enhanced clarification failed: {str(e)}",
            "enhanced": False,
            "error": str(e)
        }


@app.get("/api/ai/conversation/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary():
    """Get conversation summary and analytics"""
    return await ai_controller.get_conversation_summary()


@app.delete("/api/ai/conversation/clear")
async def clear_conversation_history():
    """Clear conversation history"""
    return await ai_controller.clear_conversation_history()





# Document comparison endpoints
@app.post("/api/compare", response_model=DocumentComparisonResponse)
@limiter.limit("5/minute")
async def compare_documents(request: Request, comparison_request: DocumentComparisonRequest):
    """Compare two legal documents"""
    return await comparison_controller.compare_documents(comparison_request)


@app.get("/api/compare/{comparison_id}/summary", response_model=ComparisonSummaryResponse)
async def get_comparison_summary(comparison_id: str):
    """Get summary of a previous comparison"""
    return await comparison_controller.get_comparison_summary(comparison_id)


@app.get("/api/compare/export/formats")
async def get_comparison_export_formats():
    """Get available export formats for comparison reports"""
    return await comparison_controller.get_export_formats()


@app.post("/api/compare/export/{format}")
async def export_comparison_report(
    format: str,
    comparison_data: DocumentComparisonResponse,
    request: Request
):
    """Export comparison report in specified format (PDF/Word)"""
    from fastapi.responses import Response
    
    try:
        # Export the report
        exported_data = await comparison_controller.export_comparison_report(
            comparison_data, format
        )
        
        # Set appropriate content type and filename
        if format.lower() == 'pdf':
            content_type = 'application/pdf'
            filename = f"comparison_report_{comparison_data.comparison_id}.pdf"
        elif format.lower() in ['docx', 'word']:
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"comparison_report_{comparison_data.comparison_id}.docx"
        else:
            content_type = 'application/octet-stream'
            filename = f"comparison_report_{comparison_data.comparison_id}.{format}"
        
        return Response(
            content=exported_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(exported_data))
            }
        )
        
    except Exception as e:
        logger.error(f"Export endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Export endpoints
@app.post("/api/export/pdf")
@limiter.limit("5/minute")
async def export_to_pdf(request: Request, data: dict):
    """Export analysis results to PDF"""
    return await export_controller.export_to_pdf(data)


@app.post("/api/export/word")
@limiter.limit("5/minute")
async def export_to_word(request: Request, data: dict):
    """Export analysis results to Word document"""
    return await export_controller.export_to_word(data)


# Email notification endpoints
@app.post("/api/email/send-analysis")
@limiter.limit("5/hour")
async def send_analysis_email(request: Request, email_request: dict):
    """Send analysis report via email"""
    controller = get_initialized_controller('email')
    if not controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        from models.email_models import EmailNotificationRequest
        
        # Get current user from request state (set by Firebase middleware)
        current_user = getattr(request.state, 'user', None)
        
        # Parse email request
        notification_request = EmailNotificationRequest(**email_request['notification'])
        analysis_data = email_request.get('analysis_data', {})
        
        response = await controller.send_analysis_email(
            request=notification_request,
            analysis_data=analysis_data,
            current_user=current_user
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Email endpoint error: {e}")
        return {
            "success": False,
            "delivery_status": "failed",
            "error_message": f"Email request failed: {str(e)}"
        }


@app.get("/api/email/rate-limit/{user_id}")
async def get_email_rate_limit(user_id: str):
    """Get email rate limit information for user"""
    controller = get_initialized_controller('email')
    if not controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        rate_limit_info = await controller.get_email_rate_limit_info(user_id)
        return rate_limit_info.dict()
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/email/test")
async def test_email_service():
    """Test email service availability"""
    controller = get_initialized_controller('email')
    if not controller:
        return {"success": False, "error": "Email service not available"}
    
    return await controller.test_email_service()


@app.post("/api/email/send-test")
@limiter.limit("2/hour")
async def send_test_email(request: Request, test_request: dict):
    """Send test email to verify functionality"""
    controller = get_initialized_controller('email')
    if not controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        # Get current user from request state (set by Firebase middleware)
        current_user = getattr(request.state, 'user', None)
        user_id = current_user.get('uid', 'anonymous') if current_user else 'anonymous'
        
        user_email = test_request.get('email')
        if not user_email:
            return {"success": False, "error": "Email address required"}
        
        response = await controller.send_test_email(
            user_email=user_email,
            user_id=user_id,
            subject=test_request.get('subject', 'LegalSaathi Test Email')
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Test email error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/email/send-test-with-pdf")
@limiter.limit("1/hour")
async def send_test_email_with_pdf(request: Request, test_request: dict):
    """Send test email with PDF attachment to verify PDF functionality"""
    controller = get_initialized_controller('email')
    if not controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        # Get current user from request state
        current_user = getattr(request.state, 'user', None)
        user_id = current_user.get('uid', 'anonymous') if current_user else 'anonymous'
        
        user_email = test_request.get('email')
        if not user_email:
            return {"success": False, "error": "Email address required"}
        
        # Create a simple test PDF content
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        # Create PDF in memory
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add content to PDF
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 100, "LegalSaathi PDF Attachment Test")
        
        p.setFont("Helvetica", 12)
        p.drawString(100, height - 140, "This is a test PDF attachment to verify email functionality.")
        p.drawString(100, height - 160, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.drawString(100, height - 180, f"Sent to: {user_email}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, height - 220, "PDF Attachment Features:")
        p.setFont("Helvetica", 10)
        p.drawString(120, height - 240, "✓ SMTP Email Service")
        p.drawString(120, height - 255, "✓ PDF Generation")
        p.drawString(120, height - 270, "✓ Email Attachment")
        p.drawString(120, height - 285, "✓ Gmail SMTP Integration")
        
        p.showPage()
        p.save()
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated test PDF, size: {len(pdf_content)} bytes")
        
        # Send email with PDF using SMTP service directly
        if controller.gmail_service.smtp_service and controller.gmail_service.smtp_service.is_available():
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0ea5e9;">📎 LegalSaathi PDF Attachment Test</h2>
                    <p>This is a test email with PDF attachment to verify email functionality.</p>
                    
                    <div style="background-color: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #1e40af;"><strong>📋 Test Details:</strong></p>
                        <ul style="margin: 10px 0; color: #1e40af;">
                            <li>Email Service: SMTP (Gmail)</li>
                            <li>PDF Size: {len(pdf_content)} bytes</li>
                            <li>Attachment: test_document.pdf</li>
                            <li>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        </ul>
                    </div>
                    
                    <p>If you received this email with the PDF attachment, the email service is working correctly!</p>
                    <br>
                    <p>Best regards,<br><strong>LegalSaathi Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            LegalSaathi PDF Attachment Test
            
            This is a test email with PDF attachment to verify email functionality.
            
            Test Details:
            - Email Service: SMTP (Gmail)
            - PDF Size: {len(pdf_content)} bytes
            - Attachment: test_document.pdf
            - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you received this email with the PDF attachment, the email service is working correctly!
            
            Best regards,
            LegalSaathi Team
            """
            
            response = await controller.gmail_service.smtp_service._send_smtp_email(
                to_email=user_email,
                subject="LegalSaathi PDF Attachment Test",
                html_content=html_content,
                text_content=text_content,
                pdf_content=pdf_content
            )
            
            if response.success:
                controller.gmail_service.increment_rate_limit(user_id)
                return {
                    "success": True,
                    "message_id": response.message_id,
                    "delivery_status": response.delivery_status.value,
                    "pdf_size": len(pdf_content),
                    "service_used": "SMTP"
                }
            else:
                return {
                    "success": False,
                    "error": response.error,
                    "delivery_status": response.delivery_status.value
                }
        else:
            return {"success": False, "error": "SMTP service not available"}
        
    except Exception as e:
        logger.error(f"Test email with PDF error: {e}")
        return {"success": False, "error": str(e)}


# Background tasks endpoint
@app.post("/api/tasks/cleanup")
async def cleanup_cache(background_tasks: BackgroundTasks):
    """Trigger cache cleanup"""
    background_tasks.add_task(cache_service.clear_expired_cache)
    return SuccessResponse(message="Cache cleanup scheduled").dict()


# Logging endpoint
@app.get("/api/logs")
async def get_logs(request: Request, lines: int = 100):
    """Get recent application logs"""
    try:
        with open('legal_saathi.log', 'r') as f:
            # Read last N lines
            all_lines = f.readlines()
            recent_logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {"logs": recent_logs}
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to read logs")

# Static file serving for React frontend - optimized for Cloud Run
CLIENT_DIST_PATH = "client/dist"
CLIENT_INDEX_PATH = os.path.join(CLIENT_DIST_PATH, "index.html")

# Check if client build exists
if os.path.exists(CLIENT_DIST_PATH) and os.path.exists(CLIENT_INDEX_PATH):
    logger.info(f"✅ Client build found at {CLIENT_DIST_PATH}")
    
    # Mount static assets with proper caching headers
    app.mount("/assets", StaticFiles(directory=os.path.join(CLIENT_DIST_PATH, "assets")), name="assets")
    
    # Serve favicon and other root-level static files
    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon"""
        favicon_path = os.path.join(CLIENT_DIST_PATH, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    @app.get("/manifest.json")
    async def manifest():
        """Serve PWA manifest"""
        manifest_path = os.path.join(CLIENT_DIST_PATH, "manifest.json")
        if os.path.exists(manifest_path):
            return FileResponse(manifest_path, media_type="application/json")
        raise HTTPException(status_code=404, detail="Manifest not found")
    
    @app.get("/")
    async def serve_frontend():
        """Serve React frontend root"""
        return FileResponse(CLIENT_INDEX_PATH, media_type="text/html")
    
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """Serve React frontend for all routes (SPA) with optimized static file handling"""
        # Skip API routes, docs, and health checks
        if (path.startswith("api/") or 
            path.startswith("docs") or 
            path.startswith("redoc") or 
            path.startswith("health")):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Handle static files with proper MIME types
        static_file_path = os.path.join(CLIENT_DIST_PATH, path)
        if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            # Determine MIME type based on file extension
            mime_type = "text/plain"
            if path.endswith(".js"):
                mime_type = "application/javascript"
            elif path.endswith(".css"):
                mime_type = "text/css"
            elif path.endswith(".html"):
                mime_type = "text/html"
            elif path.endswith(".json"):
                mime_type = "application/json"
            elif path.endswith(".png"):
                mime_type = "image/png"
            elif path.endswith(".jpg") or path.endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif path.endswith(".svg"):
                mime_type = "image/svg+xml"
            elif path.endswith(".ico"):
                mime_type = "image/x-icon"
            elif path.endswith(".woff") or path.endswith(".woff2"):
                mime_type = "font/woff2"
            elif path.endswith(".ttf"):
                mime_type = "font/ttf"
            
            return FileResponse(static_file_path, media_type=mime_type)
        
        # For all other routes, serve the React app (SPA routing)
        return FileResponse(CLIENT_INDEX_PATH, media_type="text/html")
else:
    logger.warning(f"⚠️  Client build not found at {CLIENT_DIST_PATH}. Frontend will not be served.")
    
    @app.get("/")
    async def serve_api_info():
        """Serve API information when frontend is not available"""
        return {
            "message": "Legal Saathi API",
            "version": "2.0.0",
            "status": "running",
            "frontend": "not_available",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "timestamp": datetime.now().isoformat()
        }


# Root API endpoint
@app.get("/api")
async def api_root():
    """API root endpoint with information"""
    return {
        "name": "Legal Saathi Document Advisor API",
        "version": "2.0.0",
        "description": "AI-powered legal document analysis platform",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )