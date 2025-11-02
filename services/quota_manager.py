"""
Quota Manager Service for LegalSaathi - INTERNAL USE ONLY
Manages API quotas, rate limiting, and intelligent request throttling.

SECURITY WARNING: This service manages sensitive quota and rate limiting data.
- Never expose quota information to end users
- Only use for internal API management
- Protects our Google Cloud API limits and costs
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from collections import defaultdict, deque
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ThrottleAction(Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    REJECT = "reject"

class ServicePriority(Enum):
    HIGH = 1      # Critical operations
    MEDIUM = 2    # Standard operations
    LOW = 3       # Background operations

@dataclass
class QuotaLimit:
    service: str
    limit_per_minute: int
    limit_per_hour: int
    limit_per_day: int
    burst_limit: int
    priority: ServicePriority

@dataclass
class RateLimitResult:
    action: ThrottleAction
    allowed: bool
    retry_after: Optional[int]  # seconds
    current_usage: int
    limit: int
    reset_time: datetime
    message: str

@dataclass
class RequestBatch:
    requests: List[Dict[str, Any]]
    batch_id: str
    service: str
    operation: str
    created_at: datetime
    priority: ServicePriority

class QuotaManager:
    """
    Advanced quota management with intelligent throttling and request batching.
    Provides rate limiting, quota monitoring, and optimization for Google Cloud AI services.
    """
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/1')  # Use different DB
        
        # Initialize Redis for rate limiting
        try:
            if self.redis_url.startswith('redis://'):
                self.redis_client = redis.from_url(self.redis_url)
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
            self.redis_client.ping()  # Test connection
            self.redis_enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory rate limiting: {e}")
            self.redis_client = None
            self.redis_enabled = False
            # Fallback to in-memory storage
            self.memory_storage = defaultdict(lambda: defaultdict(deque))
        
        # Configure quota limits for each service
        self.quota_limits = {
            "vertex_ai": QuotaLimit(
                service="vertex_ai",
                limit_per_minute=100000,  # tokens per minute (increased for development)
                limit_per_hour=500000,    # tokens per hour (increased for development)
                limit_per_day=10000000,   # tokens per day (increased for development)
                burst_limit=200000,       # burst capacity (increased for development)
                priority=ServicePriority.HIGH
            ),
            "gemini_api": QuotaLimit(
                service="gemini_api",
                limit_per_minute=500,     # tokens per minute
                limit_per_hour=25000,     # tokens per hour
                limit_per_day=500000,     # tokens per day
                burst_limit=1000,         # burst capacity
                priority=ServicePriority.MEDIUM
            ),
            "document_ai": QuotaLimit(
                service="document_ai",
                limit_per_minute=10,      # pages per minute
                limit_per_hour=500,       # pages per hour
                limit_per_day=5000,       # pages per day
                burst_limit=20,           # burst capacity
                priority=ServicePriority.HIGH
            ),
            "natural_language_ai": QuotaLimit(
                service="natural_language_ai",
                limit_per_minute=10000,   # requests per minute (increased for development)
                limit_per_hour=50000,     # requests per hour (increased for development)
                limit_per_day=500000,     # requests per day (increased for development)
                burst_limit=20000,        # burst capacity (increased for development)
                priority=ServicePriority.MEDIUM
            ),
            "translation_api": QuotaLimit(
                service="translation_api",
                limit_per_minute=1000,    # characters per minute (in thousands)
                limit_per_hour=50000,     # characters per hour (in thousands)
                limit_per_day=1000000,    # characters per day (in thousands)
                burst_limit=2000,         # burst capacity
                priority=ServicePriority.LOW
            ),
            "vision_api": QuotaLimit(
                service="vision_api",
                limit_per_minute=60,      # images per minute
                limit_per_hour=3000,      # images per hour
                limit_per_day=30000,      # images per day
                burst_limit=120,          # burst capacity
                priority=ServicePriority.MEDIUM
            ),
            "speech_api": QuotaLimit(
                service="speech_api",
                limit_per_minute=60,      # minutes of audio per minute
                limit_per_hour=1000,      # minutes of audio per hour
                limit_per_day=10000,      # minutes of audio per day
                burst_limit=120,          # burst capacity
                priority=ServicePriority.LOW
            )
        }
        
        # Batch processing configuration
        self.batch_config = {
            "max_batch_size": 10,
            "batch_timeout": 5.0,  # seconds
            "batch_enabled_services": ["vertex_ai", "gemini_api", "natural_language_ai"]
        }
        
        # Active batches
        self.active_batches = {}
        self.batch_timers = {}
        
        # Circuit breaker configuration
        self.circuit_breakers = {}
        self.circuit_breaker_config = {
            "failure_threshold": 5,
            "recovery_timeout": 60,  # seconds
            "half_open_max_calls": 3
        }
        
        logger.info("Quota Manager initialized")
    
    async def check_rate_limit(
        self,
        service: str,
        operation: str,
        usage_amount: int = 1,
        user_id: str = None,
        priority: ServicePriority = ServicePriority.MEDIUM
    ) -> RateLimitResult:
        """
        Check if request is within rate limits
        """
        try:
            quota_limit = self.quota_limits.get(service)
            if not quota_limit:
                # No limits configured for this service
                return RateLimitResult(
                    action=ThrottleAction.ALLOW,
                    allowed=True,
                    retry_after=None,
                    current_usage=0,
                    limit=999999,
                    reset_time=datetime.utcnow() + timedelta(minutes=1),
                    message="No rate limits configured"
                )
            
            # Check circuit breaker first
            circuit_result = await self._check_circuit_breaker(service)
            if not circuit_result:
                return RateLimitResult(
                    action=ThrottleAction.REJECT,
                    allowed=False,
                    retry_after=60,
                    current_usage=0,
                    limit=0,
                    reset_time=datetime.utcnow() + timedelta(minutes=1),
                    message="Service circuit breaker is open"
                )
            
            # Check different time windows
            minute_result = await self._check_time_window(service, "minute", usage_amount, quota_limit.limit_per_minute)
            hour_result = await self._check_time_window(service, "hour", usage_amount, quota_limit.limit_per_hour)
            day_result = await self._check_time_window(service, "day", usage_amount, quota_limit.limit_per_day)
            
            # Determine most restrictive limit
            results = [minute_result, hour_result, day_result]
            most_restrictive = min(results, key=lambda x: x.current_usage / x.limit if x.limit > 0 else float('inf'))
            
            # Check if any limit is exceeded
            if not all(result.allowed for result in results):
                failed_result = next(result for result in results if not result.allowed)
                return RateLimitResult(
                    action=ThrottleAction.REJECT,
                    allowed=False,
                    retry_after=failed_result.retry_after,
                    current_usage=failed_result.current_usage,
                    limit=failed_result.limit,
                    reset_time=failed_result.reset_time,
                    message=f"Rate limit exceeded: {failed_result.message}"
                )
            
            # Check if throttling is needed (80% of limit)
            throttle_threshold = 0.8
            should_throttle = any(
                (result.current_usage / result.limit) > throttle_threshold 
                for result in results if result.limit > 0
            )
            
            if should_throttle and priority != ServicePriority.HIGH:
                # Calculate throttle delay based on usage
                usage_ratio = most_restrictive.current_usage / most_restrictive.limit
                throttle_delay = int((usage_ratio - throttle_threshold) * 10)  # 0-2 seconds
                
                return RateLimitResult(
                    action=ThrottleAction.THROTTLE,
                    allowed=True,
                    retry_after=throttle_delay,
                    current_usage=most_restrictive.current_usage,
                    limit=most_restrictive.limit,
                    reset_time=most_restrictive.reset_time,
                    message=f"Request throttled due to high usage"
                )
            
            # Request is allowed
            await self._record_usage(service, usage_amount)
            
            return RateLimitResult(
                action=ThrottleAction.ALLOW,
                allowed=True,
                retry_after=None,
                current_usage=most_restrictive.current_usage + usage_amount,
                limit=most_restrictive.limit,
                reset_time=most_restrictive.reset_time,
                message="Request allowed"
            )
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open - allow request on error
            return RateLimitResult(
                action=ThrottleAction.ALLOW,
                allowed=True,
                retry_after=None,
                current_usage=0,
                limit=999999,
                reset_time=datetime.utcnow() + timedelta(minutes=1),
                message=f"Rate limit check failed: {str(e)}"
            )
    
    async def _check_time_window(
        self,
        service: str,
        window: str,
        usage_amount: int,
        limit: int
    ) -> RateLimitResult:
        """Check rate limit for specific time window"""
        try:
            now = datetime.utcnow()
            
            # Calculate window boundaries
            if window == "minute":
                window_start = now.replace(second=0, microsecond=0)
                window_end = window_start + timedelta(minutes=1)
            elif window == "hour":
                window_start = now.replace(minute=0, second=0, microsecond=0)
                window_end = window_start + timedelta(hours=1)
            elif window == "day":
                window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                window_end = window_start + timedelta(days=1)
            else:
                raise ValueError(f"Invalid time window: {window}")
            
            # Get current usage for window
            current_usage = await self._get_window_usage(service, window, window_start)
            
            # Check if adding this usage would exceed limit
            new_usage = current_usage + usage_amount
            allowed = new_usage <= limit
            
            # Calculate retry after time
            retry_after = None
            if not allowed:
                retry_after = int((window_end - now).total_seconds())
            
            return RateLimitResult(
                action=ThrottleAction.ALLOW if allowed else ThrottleAction.REJECT,
                allowed=allowed,
                retry_after=retry_after,
                current_usage=current_usage,
                limit=limit,
                reset_time=window_end,
                message=f"{window} limit {'within' if allowed else 'exceeded'}"
            )
            
        except Exception as e:
            logger.error(f"Error checking time window {window}: {e}")
            # Fail open
            return RateLimitResult(
                action=ThrottleAction.ALLOW,
                allowed=True,
                retry_after=None,
                current_usage=0,
                limit=limit,
                reset_time=datetime.utcnow() + timedelta(minutes=1),
                message=f"Window check failed: {str(e)}"
            )
    
    async def _get_window_usage(self, service: str, window: str, window_start: datetime) -> int:
        """Get current usage for time window"""
        try:
            key = f"quota:{service}:{window}:{window_start.strftime('%Y%m%d_%H%M')}"
            
            if self.redis_enabled:
                usage = self.redis_client.get(key)
                return int(usage) if usage else 0
            else:
                # Use in-memory storage
                window_key = f"{window}_{window_start.strftime('%Y%m%d_%H%M')}"
                usage_data = self.memory_storage[service][window_key]
                return sum(usage_data) if usage_data else 0
                
        except Exception as e:
            logger.error(f"Error getting window usage: {e}")
            return 0
    
    async def _record_usage(self, service: str, usage_amount: int):
        """Record usage for all time windows"""
        try:
            now = datetime.utcnow()
            
            # Record for minute window
            minute_key = f"quota:{service}:minute:{now.strftime('%Y%m%d_%H%M')}"
            await self._increment_usage(minute_key, usage_amount, 120)  # 2 minute TTL
            
            # Record for hour window
            hour_key = f"quota:{service}:hour:{now.strftime('%Y%m%d_%H')}"
            await self._increment_usage(hour_key, usage_amount, 7200)  # 2 hour TTL
            
            # Record for day window
            day_key = f"quota:{service}:day:{now.strftime('%Y%m%d')}"
            await self._increment_usage(day_key, usage_amount, 172800)  # 2 day TTL
            
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
    
    async def _increment_usage(self, key: str, amount: int, ttl: int):
        """Increment usage counter with TTL"""
        try:
            if self.redis_enabled:
                pipe = self.redis_client.pipeline()
                pipe.incrby(key, amount)
                pipe.expire(key, ttl)
                pipe.execute()
            else:
                # Use in-memory storage (simplified)
                service, window, timestamp = key.split(':')[1:4]
                self.memory_storage[service][f"{window}_{timestamp}"].append(amount)
                
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
    
    async def _check_circuit_breaker(self, service: str) -> bool:
        """Check circuit breaker status for service"""
        try:
            breaker = self.circuit_breakers.get(service)
            if not breaker:
                # Initialize circuit breaker
                self.circuit_breakers[service] = {
                    "state": "closed",  # closed, open, half_open
                    "failure_count": 0,
                    "last_failure": None,
                    "half_open_calls": 0
                }
                return True
            
            now = datetime.utcnow()
            
            if breaker["state"] == "closed":
                return True
            
            elif breaker["state"] == "open":
                # Check if recovery timeout has passed
                if (breaker["last_failure"] and 
                    (now - breaker["last_failure"]).total_seconds() > self.circuit_breaker_config["recovery_timeout"]):
                    breaker["state"] = "half_open"
                    breaker["half_open_calls"] = 0
                    logger.info(f"Circuit breaker for {service} moved to half-open state")
                    return True
                return False
            
            elif breaker["state"] == "half_open":
                # Allow limited calls in half-open state
                if breaker["half_open_calls"] < self.circuit_breaker_config["half_open_max_calls"]:
                    breaker["half_open_calls"] += 1
                    return True
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return True  # Fail open
    
    async def record_success(self, service: str):
        """Record successful API call"""
        try:
            breaker = self.circuit_breakers.get(service)
            if breaker:
                if breaker["state"] == "half_open":
                    # Successful call in half-open state
                    if breaker["half_open_calls"] >= self.circuit_breaker_config["half_open_max_calls"]:
                        breaker["state"] = "closed"
                        breaker["failure_count"] = 0
                        logger.info(f"Circuit breaker for {service} closed after successful recovery")
                
                elif breaker["state"] == "closed":
                    # Reset failure count on success
                    breaker["failure_count"] = max(0, breaker["failure_count"] - 1)
                    
        except Exception as e:
            logger.error(f"Error recording success: {e}")
    
    async def record_failure(self, service: str):
        """Record failed API call"""
        try:
            breaker = self.circuit_breakers.get(service)
            if not breaker:
                self.circuit_breakers[service] = {
                    "state": "closed",
                    "failure_count": 0,
                    "last_failure": None,
                    "half_open_calls": 0
                }
                breaker = self.circuit_breakers[service]
            
            breaker["failure_count"] += 1
            breaker["last_failure"] = datetime.utcnow()
            
            # Check if failure threshold is reached
            if breaker["failure_count"] >= self.circuit_breaker_config["failure_threshold"]:
                breaker["state"] = "open"
                logger.warning(f"Circuit breaker for {service} opened due to {breaker['failure_count']} failures")
            
            # If in half-open state, go back to open on failure
            elif breaker["state"] == "half_open":
                breaker["state"] = "open"
                logger.warning(f"Circuit breaker for {service} reopened after failure in half-open state")
                
        except Exception as e:
            logger.error(f"Error recording failure: {e}")
    
    async def create_batch(
        self,
        service: str,
        operation: str,
        requests: List[Dict[str, Any]],
        priority: ServicePriority = ServicePriority.MEDIUM
    ) -> str:
        """Create a batch of requests for processing"""
        try:
            if service not in self.batch_config["batch_enabled_services"]:
                # Service doesn't support batching
                return None
            
            batch_id = f"batch_{service}_{int(time.time())}_{hash(str(requests)) % 10000:04d}"
            
            batch = RequestBatch(
                requests=requests,
                batch_id=batch_id,
                service=service,
                operation=operation,
                created_at=datetime.utcnow(),
                priority=priority
            )
            
            self.active_batches[batch_id] = batch
            
            # Set timer for batch processing
            timer = asyncio.create_task(self._batch_timer(batch_id))
            self.batch_timers[batch_id] = timer
            
            logger.info(f"Created batch {batch_id} with {len(requests)} requests")
            return batch_id
            
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            return None
    
    async def add_to_batch(self, batch_id: str, request: Dict[str, Any]) -> bool:
        """Add request to existing batch"""
        try:
            batch = self.active_batches.get(batch_id)
            if not batch:
                return False
            
            if len(batch.requests) >= self.batch_config["max_batch_size"]:
                # Batch is full, process immediately
                await self._process_batch(batch_id)
                return False
            
            batch.requests.append(request)
            logger.debug(f"Added request to batch {batch_id}, now has {len(batch.requests)} requests")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to batch: {e}")
            return False
    
    async def _batch_timer(self, batch_id: str):
        """Timer for batch processing"""
        try:
            await asyncio.sleep(self.batch_config["batch_timeout"])
            await self._process_batch(batch_id)
        except asyncio.CancelledError:
            pass  # Timer was cancelled
        except Exception as e:
            logger.error(f"Error in batch timer: {e}")
    
    async def _process_batch(self, batch_id: str):
        """Process batch of requests"""
        try:
            batch = self.active_batches.get(batch_id)
            if not batch:
                return
            
            # Cancel timer if still running
            timer = self.batch_timers.get(batch_id)
            if timer and not timer.done():
                timer.cancel()
            
            # Remove from active batches
            del self.active_batches[batch_id]
            if batch_id in self.batch_timers:
                del self.batch_timers[batch_id]
            
            logger.info(f"Processing batch {batch_id} with {len(batch.requests)} requests")
            
            # TODO: Implement actual batch processing logic
            # This would integrate with the specific AI service APIs
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
    
    async def get_quota_status(self, service: str) -> Dict[str, Any]:
        """Get current quota status for service"""
        try:
            quota_limit = self.quota_limits.get(service)
            if not quota_limit:
                return {"error": f"No quota configuration for service: {service}"}
            
            now = datetime.utcnow()
            
            # Get usage for different windows
            minute_usage = await self._get_window_usage(
                service, "minute", now.replace(second=0, microsecond=0)
            )
            hour_usage = await self._get_window_usage(
                service, "hour", now.replace(minute=0, second=0, microsecond=0)
            )
            day_usage = await self._get_window_usage(
                service, "day", now.replace(hour=0, minute=0, second=0, microsecond=0)
            )
            
            # Get circuit breaker status
            breaker = self.circuit_breakers.get(service, {"state": "closed", "failure_count": 0})
            
            return {
                "service": service,
                "quota_limits": {
                    "per_minute": quota_limit.limit_per_minute,
                    "per_hour": quota_limit.limit_per_hour,
                    "per_day": quota_limit.limit_per_day,
                    "burst_limit": quota_limit.burst_limit
                },
                "current_usage": {
                    "per_minute": minute_usage,
                    "per_hour": hour_usage,
                    "per_day": day_usage
                },
                "usage_percentages": {
                    "per_minute": (minute_usage / quota_limit.limit_per_minute) * 100 if quota_limit.limit_per_minute > 0 else 0,
                    "per_hour": (hour_usage / quota_limit.limit_per_hour) * 100 if quota_limit.limit_per_hour > 0 else 0,
                    "per_day": (day_usage / quota_limit.limit_per_day) * 100 if quota_limit.limit_per_day > 0 else 0
                },
                "circuit_breaker": {
                    "state": breaker["state"],
                    "failure_count": breaker["failure_count"]
                },
                "priority": quota_limit.priority.name,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quota status: {e}")
            return {"error": str(e)}
    
    async def get_all_quota_status(self) -> Dict[str, Any]:
        """Get quota status for all services"""
        try:
            status = {}
            for service in self.quota_limits.keys():
                status[service] = await self.get_quota_status(service)
            
            return {
                "services": status,
                "timestamp": datetime.utcnow().isoformat(),
                "batch_config": self.batch_config,
                "active_batches": len(self.active_batches)
            }
            
        except Exception as e:
            logger.error(f"Error getting all quota status: {e}")
            return {"error": str(e)}
    
    async def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics for all services"""
        try:
            now = datetime.utcnow()
            usage_stats = {}
            
            for service in self.quota_limits.keys():
                quota_limit = self.quota_limits[service]
                
                # Get usage for different windows
                minute_usage = await self._get_window_usage(
                    service, "minute", now.replace(second=0, microsecond=0)
                )
                hour_usage = await self._get_window_usage(
                    service, "hour", now.replace(minute=0, second=0, microsecond=0)
                )
                day_usage = await self._get_window_usage(
                    service, "day", now.replace(hour=0, minute=0, second=0, microsecond=0)
                )
                
                # Get circuit breaker status
                breaker = self.circuit_breakers.get(service, {"state": "closed", "failure_count": 0})
                
                usage_stats[service] = {
                    "service_name": service.replace('_', ' ').title(),
                    "priority": quota_limit.priority.name,
                    "current_usage": {
                        "per_minute": minute_usage,
                        "per_hour": hour_usage,
                        "per_day": day_usage
                    },
                    "limits": {
                        "per_minute": quota_limit.limit_per_minute,
                        "per_hour": quota_limit.limit_per_hour,
                        "per_day": quota_limit.limit_per_day
                    },
                    "usage_percentages": {
                        "per_minute": (minute_usage / quota_limit.limit_per_minute) * 100 if quota_limit.limit_per_minute > 0 else 0,
                        "per_hour": (hour_usage / quota_limit.limit_per_hour) * 100 if quota_limit.limit_per_hour > 0 else 0,
                        "per_day": (day_usage / quota_limit.limit_per_day) * 100 if quota_limit.limit_per_day > 0 else 0
                    },
                    "circuit_breaker": {
                        "state": breaker["state"],
                        "failure_count": breaker["failure_count"]
                    },
                    "status": "active" if minute_usage > 0 or hour_usage > 0 or day_usage > 0 else "idle",
                    "last_updated": now.isoformat()
                }
            
            # Calculate totals
            total_requests_today = sum(stats["current_usage"]["per_day"] for stats in usage_stats.values())
            total_requests_hour = sum(stats["current_usage"]["per_hour"] for stats in usage_stats.values())
            active_services = len([s for s in usage_stats.values() if s["status"] == "active"])
            
            return {
                "usage_stats": usage_stats,
                "summary": {
                    "total_requests_today": total_requests_today,
                    "total_requests_hour": total_requests_hour,
                    "active_services": active_services,
                    "total_services": len(usage_stats)
                },
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {"error": str(e)}
    
    async def optimize_request_timing(
        self,
        service: str,
        operation: str,
        usage_amount: int = 1,
        priority: ServicePriority = ServicePriority.MEDIUM
    ) -> Dict[str, Any]:
        """Optimize request timing based on current quota usage"""
        try:
            # Check current rate limit status
            rate_limit_result = await self.check_rate_limit(service, operation, usage_amount, priority=priority)
            
            if rate_limit_result.action == ThrottleAction.ALLOW:
                return {
                    "recommended_action": "send_immediately",
                    "delay": 0,
                    "reason": "Within rate limits"
                }
            
            elif rate_limit_result.action == ThrottleAction.THROTTLE:
                return {
                    "recommended_action": "delay",
                    "delay": rate_limit_result.retry_after,
                    "reason": "Throttling recommended to avoid rate limits"
                }
            
            elif rate_limit_result.action == ThrottleAction.REJECT:
                return {
                    "recommended_action": "batch_or_delay",
                    "delay": rate_limit_result.retry_after,
                    "reason": "Rate limit exceeded, consider batching or delaying",
                    "batch_available": service in self.batch_config["batch_enabled_services"]
                }
            
            return {
                "recommended_action": "unknown",
                "delay": 60,
                "reason": "Unable to determine optimal timing"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing request timing: {e}")
            return {
                "recommended_action": "send_immediately",
                "delay": 0,
                "reason": f"Optimization failed: {str(e)}"
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of quota manager"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {}
            }
            
            # Check Redis connection
            try:
                if self.redis_enabled:
                    self.redis_client.ping()
                    health_status["components"]["redis"] = {"status": "healthy"}
                else:
                    health_status["components"]["redis"] = {"status": "disabled", "fallback": "in_memory"}
            except Exception as e:
                health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check quota configurations
            health_status["components"]["quota_config"] = {
                "status": "healthy",
                "services_configured": len(self.quota_limits)
            }
            
            # Check circuit breakers
            open_breakers = [service for service, breaker in self.circuit_breakers.items() if breaker["state"] == "open"]
            health_status["components"]["circuit_breakers"] = {
                "status": "healthy" if not open_breakers else "degraded",
                "open_breakers": open_breakers,
                "total_breakers": len(self.circuit_breakers)
            }
            
            # Check active batches
            health_status["components"]["batching"] = {
                "status": "healthy",
                "active_batches": len(self.active_batches),
                "active_timers": len(self.batch_timers)
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Global instance
quota_manager = QuotaManager()