import { apiService } from './apiService';
import { notificationService } from './notificationService';
import { experienceLevelService } from './experienceLevelService';
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
    // ALWAYS clear existing summary to force regeneration with fresh data
    console.log('🔄 Forcing fresh document summary generation - clearing all caches');
    this.clearAllCaches();

    if (this.state.isLoading.has('document')) {
      return null;
    }

    this.state.isLoading.add('document');
    this.notify();

    try {
      console.log('Generating document summary with analysis:', {
        hasAnalysis: !!analysis,
        overallRisk: analysis?.overall_risk?.level,
        clauseCount: analysis?.analysis_results?.length,
        hasSummary: !!analysis?.summary
      });

      // Validate analysis data
      if (!analysis) {
        throw new Error('No analysis data provided');
      }

      // Create a jargon-free summary from the analysis
      const summary = await this.createJargonFreeSummary(analysis);

      if (summary) {
        this.state.documentSummary = summary;
        this.persistState();
        this.notify();
        notificationService.success('Document summary generated successfully');
        return summary;
      } else {
        throw new Error('Failed to create summary from analysis');
      }
    } catch (error) {
      console.error('Summarization error:', error);

      // Create a basic summary even if AI service fails
      try {
        const fallbackSummary = this.createBasicSummary(analysis);
        this.state.documentSummary = fallbackSummary;
        this.persistState();
        this.notify();
        notificationService.info('Document summary generated (basic mode)');
        return fallbackSummary;
      } catch (fallbackError) {
        console.error('Fallback summary creation failed:', fallbackError);
        notificationService.error('Unable to generate document summary');
        return null;
      }
    } finally {
      this.state.isLoading.delete('document');
      this.notify();
    }
  }

  private createBasicSummary(analysis: AnalysisResult): SummaryData {
    console.log('Creating basic summary as fallback');

    const keyPoints = this.extractKeyPoints(analysis);
    const riskSummary = this.createRiskSummary(analysis);
    const recommendations = this.extractRecommendations(analysis);
    const simplifiedExplanation = this.createSimplifiedExplanation(analysis);
    const jargonFreeVersion = this.createDetailedFallbackExplanation(analysis);

    return {
      keyPoints,
      riskSummary,
      recommendations,
      simplifiedExplanation,
      jargonFreeVersion,
      timestamp: new Date() // Always use current timestamp for fresh summaries
    };
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
      timestamp: new Date() // Always use current timestamp for fresh summaries
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
      // Check if we have valid analysis data
      if (!analysis || !analysis.analysis_results || analysis.analysis_results.length === 0) {
        console.warn('No analysis data available for summary generation');
        return this.createDetailedFallbackExplanation(analysis);
      }

      console.log('🚀 GENERATING AI-POWERED DOCUMENT SUMMARY with comprehensive context...');

      // Build comprehensive context with complete document analysis data
      const highRiskClauses = analysis.analysis_results.filter(r => r.risk_level.level === 'RED');
      const mediumRiskClauses = analysis.analysis_results.filter(r => r.risk_level.level === 'YELLOW');
      const lowRiskClauses = analysis.analysis_results.filter(r => r.risk_level.level === 'GREEN');

      // Build comprehensive context for AI service with detailed clause information
      const clauseExamples = analysis.analysis_results.slice(0, 5).map(clause => ({
        id: clause.clause_id,
        text: clause.clause_text?.substring(0, 300) || 'No text available', // Limit text length
        risk: clause.risk_level.level,
        score: clause.risk_level.score,
        severity: clause.risk_level.severity,
        confidence: clause.risk_level.confidence_percentage,
        explanation: clause.plain_explanation?.substring(0, 200) || 'No explanation',
        implications: clause.legal_implications?.slice(0, 2) || [],
        recommendations: clause.recommendations?.slice(0, 2) || []
      }));

      const context = {
        document: {
          documentType: analysis.document_type || 'legal document',
          overallRisk: analysis.overall_risk.level,
          summary: analysis.summary || 'Document analysis completed',
          totalClauses: analysis.analysis_results.length,
          riskBreakdown: {
            high: highRiskClauses.length,
            medium: mediumRiskClauses.length,
            low: lowRiskClauses.length
          },
          confidenceLevel: analysis.overall_risk.confidence_percentage,
          hasLowConfidenceWarning: analysis.overall_risk.low_confidence_warning || false,
          overallScore: analysis.overall_risk.score,
          overallSeverity: analysis.overall_risk.severity || analysis.overall_risk.level.toLowerCase(),
          riskCategories: analysis.overall_risk.risk_categories || {},
          hasCompleteAnalysis: true,
          analysisVersion: '2.0'
        },
        clauseExamples: clauseExamples,
        keyInsights: {
          severityIndicators: analysis.severity_indicators?.slice(0, 3) || [],
          mainRecommendations: this.extractRecommendations(analysis).slice(0, 5),
          enhancedInsights: analysis.enhanced_insights || {},
          criticalIssues: highRiskClauses.map(c => c.plain_explanation?.substring(0, 100) || 'High risk clause').slice(0, 3)
        },
        analysisMetadata: {
          processingTime: analysis.processing_time || 0,
          timestamp: new Date().toISOString(),
          analysisComplete: true,
          analysisQuality: 'comprehensive'
        }
      };

      // Get user experience level for personalized summary
      const experienceLevel = experienceLevelService.getLevelForAPI();

      const question = `Write exactly 5-6 plain sentences about what this ${analysis.document_type || 'legal document'} document contains. Only describe the document content and purpose. Do not include risk analysis, recommendations, or formatting. Just explain what the document is about in simple terms.`;

      try {
        const result = await apiService.askClarification(question, context, experienceLevel);

        console.log('🔍 AI Service Response:', {
          success: result.success,
          responseLength: result.response?.length || 0,
          serviceUsed: result.service_used,
          fallback: result.fallback,
          confidenceScore: result.confidence_score
        });

        // Check if this is a context validation error - bypass and use fallback immediately
        if (result.service_used === 'context_validation' ||
          (result.response && result.response.includes('need more complete document analysis'))) {
          console.warn('🔄 AI service rejected context, using enhanced fallback with available analysis data');
          return this.createDetailedFallbackExplanation(analysis);
        }

        if (result.success && result.response && result.response.length > 200 && !result.fallback) {
          console.log('✅ Generated HIGH-QUALITY AI document summary with full context');
          return result.response;
        } else if (result.success && result.response && result.response.length > 50) {
          // Use AI response even if it's shorter, as long as it's not an error message
          const isErrorMessage = result.response.toLowerCase().includes('need more complete') ||
            result.response.toLowerCase().includes('insufficient') ||
            result.response.toLowerCase().includes('please ensure');

          if (!isErrorMessage) {
            console.log('✅ Using AI response despite shorter length');
            return result.response;
          }
        }

        console.warn('⚠️ AI service returned insufficient response or used fallback, using enhanced fallback');
        console.warn('Response preview:', result.response?.substring(0, 200));
        return this.createDetailedFallbackExplanation(analysis);
      } catch (error) {
        console.error('❌ AI service completely failed, using enhanced fallback:', error);
        return this.createDetailedFallbackExplanation(analysis);
      }
    } catch (error) {
      console.error('Failed to generate jargon-free version:', error);
      return this.createDetailedFallbackExplanation(analysis);
    }
  }

  private createDetailedFallbackExplanation(analysis: AnalysisResult): string {
    if (!analysis || !analysis.analysis_results) {
      return `This document is currently being analyzed. Please wait for the analysis to complete to see a summary of what this document contains and its overall purpose.`;
    }

    // Create a simple 5-6 line document overview
    const documentType = analysis.document_type?.replace('_', ' ') || 'legal document';
    const riskLevel = analysis.overall_risk?.level || 'UNKNOWN';
    const totalClauses = analysis.analysis_results?.length || 0;
    const confidence = analysis.overall_risk?.confidence_percentage || 0;

    let explanation = `This is a ${documentType} containing ${totalClauses} clauses that have been analyzed for legal risks. `;

    if (riskLevel === 'RED') {
      explanation += `The document has been assessed as high risk, meaning there are significant concerns that need attention before signing. `;
    } else if (riskLevel === 'YELLOW') {
      explanation += `The document has been assessed as medium risk, meaning there are some concerns that should be reviewed carefully. `;
    } else {
      explanation += `The document has been assessed as low risk, meaning it appears to have standard terms with minimal concerns. `;
    }

    explanation += `The analysis covers the key terms, obligations, and potential issues within the document. `;

    if (confidence < 80) {
      explanation += `The AI analysis has ${confidence}% confidence, so consider professional legal review for important decisions. `;
    } else {
      explanation += `The AI analysis provides good confidence (${confidence}%) in this assessment. `;
    }

    explanation += `This summary gives you a quick overview of what the document contains and its overall risk profile.`;

    return explanation;
  }

  // Clause-specific summarization
  async generateClauseSummary(clauseId: string, clauseData: any): Promise<ClauseSummary | null> {
    // ALWAYS generate fresh clause summaries - clear existing
    console.log(`🔄 Forcing fresh clause summary for ${clauseId} - clearing cache`);
    this.state.clauseSummaries.delete(clauseId);

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

    // Generate plain language version with comprehensive context
    let plainLanguage = summary;
    try {
      // Check if we have sufficient clause data
      if (!clauseData || !clauseData.clause_text) {
        console.warn(`Insufficient clause data for clause ${clauseId}`);
        plainLanguage = this.createFallbackClauseExplanation(clauseId, clauseData);
      } else {
        // Build comprehensive context for AI service
        const context = {
          clause: {
            clauseId: clauseId,
            text: clauseData.clause_text?.substring(0, 500) || 'No text available', // Limit text length
            riskLevel: clauseData.risk_level?.level || 'unknown',
            riskScore: clauseData.risk_level?.score || 0,
            severity: clauseData.risk_level?.severity || 'unknown',
            confidence: clauseData.risk_level?.confidence_percentage || 0,
            explanation: clauseData.plain_explanation?.substring(0, 300) || 'No explanation available',
            implications: clauseData.legal_implications?.slice(0, 3) || [],
            recommendations: clauseData.recommendations?.slice(0, 3) || [],
            hasLowConfidence: clauseData.risk_level?.low_confidence_warning || false,
            riskCategories: clauseData.risk_level?.risk_categories || {},
            reasons: clauseData.risk_level?.reasons?.slice(0, 2) || [],
            hasSpecificIssues: (clauseData.risk_level?.score || 0) > 0.6
          },
          document: {
            documentType: 'legal document',
            analysisComplete: true,
            overallRisk: 'unknown',
            totalClauses: 1,
            contextVersion: '2.0'
          },
          analysisMetadata: {
            clauseAnalysisComplete: true,
            timestamp: new Date().toISOString(),
            analysisQuality: 'comprehensive'
          }
        };

        // Get user experience level for personalized clause summary
        const experienceLevel = experienceLevelService.getLevelForAPI();

        const question = `Analyze clause ${clauseId} for ${experienceLevel} level. Risk: ${clauseData.risk_level?.level || 'Unknown'} (${clauseData.risk_level?.score || 0}/1.0), Confidence: ${clauseData.risk_level?.confidence_percentage || 0}%. Text: "${clauseData.clause_text?.substring(0, 200)}...". Provide specific risks, real-world impact, and exact negotiation language.`;

        const result = await apiService.askClarification(question, context, experienceLevel);

        console.log(`🔍 Clause ${clauseId} AI Service Response:`, {
          success: result.success,
          responseLength: result.response?.length || 0,
          serviceUsed: result.service_used,
          fallback: result.fallback,
          confidenceScore: result.confidence_score
        });

        if (result.success && result.response && result.response.length > 100 && !result.fallback) {
          console.log(`✅ Generated HIGH-QUALITY AI clause summary for clause ${clauseId} with full context`);
          plainLanguage = result.response;
        } else if (result.success && result.response && result.response.length > 50) {
          // Use AI response even if shorter, as long as it's not an error message
          const isErrorMessage = result.response.toLowerCase().includes('need more complete') ||
            result.response.toLowerCase().includes('insufficient') ||
            result.response.toLowerCase().includes('please ensure');

          if (!isErrorMessage) {
            console.log(`✅ Using AI clause response for ${clauseId} despite shorter length`);
            plainLanguage = result.response;
          } else {
            console.warn(`⚠️ AI service returned error message for clause ${clauseId}, using fallback`);
            plainLanguage = this.createFallbackClauseExplanation(clauseId, clauseData);
          }
        } else {
          console.warn(`⚠️ AI service returned insufficient response for clause ${clauseId}, using fallback`);
          console.warn('Response preview:', result.response?.substring(0, 200));
          plainLanguage = this.createFallbackClauseExplanation(clauseId, clauseData);
        }
      }
    } catch (error) {
      console.error(`Failed to generate plain language summary for clause ${clauseId}:`, error);
      plainLanguage = this.createFallbackClauseExplanation(clauseId, clauseData);
    }

    return {
      clauseId,
      summary,
      keyRisks,
      plainLanguage,
      actionItems,
      timestamp: new Date() // Always use current timestamp for fresh clause summaries
    };
  }

  private createFallbackClauseExplanation(clauseId: string, clauseData: any): string {
    if (!clauseData) {
      return `## Clause ${clauseId} Analysis

**Status:** Unable to analyze this clause at the moment.

I'm having trouble analyzing this clause right now. Please try refreshing the analysis or contact support if the issue persists.`;
    }

    const riskLevel = clauseData.risk_level?.level || 'UNKNOWN';
    const riskScore = clauseData.risk_level?.score || 0;
    const confidence = clauseData.risk_level?.confidence_percentage || 0;
    const clauseText = clauseData.clause_text || '';
    const explanation = clauseData.plain_explanation || '';
    const implications = clauseData.legal_implications || [];
    const recommendations = clauseData.recommendations || [];

    let fallbackExplanation = `## Clause ${clauseId} Analysis

**Risk Level:** ${riskLevel}${riskScore > 0 ? ` (${riskScore.toFixed(1)}/1.0)` : ''}${confidence > 0 ? ` • ${confidence}% confidence` : ''}

---

`;

    // Add clause text if available
    if (clauseText) {
      const displayText = clauseText.length > 300 ? clauseText.substring(0, 300) + '...' : clauseText;
      fallbackExplanation += `### 📄 Clause Text

"${displayText}"

---

`;
    }

    // Add explanation if available
    if (explanation) {
      fallbackExplanation += `### 💡 What This Means

${explanation}

---

`;
    }

    // Add implications in a more structured way
    if (implications.length > 0) {
      fallbackExplanation += `### ⚖️ Legal Implications

`;
      implications.slice(0, 3).forEach((implication: string, index: number) => {
        fallbackExplanation += `**${index + 1}.** ${implication}\n\n`;
      });
      fallbackExplanation += `---\n\n`;
    }

    // Add recommendations in a more structured way
    if (recommendations.length > 0) {
      fallbackExplanation += `### 🎯 Recommended Actions

`;
      recommendations.slice(0, 3).forEach((rec: string, index: number) => {
        fallbackExplanation += `**${index + 1}.** ${rec}\n\n`;
      });
      fallbackExplanation += `---\n\n`;
    }

    // Add risk-specific guidance
    fallbackExplanation += `### 🚨 Risk Assessment

`;

    if (riskLevel === 'RED') {
      fallbackExplanation += `**High Risk Clause**

This clause requires immediate attention and careful consideration:

• **Review Required:** Have a qualified attorney examine this clause
• **Negotiation Needed:** This clause likely needs modification
• **Don't Rush:** Take time to understand the full implications
• **Consider Alternatives:** Explore different terms that better protect your interests

**⚠️ Important:** This is a high-risk clause that could significantly impact your rights or obligations.`;
    } else if (riskLevel === 'YELLOW') {
      fallbackExplanation += `**Moderate Risk Clause**

This clause has some concerns that warrant attention:

• **Careful Review:** Make sure you fully understand what you're agreeing to
• **Ask Questions:** Clarify any unclear or ambiguous language
• **Consider Changes:** Think about whether the terms could be improved
• **Professional Input:** Consider getting legal advice if you're unsure

**⚡ Note:** While not immediately dangerous, this clause could benefit from review or negotiation.`;
    } else if (riskLevel === 'GREEN') {
      fallbackExplanation += `**Standard Clause**

This clause appears to be relatively balanced and fair:

• **Standard Terms:** The language appears to be typical for this type of document
• **Reasonable Balance:** Terms seem fair to both parties
• **Low Concern:** No immediate red flags identified
• **Still Review:** Always read and understand what you're agreeing to

**✅ Good news:** This clause appears to be standard and doesn't raise significant concerns.`;
    } else {
      fallbackExplanation += `**Assessment Unclear**

I need more information to properly evaluate this clause:

• **Limited Data:** Insufficient information available for complete analysis
• **Professional Review:** Consider having an attorney examine this clause
• **Ask Questions:** Request clarification on any unclear terms
• **Be Cautious:** When in doubt, seek professional legal advice

**❓ Unclear:** More information is needed to provide a complete risk assessment.`;
    }

    return fallbackExplanation;
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

  // Force clear all caches for fresh responses
  clearAllCaches(): void {
    this.state.documentSummary = null;
    this.state.clauseSummaries.clear();
    this.state.isLoading.clear();
    localStorage.removeItem('legalSaathi_summaries');
    console.log('🧹 Cleared all summarization caches for fresh responses');
    this.notify();
  }

  // Clear caches when new analysis is available
  clearCachesForNewAnalysis(): void {
    console.log('🔄 Clearing caches for new document analysis');
    this.clearAllCaches();
  }

  // Force regenerate document summary
  async forceRegenerateDocumentSummary(analysis: AnalysisResult): Promise<SummaryData | null> {
    console.log('Force regenerating document summary');
    this.clearDocumentSummary();
    return await this.generateDocumentSummary(analysis);
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