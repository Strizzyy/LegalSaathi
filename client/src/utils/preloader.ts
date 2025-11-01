/**
 * Enhanced preloading utility for critical components and progressive enhancement
 * Implements intelligent preloading strategy with priority-based loading
 */

import { performanceMonitor } from './performanceMonitor';

interface PreloadConfig {
  name: string;
  importFn: () => Promise<any>;
  priority: 'critical' | 'high' | 'medium' | 'low';
  condition?: () => boolean;
  delay?: number;
}

// Component preload configurations
const PRELOAD_COMPONENTS: PreloadConfig[] = [
  // Critical components (load immediately)
  {
    name: 'DocumentUpload',
    importFn: () => import('../components/DocumentUpload'),
    priority: 'critical'
  },
  {
    name: 'Results',
    importFn: () => import('../components/Results'),
    priority: 'critical'
  },
  {
    name: 'Navigation',
    importFn: () => import('../components/Navigation'),
    priority: 'critical'
  },
  
  // High priority components (load on idle)
  {
    name: 'HeroSection',
    importFn: () => import('../components/HeroSection'),
    priority: 'high'
  },
  {
    name: 'LazyImage',
    importFn: () => import('../components/LazyImage'),
    priority: 'high'
  },
  {
    name: 'ProgressiveLoader',
    importFn: () => import('../components/ProgressiveLoader'),
    priority: 'high'
  },
  
  // Medium priority components (load with delay)
  {
    name: 'AdminPage',
    importFn: () => import('../pages/AdminPage'),
    priority: 'medium',
    condition: () => window.location.pathname.includes('/admin') || 
                     localStorage.getItem('user_role') === 'admin'
  },
  {
    name: 'HITLDashboard',
    importFn: () => import('../pages/HITLDashboard'),
    priority: 'medium',
    condition: () => window.location.pathname.includes('/hitl') || 
                     localStorage.getItem('user_role') === 'expert'
  },
  {
    name: 'MultipleImageAnalysis',
    importFn: () => import('../components/MultipleImageAnalysis'),
    priority: 'medium'
  },
  
  // Low priority components (load when idle)
  {
    name: 'AboutUs',
    importFn: () => import('../components/AboutUs'),
    priority: 'low',
    delay: 3000
  },
  {
    name: 'ContactUs',
    importFn: () => import('../components/ContactUs'),
    priority: 'low',
    delay: 3000
  },
  {
    name: 'PrivacyPolicy',
    importFn: () => import('../components/PrivacyPolicy'),
    priority: 'low',
    delay: 5000
  },
  {
    name: 'TermsOfService',
    importFn: () => import('../components/TermsOfService'),
    priority: 'low',
    delay: 5000
  }
];

// Preload critical components on application initialization
export const preloadCriticalComponents = () => {
  const criticalComponents = PRELOAD_COMPONENTS.filter(c => c.priority === 'critical');
  
  criticalComponents.forEach(({ name, importFn, condition }) => {
    if (condition && !condition()) return;
    
    performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
      console.warn(`Failed to preload critical component ${name}:`, error);
    });
  });
  
  console.log(`🚀 Preloaded ${criticalComponents.length} critical components`);
};



// Preload components on idle time
export const preloadOnIdle = () => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      // Preload less critical components during idle time
      performanceMonitor.measureComponentLoad('AboutUs', () => import('../components/AboutUs')).catch(() => {});
      performanceMonitor.measureComponentLoad('ContactUs', () => import('../components/ContactUs')).catch(() => {});
      performanceMonitor.measureComponentLoad('PrivacyPolicy', () => import('../components/PrivacyPolicy')).catch(() => {});
      performanceMonitor.measureComponentLoad('TermsOfService', () => import('../components/TermsOfService')).catch(() => {});
    });
  } else {
    // Fallback for browsers that don't support requestIdleCallback
    setTimeout(() => {
      performanceMonitor.measureComponentLoad('AboutUs', () => import('../components/AboutUs')).catch(() => {});
      performanceMonitor.measureComponentLoad('ContactUs', () => import('../components/ContactUs')).catch(() => {});
      performanceMonitor.measureComponentLoad('PrivacyPolicy', () => import('../components/PrivacyPolicy')).catch(() => {});
      performanceMonitor.measureComponentLoad('TermsOfService', () => import('../components/TermsOfService')).catch(() => {});
    }, 2000);
  }
};



// Preload high priority components on idle
export const preloadHighPriorityComponents = () => {
  const highPriorityComponents = PRELOAD_COMPONENTS.filter(c => c.priority === 'high');
  
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      highPriorityComponents.forEach(({ name, importFn, condition }) => {
        if (condition && !condition()) return;
        
        performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
          console.warn(`Failed to preload high priority component ${name}:`, error);
        });
      });
      
      console.log(`⚡ Preloaded ${highPriorityComponents.length} high priority components on idle`);
    });
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      highPriorityComponents.forEach(({ name, importFn, condition }) => {
        if (condition && !condition()) return;
        
        performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
          console.warn(`Failed to preload high priority component ${name}:`, error);
        });
      });
    }, 1000);
  }
};

// Preload medium priority components with conditions
export const preloadMediumPriorityComponents = () => {
  const mediumPriorityComponents = PRELOAD_COMPONENTS.filter(c => c.priority === 'medium');
  
  mediumPriorityComponents.forEach(({ name, importFn, condition, delay = 2000 }) => {
    if (condition && !condition()) return;
    
    setTimeout(() => {
      performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
        console.warn(`Failed to preload medium priority component ${name}:`, error);
      });
    }, delay);
  });
  
  console.log(`📦 Scheduled ${mediumPriorityComponents.length} medium priority components for preloading`);
};

// Preload low priority components when system is idle
export const preloadLowPriorityComponents = () => {
  const lowPriorityComponents = PRELOAD_COMPONENTS.filter(c => c.priority === 'low');
  
  lowPriorityComponents.forEach(({ name, importFn, condition, delay = 5000 }) => {
    if (condition && !condition()) return;
    
    setTimeout(() => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
            console.warn(`Failed to preload low priority component ${name}:`, error);
          });
        });
      } else {
        performanceMonitor.measureComponentLoad(name, importFn).catch(error => {
          console.warn(`Failed to preload low priority component ${name}:`, error);
        });
      }
    }, delay);
  });
  
  console.log(`🔄 Scheduled ${lowPriorityComponents.length} low priority components for background loading`);
};

// Enhanced preload components based on user interaction patterns
const createInteractionPreloaders = () => {
  // Preload admin components when user shows admin-like behavior
  const preloadAdminComponents = () => {
    const adminComponents = ['AdminPage'];
    adminComponents.forEach(name => {
      const config = PRELOAD_COMPONENTS.find(c => c.name === name);
      if (config) {
        performanceMonitor.measureComponentLoad(config.name, config.importFn).catch(error => {
          console.warn(`Failed to preload admin component ${name}:`, error);
        });
      }
    });
  };

  // Preload HITL components when user shows expert-like behavior
  const preloadHITLComponents = () => {
    const hitlComponents = ['HITLDashboard'];
    hitlComponents.forEach(name => {
      const config = PRELOAD_COMPONENTS.find(c => c.name === name);
      if (config) {
        performanceMonitor.measureComponentLoad(config.name, config.importFn).catch(error => {
          console.warn(`Failed to preload HITL component ${name}:`, error);
        });
      }
    });
  };

  // Preload multiple image analysis when user uploads multiple files
  const preloadMultipleImageAnalysis = () => {
    const config = PRELOAD_COMPONENTS.find(c => c.name === 'MultipleImageAnalysis');
    if (config) {
      performanceMonitor.measureComponentLoad(config.name, config.importFn).catch(error => {
        console.warn('Failed to preload MultipleImageAnalysis component:', error);
      });
    }
  };

  // Preload chart components when user views analytics
  const preloadChartComponents = () => {
    // Preload chart-related components
    import('../components/SkeletonLoader').catch(() => {});
    import('../components/ProgressiveLoader').catch(() => {});
  };

  return {
    preloadAdminComponents,
    preloadHITLComponents,
    preloadMultipleImageAnalysis,
    preloadChartComponents,
  };
};

// Intelligent preloading based on viewport and user behavior
export const setupIntelligentPreloading = () => {
  // Preload components when they're about to enter viewport
  const setupViewportPreloading = () => {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const target = entry.target as HTMLElement;
              const componentName = target.dataset.preload;
              
              if (componentName) {
                const config = PRELOAD_COMPONENTS.find(c => c.name === componentName);
                if (config) {
                  performanceMonitor.measureComponentLoad(config.name, config.importFn);
                  observer.unobserve(target);
                }
              }
            }
          });
        },
        { rootMargin: '100px' }
      );

      // Observe elements with data-preload attribute
      document.querySelectorAll('[data-preload]').forEach(el => {
        observer.observe(el);
      });

      return observer;
    }
  };

  // Preload on user interaction hints
  const setupInteractionPreloading = () => {
    // Preload on hover with delay
    document.addEventListener('mouseover', (e) => {
      const target = e.target as HTMLElement;
      const preloadHint = target.closest('[data-preload-on-hover]');
      
      if (preloadHint) {
        const componentName = preloadHint.getAttribute('data-preload-on-hover');
        if (componentName) {
          setTimeout(() => {
            const config = PRELOAD_COMPONENTS.find(c => c.name === componentName);
            if (config) {
              performanceMonitor.measureComponentLoad(config.name, config.importFn);
            }
          }, 100);
        }
      }
    });

    // Preload on focus
    document.addEventListener('focusin', (e) => {
      const target = e.target as HTMLElement;
      const preloadHint = target.closest('[data-preload-on-focus]');
      
      if (preloadHint) {
        const componentName = preloadHint.getAttribute('data-preload-on-focus');
        if (componentName) {
          const config = PRELOAD_COMPONENTS.find(c => c.name === componentName);
          if (config) {
            performanceMonitor.measureComponentLoad(config.name, config.importFn);
          }
        }
      }
    });
  };

  return {
    viewportObserver: setupViewportPreloading(),
    interactionListeners: setupInteractionPreloading()
  };
};

// Enhanced initialization with progressive enhancement
export const initializeProgressivePreloading = () => {
  console.log('🎯 Initializing progressive preloading strategy...');
  
  // Phase 1: Critical components (immediate)
  preloadCriticalComponents();
  
  // Phase 2: High priority components (on idle)
  preloadHighPriorityComponents();
  
  // Phase 3: Medium priority components (with delay)
  preloadMediumPriorityComponents();
  
  // Phase 4: Low priority components (background)
  preloadLowPriorityComponents();
  
  // Phase 5: Intelligent preloading setup
  const intelligentPreloading = setupIntelligentPreloading();
  
  // Return interaction-based preloaders and cleanup function
  const interactionPreloaders = createInteractionPreloaders();
  
  const cleanup = () => {
    intelligentPreloading.viewportObserver?.disconnect();
  };
  
  return {
    ...interactionPreloaders,
    cleanup
  };
};

// Legacy function for backward compatibility
export const initializePreloading = initializeProgressivePreloading;

// Export the interaction preloaders for backward compatibility
export const preloadOnUserInteraction = createInteractionPreloaders;