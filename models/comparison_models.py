"""
Pydantic models for document comparison requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from models.document_models import RiskAssessment, ClauseAnalysis


class DocumentComparisonRequest(BaseModel):
    document1_text: str = Field(..., min_length=100, max_length=50000)
    document2_text: str = Field(..., min_length=100, max_length=50000)
    document1_type: str  # Accept string instead of enum
    document2_type: str  # Accept string instead of enum
    comparison_focus: Optional[str] = "overall"  # "overall", "clauses", "risks", "terms"

    @validator('document1_text', 'document2_text')
    def validate_document_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Document text cannot be empty')
        return v.strip()
    
    @validator('document1_type', 'document2_type')
    def validate_document_type(cls, v):
        valid_types = [
            'rental_agreement', 'employment_contract', 'nda',
            'loan_agreement', 'partnership_agreement', 'general_contract'
        ]
        if v not in valid_types:
            # Try to normalize common variations
            normalized = v.lower().replace(' ', '_').replace('-', '_')
            if normalized in valid_types:
                return normalized
            # Default to general_contract for unknown types
            return 'general_contract'
        return v


class DocumentDifference(BaseModel):
    type: str  # "risk_level", "clause", "term", "missing_clause"
    description: str
    document1_value: Optional[str] = None
    document2_value: Optional[str] = None
    severity: str  # "high", "medium", "low"
    impact: str
    recommendation: str


class ClauseComparison(BaseModel):
    clause_type: str
    document1_clause: Optional[ClauseAnalysis] = None
    document2_clause: Optional[ClauseAnalysis] = None
    risk_difference: float  # Difference in risk scores
    comparison_notes: str
    recommendation: str


class DocumentComparisonResponse(BaseModel):
    comparison_id: str
    document1_summary: Dict[str, Any]
    document2_summary: Dict[str, Any]
    overall_risk_comparison: Dict[str, Any]
    key_differences: List[DocumentDifference]
    clause_comparisons: List[ClauseComparison]
    recommendation_summary: str
    safer_document: Optional[str] = None  # "document1", "document2", or "similar"
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class ComparisonSummaryResponse(BaseModel):
    comparison_id: str
    document1_type: str
    document2_type: str
    overall_verdict: str
    key_insights: List[str]
    risk_score_difference: float
    timestamp: datetime