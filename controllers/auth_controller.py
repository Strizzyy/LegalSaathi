"""
Authentication Controller for Firebase integration
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException, Request
from models.auth_models import (
    FirebaseTokenRequest, FirebaseTokenResponse,
    UserRegistrationRequest, UserRegistrationResponse,
    UserInfoResponse, RefreshTokenRequest, RefreshTokenResponse,
    AuthErrorResponse
)
from services.firebase_service import FirebaseService
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthController:
    """
    Authentication controller with verify_token, get_user_info, 
    refresh_token, and user registration methods
    """
    
    def __init__(self):
        self.firebase_service = FirebaseService()
    
    async def verify_token(self, token_request: FirebaseTokenRequest) -> FirebaseTokenResponse:
        """
        Verify Firebase ID token
        
        Args:
            token_request: Token verification request
            
        Returns:
            Token verification response
        """
        try:
            result = await self.firebase_service.verify_token(token_request.token)
            
            if result['success']:
                return FirebaseTokenResponse(
                    success=True,
                    user=result['user']
                )
            else:
                return FirebaseTokenResponse(
                    success=False,
                    error=result['error']
                )
                
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return FirebaseTokenResponse(
                success=False,
                error="Token verification failed"
            )
    
    async def get_user_info(self, request: Request) -> UserInfoResponse:
        """
        Get user information from authenticated request
        
        Args:
            request: FastAPI request with authenticated user
            
        Returns:
            User information response
        """
        try:
            # Check if user is authenticated
            if not hasattr(request.state, 'user') or not request.state.user:
                return UserInfoResponse(
                    success=False,
                    error="User not authenticated"
                )
            
            user_info = request.state.user
            uid = user_info['uid']
            
            # Get fresh user information from Firebase
            result = await self.firebase_service.get_user_info(uid)
            
            if result['success']:
                return UserInfoResponse(
                    success=True,
                    user=result['user']
                )
            else:
                return UserInfoResponse(
                    success=False,
                    error=result['error']
                )
                
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return UserInfoResponse(
                success=False,
                error="Failed to retrieve user information"
            )
    
    async def refresh_token(self, refresh_request: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh Firebase token (Note: This is typically handled client-side)
        
        Args:
            refresh_request: Token refresh request
            
        Returns:
            Token refresh response
        """
        try:
            # Note: Firebase token refresh is typically handled on the client side
            # This endpoint is provided for completeness but may not be used
            logger.info("Token refresh requested - typically handled client-side")
            
            return RefreshTokenResponse(
                success=False,
                error="Token refresh should be handled client-side with Firebase SDK"
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return RefreshTokenResponse(
                success=False,
                error="Token refresh failed"
            )
    
    async def register_user(self, registration_request: UserRegistrationRequest) -> UserRegistrationResponse:
        """
        Register a new user account
        
        Args:
            registration_request: User registration request
            
        Returns:
            User registration response
        """
        try:
            result = await self.firebase_service.create_user(
                email=registration_request.email,
                password=registration_request.password,
                display_name=registration_request.display_name
            )
            
            if result['success']:
                logger.info(f"User registered successfully: {result['user']['email']}")
                return UserRegistrationResponse(
                    success=True,
                    user=result['user']
                )
            else:
                return UserRegistrationResponse(
                    success=False,
                    error=result['error']
                )
                
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return UserRegistrationResponse(
                success=False,
                error="User registration failed"
            )
    
    async def get_current_user(self, request: Request) -> Dict[str, Any]:
        """
        Get current authenticated user information
        
        Args:
            request: FastAPI request with authenticated user
            
        Returns:
            Current user information
        """
        try:
            if not hasattr(request.state, 'user') or not request.state.user:
                raise HTTPException(status_code=401, detail="User not authenticated")
            
            return {
                'success': True,
                'user': request.state.user,
                'is_authenticated': getattr(request.state, 'is_authenticated', False)
            }
            
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user information")
    
    async def update_user_profile(self, request: Request, update_data: Dict[str, Any]) -> UserInfoResponse:
        """
        Update user profile information
        
        Args:
            request: FastAPI request with authenticated user
            update_data: Data to update
            
        Returns:
            Updated user information response
        """
        try:
            if not hasattr(request.state, 'user') or not request.state.user:
                return UserInfoResponse(
                    success=False,
                    error="User not authenticated"
                )
            
            uid = request.state.user['uid']
            
            # Filter allowed update fields
            allowed_fields = ['display_name', 'email']
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            if not filtered_data:
                return UserInfoResponse(
                    success=False,
                    error="No valid fields to update"
                )
            
            result = await self.firebase_service.update_user(uid, **filtered_data)
            
            if result['success']:
                return UserInfoResponse(
                    success=True,
                    user=result['user']
                )
            else:
                return UserInfoResponse(
                    success=False,
                    error=result['error']
                )
                
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return UserInfoResponse(
                success=False,
                error="Failed to update user profile"
            )
    
    async def delete_user_account(self, request: Request) -> Dict[str, Any]:
        """
        Delete user account
        
        Args:
            request: FastAPI request with authenticated user
            
        Returns:
            Deletion result
        """
        try:
            if not hasattr(request.state, 'user') or not request.state.user:
                raise HTTPException(status_code=401, detail="User not authenticated")
            
            uid = request.state.user['uid']
            
            result = await self.firebase_service.delete_user(uid)
            
            if result['success']:
                logger.info(f"User account deleted: {uid}")
                return {'success': True, 'message': 'Account deleted successfully'}
            else:
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            logger.error(f"Failed to delete user account: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete account")
    
    def create_auth_error_response(self, message: str, error_code: str = "AUTH_ERROR") -> AuthErrorResponse:
        """
        Create standardized authentication error response
        
        Args:
            message: Error message
            error_code: Error code
            
        Returns:
            Standardized error response
        """
        return AuthErrorResponse(
            error="Authentication Error",
            message=message,
            error_code=error_code,
            timestamp=datetime.now()
        )