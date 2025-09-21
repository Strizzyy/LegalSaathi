import type { AnalysisResult } from '../App';

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
}

export interface HealthResponse {
  status: string;
  services?: Record<string, boolean>;
}

class APIService {
  constructor() {
    // API service uses relative URLs for backend communication
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
      // Check if we have a file or text
      const hasFile = formData.has('document_file');
      const timestamp = Date.now();
      const endpoint = hasFile ? `/api/analyze/file?t=${timestamp}` : `/api/analyze?t=${timestamp}`;

      let requestOptions: RequestInit;

      if (hasFile) {
        // File upload endpoint
        requestOptions = {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          },
          body: formData,
        };
      } else {
        // Text analysis endpoint
        const documentText = formData.get('document_text') as string;
        const expertiseLevel = formData.get('expertise_level') as string || 'beginner';
        const userQuestions = formData.get('user_questions') as string || '';

        requestOptions = {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          },
          body: JSON.stringify({
            document_text: documentText,
            document_type: 'general_contract',
            user_expertise_level: expertiseLevel,
            user_questions: userQuestions,
            _timestamp: Date.now() // Force unique requests
          }),
        };
      }

      const response = await fetch(endpoint, requestOptions);
      console.log('Fetch response status:', response.status, response.statusText);

      if (!response.ok) {
        let errorMessage: string;
        
        try {
          // Try to parse the error response as JSON first
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || JSON.stringify(errorData);
        } catch {
          // If not JSON, get the raw text
          errorMessage = await response.text().catch(() => 'Unknown error');
        }

        // For 422 status, provide a more user-friendly message if we don't have a specific error
        if (response.status === 422 && (!errorMessage || errorMessage === 'Unknown error')) {
          errorMessage = 'Invalid file format or size. Please ensure your document is in PDF, DOC, DOCX, or TXT format and under 10MB.';
        }

        return {
          success: false,
          error: errorMessage
        };
      }

      const backendResponse = await this.handleResponse<any>(response);
      const requestId = Math.random().toString(36).substring(2, 15);
      console.log(`[${requestId}] Backend response received at`, new Date().toISOString(), ':', backendResponse);

      // Transform backend DocumentAnalysisResponse to frontend AnalysisResponse format
      const transformedResponse = this.transformBackendResponse(backendResponse);
      console.log(`[${requestId}] Final transformed response:`, transformedResponse);

      // Debug: Check if clause_text is preserved in transformation
      if (transformedResponse.success && transformedResponse.analysis) {
        console.log(`[${requestId}] Transformed clause texts:`, transformedResponse.analysis.analysis_results.map(r => ({
          id: r.clause_id,
          text: r.clause_text?.substring(0, 100) + '...'
        })));

        // CRITICAL DEBUG: Log the exact clause texts being returned
        console.log(`[${requestId}] FULL CLAUSE TEXTS:`, transformedResponse.analysis.analysis_results.map((r, i) => ({
          index: i,
          id: r.clause_id,
          fullText: r.clause_text
        })));
      }

      return transformedResponse;
    } catch (error) {
      console.error('Document analysis error:', error);
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');

      // Provide graceful degradation with helpful error messages
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          return {
            success: false,
            error: 'Unable to connect to analysis service. Please check your internet connection and try again.'
          };
        }
        if (error.message.includes('timeout')) {
          return {
            success: false,
            error: 'Analysis is taking longer than expected. Please try with a smaller document or try again later.'
          };
        }
        if (error.message.includes('Failed to process analysis response')) {
          return {
            success: false,
            error: 'Failed to process the analysis response. Please try again.'
          };
        }
      }

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

  async askClarification(question: string, context: any): Promise<ClarificationResponse> {
    try {
      // Enhance context with document and clause information
      const enhancedContext = {
        ...context,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        sessionId: this.generateSessionId()
      };

      const response = await fetch('/api/ai/clarify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          question,
          context: enhancedContext
        }),
      });

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
      // Check if this is already in the expected format (wrapped response)
      if (backendResponse.success !== undefined) {
        return backendResponse;
      }

      // CRITICAL DEBUG: Log the raw backend response
      console.log('🔍 RAW BACKEND RESPONSE:', JSON.stringify(backendResponse, null, 2));
      
      // Validate that we have clause_assessments
      if (!backendResponse.clause_assessments || !Array.isArray(backendResponse.clause_assessments)) {
        console.error('❌ MISSING clause_assessments in backend response!');
        throw new Error('Invalid backend response: missing clause_assessments');
      }

      console.log('📋 CLAUSE_ASSESSMENTS COUNT:', backendResponse.clause_assessments.length);
      
      // Transform DocumentAnalysisResponse to AnalysisResponse format
      const analysisResult: AnalysisResult = {
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
            clause_text: clause.clause_text, // Use actual clause text from backend
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

  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch('/health', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      const result = await this.handleResponse<HealthResponse>(response);

      // Ensure we have a proper services object
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
      // Return error status instead of mock data
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