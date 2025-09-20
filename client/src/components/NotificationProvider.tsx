import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '../utils';
import { notificationService } from '../services/notificationService';
import type { NotificationOptions } from '../services/notificationService';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  } | undefined;
}

interface NotificationContextType {
  showNotification: (message: string, type?: Notification['type'], options?: NotificationOptions) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = useCallback((
    message: string, 
    type: Notification['type'] = 'info', 
    options: NotificationOptions = {}
  ) => {
    const { duration = 5000, persistent = false, action } = options;
    const id = Math.random().toString(36).substr(2, 9);
    const notification: Notification = { 
      id, 
      type, 
      message, 
      duration: persistent ? 0 : duration,
      ...(action && { action })
    };
    
    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification
    if (!persistent && duration > 0) {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== id));
      }, duration);
    }
  }, []);

  // Subscribe to notification service
  useEffect(() => {
    const unsubscribe = notificationService.subscribe((message, type, options) => {
      showNotification(message, type, options);
    });

    return unsubscribe;
  }, [showNotification]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <AlertCircle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getNotificationClasses = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return 'bg-green-500/20 border-green-500/50 text-green-400';
      case 'error':
        return 'bg-red-500/20 border-red-500/50 text-red-400';
      case 'warning':
        return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400';
      case 'info':
      default:
        return 'bg-blue-500/20 border-blue-500/50 text-blue-400';
    }
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      
      {/* Notification Container */}
      <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
        <AnimatePresence>
          {notifications.map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 300, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 300, scale: 0.8 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={cn(
                "p-4 rounded-lg border shadow-lg backdrop-blur-sm",
                getNotificationClasses(notification.type)
              )}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-relaxed">
                    {notification.message}
                  </p>
                  {notification.action && (
                    <button
                      onClick={() => {
                        notification.action!.handler();
                        removeNotification(notification.id);
                      }}
                      className="text-xs underline mt-1 hover:no-underline"
                    >
                      {notification.action.label}
                    </button>
                  )}
                </div>
                <button
                  onClick={() => removeNotification(notification.id)}
                  className="flex-shrink-0 ml-2 opacity-70 hover:opacity-100 transition-opacity"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </NotificationContext.Provider>
  );
}