import React, { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  X, 
  AlertCircle,
  Image,
  Camera,
  Eye,
  File,
  Zap
} from 'lucide-react';
import { cn, formatFileSize } from '../utils';
import { notificationService } from '../services/notificationService';
import { validationService } from '../services/validationService';

interface UniversalDropZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClearFile: () => void;
  errors: Record<string, string>;
  className?: string;
}

export const UniversalDropZone = React.memo(function UniversalDropZone({
  onFileSelect,
  selectedFile,
  onClearFile,
  errors,
  className
}: UniversalDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  // @ts-ignore - dragCounter is used in drag event handlers
  const [dragCounter, setDragCounter] = useState(0);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper functions
  const isImageFile = useCallback((file: File) => {
    return file.type.startsWith('image/');
  }, []);

  const isDocumentFile = useCallback((file: File) => {
    const documentTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    return documentTypes.includes(file.type);
  }, []);

  const getFileIcon = useCallback((file: File) => {
    if (isImageFile(file)) {
      return <Image className="w-16 h-16 text-green-400 mx-auto mb-4" />;
    } else if (isDocumentFile(file)) {
      return <FileText className="w-16 h-16 text-green-400 mx-auto mb-4" />;
    } else {
      return <File className="w-16 h-16 text-green-400 mx-auto mb-4" />;
    }
  }, [isImageFile, isDocumentFile]);

  const getProcessingMethod = useCallback((file: File) => {
    if (isImageFile(file)) {
      return {
        name: 'Vision API (OCR)',
        icon: <Camera className="w-3 h-3 mr-1" />,
        color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
      };
    } else {
      return {
        name: 'Document AI',
        icon: <FileText className="w-3 h-3 mr-1" />,
        color: 'bg-blue-500/20 text-blue-300 border-blue-500/30'
      };
    }
  }, [isImageFile]);

  // Event handlers
  const handleFileSelect = useCallback((file: File) => {
    try {
      console.log('File selected:', { name: file.name, size: file.size, type: file.type });
      
      // Validate file size (20MB for images, 10MB for documents)
      const maxSize = isImageFile(file) ? 20 * 1024 * 1024 : 10 * 1024 * 1024;
      const sizeError = validationService.validateFileSize(file, maxSize);
      if (sizeError) {
        notificationService.error(sizeError);
        return;
      }

      // Validate file type
      const supportedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'image/bmp',
        'image/gif'
      ];
      
      const typeError = validationService.validateFileType(file, supportedTypes);
      if (typeError) {
        notificationService.error(typeError);
        return;
      }

      onFileSelect(file);
      
      // Create image preview if it's an image
      if (isImageFile(file)) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreview(e.target?.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        setImagePreview(null);
      }
      
      const processingType = isImageFile(file) ? 'Vision API (OCR)' : 'Document AI';
      notificationService.success(`File "${file.name}" selected. Will use ${processingType} for analysis.`);
      
    } catch (error) {
      console.error('Error in handleFileSelect:', error);
      notificationService.error('Failed to process selected file');
    }
  }, [onFileSelect, isImageFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setDragCounter(0);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    } else {
      notificationService.error('No valid files were dropped. Please try again.');
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    if (!isDragOver) {
      setIsDragOver(true);
    }
  }, [isDragOver]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => prev + 1);
    if (!isDragOver) {
      setIsDragOver(true);
    }
  }, [isDragOver]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => {
      const newCount = prev - 1;
      if (newCount <= 0) {
        setIsDragOver(false);
        return 0;
      }
      return newCount;
    });
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleClearFile = useCallback(() => {
    onClearFile();
    setImagePreview(null);
    setShowPreview(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onClearFile]);

  return (
    <div className={cn("space-y-4", className)}>
      <label className="block text-lg font-semibold text-white">
        <Upload className="w-5 h-5 inline mr-2" />
        Upload Document or Image
      </label>
      
      <div
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500",
          isDragOver 
            ? "border-cyan-400 bg-cyan-400/20 scale-105 shadow-lg shadow-cyan-500/25" 
            : "border-slate-600 hover:border-slate-500 bg-slate-800/30 hover:bg-slate-800/40"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label={selectedFile ? `File selected: ${selectedFile.name}. Click to select a different file.` : "Click to upload document or image, or drag and drop files here. Supports documents (PDF, DOC, DOCX, TXT) and images (JPEG, PNG, WEBP, BMP, GIF)."}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.bmp,.gif"
          onChange={handleFileInputChange}
          className="hidden"
          id="universal-upload-input"
          aria-label="Upload document or image for analysis"
        />
        
        {selectedFile ? (
          <div className="text-center">
            <div className="relative inline-block">
              {getFileIcon(selectedFile)}
              {isImageFile(selectedFile) && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-cyan-500 rounded-full flex items-center justify-center">
                  <Camera className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
            
            <h3 className="text-xl font-semibold text-white mb-2">
              {selectedFile.name}
            </h3>
            
            <p className="text-slate-400 mb-4">
              {formatFileSize(selectedFile.size)} • Ready for analysis
            </p>
            
            {/* Processing method indicator */}
            <div className={cn(
              "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mb-4 border",
              getProcessingMethod(selectedFile).color
            )}>
              {getProcessingMethod(selectedFile).icon}
              {getProcessingMethod(selectedFile).name}
            </div>

            <div className="flex justify-center space-x-3">
              {imagePreview && isImageFile(selectedFile) && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowPreview(true);
                  }}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Preview selected image"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </button>
              )}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearFile();
                }}
                className="inline-flex items-center px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
                aria-label={`Remove selected file: ${selectedFile.name}`}
              >
                <X className="w-4 h-4 mr-2" />
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="relative">
              <Upload className={cn(
                "w-16 h-16 mx-auto mb-4 transition-all duration-300",
                isDragOver ? "text-cyan-400 scale-110" : "text-slate-400"
              )} />
              {isDragOver && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <Zap className="w-8 h-8 text-cyan-400" />
                </motion.div>
              )}
            </div>
            
            <h3 className={cn(
              "text-xl font-semibold mb-2 transition-colors duration-300",
              isDragOver ? "text-cyan-300" : "text-white"
            )}>
              {isDragOver ? "Drop Your File Here" : "Drag & Drop Your Document or Image"}
            </h3>
            
            <p className={cn(
              "mb-4 transition-colors duration-300",
              isDragOver ? "text-cyan-300" : "text-slate-400"
            )}>
              {isDragOver ? "Release to upload" : "PDFs, Word docs, images, or text files"}
            </p>
            
            {!isDragOver && (
              <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all">
                <Upload className="w-5 h-5 mr-2" />
                Choose File
              </div>
            )}
            
            <div className="mt-6 space-y-3">
              <p className="text-sm text-slate-500">
                Documents: PDF, DOC, DOCX, TXT (Max 10MB) • Images: JPEG, PNG, WEBP, BMP, GIF (Max 20MB)
              </p>
              
              <div className="flex items-center justify-center space-x-6 text-xs text-slate-400">
                <div className="flex items-center">
                  <FileText className="w-3 h-3 mr-1" />
                  Documents → Document AI
                </div>
                <div className="flex items-center">
                  <Camera className="w-3 h-3 mr-1" />
                  Images → Vision API (OCR)
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {errors.file && (
        <div className="flex items-center text-red-400 text-sm" role="alert" aria-live="assertive">
          <AlertCircle className="w-4 h-4 mr-2" aria-hidden="true" />
          <span>{errors.file}</span>
        </div>
      )}

      {/* Image Preview Modal */}
      {showPreview && imagePreview && selectedFile && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="relative max-w-4xl max-h-full"
          >
            <button
              onClick={() => setShowPreview(false)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition-colors z-10"
              aria-label="Close preview"
            >
              <X className="w-8 h-8" />
            </button>
            <img
              src={imagePreview}
              alt="Document preview"
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent text-white p-6 rounded-b-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-300">
                    {formatFileSize(selectedFile.size)} • Ready for Vision API analysis
                  </p>
                </div>
                <div className="flex items-center px-3 py-1 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  <Camera className="w-3 h-3 mr-1" />
                  OCR Ready
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
});

export default UniversalDropZone;