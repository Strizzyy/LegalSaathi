/**
 * Admin Cost Monitoring Service - INTERNAL USE ONLY
 * Provides access to cost analytics and quota management for administrators
 */

import { auth } from '../firebaseConfig';
import type {
  CostAnalyticsResponse,
  QuotaStatusResponse,
  HealthStatusResponse,
  OptimizationRequest,
  OptimizationResponse
} from '../types/admin';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000');

class AdminCostService {
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
      console.error('Admin API request failed:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive cost analytics
   */
  async getCostAnalytics(days: number = 30): Promise<CostAnalyticsResponse> {
    return this.makeAuthenticatedRequest(
      `/api/admin/costs/analytics?days=${days}`
    );
  }

  /**
   * Get quota status for all services
   */
  async getQuotaStatus(): Promise<QuotaStatusResponse> {
    return this.makeAuthenticatedRequest('/api/admin/costs/quotas');
  }

  /**
   * Get health status of cost monitoring system
   */
  async getHealthStatus(): Promise<HealthStatusResponse> {
    return this.makeAuthenticatedRequest('/api/admin/costs/health');
  }

  /**
   * Optimize request for cost efficiency
   */
  async optimizeRequest(requestData: OptimizationRequest): Promise<OptimizationResponse> {
    return this.makeAuthenticatedRequest('/api/admin/costs/optimize', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  /**
   * Check if current user has admin access
   */
  async checkAdminAccess(): Promise<boolean> {
    try {
      await this.getHealthStatus();
      return true;
    } catch (error) {
      return false;
    }
  }
}

export const adminCostService = new AdminCostService();