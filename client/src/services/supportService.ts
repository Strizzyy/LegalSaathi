import { notificationService } from './notificationService';
import { apiService } from './apiService';
import type { 
  SupportRequest, 
  SupportTicket, 
  ExpertProfile,
  ChatMessage,
  ClauseContext,
  DocumentContext 
} from '../types/chat';

class SupportService {
  private requests: Map<string, SupportRequest> = new Map();
  private tickets: Map<string, SupportTicket> = new Map();
  private expertsCache: ExpertProfile[] = [];
  private expertsCacheExpiry: number = 0;

  // Get available experts (static list)
  async getAvailableExperts(): Promise<ExpertProfile[]> {
    // Return static list of experts
    const staticExperts: ExpertProfile[] = [
      {
        id: 'expert_1',
        name: 'Sarah Chen',
        specialty: ['Contract Law', 'Employment Law'],
        rating: 4.9,
        responseTime: '2-4 hours',
        availability: 'available'
      },
      {
        id: 'expert_2',
        name: 'Michael Rodriguez',
        specialty: ['Real Estate Law', 'Rental Agreements'],
        rating: 4.8,
        responseTime: '1-3 hours',
        availability: 'available'
      },
      {
        id: 'expert_3',
        name: 'Dr. Priya Sharma',
        specialty: ['Corporate Law', 'Partnership Agreements'],
        rating: 4.9,
        responseTime: '4-6 hours',
        availability: 'busy'
      }
    ];

    this.expertsCache = staticExperts;
    return staticExperts.filter(expert => expert.availability === 'available');
  }

  // Create a support request (static response)
  async createSupportRequest(
    documentContext: DocumentContext,
    clauseContext: ClauseContext | undefined,
    userQuestion: string,
    chatHistory: ChatMessage[],
    urgencyLevel: 'low' | 'medium' | 'high' = 'medium'
  ): Promise<SupportRequest> {
    try {
      const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      const category = this.categorizeRequest(userQuestion, clauseContext);
      const specificConcerns = this.extractConcerns(userQuestion, chatHistory);
      
      const request: SupportRequest = {
        id: requestId,
        documentId: `doc_${Date.now()}`,
        clauseId: clauseContext?.clauseId || undefined,
        userQuestion,
        chatHistory: chatHistory.slice(-10),
        urgencyLevel,
        category,
        userContext: {
          documentType: documentContext.documentType,
          specificConcerns
        },
        createdAt: new Date()
      };

      this.requests.set(requestId, request);
      
      // Create a static support ticket
      const staticTicket = this.createStaticSupportResponse(request, documentContext, clauseContext);
      
      // Show static response
      notificationService.success(
        'Thank you for your request! A human expert will review your question and respond within 4-5 hours. You will be contacted directly with detailed legal guidance.'
      );
      
      return request;
    } catch (error) {
      console.error('Error creating support request:', error);
      throw new Error('Failed to create support request');
    }
  }

  // Static support response (no backend API call)
  private createStaticSupportResponse(
    request: SupportRequest, 
    documentContext: DocumentContext, 
    clauseContext?: ClauseContext
  ): SupportTicket {
    const ticketId = `ticket_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    
    const ticket: SupportTicket = {
      id: ticketId,
      requestId: request.id,
      status: 'assigned',
      priority: request.urgencyLevel,
      estimatedResponse: '4-5 hours',
      expertName: 'Human Expert Team',
      expertSpecialty: 'Legal Document Review',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.tickets.set(ticketId, ticket);
    return ticket;
  }

  // Categorize the support request
  private categorizeRequest(
    userQuestion: string, 
    _clauseContext?: ClauseContext
  ): SupportRequest['category'] {
    const question = userQuestion.toLowerCase();
    
    if (question.includes('risk') || question.includes('danger') || question.includes('liability')) {
      return 'risk_assessment';
    }
    
    if (question.includes('term') || question.includes('clause') || question.includes('condition')) {
      return 'contract_terms';
    }
    
    if (question.includes('legal') || question.includes('law') || question.includes('regulation')) {
      return 'legal_clarification';
    }
    
    return 'general_inquiry';
  }

  // Extract specific concerns from user question and chat history
  private extractConcerns(userQuestion: string, chatHistory: ChatMessage[]): string[] {
    const concerns: string[] = [];
    const question = userQuestion.toLowerCase();
    
    // Extract concerns from current question
    if (question.includes('confus')) concerns.push('Unclear language');
    if (question.includes('risk') || question.includes('worry')) concerns.push('Risk assessment');
    if (question.includes('negotiate') || question.includes('change')) concerns.push('Contract negotiation');
    if (question.includes('legal') || question.includes('court')) concerns.push('Legal implications');
    if (question.includes('money') || question.includes('cost') || question.includes('fee')) concerns.push('Financial implications');
    
    // Extract patterns from chat history
    const historyText = chatHistory
      .filter(msg => msg.type === 'user')
      .map(msg => msg.content.toLowerCase())
      .join(' ');
    
    if (historyText.includes('deadline') || historyText.includes('time')) concerns.push('Timeline concerns');
    if (historyText.includes('penalty') || historyText.includes('fine')) concerns.push('Penalty clauses');
    if (historyText.includes('terminate') || historyText.includes('cancel')) concerns.push('Termination conditions');
    
    return [...new Set(concerns)]; // Remove duplicates
  }



  // Get ticket status (static - returns local ticket)
  async getTicketStatus(ticketId: string): Promise<SupportTicket | null> {
    return this.tickets.get(ticketId) || null;
  }

  // Get all tickets for user (static - returns local tickets only)
  async getUserTickets(): Promise<SupportTicket[]> {
    // Return local tickets sorted by creation date
    return Array.from(this.tickets.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  // Poll for ticket updates (static - no actual polling)
  async pollTicketUpdates(ticketId: string): Promise<void> {
    // Static implementation - no actual polling needed
    // The ticket status remains as created with the static message
    return;
  }

  // Check if user should be offered human support
  shouldOfferHumanSupport(chatHistory: ChatMessage[]): boolean {
    if (chatHistory.length < 3) return false;
    
    const recentMessages = chatHistory.slice(-5);
    const userMessages = recentMessages.filter(msg => msg.type === 'user');
    
    // Offer support if user seems confused or asks complex questions
    const confusionIndicators = [
      'still don\'t understand',
      'confused',
      'not clear',
      'can you explain again',
      'i need help',
      'this is complicated'
    ];
    
    const hasConfusion = userMessages.some(msg =>
      confusionIndicators.some(indicator => 
        msg.content.toLowerCase().includes(indicator)
      )
    );
    
    // Offer support if AI confidence is consistently low
    const aiMessages = recentMessages.filter(msg => msg.type === 'ai');
    const lowConfidenceCount = aiMessages.filter(msg => 
      msg.confidence && msg.confidence < 75
    ).length;
    
    return hasConfusion || lowConfidenceCount >= 2;
  }
}

export const supportService = new SupportService();
export default supportService;