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

    // Simple smooth progress that doesn't get stuck
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const remaining = 100 - prev;
        const increment = Math.max(0.1, remaining * 0.015); // Slower as it approaches 100%
        return Math.min(prev + increment, 95); // Cap at 95% to avoid getting stuck
      });
    }, 200);

    return () => {
      clearInterval(progressInterval);
    };
  }, [isLoading]);

  const getStatusLabel = (progress: number) => {
    if (progress < 20) return 'Initializing...';
    if (progress < 40) return 'Processing document...';
    if (progress < 60) return 'Analyzing clauses...';
    if (progress < 80) return 'Generating insights...';
    return 'Finalizing...';
  };

  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-slate-400">{getStatusLabel(progress)}</span>
        <span className="text-xs text-slate-400">{Math.round(progress)}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-700/50 rounded-full overflow-hidden relative">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}