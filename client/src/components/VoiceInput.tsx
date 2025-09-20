import { useState, useRef, useCallback } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { cn } from '../utils';
import { notificationService } from '../services/notificationService';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onError: (error: string) => void;
  language?: string;
  className?: string;
  disabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onError,
  language = 'en-US',
  className,
  disabled = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const startRecording = useCallback(async () => {
    if (disabled || isRecording) return;

    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000
        } 
      });

      // Set up audio level monitoring
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;

      // Start audio level monitoring
      const monitorAudioLevel = () => {
        if (!analyserRef.current) return;
        
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        setAudioLevel(average / 255);
        
        if (isRecording) {
          animationFrameRef.current = requestAnimationFrame(monitorAudioLevel);
        }
      };

      // Set up MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
          
          // Send to backend for transcription
          const formData = new FormData();
          formData.append('audio_file', audioBlob, 'recording.webm');
          formData.append('language_code', language);
          formData.append('enable_punctuation', 'true');

          const response = await fetch('/api/speech/speech-to-text', {
            method: 'POST',
            body: formData
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();

          if (result.success && result.transcript) {
            onTranscript(result.transcript);
            notificationService.success('Voice input transcribed successfully');
          } else {
            throw new Error(result.error_message || 'Transcription failed');
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Voice transcription failed';
          onError(errorMessage);
          notificationService.error(errorMessage);
        } finally {
          setIsProcessing(false);
          
          // Clean up
          stream.getTracks().forEach(track => track.stop());
          if (audioContextRef.current) {
            audioContextRef.current.close();
          }
        }
      };

      // Start recording
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      // Start audio level monitoring
      monitorAudioLevel();

      notificationService.success('Recording started');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
      onError(errorMessage);
      notificationService.error(errorMessage);
    }
  }, [disabled, isRecording, language, onTranscript, onError]);

  const stopRecording = useCallback(() => {
    if (!isRecording || !mediaRecorderRef.current) return;

    mediaRecorderRef.current.stop();
    setIsRecording(false);
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setAudioLevel(0);
  }, [isRecording]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={cn("flex items-center space-x-3", className)}>
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isProcessing}
        className={cn(
          "relative flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300",
          isRecording
            ? "bg-red-500 hover:bg-red-600 text-white animate-pulse"
            : "bg-slate-700 hover:bg-slate-600 text-slate-300",
          disabled || isProcessing
            ? "opacity-50 cursor-not-allowed"
            : "hover:scale-105"
        )}
      >
        {isProcessing ? (
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-5 h-5" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
        
        {/* Audio level indicator */}
        {isRecording && (
          <div 
            className="absolute inset-0 rounded-full border-2 border-red-300"
            style={{
              transform: `scale(${1 + audioLevel * 0.3})`,
              opacity: 0.6
            }}
          />
        )}
      </button>

      {/* Recording status */}
      {isRecording && (
        <div className="flex items-center space-x-2 text-sm">
          <div className="flex items-center space-x-1 text-red-400">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span>Recording</span>
          </div>
          <span className="text-slate-400">{formatTime(recordingTime)}</span>
        </div>
      )}

      {/* Processing status */}
      {isProcessing && (
        <div className="flex items-center space-x-2 text-sm text-blue-400">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <span>Processing...</span>
        </div>
      )}

      {/* Instructions */}
      {!isRecording && !isProcessing && (
        <span className="text-sm text-slate-400">
          Click to start voice input
        </span>
      )}
    </div>
  );
};

export default VoiceInput;