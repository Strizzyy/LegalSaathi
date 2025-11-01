"""
Consolidated Google Cloud Services
Combines Vision, Document AI, Natural Language, Speech, and Translate services
"""

import os
import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Import Google Cloud libraries
try:
    from google.cloud import vision
    from google.cloud import documentai
    from google.cloud import language_v1
    from google.cloud import speech
    from google.cloud import texttospeech
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logger.warning("Google Cloud libraries not available")

class GoogleCloudServices:
    """Consolidated Google Cloud services for document processing"""
    
    def __init__(self):
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning("Google Cloud services not available")
            return
        
        # Initialize clients
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.language_client = language_v1.LanguageServiceClient()
            self.speech_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            self.translate_client = translate.Client()
            
            # Document AI client (if configured)
            self.document_ai_client = None
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if project_id:
                try:
                    self.document_ai_client = documentai.DocumentProcessorServiceClient()
                    self.processor_name = os.getenv('DOCUMENT_AI_PROCESSOR_NAME')
                    self.processor_location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
                    logger.info("✅ Document AI client initialized")
                except Exception as e:
                    logger.warning(f"Document AI initialization failed: {e}")
            
            # File type routing for dual vision processing
            self.pdf_mime_types = {'application/pdf'}
            self.image_mime_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
            
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if project_id:
                self.document_ai_client = documentai.DocumentProcessorServiceClient()
                self.project_id = project_id
                self.processor_location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
            
            logger.info("✅ Google Cloud services initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud services: {e}")
    
    # Vision API Methods
    async def extract_text_from_image(self, image_content: bytes, preprocess: bool = True) -> Dict[str, Any]:
        """Extract text from image using Vision API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Vision not available'}
            
            image = vision.Image(content=image_content)
            response = self.vision_client.text_detection(image=image)
            
            if response.error.message:
                return {'success': False, 'error': response.error.message}
            
            texts = response.text_annotations
            if not texts:
                return {'success': False, 'error': 'No text found in image'}
            
            # First annotation contains all text
            full_text = texts[0].description
            
            # Individual text blocks
            text_blocks = []
            for text in texts[1:]:  # Skip first (full text)
                vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
                text_blocks.append({
                    'text': text.description,
                    'confidence': getattr(text, 'confidence', 0.9),
                    'bounding_box': vertices
                })
            
            return {
                'success': True,
                'full_text': full_text,
                'text_blocks': text_blocks,
                'total_blocks': len(text_blocks),
                'service_used': 'google_vision'
            }
            
        except Exception as e:
            logger.error(f"Vision API text extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_document_structure(self, image_content: bytes) -> Dict[str, Any]:
        """Analyze document structure using Vision API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Vision not available'}
            
            image = vision.Image(content=image_content)
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                return {'success': False, 'error': response.error.message}
            
            document = response.full_text_annotation
            if not document:
                return {'success': False, 'error': 'No document structure found'}
            
            # Extract pages, blocks, paragraphs
            pages = []
            for page in document.pages:
                page_info = {
                    'width': page.width,
                    'height': page.height,
                    'blocks': len(page.blocks),
                    'confidence': page.confidence
                }
                pages.append(page_info)
            
            return {
                'success': True,
                'text': document.text,
                'pages': pages,
                'total_pages': len(pages),
                'service_used': 'google_vision_document'
            }
            
        except Exception as e:
            logger.error(f"Document structure analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Document AI Methods
    async def process_document_ai(self, document_content: bytes, mime_type: str) -> Dict[str, Any]:
        """Process document using Document AI"""
        try:
            if not self.document_ai_client:
                return {'success': False, 'error': 'Document AI not configured'}
            
            # Use a general processor (you'd need to create this in Google Cloud Console)
            processor_name = f"projects/{self.project_id}/locations/{self.processor_location}/processors/general"
            
            raw_document = documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
            
            request = documentai.ProcessRequest(
                name=processor_name,
                raw_document=raw_document
            )
            
            result = self.document_ai_client.process_document(request=request)
            document = result.document
            
            # Extract entities and text
            entities = []
            for entity in document.entities:
                entities.append({
                    'type': entity.type_,
                    'text': entity.text_anchor.content if entity.text_anchor else '',
                    'confidence': entity.confidence
                })
            
            return {
                'success': True,
                'text': document.text,
                'entities': entities,
                'pages': len(document.pages),
                'service_used': 'google_document_ai'
            }
            
        except Exception as e:
            logger.error(f"Document AI processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Natural Language Methods
    async def analyze_legal_entities(self, text: str) -> Dict[str, Any]:
        """Analyze legal entities in text using Natural Language API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Natural Language not available'}
            
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Entity analysis
            entities_response = self.language_client.analyze_entities(
                request={'document': document, 'encoding_type': language_v1.EncodingType.UTF8}
            )
            
            entities = []
            for entity in entities_response.entities:
                entities.append({
                    'name': entity.name,
                    'type': entity.type_.name,
                    'salience': entity.salience,
                    'mentions': [mention.text.content for mention in entity.mentions]
                })
            
            # Sentiment analysis
            sentiment_response = self.language_client.analyze_sentiment(
                request={'document': document}
            )
            
            return {
                'success': True,
                'entities': entities,
                'sentiment': {
                    'score': sentiment_response.document_sentiment.score,
                    'magnitude': sentiment_response.document_sentiment.magnitude
                },
                'language': entities_response.language,
                'service_used': 'google_natural_language'
            }
            
        except Exception as e:
            logger.error(f"Natural Language analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Speech Methods
    async def speech_to_text(self, audio_content: bytes, language_code: str = "en-US") -> Dict[str, Any]:
        """Convert speech to text using Speech API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Speech not available'}
            
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            transcripts = []
            for result in response.results:
                transcripts.append({
                    'transcript': result.alternatives[0].transcript,
                    'confidence': result.alternatives[0].confidence
                })
            
            return {
                'success': True,
                'transcripts': transcripts,
                'full_transcript': ' '.join([t['transcript'] for t in transcripts]),
                'service_used': 'google_speech'
            }
            
        except Exception as e:
            logger.error(f"Speech to text failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def text_to_speech(self, text: str, language_code: str = "en-US") -> Dict[str, Any]:
        """Convert text to speech using Text-to-Speech API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Text-to-Speech not available'}
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return {
                'success': True,
                'audio_content': base64.b64encode(response.audio_content).decode('utf-8'),
                'audio_format': 'mp3',
                'service_used': 'google_tts'
            }
            
        except Exception as e:
            logger.error(f"Text to speech failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Translation Methods
    async def translate_text(self, text: str, target_language: str, source_language: str = None) -> Dict[str, Any]:
        """Translate text using Translate API"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Translate not available'}
            
            result = self.translate_client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            
            return {
                'success': True,
                'translated_text': result['translatedText'],
                'detected_source_language': result.get('detectedSourceLanguage'),
                'target_language': target_language,
                'service_used': 'google_translate'
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get supported languages for translation"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return {'success': False, 'error': 'Google Cloud Translate not available'}
            
            results = self.translate_client.get_languages()
            
            languages = []
            for language in results:
                languages.append({
                    'code': language['language'],
                    'name': language.get('name', language['language'])
                })
            
            return {
                'success': True,
                'languages': languages,
                'total_languages': len(languages),
                'service_used': 'google_translate'
            }
            
        except Exception as e:
            logger.error(f"Get supported languages failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Dual Vision Processing Methods
    async def process_document_intelligent(self, file_content: bytes, mime_type: str, filename: str = "") -> Dict[str, Any]:
        """Intelligently process document using optimal method based on file type"""
        start_time = time.time()
        
        try:
            # Route based on file type
            if mime_type in getattr(self, 'pdf_mime_types', {'application/pdf'}) and self.document_ai_client:
                # Use Document AI for PDFs
                result = await self._process_with_document_ai(file_content, mime_type)
                method_used = "document_ai"
            elif mime_type in getattr(self, 'image_mime_types', {'image/jpeg', 'image/png', 'image/webp'}) and hasattr(self, 'vision_client'):
                # Use Vision API for images
                result = await self._process_with_vision_api(file_content)
                method_used = "vision_api"
            else:
                # Fallback to basic text extraction
                result = await self._process_with_fallback(file_content, mime_type)
                method_used = "fallback"
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "text": result.get("text", ""),
                "method_used": method_used,
                "processing_time": processing_time,
                "confidence_scores": result.get("confidence_scores", {}),
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method_used": "error",
                "processing_time": time.time() - start_time
            }
    
    async def _process_with_fallback(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """Fallback processing for unsupported file types"""
        try:
            # Basic text extraction for PDFs
            if mime_type == 'application/pdf':
                try:
                    import PyPDF2
                    import io
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    return {
                        "text": text,
                        "confidence_scores": {"fallback": 0.6},
                        "metadata": {"processor": "pypdf2_fallback", "pages": len(pdf_reader.pages)}
                    }
                except Exception as e:
                    logger.warning(f"PDF fallback failed: {e}")
            
            # For other file types, return empty result
            return {
                "text": "",
                "confidence_scores": {"fallback": 0.0},
                "metadata": {"processor": "no_extraction", "error": "Unsupported file type"}
            }
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return {
                "text": "",
                "confidence_scores": {"error": 0.0},
                "metadata": {"processor": "error", "error": str(e)}
            }
    
    # Utility Methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all Google Cloud services"""
        return {
            'google_cloud_available': GOOGLE_CLOUD_AVAILABLE,
            'vision_available': hasattr(self, 'vision_client'),
            'document_ai_available': self.document_ai_client is not None,
            'natural_language_available': hasattr(self, 'language_client'),
            'speech_available': hasattr(self, 'speech_client'),
            'translate_available': hasattr(self, 'translate_client'),
            'is_cloud_run': self.is_cloud_run,
            'project_id': getattr(self, 'project_id', None)
        }


# Global instance
_google_cloud_services = None

def get_google_cloud_services() -> GoogleCloudServices:
    """Get global Google Cloud services instance"""
    global _google_cloud_services
    if _google_cloud_services is None:
        _google_cloud_services = GoogleCloudServices()
    return _google_cloud_services