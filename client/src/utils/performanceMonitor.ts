/**
 * Performance monitoring utility for tracking bundle optimization metrics
 */

interface PerformanceMetrics {
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
  bundleLoadTime?: number;
  componentLoadTimes: Map<string, number>;
  apiResponseTimes: Map<string, number[]>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    componentLoadTimes: new Map(),
    apiResponseTimes: new Map(),
  };

  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeWebVitals();
    this.measureBundleLoadTime();
  }

  // Initialize Core Web Vitals monitoring
  private initializeWebVitals(): void {
    // Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          this.metrics.lcp = lastEntry.startTime;
          console.log('LCP:', lastEntry.startTime);
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (error) {
        console.warn('LCP observer not supported:', error);
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            this.metrics.fid = entry.processingStart - entry.startTime;
            console.log('FID:', this.metrics.fid);
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (error) {
        console.warn('FID observer not supported:', error);
      }

      // Cumulative Layout Shift
      try {
        let cls = 0;
        const clsObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              cls += entry.value;
            }
          });
          this.metrics.cls = cls;
          console.log('CLS:', cls);
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (error) {
        console.warn('CLS observer not supported:', error);
      }
    }
  }

  // Measure bundle load time
  private measureBundleLoadTime(): void {
    if ('performance' in window) {
      window.addEventListener('load', () => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        this.metrics.ttfb = navigation.responseStart - navigation.requestStart;
        this.metrics.bundleLoadTime = navigation.loadEventEnd - navigation.fetchStart;
        
        console.log('TTFB:', this.metrics.ttfb);
        console.log('Bundle Load Time:', this.metrics.bundleLoadTime);
      });
    }
  }

  // Measure component load time
  measureComponentLoad<T>(componentName: string, loadFn: () => Promise<T>): Promise<T> {
    const startTime = performance.now();
    
    return loadFn().then((result) => {
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      this.metrics.componentLoadTimes.set(componentName, loadTime);
      console.log(`Component ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
      
      return result;
    }).catch((error) => {
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      console.warn(`Component ${componentName} failed to load in ${loadTime.toFixed(2)}ms:`, error);
      throw error;
    });
  }

  // Measure API response time
  measureApiCall<T>(endpoint: string, apiFn: () => Promise<T>): Promise<T> {
    const startTime = performance.now();
    
    return apiFn().then((result) => {
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      if (!this.metrics.apiResponseTimes.has(endpoint)) {
        this.metrics.apiResponseTimes.set(endpoint, []);
      }
      this.metrics.apiResponseTimes.get(endpoint)!.push(responseTime);
      
      console.log(`API ${endpoint} responded in ${responseTime.toFixed(2)}ms`);
      
      return result;
    }).catch((error) => {
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      console.warn(`API ${endpoint} failed in ${responseTime.toFixed(2)}ms:`, error);
      throw error;
    });
  }

  // Get performance summary
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // Get performance summary with averages
  getPerformanceSummary(): {
    webVitals: { lcp?: number; fid?: number; cls?: number; ttfb?: number };
    bundleLoadTime?: number;
    averageComponentLoadTime: number;
    averageApiResponseTime: number;
    componentLoadTimes: Record<string, number>;
    apiResponseTimes: Record<string, { avg: number; min: number; max: number; count: number }>;
  } {
    // Calculate average component load time
    const componentTimes = Array.from(this.metrics.componentLoadTimes.values());
    const averageComponentLoadTime = componentTimes.length > 0 
      ? componentTimes.reduce((a, b) => a + b, 0) / componentTimes.length 
      : 0;

    // Calculate API response time statistics
    const apiStats: Record<string, { avg: number; min: number; max: number; count: number }> = {};
    let totalApiTime = 0;
    let totalApiCalls = 0;

    this.metrics.apiResponseTimes.forEach((times, endpoint) => {
      const avg = times.reduce((a, b) => a + b, 0) / times.length;
      const min = Math.min(...times);
      const max = Math.max(...times);
      
      apiStats[endpoint] = { avg, min, max, count: times.length };
      totalApiTime += times.reduce((a, b) => a + b, 0);
      totalApiCalls += times.length;
    });

    const averageApiResponseTime = totalApiCalls > 0 ? totalApiTime / totalApiCalls : 0;

    return {
      webVitals: {
        ...(this.metrics.lcp !== undefined && { lcp: this.metrics.lcp }),
        ...(this.metrics.fid !== undefined && { fid: this.metrics.fid }),
        ...(this.metrics.cls !== undefined && { cls: this.metrics.cls }),
        ...(this.metrics.ttfb !== undefined && { ttfb: this.metrics.ttfb }),
      },
      ...(this.metrics.bundleLoadTime !== undefined && { bundleLoadTime: this.metrics.bundleLoadTime }),
      averageComponentLoadTime,
      averageApiResponseTime,
      componentLoadTimes: Object.fromEntries(this.metrics.componentLoadTimes),
      apiResponseTimes: apiStats,
    };
  }

  // Check if performance targets are met
  checkPerformanceTargets(): {
    lcp: { value?: number; target: number; passed: boolean };
    fid: { value?: number; target: number; passed: boolean };
    cls: { value?: number; target: number; passed: boolean };
    bundleSize: { passed: boolean; message: string };
  } {
    const targets = {
      lcp: 2500, // 2.5 seconds
      fid: 100,  // 100ms
      cls: 0.1,  // 0.1 score
    };

    return {
      lcp: {
        ...(this.metrics.lcp !== undefined && { value: this.metrics.lcp }),
        target: targets.lcp,
        passed: this.metrics.lcp ? this.metrics.lcp <= targets.lcp : false,
      },
      fid: {
        ...(this.metrics.fid !== undefined && { value: this.metrics.fid }),
        target: targets.fid,
        passed: this.metrics.fid ? this.metrics.fid <= targets.fid : false,
      },
      cls: {
        ...(this.metrics.cls !== undefined && { value: this.metrics.cls }),
        target: targets.cls,
        passed: this.metrics.cls ? this.metrics.cls <= targets.cls : false,
      },
      bundleSize: {
        passed: true, // Will be determined by build process
        message: 'Bundle size analysis available in build output',
      },
    };
  }

  // Cleanup observers
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Create global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// Export for use in components
export default performanceMonitor;