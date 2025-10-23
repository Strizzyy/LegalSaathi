"""
Pydantic models for AI clarification and chat requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime


class ClarificationRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=10000)  # Increased limit for detailed analysis
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    user_expertise_level: Optional[str] = "beginner"

    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

    @validator('user_expertise_level')
    def validate_expertise_level(cls, v):
        if v not in ['beginner', 'intermediate', 'expert']:
            raise ValueError('Expertise level must be beginner, intermediate, or expert')
        return v


class ClarificationResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str
    confidence_score: int = Field(..., ge=0, le=100)
    response_quality: str
    processing_time: float
    fallback: bool = False
    service_used: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[datetime] = None


class ConversationSummaryResponse(BaseModel):
    success: bool
    total_questions: int
    recent_questions: List[str]
    analytics: Dict[str, float]
    last_activity: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, bool]
    cache: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None