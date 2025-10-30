/**
 * TypeScript type definitions for admin cost monitoring
 * INTERNAL USE ONLY - Admin interfaces
 */

export interface CostAnalytics {
  daily_cost: number;
  monthly_cost: number;
  service_breakdown: Record<string, number>;
  usage_trends: Array<{
    date: string;
    cost: number;
    requests: number;
  }>;
  optimization_suggestions: string[];
  cost_savings: number;
}

export interface QuotaLimits {
  per_minute: number;
  per_hour: number;
  per_day: number;
  burst_limit: number;
}

export interface QuotaUsage {
  per_minute: number;
  per_hour: number;
  per_day: number;
}

export interface QuotaPercentages {
  per_minute: number;
  per_hour: number;
  per_day: number;
}

export interface CircuitBreakerStatus {
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
}

export interface QuotaStatus {
  service: string;
  service_name?: string;
  limits: QuotaLimits;
  current_usage: QuotaUsage;
  usage_percentages: QuotaPercentages;
  circuit_breaker: CircuitBreakerStatus;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'active' | 'idle';
  last_updated: string;
  timestamp?: string;
}

export interface HealthComponent {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'disabled';
  error?: string;
  daily_cost?: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: Record<string, HealthComponent>;
}

export interface AdminApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface CostAnalyticsResponse extends AdminApiResponse<CostAnalytics> {
  analytics: CostAnalytics;
  period_days: number;
}

export interface QuotaStatusResponse extends AdminApiResponse<Record<string, QuotaStatus>> {
  quotas: Record<string, QuotaStatus>;
}

export interface HealthStatusResponse extends AdminApiResponse<HealthStatus> {
  health: HealthStatus;
}

export interface OptimizationRequest {
  service?: string;
  operation?: string;
  query?: string;
  model?: string;
  max_tokens?: number;
}

export interface OptimizationResponse extends AdminApiResponse<any> {
  optimization: {
    recommended_action: string;
    delay?: number;
    reason: string;
    batch_available?: boolean;
  };
}

// Service priority levels
export enum ServicePriority {
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW'
}

// Service types
export enum ServiceType {
  VERTEX_AI = 'vertex_ai',
  GEMINI_API = 'gemini_api',
  DOCUMENT_AI = 'document_ai',
  NATURAL_LANGUAGE_AI = 'natural_language_ai',
  TRANSLATION_API = 'translation_api',
  VISION_API = 'vision_api',
  SPEECH_API = 'speech_api'
}

// Circuit breaker states
export enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

// Health status levels
export enum HealthStatusLevel {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  DISABLED = 'disabled'
}