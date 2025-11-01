import { apiService } from './apiService';
import type { AnalysisResult, FileInfo, Classification } from '../App';

export interface ExportOptions {
  format: 'pdf' | 'docx';
  includeTranslations?: boolean;
  includeSummary?: boolean;
  includeChatHistory?: boolean;
}

export interface ExportData {
  analysis: AnalysisResult;
  file_info?: FileInfo;
  classification?: Classification;
  translations?: Record<string, string>;
  summary?: string;
  chatHistory?: any[];
}

class ExportService {
  private downloadFile(blob: Blob, filename: string): void {
    try {
      // Validate blob
      if (!blob || blob.size === 0) {
        throw new Error('Invalid or empty file content');
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      
      // Clean up with a small delay to ensure download starts
      setTimeout(() => {
        try {
          window.URL.revokeObjectURL(url);
          if (document.body.contains(a)) {
            document.body.removeChild(a);
          }
        } catch (cleanupError) {
          console.warn('Cleanup error:', cleanupError);
        }
      }, 100);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  }

  private generateFilename(format: 'pdf' | 'docx', fileInfo?: FileInfo): string {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const baseName = fileInfo?.filename 
      ? fileInfo.filename.replace(/\.[^/.]+$/, '') 
      : 'legal-analysis-report';
    
    return `${baseName}-analysis-${timestamp}.${format === 'pdf' ? 'pdf' : 'docx'}`;
  }

  async exportToPDF(data: ExportData): Promise<{ success: boolean; error?: string }> {
    try {
      const apiData: any = { analysis: data.analysis };
      if (data.file_info) apiData.file_info = data.file_info;
      if (data.classification) apiData.classification = data.classification;
      
      const blob = await apiService.exportToPDF(apiData);

      // First, let's test if we're actually authenticated
      try {
        const authTestResponse = await fetch('/api/auth/current-user');
        console.log('Auth Test Response:', {
          status: authTestResponse.status,
          statusText: authTestResponse.statusText
        });
        if (authTestResponse.ok) {
          const authData = await authTestResponse.json();
          console.log('Current user data:', authData);
        } else {
          console.warn('Auth test failed:', await authTestResponse.text());
        }
      } catch (authError) {
        console.error('Auth test error:', authError);
      }

      console.log('PDF Export Debug:', {
        blobExists: !!blob,
        blobSize: blob?.size,
        blobType: blob?.type,
        blobConstructor: blob?.constructor.name
      });

      if (!blob || blob.size === 0) {
        console.error('PDF export service returned empty content');
        return { 
          success: false, 
          error: 'PDF generation failed on server. Please try again or contact support.' 
        };
      }

      // Try to download regardless of MIME type - let the user see what we got
      const filename = this.generateFilename('pdf', data.file_info);
      
      // If it looks like text content, let's see what it actually contains
      if (blob.type && blob.type.includes('text/')) {
        console.warn(`Received text content (${blob.type}), but attempting download anyway`);
        // Read the content to see what we got
        const text = await blob.text();
        console.log('Text content received:', text.substring(0, 500));
      }
      
      this.downloadFile(blob, filename);
      
      return { success: true };
    } catch (error: any) {
      console.error('PDF export error:', error);
      
      // Check if it's an authentication error
      if (error.message && error.message.includes('401')) {
        return { 
          success: false, 
          error: 'Please sign in to export PDF documents. Click the "Sign In" button in the top navigation.' 
        };
      }
      
      // Fallback to text export on other errors
      console.warn('PDF export failed, falling back to text export');
      return this.exportAsText(data);
    }
  }

  async exportToWord(data: ExportData): Promise<{ success: boolean; error?: string }> {
    try {
      const apiData: any = { analysis: data.analysis };
      if (data.file_info) apiData.file_info = data.file_info;
      if (data.classification) apiData.classification = data.classification;
      
      const blob = await apiService.exportToWord(apiData);

      if (!blob) {
        // Fallback to text export if Word service is unavailable
        console.warn('Word export service unavailable, falling back to text export');
        return this.exportAsText(data);
      }

      const filename = this.generateFilename('docx', data.file_info);
      this.downloadFile(blob, filename);
      
      return { success: true };
    } catch (error) {
      console.error('Word export error:', error);
      // Fallback to text export on error
      console.warn('Word export failed, falling back to text export');
      return this.exportAsText(data);
    }
  }

  // Fallback export using browser's built-in functionality
  exportAsText(data: ExportData): { success: boolean; error?: string } {
    try {
      const content = this.generateTextReport(data);
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const filename = this.generateFilename('pdf', data.file_info).replace('.pdf', '.txt');
      
      this.downloadFile(blob, filename);
      return { success: true };
    } catch (error) {
      console.error('Text export error:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Text export failed' 
      };
    }
  }

  private generateTextReport(data: ExportData): string {
    const { analysis, file_info, classification } = data;
    
    let report = 'LEGAL DOCUMENT ANALYSIS REPORT\n';
    report += '=====================================\n\n';
    
    if (file_info) {
      report += `Document: ${file_info.filename}\n`;
      report += `Size: ${this.formatFileSize(file_info.size)}\n`;
    }
    
    if (classification) {
      report += `Type: ${classification.document_type.value.replace('_', ' ').toUpperCase()}\n`;
      report += `Classification Confidence: ${Math.round(classification.confidence * 100)}%\n`;
    }
    
    report += `Analysis Date: ${new Date().toLocaleString()}\n\n`;
    
    report += 'OVERALL RISK ASSESSMENT\n';
    report += '=======================\n';
    report += `Risk Level: ${analysis.overall_risk.level}\n`;
    report += `Risk Score: ${Math.round(analysis.overall_risk.score * 100)}%\n`;
    report += `Confidence: ${analysis.overall_risk.confidence_percentage}%\n\n`;
    
    report += 'SUMMARY\n';
    report += '=======\n';
    report += `${analysis.summary}\n\n`;
    
    if (analysis.severity_indicators && analysis.severity_indicators.length > 0) {
      report += 'CRITICAL ISSUES\n';
      report += '===============\n';
      analysis.severity_indicators.forEach((indicator, index) => {
        report += `${index + 1}. ${indicator}\n`;
      });
      report += '\n';
    }
    
    report += 'DETAILED CLAUSE ANALYSIS\n';
    report += '========================\n';
    
    analysis.analysis_results.forEach((result, index) => {
      report += `\nClause #${index + 1} (${result.clause_id})\n`;
      report += `Risk Level: ${result.risk_level.level}\n`;
      report += `Risk Score: ${Math.round(result.risk_level.score * 100)}%\n`;
      report += `Confidence: ${result.risk_level.confidence_percentage}%\n`;
      report += `Severity: ${result.risk_level.severity}\n\n`;
      
      report += `Explanation: ${result.plain_explanation}\n\n`;
      
      if (result.legal_implications.length > 0) {
        report += 'Legal Implications:\n';
        result.legal_implications.forEach((implication, i) => {
          report += `  ${i + 1}. ${implication}\n`;
        });
        report += '\n';
      }
      
      if (result.recommendations.length > 0) {
        report += 'Recommendations:\n';
        result.recommendations.forEach((recommendation, i) => {
          report += `  ${i + 1}. ${recommendation}\n`;
        });
        report += '\n';
      }
      
      report += '---\n';
    });
    
    report += '\nGenerated by LegalSaathi AI Analysis System\n';
    report += 'This report is for informational purposes only and does not constitute legal advice.\n';
    
    return report;
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

export const exportService = new ExportService();
export default exportService;