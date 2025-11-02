"""
Support models for human expert support system
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentContextModel(BaseModel):
    """Document context for support requests"""
    documentType: str
    overallRisk: str
    summary: str
    totalClauses: int


class ClauseContextModel(BaseModel):
    """Clause context for support requests"""
    clauseId: str
    text: str
    riskLevel: str
    explanation: str
    implications: List[str]
    recommendations: List[str]
    riskScore: Optional[float] = None
    confidencePercentage: Optional[int] = None
    riskCategories: Optional[Dict[str, float]] = None


class UserContextModel(BaseModel):
    """User context for support requests"""
    documentType: str
    specificConcerns: List[str]


class SupportTicketRequest(BaseModel):
    """Request model for creating support tickets"""
    document_id: str
    clause_id: Optional[str] = None
    user_question: str = Field(..., min_length=10, max_length=2000)
    urgency_level: str = Field(..., pattern="^(low|medium|high)$")
    category: str = Field(..., pattern="^(risk_assessment|contract_terms|legal_clarification|general_inquiry)$")
    document_context: Optional[DocumentContextModel] = None
    clause_context: Optional[ClauseContextModel] = None
    user_context: Optional[UserContextModel] = None


class TicketResolution(BaseModel):
    """Expert resolution for support tickets"""
    summary: str
    recommendations: List[str]
    expert_notes: str
    follow_up_needed: bool = False
    estimated_review_time: str


class ExpertProfile(BaseModel):
    """Expert profile information"""
    id: str
    name: str
    specialty: str
    rating: float = Field(..., ge=0.0, le=5.0)
    response_time: str
    languages: List[str]
    expertise_areas: List[str]
    availability_status: str = Field(..., pattern="^(available|busy|offline)$")
    bio: str


class SupportTicket(BaseModel):
    """Support ticket model"""
    id: str
    document_id: str
    clause_id: Optional[str] = None
    user_question: str
    urgency_level: str
    category: str
    status: str = Field(..., pattern="^(pending|assigned|in_progress|resolved|closed)$")
    priority: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    expert_id: Optional[str] = None
    expert_name: Optional[str] = None
    expert_specialty: Optional[str] = None
    estimated_response: str
    resolution: Optional[TicketResolution] = None
    document_context: Optional[DocumentContextModel] = None
    clause_context: Optional[ClauseContextModel] = None
    user_context: Optional[UserContextModel] = None


class SupportTicketResponse(BaseModel):
    """Response model for support ticket operations"""
    success: bool
    ticket: Optional[SupportTicket] = None
    message: str
    error: Optional[str] = None


class ExpertsListResponse(BaseModel):
    """Response model for experts list"""
    success: bool
    experts: List[ExpertProfile]
    total_available: int
    error: Optional[str] = None


class TicketStatusResponse(BaseModel):
    """Response model for ticket status"""
    success: bool
    ticket: Optional[SupportTicket] = None
    error: Optional[str] = None