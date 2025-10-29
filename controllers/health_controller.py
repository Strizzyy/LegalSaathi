"""
Health controller for FastAPI backend
"""

import logging
from datetime import datetime
from fastapi import HTTPException

from models.ai_models import HealthCheckResponse
from services.ai_service import AIService
from services.cache_service import CacheService
from services.google_translate_service import GoogleTranslateService
from services.google_document_ai_service import document_ai_service
from services.google_natural_language_service import natural_language_service
from services.google_speech_service import speech_service

logger = logging.getLogger(__name__)


class HealthController:
    """Controller for health check and system status operations"""

    def __init__(self):
        self.ai_service = AIService()
        self.cache_service = CacheService()
        self.translation_service = GoogleTranslateService()
        self._initialization_complete = False
        self._services_ready = {
            'ai_service': False,
            'translation_service': False,
            'document_ai': False,
            'natural_language': False,
            'speech_service': False,
            'rag_service': False
        }

    async def health_check(self) -> HealthCheckResponse:
        """Comprehensive health check for all services"""
        try:
            services_status = {}
            
            # Fast service checks - just check if services are enabled/available
            # Don't do expensive credential verification every time
            
            # Check Google services (fast check)
            services_status['google_translate'] = getattr(self.translation_service, 'enabled', True)
            services_status['google_document_ai'] = getattr(document_ai_service, 'enabled', True)
            services_status['google_natural_language'] = getattr(natural_language_service, 'enabled', True)
            services_status['google_speech'] = getattr(speech_service, 'enabled', True)
            
            # Check AI service (fast check)
            try:
                ai_enabled = getattr(self.ai_service, 'enabled', True)
                services_status['ai_service'] = ai_enabled
                self._services_ready['ai_service'] = ai_enabled
            except Exception:
                services_status['ai_service'] = False
                self._services_ready['ai_service'] = False

            # Check RAG service (fast check)
            try:
                from services.advanced_rag_service import advanced_rag_service
                rag_enabled = hasattr(advanced_rag_service, 'sentence_transformer') and advanced_rag_service.sentence_transformer is not None
                services_status['rag_service'] = rag_enabled
                self._services_ready['rag_service'] = rag_enabled
            except Exception:
                services_status['rag_service'] = False
                self._services_ready['rag_service'] = False

            # Update service readiness based on fast checks
            self._services_ready['translation_service'] = services_status['google_translate']
            self._services_ready['document_ai'] = services_status['google_document_ai']
            self._services_ready['natural_language'] = services_status['google_natural_language']
            self._services_ready['speech_service'] = services_status['google_speech']

            # Core services (always available when application is running)
            services_status['file_processing'] = True
            services_status['document_analysis'] = True

            # Check if initialization is complete (simplified logic)
            critical_services_ready = all([
                services_status.get('ai_service', False),
                services_status.get('google_document_ai', False),
                services_status.get('google_natural_language', False),
                services_status.get('rag_service', False)
            ])
            
            if critical_services_ready:
                self._initialization_complete = True
                initialization_status = 'complete'
            else:
                initialization_status = 'initializing'

            # Get cache statistics
            cache_stats = self.cache_service.get_cache_stats()
            cache_info = {
                'size': cache_stats['analysis_cache_size'] + cache_stats['translation_cache_size'],
                'status': 'operational',
                'analysis_cache': cache_stats['analysis_cache_size'],
                'translation_cache': cache_stats['translation_cache_size'],
                'pattern_storage': cache_stats['pattern_storage_size']
            }

            # Determine overall health status
            critical_services = ['file_processing', 'document_analysis', 'ai_service', 'google_document_ai']
            
            if initialization_status == 'initializing':
                overall_status = 'initializing'
            elif not all(services_status.get(service, False) for service in critical_services):
                overall_status = 'degraded'
            elif not any(services_status.values()):
                overall_status = 'unhealthy'
            else:
                overall_status = 'healthy'

            # Add initialization info to cache
            cache_info['initialization_status'] = initialization_status
            cache_info['services_ready'] = self._services_ready.copy()

            response = HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.now(),
                services=services_status,
                cache=cache_info
            )

            logger.info(f"Health check completed: {overall_status} (initialization: {initialization_status})")
            
            return response

        except Exception as e:
            logger.error(f"An unexpected error occurred during health check: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Health check failed due to an internal error: {str(e)}"
            )

    # ... (the rest of your file remains the same) ...
    async def detailed_health_check(self) -> dict:
        """Detailed health check with service-specific information"""
        try:
            health_details = {
                'overall_status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'cache': self.cache_service.get_cache_stats(),
                'system_info': {
                    'python_version': '3.11+',
                    'fastapi_version': '0.104+',
                    'environment': 'production'
                }
            }
            
            # Test enhanced AI service with multiple providers
            try:
                ai_status = self.ai_service.get_service_status()
                health_details['services']['ai_clarification'] = {
                    'status': 'healthy' if self.ai_service.enabled else 'unavailable',
                    'primary_provider': 'Groq (Primary)' if self.ai_service.groq_enabled else 'Google Gemini (Fallback)',
                    'services': ai_status['services'],
                    'cache_status': ai_status['cache'],
                    'overall_status': ai_status['overall_status'],
                    'last_check': datetime.now().isoformat()
                }
            except Exception as e:
                health_details['services']['ai_clarification'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test translation service
            try:
                if self.translation_service.enabled:
                    health_details['services']['translation'] = {
                        'status': 'healthy',
                        'provider': 'Google Translate',
                        'cloud_enabled': self.translation_service.cloud_enabled,
                        'supported_languages': len(self.translation_service.supported_languages)
                    }
                else:
                    health_details['services']['translation'] = {
                        'status': 'unavailable',
                        'error': 'Translation service not configured'
                    }
            except Exception as e:
                health_details['services']['translation'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test Google Cloud services
            health_details['services']['google_cloud'] = {
                'document_ai': {
                    'status': 'healthy' if document_ai_service.enabled else 'unavailable',
                    'enabled': document_ai_service.enabled
                },
                'natural_language': {
                    'status': 'healthy' if natural_language_service.enabled else 'unavailable',
                    'enabled': natural_language_service.enabled
                },
                'speech': {
                    'status': 'healthy' if speech_service.enabled else 'unavailable',
                    'enabled': speech_service.enabled
                }
            }
            
            # Core services (always available)
            health_details['services']['core'] = {
                'risk_classification': {'status': 'healthy'},
                'file_processing': {'status': 'healthy'},
                'document_analysis': {'status': 'healthy'}
            }
            
            # Determine overall status
            service_statuses = []
            for service_group in health_details['services'].values():
                if isinstance(service_group, dict):
                    if 'status' in service_group:
                        service_statuses.append(service_group['status'])
                    else:
                        for sub_service in service_group.values():
                            if isinstance(sub_service, dict) and 'status' in sub_service:
                                service_statuses.append(sub_service['status'])
            
            if 'error' in service_statuses:
                health_details['overall_status'] = 'degraded'
            elif 'unavailable' in service_statuses:
                health_details['overall_status'] = 'partial'
            
            return health_details
            
        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Detailed health check failed: {str(e)}"
            )
    
    async def check_initialization_status(self) -> dict:
        """Check if backend services are fully initialized and ready"""
        try:
            # Force a quick health check to update status
            await self.health_check()
            
            # Quick check of critical services without full verification
            status = {
                'initialization_complete': self._initialization_complete,
                'services_ready': self._services_ready.copy(),
                'ready_for_requests': self._initialization_complete,
                'estimated_ready_time': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # If not ready, estimate time based on typical startup
            if not self._initialization_complete:
                # Estimate based on which services are still initializing
                pending_services = [k for k, v in self._services_ready.items() if not v]
                estimated_seconds = max(5, len(pending_services) * 2)  # Reduced estimate
                status['estimated_ready_time'] = f"{estimated_seconds} seconds"
                status['pending_services'] = pending_services
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to check initialization status: {e}")
            return {
                'initialization_complete': False,
                'ready_for_requests': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def service_metrics(self) -> dict:
        """Get service performance metrics"""
        try:
            # This would integrate with the existing metrics tracker
            # For now, return basic metrics
            # Get enhanced AI service metrics
            ai_status = self.ai_service.get_service_status()
            
            metrics = {
                'cache_performance': self.cache_service.get_cache_stats(),
                'ai_service': {
                    'enabled': self.ai_service.enabled,
                    'conversation_history_size': len(self.ai_service.conversation_history),
                    'service_status': ai_status,
                    'quota_usage': {
                        service: tracker for service, tracker in self.ai_service.quota_tracker.items()
                    }
                },
                'translation_service': {
                    'enabled': self.translation_service.enabled,
                    'cloud_enabled': getattr(self.translation_service, 'cloud_enabled', False)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get metrics: {str(e)}"
            )