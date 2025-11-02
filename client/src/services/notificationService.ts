type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface NotificationOptions {
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    handler: () => void;
  };
}

class NotificationService {
  private listeners: Array<(message: string, type: NotificationType, options?: NotificationOptions) => void> = [];

  subscribe(listener: (message: string, type: NotificationType, options?: NotificationOptions) => void) {
    this.listeners.push(listener);
    
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notify(message: string, type: NotificationType, options?: NotificationOptions) {
    this.listeners.forEach(listener => listener(message, type, options));
  }

  success(message: string, options?: NotificationOptions) {
    this.notify(message, 'success', options);
  }

  error(message: string, options?: NotificationOptions) {
    this.notify(message, 'error', { duration: 8000, ...options });
  }

  warning(message: string, options?: NotificationOptions) {
    this.notify(message, 'warning', { duration: 6000, ...options });
  }

  info(message: string, options?: NotificationOptions) {
    this.notify(message, 'info', options);
  }

  // Convenience methods for common scenarios
  copySuccess() {
    this.success('Results copied to clipboard');
  }

  copyError() {
    this.error('Failed to copy results to clipboard');
  }

  exportSuccess(format: string) {
    this.success(`${format.toUpperCase()} export completed successfully`);
  }

  exportError(format: string, fallback?: () => void) {
    const options: NotificationOptions = { duration: 8000 };
    if (fallback) {
      options.action = {
        label: 'Try Text Export',
        handler: fallback
      };
    }
    this.error(`${format.toUpperCase()} export failed`, options);
  }

  translationSuccess() {
    this.success('Translation completed');
  }

  translationError() {
    this.error('Translation service unavailable. Please try again later.');
  }

  summarizationSuccess() {
    this.success('Summary generated successfully');
  }

  summarizationError() {
    this.error('Summarization service unavailable. Please try again later.');
  }

  aiServiceError() {
    this.error('AI service temporarily unavailable. Please try again in a few moments.');
  }

  networkError() {
    this.error('Network connection issue. Please check your internet connection and try again.');
  }

  validationError(field: string) {
    this.warning(`Please check the ${field} field and try again.`);
  }

  featureUnavailable(feature: string) {
    this.warning(`${feature} is temporarily unavailable. We're working to restore this feature.`);
  }
}

export const notificationService = new NotificationService();
export default notificationService;