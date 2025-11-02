# LegalSaathi API Documentation
*Comprehensive REST API for AI-Powered Legal Document Analysis*

## Overview

The LegalSaathi API provides comprehensive legal document analysis, translation, and speech processing capabilities through a RESTful interface built with FastAPI. The platform empowers everyone to understand legal documents through AI-powered analysis, multi-language support, accessibility features, and privacy-first processing.

**Base URL**: `https://legalsaathi-document-advisor.onrender.com`
**API Version**: 2.0.0
**Live Application**: [https://legalsaathi-document-advisor.onrender.com](https://legalsaathi-document-advisor.onrender.com)
**Interactive API Docs**: [https://legalsaathi-document-advisor.onrender.com/docs](https://legalsaathi-document-advisor.onrender.com/docs)
**Alternative API Docs**: [https://legalsaathi-document-advisor.onrender.com/redoc](https://legalsaathi-document-advisor.onrender.com/redoc)

## Key Features

### 🔒 Privacy-First Processing
- Automatic PII masking before cloud AI processing
- GDPR-compliant data handling
- Secure document analysis without privacy compromise

### 🤖 8 Google Cloud AI Services Integration
- **Gemini API**: Advanced legal document analysis
- **Document AI**: Structured document processing and OCR
- **Vision API**: Image-based document text extraction
- **Translation API**: Multi-language support (50+ languages)
- **Speech-to-Text**: Voice input for accessibility
- **Text-to-Speech**: Audio output for accessibility
- **Natural Language AI**: Entity extraction and analysis
- **Vertex AI**: Semantic search and RAG capabilities

### 🧠 Intelligent Human-in-the-Loop
- AI confidence calculation and routing
- Expert review system for low-confidence analyses
- Professional legal expert verification

### ♿ Universal Accessibility
- WCAG 2.1 AA compliance
- Multi-modal input (text, voice, image)
- Multi-language interface and analysis

## Authentication

The API supports both anonymous and authenticated access:
- **Anonymous Users**: Limited rate limits, basic features
- **Firebase Authentication**: Enhanced rate limits, personalized features, expert review access
- **Google Cloud Services**: Internal API key authentication for AI services

## Rate Limiting

### Anonymous Users
- Document Analysis: 5 requests/minute
- File Upload: 3 requests/minute
- Translation: 10 requests/minute
- Speech Services: 5 requests/minute
- AI Clarification: 10 requests/minute

### Authenticated Users (Firebase)
- Document Analysis: 15 requests/minute
- File Upload: 10 requests/minute
- Translation: 30 requests/minute
- Speech Services: 20 requests/minute
- AI Clarification: 25 requests/minute
- Expert Review: 5 requests/day (when confidence < 60%)
- Vision API: 100 requests/day
- Advanced RAG: 50 requests/day

## Privacy & Security

### Privacy-First Processing Pipeline
All document analysis follows a privacy-first approach:

1. **PII Detection**: Automatic identification of sensitive information
2. **Data Masking**: PII is masked before cloud AI processing
3. **Secure Processing**: Only masked data sent to Google Cloud AI services
4. **Result Unmasking**: Results are unmasked for user display
5. **Audit Logging**: Complete privacy operation tracking

### Supported PII Types
- Personal names and identities
- Email addresses and phone numbers
- Physical addresses and locations
- Social Security Numbers (SSNs)
- Financial account numbers
- Government identification numbers

### Data Retention
- **Temporary Files**: Deleted after processing
- **Analysis Cache**: 1-24 hours depending on service
- **User Data**: Controlled by user privacy settings
- **Audit Logs**: 30 days for compliance

## Human-in-the-Loop System

### Confidence-Based Routing
The system automatically calculates AI confidence and routes documents for expert review:

#### Confidence Calculation
- **Clause Analysis Confidence**: 40% weight
- **Document Summary Confidence**: 30% weight  
- **Risk Assessment Confidence**: 30% weight
- **Overall Threshold**: 60% for automatic approval

#### Expert Review Process
1. **Automatic Detection**: System identifies low confidence (<60%)
2. **User Consent**: Optional expert review with user approval
3. **Expert Queue**: Document added to professional review queue
4. **Priority Assignment**: HIGH/MEDIUM/LOW based on complexity
5. **Expert Analysis**: Legal professional reviews AI analysis
6. **Enhanced Results**: Combined AI + human insights delivered via email

### Expert Review Features
- **Status Tracking**: Real-time updates on review progress
- **Email Notifications**: Secure delivery of enhanced results
- **Quality Assurance**: Multiple review layers for accuracy
- **Expert Credentials**: Verified legal professionals

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
    "error_rate": 0.02,
    "cache_hit_rate": 0.85
  },
  "ai_services": {
    "gemini_api": {"status": "healthy", "response_time": 0.8},
    "document_ai": {"status": "healthy", "response_time": 1.5},
    "vision_api": {"status": "healthy", "response_time": 1.2},
    "translation_api": {"status": "healthy", "response_time": 0.5}
  }
}
```

#### GET /api/health/ready
Check if backend is fully initialized and ready for requests.

**Response:**
```json
{
  "ready": true,
  "ready_for_requests": true,
  "startup_complete": true,
  "initialization_complete": true,
  "status": {
    "mode": "optimized",
    "critical_services_ready": true,
    "background_services_loading": false
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/health/startup-performance
Get detailed startup performance metrics from optimized service manager.

**Response:**
```json
{
  "startup_status": {
    "phase": "completed",
    "total_startup_time": 12.5,
    "critical_services_time": 3.2,
    "background_services_time": 9.3
  },
  "performance_metrics": {
    "service_initialization_times": {
      "document_service": 1.2,
      "ai_service": 0.8,
      "translation_service": 0.5
    }
  },
  "health_status": {
    "overall_status": "healthy",
    "service_count": 12,
    "healthy_services": 12
  }
}
    "error_rate": 0.02
  }
}
```

### Document Analysis Endpoints

#### POST /api/analyze
Analyze legal document text with privacy-first processing and intelligent confidence routing.

**Rate Limit:** 10/minute (with user-based rate limiting)
**Response Model:** `DocumentAnalysisResponse`

**Request Body:**
```json
{
  "document_text": "string (required, 100-50000 characters)",
  "document_type": "rental_agreement|employment_contract|nda|loan_agreement|partnership_agreement|general_contract",
  "user_expertise_level": "beginner|intermediate|expert"
}
```

**Privacy-First Processing:**
1. **PII Detection**: Automatic identification of sensitive information
2. **Data Masking**: PII masked before cloud AI processing  
3. **Secure Analysis**: Only masked data sent to Google Cloud AI
4. **Result Unmasking**: Results unmasked for user display
5. **Audit Logging**: Complete privacy operation tracking

**AI Services Used:**
- **Gemini API**: Primary legal analysis with experience-level adaptation
- **Natural Language AI**: Entity extraction and sentiment analysis
- **Vertex AI**: Semantic search and enhanced insights via RAG

**Response:**
```json
{
  "analysis_id": "uuid-string",
  "overall_risk": {
    "level": "RED|YELLOW|GREEN",
    "score": 0.85,
    "severity": "high|moderate|low", 
    "confidence_percentage": 85,
    "reasons": ["Broad liability waiver clause", "Unclear termination terms"],
    "risk_categories": {
      "financial": 0.8,
      "legal": 0.7,
      "operational": 0.6,
      "compliance": 0.5
    },
    "low_confidence_warning": false
  },
  "overall_confidence": 0.82,
  "should_route_to_expert": false,
  "confidence_breakdown": {
    "clause_analysis_confidence": 0.85,
    "document_summary_confidence": 0.80,
    "risk_assessment_confidence": 0.81,
    "weighted_overall_confidence": 0.82,
    "factors_affecting_confidence": [
      "Complex legal terminology in clause 3",
      "Ambiguous language in termination section"
    ],
    "improvement_suggestions": [
      "Consider expert review for high-stakes decisions",
      "Request clarification on ambiguous terms"
    ]
  },
  "clause_assessments": [
    {
      "clause_id": "1",
      "clause_text": "The Employee agrees to maintain confidentiality...",
      "risk_assessment": {
        "level": "YELLOW",
        "score": 0.65,
        "severity": "moderate",
        "confidence_percentage": 88,
        "reasons": ["Standard confidentiality clause with reasonable scope"],
        "risk_categories": {
          "financial": 0.3,
          "legal": 0.7,
          "operational": 0.4,
          "compliance": 0.8
        },
        "low_confidence_warning": false
      },
      "plain_explanation": "This clause requires you to keep company information secret. The scope is reasonable and limited to truly confidential business information.",
      "legal_implications": [
        "You cannot share confidential company information",
        "Violation could result in legal action",
        "Obligation continues after employment ends"
      ],
      "recommendations": [
        "Ensure you understand what constitutes confidential information",
        "Ask for clarification on any unclear definitions"
      ],
      "translation_available": true,
      "enhanced_insights": {
        "precedent_analysis": "Similar clauses upheld in 85% of cases",
        "negotiation_points": ["Duration of confidentiality obligation"],
        "industry_standard": true
      }
    }
  ],
  "summary": "This employment contract contains standard terms with moderate risk levels. Key areas of concern include the broad liability waiver and unclear termination procedures.",
  "key_findings": [
    "Standard confidentiality and non-compete clauses",
    "Competitive salary and benefits package",
    "Unclear intellectual property assignment terms"
  ],
  "processing_time": 2.8,
  "recommendations": [
    "Negotiate clearer termination procedures",
    "Clarify intellectual property ownership terms",
    "Consider legal review for liability waiver clause"
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "enhanced_insights": {
    "natural_language": {
      "sentiment": "neutral",
      "sentiment_score": 0.02,
      "entities": [
        {"text": "Employee", "type": "PERSON", "salience": 0.8},
        {"text": "Company", "type": "ORGANIZATION", "salience": 0.9}
      ],
      "legal_insights": {
        "document_complexity": "medium",
        "readability_score": 0.65,
        "legal_terminology_density": 0.3
      }
    },
    "vertex_ai": {
      "similar_documents": [
        {"similarity": 0.92, "document_type": "employment_contract"},
        {"similarity": 0.87, "document_type": "employment_contract"}
      ],
      "precedent_matches": [
        {"clause_type": "confidentiality", "match_score": 0.94}
      ]
    }
  },
  "privacy_processing": {
    "pii_detected": true,
    "pii_types_masked": ["email", "phone", "address"],
    "masking_confidence": 0.98,
    "audit_id": "privacy-audit-uuid"
  }
}
```

#### POST /api/analyze/file
Analyze uploaded document file with multi-format support and privacy-first processing.

**Rate Limit:** 5/minute (anonymous), 10/minute (authenticated)
**Response Model:** `DocumentAnalysisResponse`

**Request (multipart/form-data):**
- `file`: Document file (required, max 20MB)
- `document_type`: Document category (required)
- `user_expertise_level`: Experience level (optional, default: "beginner")

**Supported File Formats:**
- **PDF**: `application/pdf` - Processed with Google Document AI
- **DOC**: `application/msword` - Legacy Word document support
- **DOCX**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **TXT**: `text/plain` - Direct text processing
- **Images**: `image/jpeg`, `image/png`, `image/webp`, `image/bmp`, `image/gif`

**Document Categories:**
- `rental_agreement`: Lease contracts, rental terms
- `employment_contract`: Job agreements, employment terms
- `nda`: Non-disclosure agreements
- `loan_agreement`: Lending contracts, financial agreements  
- `partnership_agreement`: Business partnerships
- `general_contract`: Other legal documents

**Experience Levels:**
- `beginner`: Simple explanations with examples
- `intermediate`: Balanced technical and plain language
- `expert`: Detailed legal analysis and precedents

**Processing Pipeline:**
1. **File Validation**: Format, size, and content validation
2. **Text Extraction**: 
   - PDFs/DOCs: Google Document AI for structured processing
   - Images: Google Vision API for OCR
   - Text files: Direct processing
3. **Privacy Processing**: Automatic PII detection and masking
4. **AI Analysis**: Multi-service analysis with confidence calculation
5. **Expert Routing**: Automatic expert review if confidence < 60%

**Response:** Same structure as `/api/analyze` with additional file metadata:

```json
{
  "analysis_id": "uuid-string",
  "file_metadata": {
    "original_filename": "contract.pdf",
    "file_size_bytes": 245760,
    "file_type": "application/pdf",
    "processing_method": "document_ai",
    "text_extraction_confidence": 0.95,
    "pages_processed": 3
  },
  // ... rest of analysis response
}
```

**Error Responses:**
- `400`: Invalid file format or size
- `413`: File size exceeds 20MB limit
- `422`: File content cannot be processed
- `503`: Document processing service unavailable

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
Translate individual legal clause with legal context preservation and cultural adaptation.

**Rate Limit:** 15/minute (anonymous), 30/minute (authenticated)
**Response Model:** `ClauseTranslationResponse`

**Request Body:**
```json
{
  "clause_id": "string (required)",
  "clause_text": "string (required, 1-2000 chars)",
  "target_language": "es (required)",
  "source_language": "auto (optional, default: auto-detect)",
  "include_legal_context": true,
  "preserve_legal_terms": true,
  "cultural_adaptation": true
}
```

**Legal Context Features:**
- **Terminology Preservation**: Maintains legal term accuracy
- **Cultural Adaptation**: Considers different legal systems
- **Jurisdiction Awareness**: Adapts to target country's legal framework
- **Precedent Integration**: References similar legal concepts

**Response:**
```json
{
  "success": true,
  "clause_id": "confidentiality_clause_1",
  "original_text": "The Employee shall maintain strict confidentiality regarding all proprietary information...",
  "translated_text": "El Empleado deberá mantener estricta confidencialidad respecto a toda información propietaria...",
  "source_language": "en",
  "target_language": "es",
  "language_name": "Spanish (Español)",
  "legal_context": {
    "terminology_notes": [
      "'Proprietary information' translated as 'información propietaria' to maintain legal precision",
      "'Confidentiality' uses formal legal term 'confidencialidad'"
    ],
    "cultural_adaptations": [
      "Spanish employment law recognizes similar confidentiality obligations",
      "Duration and scope align with Spanish legal standards"
    ],
    "jurisdiction_notes": "This clause structure is compatible with Spanish employment law framework"
  },
  "confidence_score": 0.94,
  "translation_quality": "high",
  "legal_accuracy_score": 0.91,
  "processing_time": 1.2,
  "cached": false,
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/translate/document-summary
Translate complete document analysis summary with legal context.

**Rate Limit:** 10/minute (authenticated users only)
**Response Model:** `DocumentSummaryTranslationResponse`

**Request Body:**
```json
{
  "analysis_id": "uuid-string (required)",
  "target_language": "es (required)",
  "include_clauses": true,
  "include_recommendations": true,
  "cultural_adaptation": true
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "uuid-string",
  "target_language": "es",
  "language_name": "Spanish (Español)",
  "translated_summary": {
    "document_title": "Análisis de Contrato de Empleo",
    "overall_risk": {
      "level": "AMARILLO",
      "description": "Riesgo moderado con algunas áreas de preocupación"
    },
    "key_findings": [
      "Cláusulas estándar de confidencialidad y no competencia",
      "Paquete competitivo de salario y beneficios",
      "Términos poco claros de asignación de propiedad intelectual"
    ],
    "recommendations": [
      "Negociar procedimientos de terminación más claros",
      "Aclarar términos de propiedad intelectual",
      "Considerar revisión legal para cláusula de exención de responsabilidad"
    ]
  },
  "translated_clauses": [
    {
      "clause_id": "1",
      "original_text": "Employee agrees to maintain confidentiality...",
      "translated_text": "El Empleado acepta mantener confidencialidad...",
      "legal_context": "Cláusula estándar de confidencialidad compatible con la ley laboral española"
    }
  ],
  "cultural_adaptations": [
    "Risk levels adapted to Spanish legal context",
    "Recommendations consider Spanish employment law",
    "Terminology aligned with Spanish legal system"
  ],
  "translation_metadata": {
    "total_sections_translated": 8,
    "average_confidence": 0.92,
    "processing_time": 4.5,
    "legal_accuracy_score": 0.89
  }
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
Convert text to speech with neural voices optimized for legal content accessibility.

**Rate Limit:** 10/minute (anonymous), 20/minute (authenticated)
**Response:** Audio file (binary data)

**Request Body:**
```json
{
  "text": "string (required, 1-5000 chars)",
  "language_code": "en-US (optional, default: en-US)",
  "voice_gender": "NEUTRAL|MALE|FEMALE (optional, default: NEUTRAL)",
  "speaking_rate": 0.9,
  "pitch": 0.0,
  "audio_encoding": "MP3|WAV|OGG_OPUS (optional, default: MP3)",
  "voice_name": "string (optional, specific voice selection)",
  "optimize_for_legal": true
}
```

**Supported Language Codes:**
- **English**: en-US, en-GB, en-AU, en-CA, en-IN
- **Spanish**: es-ES, es-US, es-MX, es-AR
- **French**: fr-FR, fr-CA
- **German**: de-DE, de-AT
- **Italian**: it-IT
- **Portuguese**: pt-BR, pt-PT
- **Hindi**: hi-IN
- **Chinese**: zh-CN, zh-TW
- **Japanese**: ja-JP
- **Korean**: ko-KR
- **Russian**: ru-RU

**Voice Options:**
- **Neural Voices**: High-quality, natural-sounding voices
- **Standard Voices**: Basic text-to-speech voices
- **WaveNet Voices**: Premium quality with human-like intonation

**Legal Content Optimization:**
- Proper pronunciation of legal terminology
- Appropriate pacing for complex clauses
- Emphasis on important risk indicators
- Clear articulation of technical terms

**Response Headers:**
```
Content-Type: audio/mpeg (or audio/wav, audio/ogg)
Content-Disposition: attachment; filename="legal_analysis_audio.mp3"
Content-Length: 245760
X-Audio-Duration: 45.2
X-Voice-Used: en-US-Neural2-A
X-Processing-Time: 1.8
```

**Response Body:** Binary audio data

#### POST /api/speech/text-to-speech/info
Get text-to-speech metadata and cost estimation without generating audio.

**Rate Limit:** 15/minute
**Response Model:** `TextToSpeechInfoResponse`

**Request Body:** Same as `/api/speech/text-to-speech`

**Response:**
```json
{
  "success": true,
  "text_length": 1250,
  "estimated_duration_seconds": 45.2,
  "audio_content_type": "audio/mp3",
  "estimated_size_bytes": 245760,
  "language_code": "en-US",
  "voice_info": {
    "voice_name": "en-US-Neural2-A",
    "voice_gender": "FEMALE",
    "voice_type": "Neural",
    "language_name": "English (US)"
  },
  "processing_estimate": {
    "processing_time_seconds": 1.8,
    "cost_estimate": "$0.000016"
  },
  "legal_optimization": {
    "legal_terms_detected": 15,
    "pronunciation_adjustments": 8,
    "pacing_optimizations": 3
  },
  "accessibility_features": {
    "ssml_enhanced": true,
    "pause_optimization": true,
    "emphasis_markers": true
  },
  "error_message": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/speech/batch-text-to-speech
Convert multiple text sections to speech for complete document audio.

**Authentication Required:** Yes
**Rate Limit:** 5/minute
**Response Model:** `BatchTextToSpeechResponse`

**Request Body:**
```json
{
  "sections": [
    {
      "section_id": "summary",
      "text": "Document summary text...",
      "section_type": "summary"
    },
    {
      "section_id": "clause_1", 
      "text": "First clause text...",
      "section_type": "clause"
    }
  ],
  "language_code": "en-US",
  "voice_gender": "NEUTRAL",
  "audio_encoding": "MP3",
  "create_combined_audio": true
}
```

**Response:**
```json
{
  "success": true,
  "batch_id": "batch-uuid",
  "individual_audio_files": [
    {
      "section_id": "summary",
      "audio_url": "/api/speech/download/batch-uuid/summary.mp3",
      "duration_seconds": 25.4,
      "size_bytes": 152640
    },
    {
      "section_id": "clause_1",
      "audio_url": "/api/speech/download/batch-uuid/clause_1.mp3", 
      "duration_seconds": 18.7,
      "size_bytes": 112320
    }
  ],
  "combined_audio": {
    "audio_url": "/api/speech/download/batch-uuid/complete.mp3",
    "total_duration_seconds": 44.1,
    "total_size_bytes": 264960,
    "chapter_markers": [
      {"title": "Document Summary", "start_time": 0.0},
      {"title": "Clause 1", "start_time": 25.4}
    ]
  },
  "processing_time": 3.2,
  "expires_at": "2024-01-01T12:00:00Z"
}
```

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
Get AI-powered clarification with context-aware responses and conversation memory.

**Rate Limit:** 15/minute (anonymous), 25/minute (authenticated)
**Response Model:** `ClarificationResponse`

**Request Body:**
```json
{
  "question": "string (required, 5-1000 chars)",
  "context": {
    "document": {
      "analysis_id": "uuid-string",
      "document_type": "employment_contract",
      "overall_risk": "YELLOW",
      "summary": "Employment contract with standard terms and moderate risk",
      "total_clauses": 8,
      "key_findings": ["Standard confidentiality clause", "Competitive salary"]
    },
    "clause": {
      "clause_id": "confidentiality_1",
      "text": "Employee agrees to maintain strict confidentiality...",
      "risk_level": "YELLOW",
      "plain_explanation": "This requires you to keep company information secret",
      "legal_implications": ["Cannot share confidential information"],
      "recommendations": ["Ensure you understand what constitutes confidential information"]
    },
    "conversation_history": [
      {
        "question": "What does this confidentiality clause mean?",
        "response": "This clause requires you to keep company information secret...",
        "timestamp": "2024-01-01T10:00:00Z"
      }
    ]
  },
  "user_expertise_level": "beginner|intermediate|expert",
  "conversation_id": "conv-uuid (optional)",
  "follow_up_context": true,
  "request_examples": true
}
```

**AI Service Integration:**
- **Primary**: Gemini API for advanced legal reasoning
- **Fallback**: Groq API for high availability
- **Emergency**: Keyword-based responses for service outages

**Experience-Level Adaptation:**
- **Beginner**: Simple explanations with real-world examples
- **Intermediate**: Balanced technical and plain language
- **Expert**: Detailed legal analysis with precedents and citations

**Response:**
```json
{
  "success": true,
  "response": "This confidentiality clause is quite standard and reasonable. It means you cannot share any proprietary company information like trade secrets, client lists, or internal processes with anyone outside the company. The good news is that it's limited to truly confidential information, not general knowledge you gain from working there. For example, you couldn't share the company's secret recipe or client database, but you could mention general skills you learned.",
  "conversation_id": "conv-uuid",
  "confidence_score": 92,
  "response_quality": "high",
  "processing_time": 1.4,
  "ai_service_used": "gemini",
  "fallback_used": false,
  "context_understanding": {
    "document_context_used": true,
    "clause_context_used": true,
    "conversation_history_used": true,
    "expertise_level_adapted": true
  },
  "follow_up_suggestions": [
    "What happens if I accidentally share confidential information?",
    "How long does this confidentiality obligation last?",
    "What exactly counts as confidential information?"
  ],
  "related_clauses": [
    {
      "clause_id": "non_compete_2",
      "relevance": "Related to information protection",
      "suggestion": "You might also want to ask about the non-compete clause"
    }
  ],
  "examples_provided": [
    "Trade secrets (like proprietary formulas or processes)",
    "Client lists and contact information", 
    "Internal financial data and projections"
  ],
  "legal_precedents": [
    {
      "case_reference": "Similar confidentiality clauses upheld in 89% of employment cases",
      "jurisdiction": "US",
      "relevance": "Standard enforceability"
    }
  ],
  "risk_assessment": {
    "clause_enforceability": "high",
    "user_risk_level": "low",
    "negotiation_potential": "limited"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/ai/conversation/{conversation_id}
Get complete conversation history and analytics.

**Authentication Required:** Yes (must be conversation owner)
**Response Model:** `ConversationDetailResponse`

**Response:**
```json
{
  "success": true,
  "conversation_id": "conv-uuid",
  "document_context": {
    "analysis_id": "uuid-string",
    "document_type": "employment_contract",
    "document_title": "Employment Agreement Analysis"
  },
  "conversation_history": [
    {
      "message_id": "msg-1",
      "question": "What does this confidentiality clause mean?",
      "response": "This confidentiality clause requires...",
      "confidence_score": 92,
      "timestamp": "2024-01-01T10:00:00Z",
      "ai_service": "gemini"
    }
  ],
  "conversation_analytics": {
    "total_messages": 5,
    "average_confidence": 0.89,
    "topics_discussed": ["confidentiality", "termination", "benefits"],
    "user_satisfaction_indicators": {
      "follow_up_questions": 3,
      "clarification_requests": 1,
      "topic_completion_rate": 0.8
    }
  },
  "conversation_summary": "User asked detailed questions about employment contract terms, focusing on confidentiality obligations and termination procedures. High engagement with follow-up questions indicates good understanding development.",
  "created_at": "2024-01-01T09:30:00Z",
  "last_updated": "2024-01-01T10:15:00Z"
}
```

#### POST /api/ai/conversation/feedback
Provide feedback on AI responses for continuous improvement.

**Authentication Required:** Yes
**Rate Limit:** 50/minute

**Request Body:**
```json
{
  "conversation_id": "conv-uuid",
  "message_id": "msg-1", 
  "feedback_type": "helpful|not_helpful|incorrect|unclear",
  "rating": 4,
  "comment": "Very clear explanation with good examples",
  "improvement_suggestions": ["Could include more legal precedents"]
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": "feedback-uuid",
  "message": "Thank you for your feedback. This helps improve our AI responses.",
  "feedback_processed": true
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

### Authentication Endpoints

#### POST /api/auth/verify-token
Verify Firebase ID token for authenticated access.

**Request Body:**
```json
{
  "token": "firebase_id_token_string"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "uid": "user_id",
    "email": "user@example.com",
    "display_name": "User Name"
  }
}
```

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "display_name": "User Name"
}
```

### Expert Review Endpoints (Human-in-the-Loop System)

#### POST /api/expert-queue/submit
Submit document for expert review when AI confidence is low (<60%).

**Authentication Required:** Yes (Firebase)
**Rate Limit:** 5 requests/day per user
**Response Model:** `ExpertReviewSubmissionResponse`

**Request Body:**
```json
{
  "analysis_id": "uuid-string (required)",
  "user_email": "user@example.com (required)",
  "priority": "HIGH|MEDIUM|LOW (optional, default: MEDIUM)",
  "user_message": "Optional message for the expert (max 500 chars)",
  "consent_to_review": true,
  "notification_preferences": {
    "email_updates": true,
    "sms_updates": false
  }
}
```

**Automatic Triggering:**
- AI confidence < 60% triggers automatic expert review option
- Complex multi-party agreements
- Documents with unusual or non-standard clauses
- User-requested verification for high-stakes decisions

**Response:**
```json
{
  "success": true,
  "review_id": "expert-review-uuid",
  "queue_position": 3,
  "estimated_completion": "2024-01-01T16:00:00Z",
  "priority": "MEDIUM",
  "expert_assigned": false,
  "tracking_url": "/api/expert-queue/status/expert-review-uuid",
  "notification_email_sent": true,
  "message": "Your document has been queued for expert review"
}
```

#### GET /api/expert-queue/status/{review_id}
Check status and progress of expert review request.

**Authentication Required:** Yes (must be document owner)
**Response Model:** `ExpertReviewStatusResponse`

**Response:**
```json
{
  "review_id": "expert-review-uuid",
  "status": "PENDING|IN_REVIEW|COMPLETED|DELIVERED|CANCELLED",
  "queue_position": 2,
  "estimated_completion": "2024-01-01T16:00:00Z",
  "actual_completion": null,
  "expert_assigned": true,
  "expert_info": {
    "expert_id": "expert-uuid",
    "specialization": "Employment Law",
    "years_experience": 12,
    "rating": 4.8
  },
  "progress": {
    "percentage": 75,
    "current_stage": "Legal Analysis",
    "stages_completed": ["Initial Review", "Risk Assessment"],
    "stages_remaining": ["Final Review", "Report Generation"]
  },
  "priority": "MEDIUM",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T14:30:00Z",
  "notifications_sent": 2,
  "estimated_delivery": "2024-01-01T17:00:00Z"
}
```

#### GET /api/expert-queue/user-reviews
Get all expert reviews for authenticated user.

**Authentication Required:** Yes
**Query Parameters:**
- `status`: Filter by status (optional)
- `limit`: Number of results (default: 10, max: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "reviews": [
    {
      "review_id": "expert-review-uuid",
      "document_title": "Employment Contract Analysis",
      "status": "COMPLETED",
      "priority": "HIGH",
      "created_at": "2024-01-01T10:00:00Z",
      "completed_at": "2024-01-01T16:30:00Z",
      "expert_rating": 4.9
    }
  ],
  "total_count": 5,
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

#### POST /api/expert-queue/cancel/{review_id}
Cancel pending expert review request.

**Authentication Required:** Yes (must be document owner)
**Response:**
```json
{
  "success": true,
  "review_id": "expert-review-uuid",
  "status": "CANCELLED",
  "refund_issued": false,
  "message": "Expert review cancelled successfully"
}
```

#### GET /api/expert-queue/experts
Get list of available legal experts and their specializations.

**Response:**
```json
{
  "success": true,
  "experts": [
    {
      "expert_id": "expert-uuid",
      "name": "Dr. Sarah Johnson",
      "specializations": ["Employment Law", "Contract Law"],
      "years_experience": 15,
      "rating": 4.9,
      "reviews_completed": 1250,
      "average_turnaround_hours": 6,
      "languages": ["English", "Spanish"],
      "certifications": ["Bar Certified", "JD Harvard Law"]
    }
  ],
  "total_experts": 25,
  "average_rating": 4.7,
  "average_turnaround": "4-8 hours"
}
```

### Vision API Endpoints

The Vision API endpoints provide advanced image text extraction and document analysis capabilities using Google Cloud Vision API with intelligent preprocessing and fallback mechanisms.

#### POST /api/vision/extract-text
Extract text from uploaded image using Google Cloud Vision API with legal document optimization.

**Rate Limit:** 10/minute (anonymous), 100/day (authenticated)
**Cost Monitoring**: $1.50 per user per day limit
**Response Model:** `VisionTextExtractionResponse`

**Request (multipart/form-data):**
- `file`: Image file (required, max 20MB)
- `preprocess`: Enable image preprocessing for legal documents (default: true)
- `confidence_threshold`: Minimum confidence for text inclusion (default: 0.7)

**Supported Image Formats:**
- **JPEG/JPG**: Recommended for photos and scanned documents
- **PNG**: Recommended for screenshots and digital images  
- **WEBP**: Modern format with good compression
- **BMP**: Uncompressed bitmap format
- **GIF**: Basic support (static images only)

**Technical Specifications:**
- Maximum file size: 20MB
- Maximum resolution: 4096x4096 pixels
- Minimum resolution: 100x100 pixels
- Supported color spaces: RGB, Grayscale
- DPI optimization: 300+ DPI recommended for best results

**Image Preprocessing Features:**
- Contrast enhancement for low-quality scans
- Noise reduction for mobile photos
- Skew correction for angled documents
- Legal document layout optimization

**Response:**
```json
{
  "success": true,
  "filename": "employment_contract.jpg",
  "extracted_text": "EMPLOYMENT AGREEMENT\n\nThis Employment Agreement is entered into...",
  "high_confidence_text": "Text blocks with confidence > 70%",
  "confidence_scores": {
    "average_confidence": 0.87,
    "high_confidence_ratio": 0.82,
    "min_confidence_threshold": 0.7,
    "total_text_blocks": 28,
    "high_confidence_blocks": 23,
    "low_confidence_blocks": 5
  },
  "text_blocks_detected": 28,
  "legal_sections_identified": 5,
  "document_structure": {
    "title_detected": true,
    "paragraphs_identified": 12,
    "clauses_detected": 8,
    "signature_blocks": 2
  },
  "processing_metadata": {
    "api_used": "Google Cloud Vision API",
    "processing_time": 2.3,
    "image_preprocessing_applied": true,
    "preprocessing_operations": ["contrast_enhancement", "noise_reduction"],
    "ocr_model": "latest",
    "language_detected": "en"
  },
  "image_analysis": {
    "width": 1200,
    "height": 1600,
    "size_bytes": 345760,
    "format": "JPEG",
    "quality_score": 0.85,
    "text_density": 0.72
  },
  "warnings": [
    "Some text blocks have confidence below 80%",
    "Consider using higher resolution scan for better accuracy"
  ],
  "cost_info": {
    "api_calls_used": 1,
    "daily_usage": 15,
    "daily_limit": 100
  }
}
```

**Error Responses:**

**Vision API Not Available:**
```json
{
  "success": false,
  "filename": "contract.jpg",
  "extracted_text": "",
  "error": "Vision API not configured - image text extraction not available",
  "error_code": "VISION_API_UNAVAILABLE",
  "fallback_used": true,
  "image_info": {
    "width": 1200,
    "height": 800,
    "size_bytes": 245760,
    "format": "JPEG"
  },
  "suggestions": [
    "Configure Google Cloud Vision API credentials",
    "Try uploading as PDF instead",
    "Use text input for manual entry"
  ]
}
```

**Rate Limit Exceeded:**
```json
{
  "success": false,
  "error": "Vision API rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "daily_usage": 100,
  "daily_limit": 100,
  "reset_time": "2024-01-02T00:00:00Z",
  "suggestions": [
    "Try again after rate limit reset",
    "Upgrade to higher tier for increased limits",
    "Use document upload instead of image"
  ]
}
```

#### POST /api/vision/analyze-document
Analyze legal document from image using Vision API + document analysis pipeline.

**Rate Limit:** 5 requests/minute

**Request (multipart/form-data):**
- `file`: Image file (JPEG, PNG, WEBP, BMP, GIF, max 20MB)
- `document_type`: Document type (default: "general_contract")
- `user_expertise_level`: User expertise level (default: "beginner")

**Response:**
```json
{
  "success": true,
  "analysis_id": "uuid-string",
  "filename": "contract.jpg",
  "text_extraction": {
    "method": "Google Cloud Vision API",
    "extracted_text_length": 2450,
    "confidence_scores": {
      "average_confidence": 0.85,
      "high_confidence_ratio": 0.78,
      "min_confidence_threshold": 0.7,
      "total_text_blocks": 25,
      "high_confidence_blocks": 20
    },
    "text_blocks_detected": 25,
    "legal_sections_identified": 3
  },
  "document_analysis": {
    "overall_risk": {
      "level": "YELLOW",
      "score": 0.65,
      "severity": "moderate",
      "confidence_percentage": 82
    },
    "total_clauses": 8,
    "processing_time": 3.2,
    "summary": "Document analysis summary"
  },
  "warnings": [
    "Text extraction confidence is below 80%. Legal analysis may be affected by OCR inaccuracies."
  ]
}
```

#### GET /api/vision/status
Get status of Vision API services.

**Response:**
```json
{
  "dual_vision_service": {
    "enabled": true,
    "fallback_enabled": true
  },
  "document_ai": {
    "enabled": true,
    "project_id": "your-project-id",
    "location": "us-central1",
    "connectivity": "connected"
  },
  "vision_api": {
    "enabled": true,
    "project_id": "your-project-id", 
    "location": "us-central1",
    "connectivity": "connected"
  },
  "vision_api_details": {
    "supported_formats": ["JPEG", "PNG", "WEBP", "BMP", "GIF"],
    "max_file_size_mb": 20,
    "max_resolution": [4096, 4096],
    "min_confidence_threshold": 0.7,
    "rate_limit_per_day": 100,
    "cache_ttl_hours": 1
  }
}
```

#### GET /api/vision/supported-formats
Get list of supported file formats for Vision API.

**Response:**
```json
{
  "success": true,
  "supported_formats": {
    "images": [
      "image/jpeg", "image/jpg", "image/png",
      "image/webp", "image/bmp", "image/gif"
    ],
    "documents": [
      "application/pdf", "application/x-pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain"
    ]
  },
  "file_size_limits": {
    "images": "20MB",
    "documents": "20MB"
  },
  "processing_methods": {
    "images": "Google Cloud Vision API",
    "pdfs": "Google Document AI",
    "fallback": "Basic text extraction"
  }
}
```

**Vision API Rate Limits:**
- Text extraction: 100 requests per user per day
- Cost monitoring: $1.50 per user per day
- Response caching: 1 hour TTL
- Automatic fallback when limits exceeded

**Vision API Error Codes:**
- `503`: Vision API service not available
- `429`: Rate limit exceeded (100 requests/day)
- `413`: File size exceeds 20MB limit
- `422`: Unsupported image format or corrupted file
- `400`: Image too small (minimum 100x100 pixels)

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

### Semantic Search Endpoints (Vertex AI)

#### POST /api/search/similar-documents
Find similar legal documents using semantic search.

**Rate Limit:** 10 requests/minute
**Authentication Required:** Yes

**Request Body:**
```json
{
  "document_text": "string",
  "document_type": "rental_agreement|employment_contract|nda|loan_agreement|partnership_agreement|general_contract",
  "similarity_threshold": 0.8,
  "max_results": 10
}
```

**Response:**
```json
{
  "success": true,
  "similar_documents": [
    {
      "document_id": "string",
      "similarity_score": 0.92,
      "document_type": "employment_contract",
      "key_clauses": ["non_compete", "termination"],
      "risk_level": "YELLOW"
    }
  ],
  "total_results": 5,
  "processing_time": 1.8
}
```

#### POST /api/search/clause-precedents
Search for legal precedents and similar clauses.

**Rate Limit:** 15 requests/minute
**Authentication Required:** Yes

**Request Body:**
```json
{
  "clause_text": "string",
  "legal_domain": "employment|real_estate|business|intellectual_property",
  "jurisdiction": "US|UK|CA|AU|IN"
}
```

**Response:**
```json
{
  "success": true,
  "precedents": [
    {
      "precedent_id": "string",
      "similarity_score": 0.89,
      "case_reference": "Smith v. Johnson (2023)",
      "jurisdiction": "US",
      "outcome": "Clause upheld with modifications",
      "key_insights": ["Enforceability depends on geographic scope"]
    }
  ],
  "legal_analysis": "string",
  "recommendations": ["string"]
}
```

### Email Notification Endpoints

The email system uses Firebase Gmail OAuth2 for secure, professional email delivery with user consent and comprehensive tracking.

#### POST /api/email/send-analysis-report
Send comprehensive analysis report via secure Gmail OAuth2 integration.

**Rate Limit:** 5 requests/hour per user
**Authentication Required:** Yes (Firebase + Gmail OAuth2)
**Response Model:** `EmailDeliveryResponse`

**Request Body:**
```json
{
  "recipient_email": "user@example.com (required)",
  "analysis_id": "uuid-string (required)",
  "email_options": {
    "include_pdf": true,
    "include_word": false,
    "include_summary": true,
    "include_recommendations": true
  },
  "custom_message": "Optional personal message (max 500 chars)",
  "delivery_options": {
    "priority": "normal|high",
    "read_receipt": false,
    "encryption": true
  },
  "branding": {
    "use_professional_template": true,
    "include_logo": true,
    "custom_footer": "Optional custom footer text"
  }
}
```

**Gmail OAuth2 Requirements:**
- User must grant Gmail access permissions
- Secure token management with automatic refresh
- Professional email templates with LegalSaathi branding
- Encrypted attachment handling

**Response:**
```json
{
  "success": true,
  "email_id": "email-uuid",
  "gmail_message_id": "gmail-msg-id",
  "delivery_status": "sent",
  "recipient_email": "user@example.com",
  "attachments_included": [
    {
      "filename": "Legal_Analysis_Report.pdf",
      "size_bytes": 245760,
      "type": "application/pdf"
    }
  ],
  "email_metadata": {
    "subject": "Your Legal Document Analysis Report",
    "template_used": "professional_analysis_report",
    "encryption_used": true,
    "priority": "normal"
  },
  "tracking_info": {
    "tracking_id": "track-uuid",
    "delivery_confirmation": true,
    "read_receipt_requested": false
  },
  "estimated_delivery": "2024-01-01T00:02:00Z",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/email/send-expert-notification
Send expert review notification and status updates.

**Rate Limit:** 10 requests/hour per user
**Authentication Required:** Yes
**Internal Use**: Primarily used by expert review system

**Request Body:**
```json
{
  "recipient_email": "user@example.com",
  "notification_type": "review_started|review_completed|review_delayed",
  "review_id": "expert-review-uuid",
  "expert_info": {
    "expert_name": "Dr. Sarah Johnson",
    "specialization": "Employment Law",
    "estimated_completion": "2024-01-01T16:00:00Z"
  },
  "status_update": {
    "current_status": "IN_REVIEW",
    "progress_percentage": 75,
    "next_milestone": "Final Review"
  }
}
```

**Response:**
```json
{
  "success": true,
  "email_id": "email-uuid",
  "notification_type": "review_completed",
  "delivery_status": "sent",
  "template_used": "expert_review_completion",
  "includes_results": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/email/delivery-status/{email_id}
Check comprehensive email delivery status and tracking information.

**Authentication Required:** Yes (must be email sender)
**Response Model:** `EmailStatusResponse`

**Response:**
```json
{
  "email_id": "email-uuid",
  "gmail_message_id": "gmail-msg-id",
  "status": "sent|delivered|opened|failed|bounced|spam",
  "delivery_timeline": {
    "sent_at": "2024-01-01T00:00:00Z",
    "delivered_at": "2024-01-01T00:00:15Z",
    "opened_at": "2024-01-01T00:05:30Z",
    "last_activity": "2024-01-01T00:05:30Z"
  },
  "recipient_info": {
    "email": "user@example.com",
    "delivery_confirmed": true,
    "bounce_reason": null
  },
  "attachments_status": [
    {
      "filename": "Legal_Analysis_Report.pdf",
      "delivered": true,
      "downloaded": true,
      "download_count": 2
    }
  ],
  "engagement_metrics": {
    "opened": true,
    "open_count": 3,
    "time_spent_reading": 180,
    "links_clicked": 1
  },
  "error_details": null,
  "retry_attempts": 0,
  "final_status": "delivered_and_opened"
}
```

#### GET /api/email/user-history
Get email history for authenticated user.

**Authentication Required:** Yes
**Query Parameters:**
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by delivery status (optional)
- `type`: Filter by email type (optional)

**Response:**
```json
{
  "success": true,
  "emails": [
    {
      "email_id": "email-uuid",
      "type": "analysis_report",
      "recipient": "user@example.com",
      "subject": "Your Legal Document Analysis Report",
      "status": "delivered",
      "sent_at": "2024-01-01T00:00:00Z",
      "attachments_count": 1,
      "opened": true
    }
  ],
  "pagination": {
    "total_count": 15,
    "limit": 20,
    "offset": 0,
    "has_more": false
  },
  "summary_stats": {
    "total_emails_sent": 15,
    "delivery_rate": 0.93,
    "open_rate": 0.87,
    "most_recent": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /api/email/oauth/authorize
Initiate Gmail OAuth2 authorization flow.

**Authentication Required:** Yes (Firebase)
**Response:**
```json
{
  "success": true,
  "authorization_url": "https://accounts.google.com/oauth2/auth?...",
  "state": "oauth-state-uuid",
  "expires_in": 600,
  "scopes": ["https://www.googleapis.com/auth/gmail.send"]
}
```

#### POST /api/email/oauth/callback
Handle Gmail OAuth2 callback and store tokens.

**Authentication Required:** Yes
**Request Body:**
```json
{
  "code": "oauth-authorization-code",
  "state": "oauth-state-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "gmail_authorized": true,
  "user_email": "user@gmail.com",
  "permissions_granted": ["gmail.send"],
  "token_expires_at": "2024-01-01T01:00:00Z"
}
```

### Knowledge Graph Endpoints (Neo4j)

#### GET /api/knowledge-graph/entity-relationships/{entity_id}
Get relationships for a legal entity.

**Rate Limit:** 20 requests/minute
**Authentication Required:** Yes

**Response:**
```json
{
  "entity_id": "string",
  "entity_type": "person|company|contract|clause",
  "relationships": [
    {
      "related_entity_id": "string",
      "relationship_type": "party_to|contains|references",
      "strength": 0.85,
      "context": "Employment contract relationship"
    }
  ],
  "total_relationships": 12
}
```

#### POST /api/knowledge-graph/query
Execute custom Cypher query on legal knowledge graph.

**Rate Limit:** 10 requests/minute
**Authentication Required:** Yes (Admin only)

**Request Body:**
```json
{
  "cypher_query": "MATCH (c:Contract)-[:CONTAINS]->(cl:Clause) WHERE cl.risk_level = 'HIGH' RETURN c, cl LIMIT 10",
  "parameters": {}
}
```

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

#### POST /api/tasks/rebuild-knowledge-graph
Rebuild Neo4j knowledge graph from recent analyses.

**Authentication Required:** Yes (Admin only)

**Response:**
```json
{
  "success": true,
  "message": "Knowledge graph rebuild initiated",
  "estimated_completion": "2024-01-01T01:00:00Z"
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

## Comprehensive Request/Response Examples

### Complete Document Analysis Workflow

#### 1. Document Upload and Analysis

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/analyze/file" \
  -H "Authorization: Bearer firebase-id-token" \
  -F "file=@employment_contract.pdf" \
  -F "document_type=employment_contract" \
  -F "user_expertise_level=beginner"
```

**Response:**
```json
{
  "analysis_id": "analysis-uuid-123",
  "file_metadata": {
    "original_filename": "employment_contract.pdf",
    "file_size_bytes": 245760,
    "file_type": "application/pdf",
    "processing_method": "document_ai",
    "text_extraction_confidence": 0.95,
    "pages_processed": 3
  },
  "overall_risk": {
    "level": "YELLOW",
    "score": 0.68,
    "severity": "moderate",
    "confidence_percentage": 87,
    "reasons": [
      "Broad non-compete clause may limit future employment",
      "Intellectual property assignment terms are extensive"
    ],
    "risk_categories": {
      "financial": 0.4,
      "legal": 0.8,
      "operational": 0.6,
      "compliance": 0.7
    }
  },
  "overall_confidence": 0.87,
  "should_route_to_expert": false,
  "confidence_breakdown": {
    "clause_analysis_confidence": 0.89,
    "document_summary_confidence": 0.85,
    "risk_assessment_confidence": 0.87,
    "factors_affecting_confidence": [
      "Standard employment contract structure",
      "Clear legal language throughout"
    ]
  },
  "clause_assessments": [
    {
      "clause_id": "confidentiality_1",
      "clause_text": "Employee agrees to maintain strict confidentiality regarding all proprietary information, trade secrets, and confidential business information...",
      "risk_assessment": {
        "level": "GREEN",
        "score": 0.3,
        "severity": "low",
        "confidence_percentage": 92,
        "reasons": ["Standard confidentiality clause with reasonable scope"]
      },
      "plain_explanation": "This clause requires you to keep company secrets confidential. It's a standard and reasonable requirement that protects the company's business information while you work there and after you leave.",
      "legal_implications": [
        "You cannot share confidential company information with competitors",
        "Violation could result in legal action and damages",
        "Obligation continues after employment ends"
      ],
      "recommendations": [
        "Ask for clarification on what constitutes 'confidential information'",
        "Ensure personal knowledge and skills are not restricted"
      ],
      "enhanced_insights": {
        "precedent_analysis": "Similar clauses upheld in 89% of employment cases",
        "industry_standard": true,
        "negotiation_difficulty": "low"
      }
    }
  ],
  "summary": "This employment contract contains standard terms with moderate risk levels. The confidentiality and intellectual property clauses are comprehensive but within normal bounds. Key areas requiring attention include the non-compete clause scope and termination procedures.",
  "key_findings": [
    "Standard confidentiality and non-compete clauses present",
    "Competitive salary and benefits package outlined",
    "Intellectual property assignment is comprehensive",
    "Termination procedures could be clearer"
  ],
  "recommendations": [
    "Negotiate the geographic scope of the non-compete clause",
    "Clarify what constitutes 'work-related inventions'",
    "Request more specific termination notice requirements"
  ],
  "processing_time": 3.2,
  "timestamp": "2024-01-01T00:00:00Z",
  "privacy_processing": {
    "pii_detected": true,
    "pii_types_masked": ["email", "phone", "address", "ssn"],
    "masking_confidence": 0.98,
    "audit_id": "privacy-audit-uuid"
  }
}
```

#### 2. AI Assistant Clarification

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/ai/clarify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer firebase-id-token" \
  -d '{
    "question": "What exactly does the non-compete clause mean for my future job prospects?",
    "context": {
      "document": {
        "analysis_id": "analysis-uuid-123",
        "document_type": "employment_contract",
        "overall_risk": "YELLOW"
      },
      "clause": {
        "clause_id": "non_compete_2",
        "text": "Employee agrees not to engage in any business that competes...",
        "risk_level": "YELLOW"
      }
    },
    "user_expertise_level": "beginner",
    "request_examples": true
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "The non-compete clause means you cannot work for a direct competitor or start a competing business for a specific period after leaving this job. In your case, it appears to restrict you for 6 months within a 50-mile radius. This is actually quite reasonable compared to some contracts that restrict for 1-2 years or have broader geographic limits. However, it could limit your job options immediately after leaving, so you should consider this when making your decision.",
  "conversation_id": "conv-uuid-456",
  "confidence_score": 94,
  "response_quality": "high",
  "follow_up_suggestions": [
    "What happens if I accidentally violate the non-compete?",
    "Can I negotiate the time period or geographic scope?",
    "Does this apply if I'm fired versus if I quit?"
  ],
  "examples_provided": [
    "You couldn't work for a direct competitor like [Company X] for 6 months",
    "You couldn't start your own competing business in the same area",
    "You could work in a different industry or location outside the 50-mile radius"
  ],
  "legal_precedents": [
    {
      "case_reference": "6-month non-compete clauses upheld in 78% of cases when geographic scope is reasonable",
      "jurisdiction": "US",
      "relevance": "Similar time and geographic restrictions"
    }
  ],
  "risk_assessment": {
    "enforceability": "high",
    "user_impact": "moderate",
    "negotiation_potential": "medium"
  }
}
```

#### 3. Translation to Spanish

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/translate/document-summary" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer firebase-id-token" \
  -d '{
    "analysis_id": "analysis-uuid-123",
    "target_language": "es",
    "include_clauses": true,
    "cultural_adaptation": true
  }'
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "analysis-uuid-123",
  "target_language": "es",
  "language_name": "Spanish (Español)",
  "translated_summary": {
    "document_title": "Análisis de Contrato de Empleo",
    "overall_risk": {
      "level": "AMARILLO",
      "description": "Riesgo moderado con algunas áreas que requieren atención"
    },
    "key_findings": [
      "Cláusulas estándar de confidencialidad y no competencia presentes",
      "Paquete competitivo de salario y beneficios descrito",
      "Asignación de propiedad intelectual es integral"
    ],
    "recommendations": [
      "Negociar el alcance geográfico de la cláusula de no competencia",
      "Aclarar qué constituye 'invenciones relacionadas con el trabajo'",
      "Solicitar requisitos más específicos de aviso de terminación"
    ]
  },
  "cultural_adaptations": [
    "Términos de riesgo adaptados al contexto legal español",
    "Recomendaciones consideran la ley laboral española",
    "Terminología alineada con el sistema legal español"
  ],
  "translation_metadata": {
    "total_sections_translated": 8,
    "average_confidence": 0.94,
    "legal_accuracy_score": 0.91
  }
}
```

#### 4. Expert Review Submission (Low Confidence Case)

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/expert-queue/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer firebase-id-token" \
  -d '{
    "analysis_id": "analysis-uuid-456",
    "user_email": "user@example.com",
    "priority": "HIGH",
    "user_message": "This is a complex merger agreement and I need expert verification of the AI analysis before proceeding."
  }'
```

**Response:**
```json
{
  "success": true,
  "review_id": "expert-review-uuid-789",
  "queue_position": 2,
  "estimated_completion": "2024-01-01T16:00:00Z",
  "priority": "HIGH",
  "expert_assigned": false,
  "message": "Your document has been queued for expert review due to complexity and high stakes nature.",
  "notification_email_sent": true,
  "tracking_url": "/api/expert-queue/status/expert-review-uuid-789"
}
```

### Voice Processing Example

#### Speech-to-Text for Document Input

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/speech/speech-to-text" \
  -H "Authorization: Bearer firebase-id-token" \
  -F "audio_file=@contract_reading.wav" \
  -F "language_code=en-US" \
  -F "enable_punctuation=true"
```

**Response:**
```json
{
  "success": true,
  "transcript": "This employment agreement is entered into between ABC Corporation and John Smith. The employee agrees to maintain confidentiality regarding all proprietary information and trade secrets.",
  "confidence": 0.94,
  "language_detected": "en-US",
  "processing_time": 2.1,
  "legal_terms_detected": [
    "employment agreement",
    "confidentiality",
    "proprietary information",
    "trade secrets"
  ],
  "word_count": 28,
  "character_count": 156
}
```

### Image Processing Example

#### Vision API Text Extraction

**Request:**
```bash
curl -X POST "https://legalsaathi-document-advisor.onrender.com/api/vision/extract-text" \
  -H "Authorization: Bearer firebase-id-token" \
  -F "file=@scanned_contract.jpg" \
  -F "preprocess=true"
```

**Response:**
```json
{
  "success": true,
  "filename": "scanned_contract.jpg",
  "extracted_text": "EMPLOYMENT AGREEMENT\n\nThis Employment Agreement (\"Agreement\") is entered into as of January 1, 2024...",
  "confidence_scores": {
    "average_confidence": 0.89,
    "high_confidence_ratio": 0.85,
    "total_text_blocks": 32,
    "high_confidence_blocks": 27
  },
  "document_structure": {
    "title_detected": true,
    "paragraphs_identified": 15,
    "clauses_detected": 12,
    "signature_blocks": 2
  },
  "processing_metadata": {
    "api_used": "Google Cloud Vision API",
    "processing_time": 2.8,
    "preprocessing_operations": ["contrast_enhancement", "skew_correction"]
  }
}
```

## SDK and Integration

### JavaScript/TypeScript SDK

```typescript
interface LegalSaathiConfig {
  baseURL?: string;
  apiKey?: string;
  firebaseToken?: string;
}

class LegalSaathiAPI {
  private baseURL: string;
  private firebaseToken?: string;

  constructor(config: LegalSaathiConfig = {}) {
    this.baseURL = config.baseURL || 'https://legalsaathi-document-advisor.onrender.com';
    this.firebaseToken = config.firebaseToken;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (this.firebaseToken) {
      headers['Authorization'] = `Bearer ${this.firebaseToken}`;
    }
    
    return headers;
  }

  async analyzeDocument(params: {
    text: string;
    documentType: string;
    expertiseLevel?: 'beginner' | 'intermediate' | 'expert';
  }) {
    const response = await fetch(`${this.baseURL}/api/analyze`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        document_text: params.text,
        document_type: params.documentType,
        user_expertise_level: params.expertiseLevel || 'beginner'
      })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  async analyzeFile(file: File, documentType: string, expertiseLevel: string = 'beginner') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('user_expertise_level', expertiseLevel);

    const headers: HeadersInit = {};
    if (this.firebaseToken) {
      headers['Authorization'] = `Bearer ${this.firebaseToken}`;
    }

    const response = await fetch(`${this.baseURL}/api/analyze/file`, {
      method: 'POST',
      headers,
      body: formData
    });

    return response.json();
  }

  async translateText(params: {
    text: string;
    targetLanguage: string;
    sourceLanguage?: string;
    includeLegalContext?: boolean;
  }) {
    const response = await fetch(`${this.baseURL}/api/translate`, {
      method: T',

      body: JSON.stringify({

        target_language: params.targee,
',
        include_legal_context: params.i
      })


    return response.json();
  }

  async
 ;
    context: any;
    expertiseLevel?: string;
    conversationId?: string;
  }) {
    const response = await ffy`, {
 
   ),
fy({
        questn,
       ,
 
        conversatiionId
      })
    }

    return response.json();
  }

  async submitForExpertReviews: {
    analysisId: string;
    uing;
    LOW';
    message?: string;
  }) {
    const response = await fetch(`${this.baseURL}/api/`, {
      method: 'POST',
    
      body: JSON.stringify({
        analysis_id: parId,
 l,
   M',
,
        consent_to_review: true
})
    });

on();
  }

  async getExring) {
    con
 
    });

    return response.
  }

  async extractTextFromImage(file: File, preprocess: boolean {
    const formData = nermData();
    formData.append('file', file);
    f;

    const headers: Het = {};
    if (this.firebaseToken) {
      headers['Authorization'] = `Bearer ${this.firebaseT
    }

  {
   ',
eaders,
      body: formData
});

    return response.json();

}

// Usage Exame
const a{
 '
});

// Analyze a document
const analysis = await api.analyt({
  text: "This employment..",
  documentType: "employmen,
  expertiseLevel: "beginner"
});

// Aion
const clarification I({
  question: "What does this claus,
  context: { document: analysis },
  expertiseLevel: "beginner"
});
```

### Python SDK

`thon
impts
n
from typing import Optional, DList



    def __init__(self, base_url: str = "https://legalsaathi-document-advisor.onrender.com", 
] = None):
        self.base_url = brl
        self.firebase_token = firebase_token
        self.session = requests.Session()
        
        if firebase_token:
            self.session.headers.update({
                'Authorization': f'Bearer {fir
})
    
    def _make_request(self, method: str, endpoint: str, **kwargs)
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)

            return response.jso)
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def analyze_document(self, text: str, document_type: str, 
                        expertise_level: str
        """Analyze legal document text"""
 {
            "document_text": text,
            "document_type": document_type,
            "user_expertise_level": expertise_level
        }
        
        return self._make_request('POST', '/ap)
    
, 
                    expertise_level]:
        """Analyze document file"""
        file_path = Path(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.na
            data = {
pe,
                'user_expertise_levl
            }
            
            # Remove Content-Type header for multipart/form-data
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']

            return self._make_request('P, 
                                    files=files, data=data,rs)
    
    def translate_text(self, text: str, target_language: str, 
                      source_language: str = "auto", 
                      include_legal_context: boo:
        """Translate text with legal context"""
d = {
            "text": text,
            "target_language": target_language,
            "source_language": source_language,
            "include_legal_context": include_legal_context
        }
        
        return self._make_request('POST', '/api/translate', json=payloa)
   
    def translate_clause(self, clause_

        """Translate individual clause
        payload = {
            "clause_id": clause_id,
            "clause_text": clause_text,
            "target_language": target_language,
            "include_legal_context": True,

        }
        
        return self._make_request('POST', '/api/translate/clause', json=payloa)
    
    def ask_ai(self, question: str, context: Dict[Any, Any], 
              expertise_level: str = "beginner", 
, Any]:
        """Ask AI for clarition"""
ayload = {
          n,
        context,
            "user_expertise_level": expertis,
            "follow_up_ue,
            "request_examples": True
        }
        
        if conversation_id:
    ion_id
        
        retn=payload)
    
    str, 
                           prior
                           messag:
        """Submit document for exp"
        payload = {
    d,
            "user_email": user_
            "priority": priority,
            "consent_to_review": True
       }
        
        if message:
            payload["user_messagessage
        
        return self._make_request('
    
    def get_expert_review_status(se]:
        """Get expert review status
        return self._make_request('}')
    
    def extract_text_from_image(sel str, 
                               prep:
        """Extract text from image """
        image_path = Path(image_path)
        
        with open(image_path, 'rb') as f:

            data = {'preprocess': st)}
            
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
          
            return self._make_reque-text', 
                                    files=filesers)
    
    def speech_to_text(self, audio_path: str, 
                      language_code: str = "en-US]:

        audio_path = Path(audio_pat)
        
        with open(audio_path, 'rb') as f:
            files = {'audio_file': (audio_path.name, f, 'au
            data = {

                'enable_punctuation': 'true'
            }
            
            headers = dict(self.session.headers)

                del head]
            
            return self._make_request('POST', '/api/speech/speech-totext', 
                                    files=files, data=data, headers=headers)
    
, 
                      voice_ges:
        """Convert text to speech and return audio bytes"""
        payload = {
            "text": text,
,
            "voice_gender": 
            "optimize_for_legal": True
        }
        
eech"
        response = self.session.post(urlad)

        
        ntent

# Usage Example
api = LegalSaathiAPI(firebase_tokeen")

# Analyze a document
analysis = ent(
    text="T
    document_type="employment_coct",
    expertise_level="beginner"
)

# Ask AI for clarification
clarification = api.ask_ai(
    question="What does this clause m",
    context={"document": anaysis},
    expertise_level="beginn"
)

# Su
if analysis.get("should_route_to_expert"):
    expert_review = api.submit_expeew(
        analysis_id=analysis["analy],
   ",
="HIGH"
    )
```

## Performance Considerations

### Response Times
- **Document Analysis**: 2-5 seconds (depending on document size)
- **Translation**: 0.5-2 seconds (depending on text length)
o length)
- **AI Clarification**: 1-2ching)


### Caching Strategy
- **Analysis r TTL
- **Translation 
- **Speech Audio
- **Embeddings**: 7 daTTL
ased
### Rate Limiting Best Practicesmplement exponential backoff for rilabilityvice unavaions for serfallback opte rovidefully
- P gracit errorsdle rate limures
- Hannsient failtraogic for retry llement 
- Impcodese status eck responss ch- Alway Handling
### Errors

 quotanstaitor usage agoniequests
- Miple rs for multperationatch ose be
- Uhen possiblally wnses loc Cache respos
-limit errorate 
- I
-b: Sessionversations**ser Con- **Uys ours TTL**: 6 hs TTL   hourlts**: 24suRes**: 1 houResultuality)and qage size nding on imds (depeeconI**: 2-4 sVision AP- ** caeconds (with s audionng dis (depen: 1-3 secondessing**eech Proc- **Sp priority       mcoe.xampl@eil="userr_emause     s_id"sit_revirif neededert review mit for expberlean?ntra.",..t agreement employmenhisnalyze_documapi.abase-tok"your-firen= response.coreturnr_status()e_foe.raisons  resp      n=paylo, jsoh/text-to-speec/api/spurl}base_= f"{self. url        gender,voice_de_co: language"de"language_co             -> bytNEUTRAL")r: str = "ende = "en-US"code: strnguage_: str, laself, textpeech(ef text_to_s    d-ent-Type'ers['Cont:adersin hee' nt-Typf 'Conte  i          de,_coe': languagelanguage_cod      '          v')}dio/wahext"""ch to trt speeConve  """      , Anyt[Any") -> Dic=heada, headersdata=dat, /extract'/api/vision'POST', st(  lower(s).ocesr(preprpeg')}ge/j, 'imah.name, fage_pat: (im'file's = {      file      Vision APIusing  Any] Dict[Any,rue) ->= Tol s: borocespath:f, image_review_idstatus/{ueue/-qpi/expertT', f'/aGE"""Any, Anyr) -> Dict[ew_id: st, revilfn=payload)t', jsoqueue/submi/api/expert-, 'POST'= me] " ail,emnalysis_iid": analysis_      "a  w""ert reviet[Any, Any]ic None) -> D[str] = Optionale:IUM",  "MEDtr =ity: sl: ser_emaiid: str, unalysis_lf, at_review(seper submit_exefd', jso/ai/clarify'/apit('POST', e_requeslf._makurn senversat_id"] = coversation"conoad[payl        ontext": Trce_levelontext":     "cuestio: q"question"          pficany) -> Dict[A Nonetr] = Optional[sion_id:ersat conv             drue: Tgal_terms""preserve_le            text"""onl cgah le witAny]:Any, t[-> Dicr) ste: agtarget_langu                        xt: str,  clause_testr,id:  d payloa       t[Any, Any]> Dic) -l = Trueheadeeaders= he/file'/analyzapiOST', '/            e_levexpertis eel':ent_tytype': documt_en'docum                stream')}et-cation/octlie, f, 'appm, Any Dict[Any") ->"beginner: str = stre: t_typocumen: str, de_pathe(self, file_fil  def analyz  n=payloadnalyze', jsoi/aload =     pay   Any]:Dict[Any, r") -> nne = "begin(or_status()se.raise_f   respon         ny]:Any, A -> Dict[            token}'e_ebasase_uptional[strase_token: Oebir        f         athiAPI:ss LegalSacla Pathib importthl pafrom Any, ict,mport jsoiesort requ`py`n?"e meai.askAwait ap= arificatk AI for clast_contract" agreement.zeDocumen-tokenr-firebasen: 'youebaseToke firPI(alSaathiA = new Legpipl  }          hPOST method: '  ext`,tract-ti/vision/exaps.baseURL}/hih(`${t fetconse = awaitesp   const roken}`;dersInia))tring(toSrocess.prepess', d('preproc.appenormDataFow true) = n();sojders()getHeahis.s: t     header}`, {${reviewIdstatus/queue//api/expert-baseURL}tch(`${this.fe await onse =spst re stId:iewrevtatus(ReviewSpertponse.js res    return      ages.messaramessage: p   user_m     | 'MEDIUity |orms.priiority: parapr     s.userEmaiemail: param    user_   lysisams.anars(),Heade this.getheaders:  queue/submitert-xpe 'IUM' || 'MED: 'HIGH' riority?pstrmail: serEamar(p);nversatcoarams.on_id: p'beginner',vel || iseLe.expertvel: paramslese_xperti    user_e   ms.context: para contextioest: params.quiontringiy: JSON.s    bod  rs(Headeis.geters: th head   'POST',    method: clariURL}/api/ai/is.baseh(`${thetcringion: st   questAI(params: { ask    });ext ?? truentegalCocludeLnautoanguage || 'eLurcs.soaram_language: purce  so      tLanguagams.text, text: par       (),dersgetHea: this.ders     hea OS'P

## Advanced Features & Integrations

### Semantic Search & RAG (Vertex AI)

#### POST /api/search/similar-documents
Find similar legal documents using semantic search and vector embeddings.

**Rate Limit:** 10/minute (authenticated users only)
**Authentication Required:** Yes

**Request Body:**
```json
{
  "document_text": "string (required)",
  "document_type": "employment_contract|rental_agreement|nda|loan_agreement",
  "similarity_threshold": 0.8,
  "max_results": 10,
  "include_precedents": true
}
```

**Response:**
```json
{
  "success": true,
  "similar_documents": [
    {
      "document_id": "doc-uuid",
      "similarity_score": 0.94,
      "document_type": "employment_contract",
      "key_clauses": ["confidentiality", "termination", "benefits"],
      "risk_level": "YELLOW",
      "precedent_strength": "high"
    }
  ],
  "semantic_analysis": {
    "key_concepts": ["employment terms", "confidentiality", "compensation"],
    "legal_categories": ["labor law", "contract law"],
    "complexity_score": 0.72
  },
  "total_results": 5,
  "processing_time": 1.8
}
```

### Knowledge Graph Integration (Neo4j)

#### GET /api/knowledge-graph/entity-relationships/{entity_id}
Explore legal entity relationships and connections.

**Rate Limit:** 20/minute (authenticated users only)

**Response:**
```json
{
  "entity_id": "entity-uuid",
  "entity_type": "contract|clause|party|precedent",
  "relationships": [
    {
      "related_entity_id": "related-uuid",
      "relationship_type": "contains|references|similar_to",
      "strength": 0.89,
      "context": "Both contracts contain similar confidentiality clauses"
    }
  ],
  "graph_insights": {
    "centrality_score": 0.75,
    "cluster_membership": "employment_contracts_cluster",
    "influence_score": 0.82
  }
}
```

### Cost Monitoring & Analytics

#### GET /api/admin/cost-monitoring
Get comprehensive cost and usage analytics (Admin only).

**Authentication Required:** Yes (Admin role)

**Response:**
```json
{
  "success": true,
  "cost_summary": {
    "total_cost_today": 45.67,
    "total_cost_month": 1234.56,
    "cost_by_service": {
      "gemini_api": 25.30,
      "document_ai": 12.45,
      "vision_api": 8.92
    }
  },
  "usage_metrics": {
    "total_requests_today": 1250,
    "unique_users_today": 89,
    "average_cost_per_request": 0.037
  },
  "quota_status": {
    "gemini_api": {"used": 1200, "limit": 10000, "percentage": 12},
    "vision_api": {"used": 450, "limit": 1000, "percentage": 45}
  }
}
```

## Google AI Tools Integration

### Comprehensive AI Services Architecture

LegalSaathi integrates 8 Google Cloud AI services plus additional infrastructure in a coordinated architecture:

#### 1. Google Gemini API
- **Purpose**: Advanced legal document analysis and interpretation
- **Implementation**: Multi-service manager with Groq fallback
- **Features**: Context-aware legal reasoning, experience-level adaptation, risk assessment
- **Usage**: Primary AI engine for document understanding and user interaction
- **Rate Limits**: 60 requests/minute per user
- **Fallback**: Groq API for high availability

#### 2. Google Document AI
- **Purpose**: Structured document processing and text extraction
- **Implementation**: Dedicated processor for legal documents
- **Features**: High-accuracy OCR, table recognition, clause identification
- **Usage**: PDF and Word document processing
- **Rate Limits**: 300 requests/hour per project
- **Confidence Scoring**: Quality assessment for extracted content

#### 3. Google Cloud Vision API
- **Purpose**: Image-based document processing and OCR
- **Implementation**: Dual vision service with preprocessing
- **Features**: Text extraction from images, legal document optimization
- **Usage**: Mobile photos, scanned documents, image uploads
- **Rate Limits**: 100 requests/day per user
- **Cost Monitoring**: $1.50 per user per day limit

#### 4. Google Cloud Translation API
- **Purpose**: Multi-language document translation with legal context
- **Implementation**: Legal context-aware translation service
- **Features**: 50+ languages, legal terminology preservation, cultural adaptation
- **Usage**: Document and clause translation
- **Rate Limits**: 1000 characters per request
- **Caching**: 24-hour TTL for translation results

#### 5. Google Cloud Speech-to-Text
- **Purpose**: Voice accessibility for document input
- **Implementation**: Enhanced speech service with legal terminology
- **Features**: Legal term recognition, punctuation, multi-language support
- **Usage**: Voice document input, accessibility features
- **Rate Limits**: 60 minutes/day per user
- **Supported Languages**: 13+ languages with neural models

#### 6. Google Cloud Text-to-Speech
- **Purpose**: Audio accessibility for analysis results
- **Implementation**: Neural voice synthesis with legal optimization
- **Features**: Natural voices, adjustable parameters, legal content optimization
- **Usage**: Audio explanations, accessibility features
- **Rate Limits**: 1 million characters/month per user
- **Voice Options**: Neural, Standard, and WaveNet voices

#### 7. Google Cloud Natural Language AI
- **Purpose**: Advanced text analysis and entity extraction
- **Implementation**: Legal-specific entity recognition and analysis
- **Features**: Legal entity extraction, sentiment analysis, syntax analysis
- **Usage**: Enhanced document insights, confidence scoring
- **Rate Limits**: 5000 requests/day per project
- **Entity Types**: Legal-specific entities (parties, dates, amounts)

#### 8. Google Vertex AI
- **Purpose**: Semantic search, embeddings, and RAG capabilities
- **Implementation**: Vector embeddings for document similarity and enhanced context
- **Features**: Document similarity scoring, semantic search, precedent matching
- **Usage**: Advanced document comparison, enhanced insights via RAG
- **Rate Limits**: 1000 embedding requests/day per user
- **Vector Dimensions**: 768-dimensional embeddings for legal documents

### Additional Infrastructure Services

#### Firebase Gmail OAuth2 Integration
- **Purpose**: Secure email delivery and professional communication
- **Implementation**: OAuth2-authenticated Gmail API with token management
- **Features**: Professional email templates, secure attachments, delivery tracking
- **Usage**: Analysis report delivery, expert review notifications
- **Security**: Encrypted email transmission, user consent-based communication

#### Neo4j Graph Database
- **Purpose**: Legal knowledge graph and relationship mapping
- **Implementation**: Graph-based storage for legal entities and relationships
- **Features**: Entity relationship mapping, precedent connections, pattern analysis
- **Usage**: Enhanced legal insights, relationship discovery, precedent analysis
- **Query Language**: Cypher for complex legal relationship queries

### AI Service Coordination

```mermaid
graph TB
    A[Document Input] --> B[Privacy Masking]
    B --> C{Input Type}
    C -->|Text| D[Gemini Analysis]
    C -->|PDF/DOC| E[Document AI]
    C -->|Image| F[Vision API]
    C -->|Voice| G[Speech-to-Text]
    
    E --> D
    F --> D
    G --> D
    
    D --> H[Natural Language AI]
    H --> I[Vertex AI Embeddings]
    I --> J[Neo4j Knowledge Graph]
    J --> K[Confidence Calculation]
    
    K --> L{Confidence >= 60%?}
    L -->|Yes| M[Return Results]
    L -->|No| N[Expert Review Queue]
    
    M --> O[Translation API]
    O --> P[Text-to-Speech]
    P --> Q[Gmail Email Delivery]
    
    style D fill:#4285f4,color:#fff
    style E fill:#34a853,color:#fff
    style F fill:#ea4335,color:#fff
    style O fill:#fbbc04,color:#000
    style G fill:#ff6d01,color:#fff
    style P fill:#9c27b0,color:#fff
    style H fill:#00bcd4,color:#fff
    style I fill:#ff9800,color:#fff
    style J fill:#68bc00,color:#fff
    style Q fill:#2196f3,color:#fff
```dence text extraction, legal document optimization
- **Fallback**: Basic image processing when API unavailable

#### 3. Google Cloud Translation API
- **Purpose**: Multi-language document translation
- **Usage**: Translate analysis results to 50+ languages
- **Features**: Legal context preservation, cultural adaptation
- **Rate Limit**: 1000 characters per request

#### 4. Google Cloud Speech-to-Text
- **Purpose**: Voice input for document content
- **Usage**: Accessibility feature for document input
- **Features**: Legal terminology recognition, punctuation
- **Supported**: 13+ languages with neural models

#### 5. Google Cloud Text-to-Speech
- **Purpose**: Audio output for analysis results
- **Usage**: Accessibility feature for visually impaired users
- **Features**: Neural voices, adjustable speech parameters
- **Output**: MP3, WAV, OGG formats

#### 6. Google Cloud Natural Language AI
- **Purpose**: Advanced text analysis and entity extraction
- **Usage**: Legal entity recognition, sentiment analysis
- **Features**: Legal-specific entity types, confidence scoring

#### 7. Google Vertex AI
- **Purpose**: Semantic search and document similarity analysis
- **Usage**: Vector embeddings for legal document comparison and RAG
- **Features**: Document similarity scoring, semantic search, precedent matching
- **Rate Limit**: 1000 embedding requests per day

#### 8. Firebase Gmail OAuth2
- **Purpose**: Secure email delivery and user communication
- **Usage**: Professional email delivery for analysis reports and expert notifications
- **Features**: OAuth2-authenticated Gmail API, secure attachments, user consent-based communication

#### 9. Neo4j Graph Database
- **Purpose**: Legal knowledge graph and relationship mapping
- **Usage**: Legal entity relationships, contract dependencies, precedent connections
- **Features**: Graph-based queries, relationship discovery, legal research enhancement

### Enhanced AI Integration Architecture

```mermaid
graph TB
    A[User Input] --> B[Privacy Masking]
    B --> C{Input Type}
    C -->|Text| D[Gemini Analysis]
    C -->|Image| E[Vision API]
    C -->|Audio| F[Speech-to-Text]
    E --> D
    F --> D
    D --> G[Natural Language AI]
    G --> H[Vertex AI Embeddings]
    H --> I[Neo4j Knowledge Graph]
    I --> J[Risk Assessment]
    J --> K{Confidence Check}
    K -->|High| L[Return Results]
    K -->|Low| M[Expert Review Queue]
    L --> N[Translation API]
    N --> O[Text-to-Speech]
    O --> P[Gmail Email Delivery]
    P --> Q[Final Response]
    
    style H fill:#ff9800,color:#fff
    style I fill:#68bc00,color:#fff
    style P fill:#2196f3,color:#fff
```

## Performance Considerations

- **Multi-level Caching**: Analysis (1hr), Translation (24hr), Speech (6hr)
- **Parallel Processing**: Concurrent AI service calls
- **Privacy-First**: PII masking before cloud processing
- **Intelligent Fallbacks**: Multiple AI service redundancy
- **Rate Limiting**: User-based limits with Firebase authentication
- **Async Processing**: Background expert review processing

## Monitoring and Analytics

The API includes built-in monitoring for:
- Response times
- Error rates
- Usage patterns
- Service health
- Resource utilization

Access monitoring data through the `/api/health/metrics` endpoint.