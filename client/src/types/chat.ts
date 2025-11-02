export interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  clauseReference?: string | undefined;
  examples?: string[] | undefined;
  confidence?: number | undefined;
  // Enhanced experience level fields
  experienceLevel?: string | undefined;
  termsExplained?: string[] | undefined;
  complexityScore?: number | undefined;
}

export interface ClauseContext {
  clauseId: string;
  text: string;
  riskLevel: 'RED' | 'YELLOW' | 'GREEN';
  explanation: string;
  implications: string[];
  recommendations: string[];
  riskScore?: number;
  confidencePercentage?: number;
  riskCategories?: Record<string, number>;
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

// Human-in-the-Loop Confidence Types
export interface ConfidenceBreakdown {
  overall_confidence: number;
  clause_confidences: Record<string, number>;
  section_confidences: Record<string, number>;
  component_weights: Record<string, number>;
  factors_affecting_confidence: string[];
  improvement_suggestions: string[];
}

export interface ClarificationResponse {
  success: boolean;
  response: string;
  conversation_id: string;
  confidence_score: number;
  response_quality: string;
  processing_time: number;
  fallback?: boolean;
  service_used?: string;
  error_type?: string;
  timestamp?: string;
  experience_level?: string;
  terms_explained?: string[];
  complexity_score?: number;
  // Human-in-the-loop confidence fields
  overall_confidence?: number;
  should_route_to_expert?: boolean;
  confidence_breakdown?: ConfidenceBreakdown;
}

export interface ExpertReviewConsent {
  documentId: string;
  userEmail: string;
  consentGiven: boolean;
  timestamp: Date;
  estimatedReviewTime: string;
}