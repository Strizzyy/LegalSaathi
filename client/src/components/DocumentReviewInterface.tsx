/**
 * Document Review Interface Component
 * Displays original document, AI analysis, and expert review tools
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { notificationService } from '../services/notificationService';

interface ReviewItem {
  review_id: string;
  user_email: string;
  confidence_score: number;
  confidence_breakdown: any;
  status: string;
  priority: string;
  created_at: string;
  document_type?: string;
  ai_analysis: any;
  document_content: string;
}

interface ClauseReview {
  clause_id: string;
  original_text: string;
  ai_assessment: any;
  ai_confidence: number;
  expert_modification?: any;
  approved: boolean;
  expert_notes?: string;
}

const DocumentReviewInterface: React.FC = () => {
  const { reviewId } = useParams<{ reviewId: string }>();
  const navigate = useNavigate();
  
  const [reviewItem, setReviewItem] = useState<ReviewItem | null>(null);
  const [clauseReviews, setClauseReviews] = useState<ClauseReview[]>([]);
  const [overallSummary, setOverallSummary] = useState('');
  const [expertNotes, setExpertNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [reviewStartTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState<'document' | 'analysis' | 'review'>('document');

  useEffect(() => {
    if (reviewId) {
      loadReviewDetails();
    }
  }, [reviewId]);

  const loadReviewDetails = async () => {
    try {
      setIsLoading(true);
      setError('');

      const token = localStorage.getItem('expert_token');
      if (!token) {
        navigate('/expert-portal');
        return;
      }

      const response = await fetch(`/api/expert/review/${reviewId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load review details');
      }

      const result = await response.json();
      
      if (!result.success || !result.review) {
        throw new Error('Review not found');
      }

      const review = result.review;
      setReviewItem(review);
      setOverallSummary(review.ai_analysis.summary || '');

      // Initialize clause reviews from AI analysis
      if (review.ai_analysis.analysis_results) {
        const clauses = review.ai_analysis.analysis_results.map((clause: any, index: number) => ({
          clause_id: clause.clause_id || `clause_${index}`,
          original_text: clause.clause_text || '',
          ai_assessment: clause,
          ai_confidence: clause.risk_level?.confidence_percentage || 0,
          approved: false,
          expert_notes: ''
        }));
        setClauseReviews(clauses);
      }

    } catch (error: any) {
      console.error('Failed to load review details:', error);
      setError(error.message || 'Failed to load review details');
      notificationService.error('Failed to load review details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClauseApproval = (clauseId: string, approved: boolean) => {
    setClauseReviews(prev => 
      prev.map(clause => 
        clause.clause_id === clauseId 
          ? { ...clause, approved, expert_modification: approved ? undefined : clause.expert_modification }
          : clause
      )
    );
  };

  const handleClauseModification = (clauseId: string, field: string, value: any) => {
    setClauseReviews(prev => 
      prev.map(clause => {
        if (clause.clause_id === clauseId) {
          const modification = clause.expert_modification || { ...clause.ai_assessment };
          
          if (field === 'plain_explanation') {
            modification.plain_explanation = value;
          } else if (field === 'legal_implications') {
            modification.legal_implications = Array.isArray(value) ? value : [value];
          } else if (field === 'recommendations') {
            modification.recommendations = Array.isArray(value) ? value : [value];
          } else if (field === 'risk_level') {
            modification.risk_level = { ...modification.risk_level, level: value };
          }
          
          return { 
            ...clause, 
            expert_modification: modification,
            approved: false // Reset approval when modified
          };
        }
        return clause;
      })
    );
  };

  const handleClauseNotes = (clauseId: string, notes: string) => {
    setClauseReviews(prev => 
      prev.map(clause => 
        clause.clause_id === clauseId 
          ? { ...clause, expert_notes: notes }
          : clause
      )
    );
  };

  const validateCompleteness = (): boolean => {
    // Check if all clauses are either approved or modified
    const incompleteClause = clauseReviews.find(clause => 
      !clause.approved && !clause.expert_modification
    );
    
    if (incompleteClause) {
      notificationService.error(`Please review clause: ${incompleteClause.clause_id}`);
      return false;
    }

    if (!overallSummary.trim()) {
      notificationService.error('Please provide an overall summary');
      return false;
    }

    return true;
  };

  const submitReview = async () => {
    if (!validateCompleteness()) {
      return;
    }

    try {
      setIsSubmitting(true);

      const token = localStorage.getItem('expert_token');
      if (!token) {
        navigate('/expert-portal');
        return;
      }

      // Calculate review duration
      const reviewDuration = Math.round((new Date().getTime() - reviewStartTime.getTime()) / (1000 * 60));

      // Build expert analysis
      const expertAnalysis = {
        ...reviewItem?.ai_analysis,
        summary: overallSummary,
        analysis_results: clauseReviews.map(clause => ({
          ...clause.ai_assessment,
          ...(clause.expert_modification || {}),
          expert_reviewed: true,
          expert_approved: clause.approved,
          expert_notes: clause.expert_notes
        })),
        expert_reviewed: true,
        expert_notes: expertNotes,
        review_duration_minutes: reviewDuration
      };

      // Count modified clauses
      const clausesModified = clauseReviews.filter(clause => 
        clause.expert_modification || !clause.approved
      ).length;

      const submission = {
        review_id: reviewId,
        expert_analysis: expertAnalysis,
        expert_notes: expertNotes,
        clauses_modified: clausesModified,
        complexity_rating: calculateComplexityRating(),
        review_duration_minutes: reviewDuration
      };

      const response = await fetch(`/api/expert/review/${reviewId}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submission),
      });

      if (!response.ok) {
        throw new Error('Failed to submit expert review');
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to submit expert review');
      }

      notificationService.success('Expert review submitted successfully');
      navigate('/expert-dashboard');

    } catch (error: any) {
      console.error('Failed to submit review:', error);
      notificationService.error(error.message || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  const calculateComplexityRating = (): number => {
    // Simple complexity calculation based on various factors
    let complexity = 1;
    
    if (reviewItem) {
      // Factor in confidence score (lower confidence = higher complexity)
      complexity += (1 - reviewItem.confidence_score) * 2;
      
      // Factor in number of clauses
      complexity += Math.min(clauseReviews.length / 10, 2);
      
      // Factor in modifications made
      const modificationsCount = clauseReviews.filter(c => c.expert_modification).length;
      complexity += (modificationsCount / clauseReviews.length) * 2;
    }
    
    return Math.min(Math.max(Math.round(complexity), 1), 5);
  };

  const handleCancel = () => {
    if (window.confirm('Are you sure you want to cancel this review? Your progress will be lost.')) {
      navigate('/expert-dashboard');
    }
  };

  const decodeDocumentContent = (content: string): string => {
    try {
      return atob(content);
    } catch {
      return content;
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'RED': return 'text-red-400 bg-red-900/30';
      case 'YELLOW': return 'text-yellow-400 bg-yellow-900/30';
      case 'GREEN': return 'text-green-400 bg-green-900/30';
      default: return 'text-slate-400 bg-slate-900/30';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-300">Loading Review Details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">
            <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="text-red-300 mb-4">{error}</p>
          <div className="space-x-4">
            <button
              onClick={loadReviewDetails}
              className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
            >
              Retry
            </button>
            <button
              onClick={() => navigate('/expert-dashboard')}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!reviewItem) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/expert-dashboard')}
                className="text-slate-400 hover:text-white mr-4"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-bold text-white">
                Expert Review - {reviewItem.review_id.split('_').pop()}
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-slate-300">
                Confidence: {(reviewItem.confidence_score * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-slate-300">
                User: {reviewItem.user_email}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-slate-800/50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              {[
                { key: 'document', label: 'Original Document', icon: '📄' },
                { key: 'analysis', label: 'AI Analysis', icon: '🤖' },
                { key: 'review', label: 'Expert Review', icon: '👨‍⚖️' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center space-x-2 ${
                    activeTab === tab.key
                      ? 'border-cyan-500 text-cyan-400'
                      : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
            
            {/* Quick Actions */}
            <div className="flex items-center space-x-3">
              <div className="text-sm text-slate-400">
                Review Progress: {clauseReviews.filter(c => c.approved || c.expert_modification).length}/{clauseReviews.length}
              </div>
              <div className="flex space-x-2">
                {activeTab !== 'analysis' && (
                  <button
                    onClick={() => setActiveTab('analysis')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                  >
                    View Analysis
                  </button>
                )}
                {activeTab !== 'review' && (
                  <button
                    onClick={() => setActiveTab('review')}
                    className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 text-sm font-medium"
                  >
                    Start Review
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'document' && (
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Original Document</h2>
            <div className="bg-slate-900 rounded-lg p-6 max-h-96 overflow-y-auto">
              <pre className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                {decodeDocumentContent(reviewItem.document_content)}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {/* Overall Analysis Summary */}
            <div className="bg-slate-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">AI Analysis Summary</h2>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${
                      reviewItem.confidence_score < 0.4 ? 'text-red-400' : 
                      reviewItem.confidence_score < 0.7 ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {(reviewItem.confidence_score * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-400">Overall Confidence</div>
                  </div>
                  <div className={`px-4 py-2 rounded-lg ${
                    reviewItem.ai_analysis.overall_risk?.level === 'RED' ? 'bg-red-900/30 text-red-300' :
                    reviewItem.ai_analysis.overall_risk?.level === 'YELLOW' ? 'bg-yellow-900/30 text-yellow-300' :
                    'bg-green-900/30 text-green-300'
                  }`}>
                    <div className="font-medium">
                      {reviewItem.ai_analysis.overall_risk?.level || 'UNKNOWN'} RISK
                    </div>
                    <div className="text-xs opacity-75">
                      Score: {reviewItem.ai_analysis.overall_risk?.score || 0}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-slate-900 rounded-lg p-4 mb-4">
                <p className="text-slate-300 leading-relaxed">{reviewItem.ai_analysis.summary}</p>
              </div>

              {/* Confidence Breakdown */}
              {reviewItem.confidence_breakdown && (
                <div className="bg-slate-900 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-3">Confidence Breakdown</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Component Weights:</h4>
                      <div className="space-y-1">
                        {Object.entries(reviewItem.confidence_breakdown.component_weights || {}).map(([component, weight]) => (
                          <div key={component} className="flex justify-between text-sm">
                            <span className="text-slate-300">{component.replace('_', ' ')}:</span>
                            <span className="text-slate-400">{(weight as number * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Factors Affecting Confidence:</h4>
                      <ul className="text-sm text-slate-300 space-y-1">
                        {(reviewItem.confidence_breakdown.factors_affecting_confidence || []).map((factor: string, i: number) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="text-yellow-400 mt-1">•</span>
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Clause Analysis */}
            <div className="bg-slate-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Detailed Clause Analysis</h2>
                <div className="text-sm text-slate-400">
                  {reviewItem.ai_analysis.analysis_results?.length || 0} clauses analyzed
                </div>
              </div>
              
              <div className="space-y-6">
                {reviewItem.ai_analysis.analysis_results?.map((clause: any, index: number) => (
                  <div key={index} className="bg-slate-900 rounded-lg p-6 border-l-4 border-slate-700 hover:border-cyan-500 transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-white">
                          Clause {index + 1}
                        </h3>
                        <span className="text-sm text-slate-500">
                          ID: {clause.clause_id}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="text-right text-sm">
                          <div className={`font-medium ${
                            (clause.risk_level?.confidence_percentage || 0) < 40 ? 'text-red-400' : 
                            (clause.risk_level?.confidence_percentage || 0) < 70 ? 'text-yellow-400' : 'text-green-400'
                          }`}>
                            {clause.risk_level?.confidence_percentage || 0}%
                          </div>
                          <div className="text-slate-400">Confidence</div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(clause.risk_level?.level)}`}>
                          {clause.risk_level?.level || 'UNKNOWN'} RISK
                        </span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Left Column - Clause Content */}
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Original Clause Text:
                          </h4>
                          <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
                            <p className="text-slate-300 text-sm leading-relaxed">{clause.clause_text}</p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Plain Language Explanation:
                          </h4>
                          <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
                            <p className="text-slate-300 text-sm leading-relaxed">{clause.plain_explanation}</p>
                          </div>
                        </div>
                      </div>

                      {/* Right Column - Analysis Details */}
                      <div className="space-y-4">
                        {clause.legal_implications && clause.legal_implications.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                              </svg>
                              Legal Implications:
                            </h4>
                            <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
                              <ul className="text-slate-300 text-sm space-y-2">
                                {clause.legal_implications.map((implication: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <span className="text-red-400 mt-1 flex-shrink-0">⚠</span>
                                    <span>{implication}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}
                        
                        {clause.recommendations && clause.recommendations.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                              </svg>
                              Recommendations:
                            </h4>
                            <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
                              <ul className="text-slate-300 text-sm space-y-2">
                                {clause.recommendations.map((recommendation: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <span className="text-green-400 mt-1 flex-shrink-0">✓</span>
                                    <span>{recommendation}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}

                        {/* Risk Details */}
                        {clause.risk_level && (
                          <div>
                            <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                              Risk Assessment:
                            </h4>
                            <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                <div>
                                  <span className="text-slate-400">Risk Score:</span>
                                  <div className="text-white font-medium">{clause.risk_level.score || 0}</div>
                                </div>
                                <div>
                                  <span className="text-slate-400">Severity:</span>
                                  <div className="text-white font-medium">{clause.risk_level.severity || 'N/A'}</div>
                                </div>
                              </div>
                              {clause.risk_level.reasons && clause.risk_level.reasons.length > 0 && (
                                <div className="mt-3">
                                  <span className="text-slate-400 text-xs">Risk Factors:</span>
                                  <ul className="mt-1 space-y-1">
                                    {clause.risk_level.reasons.map((reason: string, i: number) => (
                                      <li key={i} className="text-slate-300 text-xs flex items-start space-x-1">
                                        <span className="text-orange-400">•</span>
                                        <span>{reason}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'review' && (
          <div className="space-y-6">
            {/* Overall Summary */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Expert Summary</h2>
              <textarea
                value={overallSummary}
                onChange={(e) => setOverallSummary(e.target.value)}
                className="w-full h-32 bg-slate-900 border border-slate-600 rounded-lg p-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
                placeholder="Provide your expert summary of the document analysis..."
              />
            </div>

            {/* Clause Reviews */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Clause Review</h2>
              <div className="space-y-6">
                {clauseReviews.map((clause, index) => (
                  <div key={clause.clause_id} className="bg-slate-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-white">
                        Clause {index + 1}
                      </h3>
                      <div className="flex items-center space-x-4">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={clause.approved}
                            onChange={(e) => handleClauseApproval(clause.clause_id, e.target.checked)}
                            className="mr-2 rounded border-slate-600 bg-slate-700 text-cyan-500 focus:ring-cyan-500"
                          />
                          <span className="text-sm text-slate-300">Approve AI Analysis</span>
                        </label>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* AI Analysis */}
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-slate-400">AI Analysis</h4>
                        <div className="bg-slate-800 rounded p-3 text-sm">
                          <p className="text-slate-300 mb-2">{clause.ai_assessment.plain_explanation}</p>
                          <div className={`inline-block px-2 py-1 rounded text-xs ${getRiskLevelColor(clause.ai_assessment.risk_level?.level)}`}>
                            {clause.ai_assessment.risk_level?.level} Risk
                          </div>
                        </div>
                      </div>

                      {/* Expert Modification */}
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-slate-400">Expert Modification</h4>
                        
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Explanation</label>
                          <textarea
                            value={clause.expert_modification?.plain_explanation || clause.ai_assessment.plain_explanation}
                            onChange={(e) => handleClauseModification(clause.clause_id, 'plain_explanation', e.target.value)}
                            className="w-full h-20 bg-slate-800 border border-slate-600 rounded p-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
                            disabled={clause.approved}
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Risk Level</label>
                          <select
                            value={clause.expert_modification?.risk_level?.level || clause.ai_assessment.risk_level?.level}
                            onChange={(e) => handleClauseModification(clause.clause_id, 'risk_level', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-600 rounded p-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
                            disabled={clause.approved}
                          >
                            <option value="GREEN">GREEN - Low Risk</option>
                            <option value="YELLOW">YELLOW - Medium Risk</option>
                            <option value="RED">RED - High Risk</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Expert Notes</label>
                          <textarea
                            value={clause.expert_notes || ''}
                            onChange={(e) => handleClauseNotes(clause.clause_id, e.target.value)}
                            className="w-full h-16 bg-slate-800 border border-slate-600 rounded p-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
                            placeholder="Add your expert notes..."
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Expert Notes */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Overall Expert Notes</h2>
              <textarea
                value={expertNotes}
                onChange={(e) => setExpertNotes(e.target.value)}
                className="w-full h-24 bg-slate-900 border border-slate-600 rounded-lg p-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
                placeholder="Add any additional notes about this review..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <button
                onClick={handleCancel}
                className="px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
              >
                Cancel Review
              </button>
              
              <button
                onClick={submitReview}
                disabled={isSubmitting}
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <div className="flex items-center">
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    Submitting...
                  </div>
                ) : (
                  'Submit Expert Review'
                )}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Floating Action Menu */}
      <div className="fixed bottom-6 right-6 flex flex-col space-y-3">
        {activeTab !== 'review' && (
          <button
            onClick={() => setActiveTab('review')}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white p-4 rounded-full shadow-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 group"
            title="Start Expert Review"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}
        
        {activeTab === 'review' && (
          <button
            onClick={submitReview}
            disabled={isSubmitting || !validateCompleteness()}
            className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-full shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Submit Expert Review"
          >
            {isSubmitting ? (
              <div className="animate-spin w-6 h-6 border-2 border-white border-t-transparent rounded-full"></div>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>
        )}
        
        <button
          onClick={() => navigate('/expert-dashboard')}
          className="bg-slate-600 hover:bg-slate-700 text-white p-3 rounded-full shadow-lg transition-colors"
          title="Back to Dashboard"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default DocumentReviewInterface;