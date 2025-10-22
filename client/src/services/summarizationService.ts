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

      // Extract detailed clause information with full context
      const clauseExamples = analysis.analysis_results.slice(0, 5).map(clause => ({
        id: clause.clause_id,
        text: clause.clause_text, // Include full clause text for better context
        risk: clause.risk_level.level,
        score: clause.risk_level.score,
        severity: clause.risk_level.severity,
        confidence: clause.risk_level.confidence_percentage,
        explanation: clause.plain_explanation,
        implications: clause.legal_implications,
        recommendations: clause.recommendations,
        hasLowConfidence: clause.risk_level.low_confidence_warning || false,
        riskCategories: clause.risk_level.risk_categories || {},
        reasons: clause.risk_level.reasons || []
      }));

      // Build COMPREHENSIVE context with ALL available analysis data for high-quality AI responses
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
          // Add comprehensive document-level data
          overallReasons: analysis.overall_risk.reasons || [],
          documentLength: analysis.document_text?.length || 0,
          analysisVersion: '2.0',
          hasCompleteAnalysis: true
        },
        clauseExamples: clauseExamples,
        // Add ALL clause data for comprehensive context
        allClauses: analysis.analysis_results.map(clause => ({
          id: clause.clause_id,
          text: clause.clause_text,
          risk: clause.risk_level.level,
          score: clause.risk_level.score,
          severity: clause.risk_level.severity,
          confidence: clause.risk_level.confidence_percentage,
          explanation: clause.plain_explanation,
          implications: clause.legal_implications,
          recommendations: clause.recommendations,
          reasons: clause.risk_level.reasons || [],
          riskCategories: clause.risk_level.risk_categories || {}
        })),
        keyInsights: {
          severityIndicators: analysis.severity_indicators || [],
          mainRecommendations: this.extractRecommendations(analysis).slice(0, 8), // More recommendations
          enhancedInsights: analysis.enhanced_insights || {},
          criticalIssues: highRiskClauses.map(c => c.plain_explanation).slice(0, 3),
          documentPatterns: analysis.document_patterns || [],
          complianceFlags: analysis.compliance_flags || []
        },
        analysisMetadata: {
          processingTime: analysis.processing_time,
          timestamp: new Date().toISOString(),
          analysisComplete: true,
          analysisQuality: 'comprehensive',
          contextVersion: '2.0'
        }
      };

      // Get user experience level for personalized summary
      const experienceLevel = experienceLevelService.getLevelForAPI();

      const question = `You are LegalSaathi, the world's most detailed legal document advisor. Analyze this legal document and provide a comprehensive, actionable summary for someone at ${experienceLevel} experience level.

COMPLETE DOCUMENT ANALYSIS DATA:
Document Type: ${analysis.document_type || 'Legal Document'}
Overall Risk Assessment: ${analysis.overall_risk.level} (Risk Score: ${analysis.overall_risk.score}/1.0, Severity: ${analysis.overall_risk.severity || 'Unknown'})
Analysis Confidence: ${analysis.overall_risk.confidence_percentage}%
Total Clauses Analyzed: ${analysis.analysis_results.length}
Risk Distribution: ${highRiskClauses.length} HIGH-RISK, ${mediumRiskClauses.length} MEDIUM-RISK, ${lowRiskClauses.length} LOW-RISK clauses
Overall Risk Reasons: ${(analysis.overall_risk.reasons || []).join(' | ')}

DETAILED CLAUSE-BY-CLAUSE DATA:
${clauseExamples.map((clause) => `
CLAUSE ${clause.id} COMPLETE ANALYSIS:
- Risk Level: ${clause.risk} (Risk Score: ${clause.score}/1.0, Severity: ${clause.severity})
- Analysis Confidence: ${clause.confidence}%
- Risk Reasons: ${(clause.reasons || []).join(' | ')}
- Full Clause Text: "${clause.text}"
- Current AI Analysis: ${clause.explanation}
- Legal Implications: ${clause.implications.join(' | ')}
- Specific Recommendations: ${clause.recommendations.join(' | ')}
- Risk Categories: Financial=${clause.riskCategories?.financial || 'N/A'}, Legal=${clause.riskCategories?.legal || 'N/A'}, Operational=${clause.riskCategories?.operational || 'N/A'}
`).join('\n')}

ABSOLUTE REQUIREMENTS - FAILURE TO FOLLOW RESULTS IN REJECTION:

1. **SPECIFIC DATA USAGE**: Reference exact clause texts, risk scores (${analysis.overall_risk.score}/1.0), confidence percentages (${analysis.overall_risk.confidence_percentage}%), and analysis findings from above.

2. **DETAILED EXPLANATIONS**: For each high-risk clause, explain:
   - WHAT it means in plain language with specific examples
   - WHY it's problematic (reference the exact risk score and reasons)
   - HOW it could affect the user (concrete scenarios with dollar amounts/timeframes)
   - WHAT specific actions to take (exact negotiation language)

3. **CONCRETE EXAMPLES**: Use real-world scenarios like:
   - "If you're terminated, this clause means you'll lose $X in severance because [specific clause language]"
   - "This 24-month non-compete prevents you from working at companies like [specific examples] because [exact restriction]"
   - "The $5,000 security deposit could be lost if the landlord claims damages for normal wear and tear because [specific clause language]"

4. **SPECIFIC NEGOTIATION TACTICS**:
   - Exact language to propose: "Change 'at landlord's sole discretion' to 'for documented damages exceeding normal wear and tear'"
   - Specific alternatives: "Reduce non-compete from 24 months to 6 months"
   - Concrete compromises: "Add compensation of $X/month during non-compete period"

5. **ACTIONABLE STEPS WITH TIMELINES**:
   - "Before signing: Request these 3 specific changes..."
   - "During negotiation: Use this exact language..."
   - "If they refuse: Consider these 2 alternatives..."

6. **RISK QUANTIFICATION**: Use the actual risk scores and explain:
   - "This clause scored ${analysis.overall_risk.score}/1.0 risk because [specific reasons]"
   - "With ${analysis.overall_risk.confidence_percentage}% confidence, this creates problems because [specific examples]"

ABSOLUTELY FORBIDDEN - WILL CAUSE REJECTION:
❌ "Could be improved" (HOW specifically?)
❌ "Consult a lawyer" (Give specific guidance first)
❌ "Review carefully" (What exactly to look for?)
❌ "May cause issues" (What specific issues?)
❌ "Consider negotiating" (What exact changes?)
❌ "Creates financial disadvantages" (What specific disadvantages with examples?)
❌ "Main issues:" without specific details
❌ "Lacks specific criteria" without proposing exact criteria

REQUIRED FORMAT - Use clear sections with proper formatting:

**Executive Summary**
[2-3 sentences with specific recommendation]

**Key Document Issues**
- [Issue 1 with specific details]
- [Issue 2 with specific details]
- [Issue 3 with specific details]

**Risk Analysis**
[Detailed explanation of risks with specific examples and dollar amounts/timeframes]

**Recommended Actions**
1. [First action with specific steps]
2. [Second action with specific steps]
3. [Third action with specific steps]

**Negotiation Strategy**
[Exact language changes and alternatives with specific wording]

Adjust complexity for ${experienceLevel} level but maintain comprehensive detail and specificity.`;

      const result = await apiService.askClarification(question, context, experienceLevel);

      console.log('🔍 AI Service Response:', {
        success: result.success,
        responseLength: result.response?.length || 0,
        serviceUsed: result.service_used,
        fallback: result.fallback,
        confidenceScore: result.confidence_score
      });

      if (result.success && result.response && result.response.length > 500 && !result.fallback) {
        console.log('✅ Generated HIGH-QUALITY AI document summary with full context');
        return result.response;
      } else {
        console.warn('⚠️ AI service returned insufficient response or used fallback, using enhanced fallback');
        console.warn('Response preview:', result.response?.substring(0, 200));
        return this.createDetailedFallbackExplanation(analysis);
      }
    } catch (error) {
      console.error('Failed to generate jargon-free version:', error);
      return this.createDetailedFallbackExplanation(analysis);
    }
  }

  private createDetailedFallbackExplanation(analysis: AnalysisResult): string {
    if (!analysis || !analysis.analysis_results) {
      return `I'd be happy to explain your legal document in simple terms. However, it looks like the document analysis is still in progress or hasn't been completed yet. 

Once the analysis is finished, I'll be able to tell you:
- What type of document this is and what it's for
- The main risks and benefits
- What you should pay attention to
- Whether you might need professional legal advice

Please wait for the analysis to complete, or try refreshing the page if you think there might be an issue.`;
    }

    const riskLevel = analysis.overall_risk?.level || 'UNKNOWN';
    const totalClauses = analysis.analysis_results?.length || 0;
    const confidence = analysis.overall_risk?.confidence_percentage || 0;

    let explanation = `Here's what I can tell you about your legal document:\n\n`;

    // Document overview
    explanation += `**Document Overview:**\n`;
    explanation += `This document contains ${totalClauses} clause${totalClauses !== 1 ? 's' : ''} that I've analyzed. `;
    explanation += `Overall, I've assessed it as ${riskLevel.toLowerCase()} risk`;
    if (confidence > 0) {
      explanation += ` with ${confidence}% confidence`;
    }
    explanation += `.\n\n`;

    // Risk breakdown
    if (analysis.analysis_results && analysis.analysis_results.length > 0) {
      const riskCounts = {
        red: analysis.analysis_results.filter(r => r.risk_level?.level === 'RED').length,
        yellow: analysis.analysis_results.filter(r => r.risk_level?.level === 'YELLOW').length,
        green: analysis.analysis_results.filter(r => r.risk_level?.level === 'GREEN').length,
      };

      explanation += `**What This Means:**\n`;

      if (riskCounts.red > 0) {
        explanation += `- ${riskCounts.red} clause${riskCounts.red !== 1 ? 's' : ''} need${riskCounts.red === 1 ? 's' : ''} immediate attention (high risk)\n`;
      }

      if (riskCounts.yellow > 0) {
        explanation += `- ${riskCounts.yellow} clause${riskCounts.yellow !== 1 ? 's' : ''} should be reviewed carefully (medium risk)\n`;
      }

      if (riskCounts.green > 0) {
        explanation += `- ${riskCounts.green} clause${riskCounts.green !== 1 ? 's' : ''} appear${riskCounts.green === 1 ? 's' : ''} to be standard and fair (low risk)\n`;
      }

      explanation += `\n`;
    }

    // Recommendations based on risk level
    explanation += `**What You Should Do:**\n`;

    if (riskLevel === 'RED') {
      explanation += `Since this is a high-risk document, I strongly recommend:\n`;
      explanation += `- Have a qualified lawyer review this before signing\n`;
      explanation += `- Pay special attention to the high-risk clauses\n`;
      explanation += `- Consider negotiating problematic terms\n`;
      explanation += `- Don't rush into signing this agreement\n`;
    } else if (riskLevel === 'YELLOW') {
      explanation += `Since this has moderate risk, I recommend:\n`;
      explanation += `- Review the medium-risk clauses carefully\n`;
      explanation += `- Consider getting legal advice if you're unsure\n`;
      explanation += `- Make sure you understand what you're agreeing to\n`;
      explanation += `- Ask questions about anything that seems unclear\n`;
    } else {
      explanation += `This appears to be a lower-risk document, but you should still:\n`;
      explanation += `- Read through all the clauses\n`;
      explanation += `- Make sure you understand your obligations\n`;
      explanation += `- Keep a copy for your records\n`;
      explanation += `- Ask for clarification if needed\n`;
    }

    // Low confidence warning
    if (analysis.overall_risk?.low_confidence_warning) {
      explanation += `\n**Important Note:** The AI analysis has lower confidence in this assessment, so I especially recommend getting professional legal review to be safe.`;
    }

    explanation += `\n\nRemember: This is an AI analysis to help you understand the document better. For important legal decisions, always consult with a qualified attorney who can provide personalized advice for your specific situation.`;

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
        // Build COMPREHENSIVE context with complete clause and document information
        const context = {
          clause: {
            clauseId: clauseId,
            text: clauseData.clause_text, // Full clause text for complete context
            riskLevel: clauseData.risk_level?.level || 'unknown',
            riskScore: clauseData.risk_level?.score || 0,
            severity: clauseData.risk_level?.severity || 'unknown',
            confidence: clauseData.risk_level?.confidence_percentage || 0,
            explanation: clauseData.plain_explanation || '',
            implications: clauseData.legal_implications || [],
            recommendations: clauseData.recommendations || [],
            hasLowConfidence: clauseData.risk_level?.low_confidence_warning || false,
            riskCategories: clauseData.risk_level?.risk_categories || {},
            // Add comprehensive clause-specific data
            reasons: clauseData.risk_level?.reasons || [],
            clauseType: clauseData.clause_type || 'general',
            clauseCategory: clauseData.clause_category || 'standard',
            hasSpecificIssues: (clauseData.risk_level?.score || 0) > 0.6
          },
          document: {
            documentType: 'legal document',
            analysisComplete: true,
            // Add document context for better clause understanding
            overallRisk: 'unknown',
            totalClauses: 1,
            contextVersion: '2.0'
          },
          analysisMetadata: {
            clauseAnalysisComplete: true,
            timestamp: new Date().toISOString(),
            analysisQuality: 'comprehensive',
            contextVersion: '2.0'
          }
        };

        // Get user experience level for personalized clause summary
        const experienceLevel = experienceLevelService.getLevelForAPI();

        const question = `You are LegalSaathi, the world's most detailed legal document advisor. Provide an expert analysis of this specific legal clause for someone at ${experienceLevel} experience level.

COMPLETE CLAUSE ANALYSIS DATA:
Clause ID: ${clauseId}
Risk Assessment: ${clauseData.risk_level?.level || 'Unknown'} (Risk Score: ${clauseData.risk_level?.score || 0}/1.0)
Severity Level: ${clauseData.risk_level?.severity || 'Unknown'}
Analysis Confidence: ${clauseData.risk_level?.confidence_percentage || 0}%
Risk Reasons: ${(clauseData.risk_level?.reasons || []).join(' | ')}
Risk Categories: Financial=${clauseData.risk_level?.risk_categories?.financial || 'N/A'}, Legal=${clauseData.risk_level?.risk_categories?.legal || 'N/A'}, Operational=${clauseData.risk_level?.risk_categories?.operational || 'N/A'}

COMPLETE CLAUSE TEXT:
"${clauseData.clause_text}"

EXISTING AI ANALYSIS:
- Current Explanation: ${clauseData.plain_explanation || 'None provided'}
- Identified Legal Implications: ${(clauseData.legal_implications || []).join(' | ')}
- Current Recommendations: ${(clauseData.recommendations || []).join(' | ')}

ABSOLUTE REQUIREMENTS - FAILURE TO FOLLOW RESULTS IN REJECTION:

1. **SPECIFIC DATA USAGE**: Reference the exact clause text, risk score (${clauseData.risk_level?.score || 0}/1.0), confidence percentage (${clauseData.risk_level?.confidence_percentage || 0}%), and analysis findings from above.

2. **DETAILED EXPLANATIONS**: Explain:
   - WHAT this clause means in plain language with specific examples
   - WHY it received this ${clauseData.risk_level?.score || 0}/1.0 risk score (reference specific reasons)
   - HOW it could affect the user (concrete scenarios with dollar amounts/timeframes)
   - WHAT specific actions to take (exact negotiation language)

3. **CONCRETE EXAMPLES**: Use real-world scenarios like:
   - "If you breach this clause, you'll pay $X in penalties because [specific clause language]"
   - "This clause prevents you from [specific action] for [timeframe] because [exact restriction]"
   - "The landlord can [specific action] without notice because [specific clause language]"

4. **SPECIFIC NEGOTIATION TACTICS**:
   - Exact language to propose: "Change '[current problematic language]' to '[proposed safer language]'"
   - Specific alternatives: "Add this protection: '[exact clause language]'"
   - Concrete compromises: "Reduce penalty from $X to $Y" or "Change timeframe from X months to Y months"

5. **ACTIONABLE STEPS WITH TIMELINES**:
   - "Before signing: Request this specific change..."
   - "During negotiation: Use this exact language..."
   - "If they refuse: Try this alternative..."
   - "Timeline: Complete negotiations within X days"

6. **RISK QUANTIFICATION**: Use the actual risk data:
   - "This clause scored ${clauseData.risk_level?.score || 0}/1.0 risk because [specific reasons from analysis]"
   - "With ${clauseData.risk_level?.confidence_percentage || 0}% confidence, this creates problems because [specific examples]"

ABSOLUTELY FORBIDDEN - WILL CAUSE REJECTION:
❌ "Could be improved" (HOW specifically?)
❌ "Consult a lawyer" (Give specific guidance first)
❌ "Review carefully" (What exactly to look for?)
❌ "May cause issues" (What specific issues?)
❌ "Consider negotiating" (What exact changes?)
❌ "Creates financial disadvantages" (What specific disadvantages with examples?)
❌ "Main issues:" without specific details
❌ "Lacks specific criteria" without proposing exact criteria

REQUIRED FORMAT - Use clear sections with proper formatting:

**Clause Purpose**
[What this clause does and why it exists]

**Risk Analysis**
[Why it scored ${clauseData.risk_level?.score || 0}/1.0 with specific examples]

**Real Impact**
[Concrete examples of how this affects the user with specific scenarios]

**Key Issues**
- [Issue 1 with specific details]
- [Issue 2 with specific details]
- [Issue 3 with specific details]

**Recommended Actions**
1. [First action with specific steps]
2. [Second action with specific steps]
3. [Third action with specific steps]

**Negotiation Strategy**
[Exact language changes to propose with specific wording]

Tailor complexity for ${experienceLevel} level but maintain comprehensive detail and specificity.`;

        const result = await apiService.askClarification(question, context, experienceLevel);
        
        console.log(`🔍 Clause ${clauseId} AI Service Response:`, {
          success: result.success,
          responseLength: result.response?.length || 0,
          serviceUsed: result.service_used,
          fallback: result.fallback,
          confidenceScore: result.confidence_score
        });

        if (result.success && result.response && result.response.length > 300 && !result.fallback) {
          console.log(`✅ Generated HIGH-QUALITY AI clause summary for clause ${clauseId} with full context`);
          plainLanguage = result.response;
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
      return `I'm having trouble analyzing Clause ${clauseId} right now. Please try refreshing the analysis or contact support if the issue persists.`;
    }

    const riskLevel = clauseData.risk_level?.level || 'UNKNOWN';
    const clauseText = clauseData.clause_text || '';
    const explanation = clauseData.plain_explanation || '';
    const implications = clauseData.legal_implications || [];
    const recommendations = clauseData.recommendations || [];

    let fallbackExplanation = `**Clause ${clauseId} Summary:**\n\n`;

    // Add clause text if available
    if (clauseText) {
      fallbackExplanation += `**What it says:** "${clauseText.substring(0, 200)}${clauseText.length > 200 ? '...' : ''}"\n\n`;
    }

    // Add risk assessment
    fallbackExplanation += `**Risk Level:** ${riskLevel.toLowerCase()}\n\n`;

    // Add explanation if available
    if (explanation) {
      fallbackExplanation += `**What it means:** ${explanation}\n\n`;
    }

    // Add implications
    if (implications.length > 0) {
      fallbackExplanation += `**Key implications:**\n`;
      implications.slice(0, 3).forEach((implication: string, index: number) => {
        fallbackExplanation += `${index + 1}. ${implication}\n`;
      });
      fallbackExplanation += `\n`;
    }

    // Add recommendations
    if (recommendations.length > 0) {
      fallbackExplanation += `**Recommendations:**\n`;
      recommendations.slice(0, 3).forEach((rec: string, index: number) => {
        fallbackExplanation += `${index + 1}. ${rec}\n`;
      });
      fallbackExplanation += `\n`;
    }

    // Add general guidance based on risk level
    if (riskLevel === 'RED') {
      fallbackExplanation += `**⚠️ Important:** This is a high-risk clause. Consider having a lawyer review this specific section before proceeding.`;
    } else if (riskLevel === 'YELLOW') {
      fallbackExplanation += `**⚡ Note:** This clause has moderate risk. Make sure you understand what you're agreeing to.`;
    } else if (riskLevel === 'GREEN') {
      fallbackExplanation += `**✅ Good news:** This clause appears to be standard and fair.`;
    } else {
      fallbackExplanation += `**❓ Unclear:** I need more information to properly assess this clause. Consider getting professional advice.`;
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