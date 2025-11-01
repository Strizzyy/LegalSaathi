"""
Pydantic models for Expert Queue Management in Human-in-the-Loop System
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid

Base = declarative_base()


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Database Models
class ExpertReviewItem(Base):
    __tablename__ = "expert_review_items"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(100), unique=True, nullable=False, index=True)
    document_content = Column(Text, nullable=False)  # Base64 encoded document
    ai_analysis = Column(Text, nullable=False)  # JSON string of AI analysis
    user_email = Column(String(255), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, index=True)
    confidence_breakdown = Column(Text)  # JSON string of confidence breakdown
    status = Column(String(20), nullable=False, default=ReviewStatus.PENDING.value, index=True)
    priority = Column(String(10), nullable=False, default=Priority.MEDIUM.value, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_expert_id = Column(String(100), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion_hours = Column(Integer, default=24)
    document_type = Column(String(50), nullable=True)
    expert_notes = Column(Text, nullable=True)
    expert_analysis = Column(Text, nullable=True)  # JSON string of expert analysis
    review_duration_minutes = Column(Integer, nullable=True)


class ExpertUser(Base):
    __tablename__ = "expert_users"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="legal_expert")  # legal_expert, senior_expert, admin
    specializations = Column(Text, nullable=True)  # JSON array of specializations
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    reviews_completed = Column(Integer, default=0)
    average_review_time = Column(Float, default=0.0)  # in minutes


class ReviewMetrics(Base):
    __tablename__ = "review_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(100), ForeignKey('expert_review_items.review_id'), nullable=False, index=True)
    expert_id = Column(String(100), ForeignKey('expert_users.uid'), nullable=False, index=True)
    review_duration_minutes = Column(Integer, nullable=False)
    clauses_modified = Column(Integer, default=0)
    confidence_improvement = Column(Float, default=0.0)
    user_satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    complexity_rating = Column(Integer, nullable=False)  # 1-5 scale
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Pydantic Models for API
class ExpertReviewSubmission(BaseModel):
    document_content: str = Field(..., description="Base64 encoded document content")
    ai_analysis: Dict[str, Any] = Field(..., description="AI analysis results")
    user_email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_breakdown: Dict[str, Any] = Field(..., description="Detailed confidence breakdown")
    document_type: Optional[str] = None
    priority: Optional[Priority] = None

    @validator('user_email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Valid email address required')
        return v.lower().strip()


class ExpertReviewResponse(BaseModel):
    review_id: str
    status: ReviewStatus
    estimated_completion_hours: int
    priority: Priority
    created_at: datetime
    message: str


class ExpertReviewItemResponse(BaseModel):
    review_id: str
    user_email: str
    confidence_score: float
    confidence_breakdown: Dict[str, Any]
    status: ReviewStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    assigned_expert_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion_hours: int
    document_type: Optional[str] = None
    expert_notes: Optional[str] = None
    ai_analysis: Dict[str, Any]
    document_content: Optional[str] = None  # Only included for assigned expert


class ExpertAnalysisSubmission(BaseModel):
    review_id: str
    expert_analysis: Dict[str, Any] = Field(..., description="Expert-reviewed analysis")
    expert_notes: Optional[str] = None
    clauses_modified: int = Field(default=0, ge=0)
    complexity_rating: int = Field(..., ge=1, le=5)
    review_duration_minutes: int = Field(..., ge=1)


class ExpertAnalysisResponse(BaseModel):
    review_id: str
    expert_id: str
    expert_analysis: Dict[str, Any]
    expert_notes: Optional[str] = None
    completed_at: datetime
    review_duration_minutes: int
    confidence_improvement: float


class QueueStatsResponse(BaseModel):
    total_items: int
    pending_items: int
    in_review_items: int
    completed_items: int
    cancelled_items: int
    average_completion_time_hours: float
    oldest_pending_item: Optional[datetime] = None
    expert_workload: Dict[str, int]  # expert_id -> number of assigned reviews


class ExpertUserResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    role: str
    specializations: List[str] = []
    active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    reviews_completed: int
    average_review_time: float


class ReviewMetricsResponse(BaseModel):
    review_id: str
    expert_id: str
    review_duration_minutes: int
    clauses_modified: int
    confidence_improvement: float
    user_satisfaction_rating: Optional[int] = None
    complexity_rating: int
    created_at: datetime


class QueueFilters(BaseModel):
    status: Optional[ReviewStatus] = None
    priority: Optional[Priority] = None
    assigned_expert_id: Optional[str] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class QueueResponse(BaseModel):
    items: List[ExpertReviewItemResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


def generate_review_id() -> str:
    """Generate unique review ID"""
    return f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"


def calculate_priority(confidence_score: float) -> Priority:
    """Calculate priority based on confidence score"""
    if confidence_score < 0.3:
        return Priority.URGENT
    elif confidence_score < 0.4:
        return Priority.HIGH
    elif confidence_score < 0.5:
        return Priority.MEDIUM
    else:
        return Priority.LOW


def calculate_estimated_hours(confidence_score: float, priority: Priority) -> int:
    """Calculate estimated completion hours based on confidence and priority"""
    base_hours = {
        Priority.URGENT: 6,
        Priority.HIGH: 12,
        Priority.MEDIUM: 24,
        Priority.LOW: 48
    }
    
    # Adjust based on confidence score
    if confidence_score < 0.2:
        return max(4, base_hours[priority] - 6)
    elif confidence_score < 0.4:
        return base_hours[priority]
    else:
        return min(72, base_hours[priority] + 12)