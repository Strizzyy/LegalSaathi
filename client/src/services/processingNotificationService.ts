import { notificationService } from './notificationService';

interface ProcessingResult {
  success: boolean;
  confidence_scores?: {
    average_confidence?: number;
    high_confidence_ratio?: number;
    min_confidence_threshold?: number;
    total_text_blocks?: number;
    high_confidence_blocks?: number;
  };
  text_extraction?: {
    confidence_scores?: any;
  };
  warnings?: string[];
  processing_metadata?: {
    api_used?: string;
    fallback_used?: boolean;
  };
  fallback_used?: boolean;
  method_used?: string;
}

interface BatchResult {
  results: Array<{
    file: File;
    result: ProcessingResult;
    error?: string;
    processingTime: number;
  }>;
  totalTime: number;
}

class ProcessingNotificationService {
  
  /**
   * Show dynamic notifications based on single file processing results
   */
  showProcessingNotifications(result: ProcessingResult, fileName?: string) {
    const filePrefix = fileName ? `"${fileName}": ` : '';
    
    // Check for fallback usage
    if (result.fallback_used || result.processing_metadata?.fallback_used) {
      notificationService.warning(
        `${filePrefix}Using fallback processing - some features may be limited`,
        { duration: 5000 }
      );
    }

    // Check Vision API confidence scores
    if (result.confidence_scores || result.text_extraction?.confidence_scores) {
      const confidence = result.confidence_scores || result.text_extraction?.confidence_scores;
      this.showConfidenceNotifications(confidence, filePrefix);
    }

    // Show API-specific notifications
    if (result.processing_metadata?.api_used) {
      this.showAPINotifications(result.processing_metadata.api_used, filePrefix);
    }

    // Show any warnings from the processing
    if (result.warnings && result.warnings.length > 0) {
      result.warnings.forEach(warning => {
        notificationService.warning(`${filePrefix}${warning}`, { duration: 4000 });
      });
    }

    // Success notification with processing method
    if (result.success) {
      const method = this.getProcessingMethod(result);
      notificationService.success(
        `${filePrefix}Successfully processed using ${method}`,
        { duration: 3000 }
      );
    }
  }

  /**
   * Show notifications for batch processing results
   */
  showBatchNotifications(batchResult: BatchResult) {
    const { results, totalTime } = batchResult;
    const successful = results.filter(r => r.result?.success && !r.error).length;
    const failed = results.filter(r => r.error || !r.result?.success).length;
    const total = results.length;

    // Overall batch result
    if (successful === total) {
      notificationService.success(
        `All ${total} files processed successfully in ${Math.round(totalTime / 1000)}s`,
        { duration: 4000 }
      );
    } else if (successful > 0) {
      notificationService.warning(
        `${successful}/${total} files processed successfully. ${failed} failed.`,
        { duration: 5000 }
      );
    } else {
      notificationService.error(
        `All ${total} files failed to process. Please check file formats and try again.`,
        { duration: 6000 }
      );
    }

    // Analyze confidence across all successful results
    this.showBatchConfidenceNotifications(results);

    // Show API usage summary
    this.showBatchAPIUsage(results);
  }

  /**
   * Show confidence-based notifications
   */
  private showConfidenceNotifications(confidence: any, filePrefix: string = '') {
    if (!confidence) return;

    const avgConfidence = confidence.average_confidence || 0;
    const highConfidenceRatio = confidence.high_confidence_ratio || 0;

    // Very low confidence
    if (avgConfidence < 0.3) {
      notificationService.error(
        `${filePrefix}Very low OCR confidence (${Math.round(avgConfidence * 100)}%). Text extraction may be highly inaccurate.`,
        { 
          duration: 8000,
          action: {
            label: 'Tips',
            handler: () => this.showImageQualityTips()
          }
        }
      );
    }
    // Low confidence
    else if (avgConfidence < 0.6) {
      notificationService.warning(
        `${filePrefix}Low OCR confidence (${Math.round(avgConfidence * 100)}%). Consider using a clearer image.`,
        { duration: 6000 }
      );
    }
    // Medium confidence with low high-confidence ratio
    else if (avgConfidence < 0.8 && highConfidenceRatio < 0.5) {
      notificationService.warning(
        `${filePrefix}Mixed OCR quality detected. ${Math.round(highConfidenceRatio * 100)}% of text has high confidence.`,
        { duration: 5000 }
      );
    }
    // Good confidence
    else if (avgConfidence >= 0.8) {
      notificationService.info(
        `${filePrefix}Good OCR quality (${Math.round(avgConfidence * 100)}% confidence)`,
        { duration: 3000 }
      );
    }

    // High confidence blocks notification
    if (confidence.total_text_blocks && confidence.high_confidence_blocks) {
      const ratio = confidence.high_confidence_blocks / confidence.total_text_blocks;
      if (ratio < 0.3) {
        notificationService.warning(
          `${filePrefix}Only ${Math.round(ratio * 100)}% of text blocks have high confidence. Legal analysis may be affected.`,
          { duration: 5000 }
        );
      }
    }
  }

  /**
   * Show API-specific notifications
   */
  private showAPINotifications(apiUsed: string, filePrefix: string = '') {
    if (apiUsed.includes('Vision API')) {
      notificationService.info(
        `${filePrefix}Processed with Google Vision API (OCR)`,
        { duration: 2000 }
      );
    } else if (apiUsed.includes('Document AI')) {
      notificationService.info(
        `${filePrefix}Processed with Google Document AI`,
        { duration: 2000 }
      );
    } else if (apiUsed.includes('Fallback')) {
      notificationService.warning(
        `${filePrefix}Using basic text extraction - advanced features unavailable`,
        { duration: 4000 }
      );
    }
  }

  /**
   * Show batch confidence analysis
   */
  private showBatchConfidenceNotifications(results: Array<any>) {
    const imageResults = results.filter(r => 
      r.file.type.startsWith('image/') && 
      r.result?.success && 
      r.result?.confidence_scores
    );

    if (imageResults.length === 0) return;

    const confidences = imageResults.map(r => r.result.confidence_scores.average_confidence || 0);
    const avgBatchConfidence = confidences.reduce((sum, c) => sum + c, 0) / confidences.length;
    const lowConfidenceCount = confidences.filter(c => c < 0.6).length;

    if (lowConfidenceCount > 0) {
      notificationService.warning(
        `${lowConfidenceCount}/${imageResults.length} images have low OCR confidence. Consider using clearer images for better results.`,
        { 
          duration: 6000,
          action: {
            label: 'Tips',
            handler: () => this.showImageQualityTips()
          }
        }
      );
    } else if (avgBatchConfidence >= 0.8) {
      notificationService.success(
        `Excellent OCR quality across all ${imageResults.length} images (${Math.round(avgBatchConfidence * 100)}% avg confidence)`,
        { duration: 4000 }
      );
    }
  }

  /**
   * Show API usage summary for batch
   */
  private showBatchAPIUsage(results: Array<any>) {
    const visionCount = results.filter(r => 
      r.file.type.startsWith('image/') && r.result?.success
    ).length;
    
    const documentCount = results.filter(r => 
      !r.file.type.startsWith('image/') && r.result?.success
    ).length;

    if (visionCount > 0 && documentCount > 0) {
      notificationService.info(
        `Processed ${documentCount} documents (Document AI) and ${visionCount} images (Vision API)`,
        { duration: 4000 }
      );
    }
  }

  /**
   * Get processing method from result
   */
  private getProcessingMethod(result: ProcessingResult): string {
    if (result.processing_metadata?.api_used) {
      return result.processing_metadata.api_used;
    }
    if (result.method_used) {
      return result.method_used;
    }
    if (result.fallback_used) {
      return 'Fallback Processing';
    }
    return 'AI Processing';
  }

  /**
   * Show image quality improvement tips
   */
  private showImageQualityTips() {
    const tips = [
      "📸 Use good lighting when taking photos",
      "🔍 Ensure text is clearly visible and in focus", 
      "📐 Keep the document flat and avoid shadows",
      "📱 Use higher resolution images when possible",
      "🖼️ Crop to show only the document content"
    ];

    const randomTip = tips[Math.floor(Math.random() * tips.length)];
    notificationService.info(
      `Tip: ${randomTip}`,
      { duration: 5000 }
    );
  }

  /**
   * Show processing time notifications for performance feedback
   */
  showPerformanceNotifications(processingTime: number, fileCount: number = 1) {
    const avgTime = processingTime / fileCount;
    
    if (avgTime > 10000) { // > 10 seconds per file
      notificationService.info(
        `Processing took ${Math.round(avgTime / 1000)}s per file. Large or complex documents may take longer.`,
        { duration: 4000 }
      );
    } else if (avgTime < 2000 && fileCount > 1) { // < 2 seconds per file in batch
      notificationService.success(
        `Fast batch processing: ${Math.round(avgTime / 1000)}s average per file`,
        { duration: 3000 }
      );
    }
  }

  /**
   * Show file type specific notifications
   */
  showFileTypeNotifications(files: File[]) {
    const imageCount = files.filter(f => f.type.startsWith('image/')).length;
    const docCount = files.length - imageCount;

    if (imageCount > 0 && docCount > 0) {
      notificationService.info(
        `Processing ${docCount} documents and ${imageCount} images with optimal APIs`,
        { duration: 3000 }
      );
    } else if (imageCount > 1) {
      notificationService.info(
        `Processing ${imageCount} images with Vision API (OCR)`,
        { duration: 3000 }
      );
    } else if (docCount > 1) {
      notificationService.info(
        `Processing ${docCount} documents with Document AI`,
        { duration: 3000 }
      );
    }
  }

  /**
   * Show rate limiting notifications
   */
  showRateLimitNotifications(error: string) {
    if (error.toLowerCase().includes('rate limit')) {
      notificationService.warning(
        'Processing rate limit reached. Please wait a moment before uploading more files.',
        { 
          duration: 6000,
          action: {
            label: 'Learn More',
            handler: () => {
              notificationService.info(
                'Rate limits help ensure fair usage. Try processing fewer files at once.',
                { duration: 5000 }
              );
            }
          }
        }
      );
    }
  }
}

export const processingNotificationService = new ProcessingNotificationService();
export default processingNotificationService;