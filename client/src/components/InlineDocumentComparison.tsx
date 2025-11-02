import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  ArrowRight,
  CheckCircle,
  BarChart3,
  Loader2,
  ChevronDown,
  ChevronUp,
  Download,
  Eye,
  GitCompare,
  TrendingUp,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { comparisonService, DocumentComparisonRequest, DocumentComparisonResponse } from '../services/comparisonService';
import { notificationService } from '../services/notificationService';

interface InlineDocumentComparisonProps {
  currentDocument?: {
    text: string;
    type: string;
  };
  isExpanded: boolean;
  onToggleExpanded: () => void;
  className?: string;
  showExpandToggle?: boolean;
}

export function InlineDocumentComparison({ 
  currentDocument, 
  isExpanded, 
  onToggleExpanded, 
  className = '',
  showExpandToggle = true
}: InlineDocumentComparisonProps) {
  const [step, setStep] = useState<'input' | 'results'>('input');
  const [document2Text, setDocument2Text] = useState('');
  const [document2Type, setDocument2Type] = useState('rental_agreement');
  const [comparisonFocus, setComparisonFocus] = useState('overall');
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonProgress, setComparisonProgress] = useState(0);
  const [comparisonMessage, setComparisonMessage] = useState('');
  const [isUploadingDoc2, setIsUploadingDoc2] = useState(false);
  const [uploadMethod, setUploadMethod] = useState<'text' | 'file'>('text');
  const [comparisonResult, setComparisonResult] = useState<DocumentComparisonResponse | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']));
  const [viewMode, setViewMode] = useState<'overview' | 'side-by-side' | 'visual-diff'>('overview');
  const [isExporting, setIsExporting] = useState(false);

  const documentTypes = [
    { value: 'rental_agreement', label: 'Rental Agreement' },
    { value: 'employment_contract', label: 'Employment Contract' },
    { value: 'nda', label: 'Non-Disclosure Agreement' },
    { value: 'loan_agreement', label: 'Loan Agreement' },
    { value: 'partnership_agreement', label: 'Partnership Agreement' },
    { value: 'general_contract', label: 'General Contract' }
  ];

  const focusOptions = [
    { value: 'overall', label: 'Overall Comparison' },
    { value: 'clauses', label: 'Clause-by-Clause' },
    { value: 'risks', label: 'Risk Analysis' },
    { value: 'terms', label: 'Terms & Conditions' }
  ];

  const handleCompare = async () => {
    if (!currentDocument) {
      notificationService.error('No current document to compare');
      return;
    }

    // Debug logging
    console.log('Current document for comparison:', {
      hasText: !!currentDocument.text,
      textLength: currentDocument.text?.length || 0,
      type: currentDocument.type,
      textPreview: currentDocument.text?.substring(0, 100) + '...'
    });

    // Enhanced validation
    if (!currentDocument.text || !currentDocument.text.trim()) {
      notificationService.error('Current document is empty or invalid');
      return;
    }

    if (!document2Text.trim()) {
      notificationService.error('Please enter the second document text');
      return;
    }

    if (currentDocument.text.trim().length < 100) {
      notificationService.error('Current document must be at least 100 characters long');
      return;
    }

    if (document2Text.trim().length < 100) {
      notificationService.error('Second document must be at least 100 characters long');
      return;
    }

    // Check for meaningful content (not just whitespace or repeated characters)
    const doc1Words = currentDocument.text.trim().split(/\s+/).filter(word => word.length > 2);
    const doc2Words = document2Text.trim().split(/\s+/).filter(word => word.length > 2);

    if (doc1Words.length < 20) {
      notificationService.error('Current document does not contain enough meaningful content');
      return;
    }

    if (doc2Words.length < 20) {
      notificationService.error('Second document does not contain enough meaningful content');
      return;
    }

    // Check if documents are too similar (might be duplicates)
    const similarity = calculateTextSimilarity(currentDocument.text, document2Text);
    if (similarity > 0.95) {
      notificationService.error('Documents appear to be identical or nearly identical');
      return;
    }

    setIsComparing(true);
    setComparisonProgress(0);
    setComparisonMessage('Preparing documents for comparison...');

    try {
      const request: DocumentComparisonRequest = {
        document1_text: currentDocument.text.trim(),
        document2_text: document2Text.trim(),
        document1_type: currentDocument.type,
        document2_type: document2Type,
        comparison_focus: comparisonFocus
      };

      console.log('🚀 Starting ULTRA-FAST document comparison...');
      
      // Use progress tracking for better UX
      const result = await comparisonService.compareDocumentsWithProgress(
        request,
        (progress, message) => {
          setComparisonProgress(progress);
          setComparisonMessage(message);
        }
      );
      
      setComparisonResult(result);
      setStep('results');
      notificationService.success('Document comparison completed successfully');
    } catch (error: any) {
      console.error('Comparison failed:', error);

      // Provide more specific error messages
      let errorMessage = 'Failed to compare documents';
      if (error.message) {
        if (error.message.includes('empty') || error.message.includes('no text')) {
          errorMessage = 'One or both documents are empty or contain insufficient text';
        } else if (error.message.includes('100 characters')) {
          errorMessage = 'Both documents must contain at least 100 characters of meaningful text';
        } else if (error.message.includes('extract')) {
          errorMessage = 'Unable to process document content. Please check document format';
        } else {
          errorMessage = error.message;
        }
      }

      notificationService.error(errorMessage);
    } finally {
      setIsComparing(false);
    }
  };

  // Helper function to calculate text similarity
  const calculateTextSimilarity = (text1: string, text2: string): number => {
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));

    const intersection = new Set([...words1].filter(word => words2.has(word)));
    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const handleReset = () => {
    setStep('input');
    setDocument2Text('');
    setComparisonResult(null);
    setExpandedSections(new Set(['summary']));
    setViewMode('overview');
    setIsExporting(false);
    setIsUploadingDoc2(false);
    setUploadMethod('text');
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    if (!allowedTypes.includes(file.type)) {
      notificationService.error('Please upload a PDF, Word document, or text file');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      notificationService.error('File size must be less than 10MB');
      return;
    }

    setIsUploadingDoc2(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success && result.text) {
        setDocument2Text(result.text);
        notificationService.success('Document uploaded successfully');
      } else {
        throw new Error(result.error || 'Failed to extract text from document');
      }
    } catch (error: any) {
      console.error('File upload failed:', error);
      notificationService.error(`Upload failed: ${error.message}`);
    } finally {
      setIsUploadingDoc2(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleExport = async (format: 'pdf' | 'docx') => {
    if (!comparisonResult) return;

    setIsExporting(true);
    try {
      const blob = await comparisonService.exportComparisonReport(comparisonResult, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `comparison_report_${comparisonResult.comparison_id}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      notificationService.success(`Report exported as ${format.toUpperCase()} successfully`);
    } catch (error: any) {
      console.error('Export failed:', error);
      notificationService.error(`Failed to export report: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const renderInputStep = () => (
    <div className="space-y-4">
      <div>
        <p className="text-slate-400 text-sm">
          Compare your current document with another to identify differences in risk levels, clauses, and terms.
        </p>
      </div>

      {/* Current Document Info */}
      {currentDocument && (
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-600/50">
          <h4 className="font-medium text-white mb-2 flex items-center text-sm">
            <FileText className="w-4 h-4 mr-2" />
            Document 1 (Current)
          </h4>
          <div className="text-xs text-slate-300">
            <p><strong>Type:</strong> {currentDocument.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
            <p><strong>Length:</strong> {currentDocument.text.length} characters</p>
          </div>
        </div>
      )}

      {/* Second Document Input */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Document 2
        </label>
        
        {/* Upload Method Selection */}
        <div className="flex space-x-2 mb-3">
          <button
            type="button"
            onClick={() => setUploadMethod('text')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              uploadMethod === 'text'
                ? 'bg-cyan-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Paste Text
          </button>
          <button
            type="button"
            onClick={() => setUploadMethod('file')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              uploadMethod === 'file'
                ? 'bg-cyan-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Upload File
          </button>
        </div>

        {uploadMethod === 'text' ? (
          <textarea
            value={document2Text}
            onChange={(e) => setDocument2Text(e.target.value)}
            placeholder="Paste the second document text here for comparison..."
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none text-sm"
            rows={6}
          />
        ) : (
          <div className="border-2 border-dashed border-slate-600 rounded-lg p-4 text-center">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              disabled={isUploadingDoc2}
              className="hidden"
              id="document2-upload-inline"
            />
            <label
              htmlFor="document2-upload-inline"
              className={`cursor-pointer ${isUploadingDoc2 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex flex-col items-center space-y-2">
                {isUploadingDoc2 ? (
                  <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                ) : (
                  <FileText className="w-6 h-6 text-slate-400" />
                )}
                <p className="text-slate-300 font-medium text-sm">
                  {isUploadingDoc2 ? 'Uploading...' : 'Click to upload document'}
                </p>
                <p className="text-xs text-slate-400">
                  Supports PDF, Word (.doc, .docx), and text files (max 10MB)
                </p>
              </div>
            </label>
          </div>
        )}
        
        <p className="text-xs text-slate-400 mt-1">
          {document2Text.length} characters (minimum 100 required)
        </p>
      </div>

      {/* Document Type and Focus Selection */}
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Document 2 Type
          </label>
          <select
            value={document2Type}
            onChange={(e) => setDocument2Type(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none text-sm"
          >
            {documentTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Comparison Focus
          </label>
          <select
            value={comparisonFocus}
            onChange={(e) => setComparisonFocus(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none text-sm"
          >
            {focusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors text-sm"
        >
          Reset
        </button>
        <button
          onClick={handleCompare}
          disabled={!document2Text.trim() || document2Text.length < 100 || isComparing}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 text-sm"
        >
          {isComparing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Comparing...</span>
            </>
          ) : (
            <>
              <BarChart3 className="w-4 h-4" />
              <span>Compare Documents</span>
            </>
          )}
        </button>
      </div>

      {/* Progress Indicator */}
      {isComparing && (
        <div className="mt-4 p-3 bg-slate-800/50 rounded-lg border border-slate-600/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white font-medium text-sm">Comparison Progress</span>
            <span className="text-cyan-400 text-xs">{Math.round(comparisonProgress)}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5 mb-2">
            <div 
              className="bg-gradient-to-r from-cyan-500 to-blue-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${comparisonProgress}%` }}
            />
          </div>
          <p className="text-slate-400 text-xs">{comparisonMessage}</p>
        </div>
      )}
    </div>
  );

  const renderResultsStep = () => {
    if (!comparisonResult) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-base font-semibold text-white">
            Comparison Results
          </h4>
          <button
            onClick={() => setStep('input')}
            className="text-cyan-400 hover:text-cyan-300 text-sm flex items-center space-x-1"
          >
            <ArrowRight className="w-4 h-4 rotate-180" />
            <span>New Comparison</span>
          </button>
        </div>

        {/* View Mode Selector */}
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-600/50">
          <div className="flex items-center justify-between mb-3">
            <h5 className="font-medium text-white text-sm">View Mode</h5>
            <div className="flex space-x-1">
              <button
                onClick={() => setViewMode('overview')}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  viewMode === 'overview'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <BarChart3 className="w-3 h-3 inline mr-1" />
                Overview
              </button>
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  viewMode === 'side-by-side'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <GitCompare className="w-3 h-3 inline mr-1" />
                Side-by-Side
              </button>
              <button
                onClick={() => setViewMode('visual-diff')}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  viewMode === 'visual-diff'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <Eye className="w-3 h-3 inline mr-1" />
                Visual Diff
              </button>
            </div>
          </div>

          {/* Export Options */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Export Report:</span>
            <div className="flex space-x-1">
              <button
                onClick={() => handleExport('pdf')}
                disabled={isExporting}
                className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                {isExporting ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Download className="w-3 h-3" />
                )}
                <span>PDF</span>
              </button>
              <button
                onClick={() => handleExport('docx')}
                disabled={isExporting}
                className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                {isExporting ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Download className="w-3 h-3" />
                )}
                <span>Word</span>
              </button>
            </div>
          </div>
        </div>

        {/* Render content based on view mode */}
        {viewMode === 'overview' && renderOverviewContent()}
        {viewMode === 'side-by-side' && renderSideBySideContent()}
        {viewMode === 'visual-diff' && renderVisualDiffContent()}
      </div>
    );
  };

  const renderOverviewContent = () => {
    if (!comparisonResult) return null;
    const { formatRiskLevel } = comparisonService;

    return (
      <div className="space-y-4">
        {/* Overall Summary */}
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/50">
          <button
            onClick={() => toggleSection('summary')}
            className="w-full flex items-center justify-between text-left"
          >
            <h5 className="font-medium text-white flex items-center text-sm">
              <BarChart3 className="w-4 h-4 mr-2" />
              Overall Comparison
            </h5>
            {expandedSections.has('summary') ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          <AnimatePresence>
            {expandedSections.has('summary') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 space-y-3"
              >
                <div className="grid md:grid-cols-2 gap-3">
                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <h6 className="font-medium text-white mb-2 text-sm">Document 1</h6>
                    <div className="space-y-1 text-xs">
                      <p className="text-slate-300">
                        <strong>Type:</strong> {comparisonResult.document1_summary.type.replace('_', ' ')}
                      </p>
                      <p className="text-slate-300">
                        <strong>Risk:</strong>
                        <span className={`ml-1 ${formatRiskLevel(comparisonResult.document1_summary.overall_risk.level).color}`}>
                          {formatRiskLevel(comparisonResult.document1_summary.overall_risk.level).text}
                        </span>
                      </p>
                      <p className="text-slate-300">
                        <strong>Clauses:</strong> {comparisonResult.document1_summary.clause_count}
                      </p>
                    </div>
                  </div>

                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <h6 className="font-medium text-white mb-2 text-sm">Document 2</h6>
                    <div className="space-y-1 text-xs">
                      <p className="text-slate-300">
                        <strong>Type:</strong> {comparisonResult.document2_summary.type.replace('_', ' ')}
                      </p>
                      <p className="text-slate-300">
                        <strong>Risk:</strong>
                        <span className={`ml-1 ${formatRiskLevel(comparisonResult.document2_summary.overall_risk.level).color}`}>
                          {formatRiskLevel(comparisonResult.document2_summary.overall_risk.level).text}
                        </span>
                      </p>
                      <p className="text-slate-300">
                        <strong>Clauses:</strong> {comparisonResult.document2_summary.clause_count}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-3">
                  <h6 className="font-medium text-white mb-2 text-sm">Verdict</h6>
                  <p className="text-slate-300 mb-2 text-sm">{comparisonResult.overall_risk_comparison.verdict}</p>
                  <p className="text-xs text-slate-400">{comparisonResult.recommendation_summary}</p>
                </div>

                {comparisonResult.safer_document && comparisonResult.safer_document !== 'similar' && (
                  <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="font-medium text-green-400 text-sm">
                        Recommendation: Choose Document {comparisonResult.safer_document === 'document1' ? '1' : '2'}
                      </span>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  };  const
 renderSideBySideContent = () => {
    if (!comparisonResult) return null;

    return (
      <div className="space-y-4">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/50">
          <h5 className="font-medium text-white mb-3 flex items-center text-sm">
            <GitCompare className="w-4 h-4 mr-2" />
            Side-by-Side Clause Comparison
          </h5>

          <div className="space-y-3">
            {comparisonResult.clause_comparisons.slice(0, 6).map((comparison, index) => (
              <div key={index} className="border border-slate-600/50 rounded-lg overflow-hidden">
                <div className="bg-slate-700/50 p-2 border-b border-slate-600/50">
                  <h6 className="font-medium text-white capitalize text-sm">
                    {comparison.clause_type.replace('_', ' ')}
                  </h6>
                  <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                    <span>Risk Difference: {comparison.risk_difference.toFixed(3)}</span>
                    <span className={`px-2 py-0.5 rounded ${
                      Math.abs(comparison.risk_difference) > 0.3 ? 'bg-red-500/20 text-red-400' :
                      Math.abs(comparison.risk_difference) > 0.1 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {Math.abs(comparison.risk_difference) > 0.3 ? 'High Impact' :
                       Math.abs(comparison.risk_difference) > 0.1 ? 'Medium Impact' : 'Low Impact'}
                    </span>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-0">
                  {/* Document 1 Clause */}
                  <div className="p-3 border-r border-slate-600/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-slate-300">Document 1</span>
                      {comparison.document1_clause && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          comparison.document1_clause.risk_assessment.level === 'RED' ? 'bg-red-500/20 text-red-400' :
                          comparison.document1_clause.risk_assessment.level === 'YELLOW' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {comparison.document1_clause.risk_assessment.level}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-300 bg-slate-900/50 p-2 rounded max-h-24 overflow-y-auto">
                      {comparison.document1_clause ? 
                        comparison.document1_clause.clause_text.substring(0, 200) + 
                        (comparison.document1_clause.clause_text.length > 200 ? '...' : '') :
                        <span className="text-slate-500 italic">No equivalent clause</span>
                      }
                    </div>
                  </div>

                  {/* Document 2 Clause */}
                  <div className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-slate-300">Document 2</span>
                      {comparison.document2_clause && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          comparison.document2_clause.risk_assessment.level === 'RED' ? 'bg-red-500/20 text-red-400' :
                          comparison.document2_clause.risk_assessment.level === 'YELLOW' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {comparison.document2_clause.risk_assessment.level}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-300 bg-slate-900/50 p-2 rounded max-h-24 overflow-y-auto">
                      {comparison.document2_clause ? 
                        comparison.document2_clause.clause_text.substring(0, 200) + 
                        (comparison.document2_clause.clause_text.length > 200 ? '...' : '') :
                        <span className="text-slate-500 italic">No equivalent clause</span>
                      }
                    </div>
                  </div>
                </div>

                <div className="bg-slate-700/30 p-2 border-t border-slate-600/50">
                  <p className="text-xs text-slate-300 mb-1">
                    <strong>Analysis:</strong> {comparison.comparison_notes}
                  </p>
                  <p className="text-xs text-slate-300">
                    <strong>Recommendation:</strong> {comparison.recommendation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderVisualDiffContent = () => {
    if (!comparisonResult) return null;

    // Extract visual differences data
    const visualDiff = {
      total_changes: comparisonResult.key_differences.length,
      high_impact_changes: comparisonResult.key_differences.filter(d => d.severity === 'high').length,
      matched_clauses: comparisonResult.clause_comparisons.filter(c => c.document1_clause && c.document2_clause).length,
      unique_to_doc1: comparisonResult.clause_comparisons.filter(c => c.document1_clause && !c.document2_clause).length,
      unique_to_doc2: comparisonResult.clause_comparisons.filter(c => !c.document1_clause && c.document2_clause).length
    };

    return (
      <div className="space-y-4">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/50">
          <h5 className="font-medium text-white mb-3 flex items-center text-sm">
            <Eye className="w-4 h-4 mr-2" />
            Visual Difference Analysis
          </h5>

          {/* Change Summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
            <div className="bg-slate-700/50 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-white">{visualDiff.total_changes}</div>
              <div className="text-xs text-slate-400">Total Changes</div>
            </div>
            <div className="bg-red-500/20 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-red-400">{visualDiff.high_impact_changes}</div>
              <div className="text-xs text-slate-400">High Impact</div>
            </div>
            <div className="bg-blue-500/20 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-blue-400">{visualDiff.matched_clauses}</div>
              <div className="text-xs text-slate-400">Matched</div>
            </div>
            <div className="bg-orange-500/20 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-orange-400">{visualDiff.unique_to_doc1}</div>
              <div className="text-xs text-slate-400">Unique to Doc 1</div>
            </div>
            <div className="bg-purple-500/20 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-purple-400">{visualDiff.unique_to_doc2}</div>
              <div className="text-xs text-slate-400">Unique to Doc 2</div>
            </div>
          </div>

          {/* Change Impact Visualization */}
          <div className="space-y-3">
            <h6 className="font-medium text-white text-sm">Change Impact Analysis</h6>
            
            {comparisonResult.key_differences.slice(0, 4).map((diff, index) => (
              <div key={index} className={`rounded-lg p-3 border-l-4 ${
                diff.severity === 'high' ? 'border-red-500 bg-red-500/10' :
                diff.severity === 'medium' ? 'border-yellow-500 bg-yellow-500/10' :
                'border-green-500 bg-green-500/10'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h6 className="font-medium text-white mb-1 text-sm">{diff.description}</h6>
                    <p className="text-xs text-slate-300 mb-1">{diff.impact}</p>
                    <p className="text-xs text-slate-400">{diff.recommendation}</p>
                  </div>
                  <div className="flex items-center space-x-1">
                    <TrendingUp className={`w-3 h-3 ${
                      diff.severity === 'high' ? 'text-red-400' :
                      diff.severity === 'medium' ? 'text-yellow-400' :
                      'text-green-400'
                    }`} />
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      diff.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                      diff.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {diff.severity.toUpperCase()}
                    </span>
                  </div>
                </div>

                {(diff.document1_value || diff.document2_value) && (
                  <div className="mt-2 grid md:grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-900/50 p-2 rounded">
                      <span className="text-slate-400">Document 1:</span>
                      <p className="text-slate-300">{diff.document1_value || 'Not specified'}</p>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded">
                      <span className="text-slate-400">Document 2:</span>
                      <p className="text-slate-300">{diff.document2_value || 'Not specified'}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.8 }}
      className={`bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50 ${className}`}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50">
        {showExpandToggle ? (
          <button
            onClick={onToggleExpanded}
            className="w-full flex items-center justify-between text-left group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-lg">
                <GitCompare className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                  Document Comparison
                </h3>
                <p className="text-sm text-slate-400">
                  {isExpanded ? 'Compare your document with another' : 'Click to expand and compare documents'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {comparisonResult && (
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                  Results Available
                </span>
              )}
              {isExpanded ? (
                <Minimize2 className="w-5 h-5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
              ) : (
                <Maximize2 className="w-5 h-5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
              )}
            </div>
          </button>
        ) : (
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-lg">
              <GitCompare className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                Document Comparison
              </h3>
              <p className="text-sm text-slate-400">
                Compare your document with another to identify differences in risk levels, clauses, and terms
              </p>
            </div>
            {comparisonResult && (
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded ml-auto">
                Results Available
              </span>
            )}
          </div>
        )}
      </div>

      {/* Content */}
      <AnimatePresence>
        {(isExpanded || !showExpandToggle) && (
          <motion.div
            initial={{ opacity: 0, height: showExpandToggle ? 0 : 'auto' }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: showExpandToggle ? 0 : 'auto' }}
            transition={{ duration: showExpandToggle ? 0.3 : 0 }}
            className="overflow-hidden"
          >
            <div className="p-4">
              <AnimatePresence mode="wait">
                {step === 'input' && (
                  <motion.div
                    key="input"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderInputStep()}
                  </motion.div>
                )}

                {step === 'results' && (
                  <motion.div
                    key="results"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderResultsStep()}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}