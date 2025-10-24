"""
Pydantic models for translation requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    target_language: str = Field(..., min_length=2, max_length=10)
    source_language: Optional[str] = None

    @validator('target_language')
    def validate_target_language(cls, v):
        supported_languages = ['en', 'hi', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        if v not in supported_languages:
            raise ValueError(f'Unsupported target language: {v}')
        return v


class ClauseTranslationRequest(BaseModel):
    clause_id: str
    clause_text: str = Field(..., min_length=1, max_length=2000)
    target_language: str = Field(..., min_length=2, max_length=10)
    source_language: Optional[str] = None
    include_legal_context: bool = True

    @validator('target_language')
    def validate_target_language(cls, v):
        supported_languages = ['en', 'hi', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        if v not in supported_languages:
            raise ValueError(f'Unsupported target language: {v}')
        return v


class TranslationResponse(BaseModel):
    success: bool
    translated_text: str
    source_language: str
    target_language: str
    language_name: str
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ClauseTranslationResponse(BaseModel):
    success: bool
    clause_id: str
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    language_name: str
    legal_context: Optional[str] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SupportedLanguagesResponse(BaseModel):
    success: bool = True
    languages: List[Dict[str, str]]
    total_count: int
    timestamp: datetime = Field(default_factory=datetime.now)


# Document Summary Translation Models

class DocumentSummaryContent(BaseModel):
    """Interface for structured document summary content"""
    what_this_document_means: Optional[str] = None
    key_points: Optional[List[str]] = None
    risk_assessment: Optional[str] = None
    what_you_should_do: Optional[List[str]] = None
    simple_explanation: Optional[str] = None
    
    # Alternative field names for compatibility
    jargon_free_version: Optional[str] = None
    key_points_list: Optional[List[str]] = None
    risk_summary: Optional[str] = None
    recommendations: Optional[List[str]] = None
    simplified_explanation: Optional[str] = None


class DocumentSummaryTranslationRequest(BaseModel):
    """Request model for document summary translation"""
    summary_content: Dict[str, Any] = Field(..., description="Document summary content to translate")
    target_language: str = Field(..., min_length=2, max_length=10, description="Target language code")
    source_language: str = Field(default="en", description="Source language code")
    preserve_formatting: bool = Field(default=True, description="Preserve original formatting")
    user_id: Optional[str] = Field(default="anonymous", description="User ID for rate limiting")

    @validator('target_language', 'source_language')
    def validate_language_codes(cls, v):
        # Extended language support validation
        supported_languages = [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi',
            'nl', 'sv', 'da', 'no', 'fi', 'pl', 'cs', 'hu', 'tr', 'he', 'th', 'vi',
            'id', 'ms', 'tl', 'bn', 'ta', 'te', 'ur'
        ]
        if v not in supported_languages:
            raise ValueError(f'Unsupported language code: {v}')
        return v


class SectionTranslationResult(BaseModel):
    """Result for individual section translation"""
    success: bool
    section_type: str
    original_text: str
    translated_text: Optional[str] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None


class DocumentSummaryTranslationResponse(BaseModel):
    """Response model for document summary translation"""
    success: bool
    translated_summary: Optional[Dict[str, Any]] = None
    source_language: str
    target_language: str
    language_name: str
    sections_translated: int = 0
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_sections: int = 0
    warnings: Optional[List[str]] = None
    failed_details: Optional[List[Dict[str, Any]]] = None
    fallback_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SummarySectionTranslationRequest(BaseModel):
    """Request model for individual summary section translation"""
    section_content: str = Field(..., min_length=1, max_length=5000)
    section_type: str = Field(..., description="Type of summary section")
    target_language: str = Field(..., min_length=2, max_length=10)
    source_language: str = Field(default="en")
    user_id: Optional[str] = Field(default="anonymous")

    @validator('section_type')
    def validate_section_type(cls, v):
        valid_sections = [
            'what_this_document_means', 'key_points', 'risk_assessment',
            'what_you_should_do', 'simple_explanation'
        ]
        if v not in valid_sections:
            raise ValueError(f'Invalid section type: {v}')
        return v


class SummarySectionTranslationResponse(BaseModel):
    """Response model for individual summary section translation"""
    success: bool
    section_type: str
    original_text: str
    translated_text: Optional[str] = None
    source_language: str
    target_language: str
    language_name: str
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    retry_after: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SupportedLanguage(BaseModel):
    """Model for supported language information"""
    code: str
    name: str
    native_name: str
    flag: str


class EnhancedSupportedLanguagesResponse(BaseModel):
    """Enhanced response for supported languages with additional metadata"""
    success: bool = True
    languages: List[SupportedLanguage]
    total_count: int
    features: Dict[str, bool] = Field(default_factory=lambda: {
        'document_summary_translation': True,
        'section_specific_context': True,
        'legal_terminology_preservation': True,
        'confidence_scoring': True,
        'translation_caching': True
    })
    rate_limits: Dict[str, int] = Field(default_factory=lambda: {
        'requests_per_minute': 50,
        'daily_request_limit': 1000,
        'daily_character_limit': 100000
    })
    timestamp: datetime = Field(default_factory=datetime.now)


class TranslationUsageStats(BaseModel):
    """Model for translation usage statistics"""
    daily_requests: int
    daily_characters: int
    daily_request_limit: int
    daily_character_limit: int
    supported_languages_count: int
    cache_ttl_hours: float
    user_requests_in_window: Optional[int] = None
    user_rate_limit: Optional[int] = None