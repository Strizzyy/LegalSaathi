/**
 * Expert User Management Component
 * Admin interface for managing expert accounts and role assignments
 */

import React, { useState, useEffect } from 'react';
import { notificationService } from '../services/notificationService';

interface ExpertUser {
  uid: string;
  email: string;
  display_name?: string;
  role: string;
  specializations: string[];
  active: boolean;
  created_at: string;
  last_login?: string;
  reviews_completed: number;
  average_review_time: number;
}

interface AvailableRole {
  name: string;
  permissions: string[];
}

export const ExpertUserManagement: React.FC = () => {
  const [experts, setExperts] = useState<ExpertUser[]>([]);
  const [availableRoles, setAvailableRoles] = useState<Record<string, AvailableRole>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddExpert, setShowAddExpert] = useState(false);
  const [newExpertForm, setNewExpertForm] = useState({
    user_id: '',
    role: 'legal_expert',
    specializations: [] as string[]
  });

  useEffect(() => {
    loadExpertData();
  }, []);

  const loadExpertData = async () => {
    try {
      setIsLoading(true);
      setError('');

      const token = localStorage.getItem('expert_token');
      if (!token) {
        throw new Error('Expert authentication required');
      }

      // Load experts and available roles
      const [expertsResponse, rolesResponse] = await Promise.all([
        fetch('/api/expert/admin/experts', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch('/api/expert/admin/roles', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      ]);

      if (!expertsResponse.ok || !rolesResponse.ok) {
        throw new Error('Failed to load expert data');
      }

      const expertsResult = await expertsResponse.json();
      const rolesResult = await rolesResponse.json();

      if (expertsResult.success) {
        setExperts(expertsResult.experts || []);
      }

      if (rolesResult.success) {
        setAvailableRoles(rolesResult.roles || {});
      }

    } catch (error: any) {
      console.error('Failed to load expert data:', error);
      setError(error.message || 'Failed to load expert data');
      notificationService.error('Failed to load expert data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssignRole = async () => {
    try {
      if (!newExpertForm.user_id.trim()) {
        notificationService.error('Please enter a user ID');
        return;
      }

      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch('/api/expert/admin/assign-role', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newExpertForm),
      });

      if (!response.ok) {
        throw new Error('Failed to assign expert role');
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to assign expert role');
      }

      notificationService.success('Expert role assigned successfully');
      setShowAddExpert(false);
      setNewExpertForm({
        user_id: '',
        role: 'legal_expert',
        specializations: []
      });
      
      // Reload expert data
      await loadExpertData();

    } catch (error: any) {
      console.error('Failed to assign expert role:', error);
      notificationService.error(error.message || 'Failed to assign expert role');
    }
  };

  const handleRemoveRole = async (userId: string) => {
    if (!window.confirm('Are you sure you want to remove expert role from this user?')) {
      return;
    }

    try {
      const token = localStorage.getItem('expert_token');
      if (!token) return;

      const response = await fetch(`/api/expert/admin/remove-role/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to remove expert role');
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to remove expert role');
      }

      notificationService.success('Expert role removed successfully');
      
      // Reload expert data
      await loadExpertData();

    } catch (error: any) {
      console.error('Failed to remove expert role:', error);
      notificationService.error(error.message || 'Failed to remove expert role');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'text-red-400 bg-red-900/30';
      case 'senior_expert': return 'text-purple-400 bg-purple-900/30';
      case 'legal_expert': return 'text-blue-400 bg-blue-900/30';
      default: return 'text-slate-400 bg-slate-900/30';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-300">Loading Expert Management...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Expert User Management</h2>
        <button
          onClick={() => setShowAddExpert(true)}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all duration-200 font-medium"
        >
          Add Expert
        </button>
      </div>

      {/* Add Expert Form */}
      {showAddExpert && (
        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Assign Expert Role</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                User ID (Firebase UID)
              </label>
              <input
                type="text"
                value={newExpertForm.user_id}
                onChange={(e) => setNewExpertForm(prev => ({ ...prev, user_id: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                placeholder="Enter Firebase user ID"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Expert Role
              </label>
              <select
                value={newExpertForm.role}
                onChange={(e) => setNewExpertForm(prev => ({ ...prev, role: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                {Object.entries(availableRoles).map(([roleKey, roleInfo]) => (
                  <option key={roleKey} value={roleKey}>
                    {roleInfo.name.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <div className="flex space-x-2">
                <button
                  onClick={handleAssignRole}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  Assign Role
                </button>
                <button
                  onClick={() => setShowAddExpert(false)}
                  className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>

          {/* Role Permissions Preview */}
          {newExpertForm.role && availableRoles[newExpertForm.role] && (
            <div className="mt-4 p-4 bg-slate-900 rounded-lg">
              <h4 className="text-sm font-medium text-slate-300 mb-2">Role Permissions:</h4>
              <div className="flex flex-wrap gap-2">
                {availableRoles[newExpertForm.role].permissions.map((permission, index) => (
                  <span key={index} className="px-2 py-1 bg-cyan-900/50 text-cyan-300 rounded text-xs">
                    {permission.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Expert List */}
      <div className="bg-slate-800 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-medium text-white">Expert Users ({experts.length})</h3>
        </div>

        {experts.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-slate-400 mb-2">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
            <p className="text-slate-400">No expert users found</p>
            <p className="text-sm text-slate-500 mt-1">Add expert roles to users to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700">
            {experts.map((expert) => (
              <div key={expert.uid} className="p-6 hover:bg-slate-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="text-white font-medium">
                        {expert.display_name || expert.email}
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(expert.role)}`}>
                        {expert.role.replace('_', ' ').toUpperCase()}
                      </span>
                      {!expert.active && (
                        <span className="px-2 py-1 bg-red-900/30 text-red-300 rounded-full text-xs font-medium">
                          INACTIVE
                        </span>
                      )}
                    </div>
                    
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>Email: {expert.email}</div>
                      <div>UID: {expert.uid}</div>
                      <div>Created: {formatDate(expert.created_at)}</div>
                      <div>Last Login: {formatDate(expert.last_login)}</div>
                      <div>Reviews: {expert.reviews_completed}</div>
                      <div>Avg. Time: {(expert.average_review_time / 60).toFixed(1)}h</div>
                      {expert.specializations.length > 0 && (
                        <div className="flex items-center space-x-2 mt-2">
                          <span>Specializations:</span>
                          <div className="flex flex-wrap gap-1">
                            {expert.specializations.map((spec, index) => (
                              <span key={index} className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs">
                                {spec}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="text-right text-sm">
                      <div className="text-white font-medium">
                        {expert.reviews_completed}
                      </div>
                      <div className="text-slate-400">Reviews</div>
                    </div>
                    
                    <button
                      onClick={() => handleRemoveRole(expert.uid)}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors"
                    >
                      Remove Role
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Roles Reference */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Available Expert Roles</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(availableRoles).map(([roleKey, roleInfo]) => (
            <div key={roleKey} className="bg-slate-900 rounded-lg p-4">
              <h4 className={`font-medium mb-2 ${getRoleColor(roleKey)}`}>
                {roleInfo.name.replace('_', ' ').toUpperCase()}
              </h4>
              <div className="space-y-1">
                {roleInfo.permissions.map((permission, index) => (
                  <div key={index} className="text-xs text-slate-400">
                    • {permission.replace('_', ' ')}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};