
import type { AnalysisResult, FileInfo, Classification } from '../App';

export interface EmailNotificationRequest {
  user_email: string;
  analysis_id: string;
  include_pdf: boolean;
  email_template: 'standard' | 'detailed' | 'summary';
  custom_message?: string;
  priority: 'low' | 'normal' | 'high';
}

export interface EmailNotificationResponse {
  success: boolean;
  message_id?: string;
  delivery_status: string;
  error_message?: string;
  timestamp: string;
}

export interface EmailRateLimitInfo {
  user_id: string;
  emails_sent_today: number;
  emails_sent_this_hour: number;
  daily_limit: number;
  hourly_limit: number;
  next_reset_time: string;
  is_rate_limited: boolean;
}

export interface SendEmailData {
  analysis: AnalysisResult;
  file_info?: FileInfo;
  classification?: Classification;
}

class EmailService {
  async sendAnalysisEmail(
    emailRequest: EmailNotificationRequest,
    analysisData: SendEmailData
  ): Promise<EmailNotificationResponse> {
    try {
      const response = await fetch('/api/email/send-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification: emailRequest,
          analysis_data: analysisData
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Email send error:', error);
      return {
        success: false,
        delivery_status: 'failed',
        error_message: error instanceof Error ? error.message : 'Failed to send email',
        timestamp: new Date().toISOString()
      };
    }
  }

  async getRateLimitInfo(userId: string): Promise<EmailRateLimitInfo | null> {
    try {
      const response = await fetch(`/api/email/rate-limit/${userId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success ? result : null;
    } catch (error) {
      console.error('Rate limit check error:', error);
      return null;
    }
  }

  async testEmailService(): Promise<{ success: boolean; message: string; email_service_available: boolean }> {
    try {
      const response = await fetch('/api/email/test');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Email service test error:', error);
      return {
        success: false,
        message: 'Failed to test email service',
        email_service_available: false
      };
    }
  }

  async sendTestEmail(email: string, subject?: string): Promise<EmailNotificationResponse> {
    try {
      const response = await fetch('/api/email/send-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          subject: subject || 'LegalSaathi Test Email'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Test email error:', error);
      return {
        success: false,
        delivery_status: 'failed',
        error_message: error instanceof Error ? error.message : 'Failed to send test email',
        timestamp: new Date().toISOString()
      };
    }
  }

  formatRateLimitMessage(rateLimitInfo: EmailRateLimitInfo): string {
    if (!rateLimitInfo.is_rate_limited) {
      return `You can send ${rateLimitInfo.hourly_limit - rateLimitInfo.emails_sent_this_hour} more emails this hour.`;
    }

    const resetTime = new Date(rateLimitInfo.next_reset_time);
    const now = new Date();
    const minutesUntilReset = Math.ceil((resetTime.getTime() - now.getTime()) / (1000 * 60));

    if (rateLimitInfo.emails_sent_this_hour >= rateLimitInfo.hourly_limit) {
      return `Hourly limit reached (${rateLimitInfo.hourly_limit} emails/hour). Try again in ${minutesUntilReset} minutes.`;
    }

    if (rateLimitInfo.emails_sent_today >= rateLimitInfo.daily_limit) {
      const hoursUntilReset = Math.ceil(minutesUntilReset / 60);
      return `Daily limit reached (${rateLimitInfo.daily_limit} emails/day). Try again in ${hoursUntilReset} hours.`;
    }

    return 'Rate limit exceeded. Please try again later.';
  }

  validateEmailAddress(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  generateAnalysisId(): string {
    return `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const emailService = new EmailService();
export default emailService;