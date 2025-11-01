/**
 * Progressive enhancement components and utilities
 * Ensures core functionality works without JavaScript and provides graceful degradation
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { cn } from '../utils';

// Progressive enhancement wrapper
interface ProgressiveEnhancementProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  enableJavaScript?: boolean;
  className?: string;
}

export const ProgressiveEnhancement: React.FC<ProgressiveEnhancementProps> = ({
  children,
  fallback,
  enableJavaScript = true,
  className
}) => {
  const [jsEnabled, setJsEnabled] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Detect JavaScript availability
    setJsEnabled(enableJavaScript);

    // Monitor online status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [enableJavaScript]);

  // Offline fallback
  if (!isOnline) {
    return (
      <div className={cn('text-center p-8 bg-slate-800 rounded-lg', className)}>
        <WifiOff className="w-12 h-12 text-slate-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">You're offline</h3>
        <p className="text-slate-300 mb-4">
          Some features may not be available while you're offline.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    );
  }

  // JavaScript disabled fallback
  if (!jsEnabled && fallback) {
    return (
      <div className={className}>
        <noscript>
          {fallback}
        </noscript>
      </div>
    );
  }

  return <div className={className}>{children}</div>;
};

// No-JavaScript form component
export const NoJSForm: React.FC<{
  action: string;
  method?: 'GET' | 'POST';
  children: React.ReactNode;
  className?: string;
}> = ({ action, method = 'POST', children, className }) => {
  return (
    <form action={action} method={method} className={className}>
      {children}
      <noscript>
        <div className="mt-4 p-4 bg-yellow-900/50 border border-yellow-600 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-yellow-400 mr-2" />
            <p className="text-yellow-200 text-sm">
              JavaScript is disabled. Basic functionality is available, but some features may be limited.
            </p>
          </div>
        </div>
      </noscript>
    </form>
  );
};

// Progressive file upload component
export const ProgressiveFileUpload: React.FC<{
  onFileSelect?: (files: FileList) => void;
  accept?: string;
  multiple?: boolean;
  className?: string;
}> = ({ onFileSelect, accept, multiple = false, className }) => {
  const [dragActive, setDragActive] = useState(false);
  const [jsEnabled, setJsEnabled] = useState(false);

  useEffect(() => {
    setJsEnabled(true);
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect?.(e.dataTransfer.files);
    }
  }, [onFileSelect]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileSelect?.(e.target.files);
    }
  }, [onFileSelect]);

  return (
    <div className={className}>
      {/* Enhanced version with JavaScript */}
      {jsEnabled && (
        <div
          className={cn(
            'border-2 border-dashed border-slate-600 rounded-lg p-8 text-center transition-colors',
            dragActive ? 'border-cyan-400 bg-cyan-400/10' : 'hover:border-slate-500'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept={accept}
            multiple={multiple}
            onChange={handleChange}
            className="hidden"
            id="file-upload-enhanced"
          />
          <label
            htmlFor="file-upload-enhanced"
            className="cursor-pointer block"
          >
            <div className="text-slate-300 mb-2">
              Drag and drop files here, or click to select
            </div>
            <div className="text-sm text-slate-500">
              {accept ? `Supported formats: ${accept}` : 'All file types supported'}
            </div>
          </label>
        </div>
      )}

      {/* Fallback version without JavaScript */}
      <noscript>
        <div className="border-2 border-slate-600 rounded-lg p-8 text-center">
          <input
            type="file"
            accept={accept}
            multiple={multiple}
            className="block w-full text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-cyan-500 file:text-white hover:file:bg-cyan-600"
          />
          <div className="mt-2 text-sm text-slate-500">
            Select files to upload
          </div>
        </div>
      </noscript>
    </div>
  );
};

// Progressive navigation component
export const ProgressiveNavigation: React.FC<{
  items: Array<{ href: string; label: string; onClick?: () => void }>;
  className?: string;
}> = ({ items, className }) => {
  const [jsEnabled, setJsEnabled] = useState(false);

  useEffect(() => {
    setJsEnabled(true);
  }, []);

  return (
    <nav className={className}>
      {jsEnabled ? (
        // Enhanced navigation with JavaScript
        <div className="flex space-x-6">
          {items.map((item, index) => (
            <button
              key={index}
              onClick={item.onClick}
              className="text-slate-300 hover:text-white transition-colors"
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : (
        // Fallback navigation without JavaScript
        <div className="flex space-x-6">
          {items.map((item, index) => (
            <a
              key={index}
              href={item.href}
              className="text-slate-300 hover:text-white transition-colors"
            >
              {item.label}
            </a>
          ))}
        </div>
      )}
      
      <noscript>
        <div className="flex space-x-6">
          {items.map((item, index) => (
            <a
              key={index}
              href={item.href}
              className="text-slate-300 hover:text-white transition-colors"
            >
              {item.label}
            </a>
          ))}
        </div>
      </noscript>
    </nav>
  );
};

// Progressive content loader with fallback
export const ProgressiveContentLoader: React.FC<{
  loadContent: () => Promise<React.ReactNode>;
  fallbackContent: React.ReactNode;
  loadingContent?: React.ReactNode;
  errorContent?: React.ReactNode;
  className?: string;
}> = ({
  loadContent,
  fallbackContent,
  loadingContent,
  errorContent,
  className
}) => {
  const [content, setContent] = useState<React.ReactNode>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jsEnabled, setJsEnabled] = useState(false);

  useEffect(() => {
    setJsEnabled(true);
    
    loadContent()
      .then(setContent)
      .catch((err) => {
        setError(err.message);
        console.error('Failed to load progressive content:', err);
      })
      .finally(() => setLoading(false));
  }, [loadContent]);

  if (!jsEnabled) {
    return <div className={className}>{fallbackContent}</div>;
  }

  if (loading) {
    return (
      <div className={className}>
        {loadingContent || (
          <div className="text-center p-4">
            <div className="animate-spin w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-slate-300">Loading content...</p>
          </div>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        {errorContent || (
          <div className="text-center p-4 text-red-400">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
            <p>Failed to load content</p>
            <p className="text-sm text-slate-500 mt-1">{error}</p>
          </div>
        )}
        <noscript>
          {fallbackContent}
        </noscript>
      </div>
    );
  }

  return (
    <div className={className}>
      {content}
      <noscript>
        {fallbackContent}
      </noscript>
    </div>
  );
};

// Connection status indicator
export const ConnectionStatus: React.FC<{ className?: string }> = ({ className }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showStatus, setShowStatus] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowStatus(true);
      setTimeout(() => setShowStatus(false), 3000);
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      setShowStatus(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <AnimatePresence>
      {showStatus && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className={cn(
            'fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg',
            isOnline 
              ? 'bg-green-500 text-white' 
              : 'bg-red-500 text-white',
            className
          )}
        >
          <div className="flex items-center space-x-2">
            {isOnline ? (
              <Wifi className="w-4 h-4" />
            ) : (
              <WifiOff className="w-4 h-4" />
            )}
            <span className="text-sm font-medium">
              {isOnline ? 'Back online' : 'You\'re offline'}
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProgressiveEnhancement;