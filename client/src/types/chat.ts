export interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  clauseReference?: string | undefined;
  examples?: string[] | undefined;
  confidence?: number | undefined;
}

export interface ClauseContext {
  clauseId: string;
  text: string;
  riskLevel: 'RED' | 'YELLOW' | 'GREEN';
  explanation: string;
  implications: string[];
  recommendations: string[];
}

export interface DocumentContext {
  documentType: string;
  overallRisk: string;
  summary: string;
  totalClauses: number;
}

export interface ChatSession {
  id: string;
  clauseContext?: ClauseContext | undefined;
  documentContext: DocumentContext;
  messages: ChatMessage[];
  createdAt: Date;
  lastActivity: Date;
}

export interface SupportRequest {
  id: string;
  documentId: string;
  clauseId?: string | undefined;
  userQuestion: string;
  chatHistory: ChatMessage[];
  urgencyLevel: 'low' | 'medium' | 'high';
  category: 'legal_clarification' | 'risk_assessment' | 'contract_terms' | 'general_inquiry';
  userContext: {
    documentType: string;
    specificConcerns: string[];
  };
  createdAt: Date;
}

export interface SupportTicket {
  id: string;
  requestId: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'resolved' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimatedResponse: string;
  expertId?: string | undefined;
  expertName?: string | undefined;
  expertSpecialty?: string | undefined;
  createdAt: Date;
  updatedAt: Date;
  resolution?: {
    summary: string;
    recommendations: string[];
    followUpRequired: boolean;
  } | undefined;
}

export interface ExpertProfile {
  id: string;
  name: string;
  specialty: string[];
  rating: number;
  responseTime: string;
  availability: 'available' | 'busy' | 'offline';
}