interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class PerformanceService {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private completedMetrics: PerformanceMetric[] = [];

  startTimer(name: string, metadata?: Record<string, any>): void {
    const metric: PerformanceMetric = {
      name,
      startTime: performance.now(),
      metadata: metadata || {},
    };
    
    this.metrics.set(name, metric);
  }

  endTimer(name: string): number | null {
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`Performance timer "${name}" not found`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;

    const completedMetric: PerformanceMetric = {
      ...metric,
      endTime,
      duration,
    };

    this.completedMetrics.push(completedMetric);
    this.metrics.delete(name);

    // Log slow operations in development
    if (process.env.NODE_ENV === 'development' && duration > 1000) {
      console.warn(`Slow operation detected: ${name} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  measureAsync<T>(name: string, asyncFn: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    this.startTimer(name, metadata);
    
    return asyncFn()
      .then((result) => {
        this.endTimer(name);
        return result;
      })
      .catch((error) => {
        this.endTimer(name);
        throw error;
      });
  }

  measureSync<T>(name: string, syncFn: () => T, metadata?: Record<string, any>): T {
    this.startTimer(name, metadata);
    
    try {
      const result = syncFn();
      this.endTimer(name);
      return result;
    } catch (error) {
      this.endTimer(name);
      throw error;
    }
  }

  getMetrics(): PerformanceMetric[] {
    return [...this.completedMetrics];
  }

  getMetricsByName(name: string): PerformanceMetric[] {
    return this.completedMetrics.filter(metric => metric.name === name);
  }

  getAverageTime(name: string): number | null {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return null;

    const totalTime = metrics.reduce((sum, metric) => sum + (metric.duration || 0), 0);
    return totalTime / metrics.length;
  }

  clearMetrics(): void {
    this.completedMetrics = [];
    this.metrics.clear();
  }

  // Web Vitals monitoring
  observeWebVitals(): void {
    // Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'largest-contentful-paint') {
              this.recordWebVital('LCP', entry.startTime);
            }
          });
        });
        observer.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (error) {
        console.warn('Failed to observe LCP:', error);
      }

      // First Input Delay
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'first-input') {
              this.recordWebVital('FID', (entry as any).processingStart - entry.startTime);
            }
          });
        });
        observer.observe({ entryTypes: ['first-input'] });
      } catch (error) {
        console.warn('Failed to observe FID:', error);
      }

      // Cumulative Layout Shift
      try {
        let clsValue = 0;
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'layout-shift' && !(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          });
        });
        observer.observe({ entryTypes: ['layout-shift'] });

        // Record CLS on page unload
        window.addEventListener('beforeunload', () => {
          this.recordWebVital('CLS', clsValue);
        });
      } catch (error) {
        console.warn('Failed to observe CLS:', error);
      }
    }
  }

  private recordWebVital(name: string, value: number): void {
    const metric: PerformanceMetric = {
      name: `WebVital_${name}`,
      startTime: 0,
      endTime: value,
      duration: value,
      metadata: { type: 'web-vital' },
    };

    this.completedMetrics.push(metric);

    if (process.env.NODE_ENV === 'development') {
      console.log(`Web Vital ${name}:`, value);
    }
  }

  // Memory usage monitoring
  getMemoryUsage(): Record<string, number> | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit,
      };
    }
    return null;
  }

  // Network information
  getNetworkInfo(): Record<string, any> | null {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      };
    }
    return null;
  }

  // Export performance report
  generateReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      metrics: this.getMetrics(),
      memory: this.getMemoryUsage(),
      network: this.getNetworkInfo(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    return JSON.stringify(report, null, 2);
  }
}

export const performanceService = new PerformanceService();

// Initialize web vitals monitoring
performanceService.observeWebVitals();

export default performanceService;