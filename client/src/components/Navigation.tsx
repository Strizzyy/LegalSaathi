import { useState, useEffect } from 'react';
import { Shield, Wifi, WifiOff } from 'lucide-react';
import { motion } from 'framer-motion';

export function Navigation() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

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
          </div>
        </div>
      </div>
    </motion.nav>
  );
}