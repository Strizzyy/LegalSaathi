"""
Authentication models for Firebase integration
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model for Firebase authentication"""
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool = False
    preferred_language: str = "en"
    created_at: datetime
    last_login: datetime
    usage_stats: Dict[str, int] = {}
    role: str = "user"  # user, admin
    permissions: list = []  # Additional permissions


class FirebaseTokenRequest(BaseModel):
    """Request model for Firebase token validation"""
    token: str


class FirebaseTokenResponse(BaseModel):
    """Response model for Firebase token validation"""
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None


class UserRegistrationRequest(BaseModel):
    """Request model for user registration"""
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserRegistrationResponse(BaseModel):
    """Response model for user registration"""
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    """Response model for user information"""
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None


class AuthErrorResponse(BaseModel):
    """Error response model for authentication"""
    error: str
    message: str
    error_code: str
    timestamp: datetime