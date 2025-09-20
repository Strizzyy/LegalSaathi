import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Clock, 
  Star, 
  MessageCircle, 
  CheckCircle,
  User,
  Send,
  FileText
} from 'lucide-react';
import { Modal } from './Modal';
import { supportService } from '../services/supportService';
import { notificationService } from '../services/notificationService';
import type { 
  SupportTicket, 
  DocumentContext, 
  ClauseContext,
  ChatMessage 
} from '../types/chat';

interface HumanSupportProps {
  isOpen: boolean;
  onClose: () => void;
  documentContext: DocumentContext;
  clauseContext?: ClauseContext | undefined;
  chatHistory?: ChatMessage[] | undefined;
  initialQuestion?: string | undefined;
}

export function HumanSupport({ 
  isOpen, 
  onClose, 
  documentContext, 
  clauseContext, 
  chatHistory = [],
  initialQuestion = ''
}: HumanSupportProps) {
  const [currentStep, setCurrentStep] = useState<'form' | 'experts' | 'ticket'>('form');
  const [question, setQuestion] = useState(initialQuestion);
  const [urgency, setUrgency] = useState<'low' | 'medium' | 'high'>('medium');
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);

  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const concernOptions = [
    'Unclear language or terms',
    'Risk assessment concerns',
    'Contract negotiation advice',
    'Legal implications',
    'Financial implications',
    'Timeline or deadline issues',
    'Penalty or termination clauses',
    'Compliance requirements',
    'Industry-specific guidance'
  ];

  useEffect(() => {
    if (isOpen) {
      setCurrentStep('form');
      setQuestion(initialQuestion);
      setUrgency('medium');
      setSelectedConcerns([]);

      setTicket(null);

    }
  }, [isOpen, initialQuestion]);

  const handleConcernToggle = (concern: string) => {
    setSelectedConcerns(prev => 
      prev.includes(concern) 
        ? prev.filter(c => c !== concern)
        : [...prev, concern]
    );
  };

  const handleSubmitRequest = async () => {
    if (!question.trim()) {
      notificationService.error('Please enter your question');
      return;
    }

    setIsSubmitting(true);
    
    try {
      supportService.createSupportRequest(
        documentContext,
        clauseContext,
        question,
        chatHistory,
        urgency
      );
      
      const tickets = supportService.getUserTickets();
      const newTicket = tickets[0]; // Most recent ticket
      
      setTicket(newTicket);
      setCurrentStep('ticket');
      
      // Simulate expert response for demo
      if (newTicket) {
        supportService.simulateExpertResponse(newTicket.id);
      }
    } catch (error) {
      console.error('Support request error:', error);
      notificationService.error('Failed to create support request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderForm = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          Get Expert Legal Guidance
        </h3>
        <p className="text-slate-400 text-sm mb-6">
          Our legal experts will provide personalized advice for your specific situation.
        </p>
      </div>

      {/* Context Display */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
        <h4 className="font-medium text-white mb-2 flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          Document Context
        </h4>
        <div className="text-sm text-slate-300 space-y-1">
          <p><strong>Type:</strong> {documentContext.documentType}</p>
          <p><strong>Risk Level:</strong> {documentContext.overallRisk}</p>
          {clauseContext && (
            <p><strong>Specific Clause:</strong> {clauseContext.clauseId} ({clauseContext.riskLevel} risk)</p>
          )}
        </div>
      </div>

      {/* Question Input */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          What specific question do you have?
        </label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Describe your question or concern in detail..."
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none"
          rows={4}
        />
      </div>

      {/* Urgency Level */}
      <div>
        <label className="block text-sm font-medium text-white mb-3">
          How urgent is this question?
        </label>
        <div className="grid grid-cols-3 gap-3">
          {(['low', 'medium', 'high'] as const).map((level) => (
            <button
              key={level}
              onClick={() => setUrgency(level)}
              className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                urgency === level
                  ? 'border-cyan-500 bg-cyan-500/20 text-cyan-400'
                  : 'border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500'
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <Clock className="w-4 h-4" />
                <span className="capitalize">{level}</span>
              </div>
              <div className="text-xs mt-1 opacity-75">
                {level === 'low' && '24-48 hours'}
                {level === 'medium' && '4-8 hours'}
                {level === 'high' && '< 2 hours'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Specific Concerns */}
      <div>
        <label className="block text-sm font-medium text-white mb-3">
          What are your main concerns? (Select all that apply)
        </label>
        <div className="grid grid-cols-1 gap-2">
          {concernOptions.map((concern) => (
            <button
              key={concern}
              onClick={() => handleConcernToggle(concern)}
              className={`p-3 rounded-lg border text-sm text-left transition-colors ${
                selectedConcerns.includes(concern)
                  ? 'border-cyan-500 bg-cyan-500/20 text-cyan-400'
                  : 'border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500'
              }`}
            >
              <div className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                  selectedConcerns.includes(concern)
                    ? 'border-cyan-500 bg-cyan-500'
                    : 'border-slate-500'
                }`}>
                  {selectedConcerns.includes(concern) && (
                    <CheckCircle className="w-3 h-3 text-white" />
                  )}
                </div>
                <span>{concern}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmitRequest}
          disabled={!question.trim() || isSubmitting}
          className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Creating Request...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Submit Request</span>
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderTicketStatus = () => (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">
          Support Request Created!
        </h3>
        <p className="text-slate-400">
          Your request has been submitted and assigned to an expert.
        </p>
      </div>

      {ticket && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-white mb-3 flex items-center">
                <User className="w-4 h-4 mr-2" />
                Assigned Expert
              </h4>
              <div className="space-y-2">
                <p className="text-slate-300">
                  <strong>{ticket.expertName || 'Being assigned...'}</strong>
                </p>
                {ticket.expertSpecialty && (
                  <p className="text-sm text-slate-400">
                    Specializes in: {ticket.expertSpecialty}
                  </p>
                )}
                <div className="flex items-center space-x-2 text-sm">
                  <Star className="w-4 h-4 text-yellow-400" />
                  <span className="text-slate-400">4.9/5 rating</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-white mb-3 flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                Response Timeline
              </h4>
              <div className="space-y-2">
                <p className="text-slate-300">
                  <strong>{ticket.estimatedResponse}</strong>
                </p>
                <p className="text-sm text-slate-400">
                  Priority: {ticket.priority.toUpperCase()}
                </p>
                <div className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                  ticket.status === 'assigned' ? 'bg-blue-500/20 text-blue-400' :
                  ticket.status === 'in_progress' ? 'bg-yellow-500/20 text-yellow-400' :
                  ticket.status === 'resolved' ? 'bg-green-500/20 text-green-400' :
                  'bg-slate-500/20 text-slate-400'
                }`}>
                  Status: {ticket.status.replace('_', ' ').toUpperCase()}
                </div>
              </div>
            </div>
          </div>

          {ticket.resolution && (
            <div className="mt-6 pt-6 border-t border-slate-600">
              <h4 className="font-medium text-white mb-3 flex items-center">
                <MessageCircle className="w-4 h-4 mr-2" />
                Expert Response
              </h4>
              <div className="bg-slate-700 rounded-lg p-4">
                <p className="text-slate-200 mb-4">{ticket.resolution.summary}</p>
                
                {ticket.resolution.recommendations.length > 0 && (
                  <div>
                    <h5 className="font-medium text-white mb-2">Recommendations:</h5>
                    <ul className="space-y-1">
                      {ticket.resolution.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm text-slate-300">
                          <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-center">
        <button
          onClick={onClose}
          className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
        >
          Close
        </button>
      </div>
    </div>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Human Expert Support" maxWidth="xl">
      <div className="min-h-[500px]">
        <AnimatePresence mode="wait">
          {currentStep === 'form' && (
            <motion.div
              key="form"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {renderForm()}
            </motion.div>
          )}
          
          {currentStep === 'ticket' && (
            <motion.div
              key="ticket"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {renderTicketStatus()}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Modal>
  );
}