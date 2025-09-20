import { apiService } from './apiService';
import { notificationService } from './notificationService';
import type { AnalysisResult } from '../App';

export interface SummaryData {
  keyPoints: string[];
  riskSummary: string;
  recommendations: string[];
  simplifiedExplanation: string;
  jargonFreeVersion: string;
  timestamp: Date;
}

export interface ClauseSummary {
  clauseId: string;
  summary: string;
  keyRisks: string[];
  plainLanguage: string;
  actionItems: string[];
  timestamp: Date;
}

export interface SummarizationState {
  documentSummary: SummaryData | null;
  clauseSummaries: Map<string, ClauseSummary>;
  isLoading: Set<string>;
}

class SummarizationService {
  private state: SummarizationState = {
    documentSummary: null,
    clauseSummaries: new Map(),
    isLoading: new Set(),
  };

  private listeners: Set<() => void> = new Set();

  constructor() {
    this.loadPersistedState();
  }

  // State management
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener());
  }

  getState(): SummarizationState {
    return { ...this.state };
  }

  // Persistence
  private loadPersistedState(): void {
    try {
      const savedSummaries = localStorage.getItem('legalSaathi_summaries');
      if (savedSummaries) {
        const parsed = JSON.parse(savedSummaries);
        
        if (parsed.documentSummary) {
          this.state.documentSummary = {
            ...parsed.documentSummary,
            timestamp: new Date(parsed.documentSummary.timestamp)
          };
        }

        if (parsed.clauseSummaries) {
          this.state.clauseSummaries = new Map(
            Object.entries(parsed.clauseSummaries).map(([clauseId, summary]: [string, any]) => [
              clauseId,
              {
                ...summary,
                timestamp: new Date(summary.timestamp)
              }
            ])
          );
        }
      }
    } catch (error) {
      console.error('Failed to load persisted summary state:', error);
    }
  }

  private persistState(): void {
    try {
      const summariesObj: any = {
        documentSummary: this.state.documentSummary ? {
          ...this.state.documentSummary,
          timestamp: this.state.documentSummary.timestamp.toISOString()
        } : null,
        clauseSummaries: {}
      };

      this.state.clauseSummaries.forEach((summary, clauseId) => {
        summariesObj.clauseSummaries[clauseId] = {
          ...summary,
          timestamp: summary.timestamp.toISOString()
        };
      });

      localStorage.setItem('legalSaathi_summaries', JSON.stringify(summariesObj));
    } catch (error) {
      console.error('Failed to persist summary state:', error);
    }
  }

  // Document summarization
  async generateDocumentSummary(analysis: AnalysisResult): Promise<SummaryData | null> {
    if (this.state.documentSummary) {
      return this.state.documentSummary;
    }

    if (this.state.isLoading.has('document')) {
      return null;
    }

    this.state.isLoading.add('document');
    this.notify();

    try {
      // Create a jargon-free summary from the analysis
      const summary = await this.createJargonFreeSummary(analysis);
      
      if (summary) {
        this.state.documentSummary = summary;
        this.persistState();
        this.notify();
        notificationService.success('Document summary generated');
        return summary;
      } else {
        notificationService.error('Failed to generate document summary');
        return null;
      }
    } catch (error) {
      console.error('Summarization error:', error);
      notificationService.error('Summarization service unavailable');
      return null;
    } finally {
      this.state.isLoading.delete('document');
      this.notify();
    }
  }

  private async createJargonFreeSummary(analysis: AnalysisResult): Promise<SummaryData> {
    // Extract key information from analysis
    const keyPoints = this.extractKeyPoints(analysis);
    const riskSummary = this.createRiskSummary(analysis);
    const recommendations = this.extractRecommendations(analysis);
    const simplifiedExplanation = this.createSimplifiedExplanation(analysis);
    
    // Create jargon-free version using AI clarification
    const jargonFreeVersion = await this.generateJargonFreeVersion(analysis);

    return {
      keyPoints,
      riskSummary,
      recommendations,
      simplifiedExplanation,
      jargonFreeVersion,
      timestamp: new Date()
    };
  }

  private extractKeyPoints(analysis: AnalysisResult): string[] {
    const points: string[] = [];
    
    // Overall risk point
    points.push(`Overall document risk level: ${analysis.overall_risk.level.toLowerCase()}`);
    
    // High-risk clauses
    const highRiskClauses = analysis.analysis_results.filter(r => r.risk_level.level === 'RED');
    if (highRiskClauses.length > 0) {
      points.push(`${highRiskClauses.length} high-risk clause${highRiskClauses.length > 1 ? 's' : ''} identified`);
    }

    // Severity indicators
    if (analysis.severity_indicators && analysis.severity_indicators.length > 0) {
      points.push(`Critical issues detected: ${analysis.severity_indicators.length} items need immediate attention`);
    }

    // Risk categories
    if (analysis.overall_risk.risk_categories) {
      const highRiskCategories = Object.entries(analysis.overall_risk.risk_categories)
        .filter(([_, score]) => score > 0.7)
        .map(([category, _]) => category);
      
      if (highRiskCategories.length > 0) {
        points.push(`High-risk areas: ${highRiskCategories.join(', ')}`);
      }
    }

    return points;
  }

  private createRiskSummary(analysis: AnalysisResult): string {
    const riskLevel = analysis.overall_risk.level;
    const confidence = analysis.overall_risk.confidence_percentage;
    
    let summary = `This document has been assessed as ${riskLevel.toLowerCase()} risk `;
    summary += `with ${confidence}% confidence. `;
    
    if (riskLevel === 'RED') {
      summary += 'This means there are significant concerns that could lead to legal or financial problems. ';
    } else if (riskLevel === 'YELLOW') {
      summary += 'This means there are some concerns that should be reviewed carefully. ';
    } else {
      summary += 'This means the document appears to have minimal risk concerns. ';
    }

    if (analysis.overall_risk.low_confidence_warning) {
      summary += 'However, the AI analysis has lower confidence in this assessment, so professional review is recommended.';
    }

    return summary;
  }

  private extractRecommendations(analysis: AnalysisResult): string[] {
    const recommendations: string[] = [];
    
    // Collect unique recommendations from all clauses
    const allRecommendations = new Set<string>();
    analysis.analysis_results.forEach(result => {
      result.recommendations.forEach(rec => allRecommendations.add(rec));
    });

    recommendations.push(...Array.from(allRecommendations).slice(0, 5)); // Limit to top 5

    // Add general recommendations based on risk level
    if (analysis.overall_risk.level === 'RED') {
      recommendations.unshift('Seek immediate legal review before proceeding');
    } else if (analysis.overall_risk.level === 'YELLOW') {
      recommendations.unshift('Consider professional legal consultation');
    }

    return recommendations;
  }

  private createSimplifiedExplanation(analysis: AnalysisResult): string {
    let explanation = 'In simple terms: ';
    
    const riskCounts = {
      red: analysis.analysis_results.filter(r => r.risk_level.level === 'RED').length,
      yellow: analysis.analysis_results.filter(r => r.risk_level.level === 'YELLOW').length,
      green: analysis.analysis_results.filter(r => r.risk_level.level === 'GREEN').length,
    };

    if (riskCounts.red > 0) {
      explanation += `This document contains ${riskCounts.red} section${riskCounts.red > 1 ? 's' : ''} that could cause problems. `;
    }
    
    if (riskCounts.yellow > 0) {
      explanation += `There are also ${riskCounts.yellow} section${riskCounts.yellow > 1 ? 's' : ''} that need careful attention. `;
    }

    if (riskCounts.green > 0) {
      explanation += `${riskCounts.green} section${riskCounts.green > 1 ? 's' : ''} appear${riskCounts.green === 1 ? 's' : ''} to be fine. `;
    }

    explanation += 'The AI has analyzed the legal language and highlighted areas where you might face risks or need to take action.';

    return explanation;
  }

  private async generateJargonFreeVersion(analysis: AnalysisResult): Promise<string> {
    try {
      const context = {
        summary: analysis.summary,
        risk_level: analysis.overall_risk.level,
        clause_count: analysis.analysis_results.length
      };

      const question = 'Please explain this legal document analysis in very simple, jargon-free language that anyone can understand. Focus on what it means for the person and what they should do.';
      
      const result = await apiService.askClarification(question, context);
      
      if (result.success && result.response) {
        return result.response;
      } else {
        return this.createSimplifiedExplanation(analysis);
      }
    } catch (error) {
      console.error('Failed to generate jargon-free version:', error);
      return this.createSimplifiedExplanation(analysis);
    }
  }

  // Clause-specific summarization
  async generateClauseSummary(clauseId: string, clauseData: any): Promise<ClauseSummary | null> {
    const existing = this.state.clauseSummaries.get(clauseId);
    if (existing) {
      return existing;
    }

    if (this.state.isLoading.has(clauseId)) {
      return null;
    }

    this.state.isLoading.add(clauseId);
    this.notify();

    try {
      const summary = await this.createClauseSummary(clauseId, clauseData);
      
      if (summary) {
        this.state.clauseSummaries.set(clauseId, summary);
        this.persistState();
        this.notify();
        return summary;
      } else {
        return null;
      }
    } catch (error) {
      console.error('Clause summarization error:', error);
      return null;
    } finally {
      this.state.isLoading.delete(clauseId);
      this.notify();
    }
  }

  private async createClauseSummary(clauseId: string, clauseData: any): Promise<ClauseSummary> {
    const summary = clauseData.plain_explanation || 'No explanation available';
    const keyRisks = clauseData.legal_implications || [];
    const actionItems = clauseData.recommendations || [];
    
    // Generate plain language version
    let plainLanguage = summary;
    try {
      const context = {
        clause_text: clauseData.plain_explanation,
        risk_level: clauseData.risk_level?.level,
        implications: clauseData.legal_implications
      };

      const question = 'Explain this clause analysis in very simple terms, avoiding legal jargon. What does this mean for someone reading this document?';
      
      const result = await apiService.askClarification(question, context);
      if (result.success && result.response) {
        plainLanguage = result.response;
      }
    } catch (error) {
      console.error('Failed to generate plain language summary:', error);
    }

    return {
      clauseId,
      summary,
      keyRisks,
      plainLanguage,
      actionItems,
      timestamp: new Date()
    };
  }

  // Getters
  getDocumentSummary(): SummaryData | null {
    return this.state.documentSummary;
  }

  getClauseSummary(clauseId: string): ClauseSummary | null {
    return this.state.clauseSummaries.get(clauseId) || null;
  }

  isLoading(id: string): boolean {
    return this.state.isLoading.has(id);
  }

  // Clear methods
  clearDocumentSummary(): void {
    this.state.documentSummary = null;
    this.persistState();
    this.notify();
  }

  clearClauseSummary(clauseId: string): void {
    this.state.clauseSummaries.delete(clauseId);
    this.persistState();
    this.notify();
  }

  clearAllSummaries(): void {
    this.state.documentSummary = null;
    this.state.clauseSummaries.clear();
    localStorage.removeItem('legalSaathi_summaries');
    this.notify();
  }
}

export const summarizationService = new SummarizationService();
export default summarizationService;