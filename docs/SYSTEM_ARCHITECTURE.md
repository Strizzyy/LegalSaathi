# LegalSaathi System Architecture

## Overview

LegalSaathi is an AI-powered legal document analysis platform that simplifies complex legal documents into clear, accessible guidance. The system uses Google Cloud AI services and modern web technologies to provide comprehensive document analysis, translation, and speech capabilities.

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React + TypeScript Client]
        B[Vite Build System]
        C[Tailwind CSS]
    end
    
    subgraph "API Gateway Layer"
        D[FastAPI Application]
        E[Rate Limiting]
        F[CORS Middleware]
        G[Authentication]
    end
    
    subgraph "Business Logic Layer"
        H[Document Controller]
        I[Translation Controller]
        J[Speech Controller]
        K[AI Controller]
        L[Comparison Controller]
    end
    
    subgraph "Service Layer"
        M[Document Service]
        N[AI Service]
        O[Cache Service]
        P[File Service]
        Q[Google Document AI Service]
        R[Google Natural Language Service]
        S[Google Speech Service]
        T[Google Translate Service]
    end
    
    subgraph "Google Cloud AI Services"
        U[Gemini API]
        V[Document AI]
        W[Translation API]
        X[Speech-to-Text]
        Y[Text-to-Speech]
        Z[Natural Language AI]
    end
    
    subgraph "Data Storage"
        W[Local File System]
        X[JSON Pattern Storage]
        Y[Cache Storage]
    end
    
    subgraph "External Services"
        Z[Render.com Hosting]
        AA[CDN]
    end
    
    A --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    G --> J
    G --> K
    G --> L
    
    H --> M
    I --> N
    J --> N
    K --> N
    L --> M
    
    M --> O
    N --> O
    O --> P
    
    N --> Q
    M --> R
    I --> S
    J --> T
    J --> U
    N --> V
    
    M --> W
    N --> X
    O --> Y
    
    D --> Z
    A --> AA
```

## Service Organization

### Google Cloud Services Integration

The application integrates with multiple Google Cloud AI services through dedicated service classes:

#### `services/google_document_ai_service.py`
- **Purpose**: Document processing and OCR capabilities
- **Features**: 
  - Structured data extraction from legal documents
  - Entity recognition and table extraction
  - Legal clause identification
  - Confidence scoring and quality assessment

#### `services/google_natural_language_service.py`
- **Purpose**: Advanced text analysis and understanding
- **Features**:
  - Sentiment analysis for legal tone assessment
  - Named entity extraction for legal entities
  - Syntax analysis for complexity scoring
  - Content classification for document categorization

#### `services/google_speech_service.py`
- **Purpose**: Voice input and output capabilities
- **Features**:
  - Speech-to-text with legal terminology support
  - Text-to-speech with neural voices
  - Multi-language support (13+ languages)
  - Real-time streaming transcription

#### `services/google_translate_service.py`
- **Purpose**: Multi-language translation support
- **Features**:
  - Neural machine translation for 50+ languages
  - Legal context-aware translation
  - Clause-level translation precision
  - Fallback translation mechanisms

### MVC Architecture Pattern

#### Controllers (`controllers/`)
- **Document Controller**: Handles document upload and analysis requests
- **Translation Controller**: Manages translation requests and language support
- **Speech Controller**: Processes voice input/output operations
- **AI Controller**: Manages AI clarification and conversation features
- **Health Controller**: Provides system health monitoring and diagnostics

#### Models (`models/`)
- **Pydantic Models**: Type-safe data validation and serialization
- **Request/Response Schemas**: Structured API contracts
- **Enum Definitions**: Standardized value sets for consistency

#### Services (`services/`)
- **Business Logic**: Core application functionality
- **Google Cloud Integration**: Dedicated services for each AI capability
- **Caching and Performance**: Optimized data access and storage
- **File Processing**: Document parsing and content extraction

## Component Architecture

### Frontend Architecture

```mermaid
graph LR
    subgraph "React Components"
        A[App.tsx]
        B[DocumentUpload]
        C[Results]
        D[TranslationModal]
        E[VoiceInput]
        F[AudioPlayer]
    end
    
    subgraph "Services"
        G[API Service]
        H[Error Service]
        I[Notification Service]
    end
    
    subgraph "State Management"
        J[React Hooks]
        K[Context API]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    
    B --> G
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H
    G --> I
    
    A --> J
    A --> K
```

### Backend Architecture (MVC Pattern)

```mermaid
graph TB
    subgraph "Controllers"
        A[DocumentController]
        B[TranslationController]
        C[SpeechController]
        D[AIController]
        E[ComparisonController]
        F[HealthController]
    end
    
    subgraph "Models"
        G[DocumentModels]
        H[TranslationModels]
        I[SpeechModels]
        J[AIModels]
        K[ComparisonModels]
    end
    
    subgraph "Services"
        L[DocumentService]
        M[AIService]
        N[CacheService]
        O[FileService]
    end
    
    A --> G
    B --> H
    C --> I
    D --> J
    E --> K
    
    A --> L
    B --> M
    C --> M
    D --> M
    E --> L
    
    L --> N
    M --> N
    L --> O
```

## API Architecture

### RESTful API Design

```mermaid
graph LR
    subgraph "API Endpoints"
        A[/api/analyze]
        B[/api/translate]
        C[/api/speech/*]
        D[/api/ai/clarify]
        E[/api/compare]
        F[/health]
    end
    
    subgraph "HTTP Methods"
        G[POST]
        H[GET]
        I[DELETE]
    end
    
    subgraph "Response Formats"
        J[JSON]
        K[Binary Audio]
        L[PDF Export]
    end
    
    A --> G
    B --> G
    C --> G
    C --> H
    D --> G
    E --> G
    F --> H
    
    A --> J
    B --> J
    C --> J
    C --> K
    D --> J
    E --> J
    E --> L
    F --> J
```

## Data Flow Architecture

### Document Analysis Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant D as DocumentService
    participant G as Gemini API
    participant DA as Document AI
    
    U->>F: Upload Document
    F->>A: POST /api/analyze/file
    A->>D: Process Document
    D->>DA: Extract Text
    DA-->>D: Extracted Text
    D->>G: Analyze Content
    G-->>D: Analysis Results
    D-->>A: Structured Response
    A-->>F: JSON Response
    F-->>U: Display Results
```

### Translation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant T as TranslationService
    participant GT as Google Translate
    
    U->>F: Request Translation
    F->>A: POST /api/translate
    A->>T: Process Translation
    T->>GT: Translate Text
    GT-->>T: Translated Text
    T-->>A: Translation Response
    A-->>F: JSON Response
    F-->>U: Display Translation
```

### Speech Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant S as SpeechService
    participant STT as Speech-to-Text
    participant TTS as Text-to-Speech
    
    U->>F: Voice Input
    F->>A: POST /api/speech/speech-to-text
    A->>S: Process Audio
    S->>STT: Convert to Text
    STT-->>S: Transcribed Text
    S-->>A: Text Response
    A-->>F: JSON Response
    F->>A: POST /api/speech/text-to-speech
    A->>S: Generate Audio
    S->>TTS: Convert to Speech
    TTS-->>S: Audio Data
    S-->>A: Audio Response
    A-->>F: Audio File
    F-->>U: Play Audio
```

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Security Layers"
        A[Rate Limiting]
        B[CORS Protection]
        C[Input Validation]
        D[Authentication]
        E[Data Sanitization]
        F[Error Handling]
    end
    
    subgraph "Security Measures"
        G[API Key Management]
        H[File Upload Validation]
        I[Request Size Limits]
        J[Timeout Protection]
    end
    
    A --> G
    B --> H
    C --> I
    D --> J
    E --> G
    F --> H
```

## Deployment Architecture

### Render.com Deployment

```mermaid
graph TB
    subgraph "Build Process"
        A[Source Code]
        B[Node.js Setup]
        C[Frontend Build]
        D[Python Dependencies]
        E[FastAPI App]
    end
    
    subgraph "Runtime Environment"
        F[Uvicorn Server]
        G[Environment Variables]
        H[Health Checks]
        I[Static File Serving]
    end
    
    subgraph "External Dependencies"
        J[Google Cloud APIs]
        K[CDN]
        L[DNS]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    
    F --> J
    I --> K
    F --> L
```

## Performance Optimization

### Caching Strategy

```mermaid
graph LR
    subgraph "Cache Layers"
        A[Browser Cache]
        B[CDN Cache]
        C[Application Cache]
        D[API Response Cache]
    end
    
    subgraph "Cache Types"
        E[Static Assets]
        F[API Responses]
        G[Translation Cache]
        H[Analysis Cache]
    end
    
    A --> E
    B --> E
    C --> F
    C --> G
    D --> H
```

## Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: All services are stateless for easy horizontal scaling
- **Load Balancing**: FastAPI supports multiple workers
- **Caching**: Reduces API calls and improves response times
- **Async Processing**: Non-blocking operations for better throughput

### Vertical Scaling

- **Resource Optimization**: Efficient memory and CPU usage
- **Connection Pooling**: Optimized database and API connections
- **Compression**: GZip compression for reduced bandwidth
- **Monitoring**: Performance metrics and health checks

## Technology Stack

### Frontend
- **React 18**: Modern UI framework with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server for production
- **Pydantic**: Data validation and serialization
- **SlowAPI**: Rate limiting middleware

### AI Services
- **Google Gemini**: Advanced language model
- **Document AI**: Document processing and OCR
- **Translation API**: Multi-language translation
- **Speech Services**: Speech-to-text and text-to-speech
- **Natural Language AI**: Text analysis and understanding

### Infrastructure
- **Render.com**: Cloud hosting platform
- **Node.js**: JavaScript runtime for build process
- **Python 3.12**: Backend runtime environment