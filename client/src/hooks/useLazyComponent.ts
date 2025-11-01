/**
 * Enhanced lazy component hook with error handling and loading states
 * Implements dynamic component loading with comprehensive error handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { performanceMonitor } from '../utils/performanceMonitor';

interface LazyComponentState<T> {
  Component: T | null;
  loading: boolean;
  error: string | null;
  loadComponent: () => Promise<T | null>;
  preload: () => void;
  retry: () => void;
}

interface LazyComponentOptions {
  retryAttempts?: number;
  retryDelay?: number;
  timeout?: number;
  preloadOnIdle?: boolean;
  preloadOnHover?: boolean;
}

export function useLazyComponent<T = React.ComponentType<any>>(
  importFn: () => Promise<{ default: T } | T>,
  componentName: string,
  options: LazyComponentOptions = {}
): LazyComponentState<T> {
  const {
    retryAttempts = 3,
    retryDelay = 1000,
    timeout = 10000,
    preloadOnIdle = false,
    preloadOnHover = false
  } = options;

  const [Component, setComponent] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAttempt, setCurrentAttempt] = useState(0);
  
  const loadingRef = useRef(false);
  const componentRef = useRef<T | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadComponent = useCallback(async (): Promise<T | null> => {
    // Return cached component if already loaded
    if (componentRef.current) {
      return componentRef.current;
    }

    // Prevent multiple simultaneous loads
    if (loadingRef.current) {
      return new Promise((resolve) => {
        const checkLoaded = () => {
          if (componentRef.current) {
            resolve(componentRef.current);
          } else if (!loadingRef.current) {
            resolve(null);
          } else {
            setTimeout(checkLoaded, 100);
          }
        };
        checkLoaded();
      });
    }

    loadingRef.current = true;
    setLoading(true);
    setError(null);

    // Set timeout for loading
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      if (loadingRef.current) {
        setError(`Component ${componentName} failed to load within ${timeout}ms`);
        setLoading(false);
        loadingRef.current = false;
      }
    }, timeout);

    try {
      const startTime = performance.now();
      
      const module = await importFn();
      const LoadedComponent = 'default' in module ? module.default : module;
      
      const loadTime = performance.now() - startTime;
      
      // Store component reference
      componentRef.current = LoadedComponent as T;
      setComponent(LoadedComponent as T);
      
      // Track performance
      performanceMonitor.measureComponentLoad(componentName, () => Promise.resolve(LoadedComponent));
      
      console.log(`✅ Component ${componentName} loaded successfully in ${loadTime.toFixed(2)}ms`);
      
      setCurrentAttempt(0);
      return LoadedComponent as T;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error(`❌ Failed to load component ${componentName}:`, errorMessage);
      
      // Retry logic
      if (currentAttempt < retryAttempts) {
        console.log(`🔄 Retrying component ${componentName} (attempt ${currentAttempt + 1}/${retryAttempts})`);
        setCurrentAttempt(prev => prev + 1);
        
        setTimeout(() => {
          loadComponent();
        }, retryDelay * Math.pow(2, currentAttempt)); // Exponential backoff
        
        return null;
      }
      
      setError(`Failed to load ${componentName} after ${retryAttempts} attempts: ${errorMessage}`);
      return null;
      
    } finally {
      setLoading(false);
      loadingRef.current = false;
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }
  }, [importFn, componentName, retryAttempts, retryDelay, timeout, currentAttempt]);

  const preload = useCallback(() => {
    if (!componentRef.current && !loadingRef.current) {
      loadComponent();
    }
  }, [loadComponent]);

  const retry = useCallback(() => {
    setCurrentAttempt(0);
    setError(null);
    componentRef.current = null;
    setComponent(null);
    loadComponent();
  }, [loadComponent]);

  // Preload on idle if requested
  useEffect(() => {
    if (preloadOnIdle && 'requestIdleCallback' in window) {
      const idleCallback = requestIdleCallback(() => {
        preload();
      });
      
      return () => {
        cancelIdleCallback(idleCallback);
      };
    }
  }, [preload, preloadOnIdle]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    Component,
    loading,
    error,
    loadComponent,
    preload,
    retry
  };
}

// Hook for preloading multiple components
export function useLazyComponentPreloader(
  components: Array<{
    name: string;
    importFn: () => Promise<any>;
    priority?: 'high' | 'medium' | 'low';
  }>
) {
  const [preloadStatus, setPreloadStatus] = useState<Record<string, 'pending' | 'loading' | 'loaded' | 'error'>>({});

  const preloadComponent = useCallback(async (name: string, importFn: () => Promise<any>) => {
    setPreloadStatus(prev => ({ ...prev, [name]: 'loading' }));
    
    try {
      await performanceMonitor.measureComponentLoad(name, importFn);
      setPreloadStatus(prev => ({ ...prev, [name]: 'loaded' }));
      console.log(`✅ Preloaded component: ${name}`);
    } catch (error) {
      setPreloadStatus(prev => ({ ...prev, [name]: 'error' }));
      console.warn(`❌ Failed to preload component: ${name}`, error);
    }
  }, []);

  const preloadAll = useCallback(() => {
    // Sort by priority
    const sortedComponents = [...components].sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority || 'medium'] - priorityOrder[b.priority || 'medium'];
    });

    // Preload high priority components immediately
    const highPriority = sortedComponents.filter(c => c.priority === 'high');
    highPriority.forEach(({ name, importFn }) => {
      preloadComponent(name, importFn);
    });

    // Preload medium priority components on idle
    const mediumPriority = sortedComponents.filter(c => c.priority === 'medium' || !c.priority);
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        mediumPriority.forEach(({ name, importFn }) => {
          preloadComponent(name, importFn);
        });
      });
    } else {
      setTimeout(() => {
        mediumPriority.forEach(({ name, importFn }) => {
          preloadComponent(name, importFn);
        });
      }, 1000);
    }

    // Preload low priority components with delay
    const lowPriority = sortedComponents.filter(c => c.priority === 'low');
    setTimeout(() => {
      lowPriority.forEach(({ name, importFn }) => {
        preloadComponent(name, importFn);
      });
    }, 3000);
  }, [components, preloadComponent]);

  const preloadByName = useCallback((name: string) => {
    const component = components.find(c => c.name === name);
    if (component) {
      preloadComponent(component.name, component.importFn);
    }
  }, [components, preloadComponent]);

  return {
    preloadStatus,
    preloadAll,
    preloadByName,
    preloadComponent
  };
}

export default useLazyComponent;