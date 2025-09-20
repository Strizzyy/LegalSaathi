"""
Test suite for speech endpoints in FastAPI backend
"""

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app

client = TestClient(app)


class TestSpeechEndpoints:
    """Test speech-to-text and text-to-speech endpoints"""
    
    def test_speech_to_text_success(self):
        """Test successful speech-to-text conversion"""
        # Create mock audio file
        audio_content = b"mock audio content"
        audio_file = io.BytesIO(audio_content)
        
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_service.speech_to_text.return_value = {
                'success': True,
                'transcript': 'This is a test rental agreement',
                'confidence': 0.95,
                'language_detected': 'en-US',
                'processing_time': 1.2
            }
            
            response = client.post(
                "/api/speech/speech-to-text",
                files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                data={
                    "language_code": "en-US",
                    "enable_punctuation": "true"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["transcript"] == "This is a test rental agreement"
            assert data["confidence"] == 0.95
            assert data["language_detected"] == "en-US"
    
    def test_speech_to_text_no_file(self):
        """Test speech-to-text with no audio file"""
        response = client.post(
            "/api/speech/speech-to-text",
            data={
                "language_code": "en-US",
                "enable_punctuation": "true"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_speech_to_text_service_disabled(self):
        """Test speech-to-text when service is disabled"""
        audio_content = b"mock audio content"
        audio_file = io.BytesIO(audio_content)
        
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = False
            
            response = client.post(
                "/api/speech/speech-to-text",
                files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                data={"language_code": "en-US"}
            )
            
            assert response.status_code == 503
            assert "Speech service is not available" in response.json()["detail"]
    
    def test_speech_to_text_large_file(self):
        """Test speech-to-text with file too large"""
        # Create large mock file (>10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        audio_file = io.BytesIO(large_content)
        
        response = client.post(
            "/api/speech/speech-to-text",
            files={"audio_file": ("large.webm", audio_file, "audio/webm")},
            data={"language_code": "en-US"}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"]
    
    def test_text_to_speech_success(self):
        """Test successful text-to-speech conversion"""
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_audio_content = b"mock audio content"
            mock_service.text_to_speech.return_value = {
                'success': True,
                'audio_content': mock_audio_content,
                'language_code': 'en-US',
                'voice_gender': 'NEUTRAL',
                'processing_time': 0.8
            }
            
            response = client.post(
                "/api/speech/text-to-speech",
                json={
                    "text": "This is a test clause about rental payments",
                    "language_code": "en-US",
                    "voice_gender": "NEUTRAL",
                    "speaking_rate": 0.9,
                    "pitch": 0.0,
                    "audio_encoding": "MP3"
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert len(response.content) > 0
    
    def test_text_to_speech_long_text(self):
        """Test text-to-speech with text too long"""
        long_text = "x" * 5001  # Exceeds 5000 character limit
        
        response = client.post(
            "/api/speech/text-to-speech",
            json={
                "text": long_text,
                "language_code": "en-US"
            }
        )
        
        assert response.status_code == 400
        assert "too long" in response.json()["detail"]
    
    def test_text_to_speech_info(self):
        """Test text-to-speech info endpoint"""
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_audio_content = b"mock audio content"
            mock_service.text_to_speech.return_value = {
                'success': True,
                'audio_content': mock_audio_content,
                'language_code': 'en-US',
                'voice_gender': 'NEUTRAL',
                'processing_time': 0.8
            }
            
            response = client.post(
                "/api/speech/text-to-speech/info",
                json={
                    "text": "Test clause",
                    "language_code": "en-US",
                    "voice_gender": "NEUTRAL"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["audio_content_type"] == "audio/mp3"
            assert data["audio_size_bytes"] == len(mock_audio_content)
    
    def test_get_supported_languages(self):
        """Test getting supported languages"""
        response = client.get("/api/speech/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "speech_to_text_languages" in data
        assert "text_to_speech_languages" in data
        assert len(data["speech_to_text_languages"]) > 0
        
        # Check language structure
        lang = data["speech_to_text_languages"][0]
        assert "code" in lang
        assert "name" in lang
    
    def test_speech_service_error_handling(self):
        """Test error handling in speech service"""
        audio_content = b"mock audio content"
        audio_file = io.BytesIO(audio_content)
        
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_service.speech_to_text.return_value = {
                'success': False,
                'error': 'Google Cloud API error'
            }
            
            response = client.post(
                "/api/speech/speech-to-text",
                files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                data={"language_code": "en-US"}
            )
            
            assert response.status_code == 500
            assert "Speech-to-text conversion failed" in response.json()["detail"]


class TestSpeechServiceIntegration:
    """Integration tests for Google Cloud Speech services"""
    
    @pytest.mark.integration
    def test_speech_service_initialization(self):
        """Test speech service initialization"""
        from services.google_speech_service import GoogleCloudSpeechService
        
        service = GoogleCloudSpeechService()
        # Should not raise exception even if credentials are not available
        assert hasattr(service, 'enabled')
        assert hasattr(service, 'speech_client')
        assert hasattr(service, 'tts_client')
    
    @pytest.mark.integration
    def test_supported_languages_format(self):
        """Test supported languages format"""
        from services.google_speech_service import GoogleCloudSpeechService
        
        service = GoogleCloudSpeechService()
        languages = service.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert "neural_voices" in lang
            assert isinstance(lang["neural_voices"], bool)
    
    @pytest.mark.integration
    def test_fallback_methods(self):
        """Test fallback methods when service is unavailable"""
        from services.google_speech_service import GoogleCloudSpeechService
        
        service = GoogleCloudSpeechService()
        service.enabled = False
        
        # Test speech-to-text fallback
        stt_result = service.speech_to_text(b"test audio", "en-US")
        assert stt_result["success"] is False
        assert "not available" in stt_result["error"]
        
        # Test text-to-speech fallback
        tts_result = service.text_to_speech("test text", "en-US")
        assert tts_result["success"] is False
        assert "not available" in tts_result["error"]


class TestSpeechRateLimiting:
    """Test rate limiting for speech endpoints"""
    
    def test_speech_to_text_rate_limit(self):
        """Test rate limiting on speech-to-text endpoint"""
        audio_content = b"mock audio content"
        
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_service.speech_to_text.return_value = {
                'success': True,
                'transcript': 'test',
                'confidence': 0.9,
                'language_detected': 'en-US',
                'processing_time': 0.1
            }
            
            # Make multiple requests quickly
            responses = []
            for i in range(12):  # Exceeds 10/minute limit
                audio_file = io.BytesIO(audio_content)
                response = client.post(
                    "/api/speech/speech-to-text",
                    files={"audio_file": (f"test{i}.webm", audio_file, "audio/webm")},
                    data={"language_code": "en-US"}
                )
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited = [r for r in responses if r.status_code == 429]
            assert len(rate_limited) > 0
    
    def test_text_to_speech_rate_limit(self):
        """Test rate limiting on text-to-speech endpoint"""
        with patch('google_speech_service.speech_service') as mock_service:
            mock_service.enabled = True
            mock_service.text_to_speech.return_value = {
                'success': True,
                'audio_content': b"mock audio",
                'processing_time': 0.1
            }
            
            # Make multiple requests quickly
            responses = []
            for i in range(12):  # Exceeds 10/minute limit
                response = client.post(
                    "/api/speech/text-to-speech",
                    json={
                        "text": f"Test text {i}",
                        "language_code": "en-US"
                    }
                )
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited = [r for r in responses if r.status_code == 429]
            assert len(rate_limited) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])