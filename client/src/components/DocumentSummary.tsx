import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Lightbulb, 
  Loader2, 
  RefreshCw,
  BookOpen,
  Languages
} from 'lucide-react';
import { summarizationService, type SummaryData } from '../services/summarizationService';
import { TranslatedContentRenderer } from '../utils/markdownRenderer';
import GlobalTranslationPanel from './GlobalTranslationPanel';
import type { DocumentSummaryContent } from '../services/documentSummaryTranslationService';

import type { AnalysisResult } from '../App';

interface DocumentSummaryProps {
  analysis: AnalysisResult;
  className?: string;
}

export function DocumentSummary({ analysis, className = '' }: DocumentSummaryProps) {

  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);
  const [translatedSummary, setTranslatedSummary] = useState<DocumentSummaryContent | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState('en');

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
    
    // Generate simple 5-6 line summary about what the document contains
    const documentType = analysis.document_type?.replace('_', ' ') || 'legal document';
    const clauseCount = analysis_results.length;
    const riskLevel = overall_risk.level.toLowerCase();
    
    const simpleSummary = `This is a ${documentType} containing ${clauseCount} clauses that have been analyzed for legal risks. The document has been assessed as ${riskLevel} risk overall. ${clauseCount > 0 ? `The analysis covers key terms, obligations, and potential issues within the document.` : ''} ${overall_risk.confidence_percentage < 80 ? 'Consider professional legal review for important decisions.' : 'The AI analysis provides good confidence in the assessment.'} This summary gives you a quick overview of the document's content and risk profile.`;

    return {
      keyPoints: [simpleSummary],
      riskSummary: simpleSummary,
      recommendations: [simpleSummary],
      simplifiedExplanation: simpleSummary,
      jargonFreeVersion: simpleSummary,
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



  const handleTranslationComplete = (translatedContent: DocumentSummaryContent, language: string) => {
    setTranslatedSummary(translatedContent);
    setCurrentLanguage(language);
  };

  const toggleTranslationPanel = () => {
    setShowTranslation(!showTranslation);
  };

  // Get the content to display (translated or original)
  const getDisplayContent = () => {
    if (currentLanguage === 'en' || !translatedSummary) {
      return summary;
    }

    // Map translated content to SummaryData format
    return {
      keyPoints: translatedSummary.keyPoints || translatedSummary.key_points || summary?.keyPoints || [],
      riskSummary: translatedSummary.riskSummary || translatedSummary.risk_assessment || summary?.riskSummary || '',
      recommendations: translatedSummary.recommendations || translatedSummary.what_you_should_do || summary?.recommendations || [],
      simplifiedExplanation: translatedSummary.simplifiedExplanation || translatedSummary.simple_explanation || summary?.simplifiedExplanation || '',
      jargonFreeVersion: translatedSummary.jargonFreeVersion || translatedSummary.what_this_document_means || summary?.jargonFreeVersion || '',
      timestamp: summary?.timestamp || new Date()
    };
  };

  const displayContent = getDisplayContent();

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
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.35 }}
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
              <p className="text-slate-400 text-sm">
                {currentLanguage === 'en' 
                  ? 'Simple overview of what this document contains' 
                  : `Translated to ${currentLanguage.toUpperCase()}`
                }
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleTranslationPanel}
              className={`inline-flex items-center px-3 py-2 rounded-lg transition-colors text-sm ${
                showTranslation 
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Languages className="w-4 h-4 mr-2" />
              Translate
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

        {/* Translation Panel */}
        {showTranslation && summary && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6"
          >
            <GlobalTranslationPanel
              summaryContent={{
                what_this_document_means: summary.jargonFreeVersion,
                key_points: summary.keyPoints,
                risk_assessment: summary.riskSummary,
                what_you_should_do: summary.recommendations,
                simple_explanation: summary.simplifiedExplanation
              }}
              onTranslationComplete={handleTranslationComplete}
            />
          </motion.div>
        )}

        {/* Simple Summary Display */}
        <div className="p-6 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl">
          <div className="flex items-start space-x-3">
            <FileText className="w-6 h-6 text-blue-400 mt-1 flex-shrink-0" />
            <div className="flex-1">
              {currentLanguage === 'en' ? (
                <div className="text-slate-200 leading-relaxed text-lg">
                  {displayContent?.jargonFreeVersion || 'Document summary not available'}
                </div>
              ) : (
                <TranslatedContentRenderer content={displayContent?.jargonFreeVersion || 'Document summary not available'} />
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>Summary generated: {displayContent?.timestamp?.toLocaleString()}</span>
            <span className="flex items-center space-x-1">
              <Lightbulb className="w-4 h-4" />
              <span>
                {currentLanguage === 'en' 
                  ? 'AI-powered jargon-free analysis' 
                  : `AI-powered analysis • Translated to ${currentLanguage.toUpperCase()}`
                }
              </span>
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}