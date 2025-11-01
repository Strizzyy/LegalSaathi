/**
 * HITL (Human-in-the-Loop) Dashboard - Expert Review Queue Management
 * Dedicated interface for managing low-confidence document reviews
 */

import React from 'react';
import { ArrowLeft, Users, Clock, CheckCircle, Activity, Brain, FileText, AlertTriangle } from 'lucide-react';

const HITLDashboard: React.FC = () => {
  const handleBackToApp = () => {
    // Navigate back to the main application
    window.history.pushState({}, '', '/');
    window.location.reload();
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="flex items-center">
              <div className="p-2 bg-blue-900/50 rounded-lg">
                <FileText className="w-6 h-6 text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-400">Total Requests</p>
                <p className="text-2xl font-bold text-white">1</p>
                <p className="text-xs text-slate-500 mt-1">This session</p>
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
                <p className="text-2xl font-bold text-white">1</p>
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
                <p className="text-2xl font-bold text-white">0</p>
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
                <p className="text-2xl font-bold text-white">0</p>
                <p className="text-xs text-slate-500 mt-1">Expert reviewed</p>
              </div>
            </div>
          </div>
        </div>

        {/* Current Request */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 mb-8">
          <div className="px-6 py-4 border-b border-slate-700">
            <h3 className="text-lg font-medium text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-blue-400" />
              Expert Review Queue
            </h3>
          </div>
          <div className="p-6">
            <div className="bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded-lg p-6 border border-slate-600">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                  <div>
                    <h4 className="font-semibold text-white text-lg">Document Analysis Review</h4>
                    <p className="text-sm text-slate-400">Request ID: demo-hitl-001</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-yellow-900/50 text-yellow-400 border border-yellow-700">
                    Pending Expert Review
                  </span>
                  <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-red-900/50 text-red-400 border border-red-700">
                    High Priority
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <AlertTriangle className="w-4 h-4 text-red-400 mr-2" />
                    <p className="text-sm font-medium text-slate-300">AI Confidence</p>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
                    <span className="text-xl font-bold text-white">35%</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Below threshold (60%)</p>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm font-medium text-slate-300 mb-2">Document Type</p>
                  <p className="text-lg font-semibold text-white">Employment Contract</p>
                  <p className="text-xs text-slate-500 mt-1">Complex legal document</p>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm font-medium text-slate-300 mb-2">Submitted</p>
                  <p className="text-lg font-semibold text-white">Just now</p>
                  <p className="text-xs text-slate-500 mt-1">User requested review</p>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm font-medium text-slate-300 mb-2">Estimated Time</p>
                  <p className="text-lg font-semibold text-white">24 hours</p>
                  <p className="text-xs text-slate-500 mt-1">High priority queue</p>
                </div>
              </div>

              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-300 mb-3">AI Analysis Issues Identified:</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-white">Complex Legal Language</p>
                        <p className="text-xs text-slate-400">Non-compete clause contains ambiguous terms</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-white">Multi-Jurisdictional Issues</p>
                        <p className="text-xs text-slate-400">Delaware and California law conflicts</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-white">Unusual Termination Terms</p>
                        <p className="text-xs text-slate-400">Potentially unenforceable clauses detected</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-white">IP Assignment Concerns</p>
                        <p className="text-xs text-slate-400">24-month post-employment scope unclear</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex space-x-4">
                <button className="bg-emerald-600 text-white px-6 py-3 rounded-lg hover:bg-emerald-700 transition-colors font-medium flex items-center">
                  <Users className="w-4 h-4 mr-2" />
                  Assign to Expert
                </button>
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  View Full Document
                </button>
                <button className="bg-slate-600 text-white px-6 py-3 rounded-lg hover:bg-slate-700 transition-colors font-medium">
                  Set Priority
                </button>
              </div>
            </div>
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
    </div>
  );
};

export default HITLDashboard;