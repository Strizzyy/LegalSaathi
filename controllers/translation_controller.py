"""
Translation controller for FastAPI backend
"""

import logging
from fastapi import HTTPException

from models.translation_models import (
    TranslationRequest, TranslationResponse,
    ClauseTranslationRequest, ClauseTranslationResponse,
    SupportedLanguagesResponse
)
from services.google_translate_service import GoogleTranslateService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class TranslationController:
    """Controller for translation operations"""
    
    def __init__(self):
        self.translation_service = GoogleTranslateService()
        self.cache_service = CacheService()
    
    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        """Handle general text translation requests"""
        try:
            logger.info(f"Translating text to {request.target_language}")
            
            # Check cache first
            cache_key = self.cache_service.get_cache_key(
                f"{request.text}_{request.target_language}", 
                "translation"
            )
            
            cached_result = await self.cache_service.get_cached_translation(cache_key)
            if cached_result:
                logger.info("Returning cached translation")
                return TranslationResponse(**cached_result)
            
            # Perform translation
            result = self.translation_service.translate_text(
                text=request.text,
                target_language=request.target_language,
                source_language=request.source_language
            )
            
            # Handle both dict and object formats for result
            success = result.get('success', False) if isinstance(result, dict) else getattr(result, 'success', False)
            if not success:
                error_msg = result.get('error', "Translation failed") if isinstance(result, dict) else getattr(result, 'error', "Translation failed")
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
            
            # Create response
            response = TranslationResponse(
                success=result['success'],
                translated_text=result['translated_text'],
                source_language=result['source_language'],
                target_language=result['target_language'],
                language_name=result['language_name'],
                confidence_score=0.9  # Default confidence for Google Translate
            )
            
            # Cache the result
            await self.cache_service.store_translation(cache_key, response.dict())
            
            logger.info("Translation completed successfully")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Translation failed: {str(e)}"
            )
    
    async def translate_clause(self, request: ClauseTranslationRequest) -> ClauseTranslationResponse:
        """Handle clause-level translation with legal context"""
        try:
            logger.info(f"Translating clause {request.clause_id} to {request.target_language}")
            
            # Check cache first
            cache_key = self.cache_service.get_cache_key(
                f"{request.clause_text}_{request.target_language}_clause", 
                "translation"
            )
            
            cached_result = await self.cache_service.get_cached_translation(cache_key)
            if cached_result:
                logger.info("Returning cached clause translation")
                return ClauseTranslationResponse(**cached_result)
            
            # Perform translation with legal context
            translation_text = request.clause_text
            if request.include_legal_context:
                # Add legal context to improve translation accuracy
                translation_text = f"Legal clause: {request.clause_text}"
            
            result = self.translation_service.translate_text(
                text=translation_text,
                target_language=request.target_language,
                source_language=request.source_language
            )
            
            # Handle both dict and object formats for result
            success = result.get('success', False) if isinstance(result, dict) else getattr(result, 'success', False)
            if not success:
                error_msg = result.get('error', "Clause translation failed") if isinstance(result, dict) else getattr(result, 'error', "Clause translation failed")
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
            
            # Remove legal context prefix if added
            translated_text = result['translated_text']
            if request.include_legal_context and translated_text.startswith("Legal clause:"):
                translated_text = translated_text.replace("Legal clause:", "").strip()
            
            # Generate legal context explanation
            legal_context = None
            if request.include_legal_context:
                legal_context = f"This clause has been translated with legal terminology preserved for accuracy in {result['language_name']}."
            
            # Create response
            response = ClauseTranslationResponse(
                success=result['success'],
                clause_id=request.clause_id,
                original_text=request.clause_text,
                translated_text=translated_text,
                source_language=result['source_language'],
                target_language=result['target_language'],
                language_name=result['language_name'],
                legal_context=legal_context,
                confidence_score=0.9  # Default confidence for Google Translate
            )
            
            # Cache the result
            await self.cache_service.store_translation(cache_key, response.dict())
            
            logger.info("Clause translation completed successfully")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Clause translation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Clause translation failed: {str(e)}"
            )
    
    async def get_supported_languages(self) -> SupportedLanguagesResponse:
        """Get list of supported languages for translation"""
        try:
            # Get supported languages from translation service
            languages = self.translation_service.get_supported_languages()
            
            # Format for API response
            language_list = [
                {"code": code, "name": name}
                for code, name in languages.items()
            ]
            
            return SupportedLanguagesResponse(
                success=True,
                languages=language_list,
                total_count=len(language_list)
            )
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get supported languages: {str(e)}"
            )