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
import type { AnalysisResult } from '../App';

interface DocumentSummaryProps {
  analysis: AnalysisResult;
  className?: string;
}

export function DocumentSummary({ analysis, className = '' }: DocumentSummaryProps) {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [allExpanded, setAllExpanded] = useState(true);

  useEffect(() => {
    const unsubscribe = summarizationService.subscribe(() => {
      setSummary(summarizationService.getDocumentSummary());
      setIsLoading(summarizationService.isLoading('document'));
    });

    // Initial load
    setSummary(summarizationService.getDocumentSummary());
    
    // Auto-generate summary if not exists
    if (!summarizationService.getDocumentSummary()) {
      handleGenerateSummary();
    }

    return unsubscribe;
  }, [analysis]);

  const handleGenerateSummary = async () => {
    await summarizationService.generateDocumentSummary(analysis);
  };

  const handleRefreshSummary = () => {
    summarizationService.clearDocumentSummary();
    handleGenerateSummary();
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
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
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
                <p className="text-slate-200 leading-relaxed">{summary.jargonFreeVersion}</p>
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
                <p className="text-slate-200 leading-relaxed">{summary.riskSummary}</p>
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
                <p className="text-slate-200 leading-relaxed">{summary.simplifiedExplanation}</p>
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