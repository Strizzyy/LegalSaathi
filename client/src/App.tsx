import { useState } from 'react';
import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { DocumentUpload } from './components/DocumentUpload';
import { Results } from './components/Results';
import { Footer } from './components/Footer';
import { LoadingOverlay } from './components/LoadingOverlay';
import { NotificationProvider } from './components/NotificationProvider';
import { ErrorBoundary } from './components/ErrorBoundary';
import { apiService } from './services/apiService';
import { notificationService } from './services/notificationService';

export interface AnalysisResult {
  analysis_id: string;
  overall_risk: {
    level: 'RED' | 'YELLOW' | 'GREEN';
    score: number;
    confidence_percentage: number;
    low_confidence_warning?: boolean;
    risk_categories?: Record<string, number>;
    severity?: string;
    reasons?: string[];
  };
  summary: string;
  analysis_results: Array<{
    clause_id: string;
    clause_text: string; // Actual clause text from backend
    risk_level: {
      level: 'RED' | 'YELLOW' | 'GREEN';
      score: number;
      severity: string;
      confidence_percentage: number;
      low_confidence_warning?: boolean;
      risk_categories?: Record<string, number>;
      reasons?: string[];
    };
    plain_explanation: string;
    legal_implications: string[];
    recommendations: string[];
  }>;
  processing_time: number;
  severity_indicators?: string[];
  enhanced_insights?: {
    document_ai?: any;
    natural_language?: any;
  };
  document_type?: string;
  document_text?: string;
  document_patterns?: string[];
  compliance_flags?: string[];
}

export interface FileInfo {
  filename: string;
  size: number;
}

export interface Classification {
  document_type: { value: string };
  confidence: number;
}

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'results'>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [classification, setClassification] = useState<Classification | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  // React app handles routing internally - no server-side navigation needed

  const handleAnalysisSubmit = async (formData: FormData) => {
    setIsLoading(true);
    
    // Clear previous results to prevent stale data
    setAnalysisResult(null);
    setFileInfo(null);
    setClassification(null);
    setWarnings([]);
    
    try {
      const result = await apiService.analyzeDocument(formData);
      
      if (result.success && result.analysis) {
        console.log('Setting new analysis result:', result.analysis);
        setAnalysisResult(result.analysis);
        setFileInfo(null); // File info no longer used
        setClassification(null); // Classification no longer used
        setWarnings(result.warnings || []);
        
        setCurrentView('results');
        notificationService.success('Document analysis completed successfully');
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      let errorMessage = 'An unexpected error occurred';
      
      if (error instanceof Error) {
        try {
          // Check if error.message is a stringified JSON object
          const parsedError = JSON.parse(error.message);
          errorMessage = parsedError.detail || parsedError.error || error.message;
        } catch {
          // If not JSON, use the error message directly
          errorMessage = error.message;
        }
      } else if (error && typeof error === 'object') {
        try {
          // Try to extract error details from the error object
          const errorObj = error as { detail?: string; message?: string; error?: string };
          errorMessage = errorObj.detail || errorObj.error || errorObj.message || 'An unknown error occurred';
        } catch {
          errorMessage = 'An unknown error occurred';
        }
      }

      // If we still have an object notation in the error message, use a user-friendly message
      if (errorMessage.includes('[object Object]') || errorMessage === '[object Object]') {
        errorMessage = 'File upload failed. Please ensure your file is:\n' +
          '1. A supported type (PDF, DOC, DOCX, or TXT)\n' +
          '2. Under 10MB in size\n' +
          '3. Contains readable text\n' +
          '4. Not corrupted';
      }
      
      notificationService.error(`Analysis failed: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToHome = () => {
    setCurrentView('home');
    setAnalysisResult(null);
    setFileInfo(null);
    setClassification(null);
    setWarnings([]);
    // Clear React state
    
    // Update URL without page reload
    window.history.pushState({}, '', '/');
  };

  return (
    <ErrorBoundary>
      <NotificationProvider>
        <div className="min-h-screen bg-slate-900 relative overflow-hidden">
          <Navigation />
          
          <main>
            {currentView === 'home' ? (
              <>
                <HeroSection />
                <ErrorBoundary fallback={
                  <div className="py-20 text-center">
                    <p className="text-red-400">Document upload component failed to load</p>
                  </div>
                }>
                  <DocumentUpload onSubmit={handleAnalysisSubmit} />
                </ErrorBoundary>
              </>
            ) : (
              <ErrorBoundary fallback={
                <div className="py-20 text-center">
                  <p className="text-red-400">Results component failed to load</p>
                  <button 
                    onClick={handleBackToHome}
                    className="mt-4 px-4 py-2 bg-cyan-500 text-white rounded-lg"
                  >
                    Back to Home
                  </button>
                </div>
              }>
                <Results
                  key={analysisResult?.processing_time || Date.now()}
                  analysis={analysisResult}
                  fileInfo={fileInfo}
                  classification={classification}
                  warnings={warnings}
                  onBackToHome={handleBackToHome}
                />
              </ErrorBoundary>
            )}
          </main>
          
          <Footer />
          
          {isLoading && <LoadingOverlay />}
        </div>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;