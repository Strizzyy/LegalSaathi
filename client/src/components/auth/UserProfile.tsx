/**
 * User Profile Component with authentication status display
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  ArrowLeft,
  Edit2,
  LogOut
} from 'lucide-react';

interface UserProfileProps {
  onBack?: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ onBack }) => {
  const { user, signOut } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  if (!user) {
    return null;
  }

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error: any) {
      console.error('Failed to sign out:', error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="w-full max-w-sm mx-auto bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-5 shadow-2xl">
      {/* Back Button */}
      {onBack && (
        <button
          onClick={onBack}
          className="flex items-center text-slate-400 hover:text-white transition-colors mb-3 p-1 -ml-1 rounded-lg hover:bg-slate-700/50"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
      )}

      {/* Profile Avatar and Name */}
      <div className="text-center mb-5">
        <div className="w-14 h-14 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-2">
          {user.photoURL ? (
            <img 
              src={user.photoURL} 
              alt={user.displayName || 'User'} 
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-white text-lg font-bold">
              {user.displayName ? getInitials(user.displayName) : 'U'}
            </span>
          )}
        </div>
        
        <h1 className="text-xl font-bold text-white mb-1">
          {user.displayName || 'User'}
        </h1>
        <p className="text-slate-400 text-xs">
          Manage your account settings and preferences
        </p>
        
        {/* Verification Status */}
        <div className="flex items-center justify-center mt-2">
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            user.emailVerified 
              ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
              : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
          }`}>
            {user.emailVerified ? 'Verified' : 'Unverified'}
          </div>
        </div>
      </div>

      {/* Profile Information */}
      <div className="space-y-3">
        {/* Display Name */}
        <div>
          <label className="block text-white text-xs font-medium mb-1">
            Display Name
          </label>
          <div className="flex items-center justify-between px-3 py-2 bg-slate-900/50 border border-slate-600/50 rounded-lg">
            <span className="text-slate-300 text-sm">{user.displayName || 'Not set'}</span>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="p-1 text-slate-400 hover:text-white transition-colors"
            >
              <Edit2 className="h-3 w-3" />
            </button>
          </div>
        </div>

        {/* Email Address */}
        <div>
          <label className="block text-white text-xs font-medium mb-1">
            Email Address
          </label>
          <div className="flex items-center justify-between px-3 py-2 bg-slate-900/50 border border-slate-600/50 rounded-lg">
            <span className="text-slate-300 truncate text-sm">{user.email}</span>
            <div className={`px-2 py-1 rounded text-xs font-medium ml-2 ${
              user.emailVerified 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {user.emailVerified ? 'Verified' : 'Unverified'}
            </div>
          </div>
        </div>

        {/* Member Since */}
        <div>
          <label className="block text-white text-xs font-medium mb-1">
            Member Since
          </label>
          <div className="px-3 py-2 bg-slate-900/50 border border-slate-600/50 rounded-lg">
            <span className="text-slate-300 text-sm">
              {user.metadata?.creationTime ? formatDate(user.metadata.creationTime) : 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      {/* Sign Out Button */}
      <div className="mt-5">
        <button
          onClick={handleSignOut}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-2.5 rounded-lg font-medium hover:from-cyan-400 hover:to-blue-400 transition-all flex items-center justify-center text-sm"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </button>
      </div>
    </div>
  );
};