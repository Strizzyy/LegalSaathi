import { useState, useEffect } from 'react';
import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { DocumentUpload } from './components/DocumentUpload';
import { Results } from './components/Results';
import { Footer } from './components/Footer';
import { LoadingOverlay } from './components/LoadingOverlay';
import { NotificationProvider } from './components/NotificationProvider';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import { AuthModal } from './components/auth/AuthModal';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { UserProfile } from './components/auth/UserProfile';
import { PrivacyPolicy } from './components/PrivacyPolicy';
import { TermsOfService } from './components/TermsOfService';
import { AboutUs } from './components/AboutUs';
import { ContactUs } from './components/ContactUs';
import { ProductSection } from './components/ProductSection';
import { MultipleImageAnalysis } from './components/MultipleImageAnalysis';
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
  const [currentView, setCurrentView] = useState<'home' | 'results' | 'profile' | 'privacy' | 'terms' | 'about' | 'contact' | 'document-summary' | 'risk-assessment' | 'clause-analysis' | 'multiple-images'>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [classification, setClassification] = useState<Classification | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  // Handle scroll behavior when view changes
  useEffect(() => {
    if (currentView === 'privacy' || currentView === 'terms' || currentView === 'about' || currentView === 'contact' || 
        currentView === 'document-summary' || currentView === 'risk-assessment' || currentView === 'clause-analysis' || 
        currentView === 'multiple-images') {
      // Ensure we're at the top when viewing full-page components
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [currentView]);

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
    
    // Scroll to top of the page smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleShowAuth = (mode: 'login' | 'register' = 'login') => {
    setAuthModalMode(mode);
    setShowAuthModal(true);
  };

  const handleShowProfile = () => {
    setCurrentView('profile');
  };

  const handleShowPrivacy = () => {
    setCurrentView('privacy');
    // Smooth scroll to top when navigating to legal documents
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleShowTerms = () => {
    setCurrentView('terms');
    // Smooth scroll to top when navigating to legal documents
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleShowAbout = () => {
    setCurrentView('about');
    // Smooth scroll to top when navigating to about page
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleShowContact = () => {
    setCurrentView('contact');
    // Smooth scroll to top when navigating to contact page
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToDocumentSummary = () => {
    setCurrentView('document-summary');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToRiskAssessment = () => {
    setCurrentView('risk-assessment');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToClauseAnalysis = () => {
    setCurrentView('clause-analysis');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToMultipleImages = () => {
    setCurrentView('multiple-images');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <ErrorBoundary>
      <AuthProvider>
        <NotificationProvider>
          <div className="min-h-screen bg-slate-900 relative overflow-hidden">
            <Navigation 
              onShowAuth={handleShowAuth}
              onShowProfile={handleShowProfile}
              onShowAbout={handleShowAbout}
              onShowContact={handleShowContact}
            />
            
            <main>
              {currentView === 'home' ? (
                <>
                  <HeroSection />
                  <ProductSection 
                    onNavigateToDocumentSummary={handleNavigateToDocumentSummary}
                    onNavigateToRiskAssessment={handleNavigateToRiskAssessment}
                    onNavigateToClauseAnalysis={handleNavigateToClauseAnalysis}
                    onNavigateToMultipleImages={handleNavigateToMultipleImages}
                  />
                  <ErrorBoundary fallback={
                    <div className="py-20 text-center">
                      <p className="text-red-400">Document upload component failed to load</p>
                    </div>
                  }>
                    <ProtectedRoute
                      requireAuth={false}
                      onAuthRequired={() => handleShowAuth('login')}
                    >
                      <DocumentUpload onSubmit={handleAnalysisSubmit} />
                    </ProtectedRoute>
                  </ErrorBoundary>
                </>
              ) : currentView === 'profile' ? (
                <div className="min-h-screen bg-slate-900 flex items-center justify-center pt-24 pb-8 px-4">
                  <ProtectedRoute
                    requireAuth={true}
                    onAuthRequired={() => handleShowAuth('login')}
                  >
                    <UserProfile onBack={handleBackToHome} />
                  </ProtectedRoute>
                </div>
              ) : currentView === 'privacy' ? (
                <PrivacyPolicy onClose={handleBackToHome} />
              ) : currentView === 'terms' ? (
                <TermsOfService onClose={handleBackToHome} />
              ) : currentView === 'about' ? (
                <AboutUs onClose={handleBackToHome} />
              ) : currentView === 'contact' ? (
                <ContactUs onClose={handleBackToHome} />
              ) : currentView === 'document-summary' ? (
                <div className="py-20">
                  <div className="container mx-auto px-6">
                    <div className="max-w-4xl mx-auto text-center">
                      <h1 className="text-4xl font-bold text-white mb-6">Document Summary</h1>
                      <p className="text-xl text-slate-300 mb-8">
                        Upload a document to get a comprehensive AI-powered summary with key insights and recommendations.
                      </p>
                      <ErrorBoundary fallback={
                        <div className="py-20 text-center">
                          <p className="text-red-400">Document upload component failed to load</p>
                        </div>
                      }>
                        <ProtectedRoute
                          requireAuth={false}
                          onAuthRequired={() => handleShowAuth('login')}
                        >
                          <DocumentUpload onSubmit={handleAnalysisSubmit} />
                        </ProtectedRoute>
                      </ErrorBoundary>
                      <button
                        onClick={handleBackToHome}
                        className="mt-8 inline-flex items-center px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        Back to Home
                      </button>
                    </div>
                  </div>
                </div>
              ) : currentView === 'risk-assessment' ? (
                <div className="py-20">
                  <div className="container mx-auto px-6">
                    <div className="max-w-4xl mx-auto text-center">
                      <h1 className="text-4xl font-bold text-white mb-6">Risk Assessment</h1>
                      <p className="text-xl text-slate-300 mb-8">
                        Analyze potential risks in your documents with our traffic light system and confidence scoring.
                      </p>
                      <ErrorBoundary fallback={
                        <div className="py-20 text-center">
                          <p className="text-red-400">Document upload component failed to load</p>
                        </div>
                      }>
                        <ProtectedRoute
                          requireAuth={false}
                          onAuthRequired={() => handleShowAuth('login')}
                        >
                          <DocumentUpload onSubmit={handleAnalysisSubmit} />
                        </ProtectedRoute>
                      </ErrorBoundary>
                      <button
                        onClick={handleBackToHome}
                        className="mt-8 inline-flex items-center px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        Back to Home
                      </button>
                    </div>
                  </div>
                </div>
              ) : currentView === 'clause-analysis' ? (
                <div className="py-20">
                  <div className="container mx-auto px-6">
                    <div className="max-w-4xl mx-auto text-center">
                      <h1 className="text-4xl font-bold text-white mb-6">Clause Analysis</h1>
                      <p className="text-xl text-slate-300 mb-8">
                        Deep dive into individual clauses with detailed explanations and legal implications.
                      </p>
                      <ErrorBoundary fallback={
                        <div className="py-20 text-center">
                          <p className="text-red-400">Document upload component failed to load</p>
                        </div>
                      }>
                        <ProtectedRoute
                          requireAuth={false}
                          onAuthRequired={() => handleShowAuth('login')}
                        >
                          <DocumentUpload onSubmit={handleAnalysisSubmit} />
                        </ProtectedRoute>
                      </ErrorBoundary>
                      <button
                        onClick={handleBackToHome}
                        className="mt-8 inline-flex items-center px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        Back to Home
                      </button>
                    </div>
                  </div>
                </div>
              ) : currentView === 'multiple-images' ? (
                <div className="py-20">
                  <div className="container mx-auto px-6">
                    <div className="max-w-6xl mx-auto">
                      <ErrorBoundary fallback={
                        <div className="py-20 text-center">
                          <p className="text-red-400">Multiple image analysis component failed to load</p>
                        </div>
                      }>
                        <ProtectedRoute
                          requireAuth={false}
                          onAuthRequired={() => handleShowAuth('login')}
                        >
                          <MultipleImageAnalysis 
                            onAnalysisComplete={(result) => {
                              setAnalysisResult(result);
                              setCurrentView('results');
                            }}
                          />
                        </ProtectedRoute>
                      </ErrorBoundary>
                      <div className="text-center mt-8">
                        <button
                          onClick={handleBackToHome}
                          className="inline-flex items-center px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                        >
                          Back to Home
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
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
            
            <Footer 
              onShowPrivacy={handleShowPrivacy}
              onShowTerms={handleShowTerms}
            />
            
            {isLoading && <LoadingOverlay />}
            
            <AuthModal
              isOpen={showAuthModal}
              onClose={() => setShowAuthModal(false)}
              initialMode={authModalMode}
            />
          </div>
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;