import { apiService } from './apiService';
import { experienceLevelService } from './experienceLevelService';
import type { 
  ChatMessage, 
  ChatSession, 
  ClauseContext, 
  DocumentContext
} from '../types/chat';

class ChatService {
  private sessions: Map<string, ChatSession> = new Map();
  private currentSessionId: string | null = null;

  // Create a new chat session with context
  // Helper function to process text and replace ** with proper styling
  private processText(text: string): string {
    // Replace **text** with proper bold styling
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  createSession(documentContext: DocumentContext, clauseContext?: ClauseContext): ChatSession {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const initialMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'ai',
      content: this.processText(this.generateContextualGreeting(documentContext, clauseContext)),
      timestamp: new Date(),
      clauseReference: clauseContext?.clauseId || undefined,
      examples: this.generateInitialExamples(clauseContext).map(ex => this.processText(ex))
    };

    const session: ChatSession = {
      id: sessionId,
      clauseContext: clauseContext || undefined,
      documentContext,
      messages: [initialMessage],
      createdAt: new Date(),
      lastActivity: new Date()
    };

    this.sessions.set(sessionId, session);
    this.currentSessionId = sessionId;
    
    return session;
  }

  // Get current active session
  getCurrentSession(): ChatSession | null {
    if (!this.currentSessionId) return null;
    return this.sessions.get(this.currentSessionId) || null;
  }

  // Send a message in the current session
  async sendMessage(content: string): Promise<ChatMessage | null> {
    const session = this.getCurrentSession();
    if (!session) return null;

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
      clauseReference: session.clauseContext?.clauseId || undefined
    };

    session.messages.push(userMessage);
    session.lastActivity = new Date();

    try {
      // Prepare enhanced context for AI
      const enhancedContext = {
        document: session.documentContext,
        clause: session.clauseContext,
        conversationHistory: session.messages.slice(-5), // Last 5 messages for context
        userQuestion: content
      };

      // Get user experience level from service
      const experienceLevel = experienceLevelService.getLevelForAPI();
      
      const result = await apiService.askClarification(content, enhancedContext, experienceLevel);
      
      if (result.success && result.response) {
        const aiMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          type: 'ai',
          content: this.processText(this.enhanceAIResponse(result.response, session.clauseContext)),
          timestamp: new Date(),
          clauseReference: session.clauseContext?.clauseId || undefined,
          examples: this.generateContextualExamples(content, session.clauseContext),
          confidence: this.calculateResponseConfidence(result.response)
        };

        session.messages.push(aiMessage);
        session.lastActivity = new Date();
        
        return aiMessage;
      } else {
        throw new Error(result.error || 'AI service unavailable');
      }
    } catch (error) {
      console.error('Chat service error:', error);
      
      // Add fallback message
      const fallbackMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        type: 'system',
        content: "I'm having trouble processing your question right now. Would you like to connect with a human expert for immediate assistance?",
        timestamp: new Date(),
        clauseReference: session.clauseContext?.clauseId || undefined
      };

      session.messages.push(fallbackMessage);
      return fallbackMessage;
    }
  }

  // Generate contextual greeting based on document and clause context
  private generateContextualGreeting(documentContext: DocumentContext, clauseContext?: ClauseContext): string {
    const baseGreeting = `Hello! I'm your AI legal assistant, here to help you understand your ${documentContext.documentType}.`;
    
    if (clauseContext) {
      return `${baseGreeting} I see you're looking at Clause ${clauseContext.clauseId}, which has a ${clauseContext.riskLevel.toLowerCase()} risk level. What specific questions do you have about this clause?`;
    }
    
    return `${baseGreeting} Your document has an overall ${documentContext.overallRisk.toLowerCase()} risk assessment. I can help clarify any clauses, explain legal terms, or discuss potential implications. What would you like to know?`;
  }

  // Generate initial helpful examples
  private generateInitialExamples(clauseContext?: ClauseContext): string[] {
    const examples = [
      "What does this clause mean in simple terms?",
      "What are the potential risks here?",
      "How might this affect me?",
      "What should I be careful about?"
    ];

    if (clauseContext) {
      if (clauseContext.riskLevel === 'RED') {
        examples.unshift("Why is this clause considered high risk?");
        examples.push("What can I do to protect myself?");
      } else if (clauseContext.riskLevel === 'YELLOW') {
        examples.unshift("What makes this clause moderately risky?");
        examples.push("Should I negotiate this clause?");
      }
    }

    return examples.slice(0, 4); // Return top 4 examples
  }

  // Generate contextual examples based on user's question
  private generateContextualExamples(userQuestion: string, _clauseContext?: ClauseContext): string[] {
    const lowerQuestion = userQuestion.toLowerCase();
    
    if (lowerQuestion.includes('risk') || lowerQuestion.includes('danger')) {
      return [
        "Can you give me a real-world example?",
        "How likely is this risk to actually happen?",
        "What's the worst-case scenario?",
        "How can I minimize this risk?"
      ];
    }
    
    if (lowerQuestion.includes('mean') || lowerQuestion.includes('explain')) {
      return [
        "Can you break this down further?",
        "What are the key points I should remember?",
        "Are there any hidden implications?",
        "How does this compare to standard terms?"
      ];
    }
    
    return [
      "Can you provide more details?",
      "What should I do next?",
      "Are there alternatives to consider?",
      "Should I consult a lawyer about this?"
    ];
  }

  // Enhance AI response with practical examples and simple explanations
  private enhanceAIResponse(response: string, clauseContext?: ClauseContext): string {
    // Add practical context and examples
    let enhancedResponse = response;
    
    // Add practical examples for complex legal terms
    if (response.includes('liability') || response.includes('indemnification')) {
      enhancedResponse += "\n\n💡 **Real-world example**: Think of this like car insurance - if something goes wrong, who pays for the damages? This clause determines that responsibility.";
    }
    
    if (response.includes('termination') || response.includes('breach')) {
      enhancedResponse += "\n\n💡 **In simple terms**: This is like the 'rules for breaking up' - what happens if one party wants to end the agreement or doesn't follow the rules.";
    }
    
    if (response.includes('intellectual property') || response.includes('IP')) {
      enhancedResponse += "\n\n💡 **Think of it as**: Who owns the ideas, designs, or creations? It's like putting your name on your artwork - this clause decides ownership rights.";
    }
    
    // Add risk-specific guidance
    if (clauseContext?.riskLevel === 'RED') {
      enhancedResponse += "\n\n⚠️ **Important**: This is a high-risk area. Consider getting professional legal advice before proceeding.";
    }
    
    return enhancedResponse;
  }

  // Calculate confidence score for AI responses
  private calculateResponseConfidence(response: string): number {
    // Simple heuristic based on response characteristics
    let confidence = 85; // Base confidence
    
    if (response.length < 50) confidence -= 15; // Very short responses
    if (response.includes('I\'m not sure') || response.includes('unclear')) confidence -= 20;
    if (response.includes('consult') || response.includes('lawyer')) confidence -= 10; // Appropriate caution
    if (response.includes('example') || response.includes('specifically')) confidence += 10;
    
    return Math.max(60, Math.min(95, confidence)); // Clamp between 60-95%
  }

  // Switch context to a different clause
  switchToClause(clauseContext: ClauseContext): void {
    const session = this.getCurrentSession();
    if (!session) return;

    session.clauseContext = clauseContext;
    session.lastActivity = new Date();

    // Add context switch message
    const contextMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'system',
      content: `Now focusing on Clause ${clauseContext.clauseId} (${clauseContext.riskLevel.toLowerCase()} risk). How can I help you understand this clause?`,
      timestamp: new Date(),
      clauseReference: clauseContext.clauseId
    };

    session.messages.push(contextMessage);
  }

  // Get conversation history for support escalation
  getConversationHistory(): ChatMessage[] {
    const session = this.getCurrentSession();
    return session ? session.messages : [];
  }

  // Clear current session
  clearSession(): void {
    this.currentSessionId = null;
  }

  // Get all sessions (for debugging/admin)
  getAllSessions(): ChatSession[] {
    return Array.from(this.sessions.values());
  }
}

export const chatService = new ChatService();
export default chatService;