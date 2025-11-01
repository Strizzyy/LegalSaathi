/**
 * Admin Dashboard Component - INTERNAL USE ONLY
 * Provides cost monitoring and quota management interface for administrators
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { adminCostService } from '../../services/adminCostService';
import type { CostAnalytics, QuotaStatus, HealthStatus } from '../../types/admin';

interface AdminDashboardProps {
  onClose?: () => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ onClose }) => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'analytics' | 'quotas' | 'health'>('analytics');

  // Data states
  const [analytics, setAnalytics] = useState<CostAnalytics | null>(null);
  const [quotas, setQuotas] = useState<Record<string, QuotaStatus> | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check admin access on mount
  useEffect(() => {
    const checkAccess = async () => {
      try {
        const hasAccess = await adminCostService.checkAdminAccess();
        setIsAdmin(hasAccess);
        if (hasAccess) {
          await loadData();
        }
      } catch (err) {
        setError('Failed to verify admin access');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      checkAccess();
    } else {
      setLoading(false);
    }
  }, [user]);

  const loadData = async () => {
    try {
      setError(null);

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
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getUsageColor = (percentage: number): string => {
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-4">Please log in to access the admin dashboard.</p>
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You don't have admin privileges to access the cost monitoring dashboard.
          </p>
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl h-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">Admin Cost Monitoring Dashboard</h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-300">
              Admin: {user.email}
            </span>
            <button
              onClick={loadData}
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
            >
              Refresh
            </button>
            <button
              onClick={onClose}
              className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
            >
              Close
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-gray-100 border-b">
          <div className="flex">
            {[
              { key: 'analytics', label: 'Cost Analytics' },
              { key: 'quotas', label: 'Quota Status' },
              { key: 'health', label: 'System Health' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`px-6 py-3 font-medium ${activeTab === tab.key
                  ? 'bg-white border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto h-full">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && analytics && (
            <div className="space-y-6">
              {/* Cost Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-800">Daily Cost</h3>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(analytics.daily_cost)}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-green-800">Monthly Cost</h3>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(analytics.monthly_cost)}
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-purple-800">Services</h3>
                  <p className="text-2xl font-bold text-purple-600">
                    {Object.keys(analytics.service_breakdown).length}
                  </p>
                </div>
              </div>

              {/* Service Breakdown */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-semibold mb-4">Service Cost Breakdown</h3>
                <div className="space-y-2">
                  {Object.entries(analytics.service_breakdown).map(([service, cost]) => {
                    const percentage = analytics.monthly_cost > 0
                      ? (cost / analytics.monthly_cost) * 100
                      : 0;
                    return (
                      <div key={service} className="flex justify-between items-center">
                        <span className="capitalize">{service.replace('_', ' ')}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium w-20 text-right">
                            {formatCurrency(cost)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Optimization Suggestions */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-800 mb-3">Optimization Suggestions</h3>
                <ul className="space-y-2">
                  {analytics.optimization_suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-yellow-600 mr-2">💡</span>
                      <span className="text-yellow-700">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Quotas Tab */}
          {activeTab === 'quotas' && quotas && (
            <div className="space-y-4">
              {Object.entries(quotas).map(([serviceName, quota]) => (
                <div key={serviceName} className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold mb-3 capitalize">
                    {serviceName.replace('_', ' ')} - {quota.priority} Priority
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Per Minute */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Per Minute</span>
                        <span>{quota.usage_percentages.per_minute.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getUsageColor(quota.usage_percentages.per_minute)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_minute, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {quota.current_usage.per_minute} / {quota.limits.per_minute}
                      </div>
                    </div>

                    {/* Per Hour */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Per Hour</span>
                        <span>{quota.usage_percentages.per_hour.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getUsageColor(quota.usage_percentages.per_hour)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_hour, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {quota.current_usage.per_hour} / {quota.limits.per_hour}
                      </div>
                    </div>

                    {/* Per Day */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Per Day</span>
                        <span>{quota.usage_percentages.per_day.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getUsageColor(quota.usage_percentages.per_day)}`}
                          style={{ width: `${Math.min(quota.usage_percentages.per_day, 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {quota.current_usage.per_day} / {quota.limits.per_day}
                      </div>
                    </div>
                  </div>

                  {/* Circuit Breaker Status */}
                  <div className="mt-3 text-sm">
                    <span className="font-medium">Circuit Breaker: </span>
                    <span className={`capitalize ${quota.circuit_breaker.state === 'closed' ? 'text-green-600' : 'text-red-600'
                      }`}>
                      {quota.circuit_breaker.state}
                    </span>
                    {quota.circuit_breaker.failure_count > 0 && (
                      <span className="text-red-600 ml-2">
                        ({quota.circuit_breaker.failure_count} failures)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Health Tab */}
          {activeTab === 'health' && health && (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Overall System Status</h3>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' :
                    health.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                  <span className={`font-medium capitalize ${getStatusColor(health.status)}`}>
                    {health.status}
                  </span>
                  <span className="text-gray-500 text-sm ml-4">
                    Last updated: {new Date(health.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Component Status */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Component Health</h3>
                <div className="space-y-3">
                  {Object.entries(health.components).map(([component, status]) => (
                    <div key={component} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="font-medium capitalize">{component}</span>
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${status.status === 'healthy' ? 'bg-green-500' :
                          status.status === 'disabled' ? 'bg-gray-500' : 'bg-red-500'
                          }`}></div>
                        <span className={`text-sm capitalize ${getStatusColor(status.status)}`}>
                          {status.status}
                        </span>
                        {status.error && (
                          <span className="text-xs text-red-600 ml-2">
                            ({status.error})
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;