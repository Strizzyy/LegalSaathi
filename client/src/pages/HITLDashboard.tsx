/**
 * HITL (Human-in-the-Loop) Dashboard - Expert Review Queue Management
 * Dedicated interface for managing low-confidence document reviews
 */

import React, { useState, useEffect } from 'react';
import { ArrowLeft, Users, Clock, CheckCircle, Activity, Brain, FileText, AlertTriangle, RefreshCw, Eye, UserPlus } from 'lucide-react';
import { expertQueueService, ExpertReviewRequest } from '../services/expertQueueService';
import { HITLReviewPreviewModal } from '../components/HITLReviewPreviewModal';
import { notificationService } from '../services/notificationService';

const HITLDashboard: React.FC = () => {
  const [queueStats, setQueueStats] = useState({
    total_items: 0,
    pending_items: 0,
    in_review_items: 0,
    completed_items: 0,
    cancelled_items: 0,
    average_completion_time_hours: 0,
    expert_workload: {}
  });
  const [queueItems, setQueueItems] = useState<ExpertReviewRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedReviewId, setSelectedReviewId] = useState<string>('');
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningReviewId, setAssigningReviewId] = useState<string>('');
  const [expertId, setExpertId] = useState<string>('');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [optimisticUpdates, setOptimisticUpdates] = useState<Map<string, { status: string; expertId: string; timestamp: number }>>(new Map());
  const [assigningItems, setAssigningItems] = useState<Set<string>>(new Set());

  const handleBackToApp = () => {
    // Navigate back to the main application
    window.history.pushState({}, '', '/');
    window.location.reload();
  };

  const fetchQueueData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch queue statistics
      const stats = await expertQueueService.getQueueStats();
      setQueueStats(stats);
      
      // Fetch queue items (pending reviews only)
      const queueResponse = await expertQueueService.getExpertRequests('pending', undefined, 1, 20);
      
      // Apply optimistic updates to the fetched items
      const itemsWithOptimisticUpdates = (queueResponse.items || []).map(item => {
        const optimisticUpdate = optimisticUpdates.get(item.review_id);
        if (optimisticUpdate) {
          return {
            ...item,
            status: optimisticUpdate.status as any,
            assigned_expert_id: optimisticUpdate.expertId,
            assigned_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          };
        }
        return item;
      });
      
      setQueueItems(itemsWithOptimisticUpdates);
      
    } catch (err) {
      console.error('Failed to fetch queue data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to load queue data: ${errorMessage}`);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => {
    fetchQueueData();
    
    // Set up auto-refresh every 30 seconds
    const refreshInterval = setInterval(() => {
      // Only auto-refresh if there are no pending optimistic updates
      if (optimisticUpdates.size === 0 && assigningItems.size === 0) {
        fetchQueueData();
      }
    }, 30000);
    
    // Set up cleanup of old optimistic updates every 10 seconds
    const cleanupInterval = setInterval(() => {
      cleanupOldOptimisticUpdates();
    }, 10000);
    
    return () => {
      clearInterval(refreshInterval);
      clearInterval(cleanupInterval);
    };
  }, [optimisticUpdates, assigningItems]);

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Optimistic update management
  const applyOptimisticUpdate = (reviewId: string, status: string, expertId: string) => {
    setOptimisticUpdates(prev => new Map(prev.set(reviewId, {
      status,
      expertId,
      timestamp: Date.now()
    })));
    
    // Update the queue item status immediately for better UX
    setQueueItems(prev => prev.map(item => 
      item.review_id === reviewId 
        ? { 
            ...item, 
            status: status as any, 
            assigned_expert_id: expertId,
            assigned_at: new Date().toISOString(), // Update assignment time
            updated_at: new Date().toISOString()   // Update last modified time
          }
        : item
    ));
  };

  const rollbackOptimisticUpdate = (reviewId: string) => {
    setOptimisticUpdates(prev => {
      const newMap = new Map(prev);
      newMap.delete(reviewId);
      return newMap;
    });
    
    // Restore the item to pending status
    setQueueItems(prev => prev.map(item => 
      item.review_id === reviewId 
        ? { ...item, status: 'pending', assigned_expert_id: undefined }
        : item
    ));
    
    // Also refresh queue data to restore accurate state
    fetchQueueData();
  };

  const clearOptimisticUpdate = (reviewId: string) => {
    setOptimisticUpdates(prev => {
      const newMap = new Map(prev);
      newMap.delete(reviewId);
      return newMap;
    });
  };

  // Clean up old optimistic updates (older than 60 seconds)
  const cleanupOldOptimisticUpdates = () => {
    const now = Date.now();
    setOptimisticUpdates(prev => {
      const newMap = new Map();
      for (const [reviewId, update] of prev.entries()) {
        if (now - update.timestamp < 60000) { // Keep updates less than 60 seconds old
          newMap.set(reviewId, update);
        }
      }
      return newMap;
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-900/50 text-red-400 border-red-700';
      case 'high': return 'bg-orange-900/50 text-orange-400 border-orange-700';
      case 'medium': return 'bg-yellow-900/50 text-yellow-400 border-yellow-700';
      case 'low': return 'bg-green-900/50 text-green-400 border-green-700';
      default: return 'bg-gray-900/50 text-gray-400 border-gray-700';
    }
  };

  const handleViewDetails = (reviewId: string) => {
    setSelectedReviewId(reviewId);
    setShowPreviewModal(true);
  };

  const handleClosePreview = () => {
    setShowPreviewModal(false);
    setSelectedReviewId('');
  };

  const handleAssignToExpert = (reviewId: string) => {
    setAssigningReviewId(reviewId);
    setShowAssignModal(true);
  };

  const handleCloseAssignModal = () => {
    setShowAssignModal(false);
    setAssigningReviewId('');
    setExpertId('');
  };

  const handleConfirmAssignment = async () => {
    if (!expertId.trim()) {
      notificationService.error('Please enter an expert ID');
      return;
    }

    try {
      // First check if the review is still available for assignment
      const currentReview = queueItems.find(item => item.review_id === assigningReviewId);
      if (!currentReview) {
        notificationService.error('Review not found in current queue');
        handleCloseAssignModal();
        await fetchQueueData();
        return;
      }

      if (currentReview.status !== 'pending') {
        notificationService.error(`Review is already ${currentReview.status.replace('_', ' ')}`);
        handleCloseAssignModal();
        await fetchQueueData();
        return;
      }

      // Add to assigning items set to show loading state
      setAssigningItems(prev => new Set(prev.add(assigningReviewId)));
      
      // Apply optimistic update immediately
      applyOptimisticUpdate(assigningReviewId, 'in_review', expertId);
      
      // Close modal immediately to show responsive UI
      handleCloseAssignModal();
      
      // Show immediate success feedback
      notificationService.success(`Assigning review to expert ${expertId}...`);
      
      // Force a re-render to ensure the status change is visible
      setLastRefresh(new Date());

      // Make the API call
      await expertQueueService.assignToExpert(assigningReviewId, expertId);
      
      // Remove from assigning set
      setAssigningItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(assigningReviewId);
        return newSet;
      });
      
      // Show final success message
      notificationService.success(`Review assigned to expert ${expertId} successfully`);
      
      // Keep the optimistic update for longer to ensure it's visible
      setTimeout(() => {
        // Don't clear the optimistic update immediately, let it persist
      }, 1000);
      
      // Refresh the queue data to sync with server after a longer delay
      setTimeout(() => {
        fetchQueueData();
      }, 5000);
    } catch (error: any) {
      console.error('Failed to assign to expert:', error);
      
      // Rollback optimistic update
      rollbackOptimisticUpdate(assigningReviewId);
      
      // Remove from assigning set
      setAssigningItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(assigningReviewId);
        return newSet;
      });
      
      let errorMessage = 'Failed to assign review to expert';
      
      if (error.message.includes('Review not found or not available')) {
        errorMessage = 'Review is no longer available for assignment (may have been assigned to another expert)';
      } else if (error.message.includes('Authentication required')) {
        errorMessage = 'Authentication required. Please refresh the page and try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      notificationService.error(errorMessage);
    }
  };

  const handleAssignFromPreview = async (reviewId: string) => {
    setShowPreviewModal(false);
    handleAssignToExpert(reviewId);
  };

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
                <h1 className="text-2xl font-bold text-white flex items-center">
                  <Brain className="w-6 h-6 mr-2 text-blue-400" />
                  HITL Dashboard
                </h1>
                <p className="text-sm text-slate-400">Human-in-the-Loop Expert Review System</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-slate-400">Demo Mode</p>
                <p className="text-xs text-blue-400">Expert Queue Management</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Demo Banner */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 border border-blue-500 mb-8">
          <div className="flex items-center">
            <Brain className="w-8 h-8 text-white mr-4" />
            <div>
              <h2 className="text-xl font-bold text-white">Human-in-the-Loop Expert Review System</h2>
              <p className="text-blue-100 mt-1">
                This dashboard demonstrates how legal experts would manage and review low-confidence AI document analyses in a production environment.
              </p>
            </div>
          </div>
        </div>

        {/* Queue Statistics */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-white">Queue Statistics</h2>
            <p className="text-sm text-slate-400">
              Auto-refreshes every 30 seconds • Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={fetchQueueData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors flex items-center disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Now
          </button>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="flex items-center">
              <div className="p-2 bg-blue-900/50 rounded-lg">
                <FileText className="w-6 h-6 text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-400">Total Requests</p>
                <p className="text-2xl font-bold text-white">{loading ? '...' : queueStats.total_items}</p>
                <p className="text-xs text-slate-500 mt-1">All time</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-900/50 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-400">Pending Review</p>
                <p className="text-2xl font-bold text-white">{loading ? '...' : queueStats.pending_items}</p>
                <p className="text-xs text-slate-500 mt-1">Awaiting expert</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="flex items-center">
              <div className="p-2 bg-orange-900/50 rounded-lg">
                <Activity className="w-6 h-6 text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-400">In Progress</p>
                <p className="text-2xl font-bold text-white">{loading ? '...' : queueStats.in_review_items}</p>
                <p className="text-xs text-slate-500 mt-1">Being reviewed</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="flex items-center">
              <div className="p-2 bg-emerald-900/50 rounded-lg">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-400">Completed</p>
                <p className="text-2xl font-bold text-white">{loading ? '...' : queueStats.completed_items}</p>
                <p className="text-xs text-slate-500 mt-1">Expert reviewed</p>
              </div>
            </div>
          </div>
        </div>

        {/* Expert Review Queue */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 mb-8">
          <div className="px-6 py-4 border-b border-slate-700">
            <h3 className="text-lg font-medium text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-blue-400" />
              Expert Review Queue ({queueItems.length} pending)
            </h3>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-4" />
                <p className="text-slate-400">Loading queue items...</p>
              </div>
            ) : queueItems.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No pending reviews in the queue</p>
                <p className="text-sm text-slate-500 mt-2">New low-confidence documents will appear here for expert review</p>
              </div>
            ) : (
              <div className="space-y-4">
                {queueItems.map((item) => {
                  const optimisticUpdate = optimisticUpdates.get(item.review_id);
                  const isAssigning = assigningItems.has(item.review_id);
                  const displayStatus = optimisticUpdate ? optimisticUpdate.status : item.status;
                  const displayExpertId = optimisticUpdate ? optimisticUpdate.expertId : item.assigned_expert_id;
                  
                  return (
                    <div key={item.review_id} className={`bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded-lg p-6 border border-slate-600 ${isAssigning ? 'opacity-75' : ''}`}>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                          <div className={`w-3 h-3 rounded-full ${
                            displayStatus === 'in_review' ? 'bg-orange-400' : 
                            displayStatus === 'completed' ? 'bg-emerald-400' : 
                            'bg-yellow-400 animate-pulse'
                          }`}></div>
                          <div>
                            <h4 className="font-semibold text-white text-lg">Document Analysis Review</h4>
                            <p className="text-sm text-slate-400">Review ID: {item.review_id}</p>
                            {isAssigning && (
                              <p className="text-xs text-blue-400 animate-pulse">Assigning to expert...</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full border ${
                            displayStatus === 'in_review' ? 'bg-orange-900/50 text-orange-400 border-orange-700' :
                            displayStatus === 'completed' ? 'bg-emerald-900/50 text-emerald-400 border-emerald-700' :
                            'bg-yellow-900/50 text-yellow-400 border-yellow-700'
                          } ${optimisticUpdate ? 'animate-pulse' : ''}`}>
                            {displayStatus.replace('_', ' ').toUpperCase()}
                            {optimisticUpdate && <span className="ml-1 text-xs opacity-75">⟳</span>}
                          </span>
                          <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getPriorityColor(item.priority)}`}>
                            {item.priority.toUpperCase()} Priority
                          </span>
                        </div>
                      </div>
                    
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <AlertTriangle className="w-4 h-4 text-red-400 mr-2" />
                          <span className="text-sm font-medium text-slate-300">Confidence Score</span>
                        </div>
                        <p className="text-xl font-bold text-red-400">{Math.round(item.confidence_score * 100)}%</p>
                        <p className="text-xs text-slate-500">Requires expert review</p>
                      </div>
                      
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <FileText className="w-4 h-4 text-blue-400 mr-2" />
                          <span className="text-sm font-medium text-slate-300">Document Type</span>
                        </div>
                        <p className="text-lg font-semibold text-white break-words">{item.document_type || 'General Contract'}</p>
                        <p className="text-xs text-slate-500">Legal document</p>
                      </div>
                      
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <Clock className="w-4 h-4 text-yellow-400 mr-2" />
                          <span className="text-sm font-medium text-slate-300">
                            {displayStatus === 'in_review' ? 'Assigned' : 
                             displayStatus === 'completed' ? 'Completed' : 'Submitted'}
                          </span>
                        </div>
                        <p className="text-lg font-semibold text-white">
                          {displayStatus === 'in_review' && item.assigned_at ? 
                            formatTimeAgo(item.assigned_at) :
                           displayStatus === 'completed' && item.completed_at ?
                            formatTimeAgo(item.completed_at) :
                            formatTimeAgo(item.created_at)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {displayStatus === 'in_review' ? 'Time since assignment' :
                           displayStatus === 'completed' ? 'Time since completion' : 'Time in queue'}
                        </p>
                      </div>
                      
                      <div className="bg-slate-800/50 rounded-lg p-4 email-container">
                        <div className="flex items-center mb-2">
                          <Users className="w-4 h-4 text-emerald-400 mr-2 flex-shrink-0" />
                          <span className="text-sm font-medium text-slate-300">User Email</span>
                        </div>
                        <div className="relative group min-w-0">
                          <p className="text-sm font-semibold text-white email-text" 
                             title={item.user_email}>
                            {item.user_email}
                          </p>
                          {/* Tooltip for full email on hover - positioned to avoid overflow */}
                          <div className="email-tooltip bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                            {item.user_email}
                            <div className="email-tooltip-arrow top-full left-1/2 transform -translate-x-1/2"></div>
                          </div>
                        </div>
                        <p className="text-xs text-slate-500">Requesting user</p>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-slate-400">
                        <p>Estimated completion: {item.estimated_completion_hours} hours</p>
                      </div>
                      <div className="flex space-x-3">
                        <button 
                          onClick={() => handleViewDetails(item.review_id)}
                          className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors text-sm flex items-center space-x-2"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View Details</span>
                        </button>
                        {displayStatus === 'pending' && !isAssigning ? (
                          <button 
                            onClick={() => handleAssignToExpert(item.review_id)}
                            className="px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg transition-colors text-sm flex items-center space-x-2"
                          >
                            <UserPlus className="w-4 h-4" />
                            <span>Assign to Expert</span>
                          </button>
                        ) : isAssigning ? (
                          <div className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm flex items-center space-x-2">
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span className="text-xs">Assigning...</span>
                          </div>
                        ) : (
                          <div className="px-4 py-2 bg-slate-600 text-slate-300 rounded-lg text-sm flex items-center space-x-2">
                            <span className="text-xs">
                              {displayStatus === 'in_review' ? 'In Review' : 
                               displayStatus === 'completed' ? 'Completed' : 
                               displayStatus.replace('_', ' ').toUpperCase()}
                            </span>
                            {displayExpertId && (
                              <span className="text-xs text-slate-400">
                                ({displayExpertId})
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* System Information */}
        <div className="bg-slate-800 rounded-lg border border-slate-700">
          <div className="px-6 py-4 border-b border-slate-700">
            <h3 className="text-lg font-medium text-white">HITL System Information</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-medium text-white mb-2">How It Works</h4>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• AI analyzes documents and calculates confidence</li>
                  <li>• Low confidence triggers expert review queue</li>
                  <li>• Human experts provide detailed analysis</li>
                  <li>• Results sent to users via email</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-white mb-2">Confidence Thresholds</h4>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• <span className="text-red-400">High Priority:</span> &lt; 40% confidence</li>
                  <li>• <span className="text-yellow-400">Medium Priority:</span> 40-60% confidence</li>
                  <li>• <span className="text-green-400">Auto-Process:</span> &gt; 60% confidence</li>
                  <li>• Current threshold: 99% (demo mode)</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-white mb-2">Expert Capabilities</h4>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• Multi-jurisdictional law expertise</li>
                  <li>• Contract enforceability analysis</li>
                  <li>• Risk assessment validation</li>
                  <li>• Detailed recommendation generation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Review Preview Modal */}
      <HITLReviewPreviewModal
        isOpen={showPreviewModal}
        onClose={handleClosePreview}
        reviewId={selectedReviewId}
        onAssign={handleAssignFromPreview}
      />

      {/* Assign to Expert Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-lg max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-xl font-bold text-white">Assign to Expert</h2>
              <button
                onClick={handleCloseAssignModal}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              <div className="mb-4">
                <p className="text-slate-300 mb-2">
                  Review ID: <span className="font-mono text-cyan-400">{assigningReviewId}</span>
                </p>
                <p className="text-sm text-slate-400">
                  Enter the expert's Firebase UID to assign this review.
                </p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Expert ID (Firebase UID)
                </label>
                <input
                  type="text"
                  value={expertId}
                  onChange={(e) => setExpertId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  placeholder="Enter expert Firebase UID"
                />
              </div>

              <div className="bg-slate-900 rounded-lg p-4 mb-6">
                <h4 className="text-sm font-medium text-slate-300 mb-2">Demo Expert IDs:</h4>
                <div className="space-y-1 text-sm">
                  <button
                    onClick={() => setExpertId('expert_001')}
                    className="block text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    expert_001 - Senior Legal Expert
                  </button>
                  <button
                    onClick={() => setExpertId('expert_002')}
                    className="block text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    expert_002 - Contract Specialist
                  </button>
                  <button
                    onClick={() => setExpertId('admin_001')}
                    className="block text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    admin_001 - Admin Expert
                  </button>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={handleCloseAssignModal}
                  className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmAssignment}
                  disabled={!expertId.trim()}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Assign Review
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HITLDashboard;