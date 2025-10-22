import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Lightbulb, 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  RefreshCw,
  BookOpen,
  Target,
  Shield
} from 'lucide-react';
import { summarizationService, type SummaryData } from '../services/summarizationService';
import { MarkdownRenderer } from '../utils/markdownRenderer';

import type { AnalysisResult } from '../App';

interface DocumentSummaryProps {
  analysis: AnalysisResult;
  className?: string;
}

export function DocumentSummary({ analysis, className = '' }: DocumentSummaryProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [allExpanded, setAllExpanded] = useState(true);
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Subscribe to summarization service state changes
  useEffect(() => {
    // Clear caches when analysis changes to ensure fresh summaries
    if (analysis) {
      console.log('🔄 New analysis detected, clearing summary caches');
      summarizationService.clearCachesForNewAnalysis();
    }

    const unsubscribe = summarizationService.subscribe(() => {
      const currentSummary = summarizationService.getDocumentSummary();
      const loading = summarizationService.isLoading('document');
      
      setSummary(currentSummary);
      setIsLoading(loading);
    });

    // Initialize with current state
    const currentSummary = summarizationService.getDocumentSummary();
    const loading = summarizationService.isLoading('document');
    
    setSummary(currentSummary);
    setIsLoading(loading);

    // Generate summary if not available
    if (!currentSummary && !loading && analysis) {
      generateInitialSummary();
    }

    return unsubscribe;
  }, [analysis]);

  const generateInitialSummary = async () => {
    if (!analysis) return;
    
    try {
      await summarizationService.generateDocumentSummary(analysis);
    } catch (error) {
      console.error('Failed to generate initial summary:', error);
      // Fallback to local generation if AI service fails
      setSummary(generateFallbackSummary());
    }
  };

  // Fallback summary generation for when AI service is unavailable
  const generateFallbackSummary = (): SummaryData => {
    const { overall_risk, analysis_results } = analysis;
    
    // Extract key points from clause assessments
    const keyPoints = [
      `Document contains ${analysis_results.length} clauses analyzed`,
      `Overall risk level: ${overall_risk.level} (${(overall_risk.score * 100).toFixed(0)}% risk score)`,
      `Analysis confidence: ${overall_risk.confidence_percentage}%`
    ];

    // Add specific risk insights from reasons
    if (overall_risk.reasons && overall_risk.reasons.length > 0) {
      keyPoints.push(...overall_risk.reasons.slice(0, 2)); // Top 2 risk reasons
    }

    // Generate risk summary from actual data
    const riskSummary = `This document has been assessed as ${overall_risk.level.toLowerCase()} risk with a score of ${overall_risk.score.toFixed(2)}/1.0. ${overall_risk.reasons ? overall_risk.reasons[0] : 'Standard risk assessment completed.'}`;

    // Extract recommendations from clause assessments
    const recommendations: string[] = [];
    const highRiskClauses = analysis_results.filter(clause => clause.risk_level.level === 'RED');
    const mediumRiskClauses = analysis_results.filter(clause => clause.risk_level.level === 'YELLOW');
    
    if (highRiskClauses.length > 0) {
      recommendations.push(`Review ${highRiskClauses.length} high-risk clauses carefully`);
      recommendations.push(...highRiskClauses.slice(0, 2).flatMap(clause => clause.recommendations.slice(0, 1)));
    }
    
    if (mediumRiskClauses.length > 0) {
      recommendations.push(`Consider negotiating ${mediumRiskClauses.length} medium-risk clauses`);
    }

    // Generate simplified explanation
    const simplifiedExplanation = `This ${analysis.document_type?.replace('_', ' ') || 'document'} contains ${analysis_results.length} clauses. ${highRiskClauses.length} clauses need careful attention due to high risk, while ${mediumRiskClauses.length} clauses have moderate risk that should be reviewed.`;

    // Generate jargon-free version
    const jargonFreeVersion = `In simple terms: This document ${overall_risk.level === 'RED' ? 'has significant risks that need attention' : overall_risk.level === 'YELLOW' ? 'has some risks but is generally acceptable' : 'appears to have standard, low-risk terms'}. ${highRiskClauses.length > 0 ? `Pay special attention to ${highRiskClauses.length} clauses that could cause problems.` : 'Most clauses appear fair and standard.'}`;

    return {
      keyPoints,
      riskSummary,
      recommendations: recommendations.slice(0, 5), // Limit to top 5
      simplifiedExplanation,
      jargonFreeVersion,
      timestamp: new Date()
    };
  };

  const handleRefreshSummary = async () => {
    console.log('Refreshing document summary with AI service');
    try {
      await summarizationService.forceRegenerateDocumentSummary(analysis);
      // The component will re-render automatically due to the service state change
    } catch (error) {
      console.error('Failed to refresh summary:', error);
    }
  };

  const toggleSection = (section: string) => {
    if (allExpanded) {
      setAllExpanded(false);
      setExpandedSection(section);
    } else {
      setExpandedSection(expandedSection === section ? null : section);
    }
  };

  const toggleAllSections = () => {
    setAllExpanded(!allExpanded);
    setExpandedSection(null);
  };

  if (isLoading) {
    return (
      <div className={`document-summary-loading ${className}`}>
        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
          <div className="flex items-center justify-center space-x-3">
            <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
            <span className="text-white">Generating jargon-free summary...</span>
          </div>
        </div>
      </div>
    );
  }

  const handleGenerateSummary = async () => {
    if (!analysis) return;
    
    try {
      setIsLoading(true);
      await summarizationService.generateDocumentSummary(analysis);
    } catch (error) {
      console.error('Failed to generate summary:', error);
      // Fallback to local generation
      setSummary(generateFallbackSummary());
    } finally {
      setIsLoading(false);
    }
  };

  if (!summary) {
    return (
      <div className={`document-summary-error ${className}`}>
        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
          <div className="text-center">
            <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Summary Not Available</h3>
            <p className="text-slate-400 mb-4">Unable to generate document summary</p>
            <button
              onClick={handleGenerateSummary}
              disabled={isLoading}
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              {isLoading ? 'Generating...' : 'Try Again'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`document-summary ${className}`}
    >
      <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-2xl p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <BookOpen className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Document Summary</h2>
              <p className="text-slate-400 text-sm">Jargon-free explanation of your document</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleAllSections}
              className="inline-flex items-center px-3 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm"
            >
              {allExpanded ? 'Collapse All' : 'Expand All'}
            </button>
            <button
              onClick={handleRefreshSummary}
              className="inline-flex items-center px-3 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>

        {/* Summary Sections */}
        <div className="space-y-4">
          {/* Overview Section */}
          <div className="summary-section">
            <button
              onClick={() => toggleSection('overview')}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <Lightbulb className="w-5 h-5 text-yellow-400" />
                <span className="font-semibold text-white">What This Document Means</span>
              </div>
              <div className="text-slate-400">
                {expandedSection === 'overview' ? '−' : '+'}
              </div>
            </button>
            
            {(allExpanded || expandedSection === 'overview') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg"
              >
                <MarkdownRenderer text={summary.jargonFreeVersion} />
              </motion.div>
            )}
          </div>

          {/* Key Points Section */}
          <div className="summary-section">
            <button
              onClick={() => toggleSection('keyPoints')}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <Target className="w-5 h-5 text-green-400" />
                <span className="font-semibold text-white">Key Points</span>
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
                  {summary.keyPoints.length}
                </span>
              </div>
              <div className="text-slate-400">
                {expandedSection === 'keyPoints' ? '−' : '+'}
              </div>
            </button>
            
            {(allExpanded || expandedSection === 'keyPoints') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-4 bg-green-500/10 border border-green-500/30 rounded-lg"
              >
                <ul className="space-y-2">
                  {summary.keyPoints.map((point, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span className="text-slate-200">{point}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </div>

          {/* Risk Summary Section */}
          <div className="summary-section">
            <button
              onClick={() => toggleSection('risks')}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <Shield className="w-5 h-5 text-orange-400" />
                <span className="font-semibold text-white">Risk Assessment</span>
              </div>
              <div className="text-slate-400">
                {expandedSection === 'risks' ? '−' : '+'}
              </div>
            </button>
            
            {(allExpanded || expandedSection === 'risks') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg"
              >
                <MarkdownRenderer text={summary.riskSummary} />
              </motion.div>
            )}
          </div>

          {/* Recommendations Section */}
          <div className="summary-section">
            <button
              onClick={() => toggleSection('recommendations')}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <AlertTriangle className="w-5 h-5 text-cyan-400" />
                <span className="font-semibold text-white">What You Should Do</span>
                <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded-full">
                  {summary.recommendations.length}
                </span>
              </div>
              <div className="text-slate-400">
                {expandedSection === 'recommendations' ? '−' : '+'}
              </div>
            </button>
            
            {(allExpanded || expandedSection === 'recommendations') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg"
              >
                <ul className="space-y-3">
                  {summary.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <div className="w-6 h-6 bg-cyan-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-cyan-400 text-xs font-bold">{index + 1}</span>
                      </div>
                      <span className="text-slate-200">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </div>

          {/* Simplified Explanation Section */}
          <div className="summary-section">
            <button
              onClick={() => toggleSection('simplified')}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-purple-400" />
                <span className="font-semibold text-white">Simple Explanation</span>
              </div>
              <div className="text-slate-400">
                {expandedSection === 'simplified' ? '−' : '+'}
              </div>
            </button>
            
            {(allExpanded || expandedSection === 'simplified') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg"
              >
                <MarkdownRenderer text={summary.simplifiedExplanation} />
              </motion.div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>Summary generated: {summary.timestamp.toLocaleString()}</span>
            <span className="flex items-center space-x-1">
              <Lightbulb className="w-4 h-4" />
              <span>AI-powered jargon-free analysis</span>
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}