interface ErrorLog {
  timestamp: string;
  level: 'error' | 'warning' | 'info';
  message: string;
  stack?: string;
  context?: Record<string, any>;
  userAgent?: string;
  url?: string;
}

class ErrorService {
  private logs: ErrorLog[] = [];
  private maxLogs = 100;

  private createLog(
    level: ErrorLog['level'],
    message: string,
    error?: Error,
    context?: Record<string, any>
  ): ErrorLog {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...(error?.stack && { stack: error.stack }),
      ...(context && { context }),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
  }

  logError(message: string, error?: Error, context?: Record<string, any>) {
    const log = this.createLog('error', message, error, context);
    this.logs.push(log);
    
    // Keep only the most recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`[ErrorService] ${message}`, error, context);
    }

    // In production, you might want to send this to a logging service
    this.sendToLoggingService(log);
  }

  logWarning(message: string, context?: Record<string, any>) {
    const log = this.createLog('warning', message, undefined, context);
    this.logs.push(log);
    
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    if (process.env.NODE_ENV === 'development') {
      console.warn(`[ErrorService] ${message}`, context);
    }
  }

  logInfo(message: string, context?: Record<string, any>) {
    const log = this.createLog('info', message, undefined, context);
    this.logs.push(log);
    
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    if (process.env.NODE_ENV === 'development') {
      console.info(`[ErrorService] ${message}`, context);
    }
  }

  private async sendToLoggingService(log: ErrorLog) {
    // Only send errors in production
    if (process.env.NODE_ENV !== 'production') {
      return;
    }

    try {
      // This would be replaced with your actual logging service endpoint
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(log),
      });
    } catch (error) {
      // Silently fail - don't create infinite loops
      console.error('Failed to send log to service:', error);
    }
  }

  getLogs(): ErrorLog[] {
    return [...this.logs];
  }

  getErrorLogs(): ErrorLog[] {
    return this.logs.filter(log => log.level === 'error');
  }

  clearLogs() {
    this.logs = [];
  }

  // Export logs for debugging
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  // Handle unhandled errors
  setupGlobalErrorHandling() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError(
        'Unhandled Promise Rejection',
        new Error(event.reason),
        { reason: event.reason }
      );
      // Prevent the default browser behavior that logs to console
      event.preventDefault();
    });

    // Handle global errors
    window.addEventListener('error', (event) => {
      this.logError(
        'Global Error',
        event.error || new Error(event.message),
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        }
      );
      // Prevent the default browser behavior that logs to console
      event.preventDefault();
    });

    // Override console methods in production to prevent unwanted logs
    if (process.env.NODE_ENV === 'production') {
      // Store original console methods for potential restoration
      
      console.error = (...args: any[]) => {
        this.logError('Console Error', new Error(args.join(' ')));
        // Only log to console in development
      };
      
      console.warn = (...args: any[]) => {
        this.logWarning('Console Warning', { message: args.join(' ') });
        // Only log to console in development
      };
    }
  }
}

export const errorService = new ErrorService();

// Setup global error handling
errorService.setupGlobalErrorHandling();

export default errorService;