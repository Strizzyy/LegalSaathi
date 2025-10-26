import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Camera, FileText, Zap, CheckCircle, AlertTriangle } from 'lucide-react';
import UniversalDropZone from './UniversalDropZone';
import { apiService } from '../services/apiService';

export const ImageUploadDemo = React.memo(function ImageUploadDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setErrors({});
    setResult(null);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setErrors({});
    setResult(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setResult(null);

    try {
      const isImage = selectedFile.type.startsWith('image/');
      
      if (isImage) {
        // Test Vision API text extraction
        const extractResult = await apiService.extractTextFromImage(selectedFile);
        
        if (extractResult.success) {
          setResult({
            type: 'vision_extraction',
            data: extractResult,
            message: 'Text extracted successfully using Vision API!'
          });
        } else {
          setResult({
            type: 'error',
            message: extractResult.error || 'Vision API extraction failed'
          });
        }
      } else {
        // Test regular document analysis
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('document_type', 'general_contract');
        formData.append('user_expertise_level', 'beginner');
        formData.append('is_file_upload', 'true');

        const analysisResult = await apiService.analyzeDocument(formData);
        
        if (analysisResult.success) {
          setResult({
            type: 'document_analysis',
            data: analysisResult,
            message: 'Document analyzed successfully!'
          });
        } else {
          setResult({
            type: 'error',
            message: analysisResult.error || 'Document analysis failed'
          });
        }
      }
    } catch (error) {
      setResult({
        type: 'error',
        message: error instanceof Error ? error.message : 'Analysis failed'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const isImage = selectedFile?.type.startsWith('image/');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            🖼️ Image & Document Upload Demo
          </h1>
          <p className="text-xl text-slate-300">
            Test drag & drop functionality with Vision API integration
          </p>
        </motion.div>

        {/* Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <UniversalDropZone
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
            onClearFile={handleClearFile}
            errors={errors}
          />
        </motion.div>

        {/* Action Button */}
        {selectedFile && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center mb-8"
          >
            <button
              onClick={handleAnalyze}
              disabled={isProcessing}
              className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl hover:from-cyan-400 hover:to-blue-400 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/25 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  {isImage ? 'Extracting Text...' : 'Analyzing Document...'}
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  {isImage ? 'Extract Text (Vision API)' : 'Analyze Document'}
                </>
              )}
            </button>
          </motion.div>
        )}

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-800/50 border border-slate-600 rounded-2xl p-6"
          >
            <div className="flex items-center mb-4">
              {result.type === 'error' ? (
                <AlertTriangle className="w-6 h-6 text-red-400 mr-2" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-400 mr-2" />
              )}
              <h3 className="text-xl font-semibold text-white">
                {result.type === 'error' ? 'Error' : 'Success'}
              </h3>
            </div>

            <p className="text-slate-300 mb-4">{result.message}</p>

            {result.type === 'vision_extraction' && result.data && (
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-white mb-2">Extracted Text:</h4>
                  <div className="bg-slate-900/50 p-4 rounded-lg">
                    <p className="text-slate-300 whitespace-pre-wrap">
                      {result.data.extracted_text || 'No text detected'}
                    </p>
                  </div>
                </div>

                {result.data.confidence_scores && (
                  <div>
                    <h4 className="font-semibold text-white mb-2">Confidence Scores:</h4>
                    <div className="bg-slate-900/50 p-4 rounded-lg">
                      <pre className="text-slate-300 text-sm">
                        {JSON.stringify(result.data.confidence_scores, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {result.data.warnings && result.data.warnings.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-yellow-400 mb-2">Warnings:</h4>
                    <ul className="list-disc list-inside text-yellow-300">
                      {result.data.warnings.map((warning: string, index: number) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {result.type === 'document_analysis' && result.data && (
              <div>
                <h4 className="font-semibold text-white mb-2">Analysis Result:</h4>
                <div className="bg-slate-900/50 p-4 rounded-lg">
                  <pre className="text-slate-300 text-sm overflow-auto max-h-96">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}
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
            <Camera className="w-6 h-6 mr-2" />
            How to Test
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-slate-300">
            <div>
              <h4 className="font-semibold text-white mb-2">📄 Document Files</h4>
              <ul className="space-y-1 text-sm">
                <li>• Drag & drop PDF, DOC, DOCX, or TXT files</li>
                <li>• Uses Document AI for analysis</li>
                <li>• Max size: 10MB</li>
                <li>• Full legal document analysis</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">🖼️ Image Files</h4>
              <ul className="space-y-1 text-sm">
                <li>• Drag & drop JPEG, PNG, WEBP, BMP, or GIF</li>
                <li>• Uses Vision API for OCR text extraction</li>
                <li>• Max size: 20MB</li>
                <li>• Perfect for screenshots or photos of documents</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
});

export default ImageUploadDemo;