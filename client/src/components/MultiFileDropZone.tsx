import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle,
  Image,
  Camera,
  Eye,
  File,
  Zap,
  Plus,
  Trash2,
  FolderOpen,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { cn, formatFileSize } from '../utils';
import { notificationService } from '../services/notificationService';
import { validationService } from '../services/validationService';
import { processingNotificationService } from '../services/processingNotificationService';

interface FileWithPreview {
  file: File;
  id: string;
  preview?: string;
  processingMethod: {
    name: string;
    icon: React.ReactNode;
    color: string;
  };
}

interface MultiFileDropZoneProps {
  onFilesSelect: (files: File[]) => void;
  selectedFiles: File[];
  onRemoveFile: (fileId: string) => void;
  onClearAll: () => void;
  errors: Record<string, string>;
  className?: string;
  maxFiles?: number;
  allowMixedTypes?: boolean;
}

export const MultiFileDropZone = React.memo(function MultiFileDropZone({
  onFilesSelect,
  selectedFiles,
  onRemoveFile,
  onClearAll,
  errors,
  className,
  maxFiles = 10,
  allowMixedTypes = true
}: MultiFileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  // @ts-ignore - dragCounter is used in drag event handlers
  const [dragCounter, setDragCounter] = useState(0);
  const [filesWithPreview, setFilesWithPreview] = useState<FileWithPreview[]>([]);
  const [showPreview, setShowPreview] = useState<string | null>(null);
  const [currentPreviewIndex, setCurrentPreviewIndex] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper functions (moved up to avoid hoisting issues)
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

  const createFileWithPreview = useCallback(async (file: File): Promise<FileWithPreview> => {
    const fileWithPreview: FileWithPreview = {
      file,
      id: `${file.name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      processingMethod: getProcessingMethod(file)
    };

    // Create preview for images
    if (isImageFile(file)) {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          resolve({
            ...fileWithPreview,
            preview: e.target?.result as string
          });
        };
        reader.readAsDataURL(file);
      });
    }

    return fileWithPreview;
  }, [isImageFile, getProcessingMethod]);

  // Preview navigation functions
  const getImageFiles = useCallback(() => {
    return filesWithPreview.filter(f => f.preview);
  }, [filesWithPreview]);

  const handlePreviewNavigation = useCallback((direction: 'prev' | 'next') => {
    const imageFiles = getImageFiles();
    if (imageFiles.length <= 1) return;

    if (direction === 'next') {
      setCurrentPreviewIndex(prev => (prev + 1) % imageFiles.length);
    } else {
      setCurrentPreviewIndex(prev => (prev - 1 + imageFiles.length) % imageFiles.length);
    }
  }, [getImageFiles]);

  const openPreview = useCallback((fileId: string) => {
    const imageFiles = getImageFiles();
    const index = imageFiles.findIndex(f => f.id === fileId);
    if (index !== -1) {
      setCurrentPreviewIndex(index);
      setShowPreview(fileId);
    }
  }, [getImageFiles]);

  // Sync selectedFiles prop with internal state
  useEffect(() => {
    const syncFiles = async () => {
      if (selectedFiles.length === 0) {
        // Clear internal state when no files are selected
        setFilesWithPreview([]);
        setShowPreview(null);
      } else {
        // Check if we need to recreate internal state from props
        // This happens when parent component updates selectedFiles
        const propFileNames = selectedFiles.map(f => f.name).sort().join(',');
        const currentFileNames = filesWithPreview.map(f => f.file.name).sort().join(',');
        
        if (propFileNames !== currentFileNames) {
          console.log('Syncing MultiFileDropZone internal state with props:', selectedFiles.length, 'files');
          // Recreate internal state from props
          const newFilesWithPreview = await Promise.all(
            selectedFiles.map(file => createFileWithPreview(file))
          );
          setFilesWithPreview(newFilesWithPreview);
        }
      }
    };

    syncFiles();
  }, [selectedFiles]); // Removed createFileWithPreview to avoid dependency issues

  // Keyboard navigation for preview
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!showPreview) return;

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          handlePreviewNavigation('prev');
          break;
        case 'ArrowRight':
          e.preventDefault();
          handlePreviewNavigation('next');
          break;
        case 'Escape':
          e.preventDefault();
          setShowPreview(null);
          break;
      }
    };

    if (showPreview) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
    
    return undefined;
  }, [showPreview, handlePreviewNavigation]);

  const getFileIcon = useCallback((file: File, size: string = "w-8 h-8") => {
    if (isImageFile(file)) {
      return <Image className={`${size} text-green-400`} />;
    } else if (isDocumentFile(file)) {
      return <FileText className={`${size} text-blue-400`} />;
    } else {
      return <File className={`${size} text-gray-400`} />;
    }
  }, [isImageFile, isDocumentFile]);

  const validateFile = useCallback((file: File): string | null => {
    // Validate file size (20MB for images, 10MB for documents)
    const maxSize = isImageFile(file) ? 20 * 1024 * 1024 : 10 * 1024 * 1024;
    const sizeError = validationService.validateFileSize(file, maxSize);
    if (sizeError) return sizeError;

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
    if (typeError) return typeError;

    return null;
  }, [isImageFile]);

  // Event handlers
  const handleFilesSelect = useCallback(async (newFiles: File[]) => {
    try {
      const validFiles: File[] = [];
      const errors: string[] = [];

      // Check max files limit
      if (newFiles.length > maxFiles) {
        notificationService.error(`Maximum ${maxFiles} files allowed. Please select ${maxFiles} or fewer files.`);
        return;
      }

      // Filter files based on allowMixedTypes
      let filesToProcess = newFiles;
      if (!allowMixedTypes) {
        // Only allow image files when allowMixedTypes is false
        filesToProcess = newFiles.filter(file => isImageFile(file));
        const skippedFiles = newFiles.length - filesToProcess.length;
        if (skippedFiles > 0) {
          errors.push(`${skippedFiles} non-image file(s) were skipped (only images allowed)`);
        }
      }

      // Validate each file
      for (const file of filesToProcess) {
        const validationError = validateFile(file);
        if (validationError) {
          errors.push(`"${file.name}": ${validationError}`);
          continue;
        }

        validFiles.push(file);
      }

      if (errors.length > 0) {
        notificationService.error(`Some files were skipped: ${errors.join(', ')}`);
      }

      if (validFiles.length > 0) {
        console.log('Processing valid files:', validFiles.length, validFiles.map(f => f.name));
        
        // Create previews for valid files
        const filesWithPreviews = await Promise.all(
          validFiles.map(file => createFileWithPreview(file))
        );

        // Replace the current selection instead of appending
        setFilesWithPreview(filesWithPreviews);
        onFilesSelect(validFiles);

        // Show dynamic file type notifications
        processingNotificationService.showFileTypeNotifications(validFiles);
        
        // Simple success message
        notificationService.success(
          `${validFiles.length} file${validFiles.length > 1 ? 's' : ''} selected successfully`
        );
      }
    } catch (error) {
      console.error('Error in handleFilesSelect:', error);
      notificationService.error('Failed to process selected files');
    }
  }, [maxFiles, validateFile, createFileWithPreview, onFilesSelect, isImageFile, allowMixedTypes]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setDragCounter(0);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFilesSelect(files);
    } else {
      notificationService.error('No valid files were dropped. Please try again.');
    }
  }, [handleFilesSelect]);

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
      handleFilesSelect(Array.from(files));
    }
  }, [handleFilesSelect]);

  const handleRemoveFile = useCallback((fileId: string) => {
    const fileToRemove = filesWithPreview.find(f => f.id === fileId);
    if (fileToRemove) {
      const updatedFilesWithPreview = filesWithPreview.filter(f => f.id !== fileId);
      setFilesWithPreview(updatedFilesWithPreview);
      
      // Update the selectedFiles array and notify parent
      const updatedSelectedFiles = updatedFilesWithPreview.map(f => f.file);
      onFilesSelect(updatedSelectedFiles);
      
      onRemoveFile(fileId);
      notificationService.success(`"${fileToRemove.file.name}" removed`);
    }
  }, [filesWithPreview, onRemoveFile, onFilesSelect]);

  const handleClearAll = useCallback(() => {
    setFilesWithPreview([]);
    setShowPreview(null);
    
    // Notify parent with empty array
    onFilesSelect([]);
    onClearAll();
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    notificationService.success('All files cleared');
  }, [onClearAll, onFilesSelect]);





  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <label className="block text-lg font-semibold text-white">
          <FolderOpen className="w-5 h-5 inline mr-2" />
          Upload Multiple Documents & Images
        </label>
        {selectedFiles.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-slate-400">
              {selectedFiles.length}/{maxFiles} files
            </span>
            <button
              onClick={handleClearAll}
              className="text-red-400 hover:text-red-300 transition-colors"
              aria-label="Clear all files"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
      
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
        aria-label={`Upload multiple files. ${selectedFiles.length} files selected. Maximum ${maxFiles} files allowed.`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowMixedTypes 
            ? ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.bmp,.gif"
            : ".jpg,.jpeg,.png,.webp,.bmp,.gif"
          }
          onChange={handleFileInputChange}
          className="hidden"
          id="multi-file-upload-input"
          aria-label={allowMixedTypes 
            ? "Upload multiple documents or images for analysis"
            : "Upload multiple images for analysis"
          }
        />
        
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
            {isDragOver ? "Drop Your Files Here" : "Drag & Drop Multiple Files"}
          </h3>
          
          <p className={cn(
            "mb-4 transition-colors duration-300",
            isDragOver ? "text-cyan-300" : "text-slate-400"
          )}>
            {isDragOver 
              ? "Release to upload all files" 
              : allowMixedTypes
                ? `Select up to ${maxFiles} files - PDFs, Word docs, images, or text files`
                : `Select up to ${maxFiles} image files - JPEG, PNG, WEBP, BMP, or GIF`
            }
          </p>
          
          {!isDragOver && (
            <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all">
              <Plus className="w-5 h-5 mr-2" />
              Choose Files
            </div>
          )}
          
          <div className="mt-6 space-y-3">
            <p className="text-sm text-slate-500">
              {allowMixedTypes 
                ? "Documents: PDF, DOC, DOCX, TXT (Max 10MB) • Images: JPEG, PNG, WEBP, BMP, GIF (Max 20MB)"
                : "Images: JPEG, PNG, WEBP, BMP, GIF (Max 20MB)"
              }
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
      </div>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <h4 className="text-lg font-semibold text-white flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
            Selected Files ({selectedFiles.length})
          </h4>
          
          <div className="grid gap-3 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {filesWithPreview.map((fileItem) => (
                <motion.div
                  key={fileItem.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center space-x-4 p-4 bg-slate-800/50 border border-slate-600 rounded-xl hover:bg-slate-800/70 transition-colors"
                >
                  {/* File Icon/Preview */}
                  <div className="flex-shrink-0 relative">
                    {fileItem.preview ? (
                      <div className="relative">
                        <img
                          src={fileItem.preview}
                          alt={fileItem.file.name}
                          className="w-12 h-12 object-cover rounded-lg"
                        />
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-500 rounded-full flex items-center justify-center">
                          <Camera className="w-2 h-2 text-white" />
                        </div>
                      </div>
                    ) : (
                      getFileIcon(fileItem.file, "w-12 h-12")
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <h5 className="font-medium text-white truncate">
                      {fileItem.file.name}
                    </h5>
                    <p className="text-sm text-slate-400">
                      {formatFileSize(fileItem.file.size)}
                    </p>
                    
                    {/* Processing Method Badge */}
                    <div className={cn(
                      "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1 border",
                      fileItem.processingMethod.color
                    )}>
                      {fileItem.processingMethod.icon}
                      {fileItem.processingMethod.name}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    {fileItem.preview && (
                      <button
                        onClick={() => openPreview(fileItem.id)}
                        className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 rounded-lg transition-colors"
                        aria-label={`Preview ${fileItem.file.name}`}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleRemoveFile(fileItem.id)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded-lg transition-colors"
                      aria-label={`Remove ${fileItem.file.name}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
      
      {errors.files && (
        <div className="flex items-center text-red-400 text-sm" role="alert" aria-live="assertive">
          <AlertCircle className="w-4 h-4 mr-2" aria-hidden="true" />
          <span>{errors.files}</span>
        </div>
      )}

      {/* Image Preview Carousel Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="relative w-full h-full flex items-center justify-center p-4"
          >
            {/* Close Button */}
            <button
              onClick={() => setShowPreview(null)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-20 bg-black/50 rounded-full p-2"
              aria-label="Close preview"
            >
              <X className="w-6 h-6" />
            </button>

            {(() => {
              const imageFiles = getImageFiles();
              const currentFile = imageFiles[currentPreviewIndex];
              
              if (!currentFile || !currentFile.preview) return null;

              return (
                <>
                  {/* Navigation Arrows */}
                  {imageFiles.length > 1 && (
                    <>
                      <button
                        onClick={() => handlePreviewNavigation('prev')}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-white hover:text-gray-300 transition-colors z-20 bg-black/50 rounded-full p-3"
                        aria-label="Previous image"
                      >
                        <ChevronLeft className="w-8 h-8" />
                      </button>
                      
                      <button
                        onClick={() => handlePreviewNavigation('next')}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:text-gray-300 transition-colors z-20 bg-black/50 rounded-full p-3"
                        aria-label="Next image"
                      >
                        <ChevronRight className="w-8 h-8" />
                      </button>
                    </>
                  )}

                  {/* Main Image */}
                  <div className="relative max-w-5xl max-h-full flex items-center justify-center">
                    <motion.img
                      key={currentFile.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.3 }}
                      src={currentFile.preview}
                      alt={`Preview of ${currentFile.file.name}`}
                      className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
                    />
                    
                    {/* Image Info Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent text-white p-6 rounded-b-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-lg mb-1">
                            {currentFile.file.name}
                          </p>
                          <p className="text-sm text-gray-300 mb-2">
                            {formatFileSize(currentFile.file.size)} • Ready for Vision API analysis
                          </p>
                          {imageFiles.length > 1 && (
                            <p className="text-xs text-gray-400">
                              Image {currentPreviewIndex + 1} of {imageFiles.length}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center px-3 py-1 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                            <Camera className="w-3 h-3 mr-1" />
                            OCR Ready
                          </div>
                          {imageFiles.length > 1 && (
                            <div className="text-xs text-gray-400">
                              Use ← → keys to navigate
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Thumbnail Strip */}
                  {imageFiles.length > 1 && (
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2 bg-black/50 rounded-lg p-2">
                      {imageFiles.map((file, index) => (
                        <button
                          key={file.id}
                          onClick={() => setCurrentPreviewIndex(index)}
                          className={cn(
                            "w-12 h-12 rounded overflow-hidden border-2 transition-all",
                            index === currentPreviewIndex
                              ? "border-cyan-400 scale-110"
                              : "border-gray-600 hover:border-gray-400"
                          )}
                        >
                          <img
                            src={file.preview}
                            alt={`Thumbnail ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </button>
                      ))}
                    </div>
                  )}
                </>
              );
            })()}
          </motion.div>
        </div>
      )}
    </div>
  );
});

export default MultiFileDropZone;