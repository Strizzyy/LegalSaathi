import React, { useState, useRef, useCallback } from 'react';
import { 
  X, 
  AlertCircle,
  Image,
  Camera,
  Eye,
  FileText
} from 'lucide-react';
import { cn, formatFileSize } from '../utils';
import { notificationService } from '../services/notificationService';
import { validationService } from '../services/validationService';

interface ImageDropZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClearFile: () => void;
  isDragOver: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragEnter: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  errors: Record<string, string>;
}

export const ImageDropZone = React.memo(function ImageDropZone({
  onFileSelect,
  selectedFile,
  onClearFile,
  isDragOver,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop,
  errors
}: ImageDropZoneProps) {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      
      // Validate file type (images only)
      const typeError = validationService.validateFileType(file, [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'image/bmp',
        'image/gif'
      ]);
      
      if (typeError) {
        notificationService.error(typeError);
        return;
      }

      // Validate file size (20MB for images)
      const sizeError = validationService.validateFileSize(file, 20 * 1024 * 1024);
      if (sizeError) {
        notificationService.error(sizeError);
        return;
      }

      onFileSelect(file);
      
      // Create image preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, [onFileSelect]);

  const handleClearFile = useCallback(() => {
    onClearFile();
    setImagePreview(null);
    setShowPreview(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onClearFile]);

  const isImageFile = selectedFile?.type.startsWith('image/');

  return (
    <div className="space-y-4">
      <label className="block text-lg font-semibold text-white">
        <Camera className="w-5 h-5 inline mr-2" />
        Upload Image Document
      </label>
      
      <div
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500",
          isDragOver 
            ? "border-cyan-400 bg-cyan-400/20 scale-105 shadow-lg shadow-cyan-500/25" 
            : "border-slate-600 hover:border-slate-500 bg-slate-800/30 hover:bg-slate-800/40"
        )}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label={selectedFile ? `Image selected: ${selectedFile.name}. Click to select a different image.` : "Click to upload image or drag and drop image files here. Supported formats: JPEG, PNG, WEBP, BMP, GIF. Maximum size: 20MB."}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.bmp,.gif"
          onChange={handleFileInputChange}
          className="hidden"
          id="image-upload-input"
          aria-label="Upload image document for OCR analysis"
        />
        
        {selectedFile && isImageFile ? (
          <div className="text-center">
            <div className="relative">
              <Image className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-cyan-500 rounded-full flex items-center justify-center">
                <Camera className="w-3 h-3 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {selectedFile.name}
            </h3>
            <p className="text-slate-400 mb-4">
              {formatFileSize(selectedFile.size)} • Ready for OCR analysis
            </p>
            
            {/* Processing method indicator */}
            <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mb-4 bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              <Camera className="w-3 h-3 mr-1" />
              Vision API (OCR)
            </div>

            <div className="flex justify-center space-x-3">
              {imagePreview && (
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
                aria-label={`Remove selected image: ${selectedFile.name}`}
              >
                <X className="w-4 h-4 mr-2" />
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <Camera className={cn(
              "w-16 h-16 mx-auto mb-4 transition-all duration-300",
              isDragOver ? "text-cyan-400 scale-110" : "text-slate-400"
            )} />
            <h3 className={cn(
              "text-xl font-semibold mb-2 transition-colors duration-300",
              isDragOver ? "text-cyan-300" : "text-white"
            )}>
              {isDragOver ? "Drop Your Image Here" : "Drag & Drop Image Document"}
            </h3>
            <p className={cn(
              "mb-4 transition-colors duration-300",
              isDragOver ? "text-cyan-300" : "text-slate-400"
            )}>
              {isDragOver ? "Release to upload" : "Screenshots, photos of contracts, or scanned documents"}
            </p>
            {!isDragOver && (
              <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all">
                <Image className="w-5 h-5 mr-2" />
                Choose Image
              </div>
            )}
            <div className="mt-4 space-y-2">
              <p className="text-sm text-slate-500">
                Supported: JPEG, PNG, WEBP, BMP, GIF (Max 20MB)
              </p>
              <div className="flex items-center justify-center text-xs text-slate-400">
                <div className="flex items-center">
                  <Camera className="w-3 h-3 mr-1" />
                  Uses Google Vision API for text extraction
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
      {showPreview && imagePreview && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setShowPreview(false)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition-colors"
              aria-label="Close preview"
            >
              <X className="w-8 h-8" />
            </button>
            <img
              src={imagePreview}
              alt="Document preview"
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white p-4 rounded-b-lg">
              <p className="text-sm">
                <FileText className="w-4 h-4 inline mr-2" />
                {selectedFile?.name} • {selectedFile && formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default ImageDropZone;