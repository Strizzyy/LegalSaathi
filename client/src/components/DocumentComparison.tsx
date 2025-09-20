import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle, 
  BarChart3,
  Loader2,
  ChevronDown,
  ChevronUp
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
  const [comparisonResult, setComparisonResult] = useState<DocumentComparisonResponse | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']));

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

    try {
      const request: DocumentComparisonRequest = {
        document1_text: currentDocument.text.trim(),
        document2_text: document2Text.trim(),
        document1_type: currentDocument.type,
        document2_type: document2Type,
        comparison_focus: comparisonFocus
      };

      const result = await comparisonService.compareDocuments(request);
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
    onClose();
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
          Document 2 Text
        </label>
        <textarea
          value={document2Text}
          onChange={(e) => setDocument2Text(e.target.value)}
          placeholder="Paste the second document text here for comparison..."
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none"
          rows={8}
        />
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

    const { formatRiskLevel, formatRiskDifference, getSeverityColor } = comparisonService;

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

        {/* Key Differences */}
        {comparisonResult.key_differences.length > 0 && (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
            <button
              onClick={() => toggleSection('differences')}
              className="w-full flex items-center justify-between text-left"
            >
              <h4 className="font-medium text-white flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2" />
                Key Differences ({comparisonResult.key_differences.length})
              </h4>
              {expandedSections.has('differences') ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            <AnimatePresence>
              {expandedSections.has('differences') && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 space-y-3"
                >
                  {comparisonResult.key_differences.map((diff, index) => (
                    <div key={index} className={`rounded-lg p-4 border ${getSeverityColor(diff.severity)}`}>
                      <div className="flex items-start justify-between mb-2">
                        <h5 className="font-medium text-white">{diff.description}</h5>
                        <span className={`text-xs px-2 py-1 rounded ${getSeverityColor(diff.severity)}`}>
                          {diff.severity.toUpperCase()}
                        </span>
                      </div>
                      
                      {(diff.document1_value || diff.document2_value) && (
                        <div className="grid md:grid-cols-2 gap-3 mb-3 text-sm">
                          <div>
                            <p className="text-slate-400 mb-1">Document 1:</p>
                            <p className="text-slate-300">{diff.document1_value || 'Not specified'}</p>
                          </div>
                          <div>
                            <p className="text-slate-400 mb-1">Document 2:</p>
                            <p className="text-slate-300">{diff.document2_value || 'Not specified'}</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="space-y-2 text-sm">
                        <p className="text-slate-300">
                          <strong>Impact:</strong> {diff.impact}
                        </p>
                        <p className="text-slate-300">
                          <strong>Recommendation:</strong> {diff.recommendation}
                        </p>
                      </div>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Clause Comparisons */}
        {comparisonResult.clause_comparisons.length > 0 && (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-600">
            <button
              onClick={() => toggleSection('clauses')}
              className="w-full flex items-center justify-between text-left"
            >
              <h4 className="font-medium text-white flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Clause Comparisons ({comparisonResult.clause_comparisons.length})
              </h4>
              {expandedSections.has('clauses') ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            <AnimatePresence>
              {expandedSections.has('clauses') && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 space-y-3"
                >
                  {comparisonResult.clause_comparisons.map((comparison, index) => (
                    <div key={index} className="bg-slate-700/50 rounded-lg p-4">
                      <h5 className="font-medium text-white mb-2 capitalize">
                        {comparison.clause_type.replace('_', ' ')}
                      </h5>
                      
                      <div className="space-y-2 text-sm">
                        <p className="text-slate-300">
                          <strong>Comparison:</strong> {comparison.comparison_notes}
                        </p>
                        <p className="text-slate-300">
                          <strong>Risk Difference:</strong> 
                          <span className={`ml-1 ${formatRiskDifference(comparison.risk_difference).color}`}>
                            {formatRiskDifference(comparison.risk_difference).text}
                          </span>
                        </p>
                        <p className="text-slate-300">
                          <strong>Recommendation:</strong> {comparison.recommendation}
                        </p>
                      </div>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

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

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Document Comparison" maxWidth="4xl">
      <div className="min-h-[600px]">
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
      </div>
    </Modal>
  );
}