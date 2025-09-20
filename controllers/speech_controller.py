"""
Speech controller for FastAPI backend
"""

import logging
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import io

from models.speech_models import (
    SpeechToTextRequest, SpeechToTextResponse,
    TextToSpeechRequest, TextToSpeechResponse,
    SupportedLanguagesResponse
)
from services.google_speech_service import speech_service

logger = logging.getLogger(__name__)


class SpeechController:
    """Controller for speech-to-text and text-to-speech operations"""
    
    def __init__(self):
        self.speech_service = speech_service
    
    async def speech_to_text(
        self, 
        audio_file: UploadFile = File(...),
        language_code: str = "en-US",
        enable_punctuation: bool = True
    ) -> SpeechToTextResponse:
        """Handle speech-to-text conversion for document input"""
        try:
            logger.info(f"Processing speech-to-text for language: {language_code}")
            
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
            
            if len(audio_content) == 0:
                raise HTTPException(status_code=400, detail="Empty audio file")
            
            # Validate file size (max 10MB)
            if len(audio_content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400, 
                    detail="Audio file too large (max 10MB)"
                )
            
            # Process speech-to-text
            result = self.speech_service.speech_to_text(
                audio_content=audio_content,
                language_code=language_code,
                enable_punctuation=enable_punctuation
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Speech-to-text conversion failed')
                )
            
            # Create response
            response = SpeechToTextResponse(
                success=True,
                transcript=result['transcript'],
                confidence=result.get('confidence', 0.9),
                language_detected=result.get('language_detected', language_code),
                processing_time=result.get('processing_time', 0.0)
            )
            
            logger.info("Speech-to-text conversion completed successfully")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Speech-to-text conversion failed: {str(e)}"
            )
    
    async def text_to_speech(self, request: TextToSpeechRequest) -> StreamingResponse:
        """Handle text-to-speech conversion for accessibility"""
        try:
            logger.info(f"Processing text-to-speech for language: {request.language_code}")
            
            if not self.speech_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Speech service is not available"
                )
            
            # Validate text length
            if len(request.text) > 5000:
                raise HTTPException(
                    status_code=400,
                    detail="Text too long for speech synthesis (max 5000 characters)"
                )
            
            # Process text-to-speech
            result = self.speech_service.text_to_speech(
                text=request.text,
                language_code=request.language_code,
                voice_gender=request.voice_gender,
                speaking_rate=request.speaking_rate,
                pitch=request.pitch
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Text-to-speech conversion failed')
                )
            
            # Create audio stream
            audio_content = result['audio_content']
            audio_stream = io.BytesIO(audio_content)
            
            # Determine content type based on encoding
            content_type_map = {
                'MP3': 'audio/mpeg',
                'WAV': 'audio/wav',
                'OGG_OPUS': 'audio/ogg'
            }
            content_type = content_type_map.get(request.audio_encoding, 'audio/mpeg')
            
            logger.info("Text-to-speech conversion completed successfully")
            
            return StreamingResponse(
                io.BytesIO(audio_content),
                media_type=content_type,
                headers={
                    "Content-Disposition": "attachment; filename=speech.mp3",
                    "Content-Length": str(len(audio_content))
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech conversion failed: {str(e)}"
            )
    
    async def get_text_to_speech_info(self, request: TextToSpeechRequest) -> TextToSpeechResponse:
        """Get text-to-speech info without returning audio content"""
        try:
            if not self.speech_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Speech service is not available"
                )
            
            # Process text-to-speech to get metadata
            result = self.speech_service.text_to_speech(
                text=request.text,
                language_code=request.language_code,
                voice_gender=request.voice_gender,
                speaking_rate=request.speaking_rate,
                pitch=request.pitch
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Text-to-speech processing failed')
                )
            
            # Create response with metadata only
            response = TextToSpeechResponse(
                success=True,
                audio_content_type=f"audio/{request.audio_encoding.lower()}",
                audio_size_bytes=len(result['audio_content']),
                language_code=request.language_code,
                voice_gender=request.voice_gender,
                processing_time=result.get('processing_time', 0.0)
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