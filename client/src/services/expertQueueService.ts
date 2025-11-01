/**
 * Expert Queue Service - Human-in-the-Loop Management
 * Manages expert review queue for low confidence documents
 */

import { auth } from '../firebaseConfig';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ExpertReviewRequest {
  id: string;
  document_id: string;
  user_email: string;
  document_type: string;
  confidence_score: number;
  confidence_breakdown: {
    overall_confidence: number;
    clause_confidences: Record<string, number>;
    section_confidences: Record<string, number>;
    factors_affecting_confidence: string[];
    improvement_suggestions: string[];
  };
  document_text: string;
  ai_analysis: any;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_expert?: string;
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
  expert_notes?: string;
}

export interface ExpertReviewResponse {
  request_id: string;
  expert_analysis: string;
  confidence_score: number;
  recommendations: string[];
  risk_assessment: any;
  expert_notes: string;
  completed_at: string;
  expert_id: string;
}

export interface ExpertQueueStats {
  total_requests: number;
  pending_requests: number;
  in_progress_requests: number;
  completed_requests: number;
  average_completion_time: number;
  expert_workload: Record<string, number>;
}

class ExpertQueueService {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }

    const token = await user.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  private async makeAuthenticatedRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        if (response.status === 403) {
          throw new Error('Admin access required');
        }
        throw new Error(`Request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Expert Queue API request failed:', error);
      throw error;
    }
  }

  /**
   * Submit document for expert review
   */
  async submitForExpertReview(data: {
    document_id: string;
    user_email: string;
    document_type: string;
    confidence_score: number;
    confidence_breakdown: any;
    document_text: string;
    ai_analysis: any;
  }): Promise<{ success: boolean; request_id: string; estimated_completion: string }> {
    return this.makeAuthenticatedRequest('/api/expert-queue/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Get all expert review requests (admin only)
   */
  async getExpertRequests(
    status?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{
    requests: ExpertReviewRequest[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }

    return this.makeAuthenticatedRequest(`/api/admin/expert-queue/requests?${params}`);
  }

  /**
   * Get expert queue statistics (admin only)
   */
  async getQueueStats(): Promise<ExpertQueueStats> {
    return this.makeAuthenticatedRequest('/api/admin/expert-queue/stats');
  }

  /**
   * Assign request to expert (admin only)
   */
  async assignToExpert(requestId: string, expertId: string): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/admin/expert-queue/assign/${requestId}`, {
      method: 'POST',
      body: JSON.stringify({ expert_id: expertId }),
    });
  }

  /**
   * Update request status (admin only)
   */
  async updateRequestStatus(
    requestId: string, 
    status: string, 
    notes?: string
  ): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/admin/expert-queue/status/${requestId}`, {
      method: 'PUT',
      body: JSON.stringify({ status, notes }),
    });
  }

  /**
   * Submit expert review response (expert only)
   */
  async submitExpertReview(
    requestId: string,
    reviewData: {
      expert_analysis: string;
      confidence_score: number;
      recommendations: string[];
      risk_assessment: any;
      expert_notes: string;
    }
  ): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/${requestId}`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  /**
   * Get request details (admin/expert only)
   */
  async getRequestDetails(requestId: string): Promise<ExpertReviewRequest> {
    return this.makeAuthenticatedRequest(`/api/admin/expert-queue/request/${requestId}`);
  }

  /**
   * Cancel expert review request
   */
  async cancelRequest(requestId: string): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/cancel/${requestId}`, {
      method: 'POST',
    });
  }
}

export const expertQueueService = new ExpertQueueService();