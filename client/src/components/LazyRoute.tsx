import React, { Suspense, useState, useEffect } from 'react';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../utils';
import { DashboardWidgetSkeleton, DocumentAnalysisSkeleton, ChartSkeleton } from './SkeletonLoader';

interface LazyRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;

  timeout?: number;
  retryAttempts?: number;
  showProgress?: boolean;
  componentName?: string;
  className?: string;
}

interface LoadingState {
  progress: number;
  message: string;
  stage: 'loading' | 'error' | 'timeout' | 'retry';
}

const DefaultLoadingFallback: React.FC<{
  showProgress?: boolean;
  componentName?: string;
  loadingState?: LoadingState;
  onRetry?: () => void;
}> = ({ showProgress = false, componentName, loadingState, onRetry }) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    return () => clearInterval(interval);
  }, []);

  if (loadingState?.stage === 'error' || loadingState?.stage === 'timeout') {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md mx-auto p-8"
        >
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">
            {loadingState.stage === 'timeout' ? 'Loading Timeout' : 'Loading Error'}
          </h3>
          <p className="text-slate-300 mb-4">
            {loadingState.stage === 'timeout'
              ? `The ${componentName || 'component'} is taking longer than expected to load.`
              : `Failed to load ${componentName || 'component'}. ${loadingState.message}`
            }
          </p>
          <div className="space-y-3">
            <button
              onClick={onRetry}
              className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors inline-flex items-center"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="block mx-auto text-slate-400 hover:text-slate-300 text-sm"
            >
              Reload Page
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center max-w-md mx-auto"
      >
        {/* Loading spinner */}
        <div className="relative mb-6">
          <Loader2 className="w-12 h-12 animate-spin text-cyan-400 mx-auto" />
          {showProgress && loadingState && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-xs font-mono text-cyan-300">
                {Math.round(loadingState.progress)}%
              </div>
            </div>
          )}
        </div>

        {/* Loading message */}
        <div className="space-y-2">
          <p className="text-slate-300 text-lg">
            Loading {componentName || 'component'}{dots}
          </p>
          <p className="text-slate-500 text-sm">
            {loadingState?.message || 'Please wait while we prepare the interface'}
          </p>
        </div>

        {/* Progress bar */}
        {showProgress && loadingState && (
          <div className="mt-6 w-full bg-slate-700 rounded-full h-2">
            <motion.div
              className="bg-cyan-400 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${loadingState.progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        )}

        {/* Skeleton preview for known components */}
        {componentName && (
          <div className="mt-8 opacity-30">
            {componentName.includes('Admin') && <DashboardWidgetSkeleton />}
            {componentName.includes('Results') && <DocumentAnalysisSkeleton />}
            {componentName.includes('Chart') && <ChartSkeleton />}
          </div>
        )}
      </motion.div>
    </div>
  );
};

const ErrorBoundaryFallback: React.FC<{
  error: Error;
  resetError: () => void;
  componentName?: string;
}> = ({ error, resetError, componentName }) => (
  <div className="min-h-screen bg-slate-900 flex items-center justify-center">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center max-w-md mx-auto p-8"
    >
      <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
      <h3 className="text-xl font-semibold text-white mb-2">Component Error</h3>
      <p className="text-slate-300 mb-4">
        The {componentName || 'component'} encountered an error and couldn't be displayed.
      </p>
      <details className="text-left mb-6 p-4 bg-slate-800 rounded-lg">
        <summary className="text-slate-400 cursor-pointer mb-2">Error Details</summary>
        <pre className="text-xs text-red-300 overflow-auto">
          {error.message}
        </pre>
      </details>
      <div className="space-y-3">
        <button
          onClick={resetError}
          className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors inline-flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </button>
        <button
          onClick={() => window.location.reload()}
          className="block mx-auto text-slate-400 hover:text-slate-300 text-sm"
        >
          Reload Page
        </button>
      </div>
    </motion.div>
  </div>
);

class LazyRouteErrorBoundary extends React.Component<
  { children: React.ReactNode; componentName?: string; onError?: (error: Error) => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('LazyRoute Error:', error, errorInfo);
    this.props.onError?.(error);
  }

  override render() {
    if (this.state.hasError && this.state.error) {
      return (
        <ErrorBoundaryFallback
          error={this.state.error}
          resetError={() => this.setState({ hasError: false, error: null })}
          {...(this.props.componentName && { componentName: this.props.componentName })}
        />
      );
    }

    return this.props.children;
  }
}

export const LazyRoute: React.FC<LazyRouteProps> = ({
  children,
  fallback,
  timeout = 10000,
  retryAttempts = 3,
  showProgress = false,
  componentName,
  className
}) => {
  const [loadingState, setLoadingState] = useState<LoadingState>({
    progress: 0,
    message: 'Initializing...',
    stage: 'loading'
  });
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let progressInterval: NodeJS.Timeout;
    let timeoutId: NodeJS.Timeout;

    if (showProgress) {
      // Simulate loading progress
      progressInterval = setInterval(() => {
        setLoadingState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + Math.random() * 15, 90),
          message: prev.progress < 30 ? 'Loading resources...' :
                   prev.progress < 60 ? 'Preparing interface...' :
                   prev.progress < 90 ? 'Almost ready...' : 'Finalizing...'
        }));
      }, 200);
    }

    // Set timeout for loading
    timeoutId = setTimeout(() => {
      setLoadingState(prev => ({
        ...prev,
        stage: 'timeout',
        message: 'Loading is taking longer than expected'
      }));
    }, timeout);

    return () => {
      if (progressInterval) clearInterval(progressInterval);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [showProgress, timeout, retryCount]);

  const handleRetry = () => {
    if (retryCount < retryAttempts) {
      setRetryCount(prev => prev + 1);
      setLoadingState({
        progress: 0,
        message: `Retrying... (${retryCount + 1}/${retryAttempts})`,
        stage: 'retry'
      });
    } else {
      setLoadingState(prev => ({
        ...prev,
        stage: 'error',
        message: 'Maximum retry attempts reached'
      }));
    }
  };

  const defaultFallback = (
    <DefaultLoadingFallback
      {...(showProgress !== undefined && { showProgress })}
      {...(componentName && { componentName })}
      {...(loadingState && { loadingState })}
      {...(handleRetry && { onRetry: handleRetry })}
    />
  );

  return (
    <div className={cn('lazy-route-container', className)}>
      <LazyRouteErrorBoundary
        {...(componentName && { componentName })}
        onError={(error) => {
          setLoadingState(prev => ({
            ...prev,
            stage: 'error',
            message: error.message
          }));
        }}
      >
        <Suspense fallback={fallback || defaultFallback}>
          <AnimatePresence mode="wait">
            <motion.div
              key="lazy-content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </Suspense>
      </LazyRouteErrorBoundary>
    </div>
  );
};

// Enhanced lazy route with preloading
export const PreloadableLazyRoute: React.FC<LazyRouteProps & {
  preloadComponent?: () => Promise<any>;
  preloadTrigger?: 'hover' | 'viewport' | 'idle' | 'immediate';
}> = ({ preloadComponent, preloadTrigger = 'hover', ...props }) => {
  const [isPreloaded, setIsPreloaded] = useState(false);

  useEffect(() => {
    if (preloadTrigger === 'immediate' && preloadComponent && !isPreloaded) {
      preloadComponent().then(() => setIsPreloaded(true));
    } else if (preloadTrigger === 'idle' && preloadComponent && !isPreloaded) {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          preloadComponent().then(() => setIsPreloaded(true));
        });
      } else {
        setTimeout(() => {
          preloadComponent().then(() => setIsPreloaded(true));
        }, 1000);
      }
    }
  }, [preloadComponent, preloadTrigger, isPreloaded]);

  const handlePreload = () => {
    if (preloadComponent && !isPreloaded) {
      preloadComponent().then(() => setIsPreloaded(true));
    }
  };

  return (
    <div
      onMouseEnter={preloadTrigger === 'hover' ? handlePreload : undefined}
      data-preload={props.componentName}
    >
      <LazyRoute {...props} />
    </div>
  );
};

export default LazyRoute;