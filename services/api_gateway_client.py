"""
Google Cloud API Gateway Client
Handles centralized request routing, rate limiting, and monitoring
"""

import asyncio
import os
import time
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import aiohttp
try:
    from google.auth import default
    from google.auth.transport.requests import Request
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class APIGatewayConfig:
    """Configuration for API Gateway"""
    gateway_url: str
    project_id: str
    location: str
    gateway_id: str
    api_id: str
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class GatewayRequest:
    """Request structure for API Gateway"""
    endpoint: str
    method: str = "POST"
    payload: Dict[str, Any] = None
    headers: Dict[str, str] = None
    timeout: int = 60
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class GatewayResponse:
    """Response structure from API Gateway"""
    success: bool
    status_code: int
    content: str
    headers: Dict[str, str]
    response_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class APIGatewayClient:
    """
    Client for Google Cloud API Gateway integration
    Provides centralized request routing, authentication, and monitoring
    """
    
    def __init__(self, config: Optional[APIGatewayConfig] = None):
        self.config = config or self._load_default_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.credentials = None
        self.auth_session = None
        
        # Request tracking
        self.request_count = 0
        self.total_response_time = 0.0
        self.error_count = 0
        self.last_request_time = None
        
        # Rate limiting
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_window = 1000
        self.request_timestamps = []
        
        # Initialize authentication
        self._initialize_auth()
        
        logger.info(f"API Gateway client initialized for {self.config.gateway_url}")
    
    def _load_default_config(self) -> APIGatewayConfig:
        """Load default configuration from environment variables"""
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        gateway_id = os.getenv('API_GATEWAY_ID', 'legalsaathi-gateway')
        api_id = os.getenv('API_GATEWAY_API_ID', 'legalsaathi-api')
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT_ID environment variable is required")
        
        # Construct gateway URL
        gateway_url = f"https://{gateway_id}-{api_id}-{location}.gateway.dev"
        
        return APIGatewayConfig(
            gateway_url=gateway_url,
            project_id=project_id,
            location=location,
            gateway_id=gateway_id,
            api_id=api_id
        )
    
    def _initialize_auth(self):
        """Initialize Google Cloud authentication"""
        if not GOOGLE_AUTH_AVAILABLE:
            logger.warning("Google Auth libraries not available")
            self.credentials = None
            return
            
        try:
            self.credentials, project = default()
            logger.info(f"Initialized Google Cloud auth for project: {project}")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud auth: {e}")
            self.credentials = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Create authenticated session (simplified for now)
        self.auth_session = None
        
        # Create regular session for non-authenticated requests
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.auth_session:
            await self.auth_session.close()
    
    async def send_request(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send request through API Gateway with authentication and monitoring
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{time.time()}{request.endpoint}".encode()).hexdigest()[:8]
        
        try:
            # Check rate limits
            if not self._check_rate_limit():
                return GatewayResponse(
                    success=False,
                    status_code=429,
                    content="",
                    headers={},
                    response_time=time.time() - start_time,
                    error="Rate limit exceeded"
                )
            
            # Prepare request
            url = f"{self.config.gateway_url}/{request.endpoint.lstrip('/')}"
            headers = self._prepare_headers(request.headers or {})
            
            logger.debug(f"[{request_id}] Sending {request.method} request to {url}")
            
            # Choose session based on authentication needs
            session = self.auth_session if self.credentials else self.session
            
            if not session:
                raise RuntimeError("No session available")
            
            # Make request with retries
            response = await self._make_request_with_retries(
                session, request, url, headers, request_id
            )
            
            # Update metrics
            self._update_metrics(True, time.time() - start_time)
            
            return response
            
        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"[{request_id}] API Gateway request failed: {e}")
            
            return GatewayResponse(
                success=False,
                status_code=500,
                content="",
                headers={},
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _make_request_with_retries(
        self, 
        session: aiohttp.ClientSession, 
        request: GatewayRequest, 
        url: str, 
        headers: Dict[str, str],
        request_id: str
    ) -> GatewayResponse:
        """Make request with retry logic"""
        
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                
                async with session.request(
                    method=request.method,
                    url=url,
                    json=request.payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as response:
                    
                    content = await response.text()
                    response_time = time.time() - start_time
                    
                    logger.debug(f"[{request_id}] Response: {response.status} in {response_time:.3f}s")
                    
                    # Check if request was successful
                    if 200 <= response.status < 300:
                        return GatewayResponse(
                            success=True,
                            status_code=response.status,
                            content=content,
                            headers=dict(response.headers),
                            response_time=response_time,
                            metadata={
                                'attempt': attempt + 1,
                                'request_id': request_id
                            }
                        )
                    
                    # Handle specific error codes
                    elif response.status == 429:  # Rate limited
                        if attempt < self.config.max_retries:
                            delay = self.config.retry_delay * (2 ** attempt)
                            logger.warning(f"[{request_id}] Rate limited, retrying in {delay}s")
                            await asyncio.sleep(delay)
                            continue
                    
                    elif 500 <= response.status < 600:  # Server error
                        if attempt < self.config.max_retries:
                            delay = self.config.retry_delay * (2 ** attempt)
                            logger.warning(f"[{request_id}] Server error {response.status}, retrying in {delay}s")
                            await asyncio.sleep(delay)
                            continue
                    
                    # Non-retryable error
                    return GatewayResponse(
                        success=False,
                        status_code=response.status,
                        content=content,
                        headers=dict(response.headers),
                        response_time=response_time,
                        error=f"HTTP {response.status}: {content[:200]}"
                    )
                    
            except asyncio.TimeoutError as e:
                last_error = f"Request timeout after {request.timeout}s"
                if attempt < self.config.max_retries:
                    logger.warning(f"[{request_id}] Timeout, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                    
            except Exception as e:
                last_error = str(e)
                if attempt < self.config.max_retries:
                    logger.warning(f"[{request_id}] Request failed, retrying: {e}")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
        
        # All retries exhausted
        return GatewayResponse(
            success=False,
            status_code=500,
            content="",
            headers={},
            response_time=0,
            error=f"Request failed after {self.config.max_retries + 1} attempts. Last error: {last_error}"
        )
    
    def _prepare_headers(self, custom_headers: Dict[str, str]) -> Dict[str, str]:
        """Prepare headers for API Gateway request"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'LegalSaathi-APIGateway/1.0',
            'X-Request-ID': hashlib.md5(f"{time.time()}".encode()).hexdigest()[:16],
            'X-Client-Version': '1.0.0'
        }
        
        # Add custom headers
        headers.update(custom_headers)
        
        # Add authentication header if available
        if self.credentials and GOOGLE_AUTH_AVAILABLE:
            try:
                # Refresh credentials if needed
                if not self.credentials.valid:
                    self.credentials.refresh(Request())
                
                headers['Authorization'] = f'Bearer {self.credentials.token}'
            except Exception as e:
                logger.warning(f"Failed to add auth header: {e}")
        
        return headers
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        
        # Remove old timestamps outside the window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < self.rate_limit_window
        ]
        
        # Check if we're within limits
        if len(self.request_timestamps) >= self.max_requests_per_window:
            return False
        
        # Add current timestamp
        self.request_timestamps.append(now)
        return True
    
    def _update_metrics(self, success: bool, response_time: float):
        """Update request metrics"""
        self.request_count += 1
        self.total_response_time += response_time
        self.last_request_time = datetime.now()
        
        if not success:
            self.error_count += 1
        
        logger.debug(f"Updated metrics: {self.request_count} requests, "
                    f"{self.error_count} errors, "
                    f"{self.total_response_time/self.request_count:.3f}s avg")
    
    async def send_ai_request(self, service: str, prompt: str, **kwargs) -> GatewayResponse:
        """Send AI service request through API Gateway"""
        
        payload = {
            'service': service,
            'prompt': prompt,
            'parameters': kwargs
        }
        
        request = GatewayRequest(
            endpoint='ai/process',
            method='POST',
            payload=payload,
            timeout=kwargs.get('timeout', 60),
            priority=kwargs.get('priority', 1)
        )
        
        return await self.send_request(request)
    
    async def send_document_analysis_request(
        self, 
        document_content: str, 
        analysis_type: str = 'full',
        **kwargs
    ) -> GatewayResponse:
        """Send document analysis request through API Gateway"""
        
        payload = {
            'document_content': document_content,
            'analysis_type': analysis_type,
            'parameters': kwargs
        }
        
        request = GatewayRequest(
            endpoint='document/analyze',
            method='POST',
            payload=payload,
            timeout=kwargs.get('timeout', 120),  # Longer timeout for document analysis
            priority=kwargs.get('priority', 2)
        )
        
        return await self.send_request(request)
    
    async def send_batch_requests(self, requests: List[GatewayRequest]) -> List[GatewayResponse]:
        """Send multiple requests concurrently through API Gateway"""
        
        if not requests:
            return []
        
        # Group by priority
        high_priority = [req for req in requests if req.priority == 1]
        medium_priority = [req for req in requests if req.priority == 2]
        low_priority = [req for req in requests if req.priority == 3]
        
        results = []
        
        # Process high priority first
        if high_priority:
            high_results = await asyncio.gather(
                *[self.send_request(req) for req in high_priority],
                return_exceptions=True
            )
            results.extend(high_results)
        
        # Process medium and low priority concurrently
        if medium_priority or low_priority:
            remaining = medium_priority + low_priority
            remaining_results = await asyncio.gather(
                *[self.send_request(req) for req in remaining],
                return_exceptions=True
            )
            results.extend(remaining_results)
        
        # Convert exceptions to error responses
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(GatewayResponse(
                    success=False,
                    status_code=500,
                    content="",
                    headers={},
                    response_time=0,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        success_rate = 0
        avg_response_time = 0
        
        if self.request_count > 0:
            success_rate = ((self.request_count - self.error_count) / self.request_count) * 100
            avg_response_time = self.total_response_time / self.request_count
        
        return {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'success_rate': round(success_rate, 2),
            'average_response_time': round(avg_response_time, 3),
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'rate_limit_window': self.rate_limit_window,
            'max_requests_per_window': self.max_requests_per_window,
            'current_window_requests': len(self.request_timestamps),
            'gateway_url': self.config.gateway_url,
            'authenticated': self.credentials is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on API Gateway"""
        try:
            request = GatewayRequest(
                endpoint='health',
                method='GET',
                timeout=10
            )
            
            response = await self.send_request(request)
            
            return {
                'gateway_available': response.success,
                'status_code': response.status_code,
                'response_time': response.response_time,
                'error': response.error
            }
            
        except Exception as e:
            return {
                'gateway_available': False,
                'status_code': 500,
                'response_time': 0,
                'error': str(e)
            }


# Global instance for easy access
api_gateway_client = None


async def get_api_gateway_client() -> APIGatewayClient:
    """Get or create global API Gateway client instance"""
    global api_gateway_client
    
    if api_gateway_client is None:
        try:
            api_gateway_client = APIGatewayClient()
        except Exception as e:
            logger.warning(f"Failed to initialize API Gateway client: {e}")
            # Return a mock client that always fails gracefully
            api_gateway_client = MockAPIGatewayClient()
    
    return api_gateway_client


class MockAPIGatewayClient:
    """Mock API Gateway client for when configuration is not available"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def send_request(self, request: GatewayRequest) -> GatewayResponse:
        return GatewayResponse(
            success=False,
            status_code=503,
            content="",
            headers={},
            response_time=0,
            error="API Gateway not configured"
        )
    
    async def send_ai_request(self, service: str, prompt: str, **kwargs) -> GatewayResponse:
        return await self.send_request(GatewayRequest(endpoint=""))
    
    async def send_document_analysis_request(self, document_content: str, **kwargs) -> GatewayResponse:
        return await self.send_request(GatewayRequest(endpoint=""))
    
    async def send_batch_requests(self, requests: List[GatewayRequest]) -> List[GatewayResponse]:
        return [await self.send_request(req) for req in requests]
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            'total_requests': 0,
            'error_count': 0,
            'success_rate': 0,
            'average_response_time': 0,
            'gateway_available': False,
            'error': 'API Gateway not configured'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            'gateway_available': False,
            'status_code': 503,
            'response_time': 0,
            'error': 'API Gateway not configured'
        }


async def cleanup_api_gateway_client():
    """Cleanup global API Gateway client"""
    global api_gateway_client
    
    if api_gateway_client and hasattr(api_gateway_client, 'session'):
        if api_gateway_client.session:
            await api_gateway_client.session.close()
        if hasattr(api_gateway_client, 'auth_session') and api_gateway_client.auth_session:
            await api_gateway_client.auth_session.close()
    
    api_gateway_client = None