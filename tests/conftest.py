"""
Test configuration and fixtures for LegalSaathi API tests
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os
from unittest.mock import Mock, patch

# Import the main application
from main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    from fastapi.testclient import TestClient
    # Use TestClient for now since AsyncClient setup is complex
    client = TestClient(app)
    
    # Create a mock async client that wraps the sync client
    class MockAsyncClient:
        def __init__(self, sync_client):
            self.sync_client = sync_client
        
        async def post(self, url, **kwargs):
            return self.sync_client.post(url, **kwargs)
        
        async def get(self, url, **kwargs):
            return self.sync_client.get(url, **kwargs)
        
        async def put(self, url, **kwargs):
            return self.sync_client.put(url, **kwargs)
        
        async def delete(self, url, **kwargs):
            return self.sync_client.delete(url, **kwargs)
    
    yield MockAsyncClient(client)


@pytest.fixture
def mock_firebase_service():
    """Mock Firebase service for testing."""
    with patch('services.firebase_service.FirebaseService') as mock:
        mock_instance = Mock()
        mock_instance.verify_token.return_value = {
            'success': True,
            'user': {
                'uid': 'test_user_123',
                'email': 'test@example.com',
                'display_name': 'Test User'
            }
        }
        mock_instance._firebase_available = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service for testing."""
    with patch('services.gmail_service.GmailService') as mock:
        mock_instance = Mock()
        mock_instance.send_analysis_report.return_value = {
            'success': True,
            'message_id': 'test_message_123',
            'delivery_status': 'sent'
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_translate_service():
    """Mock Google Translate service for testing."""
    with patch('services.google_translate_service.GoogleTranslateService') as mock:
        mock_instance = Mock()
        mock_instance.translate_text.return_value = {
            'success': True,
            'translated_text': 'Texto traducido',
            'source_language': 'en',
            'target_language': 'es',
            'confidence_score': 0.95
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_speech_service():
    """Mock Google Speech service for testing."""
    with patch('services.google_speech_service.GoogleSpeechService') as mock:
        mock_instance = Mock()
        mock_instance.speech_to_text.return_value = {
            'success': True,
            'transcript': 'This is a test transcript',
            'confidence': 0.95,
            'language_detected': 'en-US'
        }
        mock_instance.text_to_speech.return_value = b'fake_audio_data'
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_document_text():
    """Sample legal document text for testing."""
    return """
    RENTAL AGREEMENT
    
    This rental agreement is entered into between the Landlord and Tenant.
    
    1. RENT: The monthly rent is $1,500 due on the 1st of each month.
    
    2. SECURITY DEPOSIT: A security deposit of $3,000 is required.
    
    3. TERMINATION: Either party may terminate this agreement with 30 days notice.
    
    4. LIABILITY: The Landlord shall not be liable for any damages exceeding $500.
    """


@pytest.fixture
def sample_analysis_response():
    """Sample document analysis response for testing."""
    return {
        "analysis_id": "test_analysis_123",
        "overall_risk": {
            "level": "YELLOW",
            "score": 0.65,
            "severity": "moderate",
            "confidence_percentage": 85,
            "reasons": ["High security deposit", "Broad liability waiver"],
            "risk_categories": {
                "financial": 0.7,
                "legal": 0.6,
                "operational": 0.5
            },
            "low_confidence_warning": False
        },
        "clause_assessments": [
            {
                "clause_id": "1",
                "clause_text": "The monthly rent is $1,500 due on the 1st of each month.",
                "risk_assessment": {
                    "level": "GREEN",
                    "score": 0.2,
                    "severity": "low",
                    "confidence_percentage": 95,
                    "reasons": ["Standard rent clause"],
                    "risk_categories": {
                        "financial": 0.2,
                        "legal": 0.1,
                        "operational": 0.1
                    },
                    "low_confidence_warning": False
                },
                "plain_explanation": "This is a standard rent payment clause.",
                "legal_implications": ["Monthly payment obligation"],
                "recommendations": ["Ensure payment is made on time"],
                "translation_available": True
            }
        ],
        "summary": "This is a standard rental agreement with moderate risk.",
        "processing_time": 2.5,
        "recommendations": ["Review security deposit amount"],
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing."""
    # Create a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write minimal WAV header
        f.write(b'RIFF')
        f.write((36).to_bytes(4, 'little'))  # File size - 8
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))  # Subchunk1Size
        f.write((1).to_bytes(2, 'little'))   # AudioFormat (PCM)
        f.write((1).to_bytes(2, 'little'))   # NumChannels
        f.write((44100).to_bytes(4, 'little'))  # SampleRate
        f.write((88200).to_bytes(4, 'little'))  # ByteRate
        f.write((2).to_bytes(2, 'little'))   # BlockAlign
        f.write((16).to_bytes(2, 'little'))  # BitsPerSample
        f.write(b'data')
        f.write((0).to_bytes(4, 'little'))   # Subchunk2Size
        
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def auth_headers():
    """Sample authentication headers for testing."""
    return {
        "Authorization": "Bearer test_firebase_token_123",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_cost_monitor():
    """Mock cost monitoring service for testing."""
    with patch('services.cache_service.CacheService') as mock:
        mock_instance = Mock()
        mock_instance.check_usage_limits.return_value = True
        mock_instance.get_usage_stats.return_value = {
            'document_ai': {'requests': 10, 'limit': 1000},
            'translation': {'requests': 50, 'limit': 10000},
            'speech_to_text': {'requests': 5, 'limit': 300},
            'text_to_speech': {'requests': 8, 'limit': 200}
        }
        mock.return_value = mock_instance
        yield mock_instance