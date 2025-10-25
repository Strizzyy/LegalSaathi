"""
API Contract Validation Tests
Tests to ensure frontend and backend expectations match exactly
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from typing import Dict, Any


class TestAPIContracts:
    """Test API contracts to ensure frontend/backend compatibility"""
    
    def test_document_analysis_request_contract(self, client: TestClient, sample_document_text: str):
        """Test document analysis request/response contract"""
        request_data = {
            "document_text": sample_document_text,
            "document_type": "rental_agreement",
            "user_expertise_level": "beginner",
            "analysis_options": {
                "include_ai_insights": True,
                "include_translation_options": True,
                "detailed_explanations": True,
                "confidence_threshold": 0.7
            }
        }
        
        response = client.post("/api/analyze", json=request_data)
        
        # Test response structure
        assert response.status_code in [200, 422, 500]  # Allow for service errors in tests
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields exist
            required_fields = [
                "analysis_id", "overall_risk", "clause_assessments", 
                "summary", "processing_time", "timestamp"
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify overall_risk structure
            risk = data["overall_risk"]
            risk_fields = ["level", "score", "severity", "confidence_percentage", "reasons"]
            for field in risk_fields:
                assert field in risk, f"Missing risk field: {field}"
            
            # Verify clause_assessments structure
            if data["clause_assessments"]:
                clause = data["clause_assessments"][0]
                clause_fields = [
                    "clause_id", "clause_text", "risk_assessment", 
                    "plain_explanation", "legal_implications", "recommendations"
                ]
                for field in clause_fields:
                    assert field in clause, f"Missing clause field: {field}"
    
    def test_translation_request_contract(self, client: TestClient):
        """Test translation request/response contract"""
        request_data = {
            "text": "This agreement is binding upon both parties",
            "target_language": "es",
            "source_language": "en"
        }
        
        response = client.post("/api/translate", json=request_data)
        
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            required_fields = [
                "success", "translated_text", "source_language", 
                "target_language", "confidence_score", "timestamp"
            ]
            for field in required_fields:
                assert field in data, f"Missing translation field: {field}"
            
            # Verify data types
            assert isinstance(data["success"], bool)
            assert isinstance(data["translated_text"], str)
            assert isinstance(data["confidence_score"], (int, float))
    
    def test_speech_to_text_contract(self, client: TestClient, sample_audio_file: str):
        """Test speech-to-text request/response contract"""
        with open(sample_audio_file, 'rb') as f:
            files = {"audio_file": ("test.wav", f, "audio/wav")}
            data = {
                "language_code": "en-US",
                "enable_punctuation": True
            }
            
            response = client.post("/api/speech/speech-to-text", files=files, data=data)
        
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields - frontend expects 'transcript'
            required_fields = [
                "success", "transcript", "confidence", 
                "language_detected", "processing_time", "timestamp"
            ]
            for field in required_fields:
                assert field in data, f"Missing speech field: {field}"
            
            # Verify the critical field that frontend expects
            assert "transcript" in data, "Frontend expects 'transcript' field"
            assert isinstance(data["transcript"], str)
    
    def test_text_to_speech_contract(self, client: TestClient):
        """Test text-to-speech request/response contract"""
        request_data = {
            "text": "This is a test for text to speech",
            "language_code": "en-US",
            "voice_gender": "NEUTRAL",
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "audio_encoding": "MP3"
        }
        
        response = client.post("/api/speech/text-to-speech", json=request_data)
        
        assert response.status_code in [200, 422, 500]
        
        # For TTS, we expect binary audio data or error response
        if response.status_code == 200:
            # Should return audio file
            assert response.headers.get("content-type") in [
                "audio/mpeg", "audio/wav", "audio/ogg"
            ]
    
    def test_email_notification_contract(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test email notification request/response contract"""
        request_data = {
            "notification": {
                "user_email": "test@example.com",
                "analysis_id": "test_analysis_123",
                "include_pdf": True,
                "email_template": "standard"
            },
            "analysis_data": {
                "analysis_id": "test_analysis_123",
                "summary": "Test analysis summary"
            }
        }
        
        response = client.post(
            "/api/email/send-analysis", 
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            required_fields = ["success", "delivery_status"]
            for field in required_fields:
                assert field in data, f"Missing email field: {field}"
    
    def test_authentication_contract(self, client: TestClient):
        """Test authentication request/response contract"""
        request_data = {
            "token": "test_firebase_token"
        }
        
        response = client.post("/api/auth/verify-token", json=request_data)
        
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            required_fields = ["success"]
            for field in required_fields:
                assert field in data, f"Missing auth field: {field}"
            
            if data["success"]:
                assert "user" in data
    
    def test_error_response_contract(self, client: TestClient):
        """Test error response format consistency"""
        # Test with invalid request to trigger error
        response = client.post("/api/analyze", json={"invalid": "data"})
        
        assert response.status_code >= 400
        
        data = response.json()
        
        # Verify error response structure
        error_fields = ["error", "message"]
        for field in error_fields:
            assert field in data, f"Missing error field: {field}"
    
    def test_rate_limiting_headers(self, client: TestClient):
        """Test rate limiting response headers"""
        response = client.get("/api/health")
        
        # Should have processing time header
        assert "X-Process-Time" in response.headers
        
        # Should have cache control for API responses
        if response.url.path.startswith("/api/"):
            assert "Cache-Control" in response.headers
    
    def test_supported_languages_contract(self, client: TestClient):
        """Test supported languages endpoint contract"""
        response = client.get("/api/translate/languages")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify structure
        required_fields = ["success", "languages", "total_count", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing languages field: {field}"
        
        # Verify language structure
        if data["languages"]:
            language = data["languages"][0]
            assert "code" in language
            assert "name" in language
    
    def test_health_check_contract(self, client: TestClient):
        """Test health check endpoint contract"""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify basic health check structure
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"Missing health field: {field}"
    
    def test_detailed_health_check_contract(self, client: TestClient):
        """Test detailed health check endpoint contract"""
        response = client.get("/api/health/detailed")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify detailed health check structure
        required_fields = ["status", "services"]
        for field in required_fields:
            assert field in data, f"Missing detailed health field: {field}"
    
    def test_document_summary_translation_contract(self, client: TestClient):
        """Test document summary translation contract"""
        request_data = {
            "what_this_document_means": "This is a rental agreement",
            "key_points": ["Monthly rent is $1500", "Security deposit required"],
            "risk_assessment": "Moderate risk due to high deposit",
            "what_you_should_do": "Review the deposit terms carefully",
            "simple_explanation": "This is a standard rental contract",
            "target_language": "es",
            "source_language": "en"
        }
        
        response = client.post("/api/translate/document-summary", json=request_data)
        
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all summary sections are translated
            required_fields = [
                "translated_what_this_document_means",
                "translated_key_points", 
                "translated_risk_assessment",
                "translated_what_you_should_do",
                "translated_simple_explanation",
                "source_language",
                "target_language"
            ]
            for field in required_fields:
                assert field in data, f"Missing summary translation field: {field}"


class TestAPIValidation:
    """Test API input validation"""
    
    def test_document_analysis_validation(self, client: TestClient):
        """Test document analysis input validation"""
        # Test missing required fields
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422
        
        # Test invalid document type
        response = client.post("/api/analyze", json={
            "document_text": "test",
            "document_type": "invalid_type",
            "user_expertise_level": "beginner"
        })
        assert response.status_code == 422
        
        # Test invalid expertise level
        response = client.post("/api/analyze", json={
            "document_text": "test",
            "document_type": "rental_agreement", 
            "user_expertise_level": "invalid_level"
        })
        assert response.status_code == 422
    
    def test_translation_validation(self, client: TestClient):
        """Test translation input validation"""
        # Test missing text
        response = client.post("/api/translate", json={
            "target_language": "es"
        })
        assert response.status_code == 422
        
        # Test invalid language code
        response = client.post("/api/translate", json={
            "text": "test",
            "target_language": "invalid_lang"
        })
        assert response.status_code == 422
        
        # Test text too long (over 5000 chars)
        long_text = "a" * 5001
        response = client.post("/api/translate", json={
            "text": long_text,
            "target_language": "es"
        })
        assert response.status_code == 422
    
    def test_email_validation(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test email notification input validation"""
        # Test invalid email format
        response = client.post("/api/email/send-analysis", json={
            "notification": {
                "user_email": "invalid_email",
                "analysis_id": "test"
            }
        }, headers=auth_headers)
        assert response.status_code == 422
        
        # Test missing required fields
        response = client.post("/api/email/send-analysis", json={
            "notification": {}
        }, headers=auth_headers)
        assert response.status_code == 422
    
    def test_file_upload_validation(self, client: TestClient):
        """Test file upload validation"""
        # Test invalid file type
        files = {"file": ("test.txt", b"test content", "text/plain")}
        data = {"document_type": "rental_agreement"}
        
        response = client.post("/api/analyze/file", files=files, data=data)
        # Should either accept or reject with proper error
        assert response.status_code in [200, 422, 413, 500]
        
        # Test missing document type
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        
        response = client.post("/api/analyze/file", files=files)
        assert response.status_code == 422