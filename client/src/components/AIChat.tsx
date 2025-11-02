import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  MessageSquare,
  AlertCircle,
  CheckCircle,
  Lightbulb,
  Users
} from 'lucide-react';
import { Modal } from './Modal';
import { chatService } from '../services/chatService';
import { supportService } from '../services/supportService';
import { notificationService } from '../services/notificationService';
import type { 
  ChatMessage, 
  ClauseContext, 
  DocumentContext,
  SupportTicket 
} from '../types/chat';

interface AIChatProps {
  isOpen: boolean;
  onClose: () => void;
  documentContext: DocumentContext;
  clauseContext?: ClauseContext | undefined;
}

// Helper function to safely render HTML content
const renderMessageContent = (content: string) => {
  return { __html: content };
};

export function AIChat({ isOpen, onClose, documentContext, clauseContext }: AIChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showExamples, setShowExamples] = useState(true);
  const [showHumanSupport, setShowHumanSupport] = useState(false);
  const [supportTicket, setSupportTicket] = useState<SupportTicket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize chat session when component opens
  useEffect(() => {
    if (isOpen) {
      const session = chatService.createSession(documentContext, clauseContext);
      setMessages(session.messages);
      setShowExamples(true);
      setShowHumanSupport(false);
      setSupportTicket(null);
    } else {
      chatService.clearSession();
    }
  }, [isOpen, documentContext, clauseContext]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check if human support should be offered
  useEffect(() => {
    if (messages.length > 0) {
      const shouldOffer = supportService.shouldOfferHumanSupport(messages);
      setShowHumanSupport(shouldOffer);
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    setInputValue('');
    setIsLoading(true);
    setShowExamples(false);

    try {
      const aiMessage = await chatService.sendMessage(inputValue.trim());
      if (aiMessage) {
        const session = chatService.getCurrentSession();
        if (session) {
          setMessages([...session.messages]);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      notificationService.error('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setInputValue(example);
    setShowExamples(false);
    inputRef.current?.focus();
  };

  const handleContactHuman = async () => {
    try {
      await supportService.createSupportRequest(
        documentContext,
        clauseContext,
        inputValue || "I need help understanding this document",
        messages,
        'medium'
      );
      
      const tickets = await supportService.getUserTickets();
      const newTicket = tickets.length > 0 ? tickets[0] : null; // Most recent ticket
      
      setSupportTicket(newTicket);
      setShowHumanSupport(false);
      
      // Poll for ticket updates instead of simulation
      if (newTicket) {
        // Poll every 30 seconds for updates
        const pollInterval = setInterval(async () => {
          await supportService.pollTicketUpdates(newTicket.id);
          const updatedTicket = await supportService.getTicketStatus(newTicket.id);
          if (updatedTicket && updatedTicket.status === 'resolved') {
            setSupportTicket(updatedTicket);
            clearInterval(pollInterval);
          }
        }, 30000);
        
        // Clear interval after 10 minutes
        setTimeout(() => clearInterval(pollInterval), 600000);
      }
    } catch (error) {
      console.error('Support request error:', error);
      notificationService.error('Failed to create support request. Please try again.');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    
    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      >
        <div className={`flex items-start space-x-3 max-w-[85%] ${
          isUser ? 'flex-row-reverse space-x-reverse' : ''
        }`}>
          {/* Avatar */}
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser 
              ? 'bg-cyan-500' 
              : isSystem 
                ? 'bg-slate-600'
                : 'bg-gradient-to-r from-purple-500 to-pink-500'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : isSystem ? (
              <AlertCircle className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
          
          {/* Message Content */}
          <div className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-cyan-500 text-white'
              : isSystem
                ? 'bg-slate-600 text-slate-100'
                : 'bg-slate-700 text-slate-100'
          }`}>
            <div 
              className="text-sm whitespace-pre-wrap leading-relaxed"
              dangerouslySetInnerHTML={renderMessageContent(message.content)}
            />
            
            {/* Confidence indicator for AI messages */}
            {!isUser && !isSystem && message.confidence && (
              <div className="flex items-center mt-2 pt-2 border-t border-slate-600/50">
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <CheckCircle className="w-3 h-3" />
                  <span>Confidence: {message.confidence}%</span>
                </div>
              </div>
            )}
            
            {/* Experience level adaptation info for AI messages */}
            {!isUser && !isSystem && (message.experienceLevel || message.termsExplained || message.complexityScore !== undefined) && (
              <div className="mt-2 pt-2 border-t border-slate-600/50">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  {message.experienceLevel && (
                    <div className="flex items-center space-x-1 text-slate-400">
                      <Users className="w-3 h-3" />
                      <span>Adapted for: <span className="text-cyan-400 capitalize">{message.experienceLevel}</span></span>
                    </div>
                  )}
                  {message.termsExplained && message.termsExplained.length > 0 && (
                    <div className="flex items-center space-x-1 text-slate-400">
                      <Lightbulb className="w-3 h-3" />
                      <span>Explained {message.termsExplained.length} legal term{message.termsExplained.length > 1 ? 's' : ''}</span>
                    </div>
                  )}
                  {message.complexityScore !== undefined && (
                    <div className="flex items-center space-x-1 text-slate-400">
                      <span>Complexity: {message.complexityScore.toFixed(1)}/5</span>
                    </div>
                  )}
                </div>
                {message.termsExplained && message.termsExplained.length > 0 && (
                  <div className="mt-1 text-xs text-slate-500">
                    Terms: {message.termsExplained.join(', ')}
                  </div>
                )}
              </div>
            )}
            
            {/* Clause reference */}
            {message.clauseReference && (
              <div className="text-xs text-slate-400 mt-1">
                📋 Clause {message.clauseReference}
              </div>
            )}
            
            {/* Timestamp */}
            <div className="text-xs opacity-70 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="AI Legal Assistant" maxWidth="xl">
      <div className="flex flex-col h-[600px]">
        {/* Context Header */}
        {clauseContext && (
          <div className="bg-slate-800 rounded-lg p-3 mb-4 border border-slate-600">
            <div className="flex items-center space-x-2 text-sm">
              <MessageSquare className="w-4 h-4 text-cyan-400" />
              <span className="text-slate-300">
                Discussing: <strong>Clause {clauseContext.clauseId}</strong>
              </span>
              <span className={`px-2 py-1 rounded text-xs ${
                clauseContext.riskLevel === 'RED' ? 'bg-red-500/20 text-red-400' :
                clauseContext.riskLevel === 'YELLOW' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-green-500/20 text-green-400'
              }`}>
                {clauseContext.riskLevel} Risk
              </span>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
          {messages.map(renderMessage)}
          
          {/* Loading indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-700 px-4 py-3 rounded-2xl">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                    <span className="text-sm text-slate-400">AI is analyzing your question...</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
          
          {/* Example suggestions */}
          <AnimatePresence>
            {showExamples && messages.length > 0 && messages[messages.length - 1]?.examples && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex justify-start"
              >
                <div className="max-w-[85%]">
                  <div className="flex items-center space-x-2 mb-2 text-xs text-slate-400">
                    <Lightbulb className="w-3 h-3" />
                    <span>Try asking:</span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {messages[messages.length - 1].examples?.map((example, index) => (
                      <button
                        key={index}
                        onClick={() => handleExampleClick(example)}
                        className="text-left px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-300 transition-colors"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <div ref={messagesEndRef} />
        </div>

        {/* Human Support Offer */}
        <AnimatePresence>
          {showHumanSupport && !supportTicket && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-4"
            >
              <div className="flex items-start space-x-3">
                <Users className="w-5 h-5 text-blue-400 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-blue-400 mb-1">
                    Need Human Expert Help?
                  </h4>
                  <p className="text-xs text-slate-300 mb-3">
                    Our legal experts can provide personalized guidance for complex questions.
                  </p>
                  <button
                    onClick={handleContactHuman}
                    className="px-3 py-1.5 bg-blue-500 hover:bg-blue-400 text-white text-xs rounded-lg transition-colors"
                  >
                    Contact Human Expert
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Support Ticket Status */}
        <AnimatePresence>
          {supportTicket && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 mb-4"
            >
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-green-400 mb-1">
                    Expert Support Request Created
                  </h4>
                  <div className="text-xs text-slate-300 space-y-1">
                    <p><strong>Expert:</strong> {supportTicket.expertName || 'Being assigned...'}</p>
                    <p><strong>Estimated Response:</strong> {supportTicket.estimatedResponse}</p>
                    <p><strong>Status:</strong> {supportTicket.status.replace('_', ' ').toUpperCase()}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input Area */}
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <label htmlFor="ai-chat-input" className="sr-only">
              {clauseContext 
                ? `Ask about Clause ${clauseContext.clauseId}` 
                : "Ask about clauses, risks, or legal implications"
              }
            </label>
            <textarea
              id="ai-chat-input"
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={clauseContext 
                ? `Ask about Clause ${clauseContext.clauseId}...` 
                : "Ask about clauses, risks, or legal implications..."
              }
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none"
              rows={2}
              disabled={isLoading}
              aria-label={clauseContext 
                ? `Ask about Clause ${clauseContext.clauseId}` 
                : "Ask about clauses, risks, or legal implications"
              }
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </Modal>
  );
}