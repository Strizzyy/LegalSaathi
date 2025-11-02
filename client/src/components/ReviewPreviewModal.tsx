/**
 * Review Preview Modal Component
 * Shows a quick preview of review details before full assignment
 */

import React, { useState, useEffect } from 'react';

interface ReviewPreview {
  review_id: string;
  user_email: string;
  confidence_score: number;
  status: string;
  priority: string;
  created_at: string;
  document_type?: string;
  estimated_completion_hours: number;
  ai_analysis_summary: {
    summary: string;
    overall_risk: any;
    clause_count: number;
    processing_time: number;
  };
  confidence_breakdown: any;
}

interface ReviewPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewId: string;
  onAssign: (reviewId: string) => void;
  onViewFull: (reviewId: string) => void;
}

export const ReviewPreviewModal: React.FC<ReviewPreviewModalProps> = ({
  isOpen,
  onClose,
  reviewId,
  onAssign,
  onViewFull
}) => {
  const [preview, setPreview] = useState<ReviewPreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && reviewId) {
      loadPreview();
    }
  }, [isOpen, reviewId]);

  const loadPreview = async () => {
    try {
      setIsLoading(true);
      setError('');

      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch(`/api/expert/review/${reviewId}/preview`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load preview');
      }

      const result = await response.json();
      
      if (result.success && result.preview) {
        setPreview(result.preview);
      } else {
        throw new Error('Preview not available');
      }

    } catch (error: any) {
      console.error('Failed to load preview:', error);
      setError(error.message || 'Failed to load preview');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getRiskLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'RED': return 'text-red-400 bg-red-900/30';
      case 'YELLOW': return 'text-yellow-400 bg-yellow-900/30';
      case 'GREEN': return 'text-green-400 bg-green-900/30';
      default: return 'text-slate-400 bg-slate-900/30';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent': return 'text-red-400 bg-red-900/30';
      case 'high': return 'text-orange-400 bg-orange-900/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/30';
      case 'low': return 'text-green-400 bg-green-900/30';
      default: return 'text-slate-400 bg-slate-900/30';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">
            Review Preview - #{reviewId.split('_').pop()}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-slate-300">Loading preview...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <div className="text-red-400 mb-4">
                <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-red-300 mb-4">{error}</p>
              <button
                onClick={loadPreview}
                className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : preview ? (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">User</div>
                  <div className="text-white font-medium">{preview.user_email}</div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Confidence</div>
                  <div className={`text-xl font-bold ${
                    preview.confidence_score < 0.4 ? 'text-red-400' : 
                    preview.confidence_score < 0.7 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {(preview.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Priority</div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(preview.priority)}`}>
                    {preview.priority.toUpperCase()}
                  </span>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Est. Time</div>
                  <div className="text-white font-medium">{preview.estimated_completion_hours}h</div>
                </div>
              </div>

              {/* AI Analysis Summary */}
              <div className="bg-slate-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium text-white">AI Analysis Summary</h3>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-slate-400">
                      {preview.ai_analysis_summary.clause_count} clauses
                    </span>
                    {preview.ai_analysis_summary.overall_risk && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(preview.ai_analysis_summary.overall_risk.level)}`}>
                        {preview.ai_analysis_summary.overall_risk.level} RISK
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {preview.ai_analysis_summary.summary || 'No summary available'}
                </p>
              </div>

              {/* Document Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-400 mb-2">Document Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Type:</span>
                      <span className="text-slate-300">{preview.document_type || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Submitted:</span>
                      <span className="text-slate-300">{formatDate(preview.created_at)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Processing Time:</span>
                      <span className="text-slate-300">{preview.ai_analysis_summary.processing_time}s</span>
                    </div>
                  </div>
                </div>

                {/* Confidence Breakdown */}
                {preview.confidence_breakdown && (
                  <div className="bg-slate-900 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-400 mb-2">Confidence Factors</h4>
                    <div className="space-y-2 text-sm">
                      {Object.entries(preview.confidence_breakdown.component_weights || {}).slice(0, 3).map(([component, weight]) => (
                        <div key={component} className="flex justify-between">
                          <span className="text-slate-500">{component.replace('_', ' ')}:</span>
                          <span className="text-slate-300">{((weight as number) * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Low Confidence Warning */}
              {preview.confidence_score < 0.5 && (
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <div className="text-yellow-300 font-medium">Low Confidence Analysis</div>
                      <div className="text-yellow-200 text-sm">
                        This document requires careful expert review due to low AI confidence scores.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Actions */}
        {preview && (
          <div className="flex justify-between items-center p-6 border-t border-slate-700">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
            >
              Close
            </button>
            
            <div className="flex space-x-3">
              <button
                onClick={() => onViewFull(reviewId)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span>View Full Details</span>
              </button>
              
              {preview.status === 'pending' && (
                <button
                  onClick={() => onAssign(reviewId)}
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 font-medium flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <span>Assign to Me & Start Review</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};