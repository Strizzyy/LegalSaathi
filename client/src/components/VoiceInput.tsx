import { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Globe, ChevronDown } from 'lucide-react';
import { cn } from '../utils';
import { notificationService } from '../services/notificationService';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onError: (error: string) => void;
  language?: string;
  className?: string;
  disabled?: boolean;
  showLanguageSelector?: boolean;
  onLanguageChange?: (language: string) => void;
  forceEnglish?: boolean; // Force English as default language
}

interface SupportedLanguage {
  code: string;
  name: string;
  flag: string;
}

const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
  { code: 'hi-IN', name: 'Hindi (India)', flag: '🇮🇳' },
  { code: 'es-US', name: 'Spanish (US)', flag: '🇺🇸' },
  { code: 'es-ES', name: 'Spanish (Spain)', flag: '🇪🇸' },
  { code: 'fr-FR', name: 'French (France)', flag: '🇫🇷' },
  { code: 'de-DE', name: 'German (Germany)', flag: '🇩🇪' },
  { code: 'it-IT', name: 'Italian (Italy)', flag: '🇮🇹' },
  { code: 'pt-BR', name: 'Portuguese (Brazil)', flag: '🇧🇷' },
  { code: 'ja-JP', name: 'Japanese (Japan)', flag: '🇯🇵' },
  { code: 'ko-KR', name: 'Korean (South Korea)', flag: '🇰🇷' },
  { code: 'zh-CN', name: 'Chinese (Simplified)', flag: '🇨🇳' }
];

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onError,
  language = 'en-US', // Force English as default
  className,
  disabled = false,
  showLanguageSelector = true,
  onLanguageChange,
  forceEnglish = true // Force English by default
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    // Force English as default if forceEnglish is true
    const defaultLang = forceEnglish ? 'en-US' : (language || 'en-US');
    console.log('VoiceInput initialized with language:', language, '-> using:', defaultLang, 'forceEnglish:', forceEnglish);
    return defaultLang;
  });
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

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
          
          // Send to backend for transcription using enhanced API
          const result = await fetch('/api/speech/speech-to-text', {
            method: 'POST',
            body: (() => {
              const formData = new FormData();
              formData.append('audio_file', audioBlob, 'recording.webm');
              formData.append('language_code', selectedLanguage); // Use selected language
              formData.append('enable_punctuation', 'true');
              return formData;
            })()
          }).then(async (response) => {
            if (!response.ok) {
              const errorData = await response.json().catch(() => ({}));
              throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            return response.json();
          });

          if (result.success && result.transcript) {
            onTranscript(result.transcript);
            
            // Show enhanced success message with confidence if available
            const confidence = result.confidence ? Math.round(result.confidence * 100) : null;
            const message = confidence 
              ? `Voice input transcribed successfully (${confidence}% confidence)`
              : 'Voice input transcribed successfully';
            
            notificationService.success(message);
          } else {
            throw new Error(result.error_message || result.error || 'Transcription failed');
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

      notificationService.success(`Recording started in ${getCurrentLanguage().name}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
      onError(errorMessage);
      notificationService.error(errorMessage);
    }
  }, [disabled, isRecording, selectedLanguage, onTranscript, onError]);

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

  const getCurrentLanguage = (): SupportedLanguage => {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];
  };

  const handleLanguageChange = (languageCode: string) => {
    setSelectedLanguage(languageCode);
    setShowLanguageDropdown(false);
    onLanguageChange?.(languageCode);
    notificationService.success(`Voice input language changed to ${SUPPORTED_LANGUAGES.find(l => l.code === languageCode)?.name}`);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowLanguageDropdown(false);
      }
    };

    if (showLanguageDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
    
    return undefined;
  }, [showLanguageDropdown]);

  return (
    <div className={cn("voice-input-container flex items-center space-x-3", className)}>
      {/* Language Selector */}
      {showLanguageSelector && !isRecording && !isProcessing && (
        <div className="relative z-50" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
            disabled={disabled}
            className={cn(
              "flex items-center space-x-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-sm",
              disabled && "opacity-50 cursor-not-allowed"
            )}
          >
            <Globe className="w-4 h-4" />
            <span className="text-lg">{getCurrentLanguage().flag}</span>
            <span className="hidden sm:inline">{getCurrentLanguage().name}</span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {/* Language Dropdown */}
          {showLanguageDropdown && (
            <div 
              className="absolute top-full left-0 mt-2 w-64 bg-slate-800 border border-slate-600 rounded-lg shadow-2xl max-h-64 overflow-y-auto z-[99999]"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: '0.5rem',
                zIndex: 99999,
                backgroundColor: 'rgb(30 41 59)',
                border: '1px solid rgb(71 85 105)',
                borderRadius: '0.5rem',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                maxHeight: '16rem',
                overflowY: 'auto',
                width: '16rem'
              }}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className={cn(
                    "w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-slate-700 transition-colors",
                    selectedLanguage === lang.code && "bg-slate-700 text-blue-400"
                  )}
                >
                  <span className="text-lg">{lang.flag}</span>
                  <div>
                    <div className="text-sm font-medium text-white">{lang.name}</div>
                    <div className="text-xs text-slate-400">{lang.code}</div>
                  </div>
                  {selectedLanguage === lang.code && (
                    <div className="ml-auto w-2 h-2 bg-blue-400 rounded-full" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Microphone Button */}
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

      {/* Status Display */}
      <div className="flex-1 min-w-0">
        {/* Recording status */}
        {isRecording && (
          <div className="flex items-center space-x-2 text-sm">
            <div className="flex items-center space-x-1 text-red-400">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span>Recording in {getCurrentLanguage().name}</span>
            </div>
            <span className="text-slate-400">{formatTime(recordingTime)}</span>
          </div>
        )}

        {/* Processing status */}
        {isProcessing && (
          <div className="flex items-center space-x-2 text-sm text-blue-400">
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            <span>Processing {getCurrentLanguage().name}...</span>
          </div>
        )}

        {/* Instructions */}
        {!isRecording && !isProcessing && (
          <div className="text-sm text-slate-400">
            <div>Click to start voice input</div>
            <div className="text-xs text-slate-500">
              Language: {getCurrentLanguage().flag} {getCurrentLanguage().name}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceInput;