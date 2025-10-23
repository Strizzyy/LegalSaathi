/**
 * User Profile Component with authentication status display
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  Edit2, 
  Save, 
  X, 
  LogOut,
  Loader2
} from 'lucide-react';

export const UserProfile: React.FC = () => {
  const { user, signOut, updateUserProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user?.displayName || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!user) {
    return null;
  }

  const handleSaveProfile = async () => {
    if (!displayName.trim()) {
      setError('Display name cannot be empty');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await updateUserProfile(displayName.trim());
      setSuccess('Profile updated successfully');
      setIsEditing(false);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setDisplayName(user?.displayName || '');
    setIsEditing(false);
    setError('');
    setSuccess('');
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error: any) {
      setError('Failed to sign out');
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
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="flex flex-col items-center space-y-4">
          <Avatar className="h-20 w-20">
            <AvatarImage src={user.photoURL || undefined} alt={user.displayName || 'User'} />
            <AvatarFallback className="text-lg">
              {user.displayName ? getInitials(user.displayName) : <User className="h-8 w-8" />}
            </AvatarFallback>
          </Avatar>
          
          <div className="space-y-2">
            <CardTitle className="text-2xl">
              {user.displayName || 'User Profile'}
            </CardTitle>
            <CardDescription>
              Manage your account settings and preferences
            </CardDescription>
          </div>

          {/* Authentication Status */}
          <div className="flex items-center space-x-2">
            <Badge variant={user.emailVerified ? 'default' : 'secondary'} className="flex items-center space-x-1">
              <Shield className="h-3 w-3" />
              <span>{user.emailVerified ? 'Verified' : 'Unverified'}</span>
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Success/Error Messages */}
        {success && (
          <Alert>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}
        
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Profile Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Profile Information</h3>
          
          {/* Display Name */}
          <div className="space-y-2">
            <Label htmlFor="displayName" className="flex items-center space-x-2">
              <User className="h-4 w-4" />
              <span>Display Name</span>
            </Label>
            
            {isEditing ? (
              <div className="flex space-x-2">
                <Input
                  id="displayName"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Enter your display name"
                  disabled={loading}
                />
                <Button
                  size="sm"
                  onClick={handleSaveProfile}
                  disabled={loading}
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCancelEdit}
                  disabled={loading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <span>{user.displayName || 'Not set'}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Email */}
          <div className="space-y-2">
            <Label className="flex items-center space-x-2">
              <Mail className="h-4 w-4" />
              <span>Email Address</span>
            </Label>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
              <span>{user.email}</span>
              <Badge variant={user.emailVerified ? 'default' : 'secondary'}>
                {user.emailVerified ? 'Verified' : 'Unverified'}
              </Badge>
            </div>
          </div>

          {/* Account Created */}
          <div className="space-y-2">
            <Label className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Member Since</span>
            </Label>
            <div className="p-3 bg-gray-50 rounded-md">
              <span>{user.metadata?.creationTime ? formatDate(user.metadata.creationTime) : 'Unknown'}</span>
            </div>
          </div>

          {/* Last Sign In */}
          <div className="space-y-2">
            <Label className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Last Sign In</span>
            </Label>
            <div className="p-3 bg-gray-50 rounded-md">
              <span>{user.metadata?.lastSignInTime ? formatDate(user.metadata.lastSignInTime) : 'Unknown'}</span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Account Actions */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Account Actions</h3>
          
          <div className="flex flex-col space-y-2">
            <Button
              variant="outline"
              onClick={handleSignOut}
              className="w-full justify-start"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>

        {/* Privacy Notice */}
        <div className="p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Privacy Notice:</strong> We don't store your document analysis results. 
            All analyses are processed in real-time and only your authentication information is retained.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};