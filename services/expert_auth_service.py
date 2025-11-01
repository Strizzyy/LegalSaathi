"""
Expert Authentication Service for Human-in-the-Loop System
Handles expert authentication with Firebase custom claims and role-based permissions
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from firebase_admin import auth
from sqlalchemy.orm import Session

from services.firebase_service import FirebaseService
from models.expert_queue_models import ExpertUser, Base
from models.auth_models import User

logger = logging.getLogger(__name__)


class ExpertRole:
    """Expert role constants"""
    LEGAL_EXPERT = "legal_expert"
    SENIOR_EXPERT = "senior_expert"
    ADMIN = "admin"
    
    @classmethod
    def all_roles(cls) -> List[str]:
        return [cls.LEGAL_EXPERT, cls.SENIOR_EXPERT, cls.ADMIN]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        return role in cls.all_roles()


class ExpertAuthenticationError(Exception):
    """Expert authentication specific error"""
    pass


class ExpertAuthorizationError(Exception):
    """Expert authorization specific error"""
    pass


class ExpertAuthService:
    """
    Expert Authentication Service with Firebase custom claims integration.
    Verifies expert credentials and manages role-based permissions.
    """
    
    def __init__(self):
        self.firebase_service = FirebaseService()
        self.required_permissions = {
            ExpertRole.LEGAL_EXPERT: ["review_documents", "submit_analysis"],
            ExpertRole.SENIOR_EXPERT: ["review_documents", "submit_analysis", "mentor_experts"],
            ExpertRole.ADMIN: ["review_documents", "submit_analysis", "mentor_experts", "manage_experts", "view_analytics"]
        }
    
    async def authenticate_expert(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate expert and verify role using Firebase custom claims.
        
        Args:
            token: Firebase ID token
            
        Returns:
            Expert user information or None if authentication fails
        """
        try:
            # Verify Firebase token
            verification_result = await self.firebase_service.verify_token(token)
            
            if not verification_result['success']:
                raise ExpertAuthenticationError(f"Token verification failed: {verification_result['error']}")
            
            user_info = verification_result['user']
            uid = user_info['uid']
            
            # Get user record with custom claims
            user_record = auth.get_user(uid)
            custom_claims = user_record.custom_claims or {}
            
            # Check if user has expert role
            expert_role = custom_claims.get('expert_role')
            if not expert_role:
                raise ExpertAuthenticationError("User does not have expert role")
            
            if not ExpertRole.is_valid_role(expert_role):
                raise ExpertAuthenticationError(f"Invalid expert role: {expert_role}")
            
            # Get or create expert user record
            expert_user = await self._get_or_create_expert_user(
                uid=uid,
                email=user_info['email'],
                display_name=user_info.get('display_name'),
                role=expert_role,
                custom_claims=custom_claims
            )
            
            # Update last login
            await self._update_last_login(uid)
            
            logger.info(f"Expert authenticated successfully: {uid} ({expert_role})")
            
            return {
                'uid': uid,
                'email': user_info['email'],
                'display_name': user_info.get('display_name'),
                'role': expert_role,
                'permissions': self.required_permissions.get(expert_role, []),
                'specializations': expert_user.get('specializations', []),
                'active': expert_user.get('active', True),
                'reviews_completed': expert_user.get('reviews_completed', 0),
                'average_review_time': expert_user.get('average_review_time', 0.0)
            }
            
        except auth.InvalidIdTokenError:
            raise ExpertAuthenticationError("Invalid Firebase token")
        except auth.ExpiredIdTokenError:
            raise ExpertAuthenticationError("Expired Firebase token")
        except Exception as e:
            logger.error(f"Expert authentication failed: {e}")
            raise ExpertAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def verify_expert_permissions(
        self, 
        expert_id: str, 
        required_permission: str
    ) -> bool:
        """
        Verify expert has required permissions for an operation.
        
        Args:
            expert_id: Expert user ID
            required_permission: Permission to check
            
        Returns:
            True if expert has permission, False otherwise
        """
        try:
            # Get expert user record
            user_record = auth.get_user(expert_id)
            custom_claims = user_record.custom_claims or {}
            expert_role = custom_claims.get('expert_role')
            
            if not expert_role:
                return False
            
            # Check if role has required permission
            role_permissions = self.required_permissions.get(expert_role, [])
            return required_permission in role_permissions
            
        except Exception as e:
            logger.error(f"Permission verification failed for {expert_id}: {e}")
            return False
    
    async def get_expert_role(self, expert_id: str) -> Optional[str]:
        """
        Get expert role from Firebase custom claims.
        
        Args:
            expert_id: Expert user ID
            
        Returns:
            Expert role or None if not found
        """
        try:
            user_record = auth.get_user(expert_id)
            custom_claims = user_record.custom_claims or {}
            return custom_claims.get('expert_role')
            
        except Exception as e:
            logger.error(f"Failed to get expert role for {expert_id}: {e}")
            return None
    
    async def set_expert_role(
        self, 
        user_id: str, 
        role: str, 
        specializations: Optional[List[str]] = None
    ) -> bool:
        """
        Set expert role and specializations using Firebase custom claims.
        
        Args:
            user_id: Firebase user ID
            role: Expert role to assign
            specializations: List of legal specializations
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not ExpertRole.is_valid_role(role):
                raise ValueError(f"Invalid expert role: {role}")
            
            # Get existing custom claims
            user_record = auth.get_user(user_id)
            custom_claims = user_record.custom_claims or {}
            
            # Update expert claims
            custom_claims['expert_role'] = role
            custom_claims['expert_permissions'] = self.required_permissions.get(role, [])
            
            if specializations:
                custom_claims['expert_specializations'] = specializations
            
            # Set custom claims
            auth.set_custom_user_claims(user_id, custom_claims)
            
            # Update expert user record
            await self._get_or_create_expert_user(
                uid=user_id,
                email=user_record.email,
                display_name=user_record.display_name,
                role=role,
                specializations=specializations or []
            )
            
            logger.info(f"Expert role set for {user_id}: {role}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set expert role for {user_id}: {e}")
            return False
    
    async def remove_expert_role(self, user_id: str) -> bool:
        """
        Remove expert role from user.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing custom claims
            user_record = auth.get_user(user_id)
            custom_claims = user_record.custom_claims or {}
            
            # Remove expert claims
            custom_claims.pop('expert_role', None)
            custom_claims.pop('expert_permissions', None)
            custom_claims.pop('expert_specializations', None)
            
            # Set updated claims
            auth.set_custom_user_claims(user_id, custom_claims)
            
            # Deactivate expert user record
            await self._deactivate_expert_user(user_id)
            
            logger.info(f"Expert role removed for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove expert role for {user_id}: {e}")
            return False
    
    async def list_experts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all expert users.
        
        Args:
            active_only: Only return active experts
            
        Returns:
            List of expert user information
        """
        try:
            from services.expert_queue_service import expert_queue_service
            
            db = expert_queue_service.get_db()
            try:
                query = db.query(ExpertUser)
                if active_only:
                    query = query.filter(ExpertUser.active == True)
                
                experts = query.all()
                
                result = []
                for expert in experts:
                    specializations = []
                    if expert.specializations:
                        try:
                            specializations = json.loads(expert.specializations)
                        except:
                            pass
                    
                    result.append({
                        'uid': expert.uid,
                        'email': expert.email,
                        'display_name': expert.display_name,
                        'role': expert.role,
                        'specializations': specializations,
                        'active': expert.active,
                        'created_at': expert.created_at,
                        'last_login': expert.last_login,
                        'reviews_completed': expert.reviews_completed,
                        'average_review_time': expert.average_review_time
                    })
                
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to list experts: {e}")
            return []
    
    async def _get_or_create_expert_user(
        self,
        uid: str,
        email: str,
        display_name: Optional[str] = None,
        role: str = ExpertRole.LEGAL_EXPERT,
        specializations: Optional[List[str]] = None,
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get or create expert user record in database"""
        try:
            from services.expert_queue_service import expert_queue_service
            
            db = expert_queue_service.get_db()
            try:
                # Check if expert user exists
                expert_user = db.query(ExpertUser).filter(ExpertUser.uid == uid).first()
                
                if expert_user:
                    # Update existing record
                    expert_user.email = email
                    expert_user.display_name = display_name
                    expert_user.role = role
                    expert_user.active = True
                    
                    if specializations:
                        expert_user.specializations = json.dumps(specializations)
                    elif custom_claims and 'expert_specializations' in custom_claims:
                        expert_user.specializations = json.dumps(custom_claims['expert_specializations'])
                    
                    db.commit()
                else:
                    # Create new expert user
                    specializations_json = None
                    if specializations:
                        specializations_json = json.dumps(specializations)
                    elif custom_claims and 'expert_specializations' in custom_claims:
                        specializations_json = json.dumps(custom_claims['expert_specializations'])
                    
                    expert_user = ExpertUser(
                        uid=uid,
                        email=email,
                        display_name=display_name,
                        role=role,
                        specializations=specializations_json,
                        active=True,
                        created_at=datetime.utcnow(),
                        reviews_completed=0,
                        average_review_time=0.0
                    )
                    
                    db.add(expert_user)
                    db.commit()
                
                # Convert to dict
                result_specializations = []
                if expert_user.specializations:
                    try:
                        result_specializations = json.loads(expert_user.specializations)
                    except:
                        pass
                
                return {
                    'uid': expert_user.uid,
                    'email': expert_user.email,
                    'display_name': expert_user.display_name,
                    'role': expert_user.role,
                    'specializations': result_specializations,
                    'active': expert_user.active,
                    'created_at': expert_user.created_at,
                    'last_login': expert_user.last_login,
                    'reviews_completed': expert_user.reviews_completed,
                    'average_review_time': expert_user.average_review_time
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get/create expert user: {e}")
            raise
    
    async def _update_last_login(self, uid: str) -> None:
        """Update expert user last login timestamp"""
        try:
            from services.expert_queue_service import expert_queue_service
            
            db = expert_queue_service.get_db()
            try:
                expert_user = db.query(ExpertUser).filter(ExpertUser.uid == uid).first()
                if expert_user:
                    expert_user.last_login = datetime.utcnow()
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to update last login for {uid}: {e}")
    
    async def _deactivate_expert_user(self, uid: str) -> None:
        """Deactivate expert user record"""
        try:
            from services.expert_queue_service import expert_queue_service
            
            db = expert_queue_service.get_db()
            try:
                expert_user = db.query(ExpertUser).filter(ExpertUser.uid == uid).first()
                if expert_user:
                    expert_user.active = False
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to deactivate expert user {uid}: {e}")


# Global instance
expert_auth_service = ExpertAuthService()