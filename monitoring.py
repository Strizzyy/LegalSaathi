"""
Production Monitoring and Health Check Module
Provides comprehensive system health monitoring and analytics
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    uptime_seconds: float
    timestamp: datetime

@dataclass
class ServiceHealth:
    """Individual service health status"""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time: float
    last_check: datetime
    error_message: str = None

class ProductionMonitor:
    """Production monitoring and analytics system"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: List[SystemMetrics] = []
        self.service_health: Dict[str, ServiceHealth] = {}
        self.request_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'requests_per_minute': 0,
            'last_minute_requests': []
        }
        self.lock = threading.Lock()
        
        # Start background monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    self._cleanup_old_metrics()
                    time.sleep(30)  # Collect metrics every 30 seconds
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Count active connections (approximate)
            connections = len(psutil.net_connections())
            
            uptime = time.time() - self.start_time
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                active_connections=connections,
                uptime_seconds=uptime,
                timestamp=datetime.now()
            )
            
            with self.lock:
                self.metrics_history.append(metrics)
                
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than 1 hour"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        with self.lock:
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
    
    def record_request(self, success: bool, response_time: float):
        """Record request metrics"""
        current_time = time.time()
        
        with self.lock:
            self.request_metrics['total_requests'] += 1
            
            if success:
                self.request_metrics['successful_requests'] += 1
            else:
                self.request_metrics['failed_requests'] += 1
            
            # Update average response time
            total = self.request_metrics['total_requests']
            current_avg = self.request_metrics['avg_response_time']
            new_avg = ((current_avg * (total - 1)) + response_time) / total
            self.request_metrics['avg_response_time'] = new_avg
            
            # Track requests per minute
            self.request_metrics['last_minute_requests'].append(current_time)
            
            # Clean old requests (older than 1 minute)
            minute_ago = current_time - 60
            self.request_metrics['last_minute_requests'] = [
                t for t in self.request_metrics['last_minute_requests']
                if t > minute_ago
            ]
            
            self.request_metrics['requests_per_minute'] = len(
                self.request_metrics['last_minute_requests']
            )
    
    def check_service_health(self, service_name: str, check_function) -> ServiceHealth:
        """Check health of a specific service"""
        start_time = time.time()
        
        try:
            # Run the health check function
            is_healthy = check_function()
            response_time = time.time() - start_time
            
            status = 'healthy' if is_healthy else 'unhealthy'
            
            health = ServiceHealth(
                name=service_name,
                status=status,
                response_time=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            health = ServiceHealth(
                name=service_name,
                status='unhealthy',
                response_time=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )
        
        self.service_health[service_name] = health
        return health
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        current_metrics = self.get_current_metrics()
        
        # Determine overall health
        overall_status = 'healthy'
        
        # Check system resources
        if (current_metrics['cpu_percent'] > 90 or 
            current_metrics['memory_percent'] > 90 or
            current_metrics['disk_percent'] > 95):
            overall_status = 'degraded'
        
        # Check service health
        unhealthy_services = [
            name for name, health in self.service_health.items()
            if health.status == 'unhealthy'
        ]
        
        if unhealthy_services:
            overall_status = 'degraded' if len(unhealthy_services) == 1 else 'unhealthy'
        
        # Check error rate
        total_requests = self.request_metrics['total_requests']
        if total_requests > 0:
            error_rate = self.request_metrics['failed_requests'] / total_requests
            if error_rate > 0.1:  # More than 10% error rate
                overall_status = 'degraded'
            elif error_rate > 0.25:  # More than 25% error rate
                overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': time.time() - self.start_time,
            'system_metrics': current_metrics,
            'services': {name: asdict(health) for name, health in self.service_health.items()},
            'request_metrics': self.request_metrics.copy(),
            'unhealthy_services': unhealthy_services
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'active_connections': len(psutil.net_connections()),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_available_gb': 0,
                'disk_percent': 0,
                'disk_free_gb': 0,
                'active_connections': 0,
                'load_average': [0, 0, 0]
            }
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get analytics dashboard data"""
        with self.lock:
            recent_metrics = self.metrics_history[-60:]  # Last 60 data points (30 minutes)
        
        if not recent_metrics:
            return {'error': 'No metrics available'}
        
        # Calculate trends
        cpu_trend = [m.cpu_percent for m in recent_metrics]
        memory_trend = [m.memory_percent for m in recent_metrics]
        
        return {
            'current_status': self.get_health_status(),
            'trends': {
                'cpu_usage': cpu_trend,
                'memory_usage': memory_trend,
                'timestamps': [m.timestamp.isoformat() for m in recent_metrics]
            },
            'performance_summary': {
                'avg_cpu': sum(cpu_trend) / len(cpu_trend) if cpu_trend else 0,
                'avg_memory': sum(memory_trend) / len(memory_trend) if memory_trend else 0,
                'peak_cpu': max(cpu_trend) if cpu_trend else 0,
                'peak_memory': max(memory_trend) if memory_trend else 0
            },
            'request_analytics': self.request_metrics.copy()
        }

# Global monitor instance
production_monitor = ProductionMonitor()

def health_check_decorator(monitor_instance=None):
    """Decorator to monitor request performance"""
    if monitor_instance is None:
        monitor_instance = production_monitor
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                response_time = time.time() - start_time
                monitor_instance.record_request(success, response_time)
        
        return wrapper
    return decorator