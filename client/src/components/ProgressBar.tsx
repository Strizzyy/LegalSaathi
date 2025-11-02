import { useState, useEffect } from 'react';

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
        const remaining = 99 - prev;
        const increment = Math.max(0.1, remaining * 0.015); // Slower as it approaches 99%
        return Math.min(prev + increment, 99); // Cap at 99% maximum to provide realistic progress feedback
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
    if (progress < 95) return 'Finalizing...';
    return 'Almost ready...';
  };

  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-slate-400">{getStatusLabel(progress)}</span>
        <span className="text-xs text-slate-400">{Math.round(progress)}%</span>
      </div>
      <div className="w-full h-2 bg-slate-700 rounded-full relative border border-slate-600">
        <div
          className="h-full bg-gradient-to-r from-purple-400 to-pink-500 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
        
        {/* Shine effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer rounded-full" />
      </div>
    </div>
  );
}