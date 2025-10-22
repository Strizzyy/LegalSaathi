"""
Pydantic models for document analysis requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    RENTAL_AGREEMENT = "rental_agreement"
    EMPLOYMENT_CONTRACT = "employment_contract"
    INTERNSHIP_AGREEMENT = "internship_agreement"
    NDA = "nda"
    LOAN_AGREEMENT = "loan_agreement"
    PARTNERSHIP_AGREEMENT = "partnership_agreement"
    GENERAL_CONTRACT = "general_contract"


class RiskLevel(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class AnalysisOptions(BaseModel):
    include_ai_insights: bool = True
    include_translation_options: bool = True
    detailed_explanations: bool = True
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)


class DocumentAnalysisRequest(BaseModel):
    document_text: str = Field(..., min_length=100, max_length=50000)
    document_type: DocumentType
    user_expertise_level: Optional[ExpertiseLevel] = ExpertiseLevel.BEGINNER
    analysis_options: Optional[AnalysisOptions] = None

    @validator('document_text')
    def validate_document_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Document text cannot be empty')
        
        # Basic length check - must be substantial
        if len(v.strip()) < 100:
            raise ValueError('Document text must be at least 100 characters long')
        
        # For comparison mode, skip strict legal document validation
        # This allows more flexibility when comparing documents
        return v.strip()


class RiskAssessment(BaseModel):
    level: RiskLevel
    score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str]
    severity: str
    confidence_percentage: int = Field(..., ge=0, le=100)
    risk_categories: Dict[str, float]
    low_confidence_warning: bool


class ClauseAnalysis(BaseModel):
    clause_id: str
    clause_text: str
    risk_assessment: RiskAssessment
    plain_explanation: str
    legal_implications: List[str]
    recommendations: List[str]
    translation_available: bool = False


class DocumentAnalysisResponse(BaseModel):
    analysis_id: str
    overall_risk: RiskAssessment
    clause_assessments: List[ClauseAnalysis]
    summary: str
    processing_time: float
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    enhanced_insights: Optional[Dict[str, Any]] = None
    document_text: Optional[str] = None  # Original document text for comparison features
    document_type: Optional[str] = None  # Document type for comparison features


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str  # "processing", "completed", "failed"
    progress: int = Field(..., ge=0, le=100)
    estimated_completion: Optional[datetime] = None
    result: Optional[DocumentAnalysisResponse] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)