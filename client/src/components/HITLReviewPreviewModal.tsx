/**
 * HITL Review Preview Modal Component
 * Shows a quick preview of review details in the HITL dashboard
 */

import React, { useState, useEffect } from 'react';
import { expertQueueService, ExpertReviewRequest } from '../services/expertQueueService';

interface HITLReviewPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewId: string;
  onAssign: (reviewId: string) => void;
}

export const HITLReviewPreviewModal: React.FC<HITLReviewPreviewModalProps> = ({
  isOpen,
  onClose,
  reviewId,
  onAssign
}) => {
  const [review, setReview] = useState<ExpertReviewRequest | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && reviewId) {
      loadReview();
    }
  }, [isOpen, reviewId]);

  const loadReview = async () => {
    try {
      setIsLoading(true);
      setError('');

      const reviewData = await expertQueueService.getRequestDetails(reviewId, false);
      setReview(reviewData);

    } catch (error: any) {
      console.error('Failed to load review:', error);
      setError(error.message || 'Failed to load review details');
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
            Review Details - #{reviewId.split('_').pop()}
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
              <p className="text-slate-300">Loading review details...</p>
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
                onClick={loadReview}
                className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : review ? (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 rounded-lg p-4 email-container">
                  <div className="text-sm text-slate-400 mb-1">User</div>
                  <div className="relative group min-w-0">
                    <div className="text-white font-medium email-modal-text cursor-help" 
                         title={review.user_email}>
                      {review.user_email}
                    </div>
                    {/* Show tooltip if email is long */}
                    {review.user_email.length > 20 && (
                      <div className="email-tooltip bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-slate-800 border-slate-600">
                        {review.user_email}
                        <div className="email-tooltip-arrow top-full left-1/2 transform -translate-x-1/2 border-t-slate-800"></div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Confidence</div>
                  <div className={`text-xl font-bold ${
                    review.confidence_score < 0.4 ? 'text-red-400' : 
                    review.confidence_score < 0.7 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {(review.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Priority</div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(review.priority)}`}>
                    {review.priority.toUpperCase()}
                  </span>
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Est. Time</div>
                  <div className="text-white font-medium">{review.estimated_completion_hours}h</div>
                </div>
              </div>

              {/* AI Analysis Summary */}
              <div className="bg-slate-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium text-white">AI Analysis Summary</h3>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-slate-400">
                      {review.ai_analysis?.analysis_results?.length || 0} clauses
                    </span>
                    {review.ai_analysis?.overall_risk && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(review.ai_analysis.overall_risk.level)}`}>
                        {review.ai_analysis.overall_risk.level} RISK
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {review.ai_analysis?.summary || 'No summary available'}
                </p>
              </div>

              {/* Document Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-400 mb-2">Document Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Type:</span>
                      <span className="text-slate-300">{review.document_type || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Submitted:</span>
                      <span className="text-slate-300">{formatDate(review.created_at)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Status:</span>
                      <span className="text-slate-300">{review.status.replace('_', ' ').toUpperCase()}</span>
                    </div>
                  </div>
                </div>

                {/* Confidence Breakdown */}
                {review.confidence_breakdown && (
                  <div className="bg-slate-900 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-400 mb-2">Confidence Factors</h4>
                    <div className="space-y-2 text-sm">
                      {Object.entries(review.confidence_breakdown.component_weights || {}).slice(0, 3).map(([component, weight]) => (
                        <div key={component} className="flex justify-between">
                          <span className="text-slate-500">{component.replace('_', ' ')}:</span>
                          <span className="text-slate-300">{((weight as number) * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Clause Analysis Preview */}
              {review.ai_analysis?.analysis_results && review.ai_analysis.analysis_results.length > 0 && (
                <div className="bg-slate-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-400 mb-3">Clause Analysis Preview</h4>
                  <div className="space-y-3">
                    {review.ai_analysis.analysis_results.slice(0, 2).map((clause: any, index: number) => (
                      <div key={index} className="bg-slate-800 rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-white">Clause {index + 1}</span>
                          <span className={`px-2 py-1 rounded text-xs ${getRiskLevelColor(clause.risk_level?.level)}`}>
                            {clause.risk_level?.level || 'UNKNOWN'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300" style={{
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>
                          {clause.plain_explanation || clause.clause_text}
                        </p>
                      </div>
                    ))}
                    {review.ai_analysis.analysis_results.length > 2 && (
                      <div className="text-center text-sm text-slate-400">
                        +{review.ai_analysis.analysis_results.length - 2} more clauses
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Low Confidence Warning */}
              {review.confidence_score < 0.5 && (
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
        {review && (
          <div className="flex justify-between items-center p-6 border-t border-slate-700">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
            >
              Close
            </button>
            
            <div className="flex space-x-3">
              {review.status === 'pending' && (
                <button
                  onClick={() => onAssign(reviewId)}
                  className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-600 text-white rounded-lg hover:from-emerald-600 hover:to-green-700 transition-all duration-200 font-medium flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <span>Assign to Expert</span>
                </button>
              )}
              
              {review.status !== 'pending' && (
                <div className="text-sm text-slate-400">
                  Status: {review.status.replace('_', ' ').toUpperCase()}
                  {review.assigned_expert_id && (
                    <div className="text-xs">Assigned to: {review.assigned_expert_id}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};