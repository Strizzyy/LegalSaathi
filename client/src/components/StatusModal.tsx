import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { Modal } from './Modal';
import { apiService } from '../services/apiService';
import { notificationService } from '../services/notificationService';

interface StatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ServiceStatus {
  [key: string]: boolean;
}

export function StatusModal({ isOpen, onClose }: StatusModalProps) {
  const [services, setServices] = useState<ServiceStatus>({});
  const [isLoading, setIsLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkStatus = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.checkHealth();
      setServices(result.services || {});
      setLastChecked(new Date());
      notificationService.info('AI services status updated');
    } catch (error) {
      console.error('Status check error:', error);
      notificationService.error('Unable to check AI services status');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      checkStatus();
    }
  }, [isOpen]);

  const getServiceDisplayName = (serviceName: string): string => {
    const displayNames: { [key: string]: string } = {
      'document_ai': 'Document AI Processing',
      'natural_language': 'Natural Language Analysis',
      'translation': 'Translation Service',
      'risk_analysis': 'Risk Assessment Engine',
      'export': 'Export Services',
      'database': 'Database Connection',
      'gemini_api': 'Gemini AI API',
      'groq_api': 'Groq AI API (Legacy)',
    };
    return displayNames[serviceName] || serviceName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getOverallStatus = (): 'healthy' | 'degraded' | 'down' => {
    const serviceValues = Object.values(services);
    if (serviceValues.length === 0) return 'down';
    
    const healthyCount = serviceValues.filter(Boolean).length;
    const totalCount = serviceValues.length;
    
    if (healthyCount === totalCount) return 'healthy';
    if (healthyCount > 0) return 'degraded';
    return 'down';
  };

  const overallStatus = getOverallStatus();

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="AI Services Status" maxWidth="md">
      <div className="space-y-6">
        {/* Overall Status */}
        <div className={`p-4 rounded-lg border ${
          overallStatus === 'healthy' 
            ? 'bg-green-500/10 border-green-500/50' 
            : overallStatus === 'degraded'
            ? 'bg-yellow-500/10 border-yellow-500/50'
            : 'bg-red-500/10 border-red-500/50'
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              overallStatus === 'healthy' 
                ? 'bg-green-500' 
                : overallStatus === 'degraded'
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`} />
            <div>
              <h3 className={`font-semibold ${
                overallStatus === 'healthy' 
                  ? 'text-green-400' 
                  : overallStatus === 'degraded'
                  ? 'text-yellow-400'
                  : 'text-red-400'
              }`}>
                System Status: {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
              </h3>
              <p className="text-sm text-slate-400">
                {overallStatus === 'healthy' && 'All services are operational'}
                {overallStatus === 'degraded' && 'Some services may be experiencing issues'}
                {overallStatus === 'down' && 'Services are currently unavailable'}
              </p>
            </div>
          </div>
        </div>

        {/* Services List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-white">Service Details</h4>
            <button
              onClick={checkStatus}
              disabled={isLoading}
              className="inline-flex items-center px-3 py-1 text-xs bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
              ) : (
                <RefreshCw className="w-3 h-3 mr-1" />
              )}
              Refresh
            </button>
          </div>

          {Object.keys(services).length === 0 && !isLoading ? (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-400">No service status available</p>
              <button
                onClick={checkStatus}
                className="mt-3 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
              >
                Check Status
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(services).map(([serviceName, isHealthy]) => (
                <motion.div
                  key={serviceName}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    {isHealthy ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <span className="text-sm font-medium text-white">
                      {getServiceDisplayName(serviceName)}
                    </span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    isHealthy 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {isHealthy ? 'Online' : 'Offline'}
                  </span>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Last Checked */}
        {lastChecked && (
          <div className="text-center">
            <p className="text-xs text-slate-500">
              Last checked: {lastChecked.toLocaleString()}
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-4">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-400 mx-auto mb-2" />
            <p className="text-sm text-slate-400">Checking service status...</p>
          </div>
        )}
      </div>
    </Modal>
  );
}