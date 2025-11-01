"""
Translation controller for FastAPI backend
Enhanced with document summary translation capabilities
"""

import logging
from fastapi import HTTPException

from models.translation_models import (
    TranslationRequest, TranslationResponse,
    ClauseTranslationRequest, ClauseTranslationResponse,
    SupportedLanguagesResponse,
    DocumentSummaryTranslationRequest, DocumentSummaryTranslationResponse,
    SummarySectionTranslationRequest, SummarySectionTranslationResponse,
    EnhancedSupportedLanguagesResponse, SupportedLanguage,
    TranslationUsageStats
)
from services.google_translate_service import GoogleTranslateService
from services.cache_service import CacheService
from services.document_summary_translation_service import DocumentSummaryTranslationService

logger = logging.getLogger(__name__)


class TranslationController:
    """Controller for translation operations with document summary support"""
    
    def __init__(self):
        self.translation_service = GoogleTranslateService()
        self.cache_service = CacheService()
        self.summary_translation_service = DocumentSummaryTranslationService()
    
    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        """Handle general text translation requests"""
        try:
            logger.info(f"Translating text to {request.target_language}")
            
            # Check if translation service is available
            if not hasattr(self.translation_service, 'enabled') or not self.translation_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Translation service is currently unavailable"
                )
            
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
            result = await self.translation_service.translate_text(
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
                source_language=result.get('source_language', 'auto'),
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
            
            result = await self.translation_service.translate_text(
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
                source_language=result.get('source_language', 'auto'),
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
    
    async def get_enhanced_supported_languages(self) -> EnhancedSupportedLanguagesResponse:
        """Get enhanced list of supported languages with metadata for document summary translation"""
        try:
            # Get supported languages from document summary translation service
            languages_dict = self.summary_translation_service.get_supported_languages()
            
            # Format for enhanced API response
            language_list = [
                SupportedLanguage(
                    code=code,
                    name=info['name'],
                    native_name=info['native'],
                    flag=info['flag']
                )
                for code, info in languages_dict.items()
            ]
            
            return EnhancedSupportedLanguagesResponse(
                success=True,
                languages=language_list,
                total_count=len(language_list)
            )
            
        except Exception as e:
            logger.error(f"Failed to get enhanced supported languages: {e}")
            # Return a fallback response instead of raising an exception
            fallback_languages = [
                SupportedLanguage(code='en', name='English', native_name='English', flag='🇺🇸'),
                SupportedLanguage(code='es', name='Spanish', native_name='Español', flag='🇪🇸'),
                SupportedLanguage(code='fr', name='French', native_name='Français', flag='🇫🇷'),
                SupportedLanguage(code='de', name='German', native_name='Deutsch', flag='🇩🇪'),
                SupportedLanguage(code='hi', name='Hindi', native_name='हिंदी', flag='🇮🇳'),
            ]
            
            return EnhancedSupportedLanguagesResponse(
                success=True,
                languages=fallback_languages,
                total_count=len(fallback_languages)
            )
    
    async def translate_document_summary(
        self, 
        request: DocumentSummaryTranslationRequest
    ) -> DocumentSummaryTranslationResponse:
        """Translate complete document summary with all sections"""
        try:
            logger.info(f"Translating document summary to {request.target_language} for user {request.user_id}")
            
            # Perform translation using document summary translation service
            result = await self.summary_translation_service.translate_document_summary(
                summary_content=request.summary_content,
                target_language=request.target_language,
                source_language=request.source_language,
                user_id=request.user_id
            )
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Document summary translation failed')
                
                # Check for rate limiting
                if 'rate limit' in error_msg.lower():
                    raise HTTPException(
                        status_code=429,
                        detail=error_msg
                    )
                
                # Check for daily limits
                if 'daily' in error_msg.lower() and 'limit' in error_msg.lower():
                    raise HTTPException(
                        status_code=503,
                        detail=error_msg
                    )
                
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
            
            # Create response
            response = DocumentSummaryTranslationResponse(
                success=result['success'],
                translated_summary=result.get('translated_summary'),
                source_language=result['source_language'],
                target_language=result['target_language'],
                language_name=result['language_name'],
                sections_translated=result.get('sections_translated', 0),
                overall_confidence=result.get('overall_confidence', 0.0),
                failed_sections=result.get('failed_sections', 0),
                warnings=result.get('warnings'),
                failed_details=result.get('failed_details'),
                fallback_summary=result.get('fallback_summary')
            )
            
            logger.info(f"Document summary translation completed: {response.sections_translated} sections")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document summary translation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Document summary translation failed: {str(e)}"
            )
    
    async def translate_summary_section(
        self, 
        request: SummarySectionTranslationRequest
    ) -> SummarySectionTranslationResponse:
        """Translate individual summary section with legal context"""
        try:
            logger.info(f"Translating summary section {request.section_type} to {request.target_language}")
            
            # Perform section translation
            result = await self.summary_translation_service.translate_summary_section(
                section_content=request.section_content,
                section_type=request.section_type,
                target_language=request.target_language,
                source_language=request.source_language,
                user_id=request.user_id
            )
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Section translation failed')
                
                # Check for rate limiting
                if 'rate limit' in error_msg.lower():
                    raise HTTPException(
                        status_code=429,
                        detail=error_msg,
                        headers={"Retry-After": str(result.get('retry_after', 60))}
                    )
                
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
            
            # Create response
            response = SummarySectionTranslationResponse(
                success=result['success'],
                section_type=result['section_type'],
                original_text=result['original_text'],
                translated_text=result.get('translated_text'),
                source_language=result['source_language'],
                target_language=result['target_language'],
                language_name=result['language_name'],
                confidence_score=result.get('confidence_score')
            )
            
            logger.info(f"Summary section translation completed: {request.section_type}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Summary section translation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Summary section translation failed: {str(e)}"
            )
    
    async def get_translation_usage_stats(self, user_id: str = None) -> TranslationUsageStats:
        """Get translation usage statistics for monitoring"""
        try:
            stats = await self.summary_translation_service.get_usage_stats(user_id)
            
            return TranslationUsageStats(
                daily_requests=stats['daily_requests'],
                daily_characters=stats['daily_characters'],
                daily_request_limit=stats['daily_request_limit'],
                daily_character_limit=stats['daily_character_limit'],
                supported_languages_count=stats['supported_languages_count'],
                cache_ttl_hours=stats['cache_ttl_hours'],
                user_requests_in_window=stats.get('user_requests_in_window'),
                user_rate_limit=stats.get('user_rate_limit')
            )
            
        except Exception as e:
            logger.error(f"Failed to get translation usage stats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get usage statistics: {str(e)}"
            )