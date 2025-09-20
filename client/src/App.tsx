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
  overall_risk: {
    level: 'RED' | 'YELLOW' | 'GREEN';
    score: number;
    confidence_percentage: number;
    low_confidence_warning?: boolean;
    risk_categories?: Record<string, number>;
  };
  summary: string;
  analysis_results: Array<{
    clause_id: string;
    risk_level: {
      level: 'RED' | 'YELLOW' | 'GREEN';
      score: number;
      severity: string;
      confidence_percentage: number;
      low_confidence_warning?: boolean;
      risk_categories?: Record<string, number>;
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
    
    try {
      const result = await apiService.analyzeDocument(formData);
      
      if (result.success && result.analysis) {
        setAnalysisResult(result.analysis);
        setFileInfo(result.file_info || null);
        setClassification(result.classification || null);
        setWarnings(result.warnings || []);
        
        setCurrentView('results');
        notificationService.success('Document analysis completed successfully');
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Analysis failed';
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