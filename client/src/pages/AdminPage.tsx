/**
 * Admin Page - Dedicated page for cost monitoring dashboard
 * INTERNAL USE ONLY
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { adminCostService } from '../services/adminCostService';
import type { CostAnalytics, QuotaStatus, HealthStatus } from '../types/admin';
import { ArrowLeft, RefreshCw, DollarSign, Activity, Shield } from 'lucide-react';

const AdminPage: React.FC = () => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'analytics' | 'usage' | 'health'>('analytics');
  
  // Data states
  const [analytics, setAnalytics] = useState<CostAnalytics | null>(null);
  const [quotas, setQuotas] = useState<Record<string, QuotaStatus> | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Navigation function
  const handleBackToApp = () => {
    // Navigate back to the main application
    window.history.pushState({}, '', '/');
    window.location.reload();
  };

  // Check admin access on mount
  useEffect(() => {
    const checkAccess = async () => {
      try {
        if (!user) {
          setIsAdmin(false);
          setLoading(false);
          return;
        }

        const hasAccess = await adminCostService.checkAdminAccess();
        setIsAdmin(hasAccess);
        
        if (hasAccess) {
          await loadData();
        }
      } catch (err) {
        setError('Failed to verify admin access');
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    checkAccess();
  }, [user]);

  const loadData = async () => {
    try {
      setError(null);
      setRefreshing(true);
      
      // Load all data in parallel
      const [analyticsRes, quotasRes, healthRes] = await Promise.all([
        adminCostService.getCostAnalytics(30),
        adminCostService.getQuotaStatus(),
        adminCostService.getHealthStatus()
      ]);

      setAnalytics(analyticsRes.analytics);
      setQuotas(quotasRes.quotas);
      setHealth(healthRes.health);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setRefreshing(false);
    }
  };



  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'text-emerald-400';
      case 'degraded': return 'text-yellow-400';
      case 'unhealthy': return 'text-red-400';
      case 'disabled': return 'text-slate-400';
      default: return 'text-slate-400';
    }
  };

  const getUsageColor = (percentage: number): string => {
    if (percentage >= 95) return 'bg-red-400';
    if (percentage >= 80) return 'bg-yellow-400';
    if (percentage >= 60) return 'bg-blue-400';
    return 'bg-emerald-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400 mx-auto"></div>
          <p className="mt-4 text-slate-300">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 max-w-md">
          <h2 className="text-xl font-bold text-red-400 mb-4">Authentication Required</h2>
          <p className="text-slate-300 mb-4">Please log in to access the admin dashboard.</p>
          <button
            onClick={handleBackToApp}
            className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 flex items-center transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to LegalSaathi
          </button>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 max-w-md">
          <h2 className="text-xl font-bold text-red-400 mb-4">Access Denied</h2>
          <p className="text-slate-300 mb-4">
            You don't have admin privileges to access the cost monitoring dashboard.
          </p>
          <button
            onClick={handleBackToApp}
            className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 flex items-center transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to LegalSaathi
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800/95 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <button
                onClick={handleBackToApp}
                className="mr-6 px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg transition-colors flex items-center shadow-lg hover:shadow-xl"
                title="Back to LegalSaathi"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">Back to Analysis</span>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Admin Dashboard
                </h1>
                <p className="text-sm text-slate-400">Internal cost tracking and API usage monitoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-400">
                Admin: <span className="text-emerald-400">{user.email}</span>
              </span>
              <button
                onClick={loadData}
                disabled={refreshing}
                className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center transition-colors"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { key: 'analytics', label: 'Cost Analytics', icon: DollarSign },
              { key: 'usage', label: 'API Usage', icon: Activity },
              { key: 'health', label: 'System Health', icon: Shield }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`flex items-center px-1 py-4 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.key
                      ? 'border-emerald-400 text-emerald-400'
                      : 'border-transparent text-slate-400 hover:text-white hover:border-slate-600'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg mb-6">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && analytics && (
          <div className="space-y-6">
            {/* Cost Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
                <div className="flex items-center">
                  <div className="p-2 bg-emerald-900/50 rounded-lg">
                    <DollarSign className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-400">Daily Cost</p>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(analytics.daily_cost)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-900/50 rounded-lg">
                    <DollarSign className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-400">Monthly Cost</p>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(analytics.monthly_cost)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-900/50 rounded-lg">
                    <Activity className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-400">Active Services</p>
                    <p className="text-2xl font-bold text-white">
                      {Object.keys(analytics.service_breakdown).length}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Service Breakdown */}
            <div className="bg-slate-800 rounded-lg border border-slate-700">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-medium text-white">Service Cost Breakdown</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {Object.entries(analytics.service_breakdown).map(([service, cost]) => {
                    const percentage = analytics.monthly_cost > 0 
                      ? (cost / analytics.monthly_cost) * 100 
                      : 0;
                    return (
                      <div key={service} className="flex items-center justify-between">
                        <span className="text-sm font-medium text-white capitalize">
                          {service.replace('_', ' ')}
                        </span>
                        <div className="flex items-center space-x-4">
                          <div className="w-32 bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-emerald-400 h-2 rounded-full"
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-white w-20 text-right">
                            {formatCurrency(cost)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Optimization Suggestions */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-medium text-white">Optimization Suggestions</h3>
              </div>
              <div className="p-6">
                <ul className="space-y-3">
                  {analytics.optimization_suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-blue-400 mr-3 mt-0.5">•</span>
                      <span className="text-slate-300">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* API Usage Tab */}
        {activeTab === 'usage' && quotas && (
          <div className="space-y-6">
            {Object.entries(quotas).map(([serviceName, quota]) => (
              <div key={serviceName} className="bg-slate-800 rounded-lg border border-slate-700">
                <div className="px-6 py-4 border-b border-slate-700">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-white capitalize">
                      {quota.service_name || serviceName.replace('_', ' ')} - {quota.priority} Priority
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      quota.status === 'active' 
                        ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700' 
                        : 'bg-slate-700 text-slate-400 border border-slate-600'
                    }`}>
                      {quota.status}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Per Minute */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="font-medium text-slate-300">Last Minute</span>
                        <span className="text-slate-400">{quota.usage_percentages.per_minute.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full ${getUsageColor(quota.usage_percentages.per_minute)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_minute, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {quota.current_usage.per_minute.toLocaleString()} requests
                      </div>
                      <div className="text-xs text-slate-500">
                        Limit: {quota.limits.per_minute.toLocaleString()}
                      </div>
                    </div>

                    {/* Per Hour */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="font-medium text-slate-300">Last Hour</span>
                        <span className="text-slate-400">{quota.usage_percentages.per_hour.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full ${getUsageColor(quota.usage_percentages.per_hour)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_hour, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {quota.current_usage.per_hour.toLocaleString()} requests
                      </div>
                      <div className="text-xs text-slate-500">
                        Limit: {quota.limits.per_hour.toLocaleString()}
                      </div>
                    </div>

                    {/* Per Day */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="font-medium text-slate-300">Today</span>
                        <span className="text-slate-400">{quota.usage_percentages.per_day.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full ${getUsageColor(quota.usage_percentages.per_day)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_day, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {quota.current_usage.per_day.toLocaleString()} requests
                      </div>
                      <div className="text-xs text-slate-500">
                        Limit: {quota.limits.per_day.toLocaleString()}
                      </div>
                    </div>
                  </div>

                  {/* Circuit Breaker Status */}
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-300">Circuit Breaker Status:</span>
                      <span className={`text-sm font-medium capitalize ${
                        quota.circuit_breaker.state === 'closed' ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {quota.circuit_breaker.state}
                        {quota.circuit_breaker.failure_count > 0 && (
                          <span className="text-red-400 ml-2">
                            ({quota.circuit_breaker.failure_count} failures)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Health Tab */}
        {activeTab === 'health' && health && (
          <div className="space-y-6">
            {/* Overall Status */}
            <div className="bg-slate-800 rounded-lg border border-slate-700">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-medium text-white">Overall System Status</h3>
              </div>
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-4 h-4 rounded-full mr-3 ${
                      health.status === 'healthy' ? 'bg-emerald-400' : 
                      health.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
                    }`}></div>
                    <span className={`text-lg font-medium capitalize ${getStatusColor(health.status)}`}>
                      {health.status}
                    </span>
                  </div>
                  <span className="text-sm text-slate-400">
                    Last updated: {new Date(health.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Component Status */}
            <div className="bg-slate-800 rounded-lg border border-slate-700">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-medium text-white">Component Health</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(health.components).map(([component, status]) => (
                    <div key={component} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-3 ${
                          status.status === 'healthy' ? 'bg-emerald-400' : 
                          status.status === 'disabled' ? 'bg-slate-500' : 'bg-red-400'
                        }`}></div>
                        <span className="font-medium text-white capitalize">{component}</span>
                      </div>
                      <div className="text-right">
                        <span className={`text-sm font-medium capitalize ${getStatusColor(status.status)}`}>
                          {status.status}
                        </span>
                        {status.error && (
                          <div className="text-xs text-red-400 mt-1">
                            {status.error}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}


      </div>
    </div>
  );
};

export default AdminPage;