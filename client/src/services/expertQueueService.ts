/**
 * Expert Queue Service - Human-in-the-Loop Management
 * Manages expert review queue for low confidence documents
 */

import { auth } from '../firebaseConfig';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ExpertReviewRequest {
  review_id: string;
  user_email: string;
  confidence_score: number;
  confidence_breakdown: any;
  status: 'pending' | 'in_review' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
  assigned_expert_id?: string;
  assigned_at?: string;
  completed_at?: string;
  estimated_completion_hours: number;
  document_type?: string;
  expert_notes?: string;
  ai_analysis: any;
  document_content?: string;
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
      // For testing, try without authentication first, then fall back to auth if needed
      let headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      try {
        // Try to get auth headers if user is logged in
        const authHeaders = await this.getAuthHeaders();
        headers = { ...headers, ...authHeaders };
        console.log('Using authenticated request for:', endpoint);
      } catch (authError) {
        // Continue without auth headers for public endpoints
        console.log('No authentication available, trying public access for:', endpoint);
      }
      
      console.log('Making request to:', `${API_BASE_URL}${endpoint}`);
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      console.log('Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        if (response.status === 403) {
          throw new Error('Admin access required');
        }
        if (response.status === 404) {
          throw new Error(`Endpoint not found: ${endpoint}`);
        }
        throw new Error(`Request failed (${response.status}): ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      return data;
    } catch (error) {
      console.error('Expert Queue API request failed:', error);
      throw error;
    }
  }

  /**
   * Submit document for expert review
   */
  async submitForExpertReview(data: {
    document_content: string;
    user_email: string;
    document_type?: string;
    confidence_score: number;
    confidence_breakdown: any;
    ai_analysis: any;
  }): Promise<{ review_id: string; status: string; estimated_completion_hours: number; priority: string; created_at: string; message: string }> {
    return this.makeAuthenticatedRequest('/api/expert-queue/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Get all expert review requests
   */
  async getExpertRequests(
    status?: string,
    priority?: string,
    page: number = 1,
    limit: number = 20,
    sort_by: string = "created_at",
    sort_order: string = "desc"
  ): Promise<{
    items: ExpertReviewRequest[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      sort_by: sort_by,
      sort_order: sort_order,
    });
    
    if (status) {
      params.append('status', status);
    }
    
    if (priority) {
      params.append('priority', priority);
    }

    return this.makeAuthenticatedRequest(`/api/expert-queue/queue?${params}`);
  }

  /**
   * Get expert queue statistics
   */
  async getQueueStats(): Promise<{
    total_items: number;
    pending_items: number;
    in_review_items: number;
    completed_items: number;
    cancelled_items: number;
    average_completion_time_hours: number;
    oldest_pending_item?: string;
    expert_workload: Record<string, number>;
  }> {
    return this.makeAuthenticatedRequest('/api/expert-queue/stats');
  }

  /**
   * Assign request to expert
   */
  async assignToExpert(reviewId: string, expertId: string): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/${reviewId}/assign/${expertId}`, {
      method: 'PUT',
    });
  }

  /**
   * Update request status
   */
  async updateRequestStatus(
    reviewId: string, 
    status: string, 
    expertId?: string,
    notes?: string
  ): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/${reviewId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, expert_id: expertId, notes }),
    });
  }

  /**
   * Submit expert review response
   */
  async submitExpertReview(
    reviewId: string,
    expertId: string,
    reviewData: {
      expert_analysis: any;
      expert_notes?: string;
      clauses_modified: number;
      complexity_rating: number;
      review_duration_minutes: number;
    }
  ): Promise<{
    review_id: string;
    expert_id: string;
    expert_analysis: any;
    expert_notes?: string;
    completed_at: string;
    review_duration_minutes: number;
    confidence_improvement: number;
  }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/complete?expert_id=${expertId}`, {
      method: 'POST',
      body: JSON.stringify({
        review_id: reviewId,
        ...reviewData
      }),
    });
  }

  /**
   * Get request details
   */
  async getRequestDetails(reviewId: string, includeContent: boolean = false): Promise<ExpertReviewRequest> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/${reviewId}?include_content=${includeContent}`);
  }

  /**
   * Get request preview (for HITL dashboard)
   */
  async getRequestPreview(reviewId: string): Promise<any> {
    return this.makeAuthenticatedRequest(`/api/expert/review/${reviewId}/preview`);
  }

  /**
   * Get next review for expert
   */
  async getNextReviewForExpert(expertId: string): Promise<ExpertReviewRequest | null> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/next-review/${expertId}`);
  }

  /**
   * Cancel expert review request
   */
  async cancelRequest(reviewId: string): Promise<{ success: boolean }> {
    return this.makeAuthenticatedRequest(`/api/expert-queue/review/${reviewId}/cancel`, {
      method: 'DELETE',
    });
  }
}

export const expertQueueService = new ExpertQueueService();