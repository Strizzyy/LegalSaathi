"""
Startup Manager for Optimized Backend Initialization
Integrates OptimizedServiceManager with FastAPI application lifecycle
"""

import logging
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager

from services.optimized_service_manager import (
    OptimizedServiceManager, 
    ServicePriority, 
    ConnectionPoolConfig,
    get_service_manager
)
from services.service_initializers import (
    get_service_initializer,
    get_service_dependencies
)

logger = logging.getLogger(__name__)


class StartupManager:
    """
    Manages application startup with optimized service initialization
    """
    
    def __init__(self):
        self.service_manager = get_service_manager()
        self.startup_complete = False
        self.startup_error = None
        
    async def initialize_application(self) -> Dict[str, Any]:
        """
        Initialize the application with optimized service loading
        """
        try:
            logger.info("🚀 Starting optimized application initialization")
            
            # Configure connection pooling
            connection_config = ConnectionPoolConfig(
                max_connections=100,
                max_connections_per_host=30,
                keepalive_timeout=30.0,
                connect_timeout=10.0,
                read_timeout=30.0,
                total_timeout=60.0
            )
            
            # Register all services with their priorities and dependencies
            await self._register_services()
            
            # Initialize services using the optimized manager
            initialization_result = await self.service_manager.initialize_services()
            
            self.startup_complete = True
            
            logger.info("✅ Optimized application initialization completed successfully")
            
            return initialization_result
            
        except Exception as e:
            self.startup_error = str(e)
            logger.error(f"❌ Application initialization failed: {e}")
            raise
    
    async def _register_services(self):
        """Register all services with the service manager"""
        
        # Critical services (must be ready before app starts)
        critical_services = [
            ('health', 10.0, True),      # Health checks
            ('cache', 15.0, True),       # Caching system
            ('auth', 20.0, False),       # Authentication (not required for basic functionality)
            ('document', 30.0, True),    # Document processing
        ]
        
        # Background services (can initialize after app starts)
        background_services = [
            ('ai', 45.0, True),          # AI services
            ('translation', 30.0, False), # Translation services
            ('speech', 25.0, False),     # Speech services
            ('vision', 35.0, False),     # Vision processing
            ('comparison', 20.0, False), # Document comparison
            ('export', 15.0, False),     # Export functionality
        ]
        
        # Optional services (best effort initialization)
        optional_services = [
            ('email', 20.0, False),              # Email services
            ('cost_monitoring', 10.0, False),    # Cost monitoring
            ('quota_management', 10.0, False),   # Quota management
        ]
        
        # Register critical services
        for service_name, timeout, required in critical_services:
            initializer = get_service_initializer(service_name)
            dependencies = get_service_dependencies(service_name)
            
            if initializer:
                self.service_manager.register_service(
                    name=service_name,
                    initializer=initializer,
                    priority=ServicePriority.CRITICAL,
                    dependencies=dependencies,
                    timeout=timeout,
                    retry_count=3,
                    required=required
                )
                logger.info(f"Registered critical service: {service_name}")
        
        # Register background services
        for service_name, timeout, required in background_services:
            initializer = get_service_initializer(service_name)
            dependencies = get_service_dependencies(service_name)
            
            if initializer:
                self.service_manager.register_service(
                    name=service_name,
                    initializer=initializer,
                    priority=ServicePriority.BACKGROUND,
                    dependencies=dependencies,
                    timeout=timeout,
                    retry_count=2,
                    required=required
                )
                logger.info(f"Registered background service: {service_name}")
        
        # Register optional services
        for service_name, timeout, required in optional_services:
            initializer = get_service_initializer(service_name)
            dependencies = get_service_dependencies(service_name)
            
            if initializer:
                self.service_manager.register_service(
                    name=service_name,
                    initializer=initializer,
                    priority=ServicePriority.OPTIONAL,
                    dependencies=dependencies,
                    timeout=timeout,
                    retry_count=1,
                    required=required
                )
                logger.info(f"Registered optional service: {service_name}")
    
    def get_service(self, service_name: str) -> Any:
        """Get an initialized service"""
        return self.service_manager.get_service(service_name)
    
    def is_service_ready(self, service_name: str) -> bool:
        """Check if a service is ready"""
        return self.service_manager.is_service_ready(service_name)
    
    def are_critical_services_ready(self) -> bool:
        """Check if critical services are ready"""
        return self.service_manager.are_critical_services_ready()
    
    def is_startup_complete(self) -> bool:
        """Check if startup is complete"""
        return self.startup_complete
    
    def get_startup_status(self) -> Dict[str, Any]:
        """Get detailed startup status"""
        return {
            'startup_complete': self.startup_complete,
            'startup_error': self.startup_error,
            'critical_services_ready': self.service_manager.are_critical_services_ready(),
            'initialization_complete': self.service_manager.is_initialization_complete(),
            'service_manager_status': self.service_manager.get_health_status()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return self.service_manager.get_health_status()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get startup and service performance metrics"""
        health_status = self.service_manager.get_health_status()
        return {
            'startup_metrics': health_status.get('performance_metrics', {}),
            'service_metrics': health_status.get('services', {}),
            'connection_pools': health_status.get('connection_pools', {}),
            'overall_status': health_status.get('overall_status', 'unknown')
        }
    
    async def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("🛑 Starting graceful application shutdown")
        await self.service_manager.shutdown()
        logger.info("✅ Application shutdown completed")


# Global startup manager instance
_startup_manager = None


def get_startup_manager() -> StartupManager:
    """Get the global startup manager instance"""
    global _startup_manager
    if _startup_manager is None:
        _startup_manager = StartupManager()
    return _startup_manager


@asynccontextmanager
async def optimized_lifespan(app):
    """
    Optimized FastAPI lifespan context manager
    Replaces the existing lifespan function in main.py
    """
    startup_manager = get_startup_manager()
    
    try:
        # Startup
        logger.info("🚀 Starting Legal Saathi with optimized service initialization")
        
        initialization_result = await startup_manager.initialize_application()
        
        # Log initialization summary
        logger.info("🎯 Service Initialization Summary:")
        logger.info(f"   • Total services: {initialization_result['services']['total']}")
        logger.info(f"   • Ready services: {len(initialization_result['services']['ready'])}")
        logger.info(f"   • Failed services: {len(initialization_result['services']['failed'])}")
        logger.info(f"   • Degraded services: {len(initialization_result['services']['degraded'])}")
        logger.info(f"   • Critical services ready: {initialization_result['critical_services_ready']}")
        logger.info(f"   • Total startup time: {initialization_result['performance_metrics']['total_startup_time']:.2f}s")
        logger.info(f"   • Critical services time: {initialization_result['performance_metrics']['critical_services_startup_time']:.2f}s")
        
        # Update legacy health controller for backward compatibility
        try:
            health_service = startup_manager.get_service('health')
            if health_service:
                health_service._initialization_complete = True
                health_service._services_ready.update({
                    service_name: startup_manager.is_service_ready(service_name)
                    for service_name in ['ai', 'translation', 'document', 'speech']
                })
                logger.info("🔄 Legacy health controller updated for backward compatibility")
        except Exception as e:
            logger.warning(f"⚠️ Could not update legacy health controller: {e}")
        
        logger.info("🌟 Legal Saathi is ready to serve requests!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        await startup_manager.shutdown()


# Utility functions for service access
def get_initialized_service(service_name: str):
    """Get an initialized service by name"""
    startup_manager = get_startup_manager()
    return startup_manager.get_service(service_name)


def is_service_available(service_name: str) -> bool:
    """Check if a service is available and ready"""
    startup_manager = get_startup_manager()
    return startup_manager.is_service_ready(service_name)


def get_application_health() -> Dict[str, Any]:
    """Get overall application health status"""
    startup_manager = get_startup_manager()
    return startup_manager.get_health_status()


def get_application_metrics() -> Dict[str, Any]:
    """Get application performance metrics"""
    startup_manager = get_startup_manager()
    return startup_manager.get_performance_metrics()