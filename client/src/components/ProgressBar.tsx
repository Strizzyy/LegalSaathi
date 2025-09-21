import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  isLoading: boolean;
  className?: string;
}

export function ProgressBar({ isLoading, className = '' }: ProgressBarProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setProgress(0);
      return;
    }

    // Progress simulation
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const increment = Math.random() * 8 + 3; // 3-11% increments
        return Math.min(prev + increment, 92); // Cap at 92% until completion
      });
    }, 600);

    return () => {
      clearInterval(progressInterval);
    };
  }, [isLoading]);

  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-slate-400">Analyzing...</span>
        <span className="text-xs text-slate-400">{Math.round(progress)}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
}