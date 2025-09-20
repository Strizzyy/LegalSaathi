# LegalSaathi API Documentation

## Overview

The LegalSaathi API provides comprehensive legal document analysis, translation, and speech processing capabilities through a RESTful interface built with FastAPI.

**Base URL**: `https://legalsaathi-document-advisor.onrender.com`
**API Version**: 2.0.0

## Authentication

Currently, the API uses API key authentication for Google Cloud services. No user authentication is required for public endpoints.

## Rate Limiting

- Document Analysis: 10 requests/minute
- File Upload: 5 requests/minute
- Translation: 20 requests/minute
- Speech Services: 10 requests/minute
- AI Clarification: 15 requests/minute

## API Endpoints

### Health Check Endpoints

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0"
}
```

#### GET /api/health/detailed
Detailed health check with service information.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "gemini_api": "connected",
    "document_ai": "connected",
    "translation": "connected",
    "speech": "connected"
  },
  "system_info": {
    "memory_usage": "45%",
    "cpu_usage": "12%"
  }
}
```

### Document Analysis Endpoints

#### POST /api/analyze
Analyze legal document text.

**Request Body:**
```json
{
  "text": "string",
  "document_type": "contract|agreement|terms|policy|other",
  "user_expertise_level": "beginner|intermediate|expert"
}
```

**Response:**
```json
{
  "analysis_id": "string",
  "summary": "string",
  "key_points": ["string"],
  "risks": [
    {
      "level": "high|medium|low",
      "description": "string",
      "recommendation": "string"
    }
  ],
  "clauses": [
    {
      "clause_text": "string",
      "explanation": "string",
      "importance": "high|medium|low"
    }
  ],
  "overall_assessment": {
    "fairness_score": 0.85,
    "complexity_score": 0.65,
    "recommendation": "string"
  }
}
```

#### POST /api/analyze/file
Analyze uploaded document file.

**Request (multipart/form-data):**
- `file`: Document file (PDF, DOC, DOCX, TXT)
- `document_type`: Document type
- `user_expertise_level`: User expertise level

**Response:** Same as `/api/analyze`

#### POST /api/analyze/async
Start asynchronous document analysis.

**Request Body:** Same as `/api/analyze`

**Response:**
```json
{
  "analysis_id": "string",
  "status": "processing",
  "estimated_completion": "2024-01-01T00:05:00Z"
}
```

#### GET /api/analysis/status/{analysis_id}
Get status of ongoing analysis.

**Response:**
```json
{
  "analysis_id": "string",
  "status": "processing|completed|failed",
  "progress": 75,
  "result": {} // Analysis result when completed
}
```

### Translation Endpoints

#### POST /api/translate
Translate text to target language.

**Request Body:**
```json
{
  "text": "string",
  "target_language": "es|fr|de|it|pt|hi|zh|ja|ko",
  "source_language": "auto|en|es|fr|de|it|pt|hi|zh|ja|ko",
  "preserve_formatting": true
}
```

**Response:**
```json
{
  "translated_text": "string",
  "source_language": "en",
  "target_language": "es",
  "confidence": 0.95
}
```

#### POST /api/translate/clause
Translate legal clause with context.

**Request Body:**
```json
{
  "clause_text": "string",
  "context": "string",
  "target_language": "es",
  "legal_system": "common_law|civil_law|other"
}
```

**Response:**
```json
{
  "translated_clause": "string",
  "legal_notes": "string",
  "confidence": 0.92,
  "cultural_adaptations": ["string"]
}
```

#### GET /api/translate/languages
Get supported languages for translation.

**Response:**
```json
{
  "supported_languages": [
    {
      "code": "en",
      "name": "English",
      "native_name": "English"
    }
  ]
}
```

### Speech Processing Endpoints

#### POST /api/speech/speech-to-text
Convert speech to text.

**Request (multipart/form-data):**
- `audio_file`: Audio file (WAV, MP3, FLAC)
- `language_code`: Language code (default: "en-US")
- `enable_punctuation`: Enable automatic punctuation (default: true)

**Response:**
```json
{
  "transcript": "string",
  "confidence": 0.95,
  "language_code": "en-US",
  "duration": 30.5
}
```

#### POST /api/speech/text-to-speech
Convert text to speech.

**Request Body:**
```json
{
  "text": "string",
  "language_code": "en-US",
  "voice_name": "en-US-Wavenet-D",
  "speaking_rate": 1.0,
  "pitch": 0.0
}
```

**Response:** Audio file (binary data)

#### POST /api/speech/text-to-speech/info
Get text-to-speech metadata without audio.

**Request Body:** Same as `/api/speech/text-to-speech`

**Response:**
```json
{
  "audio_length": 15.3,
  "voice_info": {
    "name": "en-US-Wavenet-D",
    "gender": "MALE",
    "language": "en-US"
  },
  "audio_format": "MP3"
}
```

#### GET /api/speech/languages
Get supported languages for speech services.

**Response:**
```json
{
  "speech_to_text": [
    {
      "language_code": "en-US",
      "display_name": "English (United States)"
    }
  ],
  "text_to_speech": [
    {
      "language_code": "en-US",
      "voices": [
        {
          "name": "en-US-Wavenet-D",
          "gender": "MALE"
        }
      ]
    }
  ]
}
```

### AI Clarification Endpoints

#### POST /api/ai/clarify
Get AI-powered clarification.

**Request Body:**
```json
{
  "question": "string",
  "context": "string",
  "document_type": "contract|agreement|terms|policy|other"
}
```

**Response:**
```json
{
  "clarification": "string",
  "confidence": 0.88,
  "related_topics": ["string"],
  "follow_up_questions": ["string"]
}
```

#### GET /api/ai/conversation/summary
Get conversation summary and analytics.

**Response:**
```json
{
  "total_questions": 15,
  "common_topics": ["contract terms", "liability clauses"],
  "user_expertise_trend": "improving",
  "session_duration": 1800
}
```

#### DELETE /api/ai/conversation/clear
Clear conversation history.

**Response:**
```json
{
  "message": "Conversation history cleared successfully"
}
```

### Document Comparison Endpoints

#### POST /api/compare
Compare two legal documents.

**Request Body:**
```json
{
  "document1": {
    "text": "string",
    "title": "string"
  },
  "document2": {
    "text": "string",
    "title": "string"
  },
  "comparison_type": "full|clauses|terms|structure"
}
```

**Response:**
```json
{
  "comparison_id": "string",
  "differences": [
    {
      "type": "addition|deletion|modification",
      "section": "string",
      "description": "string",
      "impact": "high|medium|low"
    }
  ],
  "similarities": [
    {
      "section": "string",
      "match_percentage": 95.5
    }
  ],
  "recommendation": "string"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "error_code": "HTTP_STATUS_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes

- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid API key
- **413 Payload Too Large**: File size exceeds limit
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error
- **503 Service Unavailable**: External service unavailable

## Request/Response Examples

### Document Analysis Example

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This agreement shall be governed by the laws of California...",
    "document_type": "contract",
    "user_expertise_level": "beginner"
  }'
```

**Response:**
```json
{
  "analysis_id": "analysis_123",
  "summary": "This is a standard contract with California governing law...",
  "key_points": [
    "Governed by California law",
    "30-day termination clause",
    "Liability limitations apply"
  ],
  "risks": [
    {
      "level": "medium",
      "description": "Broad liability waiver clause",
      "recommendation": "Consider negotiating more specific limitations"
    }
  ],
  "overall_assessment": {
    "fairness_score": 0.75,
    "complexity_score": 0.60,
    "recommendation": "Generally fair contract with some areas for negotiation"
  }
}
```

### Translation Example

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This agreement is binding upon both parties",
    "target_language": "es",
    "source_language": "en"
  }'
```

**Response:**
```json
{
  "translated_text": "Este acuerdo es vinculante para ambas partes",
  "source_language": "en",
  "target_language": "es",
  "confidence": 0.96
}
```

## SDK and Integration

### JavaScript/TypeScript Integration

```typescript
class LegalSaathiAPI {
  private baseURL = 'https://legalsaathi-document-advisor.onrender.com';
  
  async analyzeDocument(text: string, documentType: string) {
    const response = await fetch(`${this.baseURL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        document_type: documentType,
        user_expertise_level: 'beginner'
      })
    });
    
    return response.json();
  }
  
  async translateText(text: string, targetLanguage: string) {
    const response = await fetch(`${this.baseURL}/api/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        target_language: targetLanguage
      })
    });
    
    return response.json();
  }
}
```

### Python Integration

```python
import requests
import json

class LegalSaathiAPI:
    def __init__(self):
        self.base_url = "https://legalsaathi-document-advisor.onrender.com"
    
    def analyze_document(self, text: str, document_type: str):
        url = f"{self.base_url}/api/analyze"
        payload = {
            "text": text,
            "document_type": document_type,
            "user_expertise_level": "beginner"
        }
        
        response = requests.post(url, json=payload)
        return response.json()
    
    def translate_text(self, text: str, target_language: str):
        url = f"{self.base_url}/api/translate"
        payload = {
            "text": text,
            "target_language": target_language
        }
        
        response = requests.post(url, json=payload)
        return response.json()
```

## Performance Considerations

- **Caching**: API responses are cached for 5 minutes
- **Compression**: All responses use GZip compression
- **Async Processing**: Long-running operations support async processing
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **Timeout**: Requests timeout after 120 seconds

## Monitoring and Analytics

The API includes built-in monitoring for:
- Response times
- Error rates
- Usage patterns
- Service health
- Resource utilization

Access monitoring data through the `/api/health/metrics` endpoint.