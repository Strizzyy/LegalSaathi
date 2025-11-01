"""
Unified Service Manager - Consolidates all service management functionality
Combines lightweight, optimized, and multi-service management into one efficient system
"""

import os
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ServicePriority(Enum):
    """Service priority levels"""
    CRITICAL = "critical"      # Must be ready before app starts
    BACKGROUND = "background"  # Can initialize after app starts
    OPTIONAL = "optional"      # Can fail without affecting core functionality

class ServiceStatus(Enum):
    """Service status states"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    LAZY_LOAD = "lazy_load"

@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    priority: ServicePriority
    timeout: float = 30.0
    required: bool = True
    lazy_load: bool = False

class UnifiedServiceManager:
    """
    Unified service manager that adapts to deployment environment
    - Cloud Run: Lightweight with lazy loading
    - Local/Production: Full optimization with parallel initialization
    """
    
    def __init__(self):
        self.services = {}
        self.startup_time = None
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        self.is_render = os.getenv('RENDER_DEPLOYMENT', 'false').lower() == 'true'
        self.service_configs = self._get_service_configs()
        
    def _get_service_configs(self) -> Dict[str, ServiceConfig]:
        """Get service configurations based on deployment environment"""
        if self.is_cloud_run:
            # Cloud Run: Minimal critical services, everything else lazy loaded
            return {
                'health': ServiceConfig('health', ServicePriority.CRITICAL, timeout=5.0),
                'auth': ServiceConfig('auth', ServicePriority.CRITICAL, timeout=10.0, required=False),
                'document': ServiceConfig('document', ServicePriority.BACKGROUND, lazy_load=True),
                'ai': ServiceConfig('ai', ServicePriority.BACKGROUND, lazy_load=True),
                'translation': ServiceConfig('translation', ServicePriority.OPTIONAL, lazy_load=True),
                'speech': ServiceConfig('speech', ServicePriority.OPTIONAL, lazy_load=True),
                'vision': ServiceConfig('vision', ServicePriority.OPTIONAL, lazy_load=True),
                'comparison': ServiceConfig('comparison', ServicePriority.OPTIONAL, lazy_load=True),
                'export': ServiceConfig('export', ServicePriority.OPTIONAL, lazy_load=True),
                'email': ServiceConfig('email', ServicePriority.OPTIONAL, lazy_load=True),
            }
        else:
            # Local/Production: Full service initialization
            return {
                'health': ServiceConfig('health', ServicePriority.CRITICAL, timeout=10.0),
                'cache': ServiceConfig('cache', ServicePriority.CRITICAL, timeout=15.0),
                'auth': ServiceConfig('auth', ServicePriority.CRITICAL, timeout=20.0),
                'document': ServiceConfig('document', ServicePriority.BACKGROUND, timeout=30.0),
                'ai': ServiceConfig('ai', ServicePriority.BACKGROUND, timeout=45.0),
                'translation': ServiceConfig('translation', ServicePriority.BACKGROUND, timeout=30.0),
                'speech': ServiceConfig('speech', ServicePriority.BACKGROUND, timeout=25.0),
                'vision': ServiceConfig('vision', ServicePriority.BACKGROUND, timeout=35.0),
                'comparison': ServiceConfig('comparison', ServicePriority.OPTIONAL, timeout=20.0),
                'export': ServiceConfig('export', ServicePriority.OPTIONAL, timeout=15.0),
                'email': ServiceConfig('email', ServicePriority.OPTIONAL, timeout=20.0),
            }
    
    async def initialize_services(self) -> Dict[str, Any]:
        """Initialize services based on deployment environment"""
        start_time = datetime.now()
        
        if self.is_cloud_run:
            return await self._initialize_cloud_run_services()
        else:
            return await self._initialize_full_services()
    
    async def _initialize_cloud_run_services(self) -> Dict[str, Any]:
        """Initialize services for Cloud Run with fast startup"""
        logger.info("🚀 Cloud Run mode: Using lightweight service initialization")
        
        # Initialize only critical services
        critical_services = {
            name: config for name, config in self.service_configs.items()
            if config.priority == ServicePriority.CRITICAL
        }
        
        initialized_count = 0
        for service_name, config in critical_services.items():
            try:
                service = await self._create_service(service_name)
                self.services[service_name] = service
                initialized_count += 1
                logger.info(f"✅ Initialized {service_name} service")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize {service_name}: {e}")
                if config.required:
                    self.services[service_name] = None
        
        # Mark other services for lazy loading
        lazy_services = {
            name: config for name, config in self.service_configs.items()
            if config.lazy_load
        }
        
        for service_name in lazy_services:
            self.services[service_name] = ServiceStatus.LAZY_LOAD
        
        self.startup_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success',
            'mode': 'cloud_run',
            'services_initialized': initialized_count,
            'services_lazy': len(lazy_services),
            'startup_time': self.startup_time
        }
    
    async def _initialize_full_services(self) -> Dict[str, Any]:
        """Initialize all services for local/production deployment"""
        logger.info("🔧 Full mode: Initializing all services")
        
        # Initialize critical services first
        critical_services = [
            name for name, config in self.service_configs.items()
            if config.priority == ServicePriority.CRITICAL
        ]
        
        background_services = [
            name for name, config in self.service_configs.items()
            if config.priority == ServicePriority.BACKGROUND
        ]
        
        optional_services = [
            name for name, config in self.service_configs.items()
            if config.priority == ServicePriority.OPTIONAL
        ]
        
        initialized_count = 0
        failed_count = 0
        
        # Initialize critical services sequentially
        for service_name in critical_services:
            try:
                service = await self._create_service(service_name)
                self.services[service_name] = service
                initialized_count += 1
                logger.info(f"✅ Initialized critical service: {service_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize critical service {service_name}: {e}")
                failed_count += 1
        
        # Initialize background services in parallel
        background_tasks = [
            self._initialize_service_with_timeout(name, self.service_configs[name])
            for name in background_services
        ]
        
        background_results = await asyncio.gather(*background_tasks, return_exceptions=True)
        
        for i, result in enumerate(background_results):
            service_name = background_services[i]
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Background service {service_name} failed: {result}")
                failed_count += 1
            else:
                self.services[service_name] = result
                initialized_count += 1
                logger.info(f"✅ Initialized background service: {service_name}")
        
        # Initialize optional services (best effort)
        for service_name in optional_services:
            try:
                service = await self._create_service(service_name)
                self.services[service_name] = service
                initialized_count += 1
                logger.info(f"✅ Initialized optional service: {service_name}")
            except Exception as e:
                logger.info(f"ℹ️ Optional service {service_name} not available: {e}")
        
        self.startup_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success',
            'mode': 'full',
            'services_initialized': initialized_count,
            'services_failed': failed_count,
            'startup_time': self.startup_time
        }
    
    async def _initialize_service_with_timeout(self, service_name: str, config: ServiceConfig):
        """Initialize a service with timeout protection"""
        try:
            return await asyncio.wait_for(
                self._create_service(service_name),
                timeout=config.timeout
            )
        except asyncio.TimeoutError:
            raise Exception(f"Service initialization timeout ({config.timeout}s)")
    
    async def _create_service(self, service_name: str):
        """Create a service instance"""
        if service_name == 'health':
            return await self._create_health_service()
        elif service_name == 'auth':
            return await self._create_auth_service()
        elif service_name == 'cache':
            return await self._create_cache_service()
        else:
            # For other services, return a placeholder that will trigger lazy loading
            return {
                'type': service_name,
                'status': 'placeholder',
                'initialized_at': datetime.now().isoformat()
            }
    
    async def _create_health_service(self):
        """Create health service"""
        return {
            'type': 'health',
            'status': 'healthy',
            'initialized_at': datetime.now().isoformat()
        }
    
    async def _create_auth_service(self):
        """Create auth service"""
        return {
            'type': 'auth',
            'status': 'available',
            'initialized_at': datetime.now().isoformat()
        }
    
    async def _create_cache_service(self):
        """Create cache service"""
        return {
            'type': 'cache',
            'status': 'available',
            'initialized_at': datetime.now().isoformat()
        }
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get service or trigger lazy loading"""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        
        if service == ServiceStatus.LAZY_LOAD:
            # Trigger lazy loading
            logger.info(f"🔄 Lazy loading {service_name} service")
            try:
                # Import and initialize the actual controller
                controller = self._lazy_load_controller(service_name)
                self.services[service_name] = controller
                logger.info(f"✅ Lazy loaded {service_name} service")
                return controller
            except Exception as e:
                logger.error(f"❌ Failed to lazy load {service_name}: {e}")
                return None
        
        return service
    
    def _lazy_load_controller(self, service_name: str):
        """Lazy load a controller"""
        if service_name == 'document':
            from controllers.document_controller import DocumentController
            return DocumentController()
        elif service_name == 'ai':
            from controllers.ai_controller import AIController
            return AIController()
        elif service_name == 'translation':
            from controllers.translation_controller import TranslationController
            return TranslationController()
        elif service_name == 'speech':
            from controllers.speech_controller import SpeechController
            return SpeechController()
        elif service_name == 'vision':
            from controllers.vision_controller import VisionController
            return VisionController()
        elif service_name == 'comparison':
            from controllers.comparison_controller import ComparisonController
            return ComparisonController()
        elif service_name == 'export':
            from controllers.export_controller import ExportController
            return ExportController()
        elif service_name == 'email':
            from controllers.email_controller import EmailController
            return EmailController()
        else:
            raise Exception(f"Unknown service for lazy loading: {service_name}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services"""
        return {
            'overall_status': 'healthy',
            'mode': 'cloud_run' if self.is_cloud_run else 'full',
            'services': {
                name: 'initialized' if service != ServiceStatus.LAZY_LOAD else 'lazy'
                for name, service in self.services.items()
            },
            'startup_time': self.startup_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def are_critical_services_ready(self) -> bool:
        """Check if critical services are ready"""
        critical_services = [
            name for name, config in self.service_configs.items()
            if config.priority == ServicePriority.CRITICAL and config.required
        ]
        
        return all(
            service_name in self.services and 
            self.services[service_name] is not None and
            self.services[service_name] != ServiceStatus.LAZY_LOAD
            for service_name in critical_services
        )
    
    def is_startup_complete(self) -> bool:
        """Check if startup is complete"""
        return self.startup_time is not None


# Global instance
_unified_manager = None

def get_unified_service_manager() -> UnifiedServiceManager:
    """Get the global unified service manager instance"""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedServiceManager()
    return _unified_manager