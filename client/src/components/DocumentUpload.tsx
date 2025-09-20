import { useState, useRef, useCallback } from 'react';
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
  Globe
} from 'lucide-react';
import { cn, formatFileSize } from '../lib/utils';
import { notificationService } from '../services/notificationService';
import { validationService } from '../services/validationService';
import { VoiceInput } from './VoiceInput';

interface DocumentUploadProps {
  onSubmit: (formData: FormData) => void;
}

import React from 'react';

export const DocumentUpload = React.memo(function DocumentUpload({ onSubmit }: DocumentUploadProps) {
  const [documentText, setDocumentText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [expertiseLevel, setExpertiseLevel] = useState('beginner');
  const [userQuestions, setUserQuestions] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  const [charCount, setCharCount] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  const handleFileSelect = useCallback((file: File) => {
    // Validate file size
    const sizeError = validationService.validateFileSize(file, 10 * 1024 * 1024);
    if (sizeError) {
      setErrors({ file: sizeError });
      notificationService.error(sizeError);
      return;
    }

    // Validate file type
    const typeError = validationService.validateFileType(file, ['application/pdf', 'text/plain']);
    if (typeError) {
      setErrors({ file: typeError });
      notificationService.error(typeError);
      return;
    }

    setSelectedFile(file);
    setErrors({ ...errors, file: '' });
    notificationService.success(`File "${file.name}" selected successfully`);
  }, [errors]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

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

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const loadDemoSample = (sampleType: keyof typeof demoSamples) => {
    setDocumentText(demoSamples[sampleType]);
    setCharCount(demoSamples[sampleType].length);
    clearFile();
  };



  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Create form data
    const formData = new FormData();
    
    if (selectedFile) {
      formData.append('document_file', selectedFile);
    }
    
    formData.append('document_text', documentText);
    formData.append('expertise_level', expertiseLevel);
    formData.append('user_questions', userQuestions);

    // Validate form data
    const validation = validationService.validateDocumentUpload(formData);
    
    if (!validation.isValid) {
      setErrors(validation.errors);
      // Show first error as notification
      const firstError = Object.values(validation.errors)[0];
      notificationService.validationError(firstError);
      return;
    }

    // Clear errors and submit
    setErrors({});
    onSubmit(formData);
  };

  return (
    <section id="document-upload" className="py-20 relative">
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
              Universal Legal Document Analysis
            </h2>
            <p className="text-xl text-slate-300">
              Upload or paste your legal document to get AI-powered analysis with risk assessment and plain-language explanations
            </p>
          </div>

          {/* Problem Statement */}
          <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-2xl p-6 mb-8">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2">
                  Bridging the Legal Literacy Gap
                </h3>
                <p className="text-slate-300 mb-2">
                  <strong>The Problem:</strong> 78% of people struggle to understand legal documents, leading to unfavorable agreements and financial losses.
                </p>
                <p className="text-slate-300">
                  <strong>Our Solution:</strong> AI-powered analysis that transforms complex legal language into clear, actionable insights - making legal protection accessible to everyone.
                </p>
              </div>
            </div>
          </div>

          {/* Main Form */}
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* File Upload Area */}
            <div className="space-y-4">
              <label className="block text-lg font-semibold text-white">
                <Upload className="w-5 h-5 inline mr-2" />
                Upload Document (Optional)
              </label>
              
              <div
                className={cn(
                  "relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 cursor-pointer",
                  isDragOver 
                    ? "border-cyan-400 bg-cyan-400/10" 
                    : "border-slate-600 hover:border-slate-500 bg-slate-800/30"
                )}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
                
                {selectedFile ? (
                  <div className="text-center">
                    <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {selectedFile.name}
                    </h3>
                    <p className="text-slate-400 mb-4">
                      {formatFileSize(selectedFile.size)} • Ready for analysis
                    </p>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        clearFile();
                      }}
                      className="inline-flex items-center px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Remove File
                    </button>
                  </div>
                ) : (
                  <div className="text-center">
                    <Upload className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Drag & Drop Your Document Here
                    </h3>
                    <p className="text-slate-400 mb-4">
                      or click to browse files
                    </p>
                    <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all">
                      <FileText className="w-5 h-5 mr-2" />
                      Choose File
                    </div>
                    <p className="text-sm text-slate-500 mt-4">
                      Supported formats: PDF, TXT (Max 10MB)
                    </p>
                  </div>
                )}
              </div>
              
              {errors.file && (
                <div className="flex items-center text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  {errors.file}
                </div>
              )}
            </div>

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
                />
                

              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">
                  Please ensure you provide the complete legal document for accurate analysis.
                </span>
                <span className={cn(
                  "font-mono",
                  charCount > 45000 ? "text-red-400" : "text-slate-400"
                )}>
                  {charCount.toLocaleString()} / 50,000 characters
                </span>
              </div>
              
              {errors.text && (
                <div className="flex items-center text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  {errors.text}
                </div>
              )}
              
              {errors.voice && (
                <div className="flex items-center text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  {errors.voice}
                </div>
              )}
            </div>

            {/* Expertise Level */}
            <div className="space-y-4">
              <label className="text-lg font-semibold text-white">
                Your Experience Level (Optional)
              </label>
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { value: 'beginner', label: 'Beginner', desc: 'New to legal documents' },
                  { value: 'intermediate', label: 'Intermediate', desc: 'Some legal document experience' },
                  { value: 'expert', label: 'Expert', desc: 'Legal/real estate professional' }
                ].map((level) => (
                  <label
                    key={level.value}
                    className={cn(
                      "flex items-start space-x-3 p-4 rounded-xl border cursor-pointer transition-all",
                      expertiseLevel === level.value
                        ? "border-cyan-500 bg-cyan-500/10"
                        : "border-slate-600 bg-slate-800/30 hover:border-slate-500"
                    )}
                  >
                    <input
                      type="radio"
                      name="expertise_level"
                      value={level.value}
                      checked={expertiseLevel === level.value}
                      onChange={(e) => setExpertiseLevel(e.target.value)}
                      className="mt-1 text-cyan-500 focus:ring-cyan-500"
                    />
                    <div>
                      <div className="font-semibold text-white">{level.label}</div>
                      <div className="text-sm text-slate-400">{level.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-sm text-slate-400 flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" />
                This helps us adapt our explanations to your knowledge level
              </p>
            </div>

            {/* User Questions */}
            <div className="space-y-4">
              <label className="text-lg font-semibold text-white">
                Any Specific Questions? (Optional)
              </label>
              <textarea
                value={userQuestions}
                onChange={(e) => setUserQuestions(e.target.value)}
                placeholder="e.g., What does this clause mean? Are these terms fair? What are my rights?"
                className="w-full h-24 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none resize-none transition-all"
              />
              <p className="text-sm text-slate-400">
                Ask any questions about legal terms or specific clauses you're concerned about
              </p>
            </div>

            {/* Submit Button */}
            <div className="text-center">
              <button
                type="submit"
                className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl hover:from-cyan-400 hover:to-blue-400 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/25"
              >
                <Zap className="w-5 h-5 mr-2" />
                Analyze Document
              </button>
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
                <h3 className="text-2xl font-bold text-white mb-2 flex items-center justify-center">
                  <Play className="w-6 h-6 mr-3" />
                  Try Our Demo Mode
                </h3>
                <p className="text-slate-300">
                  Experience our AI analysis with sample documents
                </p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <button
                  type="button"
                  onClick={() => loadDemoSample('rental')}
                  className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl hover:bg-red-500/30 transition-all group"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">Rental Agreement</h4>
                    <p className="text-sm text-red-400">Unfavorable lease terms</p>
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => loadDemoSample('employment')}
                  className="p-4 bg-green-500/20 border border-green-500/50 rounded-xl hover:bg-green-500/30 transition-all group"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">Employment Contract</h4>
                    <p className="text-sm text-green-400">Standard terms</p>
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => loadDemoSample('nda')}
                  className="p-4 bg-yellow-500/20 border border-yellow-500/50 rounded-xl hover:bg-yellow-500/30 transition-all group"
                >
                  <div className="text-center">
                    <div className="w-12 h-12 bg-yellow-500 rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold text-white mb-1">NDA Agreement</h4>
                    <p className="text-sm text-yellow-400">Overly broad terms</p>
                  </div>
                </button>
              </div>
              
              <div className="bg-slate-800/50 rounded-xl p-4">
                <p className="text-sm text-slate-300 text-center">
                  <AlertCircle className="w-4 h-4 inline mr-2" />
                  <strong>Demo Benefits:</strong> See real AI analysis • Understand risk levels • Experience plain-language explanations
                </p>
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
                    <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
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