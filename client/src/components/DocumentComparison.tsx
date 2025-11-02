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
  TrendingUp
} from 'lucide-react';
import { Modal } from './Modal';
import { comparisonService, DocumentComparisonRequest, DocumentComparisonResponse } from '../services/comparisonService';
import { notificationService } from '../services/notificationService';

interface DocumentComparisonProps {
  isOpen: boolean;
  onClose: () => void;
  currentDocument?: {
    text: string;
    type: string;
  };
}

export function DocumentComparison({ isOpen, onClose, currentDocument }: DocumentComparisonProps) {
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

  const handleClose = () => {
    setStep('input');
    setDocument2Text('');
    setComparisonResult(null);
    setExpandedSections(new Set(['summary']));
    setViewMode('overview');
    setIsExporting(false);
    setIsUploadingDoc2(false);
    setUploadMethod('text');
    onClose();
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
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">
          Compare Documents
        </h3>
        <p className="text-slate-400 text-sm">
          Compare your current document with another to identify differences in risk levels, clauses, and terms.
        </p>
      </div>

      {/* Current Document Info */}
      {currentDocument && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
          <h4 className="font-medium text-white mb-2 flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Document 1 (Current)
          </h4>
          <div className="text-sm text-slate-300">
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
        <div className="flex space-x-4 mb-4">
          <button
            type="button"
            onClick={() => setUploadMethod('text')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none"
            rows={8}
          />
        ) : (
          <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              disabled={isUploadingDoc2}
              className="hidden"
              id="document2-upload"
            />
            <label
              htmlFor="document2-upload"
              className={`cursor-pointer ${isUploadingDoc2 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex flex-col items-center space-y-2">
                {isUploadingDoc2 ? (
                  <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                ) : (
                  <FileText className="w-8 h-8 text-slate-400" />
                )}
                <p className="text-slate-300 font-medium">
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

      {/* Document Type Selection */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Document 2 Type
        </label>
        <select
          value={document2Type}
          onChange={(e) => setDocument2Type(e.target.value)}
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none"
        >
          {documentTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Comparison Focus */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Comparison Focus
        </label>
        <select
          value={comparisonFocus}
          onChange={(e) => setComparisonFocus(e.target.value)}
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none"
        >
          {focusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={handleClose}
          className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleCompare}
          disabled={!document2Text.trim() || document2Text.length < 100 || isComparing}
          className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
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


    </div>
  );

  const renderResultsStep = () => {
    if (!comparisonResult) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">
            Comparison Results
          </h3>
          <button
            onClick={() => setStep('input')}
            className="text-cyan-400 hover:text-cyan-300 text-sm flex items-center space-x-1"
          >
            <ArrowRight className="w-4 h-4 rotate-180" />
            <span>New Comparison</span>
          </button>
        </div>

        {/* View Mode Selector */}
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">View Mode</h4>
            <div className="flex space-x-2">
              <button
                onClick={() => setViewMode('overview')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  viewMode === 'overview'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-1" />
                Overview
              </button>
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  viewMode === 'side-by-side'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <GitCompare className="w-4 h-4 inline mr-1" />
                Side-by-Side
              </button>
              <button
                onClick={() => setViewMode('visual-diff')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  viewMode === 'visual-diff'
                    ? 'bg-cyan-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <Eye className="w-4 h-4 inline mr-1" />
                Visual Diff
              </button>
            </div>
          </div>

          {/* Export Options */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Export Report:</span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleExport('pdf')}
                disabled={isExporting}
                className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
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
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
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

        {/* Close Button */}
        <div className="flex justify-center">
          <button
            onClick={handleClose}
            className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
          >
            Close Comparison
          </button>
        </div>
      </div>
    );
  };

  const renderOverviewContent = () => {
    if (!comparisonResult) return null;
    const { formatRiskLevel } = comparisonService;

    return (
      <div className="space-y-6">
        {/* Overall Summary */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
          <button
            onClick={() => toggleSection('summary')}
            className="w-full flex items-center justify-between text-left"
          >
            <h4 className="font-medium text-white flex items-center">
              <BarChart3 className="w-4 h-4 mr-2" />
              Overall Comparison
            </h4>
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
                className="mt-4 space-y-4"
              >
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <h5 className="font-medium text-white mb-2">Document 1</h5>
                    <div className="space-y-1 text-sm">
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

                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <h5 className="font-medium text-white mb-2">Document 2</h5>
                    <div className="space-y-1 text-sm">
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

                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h5 className="font-medium text-white mb-2">Verdict</h5>
                  <p className="text-slate-300 mb-2">{comparisonResult.overall_risk_comparison.verdict}</p>
                  <p className="text-sm text-slate-400">{comparisonResult.recommendation_summary}</p>
                </div>

                {comparisonResult.safer_document && comparisonResult.safer_document !== 'similar' && (
                  <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <span className="font-medium text-green-400">
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
  };

  const renderSideBySideContent = () => {
    if (!comparisonResult) return null;

    return (
      <div className="space-y-6">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
          <h4 className="font-medium text-white mb-4 flex items-center">
            <GitCompare className="w-4 h-4 mr-2" />
            Side-by-Side Clause Comparison
          </h4>

          <div className="space-y-4">
            {comparisonResult.clause_comparisons.slice(0, 8).map((comparison, index) => (
              <div key={index} className="border border-slate-600 rounded-lg overflow-hidden">
                <div className="bg-slate-700/50 p-3 border-b border-slate-600">
                  <h5 className="font-medium text-white capitalize">
                    {comparison.clause_type.replace('_', ' ')}
                  </h5>
                  <div className="flex items-center space-x-4 text-sm text-slate-400 mt-1">
                    <span>Risk Difference: {comparison.risk_difference.toFixed(3)}</span>
                    <span className={`px-2 py-1 rounded ${
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
                  <div className="p-4 border-r border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-300">Document 1</span>
                      {comparison.document1_clause && (
                        <span className={`text-xs px-2 py-1 rounded ${
                          comparison.document1_clause.risk_assessment.level === 'RED' ? 'bg-red-500/20 text-red-400' :
                          comparison.document1_clause.risk_assessment.level === 'YELLOW' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {comparison.document1_clause.risk_assessment.level}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded max-h-32 overflow-y-auto">
                      {comparison.document1_clause ? 
                        comparison.document1_clause.clause_text.substring(0, 300) + 
                        (comparison.document1_clause.clause_text.length > 300 ? '...' : '') :
                        <span className="text-slate-500 italic">No equivalent clause</span>
                      }
                    </div>
                  </div>

                  {/* Document 2 Clause */}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-300">Document 2</span>
                      {comparison.document2_clause && (
                        <span className={`text-xs px-2 py-1 rounded ${
                          comparison.document2_clause.risk_assessment.level === 'RED' ? 'bg-red-500/20 text-red-400' :
                          comparison.document2_clause.risk_assessment.level === 'YELLOW' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {comparison.document2_clause.risk_assessment.level}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded max-h-32 overflow-y-auto">
                      {comparison.document2_clause ? 
                        comparison.document2_clause.clause_text.substring(0, 300) + 
                        (comparison.document2_clause.clause_text.length > 300 ? '...' : '') :
                        <span className="text-slate-500 italic">No equivalent clause</span>
                      }
                    </div>
                  </div>
                </div>

                <div className="bg-slate-700/30 p-3 border-t border-slate-600">
                  <p className="text-sm text-slate-300 mb-1">
                    <strong>Analysis:</strong> {comparison.comparison_notes}
                  </p>
                  <p className="text-sm text-slate-300">
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

    // Extract visual differences data (this would come from the enhanced backend)
    const visualDiff = {
      total_changes: comparisonResult.key_differences.length,
      high_impact_changes: comparisonResult.key_differences.filter(d => d.severity === 'high').length,
      matched_clauses: comparisonResult.clause_comparisons.filter(c => c.document1_clause && c.document2_clause).length,
      unique_to_doc1: comparisonResult.clause_comparisons.filter(c => c.document1_clause && !c.document2_clause).length,
      unique_to_doc2: comparisonResult.clause_comparisons.filter(c => !c.document1_clause && c.document2_clause).length
    };

    return (
      <div className="space-y-6">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
          <h4 className="font-medium text-white mb-4 flex items-center">
            <Eye className="w-4 h-4 mr-2" />
            Visual Difference Analysis
          </h4>

          {/* Change Summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-white">{visualDiff.total_changes}</div>
              <div className="text-xs text-slate-400">Total Changes</div>
            </div>
            <div className="bg-red-500/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-red-400">{visualDiff.high_impact_changes}</div>
              <div className="text-xs text-slate-400">High Impact</div>
            </div>
            <div className="bg-blue-500/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-400">{visualDiff.matched_clauses}</div>
              <div className="text-xs text-slate-400">Matched</div>
            </div>
            <div className="bg-orange-500/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-orange-400">{visualDiff.unique_to_doc1}</div>
              <div className="text-xs text-slate-400">Unique to Doc 1</div>
            </div>
            <div className="bg-purple-500/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-400">{visualDiff.unique_to_doc2}</div>
              <div className="text-xs text-slate-400">Unique to Doc 2</div>
            </div>
          </div>

          {/* Change Impact Visualization */}
          <div className="space-y-4">
            <h5 className="font-medium text-white">Change Impact Analysis</h5>
            
            {comparisonResult.key_differences.map((diff, index) => (
              <div key={index} className={`rounded-lg p-4 border-l-4 ${
                diff.severity === 'high' ? 'border-red-500 bg-red-500/10' :
                diff.severity === 'medium' ? 'border-yellow-500 bg-yellow-500/10' :
                'border-green-500 bg-green-500/10'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h6 className="font-medium text-white mb-1">{diff.description}</h6>
                    <p className="text-sm text-slate-300 mb-2">{diff.impact}</p>
                    <p className="text-sm text-slate-400">{diff.recommendation}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <TrendingUp className={`w-4 h-4 ${
                      diff.severity === 'high' ? 'text-red-400' :
                      diff.severity === 'medium' ? 'text-yellow-400' :
                      'text-green-400'
                    }`} />
                    <span className={`text-xs px-2 py-1 rounded ${
                      diff.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                      diff.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {diff.severity.toUpperCase()}
                    </span>
                  </div>
                </div>

                {(diff.document1_value || diff.document2_value) && (
                  <div className="mt-3 grid md:grid-cols-2 gap-3 text-sm">
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
    <Modal isOpen={isOpen} onClose={handleClose} title="Document Comparison" maxWidth="4xl">
      <div className="min-h-[600px] relative">
        <AnimatePresence mode="wait">
          {step === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
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
            >
              {renderResultsStep()}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Full-screen Loading Overlay for Document Comparison - positioned to cover entire modal */}
      <AnimatePresence>
        {isComparing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/95 backdrop-blur-sm z-[60] flex items-center justify-center"
          >
            <div className="text-center max-w-md mx-auto px-6">
              {/* Animated Spinner */}
              <motion.div
                className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full mx-auto mb-6"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />

              {/* Progress Information */}
              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-2">Comparing Documents</h3>
                <p className="text-slate-300 mb-4">{comparisonMessage}</p>
                
                {/* Progress Bar */}
                <div className="w-full max-w-xs mx-auto">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-400">Progress</span>
                    <span className="text-sm text-cyan-400 font-semibold">{Math.round(comparisonProgress)}%</span>
                  </div>
                  <div className="relative w-full h-2 bg-slate-700 rounded-full border border-slate-600">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${Math.min(comparisonProgress, 99)}%` }}
                    />
                    
                    {/* Shine effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer rounded-full" />
                  </div>
                </div>
              </div>

              {/* AI Processing Indicator */}
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/50">
                <div className="flex items-center justify-center space-x-2 text-sm text-slate-300">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                  <span>AI is analyzing document differences...</span>
                </div>
              </div>

              {/* Google Cloud AI Badge */}
              <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-slate-400">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z" />
                </svg>
                <span>Powered by Google Cloud AI</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </Modal>
  );
}