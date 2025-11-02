"""
Document Summary Translation Service
Provides section-specific translation capabilities for document summaries
with caching, rate limiting, and cost monitoring
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from services.google_translate_service import GoogleTranslateService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class DocumentSummaryTranslationService:
    """
    Service for translating document summary sections with advanced features:
    - Section-specific translation with legal context preservation
    - 1-hour caching system for translated content
    - Rate limiting (50 requests/minute per user)
    - Cost monitoring with daily usage limits
    - Confidence scoring for translation quality
    - Fallback mechanisms for translation failures
    """
    
    def __init__(self):
        self.google_translate = GoogleTranslateService()
        self.cache_service = CacheService()
        
        # Rate limiting: 50 requests per minute per user
        self.rate_limits = {}  # user_id -> {'count': int, 'window_start': timestamp}
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 50
        
        # Cost monitoring: daily limits
        self.daily_usage = {}  # date -> {'requests': int, 'characters': int}
        self.daily_request_limit = 1000
        self.daily_character_limit = 100000
        
        # Translation cache with 1-hour TTL
        self.translation_cache_ttl = 3600  # 1 hour
        
        # Supported languages with enhanced coverage (20+ languages)
        self.supported_languages = {
            'en': {'name': 'English', 'native': 'English', 'flag': '🇺🇸'},
            'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
            'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
            'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
            'it': {'name': 'Italian', 'native': 'Italiano', 'flag': '🇮🇹'},
            'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹'},
            'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
            'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
            'ko': {'name': 'Korean', 'native': '한국어', 'flag': '🇰🇷'},
            'zh': {'name': 'Chinese', 'native': '中文', 'flag': '🇨🇳'},
            'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦'},
            'hi': {'name': 'Hindi', 'native': 'हिंदी', 'flag': '🇮🇳'},
            'nl': {'name': 'Dutch', 'native': 'Nederlands', 'flag': '🇳🇱'},
            'sv': {'name': 'Swedish', 'native': 'Svenska', 'flag': '🇸🇪'},
            'da': {'name': 'Danish', 'native': 'Dansk', 'flag': '🇩🇰'},
            'no': {'name': 'Norwegian', 'native': 'Norsk', 'flag': '🇳🇴'},
            'fi': {'name': 'Finnish', 'native': 'Suomi', 'flag': '🇫🇮'},
            'pl': {'name': 'Polish', 'native': 'Polski', 'flag': '🇵🇱'},
            'cs': {'name': 'Czech', 'native': 'Čeština', 'flag': '🇨🇿'},
            'hu': {'name': 'Hungarian', 'native': 'Magyar', 'flag': '🇭🇺'},
            'tr': {'name': 'Turkish', 'native': 'Türkçe', 'flag': '🇹🇷'},
            'he': {'name': 'Hebrew', 'native': 'עברית', 'flag': '🇮🇱'},
            'th': {'name': 'Thai', 'native': 'ไทย', 'flag': '🇹🇭'},
            'vi': {'name': 'Vietnamese', 'native': 'Tiếng Việt', 'flag': '🇻🇳'},
            'id': {'name': 'Indonesian', 'native': 'Bahasa Indonesia', 'flag': '🇮🇩'},
            'ms': {'name': 'Malay', 'native': 'Bahasa Melayu', 'flag': '🇲🇾'},
            'tl': {'name': 'Filipino', 'native': 'Tagalog', 'flag': '🇵🇭'},
            'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': '🇧🇩'},
            'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳'},
            'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳'},
            'ur': {'name': 'Urdu', 'native': 'اردو', 'flag': '🇵🇰'},
        }
        
        # Section-specific translation contexts for legal terminology
        self.section_contexts = {
            'what_this_document_means': 'Legal document overview and general meaning',
            'key_points': 'Important legal provisions and terms',
            'risk_assessment': 'Legal risk analysis and potential consequences',
            'what_you_should_do': 'Legal recommendations and actionable advice',
            'simple_explanation': 'Simplified legal explanation for non-lawyers'
        }
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit (50 requests/minute)"""
        current_time = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = {'count': 0, 'window_start': current_time}
            return True
        
        user_limit = self.rate_limits[user_id]
        
        # Reset window if expired
        if current_time - user_limit['window_start'] >= self.rate_limit_window:
            user_limit['count'] = 0
            user_limit['window_start'] = current_time
        
        # Check if limit exceeded
        if user_limit['count'] >= self.rate_limit_max:
            return False
        
        user_limit['count'] += 1
        return True
    
    async def check_daily_limits(self) -> bool:
        """Check if daily usage limits have been exceeded"""
        today = datetime.now().date().isoformat()
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {'requests': 0, 'characters': 0}
        
        usage = self.daily_usage[today]
        return (usage['requests'] < self.daily_request_limit and 
                usage['characters'] < self.daily_character_limit)
    
    async def update_daily_usage(self, character_count: int):
        """Update daily usage statistics"""
        today = datetime.now().date().isoformat()
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {'requests': 0, 'characters': 0}
        
        self.daily_usage[today]['requests'] += 1
        self.daily_usage[today]['characters'] += character_count
    
    def generate_cache_key(self, content: str, section_type: str, target_language: str) -> str:
        """Generate cache key for translation"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"summary_translation:{section_type}:{target_language}:{content_hash}"
    
    async def get_cached_translation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached translation if available and not expired"""
        cached = await self.cache_service.get_cached_translation(cache_key)
        if cached and 'timestamp' in cached:
            cache_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cache_time < timedelta(seconds=self.translation_cache_ttl):
                logger.info(f"Cache hit for summary translation: {cache_key}")
                return cached
            else:
                logger.info(f"Cache expired for summary translation: {cache_key}")
        return None
    
    async def cache_translation(self, cache_key: str, translation_data: Dict[str, Any]):
        """Cache translation result with timestamp"""
        translation_data['timestamp'] = datetime.now().isoformat()
        await self.cache_service.store_translation(cache_key, translation_data)
    
    async def translate_summary_section(
        self,
        section_content: str,
        section_type: str,
        target_language: str,
        source_language: str = 'en',
        user_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """
        Translate individual summary section with legal context preservation
        
        Args:
            section_content: Content to translate
            section_type: Type of section (what_this_document_means, key_points, etc.)
            target_language: Target language code
            source_language: Source language code (default: 'en')
            user_id: User ID for rate limiting
            
        Returns:
            Dictionary with translation result and metadata
        """
        try:
            # Validate inputs
            if not section_content or not section_content.strip():
                return {
                    'success': False,
                    'error': 'Empty section content provided',
                    'section_type': section_type
                }
            
            if target_language not in self.supported_languages:
                return {
                    'success': False,
                    'error': f'Unsupported target language: {target_language}',
                    'section_type': section_type
                }
            
            # Check rate limiting
            if not await self.check_rate_limit(user_id):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'section_type': section_type,
                    'retry_after': 60
                }
            
            # Check daily limits
            if not await self.check_daily_limits():
                return {
                    'success': False,
                    'error': 'Daily translation limit exceeded. Please try again tomorrow.',
                    'section_type': section_type
                }
            
            # Check cache first
            cache_key = self.generate_cache_key(section_content, section_type, target_language)
            cached_result = await self.get_cached_translation(cache_key)
            if cached_result:
                return cached_result
            
            # Add legal context for better translation accuracy
            context = self.section_contexts.get(section_type, 'Legal document section')
            contextual_content = f"[Legal Context: {context}] {section_content}"
            
            # Perform translation
            translation_result = self.google_translate.translate_text(
                text=contextual_content,
                target_language=target_language,
                source_language=source_language
            )
            
            if not translation_result.get('success', False):
                return {
                    'success': False,
                    'error': translation_result.get('error', 'Translation failed'),
                    'section_type': section_type
                }
            
            # Remove context prefix from translated text
            translated_text = translation_result['translated_text']
            if translated_text.startswith('[Legal Context:'):
                # Find the end of the context marker and remove it
                context_end = translated_text.find('] ')
                if context_end != -1:
                    translated_text = translated_text[context_end + 2:].strip()
            
            # Calculate confidence score based on translation quality indicators
            confidence_score = await self.calculate_confidence_score(
                section_content, translated_text, section_type
            )
            
            # Update usage statistics
            await self.update_daily_usage(len(section_content))
            
            # Prepare result
            result = {
                'success': True,
                'section_type': section_type,
                'original_text': section_content,
                'translated_text': translated_text,
                'source_language': translation_result['source_language'],
                'target_language': target_language,
                'language_name': self.supported_languages[target_language]['name'],
                'confidence_score': confidence_score,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            await self.cache_translation(cache_key, result)
            
            logger.info(f"Successfully translated {section_type} to {target_language}")
            return result
            
        except Exception as e:
            logger.error(f"Error translating summary section {section_type}: {e}")
            return {
                'success': False,
                'error': f'Translation service error: {str(e)}',
                'section_type': section_type
            }
    
    async def translate_document_summary(
        self,
        summary_content: Dict[str, Any],
        target_language: str,
        source_language: str = 'en',
        user_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """
        Translate all summary sections: What This Document Means, Key Points, 
        Risk Assessment, What You Should Do, and Simple Explanation
        
        Args:
            summary_content: Dictionary containing all summary sections
            target_language: Target language code
            source_language: Source language code (default: 'en')
            user_id: User ID for rate limiting
            
        Returns:
            Dictionary with all translated sections and metadata
        """
        try:
            # Validate target language
            if target_language not in self.supported_languages:
                return {
                    'success': False,
                    'error': f'Unsupported target language: {target_language}'
                }
            
            # If target language is same as source, return original content
            if target_language == source_language:
                return {
                    'success': True,
                    'translated_summary': summary_content,
                    'source_language': source_language,
                    'target_language': target_language,
                    'language_name': self.supported_languages[target_language]['name'],
                    'sections_translated': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Map of expected summary sections
            section_mapping = {
                'what_this_document_means': ['jargonFreeVersion', 'overview', 'what_this_document_means'],
                'key_points': ['keyPoints', 'key_points'],
                'risk_assessment': ['riskSummary', 'risk_assessment', 'risks'],
                'what_you_should_do': ['recommendations', 'what_you_should_do', 'actions'],
                'simple_explanation': ['simplifiedExplanation', 'simple_explanation', 'simplified']
            }
            
            translated_summary = {}
            translation_results = []
            sections_translated = 0
            
            # Translate each section
            for section_type, possible_keys in section_mapping.items():
                section_content = None
                original_key = None
                
                # Find the content using possible keys
                for key in possible_keys:
                    if key in summary_content and summary_content[key]:
                        section_content = summary_content[key]
                        original_key = key
                        break
                
                if not section_content:
                    logger.warning(f"Section {section_type} not found in summary content")
                    continue
                
                # Handle list content (like key_points)
                if isinstance(section_content, list):
                    translated_items = []
                    for item in section_content:
                        if isinstance(item, str) and item.strip():
                            item_result = await self.translate_summary_section(
                                item, section_type, target_language, source_language, user_id
                            )
                            if item_result.get('success'):
                                translated_items.append(item_result['translated_text'])
                                sections_translated += 1
                            else:
                                # Fallback to original on failure
                                translated_items.append(item)
                                translation_results.append(item_result)
                    
                    translated_summary[original_key] = translated_items
                
                # Handle string content
                elif isinstance(section_content, str) and section_content.strip():
                    section_result = await self.translate_summary_section(
                        section_content, section_type, target_language, source_language, user_id
                    )
                    
                    if section_result.get('success'):
                        translated_summary[original_key] = section_result['translated_text']
                        sections_translated += 1
                    else:
                        # Fallback to original on failure
                        translated_summary[original_key] = section_content
                        translation_results.append(section_result)
                
                else:
                    # Keep original content if not translatable
                    translated_summary[original_key] = section_content
            
            # Copy over any other fields that weren't translated
            for key, value in summary_content.items():
                if key not in translated_summary:
                    translated_summary[key] = value
            
            # Calculate overall confidence score
            overall_confidence = 0.9 if sections_translated > 0 else 0.0
            
            # Check if any translations failed
            failed_translations = [r for r in translation_results if not r.get('success')]
            
            result = {
                'success': True,
                'translated_summary': translated_summary,
                'source_language': source_language,
                'target_language': target_language,
                'language_name': self.supported_languages[target_language]['name'],
                'sections_translated': sections_translated,
                'overall_confidence': overall_confidence,
                'failed_sections': len(failed_translations),
                'timestamp': datetime.now().isoformat()
            }
            
            if failed_translations:
                result['warnings'] = [f"Failed to translate {len(failed_translations)} sections"]
                result['failed_details'] = failed_translations
            
            logger.info(f"Translated document summary to {target_language}: {sections_translated} sections")
            return result
            
        except Exception as e:
            logger.error(f"Error translating document summary: {e}")
            return {
                'success': False,
                'error': f'Document summary translation failed: {str(e)}',
                'fallback_summary': summary_content  # Return original as fallback
            }
    
    async def calculate_confidence_score(
        self, 
        original_text: str, 
        translated_text: str, 
        section_type: str
    ) -> float:
        """Calculate confidence score for translation quality"""
        try:
            # Basic confidence calculation based on various factors
            confidence = 0.8  # Base confidence for Google Translate
            
            # Length similarity factor
            length_ratio = len(translated_text) / len(original_text) if len(original_text) > 0 else 0
            if 0.5 <= length_ratio <= 2.0:  # Reasonable length ratio
                confidence += 0.1
            
            # Section-specific adjustments
            if section_type in ['key_points', 'recommendations']:
                # Lists tend to translate more reliably
                confidence += 0.05
            elif section_type == 'risk_assessment':
                # Risk assessments contain more technical terms
                confidence -= 0.05
            
            # Ensure confidence is within bounds
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.7  # Default confidence
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Get all supported languages with metadata"""
        return self.supported_languages.copy()
    
    def get_language_info(self, language_code: str) -> Optional[Dict[str, str]]:
        """Get information about a specific language"""
        return self.supported_languages.get(language_code)
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in self.supported_languages
    
    async def get_usage_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get usage statistics for monitoring"""
        today = datetime.now().date().isoformat()
        daily_stats = self.daily_usage.get(today, {'requests': 0, 'characters': 0})
        
        stats = {
            'daily_requests': daily_stats['requests'],
            'daily_characters': daily_stats['characters'],
            'daily_request_limit': self.daily_request_limit,
            'daily_character_limit': self.daily_character_limit,
            'supported_languages_count': len(self.supported_languages),
            'cache_ttl_hours': self.translation_cache_ttl / 3600
        }
        
        if user_id and user_id in self.rate_limits:
            user_limit = self.rate_limits[user_id]
            stats['user_requests_in_window'] = user_limit['count']
            stats['user_rate_limit'] = self.rate_limit_max
        
        return stats