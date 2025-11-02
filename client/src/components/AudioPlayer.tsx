import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { cn } from '../utils';
import { apiService } from '../services/apiService';
import { notificationService } from '../services/notificationService';

interface AudioPlayerProps {
  text: string;
  languageCode?: string;
  voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
  speakingRate?: number;
  className?: string;
  onPlay?: () => void;
  onPause?: () => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

interface AudioCache {
  [key: string]: Blob;
}

class AudioManager {
  private static instance: AudioManager;
  private audioCache: AudioCache = {};
  private currentAudio: HTMLAudioElement | null = null;

  static getInstance(): AudioManager {
    if (!AudioManager.instance) {
      AudioManager.instance = new AudioManager();
    }
    return AudioManager.instance;
  }

  private generateCacheKey(text: string, languageCode: string, voiceGender: string, speakingRate: number): string {
    return `${text.substring(0, 100)}_${languageCode}_${voiceGender}_${speakingRate}`;
  }

  async generateAudio(
    text: string, 
    languageCode: string = 'en-US',
    voiceGender: string = 'NEUTRAL',
    speakingRate: number = 0.9
  ): Promise<Blob> {
    const cacheKey = this.generateCacheKey(text, languageCode, voiceGender, speakingRate);
    
    // Check cache first
    if (this.audioCache[cacheKey]) {
      return this.audioCache[cacheKey];
    }

    // Generate new audio
    const audioBlob = await apiService.textToSpeech(text, {
      languageCode,
      voiceGender,
      speakingRate
    });

    if (!audioBlob) {
      throw new Error('Failed to generate audio');
    }

    // Cache the result
    this.audioCache[cacheKey] = audioBlob;
    
    return audioBlob;
  }

  async playAudio(audioBlob: Blob): Promise<HTMLAudioElement> {
    // Stop current audio if playing
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    this.currentAudio = audio;

    // Clean up URL when audio ends
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
      if (this.currentAudio === audio) {
        this.currentAudio = null;
      }
    });

    return audio;
  }

  stopCurrentAudio(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
  }

  clearCache(): void {
    this.audioCache = {};
  }

  getCacheSize(): number {
    return Object.keys(this.audioCache).length;
  }
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  text,
  languageCode = 'en-US',
  voiceGender = 'NEUTRAL',
  speakingRate = 0.9,
  className,
  onPlay,
  onPause,
  onError,
  disabled = false
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioManager = AudioManager.getInstance();

  // Clean up audio when component unmounts
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  // Update progress
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateProgress = () => {
      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }
    };

    const updateDuration = () => {
      setDuration(audio.duration || 0);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(0);
      audioRef.current = null;
    };

    audio.addEventListener('timeupdate', updateProgress);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateProgress);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioRef.current]);

  const handlePlay = async () => {
    if (disabled || !text.trim()) return;

    try {
      setIsLoading(true);

      // Generate or get cached audio
      const audioBlob = await audioManager.generateAudio(
        text,
        languageCode,
        voiceGender,
        speakingRate
      );

      // Create and play audio
      const audio = await audioManager.playAudio(audioBlob);
      audioRef.current = audio;

      // Set up audio properties
      audio.volume = isMuted ? 0 : 1;
      
      await audio.play();
      setIsPlaying(true);
      onPlay?.();

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to play audio';
      console.error('Audio playback error:', error);
      onError?.(errorMessage);
      notificationService.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      onPause?.();
    }
  };

  const handleToggleMute = () => {
    if (audioRef.current) {
      const newMutedState = !isMuted;
      audioRef.current.volume = newMutedState ? 0 : 1;
      setIsMuted(newMutedState);
    }
  };

  const handleProgressClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !duration) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const newProgress = (clickX / rect.width) * 100;
    const newTime = (newProgress / 100) * duration;

    audioRef.current.currentTime = newTime;
    setProgress(newProgress);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getLanguageFlag = (langCode: string): string => {
    const flagMap: { [key: string]: string } = {
      'en-US': '🇺🇸',
      'en-GB': '🇬🇧',
      'hi-IN': '🇮🇳',
      'es-US': '🇺🇸',
      'es-ES': '🇪🇸',
      'fr-FR': '🇫🇷',
      'de-DE': '🇩🇪',
      'it-IT': '🇮🇹',
      'pt-BR': '🇧🇷',
      'ja-JP': '🇯🇵',
      'ko-KR': '🇰🇷',
      'zh-CN': '🇨🇳'
    };
    return flagMap[langCode] || '🌐';
  };

  return (
    <div className={cn("flex items-center space-x-2 p-2 bg-slate-800 rounded-lg", className)}>
      {/* Play/Pause Button */}
      <button
        onClick={isPlaying ? handlePause : handlePlay}
        disabled={disabled || isLoading || !text.trim()}
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200",
          isPlaying
            ? "bg-red-500 hover:bg-red-600 text-white"
            : "bg-blue-500 hover:bg-blue-600 text-white",
          disabled || !text.trim()
            ? "opacity-50 cursor-not-allowed"
            : "hover:scale-105"
        )}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4 ml-0.5" />
        )}
      </button>

      {/* Progress Bar */}
      {(isPlaying || progress > 0) && (
        <div className="flex-1 flex items-center space-x-2">
          <div
            className="flex-1 h-2 bg-slate-600 rounded-full cursor-pointer overflow-hidden"
            onClick={handleProgressClick}
          >
            <div
              className="h-full bg-blue-500 transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {duration > 0 && (
            <span className="text-xs text-slate-400 min-w-[40px]">
              {formatTime((progress / 100) * duration)} / {formatTime(duration)}
            </span>
          )}
        </div>
      )}

      {/* Volume Control */}
      <button
        onClick={handleToggleMute}
        disabled={!isPlaying}
        className={cn(
          "flex items-center justify-center w-6 h-6 text-slate-400 hover:text-white transition-colors",
          !isPlaying && "opacity-50 cursor-not-allowed"
        )}
      >
        {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
      </button>

      {/* Language Indicator */}
      <div className="flex items-center space-x-1 text-xs text-slate-400">
        <span>{getLanguageFlag(languageCode)}</span>
        <span className="hidden sm:inline">{languageCode}</span>
      </div>

      {/* Voice Gender Indicator */}
      <div className="text-xs text-slate-500 hidden md:block">
        {voiceGender === 'MALE' ? '♂' : voiceGender === 'FEMALE' ? '♀' : '⚲'}
      </div>
    </div>
  );
};

export default AudioPlayer;