import { notificationService } from './notificationService';
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
  
  // Mock expert profiles - in real implementation, this would come from backend
  private experts: ExpertProfile[] = [
    {
      id: 'expert_1',
      name: 'Sarah Chen',
      specialty: ['Contract Law', 'Employment Law', 'Business Agreements'],
      rating: 4.9,
      responseTime: '< 2 hours',
      availability: 'available'
    },
    {
      id: 'expert_2', 
      name: 'Michael Rodriguez',
      specialty: ['Real Estate', 'Property Law', 'Lease Agreements'],
      rating: 4.8,
      responseTime: '< 4 hours',
      availability: 'available'
    },
    {
      id: 'expert_3',
      name: 'Dr. Priya Sharma',
      specialty: ['Intellectual Property', 'Technology Law', 'Privacy'],
      rating: 4.9,
      responseTime: '< 1 hour',
      availability: 'busy'
    }
  ];

  // Create a support request
  createSupportRequest(
    documentContext: DocumentContext,
    clauseContext: ClauseContext | undefined,
    userQuestion: string,
    chatHistory: ChatMessage[],
    urgencyLevel: 'low' | 'medium' | 'high' = 'medium'
  ): SupportRequest {
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const category = this.categorizeRequest(userQuestion, clauseContext);
    const specificConcerns = this.extractConcerns(userQuestion, chatHistory);
    
    const request: SupportRequest = {
      id: requestId,
      documentId: `doc_${Date.now()}`, // In real app, this would be actual document ID
      clauseId: clauseContext?.clauseId || undefined,
      userQuestion,
      chatHistory: chatHistory.slice(-10), // Last 10 messages for context
      urgencyLevel,
      category,
      userContext: {
        documentType: documentContext.documentType,
        specificConcerns
      },
      createdAt: new Date()
    };

    this.requests.set(requestId, request);
    
    // Automatically create a ticket
    this.createTicket(request);
    
    return request;
  }

  // Create a support ticket from a request
  private createTicket(request: SupportRequest): SupportTicket {
    const ticketId = `ticket_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Find best available expert
    const expert = this.findBestExpert(request);
    const priority = this.determinePriority(request);
    const estimatedResponse = this.calculateEstimatedResponse(priority, expert);
    
    const ticket: SupportTicket = {
      id: ticketId,
      requestId: request.id,
      status: expert ? 'assigned' : 'pending',
      priority,
      estimatedResponse,
      expertId: expert?.id || undefined,
      expertName: expert?.name || undefined,
      expertSpecialty: expert?.specialty.join(', ') || undefined,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.tickets.set(ticketId, ticket);
    
    // Notify user
    this.notifyTicketCreated(ticket, expert);
    
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

  // Find the best available expert for the request
  private findBestExpert(request: SupportRequest): ExpertProfile | null {
    const availableExperts = this.experts.filter(expert => 
      expert.availability === 'available' || expert.availability === 'busy'
    );
    
    if (availableExperts.length === 0) return null;
    
    // Score experts based on specialty match and availability
    const scoredExperts = availableExperts.map(expert => {
      let score = expert.rating * 10; // Base score from rating
      
      // Bonus for specialty match
      const specialtyMatch = expert.specialty.some(specialty => 
        this.matchesSpecialty(specialty, request)
      );
      if (specialtyMatch) score += 20;
      
      // Penalty for being busy
      if (expert.availability === 'busy') score -= 10;
      
      // Bonus for fast response time
      if (expert.responseTime.includes('< 1 hour')) score += 15;
      else if (expert.responseTime.includes('< 2 hour')) score += 10;
      
      return { expert, score };
    });
    
    // Sort by score and return best match
    scoredExperts.sort((a, b) => b.score - a.score);
    return scoredExperts[0]?.expert || null;
  }

  // Check if expert specialty matches request
  private matchesSpecialty(specialty: string, request: SupportRequest): boolean {
    const specialtyLower = specialty.toLowerCase();
    const docType = request.userContext.documentType.toLowerCase();
    const category = request.category.toLowerCase();
    
    if (specialtyLower.includes('contract') && (docType.includes('contract') || docType.includes('agreement'))) return true;
    if (specialtyLower.includes('employment') && docType.includes('employment')) return true;
    if (specialtyLower.includes('real estate') && (docType.includes('lease') || docType.includes('property'))) return true;
    if (specialtyLower.includes('intellectual property') && docType.includes('ip')) return true;
    if (category.includes('legal') && specialtyLower.includes('law')) return true;
    
    return false;
  }

  // Determine ticket priority
  private determinePriority(request: SupportRequest): SupportTicket['priority'] {
    if (request.urgencyLevel === 'high') return 'urgent';
    if (request.urgencyLevel === 'medium') return 'high';
    
    // Check for high-risk indicators
    const hasHighRiskConcerns = request.userContext.specificConcerns.some(concern =>
      concern.includes('Risk') || concern.includes('Legal') || concern.includes('Penalty')
    );
    
    if (hasHighRiskConcerns) return 'high';
    
    return request.urgencyLevel === 'low' ? 'low' : 'medium';
  }

  // Calculate estimated response time
  private calculateEstimatedResponse(
    priority: SupportTicket['priority'], 
    expert: ExpertProfile | null
  ): string {
    if (!expert) return '24-48 hours (pending expert assignment)';
    
    const baseTime = expert.responseTime;
    
    switch (priority) {
      case 'urgent':
        return '< 30 minutes';
      case 'high':
        return '< 1 hour';
      case 'medium':
        return baseTime;
      case 'low':
        return '4-8 hours';
      default:
        return baseTime;
    }
  }

  // Notify user about ticket creation
  private notifyTicketCreated(ticket: SupportTicket, expert: ExpertProfile | null): void {
    if (expert) {
      notificationService.success(
        `Support request submitted! ${expert.name} (${expert.specialty[0]} specialist) will respond within ${ticket.estimatedResponse}.`
      );
    } else {
      notificationService.info(
        `Support request submitted! We're finding the best expert for your question. Estimated response: ${ticket.estimatedResponse}.`
      );
    }
  }

  // Get ticket status
  getTicketStatus(ticketId: string): SupportTicket | null {
    return this.tickets.get(ticketId) || null;
  }

  // Get all tickets for user (in real app, would filter by user ID)
  getUserTickets(): SupportTicket[] {
    return Array.from(this.tickets.values()).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime()
    );
  }

  // Get available experts
  getAvailableExperts(): ExpertProfile[] {
    return this.experts.filter(expert => expert.availability !== 'offline');
  }

  // Simulate expert response (in real app, this would be handled by backend)
  simulateExpertResponse(ticketId: string): void {
    const ticket = this.tickets.get(ticketId);
    if (!ticket) return;
    
    // Simulate response after estimated time
    setTimeout(() => {
      ticket.status = 'resolved';
      ticket.updatedAt = new Date();
      ticket.resolution = {
        summary: 'Your question has been reviewed by our legal expert.',
        recommendations: [
          'Consider consulting with a local attorney for jurisdiction-specific advice',
          'Review the clause with the other party before signing',
          'Keep documentation of all communications regarding this agreement'
        ],
        followUpRequired: false
      };
      
      notificationService.success(
        `Expert response received for your support request! Check your ticket for detailed recommendations.`
      );
    }, 5000); // 5 seconds for demo purposes
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