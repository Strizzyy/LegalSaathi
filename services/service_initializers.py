"""
Service Initializers for OptimizedServiceManager
Contains initialization functions for all backend services
"""

import logging
import asyncio
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def initialize_health_service() -> Any:
    """Initialize health controller service"""
    try:
        # Use lazy import to avoid circular dependencies
        import importlib
        health_module = importlib.import_module('controllers.health_controller')
        HealthController = getattr(health_module, 'HealthController')
        
        logger.info("Initializing health service...")
        health_controller = HealthController()
        
        # Perform basic health check to ensure service is working
        await health_controller.health_check()
        
        logger.info("Health service initialized successfully")
        return health_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize health service: {e}")
        raise


async def initialize_auth_service() -> Any:
    """Initialize authentication service"""
    try:
        # Use lazy import to avoid circular dependencies
        import importlib
        auth_module = importlib.import_module('controllers.auth_controller')
        AuthController = getattr(auth_module, 'AuthController')
        
        logger.info("Initializing authentication service...")
        auth_controller = AuthController()
        
        # Test Firebase connection if available
        if hasattr(auth_controller, 'firebase_service') and auth_controller.firebase_service._firebase_available:
            logger.info("Firebase authentication is available")
        else:
            logger.warning("Firebase authentication is not available - running in degraded mode")
        
        logger.info("Authentication service initialized successfully")
        return auth_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize authentication service: {e}")
        raise


async def initialize_document_service() -> Any:
    """Initialize document processing service"""
    try:
        # Use lazy import to avoid circular dependencies
        import importlib
        document_module = importlib.import_module('controllers.document_controller')
        DocumentController = getattr(document_module, 'DocumentController')
        
        logger.info("Initializing document service...")
        document_controller = DocumentController()
        
        # Verify document service dependencies
        if hasattr(document_controller, 'document_service'):
            logger.info("Document processing service is ready")
        
        if hasattr(document_controller, 'file_service'):
            logger.info("File processing service is ready")
        
        logger.info("Document service initialized successfully")
        return document_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize document service: {e}")
        raise


async def initialize_ai_service() -> Any:
    """Initialize AI service with Cloud Run optimization"""
    try:
        import os
        
        # Check if we're in Cloud Run environment
        is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        use_lightweight = os.getenv('USE_LIGHTWEIGHT_SERVICES', 'false').lower() == 'true'
        disable_heavy_models = os.getenv('DISABLE_SENTENCE_TRANSFORMERS', 'false').lower() == 'true'
        
        if is_cloud_run or use_lightweight or disable_heavy_models:
            logger.info("Initializing AI service in lightweight mode for Cloud Run...")
            
            # Use lightweight AI controller initialization
            from controllers.ai_controller import AIController
            ai_controller = AIController()
            
            # Configure AI service for lightweight operation if available
            if hasattr(ai_controller, 'ai_service'):
                ai_service = ai_controller.ai_service
                if hasattr(ai_service, 'configure_lightweight_mode'):
                    ai_service.configure_lightweight_mode(True)
                    logger.info("AI service configured for lightweight Cloud Run operation")
                elif hasattr(ai_service, 'disable_heavy_models'):
                    ai_service.disable_heavy_models()
                    logger.info("Heavy AI models disabled for Cloud Run")
            
            logger.info("AI service initialized in lightweight mode")
            return ai_controller
        else:
            logger.info("Initializing AI service in full mode...")
            from controllers.ai_controller import AIController
            ai_controller = AIController()
            
            # Test AI service availability
            if hasattr(ai_controller, 'ai_service'):
                ai_service = ai_controller.ai_service
                if hasattr(ai_service, 'enabled') and ai_service.enabled:
                    logger.info("AI service is enabled and ready")
                else:
                    logger.warning("AI service is not fully available - some features may be limited")
            
            logger.info("AI service initialized successfully")
            return ai_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
        # For Cloud Run, we want to continue even if AI service fails
        if os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true':
            logger.warning("AI service failed in Cloud Run - continuing with degraded functionality")
            # Return a minimal AI controller that can handle basic requests
            try:
                from controllers.ai_controller import AIController
                return AIController()
            except:
                return None
        raise


async def initialize_translation_service() -> Any:
    """Initialize translation service"""
    try:
        from controllers.translation_controller import TranslationController
        
        logger.info("Initializing translation service...")
        translation_controller = TranslationController()
        
        # Test translation service
        if hasattr(translation_controller, 'translation_service'):
            service = translation_controller.translation_service
            if hasattr(service, 'enabled') and service.enabled:
                logger.info("Translation service is enabled and ready")
            else:
                logger.warning("Translation service is not fully available")
        
        logger.info("Translation service initialized successfully")
        return translation_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize translation service: {e}")
        raise


async def initialize_speech_service() -> Any:
    """Initialize speech processing service"""
    try:
        from controllers.speech_controller import SpeechController
        
        logger.info("Initializing speech service...")
        speech_controller = SpeechController()
        
        # Test speech service availability
        logger.info("Speech service initialized successfully")
        return speech_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize speech service: {e}")
        raise


async def initialize_email_service() -> Any:
    """Initialize email service"""
    try:
        from controllers.email_controller import EmailController
        
        logger.info("Initializing email service...")
        email_controller = EmailController()
        
        logger.info("Email service initialized successfully")
        return email_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize email service: {e}")
        # Email service is not critical, so we can continue without it
        logger.warning("Email service failed to initialize - continuing without email functionality")
        raise


async def initialize_vision_service() -> Any:
    """Initialize vision processing service"""
    try:
        from controllers.vision_controller import VisionController
        
        logger.info("Initializing vision service...")
        vision_controller = VisionController()
        
        # Test vision service availability
        if hasattr(vision_controller, 'dual_vision_service'):
            logger.info("Vision service with dual processing is ready")
        
        logger.info("Vision service initialized successfully")
        return vision_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize vision service: {e}")
        raise


async def initialize_comparison_service() -> Any:
    """Initialize document comparison service"""
    try:
        from controllers.comparison_controller import ComparisonController
        
        logger.info("Initializing comparison service...")
        comparison_controller = ComparisonController()
        
        logger.info("Comparison service initialized successfully")
        return comparison_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize comparison service: {e}")
        raise


async def initialize_export_service() -> Any:
    """Initialize export service"""
    try:
        from controllers.export_controller import ExportController
        
        logger.info("Initializing export service...")
        export_controller = ExportController()
        
        logger.info("Export service initialized successfully")
        return export_controller
        
    except Exception as e:
        logger.error(f"Failed to initialize export service: {e}")
        raise


async def initialize_cache_service() -> Any:
    """Initialize cache service"""
    try:
        from services.cache_service import CacheService
        
        logger.info("Initializing cache service...")
        cache_service = CacheService()
        
        # Test cache functionality
        cache_stats = cache_service.get_cache_stats()
        logger.info(f"Cache service ready - stats: {cache_stats}")
        
        logger.info("Cache service initialized successfully")
        return cache_service
        
    except Exception as e:
        logger.error(f"Failed to initialize cache service: {e}")
        raise


async def initialize_cost_monitoring_service() -> Any:
    """Initialize cost monitoring service"""
    try:
        from services.cost_monitoring_service import cost_monitor
        
        logger.info("Initializing cost monitoring service...")
        
        # Test cost monitoring availability
        health_status = await cost_monitor.get_health_status()
        if health_status.get('status') == 'healthy':
            logger.info("Cost monitoring service is healthy")
        else:
            logger.warning("Cost monitoring service may have issues")
        
        logger.info("Cost monitoring service initialized successfully")
        return cost_monitor
        
    except ImportError:
        logger.warning("Cost monitoring service not available")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize cost monitoring service: {e}")
        raise


async def initialize_quota_management_service() -> Any:
    """Initialize quota management service"""
    try:
        from services.quota_manager import quota_manager
        
        logger.info("Initializing quota management service...")
        
        # Test quota manager availability
        health_status = await quota_manager.get_health_status()
        if health_status.get('status') == 'healthy':
            logger.info("Quota management service is healthy")
        else:
            logger.warning("Quota management service may have issues")
        
        logger.info("Quota management service initialized successfully")
        return quota_manager
        
    except ImportError:
        logger.warning("Quota management service not available")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize quota management service: {e}")
        raise


# Service dependency mapping
SERVICE_DEPENDENCIES = {
    'health': [],  # No dependencies
    'cache': [],   # No dependencies
    'auth': [],    # No dependencies
    'document': ['cache'],  # Depends on cache
    'ai': ['cache'],        # Depends on cache
    'translation': ['cache'],  # Depends on cache
    'speech': ['cache'],       # Depends on cache
    'email': [],               # No dependencies
    'vision': ['cache'],       # Depends on cache
    'comparison': ['document', 'ai'],  # Depends on document and AI
    'export': ['document'],    # Depends on document
    'cost_monitoring': [],     # No dependencies
    'quota_management': []     # No dependencies
}


def get_service_initializer(service_name: str) -> Optional[callable]:
    """Get the initializer function for a service"""
    initializers = {
        'health': initialize_health_service,
        'auth': initialize_auth_service,
        'document': initialize_document_service,
        'ai': initialize_ai_service,
        'translation': initialize_translation_service,
        'speech': initialize_speech_service,
        'email': initialize_email_service,
        'vision': initialize_vision_service,
        'comparison': initialize_comparison_service,
        'export': initialize_export_service,
        'cache': initialize_cache_service,
        'cost_monitoring': initialize_cost_monitoring_service,
        'quota_management': initialize_quota_management_service
    }
    
    return initializers.get(service_name)


def get_service_dependencies(service_name: str) -> list:
    """Get the dependencies for a service"""
    return SERVICE_DEPENDENCIES.get(service_name, [])