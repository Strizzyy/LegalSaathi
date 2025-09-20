"""
Pydantic models for speech-to-text and text-to-speech requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime


class SpeechToTextRequest(BaseModel):
    language_code: Optional[str] = "en-US"
    enable_punctuation: bool = True
    enable_word_confidence: bool = False
    audio_encoding: Optional[str] = "WEBM_OPUS"
    sample_rate_hertz: Optional[int] = 48000

    @validator('language_code')
    def validate_language_code(cls, v):
        supported_codes = [
            'en-US', 'en-GB', 'hi-IN', 'es-ES', 'es-US', 'fr-FR', 'de-DE',
            'it-IT', 'pt-BR', 'ru-RU', 'ja-JP', 'ko-KR', 'zh-CN'
        ]
        if v not in supported_codes:
            raise ValueError(f'Unsupported language code: {v}')
        return v


class SpeechToTextResponse(BaseModel):
    success: bool
    transcript: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    language_detected: str
    word_confidences: Optional[List[Dict[str, float]]] = None
    processing_time: float
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language_code: Optional[str] = "en-US"
    voice_gender: Optional[str] = "NEUTRAL"
    speaking_rate: Optional[float] = Field(0.9, ge=0.25, le=4.0)
    pitch: Optional[float] = Field(0.0, ge=-20.0, le=20.0)
    audio_encoding: Optional[str] = "MP3"

    @validator('language_code')
    def validate_language_code(cls, v):
        supported_codes = [
            'en-US', 'en-GB', 'hi-IN', 'es-ES', 'es-US', 'fr-FR', 'de-DE',
            'it-IT', 'pt-BR', 'ru-RU', 'ja-JP', 'ko-KR', 'zh-CN'
        ]
        if v not in supported_codes:
            raise ValueError(f'Unsupported language code: {v}')
        return v

    @validator('voice_gender')
    def validate_voice_gender(cls, v):
        if v not in ['MALE', 'FEMALE', 'NEUTRAL']:
            raise ValueError('Voice gender must be MALE, FEMALE, or NEUTRAL')
        return v

    @validator('audio_encoding')
    def validate_audio_encoding(cls, v):
        if v not in ['MP3', 'WAV', 'OGG_OPUS']:
            raise ValueError('Audio encoding must be MP3, WAV, or OGG_OPUS')
        return v


class TextToSpeechResponse(BaseModel):
    success: bool
    audio_content_type: str
    audio_size_bytes: int
    language_code: str
    voice_gender: str
    processing_time: float
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SupportedLanguagesResponse(BaseModel):
    success: bool = True
    speech_to_text_languages: List[Dict[str, str]]
    text_to_speech_languages: List[Dict[str, str]]
    total_stt_count: int
    total_tts_count: int
    timestamp: datetime = Field(default_factory=datetime.now)