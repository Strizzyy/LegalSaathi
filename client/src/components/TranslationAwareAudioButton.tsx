import React, { useState, useEffect, useRef } from 'react';
import { Volume2, Globe } from 'lucide-react';
import { AudioPlayer } from './AudioPlayer';
import { translationService, type ClauseData } from '../services/translationService';
import { cn } from '../utils';

interface TranslationAwareAudioButtonProps {
  clauseData: ClauseData;
  originalExplanation: string;
  className?: string;
  compact?: boolean;
}

// Map translation service language codes to speech service language codes
const TRANSLATION_TO_SPEECH_LANGUAGE_MAP: { [key: string]: string } = {
  'es': 'es-ES',    // Spanish -> Spanish (Spain)
  'fr': 'fr-FR',    // French -> French (France)
  'de': 'de-DE',    // German -> German (Germany)
  'it': 'it-IT',    // Italian -> Italian (Italy)
  'pt': 'pt-BR',    // Portuguese -> Portuguese (Brazil)
  'ru': 'ru-RU',    // Russian -> Russian (Russia)
  'ja': 'ja-JP',    // Japanese -> Japanese (Japan)
  'ko': 'ko-KR',    // Korean -> Korean (South Korea)
  'zh': 'zh-CN',    // Chinese -> Chinese (Simplified)
  'hi': 'hi-IN',    // Hindi -> Hindi (India)
  'ar': 'ar-SA',    // Arabic -> Arabic (Saudi Arabia) - if supported
  'en': 'en-US'     // English -> English (US)
};

export const TranslationAwareAudioButton: React.FC<TranslationAwareAudioButtonProps> = ({
  clauseData,
  originalExplanation,
  className,
  compact = false
}) => {
  const [translations, setTranslations] = useState(new Map());
  const [availableLanguages, setAvailableLanguages] = useState<string[]>(['en']);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const clauseKey = `${clauseData.id}_${clauseData.index}`;

  useEffect(() => {
    const unsubscribe = translationService.subscribe(() => {
      const clauseTranslations = translationService.getClauseTranslations(clauseKey);
      setTranslations(clauseTranslations);
      
      // Update available languages
      const languages = ['en', ...Array.from(clauseTranslations.keys())];
      setAvailableLanguages(languages);
      
      // If current selected language is not available, reset to English
      if (!languages.includes(selectedLanguage)) {
        setSelectedLanguage('en');
      }
    });

    // Initial load
    const clauseTranslations = translationService.getClauseTranslations(clauseKey);
    setTranslations(clauseTranslations);
    setAvailableLanguages(['en', ...Array.from(clauseTranslations.keys())]);

    return unsubscribe;
  }, [clauseKey, selectedLanguage]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowLanguageSelector(false);
      }
    };

    if (showLanguageSelector) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
    
    return undefined;
  }, [showLanguageSelector]);

  // Get the text to speak based on selected language
  const getTextToSpeak = (): string => {
    if (selectedLanguage === 'en') {
      return `${clauseData.text}. ${originalExplanation}`;
    }
    
    const translation = translations.get(selectedLanguage);
    if (translation) {
      // For translated content, we'll use the translated clause text
      // Note: We don't have translated explanations, so we'll just use the translated clause
      return translation.translatedText;
    }
    
    // Fallback to English
    return `${clauseData.text}. ${originalExplanation}`;
  };

  // Get the speech language code
  const getSpeechLanguageCode = (): string => {
    return TRANSLATION_TO_SPEECH_LANGUAGE_MAP[selectedLanguage] || 'en-US';
  };

  // Get appropriate voice gender based on language
  const getVoiceGender = (): 'MALE' | 'FEMALE' | 'NEUTRAL' => {
    return 'NEUTRAL';
  };

  // Get speaking rate based on language
  const getSpeakingRate = (langCode: string): number => {
    const rateMap: { [key: string]: number } = {
      'hi-IN': 0.8,  // Hindi - slightly slower
      'zh-CN': 0.8,  // Chinese - slightly slower
      'ja-JP': 0.8,  // Japanese - slightly slower
      'ko-KR': 0.8,  // Korean - slightly slower
      'de-DE': 0.85, // German - slightly slower
      'fr-FR': 0.9,  // French - normal
      'es-ES': 0.9,  // Spanish - normal
      'it-IT': 0.9,  // Italian - normal
      'pt-BR': 0.9,  // Portuguese - normal
      'ru-RU': 0.85, // Russian - slightly slower
      'en-US': 0.9,  // English - normal
      'en-GB': 0.9   // English - normal
    };
    return rateMap[langCode] || 0.9;
  };

  // Get language display info
  const getLanguageInfo = (langCode: string) => {
    const languageInfo: { [key: string]: { name: string; flag: string } } = {
      'en': { name: 'English', flag: '🇺🇸' },
      'es': { name: 'Spanish', flag: '🇪🇸' },
      'fr': { name: 'French', flag: '🇫🇷' },
      'de': { name: 'German', flag: '🇩🇪' },
      'it': { name: 'Italian', flag: '🇮🇹' },
      'pt': { name: 'Portuguese', flag: '🇵🇹' },
      'ru': { name: 'Russian', flag: '🇷🇺' },
      'ja': { name: 'Japanese', flag: '🇯🇵' },
      'ko': { name: 'Korean', flag: '🇰🇷' },
      'zh': { name: 'Chinese', flag: '🇨🇳' },
      'hi': { name: 'Hindi', flag: '🇮🇳' },
      'ar': { name: 'Arabic', flag: '🇸🇦' }
    };
    return languageInfo[langCode] || { name: 'English', flag: '🇺🇸' };
  };

  const currentLanguageInfo = getLanguageInfo(selectedLanguage);
  const speechLanguageCode = getSpeechLanguageCode();

  if (compact) {
    return (
      <div className={cn("relative inline-flex items-center", className)}>
        {/* Language selector for compact mode */}
        {availableLanguages.length > 1 && (
          <div className="relative mr-1" ref={dropdownRef}>
            <button
              onClick={() => setShowLanguageSelector(!showLanguageSelector)}
              className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-600 hover:bg-slate-500 text-slate-300 hover:text-white transition-all duration-200"
              title={`Audio language: ${currentLanguageInfo.name}`}
            >
              <Globe className="w-2.5 h-2.5" />
            </button>

            {showLanguageSelector && (
              <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-50 min-w-[120px]">
                {availableLanguages.map((lang) => {
                  const langInfo = getLanguageInfo(lang);
                  return (
                    <button
                      key={lang}
                      onClick={() => {
                        setSelectedLanguage(lang);
                        setShowLanguageSelector(false);
                      }}
                      className={cn(
                        "w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-slate-700 transition-colors text-xs",
                        selectedLanguage === lang && "bg-slate-700 text-blue-400"
                      )}
                    >
                      <span>{langInfo.flag}</span>
                      <span>{langInfo.name}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Audio button */}
        <button
          className={cn(
            "inline-flex items-center justify-center w-6 h-6 rounded-full",
            "bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white",
            "transition-all duration-200 hover:scale-105",
            "group relative"
          )}
          title={`Listen in ${currentLanguageInfo.name} ${currentLanguageInfo.flag}`}
        >
          <Volume2 className="w-3 h-3" />
          
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
            Listen in {currentLanguageInfo.name} {currentLanguageInfo.flag}
          </div>
          
          {/* Hidden AudioPlayer */}
          <div className="hidden">
            <AudioPlayer
              text={getTextToSpeak()}
              languageCode={speechLanguageCode}
              voiceGender={getVoiceGender()}
              speakingRate={getSpeakingRate(speechLanguageCode)}
            />
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className={cn("mt-3", className)}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Listen to explanation</span>
        </div>

        {/* Language selector for full mode */}
        {availableLanguages.length > 1 && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowLanguageSelector(!showLanguageSelector)}
              className="flex items-center space-x-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-xs transition-colors"
            >
              <Globe className="w-3 h-3" />
              <span>{currentLanguageInfo.flag}</span>
              <span className="hidden sm:inline">{currentLanguageInfo.name}</span>
            </button>

            {showLanguageSelector && (
              <div className="absolute top-full right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-50 min-w-[140px]">
                {availableLanguages.map((lang) => {
                  const langInfo = getLanguageInfo(lang);
                  return (
                    <button
                      key={lang}
                      onClick={() => {
                        setSelectedLanguage(lang);
                        setShowLanguageSelector(false);
                      }}
                      className={cn(
                        "w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-slate-700 transition-colors text-sm",
                        selectedLanguage === lang && "bg-slate-700 text-blue-400"
                      )}
                    >
                      <span>{langInfo.flag}</span>
                      <span>{langInfo.name}</span>
                      {selectedLanguage === lang && (
                        <div className="ml-auto w-2 h-2 bg-blue-400 rounded-full" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
      
      <AudioPlayer
        text={getTextToSpeak()}
        languageCode={speechLanguageCode}
        voiceGender={getVoiceGender()}
        speakingRate={getSpeakingRate(speechLanguageCode)}
        className="w-full"
      />

      {/* Language indicator */}
      <div className="mt-2 text-xs text-slate-500">
        Audio language: {currentLanguageInfo.flag} {currentLanguageInfo.name}
        {selectedLanguage !== 'en' && (
          <span className="ml-2 text-blue-400">
            (Translated content)
          </span>
        )}
      </div>
    </div>
  );
};

export default TranslationAwareAudioButton;