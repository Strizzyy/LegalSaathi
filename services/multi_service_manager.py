"""
Multi-Service Async Architecture Manager
Coordinates between Groq, Gemini, and Vertex AI services with intelligent routing
"""

import asyncio
import os
import time
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from asyncio_throttle import Throttler
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)

# Import Google Cloud libraries
try:
    import google.generativeai as genai
    from google.cloud import aiplatform
    from google.api_core import exceptions as google_exceptions
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logger.error("Google AI libraries not available")

# Import Groq for primary service
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq library not available")


class ServicePriority(Enum):
    """Service priority levels for intelligent routing"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FALLBACK = 4


class ServiceStatus(Enum):
    """Service status tracking"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"


@dataclass
class ServiceConfig:
    """Configuration for each service"""
    name: str
    priority: ServicePriority
    enabled: bool
    api_keys: List[str]
    current_key_index: int = 0
    max_requests_per_minute: int = 60
    max_tokens_per_request: int = 4000
    timeout_seconds: int = 30
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_time: int = 300  # 5 minutes


@dataclass
class ServiceMetrics:
    """Metrics tracking for each service"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    consecutive_failures: int = 0
    status: ServiceStatus = ServiceStatus.HEALTHY
    quota_reset_time: Optional[datetime] = None


@dataclass
class RequestContext:
    """Context for API requests"""
    request_id: str
    prompt: str
    request_type: str  # 'chat', 'embedding', 'analysis'
    priority: int = 1  # 1=high, 2=medium, 3=low
    max_tokens: int = 2000
    temperature: float = 0.4
    timeout: int = 30
    retry_count: int = 0


@dataclass
class ServiceResponse:
    """Standardized response from services"""
    success: bool
    content: str
    service_name: str
    response_time: float
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class CircuitBreaker:
    """Circuit breaker pattern for service resilience"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call_allowed(self) -> bool:
        """Check if calls are allowed through the circuit breaker"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class MultiServiceManager:
    """
    Manages multiple AI services with intelligent routing, load balancing,
    and comprehensive error handling
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.metrics: Dict[str, ServiceMetrics] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.throttlers: Dict[str, Throttler] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize services
        self._initialize_services()
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = datetime.now()
        
        logger.info("MultiServiceManager initialized with intelligent routing")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)
    
    def _initialize_services(self):
        """Initialize all available services with configuration"""
        
        # Groq Service (Primary - fastest response times)
        groq_keys = self._get_api_keys('GROQ_API_KEY')
        if groq_keys and GROQ_AVAILABLE:
            self.services['groq'] = ServiceConfig(
                name='groq',
                priority=ServicePriority.PRIMARY,
                enabled=True,
                api_keys=groq_keys,
                max_requests_per_minute=100,
                max_tokens_per_request=4000,
                timeout_seconds=15,
                retry_attempts=2
            )
            self.metrics['groq'] = ServiceMetrics()
            self.circuit_breakers['groq'] = CircuitBreaker(failure_threshold=3, reset_timeout=180)
            self.throttlers['groq'] = Throttler(rate_limit=100, period=60)
            
            # Initialize Groq client
            try:
                self.groq_client = Groq(api_key=groq_keys[0])
                logger.info(f"Groq service initialized with {len(groq_keys)} API keys")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.services['groq'].enabled = False
        
        # Gemini Service (Secondary - comprehensive but slower)
        gemini_keys = self._get_api_keys('GEMINI_API_KEY')
        if gemini_keys and GOOGLE_AI_AVAILABLE:
            self.services['gemini'] = ServiceConfig(
                name='gemini',
                priority=ServicePriority.SECONDARY,
                enabled=True,
                api_keys=gemini_keys,
                max_requests_per_minute=60,
                max_tokens_per_request=3000,
                timeout_seconds=30,
                retry_attempts=3
            )
            self.metrics['gemini'] = ServiceMetrics()
            self.circuit_breakers['gemini'] = CircuitBreaker(failure_threshold=5, reset_timeout=300)
            self.throttlers['gemini'] = Throttler(rate_limit=60, period=60)
            
            # Initialize Gemini client
            try:
                genai.configure(api_key=gemini_keys[0])
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info(f"Gemini service initialized with {len(gemini_keys)} API keys")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.services['gemini'].enabled = False
        
        # Vertex AI Service (Tertiary - specialized tasks and fallback)
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if project_id and GOOGLE_AI_AVAILABLE:
            self.services['vertex'] = ServiceConfig(
                name='vertex',
                priority=ServicePriority.TERTIARY,
                enabled=True,
                api_keys=[project_id],  # Use project ID as key
                max_requests_per_minute=30,
                max_tokens_per_request=2000,
                timeout_seconds=45,
                retry_attempts=2
            )
            self.metrics['vertex'] = ServiceMetrics()
            self.circuit_breakers['vertex'] = CircuitBreaker(failure_threshold=3, reset_timeout=600)
            self.throttlers['vertex'] = Throttler(rate_limit=30, period=60)
            
            # Initialize Vertex AI
            try:
                aiplatform.init(project=project_id, location=location)
                self.vertex_project = project_id
                self.vertex_location = location
                logger.info(f"Vertex AI service initialized for project {project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                self.services['vertex'].enabled = False
        
        # Log service availability
        enabled_services = [name for name, config in self.services.items() if config.enabled]
        logger.info(f"Enabled services: {enabled_services}")
        
        if not enabled_services:
            logger.warning("No AI services available - system will operate in fallback mode")
    
    def _get_api_keys(self, env_var: str) -> List[str]:
        """Get API keys from environment variables (supports multiple keys)"""
        keys = []
        
        # Primary key
        primary_key = os.getenv(env_var)
        if primary_key:
            keys.append(primary_key)
        
        # Additional keys (GROQ_API_KEY_2, GROQ_API_KEY_3, etc.)
        for i in range(2, 6):  # Support up to 5 keys per service
            additional_key = os.getenv(f"{env_var}_{i}")
            if additional_key:
                keys.append(additional_key)
        
        return keys
    
    async def process_request(self, context: RequestContext) -> ServiceResponse:
        """
        Process request with intelligent service selection and fallback
        """
        start_time = time.time()
        
        # Health check if needed
        await self._periodic_health_check()
        
        # Select best service for request
        selected_services = self._select_services_for_request(context)
        
        if not selected_services:
            return ServiceResponse(
                success=False,
                content="",
                service_name="none",
                response_time=time.time() - start_time,
                error="No available services"
            )
        
        # Try services in priority order
        last_error = None
        
        for service_name in selected_services:
            if not self._is_service_available(service_name):
                continue
            
            try:
                # Apply throttling
                async with self.throttlers[service_name]:
                    response = await self._call_service(service_name, context)
                    
                    if response.success:
                        # Record success metrics
                        self._record_success(service_name, response.response_time)
                        return response
                    else:
                        last_error = response.error
                        self._record_failure(service_name, response.error)
                        
            except Exception as e:
                last_error = str(e)
                self._record_failure(service_name, str(e))
                logger.warning(f"Service {service_name} failed: {e}")
        
        # All services failed
        return ServiceResponse(
            success=False,
            content="",
            service_name="all_failed",
            response_time=time.time() - start_time,
            error=f"All services failed. Last error: {last_error}"
        )
    
    def _select_services_for_request(self, context: RequestContext) -> List[str]:
        """Select services based on request type, priority, and availability"""
        available_services = []
        
        # Get services sorted by priority and health
        services_by_priority = sorted(
            [(name, config) for name, config in self.services.items() if config.enabled],
            key=lambda x: (x[1].priority.value, self.metrics[x[0]].consecutive_failures)
        )
        
        for service_name, config in services_by_priority:
            if self._is_service_available(service_name):
                available_services.append(service_name)
        
        # For high priority requests, prefer faster services
        if context.priority == 1:
            # Prioritize Groq for speed
            if 'groq' in available_services:
                available_services = ['groq'] + [s for s in available_services if s != 'groq']
        
        # For embedding requests, prefer Vertex AI
        if context.request_type == 'embedding':
            if 'vertex' in available_services:
                available_services = ['vertex'] + [s for s in available_services if s != 'vertex']
        
        return available_services
    
    def _is_service_available(self, service_name: str) -> bool:
        """Check if service is available for requests"""
        if service_name not in self.services:
            return False
        
        config = self.services[service_name]
        metrics = self.metrics[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        # Check if service is enabled
        if not config.enabled:
            return False
        
        # Check circuit breaker
        if not circuit_breaker.call_allowed():
            return False
        
        # Check quota limits
        if metrics.quota_reset_time and datetime.now() < metrics.quota_reset_time:
            return False
        
        # Check service status
        if metrics.status == ServiceStatus.UNAVAILABLE:
            return False
        
        return True
    
    async def _call_service(self, service_name: str, context: RequestContext) -> ServiceResponse:
        """Call specific service with request context"""
        start_time = time.time()
        
        try:
            if service_name == 'groq':
                return await self._call_groq_service(context)
            elif service_name == 'gemini':
                return await self._call_gemini_service(context)
            elif service_name == 'vertex':
                return await self._call_vertex_service(context)
            else:
                raise ValueError(f"Unknown service: {service_name}")
                
        except Exception as e:
            return ServiceResponse(
                success=False,
                content="",
                service_name=service_name,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _call_groq_service(self, context: RequestContext) -> ServiceResponse:
        """Call Groq API service"""
        start_time = time.time()
        
        try:
            # Rotate API key if multiple available
            config = self.services['groq']
            current_key = config.api_keys[config.current_key_index]
            
            # Update client with current key
            self.groq_client.api_key = current_key
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": "You are LegalSaathi, an AI legal document advisor. Provide specific, actionable guidance with concrete examples and exact negotiation language."
                },
                {
                    "role": "user",
                    "content": context.prompt
                }
            ]
            
            # Make API call
            response = self.groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=context.temperature,
                max_tokens=min(context.max_tokens, config.max_tokens_per_request),
                top_p=0.95,
                stream=False
            )
            
            content = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return ServiceResponse(
                success=True,
                content=content,
                service_name='groq',
                response_time=time.time() - start_time,
                tokens_used=tokens_used,
                metadata={'model': 'llama-3.1-8b-instant', 'key_index': config.current_key_index}
            )
            
        except Exception as e:
            # Try next API key if available
            await self._rotate_api_key('groq')
            raise e
    
    async def _call_gemini_service(self, context: RequestContext) -> ServiceResponse:
        """Call Gemini API service"""
        start_time = time.time()
        
        try:
            # Rotate API key if multiple available
            config = self.services['gemini']
            current_key = config.api_keys[config.current_key_index]
            
            # Update Gemini configuration
            genai.configure(api_key=current_key)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=context.temperature,
                max_output_tokens=min(context.max_tokens, config.max_tokens_per_request),
                top_p=0.95,
                top_k=50,
                candidate_count=1
            )
            
            # System instruction
            system_instruction = "You are LegalSaathi, an AI legal document advisor. Provide specific, actionable guidance with concrete examples, exact negotiation language, and step-by-step actions."
            
            # Safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
            
            # Create model and generate content
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                generation_config=generation_config,
                system_instruction=system_instruction,
                safety_settings=safety_settings
            )
            
            response = model.generate_content(context.prompt)
            
            # Extract content
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    raise ValueError("Content filtered by safety system")
                
                if hasattr(candidate, 'content') and candidate.content.parts:
                    content = candidate.content.parts[0].text.strip()
                elif hasattr(response, 'text') and response.text:
                    content = response.text.strip()
                else:
                    raise ValueError("No valid content in response")
            else:
                raise ValueError("No candidates in response")
            
            return ServiceResponse(
                success=True,
                content=content,
                service_name='gemini',
                response_time=time.time() - start_time,
                tokens_used=len(context.prompt) + len(content),  # Approximate
                metadata={'model': 'gemini-2.0-flash', 'key_index': config.current_key_index}
            )
            
        except Exception as e:
            # Try next API key if available
            await self._rotate_api_key('gemini')
            raise e
    
    async def _call_vertex_service(self, context: RequestContext) -> ServiceResponse:
        """Call Vertex AI service"""
        start_time = time.time()
        
        try:
            # For now, Vertex AI is primarily used for embeddings
            # For chat completions, we'll use a simple implementation
            
            if context.request_type == 'embedding':
                from vertexai.language_models import TextEmbeddingModel
                
                model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                embeddings = model.get_embeddings([context.prompt[:4000]])
                
                if embeddings and len(embeddings) > 0:
                    embedding_values = embeddings[0].values
                    content = json.dumps(embedding_values)
                else:
                    raise ValueError("No embeddings returned")
            
            else:
                # For chat, use a basic implementation or fallback
                content = "Vertex AI chat completion not fully implemented yet. Please use Groq or Gemini services."
            
            return ServiceResponse(
                success=True,
                content=content,
                service_name='vertex',
                response_time=time.time() - start_time,
                tokens_used=len(context.prompt),
                metadata={'project': self.vertex_project, 'location': self.vertex_location}
            )
            
        except Exception as e:
            raise e
    
    async def _rotate_api_key(self, service_name: str):
        """Rotate to next available API key for service"""
        if service_name not in self.services:
            return
        
        config = self.services[service_name]
        if len(config.api_keys) > 1:
            config.current_key_index = (config.current_key_index + 1) % len(config.api_keys)
            logger.info(f"Rotated {service_name} to API key index {config.current_key_index}")
    
    def _record_success(self, service_name: str, response_time: float):
        """Record successful request metrics"""
        metrics = self.metrics[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        metrics.total_requests += 1
        metrics.successful_requests += 1
        metrics.consecutive_failures = 0
        metrics.last_request_time = datetime.now()
        metrics.status = ServiceStatus.HEALTHY
        
        # Update average response time
        if metrics.average_response_time == 0:
            metrics.average_response_time = response_time
        else:
            metrics.average_response_time = (metrics.average_response_time + response_time) / 2
        
        # Record circuit breaker success
        circuit_breaker.record_success()
        
        logger.debug(f"Recorded success for {service_name}: {response_time:.3f}s")
    
    def _record_failure(self, service_name: str, error: str):
        """Record failed request metrics"""
        metrics = self.metrics[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        metrics.total_requests += 1
        metrics.failed_requests += 1
        metrics.consecutive_failures += 1
        metrics.last_request_time = datetime.now()
        
        # Update status based on error type
        if 'quota' in error.lower() or 'rate limit' in error.lower():
            metrics.status = ServiceStatus.QUOTA_EXCEEDED
            metrics.quota_reset_time = datetime.now() + timedelta(minutes=15)
        elif metrics.consecutive_failures >= 3:
            metrics.status = ServiceStatus.DEGRADED
        
        # Record circuit breaker failure
        circuit_breaker.record_failure()
        
        logger.warning(f"Recorded failure for {service_name}: {error}")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks on services"""
        now = datetime.now()
        
        if (now - self.last_health_check).seconds < self.health_check_interval:
            return
        
        self.last_health_check = now
        
        # Reset quota exceeded status if enough time has passed
        for service_name, metrics in self.metrics.items():
            if (metrics.status == ServiceStatus.QUOTA_EXCEEDED and 
                metrics.quota_reset_time and 
                now > metrics.quota_reset_time):
                metrics.status = ServiceStatus.HEALTHY
                metrics.quota_reset_time = None
                logger.info(f"Reset quota status for {service_name}")
        
        logger.debug("Completed periodic health check")
    
    async def get_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive health status of all services"""
        health_status = {}
        
        for service_name, config in self.services.items():
            metrics = self.metrics[service_name]
            circuit_breaker = self.circuit_breakers[service_name]
            
            success_rate = 0
            if metrics.total_requests > 0:
                success_rate = (metrics.successful_requests / metrics.total_requests) * 100
            
            health_status[service_name] = {
                'enabled': config.enabled,
                'status': metrics.status.value,
                'priority': config.priority.value,
                'api_keys_count': len(config.api_keys),
                'current_key_index': config.current_key_index,
                'total_requests': metrics.total_requests,
                'success_rate': round(success_rate, 2),
                'average_response_time': round(metrics.average_response_time, 3),
                'consecutive_failures': metrics.consecutive_failures,
                'circuit_breaker_state': circuit_breaker.state,
                'last_request_time': metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                'quota_reset_time': metrics.quota_reset_time.isoformat() if metrics.quota_reset_time else None
            }
        
        return health_status
    
    async def process_batch_requests(self, contexts: List[RequestContext]) -> List[ServiceResponse]:
        """Process multiple requests concurrently with load balancing"""
        if not contexts:
            return []
        
        # Group requests by priority
        high_priority = [ctx for ctx in contexts if ctx.priority == 1]
        medium_priority = [ctx for ctx in contexts if ctx.priority == 2]
        low_priority = [ctx for ctx in contexts if ctx.priority == 3]
        
        # Process high priority first, then others concurrently
        results = []
        
        if high_priority:
            high_results = await asyncio.gather(
                *[self.process_request(ctx) for ctx in high_priority],
                return_exceptions=True
            )
            results.extend(high_results)
        
        if medium_priority or low_priority:
            remaining_requests = medium_priority + low_priority
            remaining_results = await asyncio.gather(
                *[self.process_request(ctx) for ctx in remaining_requests],
                return_exceptions=True
            )
            results.extend(remaining_results)
        
        # Convert exceptions to error responses
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ServiceResponse(
                    success=False,
                    content="",
                    service_name="batch_error",
                    response_time=0,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results


# Global instance for easy access
multi_service_manager = None


async def get_multi_service_manager() -> MultiServiceManager:
    """Get or create global multi-service manager instance"""
    global multi_service_manager
    
    if multi_service_manager is None:
        multi_service_manager = MultiServiceManager()
    
    return multi_service_manager


async def cleanup_multi_service_manager():
    """Cleanup global multi-service manager"""
    global multi_service_manager
    
    if multi_service_manager:
        if hasattr(multi_service_manager, 'session') and multi_service_manager.session:
            await multi_service_manager.session.close()
        multi_service_manager = None