"""
Expert Authentication Controller for Human-in-the-Loop System
Handles expert authentication endpoints and role management
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Request, Depends
from datetime import datetime

from services.expert_auth_service import (
    expert_auth_service, ExpertAuthenticationError, ExpertAuthorizationError, ExpertRole
)
from models.auth_models import FirebaseTokenRequest, AuthErrorResponse

logger = logging.getLogger(__name__)


class ExpertAuthController:
    """
    Expert Authentication Controller with role-based access control.
    Handles expert login, role verification, and user management.
    """
    
    def __init__(self):
        self.auth_service = expert_auth_service
    
    async def authenticate_expert(self, token_request: FirebaseTokenRequest) -> Dict[str, Any]:
        """
        Authenticate expert using Firebase token with custom claims verification.
        
        Args:
            token_request: Firebase token request
            
        Returns:
            Expert authentication response
        """
        try:
            expert_info = await self.auth_service.authenticate_expert(token_request.token)
            
            if not expert_info:
                raise HTTPException(
                    status_code=401,
                    detail="Expert authentication failed"
                )
            
            logger.info(f"Expert authenticated: {expert_info['email']} ({expert_info['role']})")
            
            return {
                'success': True,
                'expert': expert_info,
                'message': 'Expert authentication successful'
            }
            
        except ExpertAuthenticationError as e:
            logger.warning(f"Expert authentication failed: {e}")
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Expert authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service error"
            )
    
    async def verify_expert_token(self, request: Request) -> Dict[str, Any]:
        """
        Verify expert token from request headers and return expert info.
        
        Args:
            request: FastAPI request with Authorization header
            
        Returns:
            Expert information if valid
        """
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Missing or invalid Authorization header"
                )
            
            token = auth_header.split(" ")[1]
            
            expert_info = await self.auth_service.authenticate_expert(token)
            
            if not expert_info:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid expert token"
                )
            
            return {
                'success': True,
                'expert': expert_info
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Token verification failed"
            )
    
    async def get_expert_profile(self, request: Request) -> Dict[str, Any]:
        """
        Get expert profile information from authenticated request.
        
        Args:
            request: Authenticated request
            
        Returns:
            Expert profile information
        """
        try:
            # Verify expert authentication
            verification_result = await self.verify_expert_token(request)
            expert_info = verification_result['expert']
            
            return {
                'success': True,
                'profile': {
                    'uid': expert_info['uid'],
                    'email': expert_info['email'],
                    'display_name': expert_info['display_name'],
                    'role': expert_info['role'],
                    'permissions': expert_info['permissions'],
                    'specializations': expert_info['specializations'],
                    'reviews_completed': expert_info['reviews_completed'],
                    'average_review_time': expert_info['average_review_time']
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get expert profile: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve expert profile"
            )
    
    async def check_expert_permission(
        self, 
        request: Request, 
        permission: str
    ) -> Dict[str, Any]:
        """
        Check if expert has specific permission.
        
        Args:
            request: Authenticated request
            permission: Permission to check
            
        Returns:
            Permission check result
        """
        try:
            verification_result = await self.verify_expert_token(request)
            expert_info = verification_result['expert']
            
            has_permission = await self.auth_service.verify_expert_permissions(
                expert_info['uid'], permission
            )
            
            return {
                'success': True,
                'has_permission': has_permission,
                'expert_role': expert_info['role'],
                'permissions': expert_info['permissions']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Permission check failed"
            )
    
    async def list_all_experts(self, request: Request) -> Dict[str, Any]:
        """
        List all expert users (admin only).
        
        Args:
            request: Authenticated admin request
            
        Returns:
            List of expert users
        """
        try:
            # Verify admin permissions
            verification_result = await self.verify_expert_token(request)
            expert_info = verification_result['expert']
            
            if expert_info['role'] != ExpertRole.ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            
            experts = await self.auth_service.list_experts(active_only=False)
            
            return {
                'success': True,
                'experts': experts,
                'total': len(experts)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list experts: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to list experts"
            )
    
    async def assign_expert_role(
        self, 
        request: Request,
        user_id: str,
        role: str,
        specializations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assign expert role to user (admin only).
        
        Args:
            request: Authenticated admin request
            user_id: User ID to assign role to
            role: Expert role to assign
            specializations: Optional specializations
            
        Returns:
            Role assignment result
        """
        try:
            # Verify admin permissions
            verification_result = await self.verify_expert_token(request)
            expert_info = verification_result['expert']
            
            if expert_info['role'] != ExpertRole.ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            
            if not ExpertRole.is_valid_role(role):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid expert role: {role}"
                )
            
            success = await self.auth_service.set_expert_role(
                user_id, role, specializations
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to assign expert role"
                )
            
            logger.info(f"Expert role assigned: {user_id} -> {role}")
            
            return {
                'success': True,
                'message': f'Expert role {role} assigned to user {user_id}'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign expert role: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to assign expert role"
            )
    
    async def remove_expert_role(
        self, 
        request: Request,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Remove expert role from user (admin only).
        
        Args:
            request: Authenticated admin request
            user_id: User ID to remove role from
            
        Returns:
            Role removal result
        """
        try:
            # Verify admin permissions
            verification_result = await self.verify_expert_token(request)
            expert_info = verification_result['expert']
            
            if expert_info['role'] != ExpertRole.ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            
            success = await self.auth_service.remove_expert_role(user_id)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to remove expert role"
                )
            
            logger.info(f"Expert role removed from user: {user_id}")
            
            return {
                'success': True,
                'message': f'Expert role removed from user {user_id}'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to remove expert role: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to remove expert role"
            )
    
    async def get_available_roles(self) -> Dict[str, Any]:
        """
        Get list of available expert roles.
        
        Returns:
            Available expert roles and their permissions
        """
        try:
            roles_info = {}
            for role in ExpertRole.all_roles():
                roles_info[role] = {
                    'name': role,
                    'permissions': self.auth_service.required_permissions.get(role, [])
                }
            
            return {
                'success': True,
                'roles': roles_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get available roles: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to get available roles"
            )
    
    def create_auth_error_response(
        self, 
        message: str, 
        error_code: str = "EXPERT_AUTH_ERROR"
    ) -> AuthErrorResponse:
        """
        Create standardized expert authentication error response.
        
        Args:
            message: Error message
            error_code: Error code
            
        Returns:
            Standardized error response
        """
        return AuthErrorResponse(
            error="Expert Authentication Error",
            message=message,
            error_code=error_code,
            timestamp=datetime.now()
        )


# Global instance
expert_auth_controller = ExpertAuthController()