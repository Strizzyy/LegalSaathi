import React, { useState, useEffect } from 'react';
import { backendReadinessService, type ReadinessState } from '../services/backendReadinessService';

interface BackendStatusIndicatorProps {
  className?: string;
  showDetails?: boolean;
}

const BackendStatusIndicator: React.FC<BackendStatusIndicatorProps> = ({ 
  className = '', 
  showDetails = false 
}) => {
  const [readinessState, setReadinessState] = useState<ReadinessState>(
    backendReadinessService.getState()
  );

  useEffect(() => {
    const unsubscribe = backendReadinessService.subscribe(() => {
      setReadinessState(backendReadinessService.getState());
    });

    return unsubscribe;
  }, []);

  // Don't show anything if backend is ready
  if (readinessState.isReady) {
    return null;
  }

  // Don't show if we've given up trying
  if (!readinessState.isChecking && readinessState.retryCount >= readinessState.maxRetries) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center">
          <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
          <span className="text-red-700 text-sm font-medium">
            Backend Connection Failed
          </span>
        </div>
        {showDetails && (
          <div className="mt-2 text-xs text-red-600">
            Unable to connect to backend services. Please refresh the page.
          </div>
        )}
      </div>
    );
  }

  // Show initialization status
  const status = readinessState.status;
  const pendingServices = status?.pending_services || [];
  const estimatedTime = status?.estimated_ready_time;

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
        <span className="text-blue-700 text-sm font-medium">
          Initializing Backend Services
        </span>
        <span className="text-blue-600 text-xs ml-2">
          ({readinessState.retryCount}/{readinessState.maxRetries})
        </span>
      </div>
      
      {showDetails && (
        <div className="mt-2 space-y-1">
          {pendingServices.length > 0 && (
            <div className="text-xs text-blue-600">
              <span className="font-medium">Pending:</span> {pendingServices.join(', ')}
            </div>
          )}
          {estimatedTime && (
            <div className="text-xs text-blue-600">
              <span className="font-medium">ETA:</span> {estimatedTime}
            </div>
          )}
          <div className="text-xs text-blue-500">
            Please wait while AI services start up...
          </div>
        </div>
      )}
    </div>
  );
};

export default BackendStatusIndicator;