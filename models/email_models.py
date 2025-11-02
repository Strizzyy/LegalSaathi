"""
Email notification models for Gmail integration
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class EmailTemplate(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
    SUMMARY = "summary"


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailNotificationRequest(BaseModel):
    """Request model for sending email notifications"""
    user_email: EmailStr
    analysis_id: str
    include_pdf: bool = True
    email_template: EmailTemplate = EmailTemplate.STANDARD
    custom_message: Optional[str] = None
    priority: EmailPriority = EmailPriority.NORMAL


class EmailNotificationResponse(BaseModel):
    """Response model for email notification requests"""
    success: bool
    message_id: Optional[str] = None
    delivery_status: str
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class EmailDeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailAttachment(BaseModel):
    """Email attachment model"""
    filename: str
    content_type: str
    size: int
    data: bytes = Field(exclude=True)  # Exclude from serialization


class EmailTemplate(BaseModel):
    """Email template model"""
    template_id: str
    subject: str
    html_content: str
    text_content: str
    variables: Dict[str, Any] = {}


class EmailSendRequest(BaseModel):
    """Internal email send request model"""
    to_email: EmailStr
    subject: str
    html_content: str
    text_content: str
    attachments: List[EmailAttachment] = []
    reply_to: Optional[EmailStr] = None
    priority: EmailPriority = EmailPriority.NORMAL


class EmailSendResponse(BaseModel):
    """Internal email send response model"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.now)


class EmailRateLimitInfo(BaseModel):
    """Email rate limiting information"""
    user_id: str
    emails_sent_today: int
    emails_sent_this_hour: int
    daily_limit: int = 50
    hourly_limit: int = 5
    next_reset_time: datetime
    is_rate_limited: bool = False


class EmailErrorResponse(BaseModel):
    """Email error response model"""
    error: str
    message: str
    error_code: str
    retry_after: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)