"""
Firebase Authentication Middleware for FastAPI
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from services.firebase_service import FirebaseService
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Firebase Authentication Middleware with JWT token validation,
    user extraction, and session management
    """
    
    def __init__(self, app, firebase_service: Optional[FirebaseService] = None):
        super().__init__(app)
        try:
            self.firebase_service = firebase_service or FirebaseService()
            self.firebase_available = getattr(self.firebase_service, '_firebase_available', False)
        except Exception as e:
            logger.warning(f"Firebase service initialization failed: {e}")
            self.firebase_service = None
            self.firebase_available = False
        
        # Define protected routes that require authentication
        self.protected_routes = [
            # '/api/export',  # Temporarily disabled for testing
            '/api/user',
            '/api/auth/user-info',
            '/api/auth/refresh-token'
        ]
        
        # Define public routes that don't require authentication
        self.public_routes = [
            '/api/health',
            '/api/auth/verify-token',
            '/api/auth/register',
            '/api/analyze',
            '/api/analyze/file',
            '/api/analyze/async',
            '/api/translate',
            '/api/speech',
            '/api/ai/clarify',
            '/api/compare',
            '/docs',
            '/redoc',
            '/openapi.json'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with Firebase authentication
        """
        # Extract and validate Firebase token (for both public and protected routes)
        try:
            token = self._extract_token(request)
            
            # Initialize request state
            request.state.user = None
            request.state.is_authenticated = False
            request.state.user_id = None
            
            if token and self.firebase_available and self.firebase_service:
                # Try to verify token if provided
                verification_result = await self.firebase_service.verify_token(token)
                
                if verification_result['success']:
                    # Add user info to request state
                    user_info = verification_result['user']
                    request.state.user = user_info
                    request.state.is_authenticated = True
                    request.state.user_id = user_info['uid']
                    
                    logger.info(f"User authenticated: {user_info['uid']} - {user_info['email']}")
                else:
                    logger.warning(f"Token verification failed: {verification_result['error']}")
            
            # Check if this is a protected route that requires authentication
            if self._is_protected_route(request.url.path):
                if not request.state.is_authenticated:
                    if not self.firebase_available:
                        # If Firebase is not available, allow access but log warning
                        logger.warning("Firebase not configured - allowing anonymous access to protected route")
                    else:
                        return self._create_auth_error_response("Authentication required")
            
            # Process request
            response = await call_next(request)
            
            # Add authentication headers to response
            if request.state.is_authenticated:
                response.headers["X-User-ID"] = request.state.user_id
                response.headers["X-Authenticated"] = "true"
            else:
                response.headers["X-Authenticated"] = "false"
            
            return response
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            # For public routes, continue even if auth fails
            if not self._is_protected_route(request.url.path):
                request.state.user = None
                request.state.is_authenticated = False
                request.state.user_id = None
                return await call_next(request)
            else:
                return self._create_auth_error_response("Authentication failed")
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract Firebase token from request headers
        
        Args:
            request: FastAPI request object
            
        Returns:
            Firebase ID token or None
        """
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        # Check X-Firebase-Token header
        firebase_token = request.headers.get("X-Firebase-Token")
        if firebase_token:
            return firebase_token
        
        return None
    
    def _is_protected_route(self, path: str) -> bool:
        """
        Check if route requires authentication
        
        Args:
            path: Request path
            
        Returns:
            True if route is protected
        """
        return any(path.startswith(route) for route in self.protected_routes)
    
    def _is_public_route(self, path: str) -> bool:
        """
        Check if route is public (no authentication required)
        
        Args:
            path: Request path
            
        Returns:
            True if route is public
        """
        # Static files and root
        if path in ['/', '/favicon.ico'] or path.startswith('/static'):
            return True
        
        # Explicit public routes
        return any(path.startswith(route) for route in self.public_routes)
    
    def _create_auth_error_response(self, message: str) -> JSONResponse:
        """
        Create standardized authentication error response
        
        Args:
            message: Error message
            
        Returns:
            JSONResponse with error details
        """
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Error",
                "message": message,
                "error_code": "AUTH_001",
                "timestamp": datetime.now().isoformat()
            }
        )


class UserBasedRateLimiter:
    """
    User-based rate limiting that applies different limits per authenticated user ID vs anonymous users
    """
    
    def __init__(self):
        self.user_limits = {}
        self.anonymous_limits = {}
        
        # Define rate limits
        self.authenticated_user_limits = {
            'analyze_document': {'requests': 20, 'window': 3600},  # 20 per hour
            'speech_to_text': {'requests': 10, 'window': 3600},    # 10 per hour
            'text_to_speech': {'requests': 20, 'window': 3600},    # 20 per hour
            'translation': {'requests': 100, 'window': 3600},      # 100 per hour
            'email_notification': {'requests': 5, 'window': 3600}  # 5 per hour
        }
        
        self.anonymous_user_limits = {
            'analyze_document': {'requests': 5, 'window': 3600},   # 5 per hour
            'speech_to_text': {'requests': 2, 'window': 3600},     # 2 per hour
            'text_to_speech': {'requests': 5, 'window': 3600},     # 5 per hour
            'translation': {'requests': 20, 'window': 3600},       # 20 per hour
            'email_notification': {'requests': 0, 'window': 3600}  # Not allowed
        }
    
    def check_rate_limit(self, user_id: Optional[str], service: str, request: Request) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            user_id: User ID (None for anonymous)
            service: Service name
            request: FastAPI request object
            
        Returns:
            True if within limits, False otherwise
        """
        try:
            current_time = datetime.now().timestamp()
            
            # Determine limits based on authentication status
            if user_id:
                limits = self.authenticated_user_limits.get(service)
                key = f"user:{user_id}:{service}"
                storage = self.user_limits
            else:
                limits = self.anonymous_user_limits.get(service)
                # Use IP address for anonymous users
                ip_address = request.client.host if request.client else "unknown"
                key = f"anonymous:{ip_address}:{service}"
                storage = self.anonymous_limits
            
            if not limits:
                return True  # No limits defined for this service
            
            # Initialize or clean up old entries
            if key not in storage:
                storage[key] = []
            
            # Remove old requests outside the time window
            window_start = current_time - limits['window']
            storage[key] = [req_time for req_time in storage[key] if req_time > window_start]
            
            # Check if within limits
            if len(storage[key]) >= limits['requests']:
                logger.warning(f"Rate limit exceeded for {key}")
                return False
            
            # Add current request
            storage[key].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow request on error to avoid blocking legitimate users
    
    def get_rate_limit_info(self, user_id: Optional[str], service: str) -> Dict[str, Any]:
        """
        Get rate limit information for a user/service combination
        
        Args:
            user_id: User ID (None for anonymous)
            service: Service name
            
        Returns:
            Dict with rate limit information
        """
        try:
            current_time = datetime.now().timestamp()
            
            # Determine limits and key
            if user_id:
                limits = self.authenticated_user_limits.get(service, {})
                key = f"user:{user_id}:{service}"
                storage = self.user_limits
            else:
                limits = self.anonymous_user_limits.get(service, {})
                key = f"anonymous:*:{service}"  # Generic key for info
                storage = self.anonymous_limits
            
            if not limits:
                return {'limit': None, 'remaining': None, 'reset_time': None}
            
            # Get current usage
            requests = storage.get(key, [])
            window_start = current_time - limits['window']
            current_requests = [req_time for req_time in requests if req_time > window_start]
            
            remaining = max(0, limits['requests'] - len(current_requests))
            reset_time = current_time + limits['window'] if current_requests else None
            
            return {
                'limit': limits['requests'],
                'remaining': remaining,
                'reset_time': reset_time,
                'window': limits['window']
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {'limit': None, 'remaining': None, 'reset_time': None}