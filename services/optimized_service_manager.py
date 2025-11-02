"""
Optimized Service Manager for Backend Performance Optimization
Implements parallel service initialization, connection pooling, and health monitoring
"""

import asyncio
import logging
import time
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ServicePriority(Enum):
    """Service initialization priority levels"""
    CRITICAL = "critical"      # Must be ready before app starts
    BACKGROUND = "background"  # Can initialize after app starts
    OPTIONAL = "optional"      # Can fail without affecting core functionality


class ServiceStatus(Enum):
    """Service status states"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    DEGRADED = "degraded"


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    priority: ServicePriority
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60.0
    required: bool = True


@dataclass
class ServiceMetrics:
    """Metrics for service performance tracking"""
    initialization_time: float = 0.0
    initialization_attempts: int = 0
    last_health_check: Optional[datetime] = None
    health_check_count: int = 0
    health_check_failures: int = 0
    status_changes: List[tuple] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ConnectionPoolConfig:
    """Configuration for HTTP connection pools"""
    max_connections: int = 100
    max_connections_per_host: int = 30
    keepalive_timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0


class OptimizedServiceManager:
    """
    Optimized service manager with parallel initialization and connection pooling
    """
    
    def __init__(self, connection_config: Optional[ConnectionPoolConfig] = None):
        self.services: Dict[str, Any] = {}
        self.service_configs: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.initialization_tasks: Dict[str, asyncio.Task] = {}
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        
        # Connection pooling
        self.connection_config = connection_config or ConnectionPoolConfig()
        self.http_sessions: Dict[str, aiohttp.ClientSession] = {}
        
        # Dependency graph
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Initialization state
        self.initialization_complete = False
        self.critical_services_ready = False
        self.startup_time = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_startup_time': 0.0,
            'critical_services_startup_time': 0.0,
            'background_services_startup_time': 0.0,
            'failed_services': [],
            'degraded_services': []
        }
        
        logger.info("OptimizedServiceManager initialized")
    
    def register_service(
        self,
        name: str,
        initializer: Callable,
        priority: ServicePriority = ServicePriority.BACKGROUND,
        dependencies: List[str] = None,
        timeout: float = 30.0,
        retry_count: int = 3,
        required: bool = True
    ):
        """Register a service for managed initialization"""
        config = ServiceConfig(
            name=name,
            priority=priority,
            dependencies=dependencies or [],
            timeout=timeout,
            retry_count=retry_count,
            required=required
        )
        
        self.service_configs[name] = config
        self.service_status[name] = ServiceStatus.NOT_STARTED
        self.service_metrics[name] = ServiceMetrics()
        
        # Build dependency graph
        self.dependency_graph[name] = set(dependencies or [])
        
        # Store initializer
        self.services[f"{name}_initializer"] = initializer
        
        logger.info(f"Registered service: {name} (priority: {priority.value})")
    
    async def initialize_services(self) -> Dict[str, Any]:
        """Initialize all services with parallel execution and dependency management"""
        start_time = time.time()
        self.startup_time = datetime.now()
        
        logger.info("Starting optimized service initialization")
        
        try:
            # Initialize connection pools first
            await self._initialize_connection_pools()
            
            # Get initialization order based on dependencies and priorities
            initialization_order = self._get_initialization_order()
            
            # Initialize critical services first (parallel within priority group)
            critical_services = [
                name for name in initialization_order 
                if self.service_configs[name].priority == ServicePriority.CRITICAL
            ]
            
            if critical_services:
                logger.info(f"Initializing critical services: {critical_services}")
                critical_start = time.time()
                
                await self._initialize_service_group(critical_services)
                
                critical_time = time.time() - critical_start
                self.performance_metrics['critical_services_startup_time'] = critical_time
                
                # Check if critical services are ready
                self.critical_services_ready = all(
                    self.service_status[name] in [ServiceStatus.READY, ServiceStatus.DEGRADED]
                    for name in critical_services
                    if self.service_configs[name].required
                )
                
                logger.info(f"Critical services initialized in {critical_time:.2f}s")
            
            # Start background services (don't wait for completion)
            background_services = [
                name for name in initialization_order 
                if self.service_configs[name].priority == ServicePriority.BACKGROUND
            ]
            
            if background_services:
                logger.info(f"Starting background service initialization: {background_services}")
                background_start = time.time()
                
                # Start background initialization but don't wait
                asyncio.create_task(self._initialize_background_services(background_services, background_start))
            
            # Initialize optional services (best effort)
            optional_services = [
                name for name in initialization_order 
                if self.service_configs[name].priority == ServicePriority.OPTIONAL
            ]
            
            if optional_services:
                logger.info(f"Starting optional service initialization: {optional_services}")
                asyncio.create_task(self._initialize_optional_services(optional_services))
            
            total_time = time.time() - start_time
            self.performance_metrics['total_startup_time'] = total_time
            
            # Start health monitoring
            await self._start_health_monitoring()
            
            self.initialization_complete = True
            
            logger.info(f"Service initialization completed in {total_time:.2f}s")
            
            return self._get_initialization_summary()
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise
    
    async def _initialize_connection_pools(self):
        """Initialize HTTP connection pools for external API calls"""
        try:
            # Create connector with optimized settings
            connector = aiohttp.TCPConnector(
                limit=self.connection_config.max_connections,
                limit_per_host=self.connection_config.max_connections_per_host,
                keepalive_timeout=self.connection_config.keepalive_timeout,
                enable_cleanup_closed=True,
                use_dns_cache=True,
                ttl_dns_cache=300,  # 5 minutes DNS cache
                family=0  # Allow both IPv4 and IPv6
            )
            
            # Create timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=self.connection_config.total_timeout,
                connect=self.connection_config.connect_timeout,
                sock_read=self.connection_config.read_timeout
            )
            
            # Create session for Google Cloud services
            self.http_sessions['google_cloud'] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'LegalSaathi/2.0',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate'
                }
            )
            
            # Create session for other external APIs
            self.http_sessions['external'] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'LegalSaathi/2.0'}
            )
            
            logger.info("HTTP connection pools initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    def _get_initialization_order(self) -> List[str]:
        """Get service initialization order based on dependencies and priorities"""
        # Topological sort with priority consideration
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            for dependency in self.dependency_graph.get(service_name, set()):
                if dependency in self.service_configs:
                    visit(dependency)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        # Sort services by priority first, then apply topological sort
        services_by_priority = {
            ServicePriority.CRITICAL: [],
            ServicePriority.BACKGROUND: [],
            ServicePriority.OPTIONAL: []
        }
        
        for name, config in self.service_configs.items():
            services_by_priority[config.priority].append(name)
        
        # Process in priority order
        final_order = []
        for priority in [ServicePriority.CRITICAL, ServicePriority.BACKGROUND, ServicePriority.OPTIONAL]:
            for service_name in services_by_priority[priority]:
                if service_name not in visited:
                    visit(service_name)
                    final_order.append(service_name)
        
        return final_order
    
    async def _initialize_service_group(self, service_names: List[str]):
        """Initialize a group of services in parallel"""
        tasks = []
        
        for service_name in service_names:
            task = asyncio.create_task(
                self._initialize_single_service(service_name),
                name=f"init_{service_name}"
            )
            tasks.append(task)
            self.initialization_tasks[service_name] = task
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                logger.error(f"Service {service_name} initialization failed: {result}")
                self.service_status[service_name] = ServiceStatus.FAILED
                self.service_metrics[service_name].error_count += 1
                self.service_metrics[service_name].last_error = str(result)
    
    async def _initialize_background_services(self, service_names: List[str], start_time: float):
        """Initialize background services without blocking startup"""
        try:
            await self._initialize_service_group(service_names)
            
            background_time = time.time() - start_time
            self.performance_metrics['background_services_startup_time'] = background_time
            
            logger.info(f"Background services initialized in {background_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Background service initialization failed: {e}")
    
    async def _initialize_optional_services(self, service_names: List[str]):
        """Initialize optional services with best effort"""
        for service_name in service_names:
            try:
                await self._initialize_single_service(service_name)
            except Exception as e:
                logger.warning(f"Optional service {service_name} failed to initialize: {e}")
                self.service_status[service_name] = ServiceStatus.FAILED
    
    async def _initialize_single_service(self, service_name: str):
        """Initialize a single service with retry logic and metrics"""
        config = self.service_configs[service_name]
        metrics = self.service_metrics[service_name]
        
        start_time = time.time()
        self.service_status[service_name] = ServiceStatus.INITIALIZING
        
        initializer = self.services.get(f"{service_name}_initializer")
        if not initializer:
            raise ValueError(f"No initializer found for service {service_name}")
        
        for attempt in range(config.retry_count):
            try:
                metrics.initialization_attempts += 1
                
                logger.info(f"Initializing service {service_name} (attempt {attempt + 1}/{config.retry_count})")
                
                # Call the service initializer
                if asyncio.iscoroutinefunction(initializer):
                    service_instance = await asyncio.wait_for(
                        initializer(), 
                        timeout=config.timeout
                    )
                else:
                    service_instance = await asyncio.wait_for(
                        asyncio.to_thread(initializer),
                        timeout=config.timeout
                    )
                
                # Store the initialized service
                self.services[service_name] = service_instance
                self.service_status[service_name] = ServiceStatus.READY
                
                initialization_time = time.time() - start_time
                metrics.initialization_time = initialization_time
                
                # Record status change
                metrics.status_changes.append((datetime.now(), ServiceStatus.READY))
                
                logger.info(f"Service {service_name} initialized successfully in {initialization_time:.2f}s")
                return service_instance
                
            except asyncio.TimeoutError:
                logger.warning(f"Service {service_name} initialization timeout (attempt {attempt + 1})")
                if attempt < config.retry_count - 1:
                    await asyncio.sleep(config.retry_delay * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Service {service_name} initialization failed (attempt {attempt + 1}): {e}")
                metrics.error_count += 1
                metrics.last_error = str(e)
                
                if attempt < config.retry_count - 1:
                    await asyncio.sleep(config.retry_delay * (attempt + 1))
        
        # All attempts failed
        if config.required:
            self.service_status[service_name] = ServiceStatus.FAILED
            self.performance_metrics['failed_services'].append(service_name)
            raise Exception(f"Required service {service_name} failed to initialize after {config.retry_count} attempts")
        else:
            self.service_status[service_name] = ServiceStatus.DEGRADED
            self.performance_metrics['degraded_services'].append(service_name)
            logger.warning(f"Non-required service {service_name} failed to initialize, continuing with degraded functionality")
    
    async def _start_health_monitoring(self):
        """Start health monitoring for all services"""
        for service_name in self.service_configs:
            if self.service_status[service_name] == ServiceStatus.READY:
                task = asyncio.create_task(
                    self._monitor_service_health(service_name),
                    name=f"health_{service_name}"
                )
                self.health_check_tasks[service_name] = task
        
        logger.info("Health monitoring started for all ready services")
    
    async def _monitor_service_health(self, service_name: str):
        """Monitor health of a specific service"""
        config = self.service_configs[service_name]
        metrics = self.service_metrics[service_name]
        
        while True:
            try:
                await asyncio.sleep(config.health_check_interval)
                
                # Perform health check
                service = self.services.get(service_name)
                if service and hasattr(service, 'health_check'):
                    try:
                        if asyncio.iscoroutinefunction(service.health_check):
                            health_result = await service.health_check()
                        else:
                            health_result = service.health_check()
                        
                        metrics.health_check_count += 1
                        metrics.last_health_check = datetime.now()
                        
                        # Update status based on health check
                        if health_result:
                            if self.service_status[service_name] == ServiceStatus.DEGRADED:
                                self.service_status[service_name] = ServiceStatus.READY
                                logger.info(f"Service {service_name} recovered")
                        else:
                            if self.service_status[service_name] == ServiceStatus.READY:
                                self.service_status[service_name] = ServiceStatus.DEGRADED
                                logger.warning(f"Service {service_name} health check failed")
                                metrics.health_check_failures += 1
                    
                    except Exception as e:
                        logger.error(f"Health check failed for {service_name}: {e}")
                        metrics.health_check_failures += 1
                        
                        if self.service_status[service_name] == ServiceStatus.READY:
                            self.service_status[service_name] = ServiceStatus.DEGRADED
                
            except asyncio.CancelledError:
                logger.info(f"Health monitoring stopped for {service_name}")
                break
            except Exception as e:
                logger.error(f"Health monitoring error for {service_name}: {e}")
    
    def get_http_session(self, service_type: str = 'external') -> aiohttp.ClientSession:
        """Get HTTP session for external API calls"""
        return self.http_sessions.get(service_type, self.http_sessions.get('external'))
    
    def get_service(self, service_name: str) -> Any:
        """Get initialized service instance"""
        return self.services.get(service_name)
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get current status of a service"""
        return self.service_status.get(service_name, ServiceStatus.NOT_STARTED)
    
    def get_service_metrics(self, service_name: str) -> ServiceMetrics:
        """Get metrics for a specific service"""
        return self.service_metrics.get(service_name, ServiceMetrics())
    
    def is_service_ready(self, service_name: str) -> bool:
        """Check if a service is ready"""
        return self.service_status.get(service_name) == ServiceStatus.READY
    
    def are_critical_services_ready(self) -> bool:
        """Check if all critical services are ready"""
        return self.critical_services_ready
    
    def is_initialization_complete(self) -> bool:
        """Check if initialization is complete"""
        return self.initialization_complete
    
    def _get_initialization_summary(self) -> Dict[str, Any]:
        """Get summary of initialization results"""
        ready_services = [
            name for name, status in self.service_status.items() 
            if status == ServiceStatus.READY
        ]
        
        failed_services = [
            name for name, status in self.service_status.items() 
            if status == ServiceStatus.FAILED
        ]
        
        degraded_services = [
            name for name, status in self.service_status.items() 
            if status == ServiceStatus.DEGRADED
        ]
        
        return {
            'initialization_complete': self.initialization_complete,
            'critical_services_ready': self.critical_services_ready,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'performance_metrics': self.performance_metrics,
            'services': {
                'ready': ready_services,
                'failed': failed_services,
                'degraded': degraded_services,
                'total': len(self.service_configs)
            },
            'service_status': {
                name: status.value for name, status in self.service_status.items()
            },
            'service_metrics': {
                name: {
                    'initialization_time': metrics.initialization_time,
                    'initialization_attempts': metrics.initialization_attempts,
                    'health_check_count': metrics.health_check_count,
                    'health_check_failures': metrics.health_check_failures,
                    'error_count': metrics.error_count,
                    'last_error': metrics.last_error
                }
                for name, metrics in self.service_metrics.items()
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            'overall_status': 'healthy' if self.critical_services_ready else 'degraded',
            'initialization_complete': self.initialization_complete,
            'critical_services_ready': self.critical_services_ready,
            'services': {
                name: {
                    'status': status.value,
                    'metrics': {
                        'initialization_time': self.service_metrics[name].initialization_time,
                        'health_check_count': self.service_metrics[name].health_check_count,
                        'health_check_failures': self.service_metrics[name].health_check_failures,
                        'error_count': self.service_metrics[name].error_count,
                        'last_health_check': (
                            self.service_metrics[name].last_health_check.isoformat()
                            if self.service_metrics[name].last_health_check else None
                        )
                    }
                }
                for name, status in self.service_status.items()
            },
            'performance_metrics': self.performance_metrics,
            'connection_pools': {
                'active_sessions': len(self.http_sessions),
                'session_types': list(self.http_sessions.keys())
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Gracefully shutdown all services and connections"""
        logger.info("Starting graceful shutdown")
        
        # Cancel health monitoring tasks
        for task in self.health_check_tasks.values():
            task.cancel()
        
        # Cancel initialization tasks
        for task in self.initialization_tasks.values():
            if not task.done():
                task.cancel()
        
        # Close HTTP sessions
        for session in self.http_sessions.values():
            await session.close()
        
        # Shutdown services that have shutdown methods
        for service_name, service in self.services.items():
            if hasattr(service, 'shutdown'):
                try:
                    if asyncio.iscoroutinefunction(service.shutdown):
                        await service.shutdown()
                    else:
                        service.shutdown()
                    logger.info(f"Service {service_name} shutdown completed")
                except Exception as e:
                    logger.error(f"Error shutting down service {service_name}: {e}")
        
        logger.info("Graceful shutdown completed")


# Global service manager instance
_service_manager: Optional[OptimizedServiceManager] = None


def get_service_manager() -> OptimizedServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = OptimizedServiceManager()
    return _service_manager


@asynccontextmanager
async def managed_service_lifecycle():
    """Context manager for service lifecycle management"""
    service_manager = get_service_manager()
    try:
        yield service_manager
    finally:
        await service_manager.shutdown()