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
    
    async def health_check(self) -> HealthCheckResponse:
        """Comprehensive health check for all services"""
        try:
            # Check core services (removed risk_classification and ai_clarification from status display)
            services_status = {
                'translation': self.translation_service.enabled,
                'file_processing': True,  # Always available
                'document_analysis': True,  # Always available
                'google_document_ai': document_ai_service.enabled,
                'google_natural_language': natural_language_service.enabled,
                'google_speech': speech_service.enabled,
                'export': True  # Export functionality available
            }
            
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
            critical_services = ['file_processing', 'document_analysis']
            overall_status = 'healthy'
            
            if not all(services_status[service] for service in critical_services):
                overall_status = 'degraded'
            
            # Check if any service is down
            if not any(services_status.values()):
                overall_status = 'unhealthy'
            
            response = HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.now(),
                services=services_status,
                cache=cache_info
            )
            
            logger.info(f"Health check completed: {overall_status}")
            return response
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Health check failed: {str(e)}"
            )
    
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
            
            # Test AI service
            try:
                if self.ai_service.enabled:
                    health_details['services']['ai_clarification'] = {
                        'status': 'healthy',
                        'provider': 'Google Gemini',
                        'last_check': datetime.now().isoformat()
                    }
                else:
                    health_details['services']['ai_clarification'] = {
                        'status': 'unavailable',
                        'error': 'Gemini API not configured'
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
    
    async def service_metrics(self) -> dict:
        """Get service performance metrics"""
        try:
            # This would integrate with the existing metrics tracker
            # For now, return basic metrics
            metrics = {
                'cache_performance': self.cache_service.get_cache_stats(),
                'ai_service': {
                    'enabled': self.ai_service.enabled,
                    'conversation_history_size': len(self.ai_service.conversation_history)
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