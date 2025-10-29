# Frontend-Backend Synchronization

This document explains how Legal Saathi synchronizes frontend and backend startup to prevent API failures during initialization.

## The Problem

Previously, the frontend would load quickly while the backend took time to initialize AI services (RAG, translation, document processing), causing:
- 500 errors when users tried to analyze documents
- Poor user experience with confusing error messages
- Failed API calls during backend startup

## The Solution

### 1. Backend Readiness Service (`backendReadinessService.ts`)

A frontend service that:
- Continuously checks backend initialization status via `/api/health/ready`
- Provides real-time updates on which services are still initializing
- Estimates completion time based on pending services
- Handles connection errors gracefully during startup

### 2. Health Controller Enhancements (`health_controller.py`)

Enhanced health checks that:
- Track individual service initialization status
- Provide detailed readiness information
- Return initialization progress and estimated completion time
- Distinguish between "initializing" and "ready" states

### 3. API Service Integration

The API service now:
- Waits for backend readiness before making requests
- Shows appropriate loading states during initialization
- Provides better error messages when backend is not ready

### 4. UI Components

- **BackendStatusIndicator**: Shows initialization progress in the top-right corner
- **DocumentUpload**: Disables submit button until backend is ready
- **Enhanced notifications**: Clear status updates during startup

## Usage

### Automatic Startup (Recommended)
```bash
python start_synchronized.py
```

This script:
1. Starts the backend
2. Waits for all services to initialize
3. Starts the frontend once backend is ready
4. Provides coordinated logging

### Manual Startup
```bash
# Terminal 1: Start backend
uvicorn main:app --reload --port 8000

# Terminal 2: Wait for backend, then start frontend
cd client
npm run dev
```

## API Endpoints

### `/api/health/ready`
Returns backend initialization status:
```json
{
  "initialization_complete": true,
  "services_ready": {
    "ai_service": true,
    "translation_service": true,
    "document_ai": true,
    "natural_language": true,
    "speech_service": true,
    "rag_service": true
  },
  "ready_for_requests": true,
  "timestamp": "2024-10-29T19:03:33.881Z"
}
```

### `/health`
Standard health check with service status:
```json
{
  "status": "healthy",
  "services": {
    "ai_service": true,
    "google_translate": true,
    "google_document_ai": true,
    "google_natural_language": true,
    "google_speech": true,
    "rag_service": true,
    "file_processing": true,
    "document_analysis": true
  },
  "cache": {
    "initialization_status": "complete",
    "services_ready": {...}
  }
}
```

## Frontend Integration

### Using the Hook
```typescript
import { useBackendReadiness } from '../hooks/useBackendReadiness';

function MyComponent() {
  const { isReady, isChecking, waitForBackend } = useBackendReadiness();
  
  const handleSubmit = async () => {
    if (!isReady) {
      await waitForBackend(30000); // Wait up to 30 seconds
    }
    // Proceed with API call
  };
}
```

### Using the Service Directly
```typescript
import { backendReadinessService } from '../services/backendReadinessService';

// Check if ready
if (backendReadinessService.isBackendReady()) {
  // Make API call
}

// Wait for readiness
const isReady = await backendReadinessService.waitForBackend(60000);
```

## Configuration

### Timeouts
- **Initial delay**: 2 seconds (let backend start)
- **Check interval**: 3 seconds
- **Max retries**: 20 attempts (~2 minutes total)
- **API timeout**: 5 seconds per health check

### Customization
Modify these values in `backendReadinessService.ts`:
```typescript
private readonly CHECK_INTERVAL = 3000; // 3 seconds
private readonly INITIAL_DELAY = 2000; // 2 seconds
maxRetries: 20 // 20 attempts
```

## Benefits

1. **No more startup errors**: Users can't submit requests until backend is ready
2. **Clear feedback**: Real-time status updates during initialization
3. **Better UX**: Loading states and progress indicators
4. **Graceful degradation**: Fallback to default languages if translation service fails
5. **Coordinated startup**: Optional synchronized startup script

## Monitoring

Watch the browser console for readiness updates:
```
🔄 Starting backend readiness check...
🔍 Backend readiness check attempt 1/20
⏳ Backend initializing... Pending: ai_service, rag_service (ETA: 10 seconds)
✅ Backend is ready!
```

The status indicator in the UI shows:
- Blue pulsing dot: Initializing
- No indicator: Ready
- Red dot: Connection failed

This ensures a smooth, synchronized startup experience for all users.