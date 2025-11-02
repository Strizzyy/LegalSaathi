/**
 * Expert Dashboard Component
 * Main dashboard for expert users showing queue of pending reviews
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signOut } from 'firebase/auth';
import { auth } from '../firebaseConfig';
import { notificationService } from '../services/notificationService';
import { ReviewPreviewModal } from '../components/ReviewPreviewModal';

interface ExpertInfo {
  uid: string;
  email: string;
  display_name?: string;
  role: string;
  permissions: string[];
  specializations: string[];
  reviews_completed: number;
  average_review_time: number;
}

interface QueueItem {
  review_id: string;
  user_email: string;
  confidence_score: number;
  status: string;
  priority: string;
  created_at: string;
  estimated_completion_hours: number;
  document_type?: string;
}

interface QueueStats {
  total_items: number;
  pending_items: number;
  in_review_items: number;
  completed_items: number;
  average_completion_time_hours: number;
  oldest_pending_item?: string;
}

export const ExpertDashboard: React.FC = () => {
  const [expertInfo, setExpertInfo] = useState<ExpertInfo | null>(null);
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentView, setCurrentView] = useState<'queue' | 'stats' | 'profile'>('queue');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedReviewId, setSelectedReviewId] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    loadExpertData();
  }, []);

  const loadExpertData = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Check if expert is logged in
      const storedExpertInfo = localStorage.getItem('expert_info');
      const storedToken = localStorage.getItem('expert_token');

      if (!storedExpertInfo || !storedToken) {
        navigate('/expert-portal');
        return;
      }

      const expert = JSON.parse(storedExpertInfo);
      setExpertInfo(expert);

      // Load queue data and stats
      await Promise.all([
        loadQueueItems(),
        loadQueueStats()
      ]);

    } catch (error: any) {
      console.error('Failed to load expert data:', error);
      setError('Failed to load dashboard data');
      notificationService.error('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadQueueItems = async () => {
    try {
      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch('/api/expert/queue/list?limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load queue items');
      }

      const result = await response.json();
      if (result.success && result.queue) {
        setQueueItems(result.queue.items || []);
      }

    } catch (error: any) {
      console.error('Failed to load queue items:', error);
    }
  };

  const loadQueueStats = async () => {
    try {
      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch('/api/expert/queue/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load queue stats');
      }

      const result = await response.json();
      if (result.success && result.stats) {
        setQueueStats(result.stats);
      }

    } catch (error: any) {
      console.error('Failed to load queue stats:', error);
    }
  };

  const handleGetNextReview = async () => {
    try {
      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch('/api/expert/queue/next', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get next review');
      }

      const result = await response.json();
      
      if (result.success && result.review) {
        // Navigate to review interface
        navigate(`/expert-review/${result.review.review_id}`);
      } else {
        notificationService.info(result.message || 'No pending reviews available');
      }

    } catch (error: any) {
      console.error('Failed to get next review:', error);
      notificationService.error('Failed to get next review');
    }
  };

  const handleViewReview = (reviewId: string) => {
    navigate(`/expert-review/${reviewId}`);
  };

  const handleShowPreview = (reviewId: string) => {
    setSelectedReviewId(reviewId);
    setShowPreviewModal(true);
  };

  const handleClosePreview = () => {
    setShowPreviewModal(false);
    setSelectedReviewId('');
  };

  const handleAssignFromPreview = async (reviewId: string) => {
    setShowPreviewModal(false);
    await handleAssignToMe(reviewId);
  };

  const handleViewFullFromPreview = (reviewId: string) => {
    setShowPreviewModal(false);
    navigate(`/expert-review/${reviewId}`);
  };

  const handleAssignToMe = async (reviewId: string) => {
    try {
      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch(`/api/expert/review/${reviewId}/assign`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to assign review');
      }

      const result = await response.json();
      
      if (result.success) {
        notificationService.success('Review assigned successfully');
        // Navigate directly to the review interface
        navigate(`/expert-review/${reviewId}`);
      } else {
        throw new Error(result.message || 'Failed to assign review');
      }

    } catch (error: any) {
      console.error('Failed to assign review:', error);
      notificationService.error(error.message || 'Failed to assign review');
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      localStorage.removeItem('expert_info');
      localStorage.removeItem('expert_token');
      navigate('/expert-portal');
      notificationService.success('Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
      notificationService.error('Logout failed');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'text-blue-400 bg-blue-900/30';
      case 'in_review': return 'text-yellow-400 bg-yellow-900/30';
      case 'completed': return 'text-green-400 bg-green-900/30';
      case 'cancelled': return 'text-red-400 bg-red-900/30';
      default: return 'text-slate-400 bg-slate-900/30';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-300">Loading Expert Dashboard...</p>
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
          <button
            onClick={loadExpertData}
            className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-white">Expert Dashboard</h1>
              {expertInfo && (
                <div className="ml-4 text-sm text-slate-400">
                  Welcome, {expertInfo.display_name || expertInfo.email}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              {expertInfo && (
                <div className="text-sm text-slate-300">
                  <span className="px-2 py-1 bg-cyan-900/50 text-cyan-300 rounded-full text-xs">
                    {expertInfo.role.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              )}
              
              <button
                onClick={handleLogout}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-slate-800/50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['queue', 'stats', 'profile'].map((view) => (
              <button
                key={view}
                onClick={() => setCurrentView(view as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  currentView === view
                    ? 'border-cyan-500 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                }`}
              >
                {view.charAt(0).toUpperCase() + view.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'queue' && (
          <div className="space-y-6">
            {/* Queue Actions */}
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Review Queue</h2>
              <button
                onClick={handleGetNextReview}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 font-medium"
              >
                Get Next Review
              </button>
            </div>

            {/* Queue Stats Summary */}
            {queueStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-400">{queueStats.pending_items}</div>
                  <div className="text-sm text-slate-400">Pending Reviews</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-yellow-400">{queueStats.in_review_items}</div>
                  <div className="text-sm text-slate-400">In Review</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-400">{queueStats.completed_items}</div>
                  <div className="text-sm text-slate-400">Completed</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-cyan-400">
                    {queueStats.average_completion_time_hours.toFixed(1)}h
                  </div>
                  <div className="text-sm text-slate-400">Avg. Time</div>
                </div>
              </div>
            )}

            {/* Queue Items */}
            <div className="bg-slate-800 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-medium text-white">Pending Reviews</h3>
              </div>
              
              {queueItems.length === 0 ? (
                <div className="p-8 text-center">
                  <div className="text-slate-400 mb-2">
                    <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-slate-400">No pending reviews available</p>
                  <p className="text-sm text-slate-500 mt-1">Check back later for new documents to review</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-700">
                  {queueItems.map((item) => (
                    <div key={item.review_id} className="p-6 hover:bg-slate-700/50 transition-colors border-l-4 border-transparent hover:border-cyan-500">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-3">
                            <span className="text-white font-medium text-lg">
                              Review #{item.review_id.split('_').pop()}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
                              {item.priority.toUpperCase()} PRIORITY
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                              {item.status.replace('_', ' ').toUpperCase()}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                            <div>
                              <span className="text-slate-500">User:</span>
                              <div className="text-slate-300 font-medium">{item.user_email}</div>
                            </div>
                            <div>
                              <span className="text-slate-500">Confidence:</span>
                              <div className={`font-medium ${
                                item.confidence_score < 0.4 ? 'text-red-400' : 
                                item.confidence_score < 0.7 ? 'text-yellow-400' : 'text-green-400'
                              }`}>
                                {(item.confidence_score * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div>
                              <span className="text-slate-500">Submitted:</span>
                              <div className="text-slate-300">{formatDate(item.created_at)}</div>
                            </div>
                            <div>
                              <span className="text-slate-500">Est. Time:</span>
                              <div className="text-slate-300 font-medium">{item.estimated_completion_hours}h</div>
                            </div>
                          </div>

                          {item.document_type && (
                            <div className="mb-3">
                              <span className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs">
                                📄 {item.document_type}
                              </span>
                            </div>
                          )}

                          {/* Confidence Warning */}
                          {item.confidence_score < 0.5 && (
                            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 mb-3">
                              <div className="flex items-center space-x-2">
                                <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                <span className="text-yellow-300 text-sm font-medium">
                                  Low Confidence - Expert Review Recommended
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex flex-col space-y-2 ml-4">
                          <div className="text-center">
                            <div className={`text-2xl font-bold ${
                              item.confidence_score < 0.4 ? 'text-red-400' : 
                              item.confidence_score < 0.7 ? 'text-yellow-400' : 'text-green-400'
                            }`}>
                              {(item.confidence_score * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-slate-400">Confidence</div>
                          </div>
                          
                          <div className="flex flex-col space-y-2">
                            <button
                              onClick={() => handleShowPreview(item.review_id)}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium flex items-center space-x-2"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              <span>Quick Preview</span>
                            </button>
                            
                            {item.status === 'pending' && (
                              <button
                                onClick={() => handleAssignToMe(item.review_id)}
                                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium flex items-center space-x-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                </svg>
                                <span>Assign to Me</span>
                              </button>
                            )}
                            
                            {item.status === 'in_review' && (
                              <button
                                onClick={() => handleViewReview(item.review_id)}
                                className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium flex items-center space-x-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span>Continue Review</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {currentView === 'stats' && queueStats && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Queue Statistics</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-slate-800 rounded-lg p-6">
                <h3 className="text-lg font-medium text-white mb-4">Queue Overview</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Items:</span>
                    <span className="text-white font-medium">{queueStats.total_items}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Pending:</span>
                    <span className="text-blue-400 font-medium">{queueStats.pending_items}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">In Review:</span>
                    <span className="text-yellow-400 font-medium">{queueStats.in_review_items}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Completed:</span>
                    <span className="text-green-400 font-medium">{queueStats.completed_items}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 rounded-lg p-6">
                <h3 className="text-lg font-medium text-white mb-4">Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Avg. Completion:</span>
                    <span className="text-cyan-400 font-medium">
                      {queueStats.average_completion_time_hours.toFixed(1)}h
                    </span>
                  </div>
                  {queueStats.oldest_pending_item && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Oldest Pending:</span>
                      <span className="text-orange-400 font-medium">
                        {formatDate(queueStats.oldest_pending_item)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {expertInfo && (
                <div className="bg-slate-800 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-white mb-4">Your Stats</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Reviews Completed:</span>
                      <span className="text-green-400 font-medium">{expertInfo.reviews_completed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Avg. Review Time:</span>
                      <span className="text-cyan-400 font-medium">
                        {(expertInfo.average_review_time / 60).toFixed(1)}h
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentView === 'profile' && expertInfo && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Expert Profile</h2>
            
            <div className="bg-slate-800 rounded-lg p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Personal Information</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-slate-400">Email</label>
                      <div className="text-white">{expertInfo.email}</div>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Display Name</label>
                      <div className="text-white">{expertInfo.display_name || 'Not set'}</div>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Role</label>
                      <div className="text-white">
                        <span className="px-2 py-1 bg-cyan-900/50 text-cyan-300 rounded-full text-sm">
                          {expertInfo.role.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Specializations & Stats</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-slate-400">Specializations</label>
                      <div className="text-white">
                        {expertInfo.specializations.length > 0 ? (
                          <div className="flex flex-wrap gap-2 mt-1">
                            {expertInfo.specializations.map((spec, index) => (
                              <span key={index} className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-sm">
                                {spec}
                              </span>
                            ))}
                          </div>
                        ) : (
                          'None specified'
                        )}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Reviews Completed</label>
                      <div className="text-white text-xl font-bold">{expertInfo.reviews_completed}</div>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Average Review Time</label>
                      <div className="text-white text-xl font-bold">
                        {(expertInfo.average_review_time / 60).toFixed(1)}h
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-700">
                <h3 className="text-lg font-medium text-white mb-4">Permissions</h3>
                <div className="flex flex-wrap gap-2">
                  {expertInfo.permissions.map((permission, index) => (
                    <span key={index} className="px-3 py-1 bg-green-900/30 text-green-300 rounded-full text-sm">
                      {permission.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Review Preview Modal */}
      <ReviewPreviewModal
        isOpen={showPreviewModal}
        onClose={handleClosePreview}
        reviewId={selectedReviewId}
        onAssign={handleAssignFromPreview}
        onViewFull={handleViewFullFromPreview}
      />
    </div>
  );
};

export default ExpertDashboard;