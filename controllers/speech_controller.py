"""
Enhanced Speech controller for FastAPI backend with user-based rate limiting,
audio validation, caching, and comprehensive error handling
"""

import logging
from fastapi import HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
import io
from typing import Optional

from models.speech_models import (
    SpeechToTextRequest, SpeechToTextResponse,
    TextToSpeechRequest, TextToSpeechResponse,
    SupportedLanguagesResponse
)
from services.google_speech_service import speech_service
from middleware.firebase_auth_middleware import UserBasedRateLimiter

logger = logging.getLogger(__name__)


class SpeechController:
    """Enhanced controller for speech-to-text and text-to-speech operations"""
    
    def __init__(self):
        self.speech_service = speech_service
        self.rate_limiter = UserBasedRateLimiter()
    
    async def speech_to_text(
        self, 
        request: Request,
        audio_file: UploadFile = File(...),
        language_code: str = "en-US",
        enable_punctuation: bool = True
    ) -> SpeechToTextResponse:
        """Handle speech-to-text conversion with enhanced validation and rate limiting"""
        try:
            # Get user info from request state
            user_id = getattr(request.state, 'user_id', None) or "anonymous"
            is_authenticated = getattr(request.state, 'is_authenticated', False)
            
            # Check rate limits
            if not self.rate_limiter.check_rate_limit(user_id, 'speech_to_text', request):
                rate_info = self.rate_limiter.get_rate_limit_info(user_id, 'speech_to_text')
                raise HTTPException(
                    status_code=429,
                    detail=f"Speech-to-text rate limit exceeded. Try again in {rate_info.get('reset_time', 3600)} seconds."
                )
            
            logger.info(f"Processing speech-to-text for user: {user_id}, language: {language_code}")
            
            if not self.speech_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Speech service is not available"
                )
            
            # Validate file
            if not audio_file.filename:
                raise HTTPException(status_code=400, detail="No audio file provided")
            
            # Read audio content
            audio_content = await audio_file.read()
            
            # Process speech-to-text with enhanced service
            result = self.speech_service.speech_to_text(
                audio_content=audio_content,
                language_code=language_code,
                enable_punctuation=enable_punctuation,
                user_id=user_id,
                filename=audio_file.filename or ""
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Speech-to-text conversion failed')
                )
            
            # Create response
            response = SpeechToTextResponse(
                success=result['success'],
                transcript=result.get('transcript', ''),
                confidence=result.get('confidence', 0.0),
                language_detected=result.get('language_detected', language_code),
                processing_time=result.get('processing_time', 0.0),
                error_message=result.get('error') if not result['success'] else None,
                usage_stats=result.get('usage_stats')
            )
            
            if result['success']:
                logger.info(f"Speech-to-text conversion completed successfully for user: {user_id}")
            else:
                logger.warning(f"Speech-to-text failed for user: {user_id}, error: {result.get('error')}")
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Speech-to-text conversion failed: {str(e)}"
            )
    
    async def text_to_speech(self, request_obj: Request, tts_request: TextToSpeechRequest) -> StreamingResponse:
        """Handle text-to-speech conversion with enhanced caching and rate limiting"""
        try:
            # Get user info from request state
            user_id = getattr(request_obj.state, 'user_id', None) or "anonymous"
            is_authenticated = getattr(request_obj.state, 'is_authenticated', False)
            
            # Check if speech service is available
            if not self.speech_service or not hasattr(self.speech_service, 'enabled') or not self.speech_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Speech service is not available"
                )
            
            # Check rate limits
            if not self.rate_limiter.check_rate_limit(user_id, 'text_to_speech', request_obj):
                rate_info = self.rate_limiter.get_rate_limit_info(user_id, 'text_to_speech')
                raise HTTPException(
                    status_code=429,
                    detail=f"Text-to-speech rate limit exceeded. Try again in {rate_info.get('reset_time', 3600)} seconds."
                )
            
            logger.info(f"Processing text-to-speech for user: {user_id}, language: {tts_request.language_code}")
            
            # Process text-to-speech with enhanced service
            result = self.speech_service.text_to_speech(
                text=tts_request.text,
                language_code=tts_request.language_code,
                voice_gender=tts_request.voice_gender,
                speaking_rate=tts_request.speaking_rate,
                pitch=tts_request.pitch,
                user_id=user_id
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Text-to-speech conversion failed')
                )
            
            # Create audio stream
            audio_content = result['audio_content']
            
            # Determine content type based on encoding
            content_type_map = {
                'MP3': 'audio/mpeg',
                'WAV': 'audio/wav',
                'OGG_OPUS': 'audio/ogg'
            }
            content_type = content_type_map.get(tts_request.audio_encoding, 'audio/mpeg')
            
            # Add cache headers if content was cached
            headers = {
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Content-Length": str(len(audio_content))
            }
            
            if result.get('cached'):
                headers["X-Cache-Status"] = "HIT"
                logger.info(f"Text-to-speech served from cache for user: {user_id}")
            else:
                headers["X-Cache-Status"] = "MISS"
                logger.info(f"Text-to-speech conversion completed for user: {user_id}")
            
            return StreamingResponse(
                io.BytesIO(audio_content),
                media_type=content_type,
                headers=headers
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech conversion failed: {str(e)}"
            )
    
    async def get_text_to_speech_info(self, request_obj: Request, tts_request: TextToSpeechRequest) -> TextToSpeechResponse:
        """Get text-to-speech info without returning audio content"""
        try:
            # Get user info from request state
            user_id = getattr(request_obj.state, 'user_id', None) or "anonymous"
            
            if not self.speech_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Speech service is not available"
                )
            
            # Process text-to-speech to get metadata
            result = self.speech_service.text_to_speech(
                text=tts_request.text,
                language_code=tts_request.language_code,
                voice_gender=tts_request.voice_gender,
                speaking_rate=tts_request.speaking_rate,
                pitch=tts_request.pitch,
                user_id=user_id
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Text-to-speech processing failed')
                )
            
            # Create response with metadata only
            response = TextToSpeechResponse(
                success=result['success'],
                audio_content_type=f"audio/{tts_request.audio_encoding.lower()}",
                audio_size_bytes=len(result.get('audio_content', b'')),
                language_code=tts_request.language_code,
                voice_gender=tts_request.voice_gender,
                processing_time=result.get('processing_time', 0.0),
                error_message=result.get('error') if not result['success'] else None,
                cached=result.get('cached'),
                usage_stats=result.get('usage_stats')
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text-to-speech info failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech processing failed: {str(e)}"
            )
    
    async def get_supported_languages(self) -> SupportedLanguagesResponse:
        """Get list of supported languages for speech services"""
        try:
            # Define supported languages for speech services
            stt_languages = [
                {"code": "en-US", "name": "English (US)"},
                {"code": "en-GB", "name": "English (UK)"},
                {"code": "hi-IN", "name": "Hindi (India)"},
                {"code": "es-ES", "name": "Spanish (Spain)"},
                {"code": "es-US", "name": "Spanish (US)"},
                {"code": "fr-FR", "name": "French (France)"},
                {"code": "de-DE", "name": "German (Germany)"},
                {"code": "it-IT", "name": "Italian (Italy)"},
                {"code": "pt-BR", "name": "Portuguese (Brazil)"},
                {"code": "ru-RU", "name": "Russian (Russia)"},
                {"code": "ja-JP", "name": "Japanese (Japan)"},
                {"code": "ko-KR", "name": "Korean (South Korea)"},
                {"code": "zh-CN", "name": "Chinese (Simplified)"}
            ]
            
            # Text-to-speech supports the same languages
            tts_languages = stt_languages.copy()
            
            return SupportedLanguagesResponse(
                success=True,
                speech_to_text_languages=stt_languages,
                text_to_speech_languages=tts_languages,
                total_stt_count=len(stt_languages),
                total_tts_count=len(tts_languages)
            )
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get supported languages: {str(e)}"
            )
    
    async def get_usage_stats(self, request: Request) -> dict:
        """Get usage statistics for the current user"""
        try:
            user_id = getattr(request.state, 'user_id', None) or "anonymous"
            
            if not self.speech_service.enabled:
                return {
                    'error': 'Speech service not available',
                    'user_id': user_id
                }
            
            stats = self.speech_service.get_usage_stats(user_id)
            stats['user_id'] = user_id
            stats['rate_limits'] = {
                'speech_to_text': self.rate_limiter.get_rate_limit_info(user_id, 'speech_to_text'),
                'text_to_speech': self.rate_limiter.get_rate_limit_info(user_id, 'text_to_speech')
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                'error': f"Failed to get usage stats: {str(e)}",
                'user_id': getattr(request.state, 'user_id', None) or "anonymous"
            }