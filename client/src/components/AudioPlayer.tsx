import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, Download } from 'lucide-react';
import { cn } from '../lib/utils';
import { notificationService } from '../services/notificationService';

interface AudioPlayerProps {
  text: string;
  language?: string;
  voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
  speakingRate?: number;
  autoPlay?: boolean;
  className?: string;
  onError?: (error: string) => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  text,
  language = 'en-US',
  voiceGender = 'NEUTRAL',
  speakingRate = 0.9,
  autoPlay = false,
  className,
  onError
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressRef = useRef<HTMLDivElement | null>(null);

  // Generate audio when text changes
  useEffect(() => {
    if (text && text.length > 0) {
      generateAudio();
    }
  }, [text, language, voiceGender, speakingRate]);

  // Auto-play if enabled
  useEffect(() => {
    if (autoPlay && audioUrl && !isPlaying) {
      handlePlay();
    }
  }, [audioUrl, autoPlay]);

  // Update progress
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateProgress = () => {
      setCurrentTime(audio.currentTime);
      setDuration(audio.duration || 0);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('timeupdate', updateProgress);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadedmetadata', updateProgress);

    return () => {
      audio.removeEventListener('timeupdate', updateProgress);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadedmetadata', updateProgress);
    };
  }, [audioUrl]);

  const generateAudio = async () => {
    if (!text || text.length === 0) return;

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/speech/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: text.substring(0, 5000), // Limit text length
          language_code: language,
          voice_gender: voiceGender,
          speaking_rate: speakingRate,
          pitch: 0.0,
          audio_encoding: 'MP3'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const url = URL.createObjectURL(audioBlob);
      
      // Clean up previous URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      
      setAudioUrl(url);
      
      // Create new audio element
      if (audioRef.current) {
        audioRef.current.src = url;
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate audio';
      onError?.(errorMessage);
      notificationService.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlay = async () => {
    if (!audioRef.current || !audioUrl) return;

    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        await audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (error) {
      const errorMessage = 'Failed to play audio';
      onError?.(errorMessage);
      notificationService.error(errorMessage);
    }
  };

  const handleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setCurrentTime(0);
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressRef.current || duration === 0) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleDownload = () => {
    if (!audioUrl) return;

    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = 'legal-document-audio.mp3';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    notificationService.success('Audio downloaded successfully');
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (!text || text.length === 0) {
    return null;
  }

  return (
    <div className={cn("bg-slate-800/50 border border-slate-600 rounded-xl p-4", className)}>
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        preload="metadata"
        muted={isMuted}
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-5 h-5 text-slate-400" />
          <span className="text-sm font-medium text-white">Audio Playback</span>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span>{language}</span>
          <span>•</span>
          <span>{voiceGender.toLowerCase()}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center space-x-3 mb-4">
        <button
          onClick={handlePlay}
          disabled={isLoading || !audioUrl}
          className={cn(
            "flex items-center justify-center w-10 h-10 rounded-full transition-all",
            isLoading || !audioUrl
              ? "bg-slate-700 text-slate-500 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600 text-white hover:scale-105"
          )}
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : isPlaying ? (
            <Pause className="w-5 h-5" />
          ) : (
            <Play className="w-5 h-5 ml-0.5" />
          )}
        </button>

        <button
          onClick={handleRestart}
          disabled={!audioUrl}
          className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <button
          onClick={handleMute}
          disabled={!audioUrl}
          className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>

        <button
          onClick={handleDownload}
          disabled={!audioUrl}
          className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
        </button>

        {/* Time display */}
        <div className="flex-1 text-right">
          <span className="text-sm text-slate-400 font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div
        ref={progressRef}
        onClick={handleProgressClick}
        className="relative h-2 bg-slate-700 rounded-full cursor-pointer group"
      >
        <div
          className="absolute top-0 left-0 h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${progressPercentage}%` }}
        />
        <div
          className="absolute top-1/2 transform -translate-y-1/2 w-3 h-3 bg-blue-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: `calc(${progressPercentage}% - 6px)` }}
        />
      </div>

      {/* Text preview */}
      <div className="mt-4 p-3 bg-slate-900/50 rounded-lg">
        <p className="text-sm text-slate-300 line-clamp-3">
          {text.length > 200 ? `${text.substring(0, 200)}...` : text}
        </p>
        {text.length > 5000 && (
          <p className="text-xs text-yellow-400 mt-2">
            Note: Only the first 5000 characters will be converted to speech
          </p>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="mt-4 flex items-center justify-center space-x-2 text-sm text-blue-400">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <span>Generating audio...</span>
        </div>
      )}
    </div>
  );
};

export default AudioPlayer;