import { useState, useEffect } from 'react';
import { Shield, Wifi, WifiOff, User, LogIn, UserPlus } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import AdminAccessButton from './admin/AdminAccessButton';

interface NavigationProps {
  onShowAuth?: (mode: 'login' | 'register') => void;
  onShowProfile?: () => void;
  onShowAbout?: () => void;
  onShowContact?: () => void;
}

export function Navigation({ onShowAuth, onShowProfile, onShowAbout, onShowContact }: NavigationProps) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const { user, loading } = useAuth();

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <motion.nav 
      className="fixed top-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <motion.a 
            href="/" 
            className="flex items-center space-x-3 group"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center group-hover:shadow-lg group-hover:shadow-cyan-500/25 transition-all duration-300">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="text-xl font-bold text-white group-hover:text-cyan-400 transition-colors">
                LegalSaathi
              </div>
              <div className="text-sm text-cyan-400 opacity-75">
                Universal Document Advisor
              </div>
            </div>
          </motion.a>

          <div className="flex items-center space-x-4">
            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-6">
              <button
                onClick={onShowAbout}
                className="text-slate-300 hover:text-cyan-400 transition-colors font-medium"
              >
                About Us
              </button>
              <button
                onClick={onShowContact}
                className="text-slate-300 hover:text-cyan-400 transition-colors font-medium"
              >
                Contact
              </button>
            </div>

            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {isOnline ? (
                <motion.div 
                  className="flex items-center space-x-2 text-green-400"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <Wifi className="w-4 h-4" />
                  <span className="text-sm hidden sm:inline">Online</span>
                </motion.div>
              ) : (
                <motion.div 
                  className="flex items-center space-x-2 text-red-400"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <WifiOff className="w-4 h-4" />
                  <span className="text-sm hidden sm:inline">Offline</span>
                </motion.div>
              )}
            </div>

            {/* AI Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-emerald-400 text-sm hidden sm:inline">AI Ready</span>
            </div>

            {/* Admin Access Button (only visible to admins) */}
            <AdminAccessButton />

            {/* Authentication Section */}
            {loading ? (
              <div className="w-8 h-8 bg-slate-700 rounded-full animate-pulse"></div>
            ) : user ? (
              /* Authenticated User */
              <motion.button
                onClick={onShowProfile}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-slate-800 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.photoURL || undefined} alt={user.displayName || 'User'} />
                  <AvatarFallback className="text-xs bg-cyan-500 text-white">
                    {user.displayName ? getInitials(user.displayName) : <User className="h-4 w-4" />}
                  </AvatarFallback>
                </Avatar>
                <span className="text-white text-sm hidden md:inline">
                  {user.displayName || user.email?.split('@')[0] || 'User'}
                </span>
              </motion.button>
            ) : (
              /* Unauthenticated User */
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onShowAuth?.('login')}
                  className="text-white hover:text-cyan-400 hover:bg-slate-800"
                >
                  <LogIn className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Sign In</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onShowAuth?.('register')}
                  className="border-cyan-500 text-cyan-400 hover:bg-cyan-500 hover:text-white"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Sign Up</span>
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.nav>
  );
}