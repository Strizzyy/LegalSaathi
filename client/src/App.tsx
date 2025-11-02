import { useState, useEffect, lazy } from 'react';
import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { DocumentUpload } from './components/DocumentUpload';
import { Footer } from './components/Footer';
import { LoadingOverlay } from './components/LoadingOverlay';
import { NotificationProvider } from './components/NotificationProvider';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import { AuthModal } from './components/auth/AuthModal';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { UserProfile } from './components/auth/UserProfile';
import { ProductSection } from './components/ProductSection';
import { apiService } from './services/apiService';
import { notificationService } from './services/notificationService';
import BackendStatusIndicator from './components/BackendStatusIndicator';
import LazyRoute from './components/LazyRoute';
import { initializeProgressivePreloading } from './utils/preloader';
import { performanceMonitor } from './utils/performanceMonitor';
import { lazyComponentManager } from './utils/lazyComponentManager';
import { ProgressiveEnhancement, ConnectionStatus } from './components/ProgressiveEnhancement';

// Lazy-loaded components for code splitting
const Results = lazy(() => import('./components/Results'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const HITLDashboard = lazy(() => import('./pages/HITLDashboard'));
const ExpertLogin = lazy(() => import('./pages/ExpertLogin'));
const ExpertDashboard = lazy(() => import('./pages/ExpertDashboard'));
const DocumentReviewInterface = lazy(() => import('./components/DocumentReviewInterface'));
const MultipleImageAnalysis = lazy(() => import('./components/MultipleImageAnalysis'));
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy'));
const TermsOfService = lazy(() => import('./components/TermsOfService'));
const AboutUs = lazy(() => import('./components/AboutUs'));
const ContactUs = lazy(() => import('./components/ContactUs'));

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
  // Human-in-the-loop confidence fields
  overall_confidence?: number;
  should_route_to_expert?: boolean;
  confidence_breakdown?: {
    overall_confidence: number;
    clause_confidences: Record<string, number>;
    section_confidences: Record<string, number>;
    component_weights: Record<string, number>;
    factors_affecting_confidence: string[];
    improvement_suggestions: string[];
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
  const [currentView, setCurrentView] = useState<'home' | 'results' | 'profile' | 'privacy' | 'terms' | 'about' | 'contact' | 'document-summary' | 'risk-assessment' | 'clause-analysis' | 'multiple-images' | 'admin' | 'hitl' | 'expert-portal' | 'expert-dashboard' | 'expert-review'>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [classification, setClassification] = useState<Classification | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  // Initialize enhanced preloading strategy and performance monitoring
  useEffect(() => {
    const preloaders = initializeProgressivePreloading();

    // Initialize lazy component manager
    lazyComponentManager.initializeProgressivePreloading();

    // Smart preloading based on user context
    const userContext = {
      isAdmin: localStorage.getItem('user_role') === 'admin',
      hasUploadedFiles: localStorage.getItem('has_uploaded_files') === 'true',
      viewedAnalytics: localStorage.getItem('viewed_analytics') === 'true',
      usedAdvancedFeatures: localStorage.getItem('used_advanced_features') === 'true'
    };

    lazyComponentManager.smartPreload(userContext);

    // Store utilities globally for debugging
    (window as any).__preloaders = preloaders;
    (window as any).__performanceMonitor = performanceMonitor;
    (window as any).__lazyComponentManager = lazyComponentManager;

    // Log performance summary after initial load
    setTimeout(() => {
      const summary = performanceMonitor.getPerformanceSummary();
      const preloadStats = lazyComponentManager.getPreloadStats();
      console.log('Performance Summary:', summary);
      console.log('Preload Statistics:', preloadStats);
    }, 5000);

    // Cleanup on unmount
    return () => {
      performanceMonitor.cleanup();
      lazyComponentManager.cleanup();
      preloaders.cleanup();
    };
  }, []);

  // Handle URL routing
  useEffect(() => {
    const path = window.location.pathname;
    if (path === '/admin') {
      setCurrentView('admin');
    } else if (path === '/hitl') {
      setCurrentView('hitl');
    } else if (path === '/expert-portal') {
      setCurrentView('expert-portal');
    } else if (path === '/expert-dashboard') {
      setCurrentView('expert-dashboard');
    } else if (path.startsWith('/expert-review/')) {
      setCurrentView('expert-review');
    } else {
      setCurrentView('home');
    }

    // Listen for URL changes
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path === '/admin') {
        setCurrentView('admin');
      } else if (path === '/hitl') {
        setCurrentView('hitl');
      } else if (path === '/expert-portal') {
        setCurrentView('expert-portal');
      } else if (path === '/expert-dashboard') {
        setCurrentView('expert-dashboard');
      } else if (path.startsWith('/expert-review/')) {
        setCurrentView('expert-review');
      } else {
        setCurrentView('home');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Handle scroll behavior when view changes
  useEffect(() => {
    if (currentView === 'privacy' || currentView === 'terms' || currentView === 'about' || currentView === 'contact' ||
      currentView === 'document-summary' || currentView === 'risk-assessment' || currentView === 'clause-analysis' ||
      currentView === 'multiple-images' || currentView === 'admin' || currentView === 'hitl' ||
      currentView === 'expert-portal' || currentView === 'expert-dashboard' || currentView === 'expert-review') {
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

        // Check if expert review is needed based on confidence
        if (result.analysis.should_route_to_expert && result.analysis.overall_confidence !== undefined) {
          console.log(`Low confidence detected: ${result.analysis.overall_confidence}, showing expert review popup`);
          // Set analysis result but don't navigate to results yet
          setAnalysisResult(result.analysis);
          setFileInfo(null);
          setClassification(null);
          setWarnings(result.warnings || []);

          // The confidence popup will be shown in the Results component
          setCurrentView('results');
        } else {
          // Normal flow for high confidence results
          setAnalysisResult(result.analysis);
          setFileInfo(null);
          setClassification(null);
          setWarnings(result.warnings || []);
          setCurrentView('results');
          notificationService.success('Document analysis completed successfully');
        }
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
          <ProgressiveEnhancement>
            <div className="min-h-screen bg-slate-900 relative overflow-hidden">
              {/* Connection Status */}
              <ConnectionStatus />

              <Navigation
                onShowAuth={handleShowAuth}
                onShowProfile={handleShowProfile}
                onShowAbout={handleShowAbout}
                onShowContact={handleShowContact}
              />

              {/* Backend Status Indicator */}
              <div className="fixed top-16 right-4 z-50">
                <BackendStatusIndicator showDetails={true} />
              </div>

              <main>
                {currentView === 'home' ? (
                  <>
                    <HeroSection />
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
                    <ProductSection
                      onNavigateToDocumentSummary={handleNavigateToDocumentSummary}
                      onNavigateToRiskAssessment={handleNavigateToRiskAssessment}
                      onNavigateToClauseAnalysis={handleNavigateToClauseAnalysis}
                      onNavigateToMultipleImages={handleNavigateToMultipleImages}
                    />
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
                  <LazyRoute
                    componentName="PrivacyPolicy"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Privacy Policy...</p>
                      </div>
                    </div>}
                  >
                    <PrivacyPolicy onClose={handleBackToHome} />
                  </LazyRoute>
                ) : currentView === 'terms' ? (
                  <LazyRoute
                    componentName="TermsOfService"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Terms of Service...</p>
                      </div>
                    </div>}
                  >
                    <TermsOfService onClose={handleBackToHome} />
                  </LazyRoute>
                ) : currentView === 'about' ? (
                  <LazyRoute
                    componentName="AboutUs"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading About Us...</p>
                      </div>
                    </div>}
                  >
                    <AboutUs onClose={handleBackToHome} />
                  </LazyRoute>
                ) : currentView === 'contact' ? (
                  <LazyRoute
                    componentName="ContactUs"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Contact Us...</p>
                      </div>
                    </div>}
                  >
                    <ContactUs onClose={handleBackToHome} />
                  </LazyRoute>
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
                            <LazyRoute
                              componentName="MultipleImageAnalysis"
                              showProgress={true}
                              fallback={<div className="py-20 text-center">
                                <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                                <p className="text-slate-300">Loading Multiple Image Analysis...</p>
                              </div>}
                            >
                              <MultipleImageAnalysis
                                onAnalysisComplete={(result) => {
                                  setAnalysisResult(result);
                                  setCurrentView('results');
                                }}
                              />
                            </LazyRoute>
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
                ) : currentView === 'admin' ? (
                  <LazyRoute
                    componentName="AdminPage"
                    showProgress={true}
                    timeout={15000}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Admin Dashboard...</p>
                        <p className="text-slate-500 text-sm mt-2">This may take a moment</p>
                      </div>
                    </div>}
                  >
                    <AdminPage />
                  </LazyRoute>
                ) : currentView === 'hitl' ? (
                  <LazyRoute
                    componentName="HITLDashboard"
                    showProgress={true}
                    timeout={15000}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Expert Dashboard...</p>
                        <p className="text-slate-500 text-sm mt-2">This may take a moment</p>
                      </div>
                    </div>}
                  >
                    <HITLDashboard />
                  </LazyRoute>
                ) : currentView === 'expert-portal' ? (
                  <LazyRoute
                    componentName="ExpertLogin"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Expert Portal...</p>
                      </div>
                    </div>}
                  >
                    <ExpertLogin />
                  </LazyRoute>
                ) : currentView === 'expert-dashboard' ? (
                  <LazyRoute
                    componentName="ExpertDashboard"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Expert Dashboard...</p>
                      </div>
                    </div>}
                  >
                    <ExpertDashboard />
                  </LazyRoute>
                ) : currentView === 'expert-review' ? (
                  <LazyRoute
                    componentName="DocumentReviewInterface"
                    showProgress={true}
                    fallback={<div className="min-h-screen bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Review Interface...</p>
                      </div>
                    </div>}
                  >
                    <DocumentReviewInterface />
                  </LazyRoute>
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
                    <LazyRoute
                      componentName="Results"
                      showProgress={true}
                      fallback={<div className="py-20 text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p className="text-slate-300">Loading Analysis Results...</p>
                      </div>}
                    >
                      <Results
                        key={analysisResult?.processing_time || Date.now()}
                        analysis={analysisResult}
                        fileInfo={fileInfo}
                        classification={classification}
                        warnings={warnings}
                        onBackToHome={handleBackToHome}
                      />
                    </LazyRoute>
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
          </ProgressiveEnhancement>
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;