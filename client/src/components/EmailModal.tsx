import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Mail, 
  Send, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  FileText,
  User
} from 'lucide-react';
import { cn } from '../utils';
import { emailService, type EmailNotificationRequest, type SendEmailData } from '../services/emailService';
import { notificationService } from '../services/notificationService';

interface EmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisData: SendEmailData;
  userEmail?: string;
  className?: string;
}

export const EmailModal: React.FC<EmailModalProps> = ({
  isOpen,
  onClose,
  analysisData,
  userEmail = '',
  className
}) => {
  const [email, setEmail] = useState(userEmail);
  const [customMessage, setCustomMessage] = useState('');
  const [includePdf, setIncludePdf] = useState(true);
  const [emailTemplate, setEmailTemplate] = useState<'standard' | 'detailed' | 'summary'>('standard');
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<any>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setEmail(userEmail);
      setCustomMessage('');
      setIncludePdf(true);
      setEmailTemplate('standard');
      setIsLoading(false);
      setIsSent(false);
      setError(null);
      checkRateLimit();
    }
  }, [isOpen, userEmail]);

  const checkRateLimit = async () => {
    try {
      // For now, we'll skip rate limit check if no user ID available
      // In a real implementation, you'd get this from auth context
      const userId = 'current_user'; // This should come from auth context
      const info = await emailService.getRateLimitInfo(userId);
      setRateLimitInfo(info);
    } catch (error) {
      console.warn('Could not check rate limit:', error);
    }
  };

  const handleSendEmail = async () => {
    if (!email.trim()) {
      setError('Email address is required');
      return;
    }

    if (!emailService.validateEmailAddress(email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (rateLimitInfo?.is_rate_limited) {
      setError(emailService.formatRateLimitMessage(rateLimitInfo));
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const emailRequest: EmailNotificationRequest = {
        user_email: email.trim(),
        analysis_id: emailService.generateAnalysisId(),
        include_pdf: includePdf,
        email_template: emailTemplate,
        priority: 'normal'
      };

      // Only add custom_message if it has content
      const trimmedMessage = customMessage.trim();
      if (trimmedMessage) {
        emailRequest.custom_message = trimmedMessage;
      }

      const response = await emailService.sendAnalysisEmail(emailRequest, analysisData);

      if (response.success) {
        setIsSent(true);
        notificationService.success('Analysis report sent successfully!');
        
        // Auto-close after 3 seconds
        setTimeout(() => {
          onClose();
        }, 3000);
      } else {
        setError(response.error_message || 'Failed to send email');
        notificationService.error('Failed to send email');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send email';
      setError(errorMessage);
      notificationService.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={handleClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className={cn(
            "relative w-full max-w-md bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl",
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Mail className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Send Analysis Report</h2>
                <p className="text-sm text-slate-400">Email your document analysis</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              disabled={isLoading}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Success State */}
            {isSent && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Email Sent Successfully!</h3>
                <p className="text-slate-400">
                  Your analysis report has been sent to <strong>{email}</strong>
                </p>
                <p className="text-sm text-slate-500 mt-2">This modal will close automatically...</p>
              </motion.div>
            )}

            {/* Form */}
            {!isSent && (
              <>
                {/* Email Input */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email address"
                      className="w-full pl-10 pr-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none transition-colors"
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {/* Email Template Selection */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Email Template
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: 'standard', label: 'Standard', desc: 'Professional summary' },
                      { value: 'detailed', label: 'Detailed', desc: 'Complete analysis' },
                      { value: 'summary', label: 'Summary', desc: 'Brief overview' }
                    ].map((template) => (
                      <button
                        key={template.value}
                        onClick={() => setEmailTemplate(template.value as any)}
                        disabled={isLoading}
                        className={cn(
                          "p-3 text-left border rounded-lg transition-colors disabled:opacity-50",
                          emailTemplate === template.value
                            ? "border-blue-500 bg-blue-500/20 text-blue-400"
                            : "border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500"
                        )}
                      >
                        <div className="font-medium text-sm">{template.label}</div>
                        <div className="text-xs opacity-75">{template.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* PDF Attachment Option */}
                <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-white">Include PDF Report</div>
                      <div className="text-xs text-slate-400">Attach detailed analysis as PDF</div>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includePdf}
                      onChange={(e) => setIncludePdf(e.target.checked)}
                      disabled={isLoading}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                  </label>
                </div>

                {/* Custom Message */}
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-slate-300 mb-2">
                    Personal Message (Optional)
                  </label>
                  <textarea
                    id="message"
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.target.value)}
                    placeholder="Add a personal message to include in the email..."
                    rows={3}
                    maxLength={500}
                    className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none transition-colors resize-none"
                    disabled={isLoading}
                  />
                  <div className="text-xs text-slate-500 mt-1">
                    {customMessage.length}/500 characters
                  </div>
                </div>

                {/* Rate Limit Info */}
                {rateLimitInfo && (
                  <div className="flex items-center space-x-2 text-sm text-slate-400">
                    <Clock className="w-4 h-4" />
                    <span>
                      {rateLimitInfo.is_rate_limited
                        ? emailService.formatRateLimitMessage(rateLimitInfo)
                        : `${rateLimitInfo.hourly_limit - rateLimitInfo.emails_sent_this_hour} emails remaining this hour`
                      }
                    </span>
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center space-x-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400"
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                  </motion.div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          {!isSent && (
            <div className="flex items-center justify-between p-6 border-t border-slate-700">
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSendEmail}
                disabled={isLoading || !email.trim() || (rateLimitInfo?.is_rate_limited)}
                className="inline-flex items-center px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Send Email
                  </>
                )}
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default EmailModal;