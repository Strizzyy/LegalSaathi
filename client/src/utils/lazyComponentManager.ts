/**
 * Lazy Component Manager for heavy UI components
 * Manages lazy loading of charts, complex forms, admin panels, and other heavy components
 */

import { lazy, ComponentType } from 'react';
import { performanceMonitor } from './performanceMonitor';

interface LazyComponentConfig {
  name: string;
  importFn: () => Promise<{ default: ComponentType<any> }>;
  preloadCondition?: () => boolean;
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: 'chart' | 'form' | 'admin' | 'dashboard' | 'modal' | 'page' | 'widget';
  estimatedSize?: number; // KB
  dependencies?: string[];
}

class LazyComponentManager {
  private components = new Map<string, ComponentType<any>>();
  private loadingStates = new Map<string, 'idle' | 'loading' | 'loaded' | 'error'>();

  private loadPromises = new Map<string, Promise<ComponentType<any>>>();

  // Heavy UI components configuration (only existing components)
  private readonly HEAVY_COMPONENTS: LazyComponentConfig[] = [
    // Existing page components
    {
      name: 'AdminPage',
      importFn: () => import('../pages/AdminPage'),
      priority: 'medium',
      category: 'page',
      estimatedSize: 80,
      preloadCondition: () => localStorage.getItem('user_role') === 'admin'
    },
    {
      name: 'HITLDashboard',
      importFn: () => import('../pages/HITLDashboard'),
      priority: 'medium',
      category: 'page',
      estimatedSize: 70,
      preloadCondition: () => localStorage.getItem('user_role') === 'expert'
    },

    // Existing heavy components
    {
      name: 'Results',
      importFn: () => import('../components/Results'),
      priority: 'high',
      category: 'page',
      estimatedSize: 120
    },
    {
      name: 'MultipleImageAnalysis',
      importFn: () => import('../components/MultipleImageAnalysis'),
      priority: 'medium',
      category: 'widget',
      estimatedSize: 45
    },

    // Legal document components
    {
      name: 'AboutUs',
      importFn: () => import('../components/AboutUs'),
      priority: 'low',
      category: 'page',
      estimatedSize: 25
    },
    {
      name: 'ContactUs',
      importFn: () => import('../components/ContactUs'),
      priority: 'low',
      category: 'page',
      estimatedSize: 30
    },
    {
      name: 'PrivacyPolicy',
      importFn: () => import('../components/PrivacyPolicy'),
      priority: 'low',
      category: 'page',
      estimatedSize: 35
    },
    {
      name: 'TermsOfService',
      importFn: () => import('../components/TermsOfService'),
      priority: 'low',
      category: 'page',
      estimatedSize: 40
    },

    // Modal components
    {
      name: 'TranslationModal',
      importFn: () => import('../components/TranslationModal'),
      priority: 'medium',
      category: 'modal',
      estimatedSize: 25
    },
    {
      name: 'EmailModal',
      importFn: () => import('../components/EmailModal'),
      priority: 'medium',
      category: 'modal',
      estimatedSize: 20
    },

    // Utility components
    {
      name: 'LazyImage',
      importFn: () => import('../components/LazyImage'),
      priority: 'high',
      category: 'widget',
      estimatedSize: 15
    },
    {
      name: 'ProgressiveLoader',
      importFn: () => import('../components/ProgressiveLoader'),
      priority: 'high',
      category: 'widget',
      estimatedSize: 20
    },
    {
      name: 'SkeletonLoader',
      importFn: () => import('../components/SkeletonLoader'),
      priority: 'high',
      category: 'widget',
      estimatedSize: 10
    }
  ];

  constructor() {
    this.initializeComponents();
  }

  private initializeComponents() {
    // Initialize loading states
    this.HEAVY_COMPONENTS.forEach(config => {
      this.loadingStates.set(config.name, 'idle');
    });

    // Setup preload queue based on priority
    this.setupPreloadQueue();
  }

  private setupPreloadQueue() {
    // Sort by priority and add to preload queue
    const sortedComponents = [...this.HEAVY_COMPONENTS].sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });

    const preloadQueue = sortedComponents.filter(config => {
      // Check preload conditions
      if (config.preloadCondition && !config.preloadCondition()) {
        return false;
      }
      return true;
    });
    
    // Process the preload queue (if needed in the future)
    console.log(`Prepared ${preloadQueue.length} components for preloading`);
  }

  // Get lazy component with automatic loading
  getLazyComponent(name: string): ComponentType<any> | null {
    const config = this.HEAVY_COMPONENTS.find(c => c.name === name);
    if (!config) {
      console.warn(`Component ${name} not found in heavy components registry`);
      return null;
    }

    // Return cached component if already loaded
    if (this.components.has(name)) {
      return this.components.get(name)!;
    }

    // Create lazy component
    const LazyComponent = lazy(() => {
      this.loadingStates.set(name, 'loading');
      
      return performanceMonitor.measureComponentLoad(name, config.importFn)
        .then(module => {
          this.loadingStates.set(name, 'loaded');
          this.components.set(name, module.default);
          console.log(`✅ Lazy loaded heavy component: ${name} (~${config.estimatedSize}KB)`);
          return module;
        })
        .catch(error => {
          this.loadingStates.set(name, 'error');
          console.error(`❌ Failed to lazy load component ${name}:`, error);
          throw error;
        });
    });

    this.components.set(name, LazyComponent);
    return LazyComponent;
  }

  // Preload component without rendering
  async preloadComponent(name: string): Promise<ComponentType<any> | null> {
    const config = this.HEAVY_COMPONENTS.find(c => c.name === name);
    if (!config) {
      console.warn(`Component ${name} not found for preloading`);
      return null;
    }

    // Return cached component if already loaded
    if (this.components.has(name) && this.loadingStates.get(name) === 'loaded') {
      return this.components.get(name)!;
    }

    // Return existing promise if already loading
    if (this.loadPromises.has(name)) {
      return this.loadPromises.get(name)!;
    }

    // Start preloading
    this.loadingStates.set(name, 'loading');
    
    const loadPromise = performanceMonitor.measureComponentLoad(name, config.importFn)
      .then(module => {
        this.loadingStates.set(name, 'loaded');
        this.components.set(name, module.default);
        this.loadPromises.delete(name);
        console.log(`🚀 Preloaded heavy component: ${name} (~${config.estimatedSize}KB)`);
        return module.default;
      })
      .catch(error => {
        this.loadingStates.set(name, 'error');
        this.loadPromises.delete(name);
        console.error(`❌ Failed to preload component ${name}:`, error);
        throw error;
      });

    this.loadPromises.set(name, loadPromise);
    return loadPromise;
  }

  // Preload components by category
  async preloadByCategory(category: LazyComponentConfig['category']): Promise<void> {
    const categoryComponents = this.HEAVY_COMPONENTS.filter(c => c.category === category);
    
    console.log(`📦 Preloading ${categoryComponents.length} ${category} components...`);
    
    const preloadPromises = categoryComponents.map(config => 
      this.preloadComponent(config.name).catch(error => {
        console.warn(`Failed to preload ${config.name}:`, error);
      })
    );

    await Promise.allSettled(preloadPromises);
  }

  // Preload components by priority
  async preloadByPriority(priority: LazyComponentConfig['priority']): Promise<void> {
    const priorityComponents = this.HEAVY_COMPONENTS.filter(c => c.priority === priority);
    
    console.log(`⚡ Preloading ${priorityComponents.length} ${priority} priority components...`);
    
    const preloadPromises = priorityComponents.map(config => 
      this.preloadComponent(config.name).catch(error => {
        console.warn(`Failed to preload ${config.name}:`, error);
      })
    );

    await Promise.allSettled(preloadPromises);
  }

  // Smart preloading based on user behavior
  async smartPreload(userContext: {
    isAdmin?: boolean;
    hasUploadedFiles?: boolean;
    viewedAnalytics?: boolean;
    usedAdvancedFeatures?: boolean;
  }): Promise<void> {
    const componentsToPreload: string[] = [];

    // Admin-specific components
    if (userContext.isAdmin) {
      componentsToPreload.push('AdminPage');
    }

    // Analytics components for users who viewed analytics
    if (userContext.viewedAnalytics) {
      componentsToPreload.push('Results', 'ProgressiveLoader');
    }

    // Advanced features for power users
    if (userContext.usedAdvancedFeatures) {
      componentsToPreload.push('MultipleImageAnalysis', 'TranslationModal', 'EmailModal');
    }

    // File upload related components
    if (userContext.hasUploadedFiles) {
      componentsToPreload.push('MultipleImageAnalysis', 'Results');
    }

    // Always preload utility components
    componentsToPreload.push('LazyImage', 'SkeletonLoader');

    console.log(`🎯 Smart preloading ${componentsToPreload.length} components based on user context`);

    const preloadPromises = componentsToPreload.map(name => 
      this.preloadComponent(name).catch(error => {
        console.warn(`Failed to smart preload ${name}:`, error);
      })
    );

    await Promise.allSettled(preloadPromises);
  }

  // Get loading state of a component
  getLoadingState(name: string): 'idle' | 'loading' | 'loaded' | 'error' {
    return this.loadingStates.get(name) || 'idle';
  }

  // Get all components by category
  getComponentsByCategory(category: LazyComponentConfig['category']): LazyComponentConfig[] {
    return this.HEAVY_COMPONENTS.filter(c => c.category === category);
  }

  // Get preload statistics
  getPreloadStats(): {
    total: number;
    loaded: number;
    loading: number;
    error: number;
    totalEstimatedSize: number;
    loadedSize: number;
  } {
    const total = this.HEAVY_COMPONENTS.length;
    let loaded = 0;
    let loading = 0;
    let error = 0;
    let totalEstimatedSize = 0;
    let loadedSize = 0;

    this.HEAVY_COMPONENTS.forEach(config => {
      const state = this.loadingStates.get(config.name);
      totalEstimatedSize += config.estimatedSize || 0;
      
      switch (state) {
        case 'loaded':
          loaded++;
          loadedSize += config.estimatedSize || 0;
          break;
        case 'loading':
          loading++;
          break;
        case 'error':
          error++;
          break;
      }
    });

    return {
      total,
      loaded,
      loading,
      error,
      totalEstimatedSize,
      loadedSize
    };
  }

  // Initialize progressive preloading
  initializeProgressivePreloading(): void {
    console.log('🎯 Initializing progressive preloading for heavy components...');

    // Phase 1: Critical components (immediate)
    this.preloadByPriority('critical');

    // Phase 2: High priority components (on idle)
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        this.preloadByPriority('high');
      });
    } else {
      setTimeout(() => {
        this.preloadByPriority('high');
      }, 1000);
    }

    // Phase 3: Medium priority components (with delay)
    setTimeout(() => {
      this.preloadByPriority('medium');
    }, 3000);

    // Phase 4: Low priority components (background)
    setTimeout(() => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          this.preloadByPriority('low');
        });
      } else {
        this.preloadByPriority('low');
      }
    }, 5000);
  }

  // Cleanup method
  cleanup(): void {
    this.components.clear();
    this.loadingStates.clear();
    this.loadPromises.clear();
    // Clear any preload queue references
  }
}

// Create global instance
export const lazyComponentManager = new LazyComponentManager();

// Export utility functions
export const getLazyComponent = (name: string) => lazyComponentManager.getLazyComponent(name);
export const preloadComponent = (name: string) => lazyComponentManager.preloadComponent(name);
export const preloadByCategory = (category: LazyComponentConfig['category']) => 
  lazyComponentManager.preloadByCategory(category);
export const smartPreload = (userContext: Parameters<typeof lazyComponentManager.smartPreload>[0]) => 
  lazyComponentManager.smartPreload(userContext);

export default lazyComponentManager;