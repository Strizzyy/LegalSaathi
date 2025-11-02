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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class AdminCostService {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const user = auth.currentUser;
    if (!user) {
      console.error('Admin service: No authenticated user');
      throw new Error('User not authenticated');
    }

    console.log('Admin service: Getting token for user:', user.email);
    const token = await user.getIdToken();
    console.log('Admin service: Token obtained, length:', token.length);
    
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
      const url = `${API_BASE_URL}${endpoint}`;
      
      console.log('Admin API request:', url);
      console.log('Headers:', { ...headers, Authorization: '[REDACTED]' });
      
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      console.log('Admin API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Admin API error response:', errorText);
        
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        if (response.status === 403) {
          throw new Error('Admin access required');
        }
        throw new Error(`Request failed: ${response.status} ${response.statusText} - ${errorText}`);
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
   * Test basic API connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      console.log('Testing API connection to:', API_BASE_URL);
      const response = await fetch(`${API_BASE_URL}/health`);
      console.log('API connection test response:', response.status);
      return response.ok;
    } catch (error) {
      console.error('API connection test failed:', error);
      return false;
    }
  }

  /**
   * Check if current user has admin access
   */
  async checkAdminAccess(): Promise<boolean> {
    try {
      // First test basic API connectivity
      const apiConnected = await this.testConnection();
      if (!apiConnected) {
        console.error('Admin check failed: API not reachable');
        return false;
      }

      // Check if user is authenticated
      const user = auth.currentUser;
      if (!user) {
        console.log('Admin check failed: No authenticated user');
        return false;
      }

      console.log('Admin check: User authenticated:', user.email);
      
      // Check if user email is in admin list (client-side check for quick feedback)
      const adminEmails = ['23cd3034@rgipt.ac.in', 'admin@legalsaathi.com', 'k.sharmashubh123@gmail.com', '23mc3055@rgipt.ac.in'];
      if (!adminEmails.includes(user.email || '')) {
        console.log('Admin check: User email not in admin list');
        return false;
      }
      
      // Try the verification endpoint (doesn't throw errors)
      try {
        const verifyResponse = await this.makeAuthenticatedRequest<{is_admin: boolean, message: string}>('/api/admin/verify');
        console.log('Admin verify response:', verifyResponse);
        return verifyResponse.is_admin;
      } catch (error) {
        console.error('Admin server verification failed:', error);
        // In development mode, allow access if user is in admin list
        if (import.meta.env.DEV) {
          console.log('Development mode: Allowing admin access despite server error');
          return true;
        }
        return false;
      }
    } catch (error) {
      console.error('Admin access check failed:', error);
      return false;
    }
  }
}

export const adminCostService = new AdminCostService();