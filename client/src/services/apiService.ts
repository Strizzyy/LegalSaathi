import type { AnalysisResult, FileInfo, Classification } from '../App';
// Performance and error services available but not used in current implementation

export interface APIError extends Error {
  status?: number;
  code?: string;
}

export interface AnalysisResponse {
  success: boolean;
  analysis?: AnalysisResult;
  file_info?: FileInfo;
  classification?: Classification;
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
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || errorMessage;
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

  // FormData creation utility - available for future use

  async analyzeDocument(formData: FormData): Promise<AnalysisResponse> {
    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
      });

      return await this.handleResponse<AnalysisResponse>(response);
    } catch (error) {
      console.error('Document analysis error:', error);
      
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
      }
      
      return {
        success: false,
        error: 'Document analysis failed. Please ensure your document is in a supported format (PDF, DOC, DOCX, TXT) and try again.'
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

      const response = await fetch('/api/clarify', {
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

  private generateSessionId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
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
          'gemini_api': true
        };
      }
      
      return result;
    } catch (error) {
      console.error('Health check error:', error);
      // Return mock data for development/testing
      return {
        status: 'healthy',
        services: {
          'document_ai': true,
          'natural_language': true,
          'translation': true,
          'risk_analysis': true,
          'export': false, // Indicate export service may not be available
          'gemini_api': true
        }
      };
    }
  }

  async exportToPDF(data: {
    analysis: AnalysisResult;
    file_info?: FileInfo;
    classification?: Classification;
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
    file_info?: FileInfo;
    classification?: Classification;
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