import React from 'react';
import { Volume2 } from 'lucide-react';
import { AudioPlayer } from './AudioPlayer';
import { cn } from '../utils';

interface ClauseAudioButtonProps {
  clauseText: string;
  explanation: string;
  languageCode?: string;
  className?: string;
  compact?: boolean;
}

export const ClauseAudioButton: React.FC<ClauseAudioButtonProps> = ({
  clauseText,
  explanation,
  languageCode = 'en-US',
  className,
  compact = false
}) => {
  // Combine clause text and explanation for TTS
  const fullText = `${clauseText}. ${explanation}`;

  // Get appropriate voice gender based on language
  const getVoiceGender = (langCode: string): 'MALE' | 'FEMALE' | 'NEUTRAL' => {
    // Use neutral voices for most languages for consistency
    return 'NEUTRAL';
  };

  // Get speaking rate based on language (some languages need slower speech)
  const getSpeakingRate = (langCode: string): number => {
    const rateMap: { [key: string]: number } = {
      'hi-IN': 0.8,  // Hindi - slightly slower
      'zh-CN': 0.8,  // Chinese - slightly slower
      'ja-JP': 0.8,  // Japanese - slightly slower
      'ko-KR': 0.8,  // Korean - slightly slower
      'de-DE': 0.85, // German - slightly slower
      'fr-FR': 0.9,  // French - normal
      'es-US': 0.9,  // Spanish - normal
      'es-ES': 0.9,  // Spanish - normal
      'it-IT': 0.9,  // Italian - normal
      'pt-BR': 0.9,  // Portuguese - normal
      'en-US': 0.9,  // English - normal
      'en-GB': 0.9   // English - normal
    };
    return rateMap[langCode] || 0.9;
  };

  if (compact) {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center w-6 h-6 rounded-full",
          "bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white",
          "transition-all duration-200 hover:scale-105",
          "group relative",
          className
        )}
        title={`Listen to clause explanation in ${languageCode}`}
      >
        <Volume2 className="w-3 h-3" />
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
          Listen to explanation
        </div>
        
        {/* Hidden AudioPlayer that gets triggered */}
        <div className="hidden">
          <AudioPlayer
            text={fullText}
            languageCode={languageCode}
            voiceGender={getVoiceGender(languageCode)}
            speakingRate={getSpeakingRate(languageCode)}
          />
        </div>
      </button>
    );
  }

  return (
    <div className={cn("mt-3", className)}>
      <div className="flex items-center space-x-2 mb-2">
        <Volume2 className="w-4 h-4 text-slate-400" />
        <span className="text-sm text-slate-400">Listen to explanation</span>
      </div>
      
      <AudioPlayer
        text={fullText}
        languageCode={languageCode}
        voiceGender={getVoiceGender(languageCode)}
        speakingRate={getSpeakingRate(languageCode)}
        className="w-full"
      />
    </div>
  );
};

export default ClauseAudioButton;