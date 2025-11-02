"""
Firebase Admin SDK service for backend authentication
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth
from models.auth_models import User

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase Admin SDK service for user authentication and management"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self._firebase_available = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with proper error handling"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.info("Firebase Admin SDK already initialized")
                self._firebase_available = True
                return
            
            # Get Firebase credentials from environment
            firebase_credentials_json = os.getenv('FIREBASE_ADMIN_CREDENTIALS_JSON', '').strip()
            firebase_credentials_path = os.getenv('FIREBASE_ADMIN_CREDENTIALS_PATH', '').strip()
            
            cred = None
            
            if firebase_credentials_json:
                try:
                    # Use JSON string from environment variable
                    cred_dict = json.loads(firebase_credentials_json)
                    cred = credentials.Certificate(cred_dict)
                    logger.info("Using Firebase credentials from environment JSON")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in FIREBASE_ADMIN_CREDENTIALS_JSON: {e}")
            
            if not cred and firebase_credentials_path and os.path.exists(firebase_credentials_path):
                try:
                    # Use credentials file path
                    cred = credentials.Certificate(firebase_credentials_path)
                    logger.info(f"Using Firebase credentials from file: {firebase_credentials_path}")
                except Exception as e:
                    logger.warning(f"Failed to load credentials from {firebase_credentials_path}: {e}")
            
            if not cred:
                # Try default path
                default_path = 'firebase-admin-credentials.json'
                if os.path.exists(default_path):
                    try:
                        cred = credentials.Certificate(default_path)
                        logger.info(f"Using Firebase credentials from default path: {default_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load credentials from {default_path}: {e}")
            
            if not cred:
                logger.warning("Firebase credentials not found. Authentication features will be disabled.")
                logger.info("To enable Firebase authentication:")
                logger.info("1. Follow FIREBASE_SETUP.md to create Firebase project")
                logger.info("2. Download service account credentials")
                logger.info("3. Set FIREBASE_ADMIN_CREDENTIALS_PATH or FIREBASE_ADMIN_CREDENTIALS_JSON")
                self._firebase_available = False
                return
            
            # Initialize Firebase Admin SDK
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
            self._firebase_available = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            logger.warning("Firebase authentication will be disabled")
            self._firebase_available = False
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return user information
        
        Args:
            token: Firebase ID token
            
        Returns:
            Dict containing user information or error
        """
        if not self._firebase_available:
            return {'success': False, 'error': 'Firebase authentication not configured'}
            
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email', ''),
                'email_verified': decoded_token.get('email_verified', False),
                'display_name': decoded_token.get('name', ''),
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'usage_stats': {}
            }
            
            logger.info(f"Token verified successfully for user: {user_info['uid']}")
            return {'success': True, 'user': user_info}
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token provided")
            return {'success': False, 'error': 'Invalid token'}
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token provided")
            return {'success': False, 'error': 'Token expired'}
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {'success': False, 'error': 'Token verification failed'}
    
    async def get_user_info(self, uid: str) -> Dict[str, Any]:
        """
        Get user information by UID
        
        Args:
            uid: Firebase user UID
            
        Returns:
            Dict containing user information or error
        """
        try:
            user_record = auth.get_user(uid)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email or '',
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name or '',
                'created_at': datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000),
                'last_login': datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else datetime.now(),
                'usage_stats': {}
            }
            
            logger.info(f"User info retrieved for UID: {uid}")
            return {'success': True, 'user': user_info}
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found for UID: {uid}")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Failed to get user info for UID {uid}: {e}")
            return {'success': False, 'error': 'Failed to retrieve user information'}
    
    async def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user account
        
        Args:
            email: User email
            password: User password
            display_name: Optional display name
            
        Returns:
            Dict containing user information or error
        """
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name or '',
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'usage_stats': {}
            }
            
            logger.info(f"User created successfully: {user_record.uid}")
            return {'success': True, 'user': user_info}
            
        except auth.EmailAlreadyExistsError:
            logger.warning(f"Email already exists: {email}")
            return {'success': False, 'error': 'Email already exists'}
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {'success': False, 'error': 'Failed to create user account'}
    
    async def delete_user(self, uid: str) -> Dict[str, Any]:
        """
        Delete a user account
        
        Args:
            uid: Firebase user UID
            
        Returns:
            Dict containing success status or error
        """
        try:
            auth.delete_user(uid)
            logger.info(f"User deleted successfully: {uid}")
            return {'success': True}
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found for deletion: {uid}")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Failed to delete user {uid}: {e}")
            return {'success': False, 'error': 'Failed to delete user account'}
    
    async def update_user(self, uid: str, **kwargs) -> Dict[str, Any]:
        """
        Update user information
        
        Args:
            uid: Firebase user UID
            **kwargs: User properties to update
            
        Returns:
            Dict containing updated user information or error
        """
        try:
            user_record = auth.update_user(uid, **kwargs)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email or '',
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name or '',
                'created_at': datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000),
                'last_login': datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else datetime.now(),
                'usage_stats': {}
            }
            
            logger.info(f"User updated successfully: {uid}")
            return {'success': True, 'user': user_info}
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found for update: {uid}")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Failed to update user {uid}: {e}")
            return {'success': False, 'error': 'Failed to update user information'}