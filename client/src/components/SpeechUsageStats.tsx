import React, { useState, useEffect } from 'react';
import { Mic, Volume2, BarChart3, RefreshCw } from 'lucide-react';
import { cn } from '../utils';
import { apiService } from '../services/apiService';

interface UsageStats {
  speech_to_text: {
    used: number;
    limit: number;
    remaining: number;
  };
  text_to_speech: {
    used: number;
    limit: number;
    remaining: number;
  };
  reset_date: string;
  rate_limits?: {
    speech_to_text: {
      limit: number;
      remaining: number;
      reset_time: number | null;
      window: number;
    };
    text_to_speech: {
      limit: number;
      remaining: number;
      reset_time: number | null;
      window: number;
    };
  };
}

interface SpeechUsageStatsProps {
  className?: string;
  compact?: boolean;
}

export const SpeechUsageStats: React.FC<SpeechUsageStatsProps> = ({
  className,
  compact = false
}) => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.getSpeechUsageStats();
      
      if (result.success && result.data) {
        setStats(result.data);
      } else {
        setError(result.error || 'Failed to load usage stats');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load usage stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const getUsagePercentage = (used: number, limit: number): number => {
    return limit > 0 ? (used / limit) * 100 : 0;
  };

  const getUsageColor = (percentage: number): string => {
    if (percentage >= 90) return 'text-red-400';
    if (percentage >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getProgressBarColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatResetTime = (resetTime: number | null): string => {
    if (!resetTime) return 'N/A';
    
    const now = Date.now() / 1000;
    const diff = resetTime - now;
    
    if (diff <= 0) return 'Now';
    
    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (compact) {
    return (
      <div className={cn("flex items-center space-x-4 text-sm", className)}>
        {loading && (
          <div className="flex items-center space-x-1 text-slate-400">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Loading...</span>
          </div>
        )}
        
        {error && (
          <div className="text-red-400 text-xs">
            Usage stats unavailable
          </div>
        )}
        
        {stats && (
          <>
            <div className="flex items-center space-x-1">
              <Mic className="w-3 h-3 text-slate-400" />
              <span className={getUsageColor(getUsagePercentage(stats.speech_to_text.used, stats.speech_to_text.limit))}>
                {stats.speech_to_text.remaining}
              </span>
            </div>
            
            <div className="flex items-center space-x-1">
              <Volume2 className="w-3 h-3 text-slate-400" />
              <span className={getUsageColor(getUsagePercentage(stats.text_to_speech.used, stats.text_to_speech.limit))}>
                {stats.text_to_speech.remaining}
              </span>
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className={cn("bg-slate-800 rounded-lg p-4", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-slate-400" />
          <h3 className="text-lg font-semibold text-white">Speech Usage</h3>
        </div>
        
        <button
          onClick={fetchStats}
          disabled={loading}
          className="flex items-center space-x-1 px-2 py-1 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="text-red-400 text-sm mb-4 p-3 bg-red-900/20 rounded border border-red-800">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      )}

      {stats && (
        <div className="space-y-6">
          {/* Daily Limits */}
          <div>
            <h4 className="text-sm font-medium text-slate-300 mb-3">Daily Limits</h4>
            
            <div className="space-y-4">
              {/* Speech-to-Text */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Mic className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-300">Speech-to-Text</span>
                  </div>
                  <span className={cn("text-sm font-medium", getUsageColor(getUsagePercentage(stats.speech_to_text.used, stats.speech_to_text.limit)))}>
                    {stats.speech_to_text.used} / {stats.speech_to_text.limit}
                  </span>
                </div>
                
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={cn("h-2 rounded-full transition-all duration-300", getProgressBarColor(getUsagePercentage(stats.speech_to_text.used, stats.speech_to_text.limit)))}
                    style={{ width: `${Math.min(100, getUsagePercentage(stats.speech_to_text.used, stats.speech_to_text.limit))}%` }}
                  />
                </div>
                
                <div className="text-xs text-slate-400 mt-1">
                  {stats.speech_to_text.remaining} requests remaining
                </div>
              </div>

              {/* Text-to-Speech */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Volume2 className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-300">Text-to-Speech</span>
                  </div>
                  <span className={cn("text-sm font-medium", getUsageColor(getUsagePercentage(stats.text_to_speech.used, stats.text_to_speech.limit)))}>
                    {stats.text_to_speech.used} / {stats.text_to_speech.limit}
                  </span>
                </div>
                
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={cn("h-2 rounded-full transition-all duration-300", getProgressBarColor(getUsagePercentage(stats.text_to_speech.used, stats.text_to_speech.limit)))}
                    style={{ width: `${Math.min(100, getUsagePercentage(stats.text_to_speech.used, stats.text_to_speech.limit))}%` }}
                  />
                </div>
                
                <div className="text-xs text-slate-400 mt-1">
                  {stats.text_to_speech.remaining} requests remaining
                </div>
              </div>
            </div>
          </div>

          {/* Rate Limits */}
          {stats.rate_limits && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-3">Rate Limits (Per Hour)</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-700/50 rounded p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    <Mic className="w-3 h-3 text-slate-400" />
                    <span className="text-xs text-slate-300">STT</span>
                  </div>
                  <div className="text-sm font-medium text-white">
                    {stats.rate_limits.speech_to_text.remaining} / {stats.rate_limits.speech_to_text.limit}
                  </div>
                  <div className="text-xs text-slate-400">
                    Resets in {formatResetTime(stats.rate_limits.speech_to_text.reset_time)}
                  </div>
                </div>
                
                <div className="bg-slate-700/50 rounded p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    <Volume2 className="w-3 h-3 text-slate-400" />
                    <span className="text-xs text-slate-300">TTS</span>
                  </div>
                  <div className="text-sm font-medium text-white">
                    {stats.rate_limits.text_to_speech.remaining} / {stats.rate_limits.text_to_speech.limit}
                  </div>
                  <div className="text-xs text-slate-400">
                    Resets in {formatResetTime(stats.rate_limits.text_to_speech.reset_time)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Reset Information */}
          <div className="text-xs text-slate-400 border-t border-slate-700 pt-3">
            Daily limits reset: {new Date(stats.reset_date).toLocaleDateString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default SpeechUsageStats;