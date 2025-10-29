import { useState, useEffect } from 'react';
import { backendReadinessService, type ReadinessState, type BackendReadinessStatus } from '../services/backendReadinessService';

export interface UseBackendReadinessReturn {
  isReady: boolean;
  isChecking: boolean;
  status: BackendReadinessStatus | undefined;
  retryCount: number;
  maxRetries: number;
  waitForBackend: (timeoutMs?: number) => Promise<boolean>;
  forceRecheck: () => Promise<void>;
}

export const useBackendReadiness = (): UseBackendReadinessReturn => {
  const [readinessState, setReadinessState] = useState<ReadinessState>(
    backendReadinessService.getState()
  );

  useEffect(() => {
    const unsubscribe = backendReadinessService.subscribe(() => {
      setReadinessState(backendReadinessService.getState());
    });

    return unsubscribe;
  }, []);

  return {
    isReady: readinessState.isReady,
    isChecking: readinessState.isChecking,
    status: readinessState.status,
    retryCount: readinessState.retryCount,
    maxRetries: readinessState.maxRetries,
    waitForBackend: backendReadinessService.waitForBackend.bind(backendReadinessService),
    forceRecheck: backendReadinessService.forceRecheck.bind(backendReadinessService)
  };
};

export default useBackendReadiness;