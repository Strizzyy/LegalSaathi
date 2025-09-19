"""
Google Cloud Translate Service for Multilingual Support
Uses Google Cloud Translate API for document translation
"""

import os
import requests
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from google.cloud import translate_v2 as translate
import logging

logger = logging.getLogger(__name__)

@dataclass
class TranslationResult:
    success: bool
    translated_text: str
    source_language: str
    target_language: str
    language_name: str
    error_message: Optional[str] = None

class GoogleTranslateService:
    """
    Google Cloud Translate service with proper authentication
    Supports English, Hindi, and regional languages
    """
    
    def __init__(self):
        # Set up authentication
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            self.client = translate.Client()
            self.enabled = True
            self.cloud_enabled = True
            logger.info("Google Cloud Translate service initialized successfully")
        except Exception as e:
            logger.warning(f"Google Cloud Translate not available, using fallback: {e}")
            self.enabled = True  # Still enabled via fallback
            self.cloud_enabled = False
            self.client = None
        # Language codes and names mapping
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi (हिंदी)',
            'es': 'Spanish (Español)',
            'fr': 'French (Français)',
            'de': 'German (Deutsch)',
            'zh': 'Chinese (中文)',
            'ar': 'Arabic (العربية)',
            'pt': 'Portuguese (Português)',
            'ru': 'Russian (Русский)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'it': 'Italian (Italiano)',
            'nl': 'Dutch (Nederlands)',
            'sv': 'Swedish (Svenska)',
            'da': 'Danish (Dansk)',
            'no': 'Norwegian (Norsk)',
            'fi': 'Finnish (Suomi)',
            'pl': 'Polish (Polski)',
            'cs': 'Czech (Čeština)',
            'hu': 'Hungarian (Magyar)',
            'ro': 'Romanian (Română)',
            'bg': 'Bulgarian (Български)',
            'hr': 'Croatian (Hrvatski)',
            'sk': 'Slovak (Slovenčina)',
            'sl': 'Slovenian (Slovenščina)',
            'et': 'Estonian (Eesti)',
            'lv': 'Latvian (Latviešu)',
            'lt': 'Lithuanian (Lietuvių)',
            'mt': 'Maltese (Malti)',
            'ga': 'Irish (Gaeilge)',
            'cy': 'Welsh (Cymraeg)',
            'eu': 'Basque (Euskera)',
            'ca': 'Catalan (Català)',
            'gl': 'Galician (Galego)',
            'is': 'Icelandic (Íslenska)',
            'mk': 'Macedonian (Македонски)',
            'sq': 'Albanian (Shqip)',
            'sr': 'Serbian (Српски)',
            'bs': 'Bosnian (Bosanski)',
            'me': 'Montenegrin (Crnogorski)',
            'tr': 'Turkish (Türkçe)',
            'he': 'Hebrew (עברית)',
            'fa': 'Persian (فارسی)',
            'ur': 'Urdu (اردو)',
            'bn': 'Bengali (বাংলা)',
            'ta': 'Tamil (தமிழ்)',
            'te': 'Telugu (తెలుగు)',
            'ml': 'Malayalam (മലയാളം)',
            'kn': 'Kannada (ಕನ್ನಡ)',
            'gu': 'Gujarati (ગુજરાતી)',
            'pa': 'Punjabi (ਪੰਜਾਬੀ)',
            'or': 'Odia (ଓଡ଼ିଆ)',
            'as': 'Assamese (অসমীয়া)',
            'mr': 'Marathi (मराठी)',
            'ne': 'Nepali (नेपाली)',
            'si': 'Sinhala (සිංහල)',
            'my': 'Myanmar (မြန်မာ)',
            'km': 'Khmer (ខ្មែរ)',
            'lo': 'Lao (ລາວ)',
            'th': 'Thai (ไทย)',
            'vi': 'Vietnamese (Tiếng Việt)',
            'id': 'Indonesian (Bahasa Indonesia)',
            'ms': 'Malay (Bahasa Melayu)',
            'tl': 'Filipino (Tagalog)',
            'sw': 'Swahili (Kiswahili)',
            'am': 'Amharic (አማርኛ)',
            'yo': 'Yoruba',
            'ig': 'Igbo',
            'ha': 'Hausa',
            'zu': 'Zulu',
            'af': 'Afrikaans',
            'xh': 'Xhosa'
        }
        
        # Google Cloud Translate API endpoint
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
        
    def translate_text(self, text: str, target_language: str = 'hi', source_language: str = 'auto') -> Dict[str, Any]:
        """
        Translate text using Google Cloud Translate API
        
        Args:
            text: Text to translate
            target_language: Target language code (default: Hindi)
            source_language: Source language code (default: auto-detect)
            
        Returns:
            Dictionary with translation result
        """
        if not self.cloud_enabled:
            return self._fallback_translation(text, target_language, source_language)
        
        try:
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'No text provided for translation'
                }
            
            if target_language not in self.supported_languages:
                return {
                    'success': False,
                    'error': f'Unsupported target language: {target_language}'
                }
            
            # Use Google Cloud Translate API
            if source_language == 'auto':
                # Auto-detect source language
                result = self.client.translate(
                    text[:5000],  # Limit text length
                    target_language=target_language
                )
                detected_language = result.get('detectedSourceLanguage', 'unknown')
            else:
                # Specify source language
                result = self.client.translate(
                    text[:5000],
                    target_language=target_language,
                    source_language=source_language
                )
                detected_language = source_language
            
            return {
                'success': True,
                'translated_text': result['translatedText'],
                'source_language': detected_language,
                'target_language': target_language,
                'language_name': self.supported_languages.get(target_language, target_language)
            }
            
        except Exception as e:
            logger.error(f"Google Cloud Translate error: {e}")
            return self._fallback_translation(text, target_language, source_language)
    
    def _fallback_translation(self, text: str, target_language: str, source_language: str) -> Dict[str, Any]:
        """Fallback translation using free API when Google Cloud is unavailable"""
        try:
            # Prepare parameters for free Google Translate API
            params = {
                'client': 'gtx',
                'sl': source_language,
                'tl': target_language,
                'dt': 't',
                'q': text[:5000]  # Limit text length
            }
            
            # Make request to free Google Translate
            response = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params=params,
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200:
                # Parse response
                result = response.json()
                
                if result and len(result) > 0 and result[0]:
                    # Extract translated text
                    translated_text = ''
                    for item in result[0]:
                        if item and len(item) > 0:
                            translated_text += item[0]
                    
                    # Detect source language if auto-detected
                    detected_language = source_language
                    if len(result) > 2 and result[2]:
                        detected_language = result[2]
                    
                    return {
                        'success': True,
                        'translated_text': translated_text,
                        'source_language': detected_language,
                        'target_language': target_language,
                        'language_name': self.supported_languages.get(target_language, target_language),
                        'fallback': True
                    }
            
            return {
                'success': False,
                'error': f'Translation service returned status {response.status_code}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Translation error: {str(e)}'
            }
    
    def translate_risk_assessment(self, assessment: Dict[str, Any], target_language: str = 'hi') -> Dict[str, Any]:
        """
        Translate an entire risk assessment result
        
        Args:
            assessment: Risk assessment dictionary
            target_language: Target language code
            
        Returns:
            Translated assessment dictionary
        """
        try:
            translated_assessment = assessment.copy()
            
            # Translate summary
            if 'summary' in assessment:
                summary_result = self.translate_text(assessment['summary'], target_language)
                if summary_result['success']:
                    translated_assessment['summary'] = summary_result['translated_text']
            
            # Translate clause explanations
            if 'analysis_results' in assessment:
                for i, result in enumerate(assessment['analysis_results']):
                    if 'plain_explanation' in result:
                        explanation_result = self.translate_text(result['plain_explanation'], target_language)
                        if explanation_result['success']:
                            translated_assessment['analysis_results'][i]['plain_explanation'] = explanation_result['translated_text']
                    
                    # Translate recommendations
                    if 'recommendations' in result and isinstance(result['recommendations'], list):
                        translated_recommendations = []
                        for rec in result['recommendations']:
                            rec_result = self.translate_text(rec, target_language)
                            if rec_result['success']:
                                translated_recommendations.append(rec_result['translated_text'])
                            else:
                                translated_recommendations.append(rec)
                        translated_assessment['analysis_results'][i]['recommendations'] = translated_recommendations
            
            return translated_assessment
            
        except Exception as e:
            print(f"Error translating assessment: {e}")
            return assessment  # Return original if translation fails
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported language codes and names"""
        return self.supported_languages.copy()
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of given text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language information
        """
        try:
            # Use translation with auto-detect to get source language
            result = self.translate_text(text, target_language='en', source_language='auto')
            
            if result['success']:
                detected_lang = result['source_language']
                return {
                    'success': True,
                    'language_code': detected_lang,
                    'language_name': self.supported_languages.get(detected_lang, detected_lang),
                    'confidence': 0.8  # Approximate confidence
                }
            else:
                return {
                    'success': False,
                    'error': 'Language detection failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Language detection error: {str(e)}'
            }
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language code is supported"""
        return language_code in self.supported_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Get the display name for a language code"""
        return self.supported_languages.get(language_code, language_code)