import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle,
  Play,
  Zap,
  Shield,
  Globe,
  Image,
  Camera,
  FolderOpen,
  Layers
} from 'lucide-react';
import { cn, formatFileSize } from '../utils';
import { notificationService } from '../services/notificationService';
import { validationService } from '../services/validationService';
import { experienceLevelService, type ExperienceLevel } from '../services/experienceLevelService';
import { VoiceInput } from './VoiceInput';
import MultiFileDropZone from './MultiFileDropZone';

interface MultiDocumentUploadProps {
  onSubmit: (formData: FormData) => void;
  onBatchSubmit?: (files: File[], options: BatchProcessingOptions) => void;
}

interface BatchProcessingOptions {
  documentType: string;
  userExpertiseLevel: ExperienceLevel;
  userQuestions?: string;
  processIndividually: boolean;
  combineResults: boolean;
}

export const MultiDocumentUpload = React.memo(function MultiDocumentUpload({ 
  onSubmit, 
  onBatchSubmit 
}: MultiDocumentUploadProps) {
  const [documentText, setDocumentText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [expertiseLevel, setExpertiseLevel] = useState<ExperienceLevel>(() => 
    experienceLevelService.getCurrentLevel()
  );
  const [userQuestions, setUserQuestions] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [processingMode, setProcessingMode] = useState<'single' | 'batch'>('single');
  const [batchOptions, setBatchOptions] = useState({
    processIndividually: true,
    combineResults: false
  });
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Clean up any object URLs if we were using them
      selectedFiles.forEach(file => {
        if (typeof file === 'object') {
          console.log('Cleaning up file references');
        }
      });
    };
  }, [selectedFiles]);

  // Demo samples
  const demoSamples = {
    rental: `RESIDENTIAL LEASE AGREEMENT

This Lease Agreement is entered into between ABC Property Management ("Landlord") and Tenant.

TERMS AND CONDITIONS:

1. RENT: Tenant agrees to pay $2,500 per month, due on the 1st of each month. Late fees of $150 will be charged for payments received after the 3rd day of the month.

2. SECURITY DEPOSIT: Tenant must pay a security deposit of $5,000, which may be used by Landlord for any damages, unpaid rent, or cleaning fees at Landlord's sole discretion.

3. MAINTENANCE: Tenant is responsible for ALL maintenance and repairs, including major structural repairs, HVAC systems, and appliances, regardless of cause.

4. TERMINATION: Landlord may terminate this lease at any time with 24 hours written notice for any reason or no reason. Tenant must give 60 days notice to terminate.

5. LIABILITY: Tenant assumes all liability for any injuries or damages occurring on the premises, including those caused by Landlord's negligence.`,

    employment: `EMPLOYMENT AGREEMENT

This Employment Agreement is between TechCorp Inc. ("Company") and Employee.

EMPLOYMENT TERMS:

1. POSITION: Employee is hired as Software Developer, reporting to the Engineering Manager.

2. COMPENSATION: Annual salary of $85,000, paid bi-weekly. Performance reviews conducted annually with potential for merit increases.

3. BENEFITS: Health insurance (Company pays 80%), dental and vision coverage, 401(k) with 4% company match, 15 days PTO annually.

4. WORK SCHEDULE: Standard 40-hour work week, Monday-Friday, 9 AM to 5 PM. Flexible work arrangements may be available with supervisor approval.

5. CONFIDENTIALITY: Employee agrees to maintain confidentiality of proprietary information and trade secrets during and after employment.`,

    nda: `NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement is between MegaCorp Industries ("Disclosing Party") and Recipient.

CONFIDENTIALITY TERMS:

1. DEFINITION OF CONFIDENTIAL INFORMATION: All information, data, materials, products, technology, computer programs, software, marketing plans, customer lists, financial information, and any other business information disclosed by Disclosing Party.

2. SCOPE: Recipient agrees that ANY information learned, observed, or accessed during any interaction with Disclosing Party shall be considered confidential, including publicly available information.

3. OBLIGATIONS: Recipient shall not disclose, use, copy, or distribute any confidential information for ANY purpose, including personal use, competitive analysis, or general knowledge.

4. DURATION: This agreement remains in effect INDEFINITELY, even after termination of business relationship.`
  };

  // Helper functions
  const isImageFile = useCallback((file: File) => {
    return file.type.startsWith('image/');
  }, []);

  const getFileStats = useCallback(() => {
    const imageCount = selectedFiles.filter(isImageFile).length;
    const docCount = selectedFiles.length - imageCount;
    return { imageCount, docCount, total: selectedFiles.length };
  }, [selectedFiles, isImageFile]);

  // Event handlers
  const handleFilesSelect = useCallback((files: File[]) => {
    setSelectedFiles(files);
    setErrors(prev => ({ ...prev, files: '' }));
    
    // Auto-switch to batch mode if multiple files
    if (files.length > 1) {
      setProcessingMode('batch');
    } else if (files.length === 1) {
      setProcessingMode('single');
    }
  }, []);

  const handleRemoveFile = useCallback((fileId: string) => {
    // Since we don't have file IDs in the simple array, we'll need to match by name and size
    // This is a simplified approach - in production, you'd want proper file IDs
    setSelectedFiles(prev => {
      const newFiles = [...prev];
      // Remove the first matching file (this is a limitation of the simple approach)
      const index = newFiles.findIndex(f => `${f.name}-${f.size}` === fileId);
      if (index > -1) {
        newFiles.splice(index, 1);
      }
      return newFiles;
    });
  }, []);

  const handleClearAllFiles = useCallback(() => {
    setSelectedFiles([]);
    setProcessingMode('single');
    setErrors(prev => ({ ...prev, files: '' }));
  }, []);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setDocumentText(text);
    setCharCount(text.length);
    
    if (text.length < 100 && text.length > 0) {
      setErrors({ ...errors, text: 'Document text must be at least 100 characters' });
    } else {
      setErrors({ ...errors, text: '' });
    }
  };

  const loadDemoSample = useCallback((sampleType: keyof typeof demoSamples) => {
    try {
      const sampleText = demoSamples[sampleType];
      setDocumentText(sampleText);
      setCharCount(sampleText.length);
      handleClearAllFiles();
      // Clear any text-related errors
      setErrors(prev => ({ ...prev, text: '', documentContent: '' }));
      notificationService.success(`${sampleType.charAt(0).toUpperCase() + sampleType.slice(1)} sample loaded`);
    } catch (error) {
      console.error('Error loading demo sample:', error);
      notificationService.error('Failed to load demo sample');
    }
  }, [handleClearAllFiles]);

  const handleSingleFileSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
   
    try {
      // Validate that we have content
      if (selectedFiles.length === 0 && !documentText.trim()) {
        setErrors({ documentContent: 'Please provide a document or paste text to analyze' });
        notificationService.error('Please provide a document or paste text to analyze');
        return;
      }

      // Clear errors
      setErrors({});

      const formData = new FormData();

      if (selectedFiles.length > 0) {
        const file = selectedFiles[0]; // Use first file for single mode
        
        // Check if it's an image file to use Vision API
        if (isImageFile(file)) {
          // For image files - use Vision API endpoint
          formData.append('file', file);
          formData.append('document_type', 'general_contract');
          formData.append('user_expertise_level', expertiseLevel);
          
          // Mark this as an image upload for Vision API
          formData.append('is_image_upload', 'true');
        } else {
          // For document files - use regular document analysis endpoint
          formData.append('file', file);
          formData.append('document_type', 'general_contract');
          formData.append('user_expertise_level', expertiseLevel);
          
          // Mark this as a file upload
          formData.append('is_file_upload', 'true');
        }
      } else if (documentText.trim()) {
        // For text analysis
        formData.append('document_text', documentText.trim());
        formData.append('document_type', 'general_contract');
        formData.append('user_expertise_level', expertiseLevel);
        
        if (userQuestions.trim()) {
          formData.append('user_questions', userQuestions.trim());
        }
        
        // Mark this as text analysis
        formData.append('is_file_upload', 'false');
      }

      onSubmit(formData);
    } catch (error) {
      console.error('Error submitting form:', error);
      notificationService.error('Failed to submit document. Please try again.');
    }
  }, [selectedFiles, documentText, expertiseLevel, userQuestions, onSubmit, isImageFile]);

  const handleBatchSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (selectedFiles.length === 0) {
      setErrors({ files: 'Please select files for batch processing' });
      notificationService.error('Please select files for batch processing');
      return;
    }

    if (!onBatchSubmit) {
      notificationService.error('Batch processing not supported');
      return;
    }

    const options: BatchProcessingOptions = {
      documentType: 'general_contract',
      userExpertiseLevel: expertiseLevel,
      userQuestions: userQuestions.trim() || undefined,
      processIndividually: batchOptions.processIndividually,
      combineResults: batchOptions.combineResults
    };

    onBatchSubmit(selectedFiles, options);
  }, [selectedFiles, expertiseLevel, userQuestions, batchOptions, onBatchSubmit]);

  const handleSubmit = processingMode === 'batch' ? handleBatchSubmit : handleSingleFileSubmit;

  // Store experience level when it changes
  React.useEffect(() => {
    experienceLevelService.setLevel(expertiseLevel);
  }, [expertiseLevel]);

  const fileStats = getFileStats();

  return (
    <section id="multi-document-upload" className="py-20 relative">
      <div className="container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto"
        >
          {/* Section Header */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-white mb-4">
              Multi-Document Legal Analysis
            </h2>
            <p className="text-xl text-slate-300">
              Upload multiple documents and images for comprehensive AI-powered legal analysis
            </p>
          </div>

          {/* Problem Statement */}
          <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-2xl p-6 mb-8">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Layers className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2">
                  Comprehensive Document Analysis
                </h3>
                <p className="text-slate-300 mb-2">
                  <strong>Enhanced Capability:</strong> Analyze multiple documents simultaneously - contracts, amendments, images, and supporting materials.
                </p>
                <p className="text-slate-300">
                  <strong>Smart Processing:</strong> Automatically routes documents to Document AI and images to Vision API for optimal text extraction and analysis.
                </p>
              </div>
            </div>
          </div>

          {/* Processing Mode Toggle */}
          {selectedFiles.length > 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <div className="bg-slate-800/50 border border-slate-600 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Layers className="w-5 h-5 mr-2" />
                  Processing Mode ({fileStats.total} files selected)
                </h3>
                
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <label className={cn(
                    "flex items-start space-x-3 p-4 rounded-xl border cursor-pointer transition-all",
                    processingMode === 'single'
                      ? "border-cyan-500 bg-cyan-500/10"
                      : "border-slate-600 bg-slate-800/30 hover:border-slate-500"
                  )}>
                    <input
                      type="radio"
                      name="processing_mode"
                      value="single"
                      checked={processingMode === 'single'}
                      onChange={(e) => setProcessingMode(e.target.value as 'single' | 'batch')}
                      className="mt-1 text-cyan-500 focus:ring-cyan-500"
                    />
                    <div>
                      <div className="font-semibold text-white">Single Document</div>
                      <div className="text-sm text-slate-400">Analyze first document only</div>
                    </div>
                  </label>

                  <label className={cn(
                    "flex items-start space-x-3 p-4 rounded-xl border cursor-pointer transition-all",
                    processingMode === 'batch'
                      ? "border-cyan-500 bg-cyan-500/10"
                      : "border-slate-600 bg-slate-800/30 hover:border-slate-500"
                  )}>
                    <input
                      type="radio"
                      name="processing_mode"
                      value="batch"
                      checked={processingMode === 'batch'}
                      onChange={(e) => setProcessingMode(e.target.value as 'single' | 'batch')}
                      className="mt-1 text-cyan-500 focus:ring-cyan-500"
                    />
                    <div>
                      <div className="font-semibold text-white">Batch Processing</div>
                      <div className="text-sm text-slate-400">Analyze all {fileStats.total} documents</div>
                    </div>
                  </label>
                </div>

                {/* File Statistics */}
                <div className="flex items-center justify-center space-x-6 text-sm text-slate-400 mb-4">
                  {fileStats.docCount > 0 && (
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 mr-1" />
                      {fileStats.docCount} document{fileStats.docCount > 1 ? 's' : ''}
                    </div>
                  )}
                  {fileStats.imageCount > 0 && (
                    <div className="flex items-center">
                      <Camera className="w-4 h-4 mr-1" />
                      {fileStats.imageCount} image{fileStats.imageCount > 1 ? 's' : ''}
                    </div>
                  )}
                </div>

                {/* Batch Options */}
                {processingMode === 'batch' && (
                  <div className="space-y-3 pt-4 border-t border-slate-600">
                    <h4 className="font-medium text-white">Batch Options</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={batchOptions.processIndividually}
                          onChange={(e) => setBatchOptions(prev => ({
                            ...prev,
                            processIndividually: e.target.checked
                          }))}
                          className="text-cyan-500 focus:ring-cyan-500"
                        />
                        <span className="text-sm text-slate-300">Process individually</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={batchOptions.combineResults}
                          onChange={(e) => setBatchOptions(prev => ({
                            ...prev,
                            combineResults: e.target.checked
                          }))}
                          className="text-cyan-500 focus:ring-cyan-500"
                        />
                        <span className="text-sm text-slate-300">Combine results</span>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Main Form */}
          <form 
            onSubmit={handleSubmit} 
            className="space-y-8"
            aria-label="Multi-document legal analysis form"
            noValidate
          >
            {/* Multi-File Upload Area */}
            <MultiFileDropZone
              onFilesSelect={handleFilesSelect}
              selectedFiles={selectedFiles}
              onRemoveFile={handleRemoveFile}
              onClearAll={handleClearAllFiles}
              errors={errors}
              maxFiles={10}
              allowMixedTypes={true}
            />

            {/* Text Input */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-lg font-semibold text-white">
                  Or Paste Document Text
                </label>
                <div className="flex items-center space-x-3">
                  <VoiceInput
                    onTranscript={(transcript) => {
                      const newText = documentText + ' ' + transcript;
                      setDocumentText(newText);
                      setCharCount(newText.length);
                    }}
                    onError={(error) => setErrors({ ...errors, voice: error })}
                    language="en-US"
                    forceEnglish={true}
                    showLanguageSelector={true}
                    onLanguageChange={(language) => {
                      console.log('Voice input language changed to:', language);
                    }}
                  />
                  <span className="text-sm text-slate-400">Alternative to file upload</span>
                </div>
              </div>
              
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={documentText}
                  onChange={handleTextChange}
                  placeholder="Paste your legal document text here (rental agreement, employment contract, NDA, etc.)..."
                  className="w-full h-64 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none transition-all"
                  maxLength={50000}
                  id="document-text-input"
                  aria-label="Legal document text input"
                  aria-describedby="text-input-description text-char-count"
                  aria-invalid={errors.text ? 'true' : 'false'}
                />
              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400" id="text-input-description">
                  Please ensure you provide the complete legal document for accurate analysis.
                </span>
                <span 
                  className={cn(
                    "font-mono",
                    charCount > 45000 ? "text-red-400" : "text-slate-400"
                  )}
                  id="text-char-count"
                  aria-label={`Character count: ${charCount.toLocaleString()} of 50,000 characters used`}
                >
                  {charCount.toLocaleString()} / 50,000 characters
                </span>
              </div>
              
              {errors.text && (
                <div className="flex items-center text-red-400 text-sm" role="alert" aria-live="assertive">
                  <AlertCircle className="w-4 h-4 mr-2" aria-hidden="true" />
                  <span id="text-error-message">{errors.text}</span>
                </div>
              )}
              
              {errors.voice && (
                <div className="flex items-center text-red-400 text-sm" role="alert" aria-live="assertive">
                  <AlertCircle className="w-4 h-4 mr-2" aria-hidden="true" />
                  <span id="voice-error-message">{errors.voice}</span>
                </div>
              )}
            </div>

            {/* Expertise Level */}
            <fieldset className="space-y-4">
              <legend className="text-lg font-semibold text-white">
                Your Experience Level (Optional)
              </legend>
              <div className="grid md:grid-cols-3 gap-4" role="radiogroup" aria-labelledby="expertise-level-description">
                {experienceLevelService.getAvailableLevels().map((levelInfo) => (
                  <label
                    key={levelInfo.level}
                    className={cn(
                      "flex items-start space-x-3 p-4 rounded-xl border cursor-pointer transition-all focus-within:ring-2 focus-within:ring-cyan-500",
                      expertiseLevel === levelInfo.level
                        ? "border-cyan-500 bg-cyan-500/10"
                        : "border-slate-600 bg-slate-800/30 hover:border-slate-500"
                    )}
                  >
                    <input
                      type="radio"
                      name="expertise_level"
                      value={levelInfo.level}
                      checked={expertiseLevel === levelInfo.level}
                      onChange={(e) => setExpertiseLevel(e.target.value as ExperienceLevel)}
                      className="mt-1 text-cyan-500 focus:ring-cyan-500"
                      aria-describedby={`expertise-${levelInfo.level}-desc`}
                    />
                    <div>
                      <div className="font-semibold text-white">{levelInfo.label}</div>
                      <div className="text-sm text-slate-400" id={`expertise-${levelInfo.level}-desc`}>{levelInfo.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-sm text-slate-400 flex items-center" id="expertise-level-description">
                <AlertCircle className="w-4 h-4 mr-2" aria-hidden="true" />
                This helps us adapt our explanations to your knowledge level
              </p>
            </fieldset>

            {/* User Questions */}
            <div className="space-y-4">
              <label htmlFor="user-questions-input" className="text-lg font-semibold text-white">
                Any Specific Questions? (Optional)
              </label>
              <textarea
                id="user-questions-input"
                value={userQuestions}
                onChange={(e) => setUserQuestions(e.target.value)}
                placeholder="e.g., What does this clause mean? Are these terms fair? What are my rights?"
                className="w-full h-24 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none transition-all"
                aria-describedby="user-questions-description"
              />
              <p className="text-sm text-slate-400" id="user-questions-description">
                Ask any questions about legal terms or specific clauses you're concerned about
              </p>
            </div>

            {/* Submit Button */}
            <div className="text-center">
              <button
                type="submit"
                className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl hover:from-cyan-400 hover:to-blue-400 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/25 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                aria-describedby="submit-button-description"
              >
                <Zap className="w-5 h-5 mr-2" aria-hidden="true" />
                {processingMode === 'batch' && selectedFiles.length > 1 
                  ? `Analyze ${selectedFiles.length} Documents` 
                  : 'Analyze Document'
                }
              </button>
              <p className="sr-only" id="submit-button-description">
                Submit your documents for AI-powered legal analysis
              </p>
            </div>
          </form>

          {/* Demo Mode Section */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="mt-16"
          >
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-2xl p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2 flex items-center justify-center" id="demo-section-title">
                  <Play className="w-6 h-6 mr-3" aria-hidden="true" />
                  Try Our Demo Mode
                </h3>
                <p className="text-slate-300" id="demo-section-description">
                  Experience our AI analysis with sample documents
                </p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-4 mb-6" role="group" aria-labelledby="demo-section-title" aria-describedby="demo-section-description">
                <button
                  type="button"
                  onClick={() => loadDemoSample('rental')}
                  className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl hover:bg-red-500/30 transition-all group focus:outline-none focus:ring-2 focus:ring-red-500"
                  aria-label="Load rental agreement demo sample with unfavorable lease terms"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" aria-hidden="true" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">Rental Agreement</h4>
                    <p className="text-sm text-red-400">Unfavorable lease terms</p>
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => loadDemoSample('employment')}
                  className="p-4 bg-green-500/20 border border-green-500/50 rounded-xl hover:bg-green-500/30 transition-all group focus:outline-none focus:ring-2 focus:ring-green-500"
                  aria-label="Load employment contract demo sample with standard terms"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" aria-hidden="true" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">Employment Contract</h4>
                    <p className="text-sm text-green-400">Standard terms</p>
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => loadDemoSample('nda')}
                  className="p-4 bg-yellow-500/20 border border-yellow-500/50 rounded-xl hover:bg-yellow-500/30 transition-all group focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  aria-label="Load NDA agreement demo sample with overly broad terms"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-yellow-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" aria-hidden="true" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">NDA Agreement</h4>
                    <p className="text-sm text-yellow-400">Overly broad terms</p>
                  </div>
                </button>
              </div>
              
              <div className="text-center">
                <p className="text-sm text-slate-400 flex items-center justify-center">
                  <Globe className="w-4 h-4 mr-2" aria-hidden="true" />
                  These samples demonstrate different risk levels and analysis capabilities
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
});

export default MultiDocumentUpload;