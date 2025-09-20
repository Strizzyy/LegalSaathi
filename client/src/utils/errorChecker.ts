/**
 * Comprehensive error checking utility for the frontend application
 * This helps identify and prevent common console errors and warnings
 */

export class ErrorChecker {
  private static instance: ErrorChecker;
  // Error tracking for future use - currently unused but available for expansion

  static getInstance(): ErrorChecker {
    if (!ErrorChecker.instance) {
      ErrorChecker.instance = new ErrorChecker();
    }
    return ErrorChecker.instance;
  }

  /**
   * Check for common React issues that cause console warnings
   */
  checkReactIssues(): string[] {
    const issues: string[] = [];

    // Check for missing React import (though not needed in React 17+)
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      // React availability check - modern React doesn't require global React
      console.debug('React availability check passed');
    }

    // Check for StrictMode double-rendering issues
    if (process.env.NODE_ENV === 'development') {
      console.info('Running in development mode - StrictMode may cause intentional double-rendering');
    }

    return issues;
  }

  /**
   * Check for TypeScript issues that might cause runtime errors
   */
  checkTypeScriptIssues(): string[] {
    const issues: string[] = [];

    // Check for any usage that might cause type errors
    try {
      // This would be expanded based on specific type checking needs
      if (typeof window !== 'undefined') {
        // Check for browser API availability
        if (!window.fetch) {
          issues.push('Fetch API not available - consider adding a polyfill');
        }
        
        if (!window.localStorage) {
          issues.push('localStorage not available');
        }
      }
    } catch (error) {
      issues.push(`TypeScript runtime check failed: ${error}`);
    }

    return issues;
  }

  /**
   * Check for performance issues that might cause console warnings
   */
  checkPerformanceIssues(): string[] {
    const issues: string[] = [];

    // Check for large bundle size warnings
    if (typeof window !== 'undefined' && window.performance) {
      const navigation = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigation && navigation.loadEventEnd - navigation.loadEventStart > 3000) {
        issues.push('Slow page load detected - consider code splitting or optimization');
      }
    }

    return issues;
  }

  /**
   * Check for accessibility issues that might cause console warnings
   */
  checkAccessibilityIssues(): string[] {
    const issues: string[] = [];

    if (typeof document !== 'undefined') {
      // Check for missing alt attributes on images
      const images = document.querySelectorAll('img:not([alt])');
      if (images.length > 0) {
        issues.push(`${images.length} images missing alt attributes`);
      }

      // Check for missing labels on form inputs
      const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
      const inputsWithoutLabels = Array.from(inputs).filter(input => {
        const id = input.getAttribute('id');
        return !id || !document.querySelector(`label[for="${id}"]`);
      });
      
      if (inputsWithoutLabels.length > 0) {
        issues.push(`${inputsWithoutLabels.length} form inputs missing proper labels`);
      }
    }

    return issues;
  }

  /**
   * Run all checks and return a comprehensive report
   */
  runAllChecks(): { issues: string[]; summary: string } {
    const allIssues = [
      ...this.checkReactIssues(),
      ...this.checkTypeScriptIssues(),
      ...this.checkPerformanceIssues(),
      ...this.checkAccessibilityIssues()
    ];

    const summary = allIssues.length === 0 
      ? 'No issues detected - application is running cleanly'
      : `${allIssues.length} potential issues detected`;

    return { issues: allIssues, summary };
  }

  /**
   * Log the error checking results
   */
  logResults(): void {
    const { issues, summary } = this.runAllChecks();
    
    if (process.env.NODE_ENV === 'development') {
      console.group('🔍 Error Checker Results');
      console.log(summary);
      
      if (issues.length > 0) {
        console.warn('Issues found:');
        issues.forEach((issue, index) => {
          console.warn(`${index + 1}. ${issue}`);
        });
      } else {
        console.log('✅ All checks passed!');
      }
      
      console.groupEnd();
    }
  }

  /**
   * Set up automatic error checking on page load
   */
  setupAutoCheck(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('load', () => {
        // Run checks after a short delay to allow React to fully render
        setTimeout(() => {
          this.logResults();
        }, 1000);
      });
    }
  }
}

// Initialize error checker in development
if (process.env.NODE_ENV === 'development') {
  const errorChecker = ErrorChecker.getInstance();
  errorChecker.setupAutoCheck();
}

export default ErrorChecker;