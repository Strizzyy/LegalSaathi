import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FolderOpen, 
  FileText, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  Camera,
  Layers,
  BarChart3,
  Clock,
  Users
} from 'lucide-react';
import MultiFileDropZone from './MultiFileDropZone';
import { apiService } from '../services/apiService';
import { processingNotificationService } from '../services/processingNotificationService';

interface ProcessingResult {
  file: File;
  result: any;
  error?: string;
  processingTime: number;
}

export const MultiFileDemo = React.memo(function MultiFileDemo() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<ProcessingResult[]>([]);
  const [processingProgress, setProcessingProgress] = useState(0);

  const handleFilesSelect = (files: File[]) => {
    setSelectedFiles(files);
    setErrors({});
    setResults([]);
    setProcessingProgress(0);
    
    // Show file type notifications
    if (files.length > 0) {
      processingNotificationService.showFileTypeNotifications(files);
    }
  };

  const handleRemoveFile = (fileId: string) => {
    // Simple removal by matching name-size combination
    setSelectedFiles(prev => {
      const newFiles = [...prev];
      const index = newFiles.findIndex(f => `${f.name}-${f.size}` === fileId);
      if (index > -1) {
        newFiles.splice(index, 1);
      }
      return newFiles;
    });
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    setErrors({});
    setResults([]);
    setProcessingProgress(0);
  };

  const processFile = async (file: File): Promise<ProcessingResult> => {
    const startTime = Date.now();
    
    try {
      const isImage = file.type.startsWith('image/');
      
      if (isImage) {
        // Process image with Vision API
        const result = await apiService.extractTextFromImage(file);
        return {
          file,
          result,
          processingTime: Date.now() - startTime
        };
      } else {
        // Process document with Document AI
        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_type', 'general_contract');
        formData.append('user_expertise_level', 'beginner');
        formData.append('is_file_upload', 'true');

        const result = await apiService.analyzeDocument(formData);
        return {
          file,
          result,
          processingTime: Date.now() - startTime
        };
      }
    } catch (error) {
      return {
        file,
        result: null,
        error: error instanceof Error ? error.message : 'Processing failed',
        processingTime: Date.now() - startTime
      };
    }
  };

  const handleBatchProcess = async () => {
    if (selectedFiles.length === 0) return;

    setIsProcessing(true);
    setResults([]);
    setProcessingProgress(0);

    const processedResults: ProcessingResult[] = [];

    // Process files sequentially to avoid overwhelming the API
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      
      try {
        const result = await processFile(file);
        processedResults.push(result);
        setResults([...processedResults]);
        setProcessingProgress(((i + 1) / selectedFiles.length) * 100);
      } catch (error) {
        processedResults.push({
          file,
          result: null,
          error: error instanceof Error ? error.message : 'Processing failed',
          processingTime: 0
        });
      }
    }

    setIsProcessing(false);
  };

  const handleParallelProcess = async () => {
    if (selectedFiles.length === 0) return;

    setIsProcessing(true);
    setResults([]);
    setProcessingProgress(0);

    try {
      // Process all files in parallel
      const promises = selectedFiles.map(file => processFile(file));
      const results = await Promise.all(promises);
      
      setResults(results);
      setProcessingProgress(100);
    } catch (error) {
      console.error('Parallel processing error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const getFileStats = () => {
    const imageCount = selectedFiles.filter(f => f.type.startsWith('image/')).length;
    const docCount = selectedFiles.length - imageCount;
    return { imageCount, docCount, total: selectedFiles.length };
  };

  const getResultStats = () => {
    const successful = results.filter(r => r.result && !r.error).length;
    const failed = results.filter(r => r.error).length;
    const avgProcessingTime = results.length > 0 
      ? results.reduce((sum, r) => sum + r.processingTime, 0) / results.length 
      : 0;
    
    return { successful, failed, avgProcessingTime };
  };

  const fileStats = getFileStats();
  const resultStats = getResultStats();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            📁 Multi-File Processing Demo
          </h1>
          <p className="text-xl text-slate-300">
            Test batch processing with multiple documents and images
          </p>
        </motion.div>

        {/* Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <MultiFileDropZone
            onFilesSelect={handleFilesSelect}
            selectedFiles={selectedFiles}
            onRemoveFile={handleRemoveFile}
            onClearAll={handleClearAll}
            errors={errors}
            maxFiles={10}
            allowMixedTypes={true}
          />
        </motion.div>

        {/* File Statistics */}
        {selectedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="grid md:grid-cols-4 gap-4 mb-8"
          >
            <div className="bg-slate-800/50 border border-slate-600 rounded-xl p-4 text-center">
              <FolderOpen className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{fileStats.total}</div>
              <div className="text-sm text-slate-400">Total Files</div>
            </div>
            
            <div className="bg-slate-800/50 border border-slate-600 rounded-xl p-4 text-center">
              <FileText className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{fileStats.docCount}</div>
              <div className="text-sm text-slate-400">Documents</div>
            </div>
            
            <div className="bg-slate-800/50 border border-slate-600 rounded-xl p-4 text-center">
              <Camera className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{fileStats.imageCount}</div>
              <div className="text-sm text-slate-400">Images</div>
            </div>
            
            <div className="bg-slate-800/50 border border-slate-600 rounded-xl p-4 text-center">
              <BarChart3 className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">
                {Math.round(processingProgress)}%
              </div>
              <div className="text-sm text-slate-400">Progress</div>
            </div>
          </motion.div>
        )}

        {/* Processing Controls */}
        {selectedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-center space-x-4 mb-8"
          >
            <button
              onClick={handleBatchProcess}
              disabled={isProcessing}
              className="inline-flex items-center px-6 py-3 text-lg font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl hover:from-cyan-400 hover:to-blue-400 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/25 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                <>
                  <Layers className="w-5 h-5 mr-2" />
                  Sequential Processing
                </>
              )}
            </button>

            <button
              onClick={handleParallelProcess}
              disabled={isProcessing}
              className="inline-flex items-center px-6 py-3 text-lg font-semibold text-white bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl hover:from-purple-400 hover:to-pink-400 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-purple-500/25 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  Parallel Processing
                </>
              )}
            </button>
          </motion.div>
        )}

        {/* Processing Progress */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <div className="bg-slate-800/50 border border-slate-600 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Processing Files...</h3>
                <span className="text-slate-400">{Math.round(processingProgress)}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${processingProgress}%` }}
                ></div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Result Statistics */}
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-green-500/20 border border-green-500/50 rounded-xl p-4 text-center">
                <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{resultStats.successful}</div>
                <div className="text-sm text-green-400">Successful</div>
              </div>
              
              <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4 text-center">
                <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{resultStats.failed}</div>
                <div className="text-sm text-red-400">Failed</div>
              </div>
              
              <div className="bg-blue-500/20 border border-blue-500/50 rounded-xl p-4 text-center">
                <Clock className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">
                  {Math.round(resultStats.avgProcessingTime)}ms
                </div>
                <div className="text-sm text-blue-400">Avg Time</div>
              </div>
            </div>

            {/* Individual Results */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-white flex items-center">
                <BarChart3 className="w-6 h-6 mr-2" />
                Processing Results
              </h3>
              
              <div className="grid gap-4 max-h-96 overflow-y-auto">
                {results.map((result, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-4 rounded-xl border ${
                      result.error 
                        ? 'bg-red-500/10 border-red-500/30' 
                        : 'bg-green-500/10 border-green-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {result.error ? (
                            <AlertTriangle className="w-5 h-5 text-red-400" />
                          ) : (
                            <CheckCircle className="w-5 h-5 text-green-400" />
                          )}
                          <h4 className="font-medium text-white">{result.file.name}</h4>
                          <span className="text-xs text-slate-400">
                            ({Math.round(result.processingTime)}ms)
                          </span>
                        </div>
                        
                        {result.error ? (
                          <p className="text-red-400 text-sm">{result.error}</p>
                        ) : (
                          <div className="space-y-2">
                            {result.result?.extracted_text && (
                              <div>
                                <p className="text-sm text-slate-400">Extracted Text:</p>
                                <p className="text-sm text-slate-300 truncate">
                                  {result.result.extracted_text.substring(0, 100)}...
                                </p>
                              </div>
                            )}
                            
                            {result.result?.confidence_scores && (
                              <div>
                                <p className="text-sm text-slate-400">Confidence:</p>
                                <p className="text-sm text-slate-300">
                                  {Math.round(result.result.confidence_scores.average_confidence * 100)}%
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div className="text-right">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          result.file.type.startsWith('image/')
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                            : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        }`}>
                          {result.file.type.startsWith('image/') ? (
                            <>
                              <Camera className="w-3 h-3 mr-1" />
                              Vision API
                            </>
                          ) : (
                            <>
                              <FileText className="w-3 h-3 mr-1" />
                              Document AI
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-2xl p-6"
        >
          <h3 className="text-xl font-bold text-white mb-4 flex items-center">
            <Users className="w-6 h-6 mr-2" />
            How to Test Multi-File Processing
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-slate-300">
            <div>
              <h4 className="font-semibold text-white mb-2">📄 Sequential Processing</h4>
              <ul className="space-y-1 text-sm">
                <li>• Processes files one by one</li>
                <li>• Safer for API rate limits</li>
                <li>• Shows progress as each file completes</li>
                <li>• Better for large batches</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">⚡ Parallel Processing</h4>
              <ul className="space-y-1 text-sm">
                <li>• Processes all files simultaneously</li>
                <li>• Faster for small batches</li>
                <li>• May hit rate limits with many files</li>
                <li>• Shows results when all complete</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
            <h4 className="font-semibold text-white mb-2">💡 Tips for Testing</h4>
            <ul className="space-y-1 text-sm text-slate-300">
              <li>• Mix documents (PDF, DOC) and images (JPEG, PNG) to see different processing methods</li>
              <li>• Try both processing modes to compare performance</li>
              <li>• Check confidence scores for image text extraction quality</li>
              <li>• Monitor processing times for different file types</li>
            </ul>
          </div>
        </motion.div>
      </div>
    </div>
  );
});

export default MultiFileDemo;