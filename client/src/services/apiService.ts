import type { AnalysisResult } from '../App';
import { experienceLevelService } from './experienceLevelService';

export interface APIError extends Error {
  status?: number;
  code?: string;
}

export interface AnalysisResponse {
  success: boolean;
  analysis?: AnalysisResult;
  warnings?: string[];
  error?: string;
}

export interface TranslationResponse {
  success: boolean;
  translated_text?: string;
  error?: string;
}

export interface ClarificationResponse {
  success: boolean;
  response?: string;
  error?: string;
  service_used?: string;
  fallback?: boolean;
  confidence_score?: number;
}

export interface HealthResponse {
  status: string;
  services?: Record<string, boolean>;
}

class APIService {
  constructor() {
    // API service uses relative URLs for backend communication
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};
    
    // Try to get Firebase auth token if available
    try {
      const { getAuth } = await import('firebase/auth');
      const { getIdToken } = await import('firebase/auth');
      const auth = getAuth();
      
      if (auth.currentUser) {
        const token = await getIdToken(auth.currentUser);
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      // Firebase not available or user not authenticated
      console.debug('No authentication token available');
    }
    
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;

      // Handle specific error cases
      if (response.status === 429) {
        errorMessage = 'API rate limit exceeded. Please wait a moment and try again.';
      } else if (response.status === 503) {
        errorMessage = 'AI service is temporarily unavailable. Please try again later.';
      }

      try {
        const errorData = await response.json();
        if (errorData.error || errorData.message || errorData.detail) {
          errorMessage = errorData.error || errorData.message || errorData.detail;

          // Check for API exhaustion indicators
          const message = errorMessage.toLowerCase();
          if (message.includes('quota') || message.includes('exhausted') || message.includes('rate limit')) {
            errorMessage = 'AI service quota exceeded. The system is using fallback analysis. Results may be less detailed.';
          }
        }
      } catch {
        // If JSON parsing fails, use the default error message
      }

      const error = new Error(errorMessage) as APIError;
      error.status = response.status;
      throw error;
    }

    try {
      return await response.json();
    } catch (error) {
      throw new Error('Invalid JSON response from server');
    }
  }


  async analyzeDocument(formData: FormData): Promise<AnalysisResponse> {
  try {
    // Clear any potential browser storage interference
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('analysis_cache');
        sessionStorage.removeItem('analysis_cache');
      } catch (e) {
        // Ignore storage errors
      }
    }
    
    const isFileUpload = formData.get('is_file_upload') === 'true';
    const timestamp = Date.now();
    const authHeaders = await this.getAuthHeaders();

    let requestOptions: RequestInit;
    let endpoint: string;

    if (isFileUpload) {
      // File upload endpoint
      endpoint = `/api/analyze/file?t=${timestamp}`;
      
      // Remove the marker field before sending
      formData.delete('is_file_upload');
      
      requestOptions = {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          ...authHeaders
        },
        body: formData, // Send FormData as-is for file uploads
      };
    } else {
      // Text analysis endpoint
      endpoint = `/api/analyze?t=${timestamp}`;
      
      const documentText = formData.get('document_text') as string;
      const documentType = formData.get('document_type') as string || 'general_contract';
      const userExpertiseLevel = formData.get('user_expertise_level') as string || 'beginner';
      const userQuestions = formData.get('user_questions') as string || '';

      // Create JSON payload for text analysis
      const jsonPayload = {
        document_text: documentText,
        document_type: documentType,
        user_expertise_level: userExpertiseLevel,
        ...(userQuestions && { user_questions: userQuestions }),
        _timestamp: timestamp // Force unique requests
      };

      requestOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          ...authHeaders
        },
        body: JSON.stringify(jsonPayload),
      };
    }

    console.log('Making request to:', endpoint);
    console.log('Request method:', isFileUpload ? 'FormData (file)' : 'JSON (text)');

    const response = await fetch(endpoint, requestOptions);
    console.log('Fetch response status:', response.status, response.statusText);

    if (!response.ok) {
      let errorMessage = 'An unknown error occurred.';
      try {
          const errorData = await response.json();
          console.error("Backend Error Details:", errorData);

          // FastAPI validation errors are in `detail` as an array of objects
          if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((err: any) => `${err.loc.join('->')}: ${err.msg}`).join('; ');
          } else {
              errorMessage = errorData.detail || errorData.message || 'Failed to analyze document.';
          }
      } catch {
          errorMessage = `Request failed with status: ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    const backendResponse = await this.handleResponse<any>(response);
    const requestId = Math.random().toString(36).substring(2, 15);
    console.log(`[${requestId}] Backend response received at`, new Date().toISOString(), ':', backendResponse);

    const transformedResponse = this.transformBackendResponse(backendResponse);
    console.log(`[${requestId}] Final transformed response:`, transformedResponse);

    if (transformedResponse.success && transformedResponse.analysis) {
      console.log(`[${requestId}] Transformed clause texts:`, transformedResponse.analysis.analysis_results.map(r => ({
        id: r.clause_id,
        text: r.clause_text?.substring(0, 100) + '...'
      })));
    }

    return transformedResponse;
  } catch (error) {
    console.error('Document analysis error:', error);
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Document analysis failed. Please ensure your document is in a supported format (PDF, DOC, DOCX, TXT) and try again.'
    };
  }
}

  async translateText(text: string, targetLanguage: string, sourceLanguage: string = 'en'): Promise<TranslationResponse> {
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          text,
          target_language: targetLanguage,
          source_language: sourceLanguage
        }),
      });

      return await this.handleResponse<TranslationResponse>(response);
    } catch (error) {
      console.error('Translation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Translation failed'
      };
    }
  }

  async translateDocumentSummary(
    summaryContent: any,
    targetLanguage: string,
    sourceLanguage: string = 'en',
    userId?: string
  ): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch('/api/translate/document-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...headers
        },
        body: JSON.stringify({
          summary_content: summaryContent,
          target_language: targetLanguage,
          source_language: sourceLanguage,
          preserve_formatting: true,
          user_id: userId || 'anonymous'
        }),
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Document summary translation error:', error);
      throw error;
    }
  }

  async translateSummarySection(
    sectionContent: string,
    sectionType: string,
    targetLanguage: string,
    sourceLanguage: string = 'en',
    userId?: string
  ): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch('/api/translate/summary-section', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...headers
        },
        body: JSON.stringify({
          section_content: sectionContent,
          section_type: sectionType,
          target_language: targetLanguage,
          source_language: sourceLanguage,
          user_id: userId || 'anonymous'
        }),
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Summary section translation error:', error);
      throw error;
    }
  }

  async getEnhancedSupportedLanguages(): Promise<any> {
    try {
      const response = await fetch('/api/translate/languages/enhanced', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Failed to get enhanced supported languages:', error);
      throw error;
    }
  }

  async getTranslationUsageStats(userId?: string): Promise<any> {
    try {
      const url = userId ? `/api/translate/usage-stats?user_id=${userId}` : '/api/translate/usage-stats';
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Failed to get translation usage stats:', error);
      throw error;
    }
  }

  async askClarification(question: string, context: any, experienceLevel?: string): Promise<ClarificationResponse> {
    try {
      // Validate question length
      if (!question || question.trim().length < 5) {
        console.warn('Question too short for AI clarification:', question);
        return {
          success: false,
          error: 'Question must be at least 5 characters long'
        };
      }

      // Validate and sanitize experience level
      const userExperienceLevel = experienceLevel || experienceLevelService.getLevelForAPI();
      const validLevels = ['beginner', 'intermediate', 'expert'];
      const sanitizedLevel = validLevels.includes(userExperienceLevel) ? userExperienceLevel : 'beginner';

      const enhancedContext = {
        ...context,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        sessionId: this.generateSessionId()
      };

      const requestBody = {
        question: question.trim(),
        context: enhancedContext,
        user_expertise_level: sanitizedLevel
      };

      console.log('AI Clarification Request:', {
        questionLength: question.length,
        experienceLevel: sanitizedLevel,
        hasContext: !!context
      });

      const response = await fetch('/api/ai/clarify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.status === 422) {
        const errorData = await response.json();
        console.error('Validation error in AI clarification:', errorData);
        return {
          success: false,
          error: 'Invalid request data. Please check your input and try again.'
        };
      }

      if (response.status === 400) {
        const errorData = await response.text();
        console.error('Bad request error in AI clarification:', errorData);
        return {
          success: false,
          error: 'Bad request. The AI service may be temporarily unavailable.'
        };
      }

      return await this.handleResponse<ClarificationResponse>(response);
    } catch (error) {
      console.error('Clarification error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'AI clarification service is temporarily unavailable. Please try again later or contact support.'
      };
    }
  }

  async speechToText(audioBlob: Blob, languageCode: string = 'en-US'): Promise<{ success: boolean; transcript?: string; error?: string }> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('language_code', languageCode);
      formData.append('enable_punctuation', 'true');

      const response = await fetch('/api/speech/speech-to-text', {
        method: 'POST',
        body: formData,
      });

      const result = await this.handleResponse<any>(response);

      return {
        success: result.success,
        transcript: result.transcript,
        error: result.error_message
      };
    } catch (error) {
      console.error('Speech-to-text error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Speech recognition failed'
      };
    }
  }

  async textToSpeech(text: string, options?: {
    languageCode?: string;
    voiceGender?: string;
    speakingRate?: number;
  }): Promise<Blob | null> {
    try {
      const response = await fetch('/api/speech/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          language_code: options?.languageCode || 'en-US',
          voice_gender: options?.voiceGender || 'NEUTRAL',
          speaking_rate: options?.speakingRate || 0.9,
          pitch: 0.0,
          audio_encoding: 'MP3'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Text-to-speech error:', error);
      return null;
    }
  }

  async getSupportedLanguages(): Promise<{ success: boolean; languages?: any[]; error?: string }> {
    try {
      const response = await fetch('/api/speech/languages', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      const result = await this.handleResponse<any>(response);

      return {
        success: result.success,
        languages: result.speech_to_text_languages,
        error: result.error_message
      };
    } catch (error) {
      console.error('Get supported languages error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get supported languages'
      };
    }
  }

  async post(url: string, data: any): Promise<{ data: any }> {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const result = await this.handleResponse<any>(response);
      return { data: result };
    } catch (error) {
      console.error('POST request error:', error);
      throw error;
    }
  }

  async get(url: string): Promise<{ data: any }> {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      const result = await this.handleResponse<any>(response);
      return { data: result };
    } catch (error) {
      console.error('GET request error:', error);
      throw error;
    }
  }

  private generateSessionId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }

  private transformBackendResponse(backendResponse: any): AnalysisResponse {
    try {
      if (backendResponse.success !== undefined) {
        return backendResponse;
      }

      console.log('🔍 RAW BACKEND RESPONSE:', JSON.stringify(backendResponse, null, 2));
      
      if (!backendResponse.clause_assessments || !Array.isArray(backendResponse.clause_assessments)) {
        console.error('❌ MISSING clause_assessments in backend response!');
        throw new Error('Invalid backend response: missing clause_assessments');
      }

      console.log('📋 CLAUSE_ASSESSMENTS COUNT:', backendResponse.clause_assessments.length);
      
      const analysisResult: AnalysisResult = {
        analysis_id: backendResponse.analysis_id || 'unknown',
        overall_risk: {
          level: backendResponse.overall_risk.level,
          score: backendResponse.overall_risk.score,
          confidence_percentage: backendResponse.overall_risk.confidence_percentage,
          low_confidence_warning: backendResponse.overall_risk.low_confidence_warning,
          risk_categories: backendResponse.overall_risk.risk_categories
        },
        summary: backendResponse.summary,
        analysis_results: backendResponse.clause_assessments.map((clause: any, index: number) => {
          console.log(`🔍 TRANSFORMING CLAUSE ${index + 1}:`, {
            id: clause.clause_id,
            hasText: !!clause.clause_text,
            textPreview: clause.clause_text?.substring(0, 100) + '...'
          });
          
          return {
            clause_id: clause.clause_id,
            clause_text: clause.clause_text,
            risk_level: {
              level: clause.risk_assessment.level,
              score: clause.risk_assessment.score,
              severity: clause.risk_assessment.severity,
              confidence_percentage: clause.risk_assessment.confidence_percentage,
              low_confidence_warning: clause.risk_assessment.low_confidence_warning,
              risk_categories: clause.risk_assessment.risk_categories
            },
            plain_explanation: clause.plain_explanation,
            legal_implications: clause.legal_implications,
            recommendations: clause.recommendations
          };
        }),
        processing_time: backendResponse.processing_time,
        enhanced_insights: backendResponse.enhanced_insights
      };

      console.log('✅ TRANSFORMED ANALYSIS RESULT:', {
        clauseCount: analysisResult.analysis_results.length,
        firstClauseText: analysisResult.analysis_results[0]?.clause_text?.substring(0, 100) + '...'
      });

      return {
        success: true,
        analysis: analysisResult,
        warnings: []
      };
    } catch (error) {
      console.error('❌ Error transforming backend response:', error, backendResponse);
      return {
        success: false,
        error: 'Failed to process analysis response'
      };
    }
  }

  // Authentication methods
  async verifyToken(token: string): Promise<{ success: boolean; user?: any; error?: string }> {
    try {
      const response = await fetch('/api/auth/verify-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      return await this.handleResponse<any>(response);
    } catch (error) {
      console.error('Token verification error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Token verification failed'
      };
    }
  }

  async registerUser(email: string, password: string, displayName?: string): Promise<{ success: boolean; user?: any; error?: string }> {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ email, password, display_name: displayName }),
      });

      return await this.handleResponse<any>(response);
    } catch (error) {
      console.error('User registration error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'User registration failed'
      };
    }
  }

  async getCurrentUser(): Promise<{ success: boolean; user?: any; error?: string }> {
    try {
      const authHeaders = await this.getAuthHeaders();
      const response = await fetch('/api/auth/current-user', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          ...authHeaders
        },
      });

      return await this.handleResponse<any>(response);
    } catch (error) {
      console.error('Get current user error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get user information'
      };
    }
  }

  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch('/health', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      const result = await this.handleResponse<HealthResponse>(response);

      if (!result.services) {
        result.services = {
          'document_ai': true,
          'natural_language': true,
          'translation': true,
          'risk_analysis': true,
          'export': true,
          'groq_api': true
        };
      }

      return result;
    } catch (error) {
      console.error('Health check error:', error);
      return {
        status: 'unhealthy',
        services: {}
      };
    }
  }

  async exportToPDF(data: {
    analysis: AnalysisResult;
  }): Promise<Blob | null> {
    try {
      const response = await fetch('/api/export/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/pdf',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`PDF export failed: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('PDF export error:', error);
      return null;
    }
  }

  async exportToWord(data: {
    analysis: AnalysisResult;
  }): Promise<Blob | null> {
    try {
      const response = await fetch('/api/export/word', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Word export failed: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Word export error:', error);
      return null;
    }
  }
}

export const apiService = new APIService();
export default apiService;