/**
 * Document comparison service for API communication
 */

import { apiService } from './apiService';

export interface DocumentComparisonRequest {
  document1_text: string;
  document2_text: string;
  document1_type: string;
  document2_type: string;
  comparison_focus?: string;
}

// Valid document types that match backend enum
const VALID_DOCUMENT_TYPES = [
  'rental_agreement',
  'employment_contract', 
  'nda',
  'loan_agreement',
  'partnership_agreement',
  'general_contract'
] as const;

export interface DocumentDifference {
  type: string;
  description: string;
  document1_value?: string;
  document2_value?: string;
  severity: string;
  impact: string;
  recommendation: string;
}

export interface ClauseComparison {
  clause_type: string;
  document1_clause?: any;
  document2_clause?: any;
  risk_difference: number;
  comparison_notes: string;
  recommendation: string;
}

export interface DocumentComparisonResponse {
  comparison_id: string;
  document1_summary: {
    type: string;
    overall_risk: any;
    clause_count: number;
    processing_time: number;
  };
  document2_summary: {
    type: string;
    overall_risk: any;
    clause_count: number;
    processing_time: number;
  };
  overall_risk_comparison: {
    document1_risk: any;
    document2_risk: any;
    risk_score_difference: number;
    verdict: string;
    category_differences: Record<string, number>;
  };
  key_differences: DocumentDifference[];
  clause_comparisons: ClauseComparison[];
  recommendation_summary: string;
  safer_document?: string;
  processing_time: number;
  timestamp: string;
}

class ComparisonService {
  // Helper method to normalize document type to backend enum format
  private normalizeDocumentType(type: string): string {
    const normalized = type.toLowerCase().replace(/\s+/g, '_');
    
    // Map common variations to valid enum values
    const typeMapping: Record<string, string> = {
      'rental': 'rental_agreement',
      'lease': 'rental_agreement',
      'employment': 'employment_contract',
      'job': 'employment_contract',
      'work': 'employment_contract',
      'nda': 'nda',
      'non_disclosure': 'nda',
      'confidentiality': 'nda',
      'loan': 'loan_agreement',
      'credit': 'loan_agreement',
      'partnership': 'partnership_agreement',
      'partner': 'partnership_agreement',
      'contract': 'general_contract',
      'agreement': 'general_contract'
    };

    // Check direct match first
    if (VALID_DOCUMENT_TYPES.includes(normalized as any)) {
      return normalized;
    }

    // Check mapping
    for (const [key, value] of Object.entries(typeMapping)) {
      if (normalized.includes(key)) {
        return value;
      }
    }

    // Default to general_contract
    return 'general_contract';
  }

  async compareDocuments(request: DocumentComparisonRequest): Promise<DocumentComparisonResponse> {
    try {
      // Normalize document types to match backend enum
      const normalizedRequest = {
        ...request,
        document1_type: this.normalizeDocumentType(request.document1_type),
        document2_type: this.normalizeDocumentType(request.document2_type),
        comparison_focus: request.comparison_focus || 'overall'
      };

      console.log('Sending comparison request:', normalizedRequest);
      
      const response = await apiService.post('/api/compare', normalizedRequest);
      return response.data;
    } catch (error: any) {
      console.error('Document comparison failed:', error);
      
      // Provide more specific error messages
      if (error.status === 422) {
        const errorDetail = error.message || 'Invalid request format';
        throw new Error(`Validation error: ${errorDetail}. Please check that both documents have sufficient content (minimum 100 characters).`);
      }
      
      throw new Error(error.response?.data?.message || error.message || 'Failed to compare documents');
    }
  }

  async getComparisonSummary(comparisonId: string): Promise<any> {
    try {
      const response = await apiService.get(`/api/compare/${comparisonId}/summary`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get comparison summary:', error);
      throw new Error(error.response?.data?.message || 'Failed to get comparison summary');
    }
  }

  // Helper method to format risk level for display
  formatRiskLevel(level: string): { text: string; color: string; icon: string } {
    switch (level.toUpperCase()) {
      case 'RED':
        return { text: 'High Risk', color: 'text-red-400', icon: '🚨' };
      case 'YELLOW':
        return { text: 'Medium Risk', color: 'text-yellow-400', icon: '⚠️' };
      case 'GREEN':
        return { text: 'Low Risk', color: 'text-green-400', icon: '✅' };
      default:
        return { text: 'Unknown', color: 'text-gray-400', icon: '❓' };
    }
  }

  // Helper method to format risk score difference
  formatRiskDifference(difference: number): { text: string; color: string } {
    const absDiff = Math.abs(difference);
    
    if (absDiff < 0.1) {
      return { text: 'Similar risk levels', color: 'text-gray-400' };
    } else if (difference > 0.3) {
      return { text: 'Document 1 much riskier', color: 'text-red-400' };
    } else if (difference > 0.1) {
      return { text: 'Document 1 riskier', color: 'text-orange-400' };
    } else if (difference < -0.3) {
      return { text: 'Document 2 much riskier', color: 'text-red-400' };
    } else if (difference < -0.1) {
      return { text: 'Document 2 riskier', color: 'text-orange-400' };
    } else {
      return { text: 'Slight difference', color: 'text-yellow-400' };
    }
  }

  // Helper method to get severity color
  getSeverityColor(severity: string): string {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'text-red-400 bg-red-500/20 border-red-500/50';
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'low':
        return 'text-green-400 bg-green-500/20 border-green-500/50';
      default:
        return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
    }
  }
}

export const comparisonService = new ComparisonService();