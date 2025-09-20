"""
Pydantic models for translation requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
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