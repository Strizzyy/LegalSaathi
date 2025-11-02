"""
Enhanced Google Cloud Speech Services for Voice Input/Output
Comprehensive speech-to-text and text-to-speech implementation with
audio validation, caching, cost monitoring, and multi-language support
"""

import os
import io
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from google.cloud import speech
from google.cloud import texttospeech
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import wave
import struct

logger = logging.getLogger(__name__)

class AudioCache:
    """Audio caching system to reduce API calls and improve performance"""
    
    def __init__(self, ttl: int = 3600):  # 1 hour TTL
        self.cache = {}
        self.ttl = ttl
    
    def _generate_key(self, text: str, language_code: str, voice_params: Dict[str, Any]) -> str:
        """Generate cache key for audio content"""
        content = f"{text}:{language_code}:{voice_params}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, language_code: str, voice_params: Dict[str, Any]) -> Optional[bytes]:
        """Get cached audio content"""
        key = self._generate_key(text, language_code, voice_params)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.info(f"Audio cache hit for key: {key[:8]}...")
                return cached_data
            else:
                del self.cache[key]
        return None
    
    def set(self, text: str, language_code: str, voice_params: Dict[str, Any], audio_content: bytes):
        """Cache audio content"""
        key = self._generate_key(text, language_code, voice_params)
        self.cache[key] = (audio_content, time.time())
        logger.info(f"Cached audio for key: {key[:8]}...")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired audio cache entries")

class CostMonitor:
    """Cost monitoring and daily usage limits for Google Cloud APIs"""
    
    def __init__(self):
        self.daily_limits = {
            'speech_to_text': 300,  # requests per day
            'text_to_speech': 200,  # requests per day
        }
        self.usage_stats = defaultdict(lambda: defaultdict(int))
        self.last_reset = datetime.now().date()
    
    def _reset_daily_stats_if_needed(self):
        """Reset daily stats if it's a new day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.usage_stats.clear()
            self.last_reset = today
            logger.info("Daily usage stats reset")
    
    def check_daily_limit(self, service: str, user_id: str = "anonymous") -> bool:
        """Check if daily limit is exceeded"""
        self._reset_daily_stats_if_needed()
        current_usage = self.usage_stats[service][user_id]
        limit = self.daily_limits.get(service, float('inf'))
        return current_usage < limit
    
    def increment_usage(self, service: str, user_id: str = "anonymous"):
        """Increment usage counter"""
        self._reset_daily_stats_if_needed()
        self.usage_stats[service][user_id] += 1
        logger.info(f"Usage incremented for {service} - user: {user_id}, count: {self.usage_stats[service][user_id]}")
    
    def get_usage_stats(self, user_id: str = "anonymous") -> Dict[str, Any]:
        """Get usage statistics for a user"""
        self._reset_daily_stats_if_needed()
        return {
            'speech_to_text': {
                'used': self.usage_stats['speech_to_text'][user_id],
                'limit': self.daily_limits['speech_to_text'],
                'remaining': max(0, self.daily_limits['speech_to_text'] - self.usage_stats['speech_to_text'][user_id])
            },
            'text_to_speech': {
                'used': self.usage_stats['text_to_speech'][user_id],
                'limit': self.daily_limits['text_to_speech'],
                'remaining': max(0, self.daily_limits['text_to_speech'] - self.usage_stats['text_to_speech'][user_id])
            },
            'reset_date': self.last_reset.isoformat()
        }

class EnhancedGoogleCloudSpeechService:
    """
    Enhanced Google Cloud Speech services for voice input/output
    Supports multiple languages, neural voices, legal terminology,
    audio validation, caching, cost monitoring, and rate limiting
    """
    
    def __init__(self):
        try:
            # Set up authentication
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-cloud-credentials.json')
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            else:
                logger.warning(f"Google Cloud credentials not found at {credentials_path}")
            
            # Initialize both speech clients
            self.speech_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            self.enabled = True
            
            # Initialize enhanced features
            self.audio_cache = AudioCache()
            self.cost_monitor = CostMonitor()
            self.supported_formats = ['webm', 'wav', 'mp3', 'ogg']
            self.max_file_size = 10 * 1024 * 1024  # 10MB
            self.max_duration = 300  # 5 minutes
            
            # Language-specific voice mapping
            self.voice_mapping = {
                'en-US': {'MALE': 'en-US-Neural2-D', 'FEMALE': 'en-US-Neural2-F', 'NEUTRAL': 'en-US-Neural2-C'},
                'hi-IN': {'MALE': 'hi-IN-Neural2-B', 'FEMALE': 'hi-IN-Neural2-A', 'NEUTRAL': 'hi-IN-Neural2-C'},
                'es-US': {'MALE': 'es-US-Neural2-B', 'FEMALE': 'es-US-Neural2-A', 'NEUTRAL': 'es-US-Neural2-C'},
                'fr-FR': {'MALE': 'fr-FR-Neural2-B', 'FEMALE': 'fr-FR-Neural2-A', 'NEUTRAL': 'fr-FR-Neural2-C'},
                'de-DE': {'MALE': 'de-DE-Neural2-B', 'FEMALE': 'de-DE-Neural2-A', 'NEUTRAL': 'de-DE-Neural2-C'},
                'it-IT': {'MALE': 'it-IT-Neural2-C', 'FEMALE': 'it-IT-Neural2-A', 'NEUTRAL': 'it-IT-Neural2-B'},
                'pt-BR': {'MALE': 'pt-BR-Neural2-B', 'FEMALE': 'pt-BR-Neural2-A', 'NEUTRAL': 'pt-BR-Neural2-C'},
                'ja-JP': {'MALE': 'ja-JP-Neural2-C', 'FEMALE': 'ja-JP-Neural2-B', 'NEUTRAL': 'ja-JP-Neural2-D'},
                'ko-KR': {'MALE': 'ko-KR-Neural2-C', 'FEMALE': 'ko-KR-Neural2-A', 'NEUTRAL': 'ko-KR-Neural2-B'},
                'zh-CN': {'MALE': 'zh-CN-Neural2-C', 'FEMALE': 'zh-CN-Neural2-A', 'NEUTRAL': 'zh-CN-Neural2-B'}
            }
            
            logger.info("Enhanced Google Cloud Speech services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Google Cloud Speech services: {e}")
            self.enabled = False
            self.speech_client = None
            self.tts_client = None
            self.audio_cache = None
            self.cost_monitor = None
    
    def validate_audio_file(self, audio_content: bytes, filename: str = "") -> Tuple[bool, str]:
        """
        Validate audio file format, size, and duration
        
        Args:
            audio_content: Raw audio bytes
            filename: Original filename for format detection
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            if len(audio_content) > self.max_file_size:
                return False, f"Audio file too large (max {self.max_file_size // (1024*1024)}MB)"
            
            if len(audio_content) == 0:
                return False, "Empty audio file"
            
            # Check file format based on filename extension
            if filename:
                file_ext = filename.lower().split('.')[-1]
                if file_ext not in self.supported_formats:
                    return False, f"Unsupported audio format. Supported: {', '.join(self.supported_formats)}"
            
            # Basic audio content validation
            if filename.lower().endswith('.wav'):
                # Validate WAV file structure
                if len(audio_content) < 44:  # WAV header is 44 bytes
                    return False, "Invalid WAV file structure"
                
                # Check WAV header
                if audio_content[:4] != b'RIFF' or audio_content[8:12] != b'WAVE':
                    return False, "Invalid WAV file header"
                
                # Extract duration from WAV header (approximate)
                try:
                    sample_rate = struct.unpack('<I', audio_content[24:28])[0]
                    byte_rate = struct.unpack('<I', audio_content[28:32])[0]
                    if byte_rate > 0:
                        duration = len(audio_content) / byte_rate
                        if duration > self.max_duration:
                            return False, f"Audio too long (max {self.max_duration} seconds)"
                except:
                    pass  # Continue if duration check fails
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            return False, f"Audio validation failed: {str(e)}"
    
    async def verify_credentials(self) -> bool:
        """Verify if Google Cloud Speech credentials are valid and services are accessible"""
        if not self.enabled:
            return False
            
        try:
            # Try to list available voices to verify Text-to-Speech
            self.tts_client.list_voices()
            
            # Create a simple config to verify Speech-to-Text
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            
            # If we can create the config and list voices, the service is accessible
            return True
        except Exception as e:
            logger.error(f"Speech service verification failed: {e}")
            return False
    

    
    def speech_to_text(self, audio_content: bytes, language_code: str = 'en-US', 
                      enable_punctuation: bool = True, user_id: str = "anonymous", 
                      filename: str = "") -> Dict[str, Any]:
        """
        Convert speech to text for legal document input with enhanced validation and error handling
        
        Args:
            audio_content: Raw audio bytes
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            enable_punctuation: Enable automatic punctuation
            user_id: User ID for rate limiting and cost monitoring
            filename: Original filename for format validation
            
        Returns:
            Dict containing transcription results and confidence scores
        """
        if not self.enabled or not self.speech_client:
            return self._fallback_transcription("Speech service not available")
        
        # Check daily usage limits
        if not self.cost_monitor.check_daily_limit('speech_to_text', user_id):
            return self._fallback_transcription("Daily speech-to-text limit exceeded")
        
        # Validate audio file
        is_valid, error_msg = self.validate_audio_file(audio_content, filename)
        if not is_valid:
            return self._fallback_transcription(f"Audio validation failed: {error_msg}")
        
        start_time = time.time()
        
        try:
            # Configure recognition settings for legal content
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                alternative_language_codes=['hi-IN', 'en-IN', 'es-US'],  # Support multiple languages
                enable_automatic_punctuation=enable_punctuation,
                enable_word_confidence=True,
                enable_word_time_offsets=True,
                model='latest_long',  # Best for longer audio
                use_enhanced=True,  # Enhanced model for better accuracy
                # Add legal terminology hints
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=[
                            'contract', 'agreement', 'clause', 'liability', 'indemnification',
                            'termination', 'breach', 'damages', 'warranty', 'representation',
                            'jurisdiction', 'arbitration', 'confidentiality', 'non-disclosure',
                            'intellectual property', 'force majeure', 'governing law',
                            'rental agreement', 'employment contract', 'lease', 'tenant', 'landlord'
                        ],
                        boost=15.0  # Boost recognition of legal terms
                    )
                ]
            )
            
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Perform transcription with timeout handling
            try:
                response = self.speech_client.recognize(config=config, audio=audio)
            except Exception as api_error:
                logger.error(f"Speech API error: {api_error}")
                return self._fallback_transcription(f"Speech recognition API error: {str(api_error)}")
            
            # Process results
            transcription_results = []
            best_transcript = ""
            overall_confidence = 0.0
            
            for result in response.results:
                alternative = result.alternatives[0]
                
                transcription_results.append({
                    'transcript': alternative.transcript,
                    'confidence': alternative.confidence,
                    'words': [
                        {
                            'word': word.word,
                            'confidence': word.confidence,
                            'start_time': word.start_time.total_seconds(),
                            'end_time': word.end_time.total_seconds()
                        }
                        for word in alternative.words
                    ]
                })
                
                if alternative.confidence > overall_confidence:
                    best_transcript = alternative.transcript
                    overall_confidence = alternative.confidence
            
            processing_time = time.time() - start_time
            
            # Increment usage counter
            self.cost_monitor.increment_usage('speech_to_text', user_id)
            
            # Analyze transcription quality
            quality_assessment = self._assess_transcription_quality(transcription_results)
            
            return {
                'success': True,
                'transcript': best_transcript,
                'confidence': overall_confidence,
                'language_detected': language_code,
                'processing_time': processing_time,
                'alternatives': transcription_results,
                'quality_assessment': quality_assessment,
                'legal_terms_detected': self._detect_legal_terms(best_transcript),
                'suggestions': self._get_improvement_suggestions(quality_assessment),
                'usage_stats': self.cost_monitor.get_usage_stats(user_id)
            }
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            return self._fallback_transcription(f"Transcription failed: {str(e)}")
    
    def text_to_speech(self, text: str, language_code: str = 'en-US', voice_gender: str = 'NEUTRAL', 
                      speaking_rate: float = 0.9, pitch: float = 0.0, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Convert text to speech for accessibility with caching and enhanced features
        
        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            voice_gender: Voice gender ('MALE', 'FEMALE', 'NEUTRAL')
            speaking_rate: Speaking rate (0.25 to 4.0)
            pitch: Voice pitch (-20.0 to 20.0)
            user_id: User ID for rate limiting and cost monitoring
            
        Returns:
            Dict containing audio content and metadata
        """
        if not self.enabled or not self.tts_client:
            return self._fallback_tts("Text-to-speech service not available")
        
        # Check daily usage limits
        if not self.cost_monitor.check_daily_limit('text_to_speech', user_id):
            return self._fallback_tts("Daily text-to-speech limit exceeded")
        
        # Validate text length
        if len(text) > 5000:
            return self._fallback_tts("Text too long for speech synthesis (max 5000 characters)")
        
        if not text.strip():
            return self._fallback_tts("Empty text provided")
        
        # Check cache first
        voice_params = {
            'voice_gender': voice_gender,
            'speaking_rate': speaking_rate,
            'pitch': pitch
        }
        
        cached_audio = self.audio_cache.get(text, language_code, voice_params)
        if cached_audio:
            return {
                'success': True,
                'audio_content': cached_audio,
                'language_code': language_code,
                'voice_gender': voice_gender,
                'processing_time': 0.0,
                'audio_format': 'MP3',
                'text_length': len(text),
                'estimated_duration': len(text) / (speaking_rate * 150),
                'cached': True,
                'usage_stats': self.cost_monitor.get_usage_stats(user_id)
            }
        
        start_time = time.time()
        
        try:
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice selection with neural voices using enhanced mapping
            voice_name = self.voice_mapping.get(language_code, {}).get(voice_gender)
            
            if voice_name:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name
                )
            else:
                # Fallback to standard voice
                gender_map = {
                    'MALE': texttospeech.SsmlVoiceGender.MALE,
                    'FEMALE': texttospeech.SsmlVoiceGender.FEMALE,
                    'NEUTRAL': texttospeech.SsmlVoiceGender.NEUTRAL
                }
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    ssml_gender=gender_map.get(voice_gender, texttospeech.SsmlVoiceGender.NEUTRAL)
                )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch,
                effects_profile_id=['telephony-class-application']  # Optimize for clarity
            )
            
            # Perform text-to-speech synthesis with timeout handling
            try:
                response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            except Exception as api_error:
                logger.error(f"TTS API error: {api_error}")
                return self._fallback_tts(f"Text-to-speech API error: {str(api_error)}")
            
            processing_time = time.time() - start_time
            
            # Cache the result
            self.audio_cache.set(text, language_code, voice_params, response.audio_content)
            
            # Increment usage counter
            self.cost_monitor.increment_usage('text_to_speech', user_id)
            
            return {
                'success': True,
                'audio_content': response.audio_content,
                'language_code': language_code,
                'voice_gender': voice_gender,
                'processing_time': processing_time,
                'audio_format': 'MP3',
                'text_length': len(text),
                'estimated_duration': len(text) / (speaking_rate * 150),
                'cached': False,
                'usage_stats': self.cost_monitor.get_usage_stats(user_id)
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {e}")
            return self._fallback_tts(f"TTS synthesis failed: {str(e)}")
    
    def transcribe_streaming(self, audio_generator, language_code: str = 'en-US') -> Dict[str, Any]:
        """
        Real-time streaming transcription for live voice input
        
        Args:
            audio_generator: Generator yielding audio chunks
            language_code: Language code for recognition
            
        Returns:
            Dict containing streaming transcription results
        """
        if not self.enabled:
            return self._fallback_transcription()
        
        try:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='latest_short'  # Optimized for short utterances
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True,
                single_utterance=False
            )
            
            # Create streaming request generator
            def request_generator():
                yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
                for chunk in audio_generator:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            # Perform streaming recognition
            responses = self.client.streaming_recognize(request_generator())
            
            final_transcript = ""
            interim_results = []
            
            for response in responses:
                for result in response.results:
                    if result.is_final:
                        final_transcript += result.alternatives[0].transcript + " "
                    else:
                        interim_results.append({
                            'transcript': result.alternatives[0].transcript,
                            'confidence': result.alternatives[0].confidence,
                            'is_final': result.is_final
                        })
            
            return {
                'success': True,
                'final_transcript': final_transcript.strip(),
                'interim_results': interim_results,
                'language_detected': language_code
            }
            
        except Exception as e:
            logger.error(f"Streaming transcription failed: {e}")
            return self._fallback_transcription()
    
    def _assess_transcription_quality(self, results: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of transcription results"""
        if not results:
            return {'overall_quality': 'poor', 'confidence_score': 0.0}
        
        # Calculate average confidence
        confidences = [r['confidence'] for r in results if r['confidence'] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Assess word-level confidence
        low_confidence_words = 0
        total_words = 0
        
        for result in results:
            for word in result.get('words', []):
                total_words += 1
                if word['confidence'] < 0.7:
                    low_confidence_words += 1
        
        low_confidence_ratio = low_confidence_words / total_words if total_words > 0 else 0.0
        
        # Determine overall quality
        if avg_confidence > 0.8 and low_confidence_ratio < 0.2:
            quality = 'excellent'
        elif avg_confidence > 0.6 and low_confidence_ratio < 0.4:
            quality = 'good'
        elif avg_confidence > 0.4:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'overall_quality': quality,
            'confidence_score': avg_confidence,
            'low_confidence_ratio': low_confidence_ratio,
            'total_words': total_words,
            'unclear_words': low_confidence_words
        }
    
    def _detect_legal_terms(self, transcript: str) -> List[Dict[str, Any]]:
        """Detect legal terms in the transcript"""
        legal_terms = {
            'contract terms': ['contract', 'agreement', 'terms', 'conditions'],
            'liability': ['liability', 'liable', 'responsible', 'damages'],
            'termination': ['terminate', 'termination', 'end', 'cancel'],
            'confidentiality': ['confidential', 'non-disclosure', 'nda', 'secret'],
            'intellectual property': ['intellectual property', 'copyright', 'trademark', 'patent'],
            'dispute resolution': ['arbitration', 'mediation', 'dispute', 'court'],
            'payment terms': ['payment', 'fee', 'cost', 'price', 'compensation']
        }
        
        detected_terms = []
        transcript_lower = transcript.lower()
        
        for category, terms in legal_terms.items():
            for term in terms:
                if term in transcript_lower:
                    detected_terms.append({
                        'category': category,
                        'term': term,
                        'found_in_context': self._extract_context(transcript, term)
                    })
        
        return detected_terms
    
    def _extract_context(self, text: str, term: str, context_words: int = 5) -> str:
        """Extract context around a found term"""
        words = text.split()
        term_lower = term.lower()
        
        for i, word in enumerate(words):
            if term_lower in word.lower():
                start = max(0, i - context_words)
                end = min(len(words), i + context_words + 1)
                return ' '.join(words[start:end])
        
        return ""
    
    def _get_improvement_suggestions(self, quality_assessment: Dict) -> List[str]:
        """Get suggestions for improving transcription quality"""
        suggestions = []
        
        if quality_assessment['overall_quality'] == 'poor':
            suggestions.extend([
                "Speak more clearly and slowly",
                "Reduce background noise",
                "Use a better microphone",
                "Speak closer to the microphone"
            ])
        elif quality_assessment['overall_quality'] == 'fair':
            suggestions.extend([
                "Speak more distinctly",
                "Pause between sentences",
                "Spell out complex legal terms if needed"
            ])
        elif quality_assessment['low_confidence_ratio'] > 0.3:
            suggestions.append("Some words were unclear - consider repeating unclear sections")
        
        if quality_assessment['unclear_words'] > 10:
            suggestions.append("Many words were unclear - try speaking in shorter segments")
        
        return suggestions
    
    def _fallback_transcription(self, error_message: str = 'Google Speech-to-Text not available - please type your input') -> Dict[str, Any]:
        """Fallback when Speech-to-Text is not available"""
        return {
            'success': False,
            'transcript': "",
            'confidence': 0.0,
            'processing_time': 0.0,
            'error': error_message,
            'alternatives': [],
            'quality_assessment': {'overall_quality': 'unavailable'},
            'legal_terms_detected': [],
            'suggestions': ['Speech recognition not available - please use text input']
        }
    
    def _fallback_tts(self, error_message: str = 'Google Text-to-Speech not available') -> Dict[str, Any]:
        """Fallback when Text-to-Speech is not available"""
        return {
            'success': False,
            'audio_content': b'',
            'processing_time': 0.0,
            'error': error_message,
            'language_code': 'en-US',
            'voice_gender': 'NEUTRAL'
        }
    
    def get_usage_stats(self, user_id: str = "anonymous") -> Dict[str, Any]:
        """Get usage statistics for a user"""
        if not self.cost_monitor:
            return {'error': 'Cost monitoring not available'}
        return self.cost_monitor.get_usage_stats(user_id)
    
    def clear_audio_cache(self):
        """Clear expired audio cache entries"""
        if self.audio_cache:
            self.audio_cache.clear_expired()
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages for speech services"""
        return [
            {"code": "en-US", "name": "English (US)", "neural_voices": True},
            {"code": "en-GB", "name": "English (UK)", "neural_voices": True},
            {"code": "hi-IN", "name": "Hindi (India)", "neural_voices": True},
            {"code": "es-ES", "name": "Spanish (Spain)", "neural_voices": True},
            {"code": "es-US", "name": "Spanish (US)", "neural_voices": True},
            {"code": "fr-FR", "name": "French (France)", "neural_voices": True},
            {"code": "de-DE", "name": "German (Germany)", "neural_voices": True},
            {"code": "it-IT", "name": "Italian (Italy)", "neural_voices": True},
            {"code": "pt-BR", "name": "Portuguese (Brazil)", "neural_voices": True},
            {"code": "ru-RU", "name": "Russian (Russia)", "neural_voices": False},
            {"code": "ja-JP", "name": "Japanese (Japan)", "neural_voices": True},
            {"code": "ko-KR", "name": "Korean (South Korea)", "neural_voices": True},
            {"code": "zh-CN", "name": "Chinese (Simplified)", "neural_voices": True}
        ]

# Global instance
speech_service = EnhancedGoogleCloudSpeechService()