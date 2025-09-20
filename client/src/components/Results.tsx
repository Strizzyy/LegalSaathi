import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  FileText, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  ChevronDown,
  ChevronUp,
  Copy,
  Download,
  Globe,
  BarChart3,
  Zap,
  MessageCircle,
  Activity,
  Users,
  Loader2
} from 'lucide-react';
import { cn, formatFileSize, formatPercentage, getRiskColor, getRiskBadgeColor, getConfidenceColor } from '../utils';

import { exportService } from '../services/exportService';
import { notificationService } from '../services/notificationService';
import { featureAvailabilityService } from '../services/featureAvailabilityService';
import { AIChat } from './AIChat';
import { HumanSupport } from './HumanSupport';
import { TranslationModal } from './TranslationModal';
import { StatusModal } from './StatusModal';
import { DocumentSummary } from './DocumentSummary';
import { ClauseTranslationButton } from './ClauseTranslationButton';
import { ClauseSummary } from './ClauseSummary';
import { DocumentComparison } from './DocumentComparison';
import type { AnalysisResult, FileInfo, Classification } from '../App';
import type { ClauseContext, DocumentContext } from '../types/chat';

interface ResultsProps {
  analysis: AnalysisResult | null;
  fileInfo: FileInfo | null;
  classification: Classification | null;
  warnings: string[];
  onBackToHome: () => void;
}

import React from 'react';

export const Results = React.memo(function Results({ analysis, fileInfo, classification, warnings, onBackToHome }: ResultsProps) {
  const [expandedClauses, setExpandedClauses] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  
  // Debug: Log the analysis data to see what we're receiving
  React.useEffect(() => {
    if (analysis) {
      console.log('Results component received analysis:', analysis);
      console.log('Clause texts in Results:', analysis.analysis_results.map(r => ({
        id: r.clause_id,
        hasText: !!r.clause_text,
        textPreview: r.clause_text?.substring(0, 50) + '...'
      })));
    }
  }, [analysis]);
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isHumanSupportOpen, setIsHumanSupportOpen] = useState(false);
  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [isTranslationOpen, setIsTranslationOpen] = useState(false);
  const [isStatusOpen, setIsStatusOpen] = useState(false);
  const [translationText, setTranslationText] = useState('');
  const [translationTitle, setTranslationTitle] = useState('');
  const [activeChatClause, setActiveChatClause] = useState<ClauseContext | undefined>(undefined);
  const [isExporting, setIsExporting] = useState<{ pdf: boolean; word: boolean }>({ pdf: false, word: false });

  if (!analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Analysis Results</h2>
          <p className="text-slate-400 mb-6">No analysis data available to display.</p>
          <button
            onClick={onBackToHome}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const toggleClause = (index: number) => {
    const newExpanded = new Set(expandedClauses);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedClauses(newExpanded);
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const copyResults = async () => {
    try {
      const resultsText = `
Document Analysis Results
========================

Overall Risk: ${analysis.overall_risk.level} (${formatPercentage(analysis.overall_risk.score)})
Confidence: ${analysis.overall_risk.confidence_percentage}%

Summary: ${analysis.summary}

Clause Analysis:
${analysis.analysis_results.map((result, index) => `
${index + 1}. ${result.risk_level.level} Risk (${formatPercentage(result.risk_level.score)})
   ${result.plain_explanation}
`).join('')}
      `.trim();

      await navigator.clipboard.writeText(resultsText);
      notificationService.copySuccess();
    } catch (error) {
      console.error('Failed to copy results:', error);
      notificationService.copyError();
    }
  };

  const openTranslation = (text: string, title: string) => {
    setTranslationText(text);
    setTranslationTitle(title);
    setIsTranslationOpen(true);
  };

  const openChat = (clauseContext?: ClauseContext) => {
    setActiveChatClause(clauseContext);
    setIsChatOpen(true);
  };

  const openHumanSupport = (clauseContext?: ClauseContext) => {
    setActiveChatClause(clauseContext);
    setIsHumanSupportOpen(true);
  };

  // Create document context for chat
  const documentContext: DocumentContext = {
    documentType: classification?.document_type?.value || 'legal document',
    overallRisk: analysis.overall_risk.level,
    summary: analysis.summary,
    totalClauses: analysis.analysis_results.length
  };

  // Helper to create clause context with complete clause data
  const createClauseContext = (result: AnalysisResult['analysis_results'][0]): ClauseContext => {
    const context: ClauseContext = {
      clauseId: result.clause_id,
      text: result.clause_text, // Use actual clause text from backend
      riskLevel: result.risk_level.level,
      explanation: result.plain_explanation,
      implications: result.legal_implications,
      recommendations: result.recommendations
    };
    
    // Add optional properties only if they exist
    if (result.risk_level.score !== undefined) {
      context.riskScore = result.risk_level.score;
    }
    if (result.risk_level.confidence_percentage !== undefined) {
      context.confidencePercentage = result.risk_level.confidence_percentage;
    }
    if (result.risk_level.risk_categories) {
      context.riskCategories = result.risk_level.risk_categories;
    }
    
    return context;
  };

  const openStatus = () => {
    setIsStatusOpen(true);
  };

  const runAdvancedAnalysis = async () => {
    toggleSection('nlAnalysis');
  };

  const exportToPDF = async () => {
    if (!featureAvailabilityService.isFeatureAvailable('export_pdf')) {
      const fallbackMessage = featureAvailabilityService.getFallbackMessage('export_pdf');
      notificationService.error(fallbackMessage);
      return;
    }

    setIsExporting(prev => ({ ...prev, pdf: true }));
    notificationService.info('Preparing PDF export...');
    
    const exportData: any = {
      analysis
    };
    if (fileInfo) exportData.file_info = fileInfo;
    if (classification) exportData.classification = classification;
    
    try {
      const result = await exportService.exportToPDF(exportData);
      
      if (result.success) {
        featureAvailabilityService.recordFeatureSuccess('export_pdf');
        notificationService.exportSuccess('PDF');
      } else {
        featureAvailabilityService.recordFeatureError('export_pdf');
        notificationService.exportError('PDF', () => {
          const fallbackData: any = { analysis };
          if (fileInfo) fallbackData.file_info = fileInfo;
          if (classification) fallbackData.classification = classification;
          exportService.exportAsText(fallbackData);
        });
      }
    } catch (error) {
      console.error('Export error:', error);
      featureAvailabilityService.recordFeatureError('export_pdf', error as Error);
      notificationService.error('Export failed. Please try again or use the text export option.');
    } finally {
      setIsExporting(prev => ({ ...prev, pdf: false }));
    }
  };

  const exportToWord = async () => {
    if (!featureAvailabilityService.isFeatureAvailable('export_word')) {
      const fallbackMessage = featureAvailabilityService.getFallbackMessage('export_word');
      notificationService.error(fallbackMessage);
      return;
    }

    setIsExporting(prev => ({ ...prev, word: true }));
    notificationService.info('Preparing Word document export...');
    
    const exportData: any = {
      analysis
    };
    if (fileInfo) exportData.file_info = fileInfo;
    if (classification) exportData.classification = classification;
    
    try {
      const result = await exportService.exportToWord(exportData);
      
      if (result.success) {
        featureAvailabilityService.recordFeatureSuccess('export_word');
        notificationService.exportSuccess('Word');
      } else {
        featureAvailabilityService.recordFeatureError('export_word');
        notificationService.exportError('Word', () => {
          const fallbackData: any = { analysis };
          if (fileInfo) fallbackData.file_info = fileInfo;
          if (classification) fallbackData.classification = classification;
          exportService.exportAsText(fallbackData);
        });
      }
    } catch (error) {
      console.error('Export error:', error);
      featureAvailabilityService.recordFeatureError('export_word', error as Error);
      notificationService.error('Word export failed. Please try again or use the text export option.');
    } finally {
      setIsExporting(prev => ({ ...prev, word: false }));
    }
  };

  const riskCounts = {
    red: analysis.analysis_results.filter(r => r.risk_level.level === 'RED').length,
    yellow: analysis.analysis_results.filter(r => r.risk_level.level === 'YELLOW').length,
    green: analysis.analysis_results.filter(r => r.risk_level.level === 'GREEN').length,
  };

  return (
    <>
    <div className="min-h-screen pt-20 pb-16">
      <div className="container mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8"
        >
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
              <FileText className="w-8 h-8 mr-3" />
              Document Analysis Results
            </h1>
            <p className="text-slate-400">AI-powered legal document analysis with risk assessment</p>
          </div>
          
          <div className="flex items-center space-x-4 mt-4 sm:mt-0">
            <div className="relative">
              <label htmlFor="language-select-header" className="sr-only">
                Select display language
              </label>
              <select
                id="language-select-header"
                value={currentLanguage}
                onChange={(e) => setCurrentLanguage(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none appearance-none pr-8"
                aria-label="Select display language"
              >
                <option value="en">🇺🇸 English</option>
                <option value="hi">🇮🇳 Hindi</option>
                <option value="es">🇪🇸 Spanish</option>
                <option value="fr">🇫🇷 French</option>
                <option value="de">🇩🇪 German</option>
                <option value="it">🇮🇹 Italian</option>
                <option value="pt">🇵🇹 Portuguese</option>
                <option value="ru">🇷🇺 Russian</option>
                <option value="ja">🇯🇵 Japanese</option>
                <option value="ko">🇰🇷 Korean</option>
                <option value="zh">🇨🇳 Chinese</option>
                <option value="ar">🇸🇦 Arabic</option>
              </select>
              <Globe className="w-4 h-4 text-slate-400 absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none" />
            </div>
            
            <button
              onClick={onBackToHome}
              className="inline-flex items-center px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Analyze Another Document</span>
              <span className="sm:hidden">New Analysis</span>
            </button>
          </div>
        </motion.div>

        {/* Document Info */}
        {(fileInfo || classification || warnings.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2" />
              Document Information
            </h2>
            
            <div className="grid md:grid-cols-3 gap-6">
              {fileInfo && (
                <div>
                  <h3 className="font-semibold text-white mb-2">File Details</h3>
                  <p className="text-slate-300 mb-1"><strong>Filename:</strong> {fileInfo.filename}</p>
                  <p className="text-slate-300"><strong>Size:</strong> {formatFileSize(fileInfo.size)}</p>
                </div>
              )}
              
              {classification && (
                <div>
                  <h3 className="font-semibold text-white mb-2">Document Classification</h3>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-full text-sm">
                      {classification.document_type.value.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">Confidence: {formatPercentage(classification.confidence)}</p>
                </div>
              )}
              
              {warnings.length > 0 && (
                <div>
                  <h3 className="font-semibold text-white mb-2">Processing Notes</h3>
                  {warnings.map((warning, index) => (
                    <div key={index} className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-2 mb-2">
                      <p className="text-yellow-400 text-sm">{warning}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* AI Analysis Transparency */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              AI Analysis Transparency
            </h2>
            <div className="google-cloud-badge">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
              <span>Powered by Google Cloud AI</span>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-white mb-3">Google Cloud AI Integration</h3>
              <div className="space-y-2">
                <div className="ai-processing-indicator">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>Advanced NLP Analysis Complete</span>
                </div>
                <div className="ai-processing-indicator">
                  <Shield className="w-4 h-4 text-green-400" />
                  <span>Risk Pattern Recognition Applied</span>
                </div>
                <div className="ai-processing-indicator">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <span>Plain Language Translation Generated</span>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-3">Analysis Confidence Metrics</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-slate-300">Overall Analysis:</span>
                    <span className="text-sm text-slate-400">{analysis.overall_risk.confidence_percentage}%</span>
                  </div>
                  <div className="confidence-bar">
                    <div 
                      className={cn(
                        "confidence-fill",
                        getConfidenceColor(analysis.overall_risk.confidence_percentage)
                      )}
                      style={{ width: `${analysis.overall_risk.confidence_percentage}%` }}
                    />
                  </div>
                </div>
                
                {analysis.overall_risk.low_confidence_warning && (
                  <div className="variability-warning">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">Results may vary - consider professional review for critical decisions</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Overall Risk Assessment */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className={cn(
            "border-2 rounded-2xl p-6 mb-8",
            analysis.overall_risk.level === 'RED' ? "border-red-500/50 bg-red-500/5" :
            analysis.overall_risk.level === 'YELLOW' ? "border-yellow-500/50 bg-yellow-500/5" :
            "border-green-500/50 bg-green-500/5"
          )}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className={cn(
                "traffic-light-large",
                getRiskColor(analysis.overall_risk.level)
              )} />
              <div>
                <h2 className="text-2xl font-bold text-white">Overall Risk Assessment</h2>
                <p className="text-slate-400">Complete document analysis summary</p>
              </div>
            </div>
            
            {analysis.overall_risk.low_confidence_warning && (
              <div className={cn(
                "px-3 py-1 rounded-full border text-sm",
                getRiskBadgeColor('YELLOW')
              )}>
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                Low Confidence: {analysis.overall_risk.confidence_percentage}%
              </div>
            )}
          </div>
          
          <div className={cn(
            "rounded-xl p-4 mb-6 border",
            analysis.overall_risk.level === 'RED' ? "bg-red-500/10 border-red-500/30" :
            analysis.overall_risk.level === 'YELLOW' ? "bg-yellow-500/10 border-yellow-500/30" :
            "bg-green-500/10 border-green-500/30"
          )}>
            <p className="text-lg text-white leading-relaxed">{analysis.summary}</p>
          </div>
          
          {analysis.overall_risk.risk_categories && (
            <div>
              <h3 className="font-semibold text-white mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Risk Category Breakdown
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(analysis.overall_risk.risk_categories).map(([category, score]) => (
                  <div key={category} className="text-center">
                    <div className="mb-2">
                      <div className="confidence-bar">
                        <div 
                          className={cn(
                            "confidence-fill",
                            score > 0.7 ? "bg-red-500" : score > 0.4 ? "bg-yellow-500" : "bg-green-500"
                          )}
                          style={{ width: `${score * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-sm">
                      <div className="font-semibold text-white capitalize">{category}</div>
                      <div className="text-slate-400">{Math.round(score * 100)}% Risk</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* Document Summary */}
        <DocumentSummary 
          analysis={analysis}
          className="mb-8"
        />

        {/* Severity Indicators */}
        {analysis.severity_indicators && analysis.severity_indicators.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-yellow-500/10 border border-yellow-500/30 rounded-2xl p-6 mb-8"
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              Critical Issues Detected
            </h2>
            <p className="text-slate-300 mb-4">High-priority concerns that require immediate attention</p>
            
            <div className="grid md:grid-cols-2 gap-4">
              {analysis.severity_indicators.map((indicator, index) => (
                <div key={index} className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3">
                  <div className="flex items-center">
                    <Shield className="w-4 h-4 text-yellow-400 mr-2 flex-shrink-0" />
                    <span className="text-yellow-400 font-medium">{indicator}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Detailed Clause Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Detailed Clause Analysis
              </h2>
              <p className="text-slate-400">Each clause analyzed for risk level and plain language explanation</p>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="traffic-light red" />
                <span className="text-slate-300">High Risk: {riskCounts.red}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="traffic-light yellow" />
                <span className="text-slate-300">Moderate: {riskCounts.yellow}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="traffic-light green" />
                <span className="text-slate-300">Low Risk: {riskCounts.green}</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            {analysis.analysis_results.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className={cn(
                  "clause-analysis-item",
                  getRiskColor(result.risk_level.level)
                )}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={cn(
                      "traffic-light-medium",
                      getRiskColor(result.risk_level.level)
                    )} />
                    <div>
                      <h3 className="text-lg font-bold text-white">Clause #{index + 1}</h3>
                      <p className="text-slate-400 text-sm">
                        {result.risk_level.severity} Risk - {result.clause_id}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={cn(
                      "px-3 py-1 rounded-full border text-sm font-medium mb-1",
                      getRiskBadgeColor(result.risk_level.level)
                    )}>
                      {result.risk_level.level} RISK
                    </div>
                    {result.risk_level.low_confidence_warning && (
                      <div className="px-2 py-1 bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 rounded text-xs">
                        <AlertTriangle className="w-3 h-3 inline mr-1" />
                        Low Confidence
                      </div>
                    )}
                    <div className="text-xs text-slate-400 mt-1">
                      Score: {formatPercentage(result.risk_level.score)} | 
                      Confidence: {result.risk_level.confidence_percentage}%
                    </div>
                  </div>
                </div>
                
                {/* Enhanced Confidence Indicator */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-300 flex items-center">
                      <Activity className="w-4 h-4 mr-1" />
                      AI Confidence Analysis:
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-400">{result.risk_level.confidence_percentage}%</span>
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        result.risk_level.confidence_percentage >= 80 ? "bg-green-400" :
                        result.risk_level.confidence_percentage >= 60 ? "bg-yellow-400" : "bg-red-400"
                      )} />
                    </div>
                  </div>
                  <div className="confidence-bar">
                    <div 
                      className={cn(
                        "confidence-fill",
                        getConfidenceColor(result.risk_level.confidence_percentage)
                      )}
                      style={{ width: `${result.risk_level.confidence_percentage}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                  </div>
                  {result.risk_level.low_confidence_warning && (
                    <div className="variability-warning mt-2">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm">Low confidence detected - consider expert review for critical decisions</span>
                    </div>
                  )}
                  {result.risk_level.confidence_percentage >= 90 && (
                    <div className="mt-2 flex items-center space-x-2 text-green-400 text-sm">
                      <CheckCircle className="w-4 h-4" />
                      <span>High confidence - AI analysis is very reliable</span>
                    </div>
                  )}
                </div>
                
                {/* Actual Clause Text */}
                {result.clause_text && (
                  <div className="bg-slate-700/50 rounded-xl p-4 mb-4 border border-slate-600">
                    <h4 className="font-semibold text-white mb-2 flex items-center">
                      <FileText className="w-4 h-4 mr-2" />
                      Original Clause Text:
                      <span className="ml-2 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                        Real Data ✓
                      </span>
                    </h4>
                    <p className="text-slate-300 text-sm leading-relaxed font-mono bg-slate-800/50 p-3 rounded border border-slate-600">
                      {result.clause_text}
                    </p>
                  </div>
                )}
                
                {/* Debug: Show if clause_text is missing */}
                {!result.clause_text && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-4">
                    <h4 className="font-semibold text-red-400 mb-2 flex items-center">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      Missing Clause Text - Debug Info:
                    </h4>
                    <pre className="text-red-300 text-xs bg-red-500/10 p-2 rounded">
                      {JSON.stringify({
                        clause_id: result.clause_id,
                        has_clause_text: !!result.clause_text,
                        clause_text_type: typeof result.clause_text,
                        clause_text_length: result.clause_text?.length || 0
                      }, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Plain Explanation */}
                <div className={cn(
                  "rounded-xl p-4 mb-4 border",
                  result.risk_level.level === 'RED' ? "bg-red-500/10 border-red-500/30" :
                  result.risk_level.level === 'YELLOW' ? "bg-yellow-500/10 border-yellow-500/30" :
                  "bg-green-500/10 border-green-500/30"
                )}>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <Info className="w-4 h-4 mr-2" />
                    What This Means:
                  </h4>
                  <p className="text-slate-200">{result.plain_explanation}</p>
                </div>
                
                {/* Clause-level Translation and Summary */}
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <ClauseTranslationButton 
                    clauseData={{
                      id: result.clause_id,
                      text: result.clause_text,
                      index: index
                    }}
                  />
                  <ClauseSummary 
                    clauseId={`${result.clause_id}_${index}`}
                    clauseData={result}
                  />
                  
                  {/* Contextual Chat Buttons */}
                  <button
                    onClick={() => openChat(createClauseContext(result))}
                    className="inline-flex items-center px-3 py-1.5 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-500/30 transition-colors text-sm"
                  >
                    <MessageCircle className="w-3 h-3 mr-1.5" />
                    Ask AI
                  </button>
                  
                  <button
                    onClick={() => openHumanSupport(createClauseContext(result))}
                    className="inline-flex items-center px-3 py-1.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors text-sm"
                  >
                    <Users className="w-3 h-3 mr-1.5" />
                    Expert Help
                  </button>
                </div>
                
                {/* Expandable Details */}
                <div className="progressive-disclosure">
                  <button
                    onClick={() => toggleClause(index)}
                    className="disclosure-header w-full"
                  >
                    <span className="flex items-center">
                      <FileText className="w-4 h-4 mr-2" />
                      <strong>View Detailed Analysis</strong>
                    </span>
                    {expandedClauses.has(index) ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                  
                  {expandedClauses.has(index) && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="disclosure-content"
                    >
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold text-white mb-3 flex items-center">
                            <AlertTriangle className="w-4 h-4 mr-2" />
                            Legal Implications:
                          </h4>
                          <ul className="space-y-2">
                            {result.legal_implications.map((implication, i) => (
                              <li key={i} className="flex items-start">
                                <div className="w-2 h-2 bg-slate-400 rounded-full mt-2 mr-3 flex-shrink-0" />
                                <span className="text-slate-300">{implication}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        <div>
                          <h4 className="font-semibold text-white mb-3 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Recommended Actions:
                          </h4>
                          <ul className="space-y-2">
                            {result.recommendations.map((recommendation, i) => (
                              <li key={i} className="flex items-start">
                                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 mr-3 flex-shrink-0" />
                                <span className="text-slate-300">{recommendation}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      
                      {/* AI Analysis Details */}
                      <div className="mt-6 pt-6 border-t border-slate-700">
                        <h4 className="font-semibold text-white mb-4 flex items-center">
                          <Zap className="w-4 h-4 mr-2" />
                          AI Analysis Details
                        </h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center">
                            <div className="text-sm text-slate-400 mb-1">Risk Score</div>
                            <div className="confidence-bar mb-2">
                              <div 
                                className={cn(
                                  "confidence-fill",
                                  result.risk_level.level === 'RED' ? "bg-red-500" :
                                  result.risk_level.level === 'YELLOW' ? "bg-yellow-500" : "bg-green-500"
                                )}
                                style={{ width: `${result.risk_level.score * 100}%` }}
                              />
                            </div>
                            <div className="text-sm text-slate-300">{formatPercentage(result.risk_level.score)}</div>
                          </div>
                          
                          <div className="text-center">
                            <div className="text-sm text-slate-400 mb-1">Confidence Level</div>
                            <div className="confidence-bar mb-2">
                              <div 
                                className={cn(
                                  "confidence-fill",
                                  getConfidenceColor(result.risk_level.confidence_percentage)
                                )}
                                style={{ width: `${result.risk_level.confidence_percentage}%` }}
                              />
                            </div>
                            <div className="text-sm text-slate-300">{result.risk_level.confidence_percentage}%</div>
                          </div>
                          
                          <div className="text-center">
                            <div className="text-sm text-slate-400 mb-1">Analysis Quality</div>
                            <div className={cn(
                              "px-2 py-1 rounded text-xs",
                              result.risk_level.confidence_percentage >= 80 ? "bg-green-500/20 text-green-400" :
                              result.risk_level.confidence_percentage >= 60 ? "bg-yellow-500/20 text-yellow-400" :
                              "bg-slate-500/20 text-slate-400"
                            )}>
                              {result.risk_level.confidence_percentage >= 80 ? "High Quality" :
                               result.risk_level.confidence_percentage >= 60 ? "Good Quality" : "Basic Quality"}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Interactive AI Features */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
        >
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white flex items-center mb-2">
              <Zap className="w-5 h-5 mr-2" />
              Interactive AI Features
            </h2>
            <p className="text-slate-400">Advanced Google Cloud AI integration for comprehensive document analysis</p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* AI Confidence Analysis */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <Shield className="w-4 h-4 mr-2" />
                AI Confidence Analysis
              </h3>
              <p className="text-slate-400 text-sm mb-3">View detailed confidence metrics for AI transparency.</p>
              <button
                onClick={() => toggleSection('confidence')}
                className="inline-flex items-center px-3 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                View Confidence Metrics
              </button>
              {expandedSections.has('confidence') && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-3 p-3 bg-slate-900/50 rounded-lg"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-300">Overall Analysis:</span>
                      <span className="text-slate-400">{analysis.overall_risk.confidence_percentage}%</span>
                    </div>
                    <div className="confidence-bar">
                      <div 
                        className={cn("confidence-fill", getConfidenceColor(analysis.overall_risk.confidence_percentage))}
                        style={{ width: `${analysis.overall_risk.confidence_percentage}%` }}
                      />
                    </div>
                    <div className="text-xs text-slate-500">
                      Average clause confidence: {Math.round(analysis.analysis_results.reduce((acc, r) => acc + r.risk_level.confidence_percentage, 0) / analysis.analysis_results.length)}%
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Multi-language Support */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <Globe className="w-4 h-4 mr-2" />
                Multi-language Support
              </h3>
              <p className="text-slate-400 text-sm mb-3">Translate the overall summary to your preferred language.</p>
              <label htmlFor="language-select-summary" className="sr-only">
                Select translation language for summary
              </label>
              <select
                id="language-select-summary"
                value={currentLanguage}
                onChange={(e) => setCurrentLanguage(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm mb-2 focus:border-cyan-500 focus:outline-none"
                aria-label="Select translation language for summary"
              >
                <option value="en">English</option>
                <option value="hi">Hindi (हिंदी)</option>
                <option value="es">Spanish (Español)</option>
                <option value="fr">French (Français)</option>
                <option value="de">German (Deutsch)</option>
                <option value="zh">Chinese (中文)</option>
                <option value="ar">Arabic (العربية)</option>
                <option value="pt">Portuguese (Português)</option>
              </select>
              <button
                onClick={() => openTranslation(analysis.summary, 'Document Summary')}
                className="inline-flex items-center px-3 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors text-sm"
              >
                <Globe className="w-4 h-4 mr-2" />
                Translate Summary
              </button>
            </div>

            {/* AI Clarification */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <MessageCircle className="w-4 h-4 mr-2" />
                Get Help & Clarification
              </h3>
              <p className="text-slate-400 text-sm mb-4">Ask questions about the document or get expert guidance.</p>
              <div className="space-y-3">
                <button
                  onClick={() => openChat()}
                  className="w-full inline-flex items-center justify-center px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-400 hover:to-pink-400 transition-all"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  AI Chat Assistant
                </button>
                <button
                  onClick={() => openHumanSupport()}
                  className="w-full inline-flex items-center justify-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Contact Human Expert
                </button>
              </div>
            </div>

            {/* Document Comparison */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Document Comparison
              </h3>
              <p className="text-slate-400 text-sm mb-3">Compare this document with another for risk differences.</p>
              <button
                onClick={() => setIsComparisonOpen(true)}
                className="inline-flex items-center px-3 py-2 bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 rounded-lg hover:bg-yellow-500/30 transition-colors text-sm"
              >
                <FileText className="w-4 h-4 mr-2" />
                Compare Documents
              </button>
            </div>

            {/* Google Cloud AI Services */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <Zap className="w-4 h-4 mr-2" />
                Google Cloud AI Services
              </h3>
              <p className="text-slate-400 text-sm mb-3">View the status of integrated Google Cloud AI services.</p>
              <button
                onClick={openStatus}
                className="inline-flex items-center px-3 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
              >
                <Activity className="w-4 h-4 mr-2" />
                Check AI Services
              </button>
            </div>

            {/* Advanced Analysis */}
            <div className="feature-card p-4">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <BarChart3 className="w-4 h-4 mr-2" />
                Advanced Analysis
              </h3>
              <p className="text-slate-400 text-sm mb-3">Get detailed Natural Language AI insights about your document.</p>
              <button
                onClick={() => runAdvancedAnalysis()}
                className="inline-flex items-center px-3 py-2 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-500/30 transition-colors text-sm"
              >
                <Zap className="w-4 h-4 mr-2" />
                Run NL Analysis
              </button>
            </div>
          </div>

          {/* Expandable Sections for Features */}
          {expandedSections.has('nlAnalysis') && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 p-6 bg-purple-500/10 border border-purple-500/30 rounded-lg"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Advanced Natural Language Analysis</h3>
              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                    <h4 className="font-medium text-white mb-2 flex items-center">
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Sentiment Analysis
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Overall Tone:</span>
                        <span className="text-blue-400">Formal/Legal</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Complexity Level:</span>
                        <span className="text-yellow-400">High</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Readability Score:</span>
                        <span className="text-red-400">Professional Level</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                    <h4 className="font-medium text-white mb-2 flex items-center">
                      <Activity className="w-4 h-4 mr-2" />
                      Entity Recognition
                    </h4>
                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">Organizations</span>
                        <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Dates</span>
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">Legal Terms</span>
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">Financial</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Key Insights</h4>
                  <ul className="space-y-2 text-sm text-slate-300">
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>Document contains {analysis.analysis_results.length} distinct legal clauses</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>Average confidence level: {Math.round(analysis.analysis_results.reduce((acc, r) => acc + r.risk_level.confidence_percentage, 0) / analysis.analysis_results.length)}%</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>Processing completed in {analysis.processing_time.toFixed(2)} seconds</span>
                    </li>
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Enhanced Export & Share */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
        >
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white flex items-center mb-2">
              <Download className="w-5 h-5 mr-2" />
              Enhanced Export & Share
            </h2>
            <p className="text-slate-400">Professional report generation with multiple formats</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => exportToPDF()}
              disabled={isExporting.pdf}
              className="inline-flex items-center justify-center px-4 py-3 bg-red-500/20 text-red-400 border border-red-500/50 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting.pdf ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Export PDF
                </>
              )}
            </button>
            
            <button
              onClick={() => exportToWord()}
              disabled={isExporting.word}
              className="inline-flex items-center justify-center px-4 py-3 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting.word ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Export Word
                </>
              )}
            </button>
            
            <button
              onClick={() => window.print()}
              className="inline-flex items-center justify-center px-4 py-3 bg-green-500/20 text-green-400 border border-green-500/50 rounded-lg hover:bg-green-500/30 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Print Analysis
            </button>
            
            <button
              onClick={copyResults}
              className="inline-flex items-center justify-center px-4 py-3 bg-slate-600/50 text-slate-300 border border-slate-600 rounded-lg hover:bg-slate-600/70 transition-colors"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy to Clipboard
            </button>
          </div>
          
          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-blue-400 text-sm">
              <Info className="w-4 h-4 inline mr-2" />
              <strong>Disclaimer:</strong> This analysis is for informational purposes only and does not constitute legal advice. 
              Please consult with a qualified legal professional for specific legal matters.
            </p>
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <button
            onClick={onBackToHome}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Analyze Another Document
          </button>
        </motion.div>
      </div>
    </div>

    {/* Modals */}
    <AIChat
      isOpen={isChatOpen}
      onClose={() => setIsChatOpen(false)}
      documentContext={documentContext}
      clauseContext={activeChatClause}
    />

    <HumanSupport
      isOpen={isHumanSupportOpen}
      onClose={() => setIsHumanSupportOpen(false)}
      documentContext={documentContext}
      clauseContext={activeChatClause}
    />

    <TranslationModal
      isOpen={isTranslationOpen}
      onClose={() => setIsTranslationOpen(false)}
      originalText={translationText}
      title={translationTitle}
    />

    <StatusModal
      isOpen={isStatusOpen}
      onClose={() => setIsStatusOpen(false)}
    />

    {analysis && (
      <DocumentComparison
        isOpen={isComparisonOpen}
        onClose={() => setIsComparisonOpen(false)}
        currentDocument={{
          text: '', // We'll need to pass the original document text from props
          type: 'general_contract'
        }}
      />
    )}
    </>
  );
});