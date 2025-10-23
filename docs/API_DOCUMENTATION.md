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

### Root API Endpoint

#### GET /api
Get API information and version details.

**Response:**
```json
{
  "name": "Legal Saathi Document Advisor API",
  "version": "2.0.0",
  "description": "AI-powered legal document analysis platform",
  "docs_url": "/docs",
  "redoc_url": "/redoc",
  "health_check": "/health",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Health Check Endpoints

#### GET /health
Basic health check endpoint.

**Response Model:** `HealthCheckResponse`

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
    "groq_api": "connected",
    "document_ai": "connected", 
    "translation": "connected",
    "speech": "connected",
    "natural_language": "connected"
  },
  "system_info": {
    "memory_usage": "45%",
    "cpu_usage": "12%"
  }
}
```

#### GET /api/health/metrics
Get service performance metrics.

**Response:**
```json
{
  "metrics": {
    "requests_per_minute": 25,
    "average_response_time": 1.2,
    "error_rate": 0.02
  }
}
```

### Document Analysis Endpoints

#### POST /api/analyze
Analyze legal document text.

**Rate Limit:** 10 requests/minute
**Response Model:** `DocumentAnalysisResponse`

**Request Body:**
```json
{
  "document_text": "string",
  "document_type": "rental_agreement|employment_contract|nda|loan_agreement|partnership_agreement|general_contract",
  "user_expertise_level": "beginner|intermediate|expert",
  "analysis_options": {
    "include_ai_insights": true,
    "include_translation_options": true,
    "detailed_explanations": true,
    "confidence_threshold": 0.7
  }
}
```

**Response:**
```json
{
  "analysis_id": "string",
  "overall_risk": {
    "level": "RED|YELLOW|GREEN",
    "score": 0.85,
    "severity": "high|moderate|low",
    "confidence_percentage": 85,
    "reasons": ["string"],
    "risk_categories": {
      "financial": 0.8,
      "legal": 0.7,
      "operational": 0.6
    },
    "low_confidence_warning": false
  },
  "clause_assessments": [
    {
      "clause_id": "1",
      "clause_text": "Full clause text from document",
      "risk_assessment": {
        "level": "RED|YELLOW|GREEN",
        "score": 0.8,
        "severity": "high|moderate|low",
        "confidence_percentage": 85,
        "reasons": ["specific reasons"],
        "risk_categories": {
          "financial": 0.8,
          "legal": 0.7,
          "operational": 0.6
        },
        "low_confidence_warning": false
      },
      "plain_explanation": "Plain language explanation",
      "legal_implications": ["implication1", "implication2"],
      "recommendations": ["recommendation1", "recommendation2"],
      "translation_available": true
    }
  ],
  "summary": "Document analysis summary",
  "processing_time": 2.5,
  "recommendations": ["overall recommendation"],
  "timestamp": "2024-01-01T00:00:00Z",
  "enhanced_insights": {
    "natural_language": {
      "sentiment": "neutral",
      "entities": [],
      "legal_insights": {}
    }
  }
}
```

#### POST /api/analyze/file
Analyze uploaded document file.

**Rate Limit:** 5 requests/minute
**Response Model:** `DocumentAnalysisResponse`

**Request (multipart/form-data):**
- `file`: Document file (PDF, DOC, DOCX, TXT, max 10MB)
- `document_type`: Document type (rental_agreement|employment_contract|nda|loan_agreement|partnership_agreement|general_contract)
- `user_expertise_level`: User expertise level (beginner|intermediate|expert, default: beginner)

**Response:** Same structure as `/api/analyze`

**File Type Support:**
- PDF: `application/pdf`
- DOC: `application/msword`
- DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- TXT: `text/plain`

#### POST /api/analyze/async
Start asynchronous document analysis.

**Rate Limit:** 5 requests/minute

**Request Body:** Same as `/api/analyze`

**Response:**
```json
{
  "success": true,
  "job_id": "string",
  "message": "Analysis started successfully",
  "status_endpoint": "/api/analysis/status/{job_id}"
}
```

#### GET /api/analysis/status/{analysis_id}
Get status of ongoing analysis.

**Response Model:** `AnalysisStatusResponse`

**Response:**
```json
{
  "analysis_id": "string",
  "status": "processing|completed|failed",
  "progress": 75,
  "estimated_completion": "2024-01-01T00:05:00Z",
  "result": null,
  "error_message": null
}
```

#### POST /api/analysis/{analysis_id}/export
Export analysis results.

**Query Parameters:**
- `format`: Export format (pdf|word, default: pdf)

**Response:**
```json
{
  "success": true,
  "message": "Export to pdf format initiated",
  "download_url": "/api/analysis/{analysis_id}/download/pdf"
}
```

### Translation Endpoints

#### POST /api/translate
Translate text to target language.

**Rate Limit:** 20 requests/minute
**Response Model:** `TranslationResponse`

**Request Body:**
```json
{
  "text": "string (1-5000 chars)",
  "target_language": "en|hi|es|fr|de|it|pt|ru|ja|ko|zh|ar|nl|sv|da|no|fi|pl|cs|hu|ro|bg|hr|sk|sl|et|lv|lt|mt|ga|cy|eu|ca|gl|is|mk|sq|sr|bs|me|tr|he|fa|ur|bn|ta|te|ml|kn|gu|pa|or|as|mr|ne|si|my|km|lo|th|vi|id|ms|tl|sw|am|yo|ig|ha|zu|af|xh",
  "source_language": "auto|{any supported language code}"
}
```

**Response:**
```json
{
  "success": true,
  "translated_text": "string",
  "source_language": "en",
  "target_language": "es", 
  "language_name": "Spanish (Español)",
  "confidence_score": 0.9,
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/translate/clause
Translate legal clause with context.

**Rate Limit:** 15 requests/minute
**Response Model:** `ClauseTranslationResponse`

**Request Body:**
```json
{
  "clause_id": "string",
  "clause_text": "string (1-2000 chars)",
  "target_language": "es",
  "source_language": "auto",
  "include_legal_context": true
}
```

**Response:**
```json
{
  "success": true,
  "clause_id": "string",
  "original_text": "string",
  "translated_text": "string",
  "source_language": "en",
  "target_language": "es",
  "language_name": "Spanish (Español)",
  "legal_context": "This clause has been translated with legal terminology preserved for accuracy in Spanish (Español).",
  "confidence_score": 0.9,
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/translate/languages
Get supported languages for translation.

**Response Model:** `SupportedLanguagesResponse`

**Response:**
```json
{
  "success": true,
  "languages": [
    {
      "code": "en",
      "name": "English"
    },
    {
      "code": "hi", 
      "name": "Hindi (हिंदी)"
    }
  ],
  "total_count": 70,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Speech Processing Endpoints

#### POST /api/speech/speech-to-text
Convert speech to text.

**Rate Limit:** 10 requests/minute
**Response Model:** `SpeechToTextResponse`

**Request (multipart/form-data):**
- `audio_file`: Audio file (WEBM, WAV, MP3, FLAC, max 10MB)
- `language_code`: Language code (default: "en-US")
- `enable_punctuation`: Enable automatic punctuation (default: true)

**Supported Language Codes:**
- en-US, en-GB, hi-IN, es-ES, es-US, fr-FR, de-DE, it-IT, pt-BR, ru-RU, ja-JP, ko-KR, zh-CN

**Response:**
```json
{
  "success": true,
  "transcript": "string",
  "confidence": 0.95,
  "language_detected": "en-US",
  "processing_time": 1.2,
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/speech/text-to-speech
Convert text to speech.

**Rate Limit:** 10 requests/minute

**Request Body:**
```json
{
  "text": "string (1-5000 chars)",
  "language_code": "en-US",
  "voice_gender": "NEUTRAL|MALE|FEMALE",
  "speaking_rate": 0.9,
  "pitch": 0.0,
  "audio_encoding": "MP3|WAV|OGG_OPUS"
}
```

**Response:** Audio file (binary data) with headers:
- Content-Type: audio/mpeg (or audio/wav, audio/ogg)
- Content-Disposition: attachment; filename=speech.mp3
- Content-Length: {size}

#### POST /api/speech/text-to-speech/info
Get text-to-speech metadata without audio.

**Rate Limit:** 15 requests/minute
**Response Model:** `TextToSpeechResponse`

**Request Body:** Same as `/api/speech/text-to-speech`

**Response:**
```json
{
  "success": true,
  "audio_content_type": "audio/mp3",
  "audio_size_bytes": 15360,
  "language_code": "en-US",
  "voice_gender": "NEUTRAL",
  "processing_time": 0.8,
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/speech/languages
Get supported languages for speech services.

**Response Model:** `SupportedLanguagesResponse`

**Response:**
```json
{
  "success": true,
  "speech_to_text_languages": [
    {
      "code": "en-US",
      "name": "English (US)"
    },
    {
      "code": "hi-IN", 
      "name": "Hindi (India)"
    }
  ],
  "text_to_speech_languages": [
    {
      "code": "en-US",
      "name": "English (US)"
    }
  ],
  "total_stt_count": 13,
  "total_tts_count": 13,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### AI Clarification Endpoints

#### POST /api/ai/clarify
Get AI-powered clarification.

**Rate Limit:** 15 requests/minute
**Response Model:** `ClarificationResponse`

**Request Body:**
```json
{
  "question": "string (5-1000 chars)",
  "context": {
    "document": {
      "documentType": "rental_agreement",
      "overallRisk": "RED",
      "summary": "Document summary",
      "totalClauses": 5
    },
    "clause": {
      "clauseId": "1",
      "text": "Clause text",
      "riskLevel": "RED",
      "explanation": "Plain explanation",
      "implications": ["implication1"],
      "recommendations": ["recommendation1"]
    },
    "conversationHistory": []
  },
  "user_expertise_level": "beginner|intermediate|expert",
  "conversation_id": "optional_string"
}
```

**Response:**
```json
{
  "success": true,
  "response": "AI clarification response",
  "conversation_id": "string",
  "confidence_score": 85,
  "response_quality": "high|medium|basic",
  "processing_time": 1.2,
  "fallback": false,
  "service_used": "groq|keyword_fallback|emergency_fallback",
  "error_type": null
}
```

#### GET /api/ai/conversation/summary
Get conversation summary and analytics.

**Response Model:** `ConversationSummaryResponse`

**Response:**
```json
{
  "success": true,
  "total_questions": 15,
  "recent_questions": [
    {
      "question": "What does this clause mean?",
      "timestamp": "2024-01-01T00:00:00Z",
      "confidence": "high"
    }
  ],
  "analytics": {
    "avg_response_length": 150,
    "fallback_rate": 0.1,
    "high_confidence_rate": 0.8
  }
}
```

#### DELETE /api/ai/conversation/clear
Clear conversation history.

**Response:**
```json
{
  "success": true,
  "message": "Conversation history cleared successfully"
}
```

### Document Comparison Endpoints

#### POST /api/compare
Compare two legal documents.

**Rate Limit:** 5 requests/minute
**Response Model:** `DocumentComparisonResponse`

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

#### GET /api/compare/{comparison_id}/summary
Get summary of a previous comparison.

**Response Model:** `ComparisonSummaryResponse`

**Response:**
```json
{
  "comparison_id": "string",
  "summary": "Comparison summary",
  "key_differences": ["difference1", "difference2"],
  "overall_similarity": 0.85,
  "recommendation": "string"
}
```

### Export Endpoints

#### POST /api/export/pdf
Export analysis results to PDF.

**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "analysis": {
    // DocumentAnalysisResponse object
  }
}
```

**Response:** PDF file (binary data) with headers:
- Content-Type: application/pdf
- Content-Disposition: attachment; filename=analysis.pdf

#### POST /api/export/word
Export analysis results to Word document.

**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "analysis": {
    // DocumentAnalysisResponse object
  }
}
```

**Response:** Word file (binary data) with headers:
- Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
- Content-Disposition: attachment; filename=analysis.docx

### Background Tasks Endpoints

#### POST /api/tasks/cleanup
Trigger cache cleanup.

**Response:**
```json
{
  "success": true,
  "message": "Cache cleanup scheduled"
}
```

### Logging Endpoints

#### GET /api/logs
Get recent application logs.

**Query Parameters:**
- `lines`: Number of log lines to return (default: 100)

**Response:**
```json
{
  "logs": ["log line 1", "log line 2"]
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

- **400 Bad Request**: Invalid request parameters or validation errors
- **401 Unauthorized**: Missing or invalid API key
- **413 Payload Too Large**: File size exceeds 10MB limit
- **422 Unprocessable Entity**: Invalid file type or content
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error
- **503 Service Unavailable**: External AI service unavailable

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