import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  AlertCircle,
  Zap,
  Globe,
  Images,
  Camera
} from 'lucide-react';
import { cn } from '../utils';
import { notificationService } from '../services/notificationService';
import { experienceLevelService, type ExperienceLevel } from '../services/experienceLevelService';
import { VoiceInput } from './VoiceInput';
import UniversalDropZone from './UniversalDropZone';
import { MultiFileDropZone } from './MultiFileDropZone';
import { useBackendReadiness } from '../hooks/useBackendReadiness';

interface DocumentUploadProps {
  onSubmit: (formData: FormData) => void;
}

export const DocumentUpload = React.memo(function DocumentUpload({ onSubmit }: DocumentUploadProps) {
  const [documentText, setDocumentText] = useState('');
  const [selectedFile, setSelectedFile] = useState<globalThis.File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<globalThis.File[]>([]);
  const [isMultipleMode, setIsMultipleMode] = useState(false);
  const [expertiseLevel, setExpertiseLevel] = useState<ExperienceLevel>(() =>
    experienceLevelService.getCurrentLevel()
  );

  const [charCount, setCharCount] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Backend readiness state
  const { isReady: isBackendReady, isChecking: isBackendChecking, waitForBackend } = useBackendReadiness();

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Clean up any object URLs if we were using them
      if (selectedFile && typeof selectedFile === 'object') {
        console.log('Cleaning up file references');
      }
    };
  }, [selectedFile]);

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

  // Helper function to check if file is an image
  const isImageFile = useCallback((file: File) => {
    return file.type.startsWith('image/');
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
    setSelectedFiles([]);
    setIsMultipleMode(false);
    setErrors(prev => ({ ...prev, file: '' }));
  }, []);

  const handleMultipleFilesSelect = useCallback((files: File[]) => {
    // The MultiFileDropZone already filters and validates files
    // We just need to update our state with the complete list
    console.log('Received files from MultiFileDropZone:', files.length, files.map(f => f.name));
    setSelectedFiles(files);
    setSelectedFile(null);
    setIsMultipleMode(true);
    setErrors(prev => ({ ...prev, file: '' }));
  }, []);

  const handleRemoveMultipleFile = useCallback((fileId: string) => {
    // Find the file to remove by matching the fileId with file properties
    // Since MultiFileDropZone creates IDs like `${file.name}-${Date.now()}-${Math.random()}`
    // we need to remove the file from our selectedFiles array
    console.log('Remove file requested:', fileId);

    // The MultiFileDropZone will handle the removal internally and call onFilesSelect with updated list
    // We don't need to do anything here as the updated list will come through handleMultipleFilesSelect
  }, []);

  const handleClearAllFiles = useCallback(() => {
    setSelectedFiles([]);
    setSelectedFile(null);
    setIsMultipleMode(false);
    setErrors(prev => ({ ...prev, file: '' }));
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

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setSelectedFiles([]);
    setIsMultipleMode(false);
    // Clear any file-related errors
    setErrors(prev => ({ ...prev, file: '' }));
  }, []);

  const loadDemoSample = useCallback((sampleType: keyof typeof demoSamples) => {
    try {
      const sampleText = demoSamples[sampleType];
      setDocumentText(sampleText);
      setCharCount(sampleText.length);
      clearFile();
      // Clear any text-related errors
      setErrors(prev => ({ ...prev, text: '', documentContent: '' }));
      notificationService.success(`${sampleType.charAt(0).toUpperCase() + sampleType.slice(1)} sample loaded`);
    } catch (error) {
      console.error('Error loading demo sample:', error);
      notificationService.error('Failed to load demo sample');
    }
  }, [clearFile]);




  const handleSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      // Check if backend is ready
      if (!isBackendReady) {
        notificationService.info('Waiting for backend services to initialize...', { duration: 3000 });
        const backendReady = await waitForBackend(30000); // 30 second timeout

        if (!backendReady) {
          notificationService.error('Backend services are not ready. Please try again in a moment.');
          return;
        }
      }

      // Add a small delay to ensure state is properly updated
      await new Promise(resolve => setTimeout(resolve, 100));

      // Get current state values to avoid stale closures
      const currentSelectedFiles = selectedFiles;
      const currentSelectedFile = selectedFile;
      const currentDocumentText = documentText.trim();

      console.log('Form submission - Current state:', {
        selectedFiles: currentSelectedFiles.length,
        selectedFile: currentSelectedFile?.name,
        documentText: currentDocumentText.length
      });

      // Validate that we have content
      if (!currentSelectedFile && currentSelectedFiles.length === 0 && !currentDocumentText) {
        setErrors({ documentContent: 'Please provide a document or paste text to analyze' });
        notificationService.error('Please provide a document or paste text to analyze');
        return;
      }

      // Clear errors
      setErrors({});

      const formData = new FormData();

      if (currentSelectedFiles.length > 0) {
        console.log('Submitting multiple images:', currentSelectedFiles.length, currentSelectedFiles.map(f => f.name));

        // Multiple image files - use multiple image analysis endpoint
        currentSelectedFiles.forEach((file, index) => {
          console.log(`Appending file ${index + 1}:`, file.name, file.size);
          formData.append('files', file);
        });
        formData.append('document_type', 'general_contract');
        formData.append('user_expertise_level', expertiseLevel);

        // Mark this as multiple image upload
        formData.append('is_multiple_image_upload', 'true');

        console.log('FormData for multiple images prepared, files count:', formData.getAll('files').length);
      } else if (currentSelectedFile) {
        // Single file
        if (isImageFile(currentSelectedFile)) {
          // For image files - use Vision API endpoint
          formData.append('file', currentSelectedFile);
          formData.append('document_type', 'general_contract');
          formData.append('user_expertise_level', expertiseLevel);

          // Mark this as an image upload for Vision API
          formData.append('is_image_upload', 'true');
        } else {
          // For document files - use regular document analysis endpoint
          formData.append('file', currentSelectedFile); // Backend expects 'file'
          formData.append('document_type', 'general_contract');
          formData.append('user_expertise_level', expertiseLevel);

          // Mark this as a file upload
          formData.append('is_file_upload', 'true');
        }
      } else if (currentDocumentText) {
        // For text analysis - use the correct field name that your backend expects
        formData.append('document_text', currentDocumentText); // Backend expects 'document_text'
        formData.append('document_type', 'general_contract');
        formData.append('user_expertise_level', expertiseLevel);



        // Mark this as text analysis
        formData.append('is_file_upload', 'false');
      }

      onSubmit(formData);
    } catch (error) {
      console.error('Error submitting form:', error);
      notificationService.error('Failed to submit document. Please try again.');
    }
  }, [selectedFile, selectedFiles, documentText, expertiseLevel, onSubmit, isImageFile]);

  // Store experience level when it changes
  React.useEffect(() => {
    experienceLevelService.setLevel(expertiseLevel);
  }, [expertiseLevel]);

  return (
    <section id="document-upload" className="py-12 relative">
      <div className="container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto"
        >
          {/* Compact Section Header */}
          <div className="text-center mb-10">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Upload & Analyze Your{' '}
              <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                Legal Documents
              </span>
            </h2>
            <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
              Instant AI analysis with risk assessment and plain-language explanations
            </p>
            <div className="flex flex-wrap items-center justify-center gap-6 text-slate-400 text-sm">
              <div className="flex items-center">
                <FileText className="w-4 h-4 mr-2 text-cyan-400" />
                <span>Documents & PDFs</span>
              </div>
              <div className="flex items-center">
                <Images className="w-4 h-4 mr-2 text-emerald-400" />
                <span>Multiple Images (OCR)</span>
              </div>
              <div className="flex items-center">
                <Camera className="w-4 h-4 mr-2 text-purple-400" />
                <span>Vision AI Analysis</span>
              </div>
            </div>
          </div>

          {/* Main Form */}
          <form
            onSubmit={handleSubmit}
            className="space-y-6"
            aria-label="Legal document analysis form"
            noValidate
          >
            {/* Enhanced File Upload Mode Toggle */}
            <div className="flex items-center justify-center mb-8">
              <div className="bg-slate-800/30 backdrop-blur-sm p-1 rounded-2xl border border-slate-700/50">
                <div className="flex space-x-1">
                  <button
                    type="button"
                    onClick={() => {
                      setIsMultipleMode(false);
                      setSelectedFiles([]);
                    }}
                    className={cn(
                      "px-8 py-4 rounded-xl font-semibold transition-all duration-300 flex items-center",
                      !isMultipleMode
                        ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg"
                        : "text-slate-400 hover:text-white"
                    )}
                  >
                    <FileText className="w-5 h-5 mr-2" />
                    Single Document
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsMultipleMode(true);
                      setSelectedFile(null);
                    }}
                    className={cn(
                      "px-8 py-4 rounded-xl font-semibold transition-all duration-300 flex items-center",
                      isMultipleMode
                        ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg"
                        : "text-slate-400 hover:text-white"
                    )}
                  >
                    <Images className="w-5 h-5 mr-2" />
                    Multiple Images
                  </button>
                </div>
              </div>
            </div>

            {/* File Upload Area */}
            {isMultipleMode ? (
              <MultiFileDropZone
                key="multiple-mode" // Force re-render when switching modes
                onFilesSelect={handleMultipleFilesSelect}
                selectedFiles={selectedFiles}
                onRemoveFile={handleRemoveMultipleFile}
                onClearAll={handleClearAllFiles}
                errors={errors}
                maxFiles={10}
                allowMixedTypes={false} // Only images for multiple mode
              />
            ) : (
              <UniversalDropZone
                key="single-mode" // Force re-render when switching modes
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                onClearFile={clearFile}
                errors={errors}
              />
            )}

            {/* Text Input */}
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-white mb-4">
                  Or Paste Document Text
                </h3>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <button
                    type="button"
                    className="group flex items-center bg-gradient-to-r from-cyan-500/20 to-blue-500/20 backdrop-blur-sm px-6 py-3 rounded-2xl border border-cyan-500/30 hover:border-cyan-400/50 hover:from-cyan-500/30 hover:to-blue-500/30 transition-all duration-300 text-cyan-300 hover:text-cyan-200 shadow-lg hover:shadow-cyan-500/25"
                    title="Use voice input to dictate your document"
                  >
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
                    <span className="text-sm font-semibold ml-3">Voice Input</span>
                  </button>
                  
                  <button
                    type="button"
                    className="group flex items-center bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm px-6 py-3 rounded-2xl border border-purple-500/30 hover:border-purple-400/50 hover:from-purple-500/30 hover:to-pink-500/30 transition-all duration-300 text-purple-300 hover:text-purple-200 shadow-lg hover:shadow-purple-500/25"
                    title="Translate document to different languages"
                  >
                    <Globe className="w-5 h-5" />
                    <span className="text-sm font-semibold ml-3">Translate</span>
                  </button>
                </div>
              </div>

              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={documentText}
                  onChange={handleTextChange}
                  placeholder="Paste your legal document text here (rental agreement, employment contract, NDA, etc.)..."
                  className="w-full h-48 px-6 py-4 bg-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-2xl text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none transition-all duration-300 hover:bg-slate-800/60"
                  maxLength={50000}
                  id="document-text-input"
                  aria-label="Legal document text input"
                  aria-describedby="text-input-description text-char-count"
                  aria-invalid={errors.text ? 'true' : 'false'}
                />
              </div>

              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 text-sm">
                <span className="text-slate-400" id="text-input-description">
                  💡 Provide complete document for accurate analysis
                </span>
                <div className="flex items-center space-x-2">
                  <div className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium",
                    charCount > 45000 
                      ? "bg-red-500/20 text-red-400 border border-red-500/30" 
                      : charCount > 0 
                        ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                        : "bg-slate-700/50 text-slate-400 border border-slate-600/30"
                  )}>
                    {charCount.toLocaleString()} / 50,000
                  </div>
                </div>
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

            {/* Enhanced Expertise Level */}
            <fieldset className="space-y-4">
              <legend className="text-lg font-semibold text-white">
                Your Experience Level (Optional)
              </legend>
              <div className="grid md:grid-cols-3 gap-4" role="radiogroup">
                {experienceLevelService.getAvailableLevels().map((levelInfo) => (
                  <label
                    key={levelInfo.level}
                    className={cn(
                      "flex items-start space-x-3 p-4 rounded-xl border cursor-pointer transition-all focus-within:ring-2 focus-within:ring-cyan-500 hover:transform hover:scale-105",
                      expertiseLevel === levelInfo.level
                        ? "border-cyan-500 bg-cyan-500/10 shadow-lg shadow-cyan-500/25"
                        : "border-slate-600 bg-slate-800/30 hover:border-slate-500 hover:bg-slate-800/50"
                    )}
                  >
                    <input
                      type="radio"
                      name="expertise_level"
                      value={levelInfo.level}
                      checked={expertiseLevel === levelInfo.level}
                      onChange={(e) => setExpertiseLevel(e.target.value as ExperienceLevel)}
                      className="mt-1 text-cyan-500 focus:ring-cyan-500"
                    />
                    <div>
                      <div className="font-semibold text-white">{levelInfo.label}</div>
                      <div className="text-sm text-slate-400 mt-1">{levelInfo.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-sm text-slate-400 flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" />
                AI responses will be adapted with explanations based on your experience level
              </p>
            </fieldset>



            {/* Enhanced Submit Button */}
            <div className="text-center">
              <button
                type="submit"
                disabled={!isBackendReady && isBackendChecking}
                className={cn(
                  "inline-flex items-center px-10 py-4 text-xl font-bold text-white rounded-2xl transition-all duration-300 transform focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 min-w-[280px]",
                  (!isBackendReady && isBackendChecking)
                    ? "bg-gray-500 cursor-not-allowed opacity-75"
                    : "bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25 focus:ring-cyan-500"
                )}
                aria-describedby="submit-button-description"
              >
                <Zap className="w-6 h-6 mr-3" aria-hidden="true" />
                {(!isBackendReady && isBackendChecking)
                  ? 'Initializing AI Services...'
                  : selectedFiles.length > 0
                    ? `Analyze ${selectedFiles.length} Images with AI`
                    : selectedFile
                      ? `Analyze ${isImageFile(selectedFile) ? 'Image' : 'Document'} with AI`
                      : 'Start AI Analysis'
                }
              </button>
              <p className="text-slate-500 text-sm mt-4">
                Free forever • No signup required • Privacy protected
              </p>
              <p className="sr-only" id="submit-button-description">
                Submit your document for AI-powered legal analysis
              </p>
            </div>
          </form>

          {/* Enhanced Demo Section */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="mt-16"
          >
            <div className="bg-slate-800/20 backdrop-blur-sm border border-slate-700/30 rounded-3xl p-8">
              <div className="text-center mb-8">
                <h3 className="text-3xl font-bold text-white mb-4">
                  Try Our AI Analysis
                </h3>
                <p className="text-slate-400">
                  Experience the power of our AI with real legal document samples
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <button
                  type="button"
                  onClick={() => loadDemoSample('rental')}
                  className="group p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl hover:border-red-500/30 hover:bg-red-500/5 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-red-500 hover:transform hover:scale-105"
                  aria-label="Load rental agreement demo sample"
                >
                  <div className="text-center">
                    <div className="w-14 h-14 bg-gradient-to-r from-red-500 to-red-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                      <FileText className="w-7 h-7 text-white" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">Rental Agreement</h4>
                    <p className="text-red-400 font-medium mb-2">High Risk Document</p>
                    <p className="text-slate-400 text-sm">Unfavorable lease terms</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => loadDemoSample('employment')}
                  className="group p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl hover:border-green-500/30 hover:bg-green-500/5 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-green-500 hover:transform hover:scale-105"
                  aria-label="Load employment contract demo sample"
                >
                  <div className="text-center">
                    <div className="w-14 h-14 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                      <FileText className="w-7 h-7 text-white" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">Employment Contract</h4>
                    <p className="text-green-400 font-medium mb-2">Low Risk Document</p>
                    <p className="text-slate-400 text-sm">Standard employment terms</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => loadDemoSample('nda')}
                  className="group p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl hover:border-yellow-500/30 hover:bg-yellow-500/5 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-yellow-500 hover:transform hover:scale-105"
                  aria-label="Load NDA agreement demo sample"
                >
                  <div className="text-center">
                    <div className="w-14 h-14 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                      <FileText className="w-7 h-7 text-white" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">NDA Agreement</h4>
                    <p className="text-yellow-400 font-medium mb-2">Medium Risk Document</p>
                    <p className="text-slate-400 text-sm">Overly broad terms</p>
                  </div>
                </button>
              </div>
            </div>
          </motion.div>

          {/* AI Process Overview */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            viewport={{ once: true }}
            className="mt-16"
          >
            <div className="bg-slate-800/30 border border-slate-700 rounded-2xl p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2 flex items-center justify-center">
                  <Globe className="w-6 h-6 mr-3" />
                  AI-Powered Analysis Process
                </h3>
                <div className="google-cloud-badge mx-auto">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z" />
                  </svg>
                  <span>Advanced machine learning models for accurate legal document analysis</span>
                </div>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  {
                    step: '1',
                    title: 'Document Processing',
                    desc: 'Upload or paste your legal document text',
                    color: 'from-cyan-500 to-blue-500'
                  },
                  {
                    step: '2',
                    title: 'AI Analysis',
                    desc: 'Advanced NLP models analyze structure and identify key clauses',
                    color: 'from-blue-500 to-purple-500'
                  },
                  {
                    step: '3',
                    title: 'Risk Assessment',
                    desc: 'Color-coded risk levels with confidence indicators',
                    color: 'from-purple-500 to-pink-500'
                  },
                  {
                    step: '4',
                    title: 'Plain Language',
                    desc: 'Complex legal terms translated into clear explanations',
                    color: 'from-pink-500 to-red-500'
                  }
                ].map((item, index) => (
                  <div key={index} className="text-center">
                    <div className={cn(
                      "w-12 h-12 bg-gradient-to-r rounded-xl flex items-center justify-center mx-auto mb-4",
                      item.color
                    )}>
                      <span className="text-white font-bold">{item.step}</span>
                    </div>
                    <h4 className="font-semibold text-white mb-2">{item.title}</h4>
                    <p className="text-sm text-slate-400">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
});