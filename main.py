"""
FastAPI main application for Legal Saathi Document Advisor
Replaces Flask app.py with modern async architecture and MVC pattern
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import json
import tempfile

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks

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
    SupportedLanguagesResponse as TranslationLanguagesResponse
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

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize cache service for cleanup
cache_service = CacheService()

# Initialize user-based rate limiter
user_rate_limiter = UserBasedRateLimiter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Legal Saathi FastAPI application")
    
    # Initialize services
    try:
        # Any startup initialization can go here
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal Saathi FastAPI application")
    
    # Cleanup
    try:
        cache_service.clear_expired_cache()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="Legal Saathi Document Advisor API",
    description="AI-powered legal document analysis platform with FastAPI backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
        "https://legalsaathi-document-advisor.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize controllers
document_controller = DocumentController()
translation_controller = TranslationController()
speech_controller = SpeechController()
health_controller = HealthController()
ai_controller = AIController()
comparison_controller = ComparisonController()
export_controller = ExportController()
try:
    email_controller = EmailController()
    logger.info("Email controller initialized")
except Exception as e:
    logger.warning(f"Email controller failed to initialize: {e}")
    email_controller = None

try:
    auth_controller = AuthController()
    logger.info("Authentication controller initialized")
except Exception as e:
    logger.warning(f"Authentication controller failed to initialize: {e}")
    auth_controller = None

# Include routers
app.include_router(support_router)
app.include_router(insights_router)


# Middleware for request logging and performance monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and add performance monitoring"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)
    
    # Add cache headers for API responses
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    
    # Log response
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
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import FirebaseTokenRequest
    request = FirebaseTokenRequest(token=token_request.get('token', ''))
    return await auth_controller.verify_token(request)


@app.post("/api/auth/register")
async def register_user(registration_request: dict):
    """Register a new user account"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import UserRegistrationRequest
    request = UserRegistrationRequest(**registration_request)
    return await auth_controller.register_user(request)


@app.get("/api/auth/user-info")
async def get_user_info(request: Request):
    """Get current user information"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    return await auth_controller.get_user_info(request)


@app.post("/api/auth/refresh-token")
async def refresh_token(refresh_request: dict):
    """Refresh Firebase token"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    from models.auth_models import RefreshTokenRequest
    request = RefreshTokenRequest(refresh_token=refresh_request.get('refresh_token', ''))
    return await auth_controller.refresh_token(request)


@app.get("/api/auth/current-user")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    return await auth_controller.get_current_user(request)


@app.put("/api/auth/profile")
async def update_user_profile(request: Request, update_data: dict):
    """Update user profile"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    return await auth_controller.update_user_profile(request, update_data)


@app.delete("/api/auth/account")
async def delete_user_account(request: Request):
    """Delete user account"""
    if not auth_controller:
        return {"success": False, "error": "Authentication service not available"}
    return await auth_controller.delete_user_account(request)


# Health check endpoints
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Basic health check endpoint"""
    return await health_controller.health_check()


@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with service information"""
    return await health_controller.detailed_health_check()


@app.get("/api/health/metrics")
async def service_metrics():
    """Get service performance metrics"""
    return await health_controller.service_metrics()


# Document analysis endpoints
@app.post("/api/analyze", response_model=DocumentAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_document(request: Request, analysis_request: DocumentAnalysisRequest):
    """Analyze legal document text"""
    return await document_controller.analyze_document(analysis_request)


@app.post("/api/analyze/file", response_model=DocumentAnalysisResponse)
@limiter.limit("5/minute")
async def analyze_document_file(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_expertise_level: str = Form("beginner")
):
    """Analyze uploaded document file"""
    return await document_controller.analyze_document_file(
        file=file,
        document_type=document_type,
        user_expertise_level=user_expertise_level
    )


@app.post("/api/analyze/async")
@limiter.limit("5/minute")
async def start_async_analysis(request: Request, analysis_request: DocumentAnalysisRequest):
    """Start async document analysis"""
    return await document_controller.start_async_analysis(analysis_request)


@app.get("/api/analysis/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """Get status of ongoing analysis"""
    return await document_controller.get_analysis_status(analysis_id)


@app.get("/api/analysis/{analysis_id}/clauses")
async def get_paginated_clauses(
    analysis_id: str,
    page: int = 1,
    page_size: int = 10,
    risk_filter: str = None,
    sort_by: str = "risk_score"
):
    """Get paginated clause results with filtering and sorting"""
    return await document_controller.get_paginated_clauses(
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
    return await document_controller.search_clauses(
        analysis_id=analysis_id,
        search_query=q,
        search_fields=fields
    )


@app.get("/api/analysis/{analysis_id}/clauses/{clause_id}")
async def get_clause_details(analysis_id: str, clause_id: str):
    """Get detailed information for a specific clause"""
    return await document_controller.get_clause_details(
        analysis_id=analysis_id,
        clause_id=clause_id
    )


@app.post("/api/analysis/{analysis_id}/export")
async def export_analysis(analysis_id: str, format: str = "pdf"):
    """Export analysis results"""
    return await document_controller.export_analysis(analysis_id, format)


# Translation endpoints
@app.post("/api/translate", response_model=TranslationResponse)
@limiter.limit("20/minute")
async def translate_text(request: Request, translation_request: TranslationRequest):
    """Translate text to target language"""
    return await translation_controller.translate_text(translation_request)


@app.post("/api/translate/clause", response_model=ClauseTranslationResponse)
@limiter.limit("15/minute")
async def translate_clause(request: Request, clause_request: ClauseTranslationRequest):
    """Translate legal clause with context"""
    return await translation_controller.translate_clause(clause_request)


@app.get("/api/translate/languages", response_model=TranslationLanguagesResponse)
async def get_translation_languages():
    """Get supported languages for translation"""
    return await translation_controller.get_supported_languages()


# Speech endpoints
@app.post("/api/speech/speech-to-text", response_model=SpeechToTextResponse)
@limiter.limit("10/minute")
async def speech_to_text(
    request: Request,
    audio_file: UploadFile = File(...),
    language_code: str = Form("en-US"),
    enable_punctuation: bool = Form(True)
):
    """Convert speech to text"""
    return await speech_controller.speech_to_text(
        audio_file=audio_file,
        language_code=language_code,
        enable_punctuation=enable_punctuation
    )


@app.post("/api/speech/text-to-speech")
@limiter.limit("10/minute")
async def text_to_speech(request: Request, tts_request: TextToSpeechRequest):
    """Convert text to speech"""
    return await speech_controller.text_to_speech(tts_request)


@app.post("/api/speech/text-to-speech/info", response_model=TextToSpeechResponse)
@limiter.limit("15/minute")
async def text_to_speech_info(request: Request, tts_request: TextToSpeechRequest):
    """Get text-to-speech metadata without audio"""
    return await speech_controller.get_text_to_speech_info(tts_request)


@app.get("/api/speech/languages", response_model=SpeechLanguagesResponse)
async def get_speech_languages():
    """Get supported languages for speech services"""
    return await speech_controller.get_supported_languages()


# AI clarification endpoints
@app.post("/api/ai/clarify", response_model=ClarificationResponse)
@limiter.limit("15/minute")
async def get_ai_clarification(request: Request, clarification_request: ClarificationRequest):
    """Get AI-powered clarification"""
    try:
        logger.info(f"Received clarification request: {clarification_request.question[:50] if clarification_request.question else 'No question'}...")
        logger.debug(f"Request details - Question length: {len(clarification_request.question)}, Experience level: {clarification_request.user_expertise_level}")
        
        result = await ai_controller.get_clarification(clarification_request)
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
    if not email_controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        from models.email_models import EmailNotificationRequest
        
        # Get current user from request state (set by Firebase middleware)
        current_user = getattr(request.state, 'user', None)
        
        # Parse email request
        notification_request = EmailNotificationRequest(**email_request['notification'])
        analysis_data = email_request.get('analysis_data', {})
        
        response = await email_controller.send_analysis_email(
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
    if not email_controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        rate_limit_info = await email_controller.get_email_rate_limit_info(user_id)
        return rate_limit_info.dict()
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/email/test")
async def test_email_service():
    """Test email service availability"""
    if not email_controller:
        return {"success": False, "error": "Email service not available"}
    
    return await email_controller.test_email_service()


@app.post("/api/email/send-test")
@limiter.limit("2/hour")
async def send_test_email(request: Request, test_request: dict):
    """Send test email to verify functionality"""
    if not email_controller:
        return {"success": False, "error": "Email service not available"}
    
    try:
        # Get current user from request state (set by Firebase middleware)
        current_user = getattr(request.state, 'user', None)
        user_id = current_user.get('uid', 'anonymous') if current_user else 'anonymous'
        
        user_email = test_request.get('email')
        if not user_email:
            return {"success": False, "error": "Email address required"}
        
        response = await email_controller.send_test_email(
            user_email=user_email,
            user_id=user_id,
            subject=test_request.get('subject', 'LegalSaathi Test Email')
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Test email error: {e}")
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

# Static file serving for React frontend
if os.path.exists("client/dist"):
    app.mount("/static", StaticFiles(directory="client/dist/assets"), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve React frontend"""
        return FileResponse("client/dist/index.html")
    
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """Serve React frontend for all routes (SPA)"""
        # Check if it's an API route
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve static files if they exist
        static_file_path = f"client/dist/{path}"
        if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # Otherwise serve the React app
        return FileResponse("client/dist/index.html")


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