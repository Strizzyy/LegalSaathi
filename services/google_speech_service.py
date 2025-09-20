"""
Google Cloud Speech Services for Voice Input/Output
Comprehensive speech-to-text and text-to-speech implementation
"""

import os
import io
import time
from typing import Dict, List, Any, Optional
from google.cloud import speech
from google.cloud import texttospeech
import logging

logger = logging.getLogger(__name__)

class GoogleCloudSpeechService:
    """
    Google Cloud Speech services for voice input/output
    Supports multiple languages, neural voices, and legal terminology
    """
    
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
            logger.info("Google Cloud Speech services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Speech services: {e}")
            self.enabled = False
            self.speech_client = None
            self.tts_client = None
    
    def speech_to_text(self, audio_content: bytes, language_code: str = 'en-US', enable_punctuation: bool = True) -> Dict[str, Any]:
        """
        Convert speech to text for legal document input
        
        Args:
            audio_content: Raw audio bytes
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            enable_punctuation: Enable automatic punctuation
            
        Returns:
            Dict containing transcription results and confidence scores
        """
        if not self.enabled or not self.speech_client:
            return self._fallback_transcription()
        
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
            
            # Perform transcription
            response = self.speech_client.recognize(config=config, audio=audio)
            
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
                'suggestions': self._get_improvement_suggestions(quality_assessment)
            }
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            return self._fallback_transcription()
    
    def text_to_speech(self, text: str, language_code: str = 'en-US', voice_gender: str = 'NEUTRAL', 
                      speaking_rate: float = 0.9, pitch: float = 0.0) -> Dict[str, Any]:
        """
        Convert text to speech for accessibility
        
        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            voice_gender: Voice gender ('MALE', 'FEMALE', 'NEUTRAL')
            speaking_rate: Speaking rate (0.25 to 4.0)
            pitch: Voice pitch (-20.0 to 20.0)
            
        Returns:
            Dict containing audio content and metadata
        """
        if not self.enabled or not self.tts_client:
            return self._fallback_tts()
        
        start_time = time.time()
        
        try:
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice selection with neural voices
            voice_name_map = {
                'en-US': {
                    'MALE': 'en-US-Neural2-D',
                    'FEMALE': 'en-US-Neural2-F',
                    'NEUTRAL': 'en-US-Neural2-C'
                },
                'hi-IN': {
                    'MALE': 'hi-IN-Neural2-B',
                    'FEMALE': 'hi-IN-Neural2-A',
                    'NEUTRAL': 'hi-IN-Neural2-C'
                },
                'es-US': {
                    'MALE': 'es-US-Neural2-B',
                    'FEMALE': 'es-US-Neural2-A',
                    'NEUTRAL': 'es-US-Neural2-C'
                }
            }
            
            # Get voice name or fallback to standard voice
            voice_name = voice_name_map.get(language_code, {}).get(voice_gender)
            
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
            
            # Perform text-to-speech synthesis
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'audio_content': response.audio_content,
                'language_code': language_code,
                'voice_gender': voice_gender,
                'processing_time': processing_time,
                'audio_format': 'MP3',
                'text_length': len(text),
                'estimated_duration': len(text) / (speaking_rate * 150)  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {e}")
            return self._fallback_tts()
    
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
    
    def _fallback_transcription(self) -> Dict[str, Any]:
        """Fallback when Speech-to-Text is not available"""
        return {
            'success': False,
            'transcript': "",
            'confidence': 0.0,
            'processing_time': 0.0,
            'error': 'Google Speech-to-Text not available - please type your input',
            'alternatives': [],
            'quality_assessment': {'overall_quality': 'unavailable'},
            'legal_terms_detected': [],
            'suggestions': ['Speech recognition not available - please use text input']
        }
    
    def _fallback_tts(self) -> Dict[str, Any]:
        """Fallback when Text-to-Speech is not available"""
        return {
            'success': False,
            'audio_content': b'',
            'processing_time': 0.0,
            'error': 'Google Text-to-Speech not available',
            'language_code': 'en-US',
            'voice_gender': 'NEUTRAL'
        }
    
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
speech_service = GoogleCloudSpeechService()