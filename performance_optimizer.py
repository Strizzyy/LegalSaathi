"""
Performance Optimization Module
Implements caching, compression, and performance enhancements
"""

import time
import gzip
import json
import hashlib
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, make_response, g
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Performance optimization and caching system"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'cache_size': 0,
            'avg_response_time': 0.0
        }
        self.max_cache_size = 1000  # Maximum number of cached items
        self.cache_ttl = 3600  # 1 hour TTL
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.cache_ttl:
                self.cache_stats['hits'] += 1
                return item['data']
            else:
                # Remove expired item
                del self.cache[key]
                self.cache_stats['cache_size'] = len(self.cache)
        
        self.cache_stats['misses'] += 1
        return None
    
    def store_in_cache(self, key: str, data: Any) -> None:
        """Store item in cache with TTL"""
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest item
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        self.cache_stats['cache_size'] = len(self.cache)
    
    def cached_function(self, ttl: int = None):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Update performance stats
                self.cache_stats['total_requests'] += 1
                total_requests = self.cache_stats['total_requests']
                current_avg = self.cache_stats['avg_response_time']
                new_avg = ((current_avg * (total_requests - 1)) + execution_time) / total_requests
                self.cache_stats['avg_response_time'] = new_avg
                
                # Store in cache
                self.store_in_cache(cache_key, result)
                
                return result
            return wrapper
        return decorator
    
    def compress_response(self, response_data: str, threshold: int = 1024) -> tuple:
        """Compress response if it's larger than threshold"""
        if len(response_data) > threshold:
            compressed = gzip.compress(response_data.encode('utf-8'))
            if len(compressed) < len(response_data):
                return compressed, True
        return response_data.encode('utf-8'), False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': self.cache_stats['cache_size'],
            'max_cache_size': self.max_cache_size,
            'avg_response_time': round(self.cache_stats['avg_response_time'], 3),
            'total_requests': self.cache_stats['total_requests']
        }
    
    def clear_cache(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        self.cache_stats['cache_size'] = 0
        logger.info("Cache cleared")

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Set start time in Flask g object for request tracking
        g.request_start_time = start_time
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            
            # Log slow requests
            if execution_time > 5.0:  # Log requests taking more than 5 seconds
                logger.warning(f"Slow request: {func.__name__} took {execution_time:.2f}s")
            
            # Store performance data
            g.request_execution_time = execution_time
    
    return wrapper

def compress_json_response(data: Dict[str, Any], threshold: int = 1024):
    """Compress JSON response if beneficial"""
    json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
    
    if len(json_str) > threshold:
        compressed = gzip.compress(json_str.encode('utf-8'))
        if len(compressed) < len(json_str) * 0.8:  # Only if 20%+ compression
            response = make_response(compressed)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Length'] = len(compressed)
            return response
    
    # Return uncompressed if compression not beneficial
    response = make_response(json_str)
    response.headers['Content-Type'] = 'application/json'
    return response

class RequestOptimizer:
    """Optimize individual requests"""
    
    @staticmethod
    def add_performance_headers(response):
        """Add performance-related headers"""
        if hasattr(g, 'request_start_time'):
            execution_time = time.time() - g.request_start_time
            response.headers['X-Response-Time'] = f"{execution_time:.3f}s"
        
        # Add caching headers for static content
        if request.endpoint in ['static', 'favicon']:
            response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    @staticmethod
    def optimize_document_processing(document_text: str) -> str:
        """Optimize document text for faster processing"""
        # Remove excessive whitespace
        lines = document_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(line.split())  # Normalize whitespace
            if cleaned_line:  # Skip empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def batch_ai_requests(requests_list: list, batch_size: int = 5):
        """Batch multiple AI requests for efficiency"""
        batches = []
        for i in range(0, len(requests_list), batch_size):
            batch = requests_list[i:i + batch_size]
            batches.append(batch)
        return batches

# Performance monitoring middleware
def setup_performance_monitoring(app):
    """Set up performance monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        g.request_start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Add performance headers
        response = RequestOptimizer.add_performance_headers(response)
        
        # Log request metrics
        if hasattr(g, 'request_start_time'):
            execution_time = time.time() - g.request_start_time
            
            # Log to performance monitor
            performance_optimizer.cache_stats['total_requests'] += 1
            
            # Update average response time
            total = performance_optimizer.cache_stats['total_requests']
            current_avg = performance_optimizer.cache_stats['avg_response_time']
            new_avg = ((current_avg * (total - 1)) + execution_time) / total
            performance_optimizer.cache_stats['avg_response_time'] = new_avg
        
        return response
    
    return app