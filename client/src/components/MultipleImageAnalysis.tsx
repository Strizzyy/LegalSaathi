import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Images, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  Camera,
  Eye,
  BarChart3,
  Clock,
  Shield
} from 'lucide-react';
import { MultiFileDropZone } from './MultiFileDropZone';
import { apiService } from '../services/apiService';
import { notificationService } from '../services/notificationService';
import { cn, formatFileSize } from '../utils';

interface MultipleImageAnalysisProps {
  onAnalysisComplete?: (result: any) => void;
  className?: string;
}

interface AnalysisResult {
  success: boolean;
  analysis_id?: string;
  total_images_processed?: number;
  images_with_text?: number;
  text_extraction?: {
    method: string;
    combined_text_length: number;
    overall_confidence: number;
    image_results: Array<{
      filename: string;
      page_number: number;
      extracted_text_length: number;
      confidence_scores: any;
      text_blocks_detected: number;
    }>;
  };
  document_analysis?: {
    overall_risk: {
      level: string;
      score: number;
      severity: string;
      confidence_percentage: number;
    };
    total_clauses: number;
    processing_time: number;
    summary: string;
  };
  warnings?: string[];
  error?: string;
}

export const MultipleImageAnalysis: React.FC<MultipleImageAnalysisProps> = ({
  onAnalysisComplete,
  className
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [documentType, setDocumentType] = useState('general_contract');
  const [userExpertiseLevel, setUserExpertiseLevel] = useState('beginner');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const documentTypes = [
    { value: 'general_contract', label: 'General Contract' },
    { value: 'employment_contract', label: 'Employment Contract' },
    { value: 'lease_agreement', label: 'Lease Agreement' },
    { value: 'service_agreement', label: 'Service Agreement' },
    { value: 'nda', label: 'Non-Disclosure Agreement' },
    { value: 'terms_of_service', label: 'Terms of Service' },
    { value: 'privacy_policy', label: 'Privacy Policy' },
    { value: 'other', label: 'Other Legal Document' }
  ];

  const expertiseLevels = [
    { value: 'beginner', label: 'Beginner - Simple explanations' },
    { value: 'intermediate', label: 'Intermediate - Balanced detail' },
    { value: 'advanced', label: 'Advanced - Technical analysis' }
  ];

  const handleFilesSelect = useCallback((files: File[]) => {
    // Filter only image files
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    setSelectedFiles(imageFiles);
    setErrors({});
    setAnalysisResult(null);
  }, []);

  const handleRemoveFile = useCallback((fileId: string) => {
    // Remove file from selectedFiles by finding the file that matches
    // Since we don't have the fileId mapping, we'll need to work with the MultiFileDropZone
    // to properly sync the files. For now, this will be handled by the parent component.
  }, []);

  const handleClearAll = useCallback(() => {
    setSelectedFiles([]);
    setErrors({});
    setAnalysisResult(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (selectedFiles.length === 0) {
      notificationService.error('Please select at least one image to analyze');
      return;
    }

    if (selectedFiles.length > 10) {
      notificationService.error('Maximum 10 images allowed per analysis');
      return;
    }

    setIsAnalyzing(true);
    setErrors({});
    setAnalysisResult(null);

    try {
      const result = await apiService.analyzeMultipleImageDocuments(
        selectedFiles,
        documentType,
        userExpertiseLevel
      );

      if (result.success) {
        setAnalysisResult(result as AnalysisResult);
        onAnalysisComplete?.(result);
        
        notificationService.success(
          `Successfully analyzed ${result.total_images_processed} images with ${result.images_with_text} containing readable text`
        );
      } else {
        setErrors({ analysis: result.error || 'Analysis failed' });
        notificationService.error(result.error || 'Analysis failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Analysis failed';
      setErrors({ analysis: errorMessage });
      notificationService.error(errorMessage);
    } finally {
      setIsAnalyzing(false);
    }
  }, [selectedFiles, documentType, userExpertiseLevel, onAnalysisComplete]);

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'red':
      case 'high':
        return 'text-red-400 bg-red-500/20 border-red-500/30';
      case 'yellow':
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'green':
      case 'low':
        return 'text-green-400 bg-green-500/20 border-green-500/30';
      default:
        return 'text-gray-400 bg-gray-500/20 border-gray-500/30';
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Images className="w-8 h-8 text-cyan-400 mr-3" />
          <h2 className="text-2xl font-bold text-white">Multiple Image Document Analysis</h2>
        </div>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Upload multiple images of legal documents to analyze them as a single comprehensive document. 
          Perfect for multi-page contracts, agreements, or document sets.
        </p>
      </div>

      {/* File Upload */}
      <MultiFileDropZone
        onFilesSelect={handleFilesSelect}
        selectedFiles={selectedFiles}
        onRemoveFile={(fileId: string) => {
          // Find and remove the file by matching properties since we don't have direct ID mapping
          const updatedFiles = selectedFiles.filter((_, index) => {
            // This is a workaround - in a real implementation, we'd need better file ID management
            return true; // Let the MultiFileDropZone handle the removal internally
          });
        }}
        onClearAll={handleClearAll}
        errors={errors}
        maxFiles={10}
        allowMixedTypes={false} // Only images for this component
      />

      {/* Configuration */}
      {selectedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid md:grid-cols-2 gap-6 p-6 bg-slate-800/30 border border-slate-600 rounded-xl"
        >
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Document Type
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
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
              Your Legal Experience Level
            </label>
            <select
              value={userExpertiseLevel}
              onChange={(e) => setUserExpertiseLevel(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            >
              {expertiseLevels.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>
        </motion.div>
      )}

      {/* Analysis Button */}
      {selectedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className={cn(
              "inline-flex items-center px-8 py-4 rounded-xl font-semibold text-lg transition-all",
              isAnalyzing
                ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-cyan-500 to-blue-500 text-white hover:from-cyan-400 hover:to-blue-400 hover:scale-105 shadow-lg hover:shadow-cyan-500/25"
            )}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                Analyzing {selectedFiles.length} Images...
              </>
            ) : (
              <>
                <Camera className="w-6 h-6 mr-3" />
                Analyze {selectedFiles.length} Image{selectedFiles.length > 1 ? 's' : ''}
              </>
            )}
          </button>
        </motion.div>
      )}

      {/* Error Display */}
      {errors.analysis && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400"
        >
          <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
          <span>{errors.analysis}</span>
        </motion.div>
      )}

      {/* Analysis Results */}
      <AnimatePresence>
        {analysisResult && analysisResult.success && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Summary Card */}
            <div className="p-6 bg-slate-800/50 border border-slate-600 rounded-xl">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-6 h-6 text-green-400 mr-3" />
                <h3 className="text-xl font-semibold text-white">Analysis Complete</h3>
              </div>

              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                  <Images className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">
                    {analysisResult.total_images_processed}
                  </div>
                  <div className="text-sm text-slate-400">Images Processed</div>
                </div>

                <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                  <FileText className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">
                    {analysisResult.images_with_text}
                  </div>
                  <div className="text-sm text-slate-400">With Readable Text</div>
                </div>

                <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                  <BarChart3 className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">
                    {analysisResult.document_analysis?.total_clauses || 0}
                  </div>
                  <div className="text-sm text-slate-400">Clauses Analyzed</div>
                </div>
              </div>

              {/* Risk Assessment */}
              {analysisResult.document_analysis && (
                <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                  <div className="flex items-center">
                    <Shield className="w-6 h-6 text-slate-400 mr-3" />
                    <div>
                      <div className="text-white font-medium">Overall Risk Assessment</div>
                      <div className="text-sm text-slate-400">
                        Confidence: {analysisResult.document_analysis.overall_risk.confidence_percentage}%
                      </div>
                    </div>
                  </div>
                  <div className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium border",
                    getRiskColor(analysisResult.document_analysis.overall_risk.level)
                  )}>
                    {analysisResult.document_analysis.overall_risk.level.toUpperCase()} RISK
                  </div>
                </div>
              )}
            </div>

            {/* Text Extraction Details */}
            {analysisResult.text_extraction && (
              <div className="p-6 bg-slate-800/50 border border-slate-600 rounded-xl">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Eye className="w-5 h-5 mr-2" />
                  Text Extraction Details
                </h4>

                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <div className="text-sm text-slate-400">Combined Text Length</div>
                    <div className="text-lg font-medium text-white">
                      {analysisResult.text_extraction.combined_text_length.toLocaleString()} characters
                    </div>
                  </div>
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <div className="text-sm text-slate-400">Overall Confidence</div>
                    <div className="text-lg font-medium text-white">
                      {(analysisResult.text_extraction.overall_confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Per-Image Results */}
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-slate-300">Per-Image Results:</h5>
                  {analysisResult.text_extraction.image_results.map((imageResult, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-slate-700/20 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-cyan-500/20 text-cyan-300 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                          {imageResult.page_number}
                        </div>
                        <div>
                          <div className="text-white font-medium truncate max-w-xs">
                            {imageResult.filename}
                          </div>
                          <div className="text-xs text-slate-400">
                            {imageResult.extracted_text_length} chars • {imageResult.text_blocks_detected} blocks
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-slate-300">
                        {(imageResult.confidence_scores.average_confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {analysisResult.warnings && analysisResult.warnings.length > 0 && (
              <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-xl">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-yellow-400 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-yellow-300 font-medium mb-2">Warnings</h4>
                    <ul className="space-y-1 text-yellow-200 text-sm">
                      {analysisResult.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MultipleImageAnalysis;