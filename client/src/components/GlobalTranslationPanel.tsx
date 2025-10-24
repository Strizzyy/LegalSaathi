import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Languages, 
  ChevronDown, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Globe,
  Zap,
  X
} from 'lucide-react';
import { 
  documentSummaryTranslationService, 
  type SupportedLanguage,
  type DocumentSummaryContent
} from '../services/documentSummaryTranslationService';

interface GlobalTranslationPanelProps {
  summaryContent: DocumentSummaryContent;
  onTranslationComplete: (translatedSummary: DocumentSummaryContent, language: string) => void;
  className?: string;
}

export function GlobalTranslationPanel({
  summaryContent,
  onTranslationComplete,
  className = ''
}: GlobalTranslationPanelProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>([]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [lastError, setLastError] = useState<string | undefined>();
  const [translationStats, setTranslationStats] = useState<{
    sectionsTranslated: number;
    confidence: number;
    failedSections: number;
  } | null>(null);
  const [showLoadingModal, setShowLoadingModal] = useState(false);

  // Subscribe to translation service state
  useEffect(() => {
    const unsubscribe = documentSummaryTranslationService.subscribe(() => {
      const state = documentSummaryTranslationService.getState();
      console.log('Translation service state updated:', {
        languageCount: state.supportedLanguages.length,
        currentLanguage: state.currentLanguage,
        isTranslating: state.isTranslating
      });
      setSupportedLanguages(state.supportedLanguages);
      setIsTranslating(state.isTranslating);
      setLastError(state.lastError);
    });

    // Initialize with current state
    const state = documentSummaryTranslationService.getState();
    console.log('Initial translation service state:', {
      languageCount: state.supportedLanguages.length,
      currentLanguage: state.currentLanguage
    });
    setSupportedLanguages(state.supportedLanguages);
    setSelectedLanguage(state.currentLanguage);
    setIsTranslating(state.isTranslating);

    return unsubscribe;
  }, []);

  const handleLanguageSelect = async (languageCode: string) => {
    if (languageCode === selectedLanguage) {
      setIsDropdownOpen(false);
      return;
    }

    setSelectedLanguage(languageCode);
    setIsDropdownOpen(false);
    setLastError(undefined);
    setTranslationStats(null);

    // Update service state
    documentSummaryTranslationService.setCurrentLanguage(languageCode);

    // If English is selected, return original content
    if (languageCode === 'en') {
      onTranslationComplete(summaryContent, languageCode);
      return;
    }

    // Show loading modal
    setShowLoadingModal(true);

    // Start translation for all sections
    try {
      const result = await documentSummaryTranslationService.translateDocumentSummary(
        summaryContent,
        languageCode,
        'en'
      );

      if (result && result.success && result.translated_summary) {
        onTranslationComplete(result.translated_summary, languageCode);
        setTranslationStats({
          sectionsTranslated: result.sections_translated,
          confidence: result.overall_confidence,
          failedSections: result.failed_sections
        });
      }
    } catch (error) {
      console.error('Translation failed:', error);
      setLastError('Translation failed');
    } finally {
      // Hide loading modal
      setShowLoadingModal(false);
    }
  };

  const getSelectedLanguage = () => {
    return supportedLanguages.find(lang => lang.code === selectedLanguage) || 
           { code: 'en', name: 'English', native_name: 'English', flag: '🇺🇸' };
  };

  const getTranslationStatusIcon = () => {
    if (isTranslating) {
      return <Loader2 className="w-4 h-4 animate-spin text-blue-400" />;
    }
    if (lastError) {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    if (translationStats && translationStats.sectionsTranslated > 0) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    return <Languages className="w-4 h-4 text-slate-400" />;
  };

  const getTranslationStatusText = () => {
    if (isTranslating) {
      return 'Translating all sections...';
    }
    if (lastError) {
      return 'Translation failed';
    }
    if (translationStats && translationStats.sectionsTranslated > 0) {
      return `${translationStats.sectionsTranslated} sections translated`;
    }
    return 'Select language to translate all sections';
  };

  return (
    <div className={`global-translation-panel ${className}`}>
      <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Languages className="w-5 h-5 text-blue-400" />
            <span className="text-white font-medium">Translate Document Summary</span>
          </div>
          <div className="text-xs text-slate-400">
            All sections will be translated
          </div>
        </div>

        <div className="relative">
          {/* Language Selection Dropdown */}
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            disabled={isTranslating}
            className="w-full inline-flex items-center justify-between space-x-3 px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center space-x-3">
              {getTranslationStatusIcon()}
              <span className="text-2xl">{getSelectedLanguage().flag}</span>
              <div className="text-left">
                <div className="text-white font-medium">{getSelectedLanguage().native_name}</div>
                <div className="text-xs text-slate-400">{getTranslationStatusText()}</div>
              </div>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto"
              >
                <div className="p-2">
                  <div className="text-xs text-slate-400 px-3 py-2 border-b border-slate-700 mb-2">
                    <div className="flex items-center space-x-2">
                      <Globe className="w-3 h-3" />
                      <span>{supportedLanguages.length} languages supported</span>
                    </div>
                  </div>
                  
                  {supportedLanguages.map((language) => (
                    <button
                      key={language.code}
                      onClick={() => handleLanguageSelect(language.code)}
                      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                        selectedLanguage === language.code
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'hover:bg-slate-700 text-slate-300'
                      }`}
                    >
                      <span className="text-xl">{language.flag}</span>
                      <div className="text-left flex-1">
                        <div className="font-medium">{language.native_name}</div>
                        <div className="text-xs text-slate-400">{language.name}</div>
                      </div>
                      {selectedLanguage === language.code && (
                        <CheckCircle className="w-4 h-4 text-blue-400" />
                      )}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Translation Status */}
        <AnimatePresence>
          {(isTranslating || lastError || translationStats) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3"
            >
              {/* Translation Progress */}
              {isTranslating && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                    <span className="text-blue-400 font-medium">Translating All Summary Sections</span>
                  </div>
                  <div className="mt-2 text-xs text-blue-300">
                    Please wait while we translate all sections with legal context preservation...
                  </div>
                </div>
              )}

              {/* Translation Error */}
              {lastError && !isTranslating && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-red-400" />
                    <span className="text-red-400 font-medium">Translation Failed</span>
                  </div>
                  <p className="text-red-300 text-sm mt-1">{lastError}</p>
                </div>
              )}

              {/* Translation Success Stats */}
              {translationStats && !isTranslating && !lastError && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 font-medium">Translation Complete</span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-white font-semibold">{translationStats.sectionsTranslated}</div>
                      <div className="text-slate-400">Sections</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{Math.round(translationStats.confidence * 100)}%</div>
                      <div className="text-slate-400">Confidence</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{translationStats.failedSections}</div>
                      <div className="text-slate-400">Failed</div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Features Info */}
        <div className="mt-3 flex items-center space-x-2 text-xs text-slate-400">
          <Zap className="w-3 h-3" />
          <span>Legal context preserved • 1-hour caching • Rate limited</span>
        </div>
      </div>

      {/* Loading Modal */}
      <AnimatePresence>
        {showLoadingModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={() => setShowLoadingModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-8 max-w-md mx-4 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center">
                {/* Close Button */}
                <button
                  onClick={() => setShowLoadingModal(false)}
                  className="absolute top-4 right-4 p-1 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* Loading Animation */}
                <div className="mb-6">
                  <div className="relative">
                    <div className="w-16 h-16 mx-auto mb-4 relative">
                      <Loader2 className="w-16 h-16 text-blue-400 animate-spin" />
                      <Languages className="w-8 h-8 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                    </div>
                  </div>
                </div>

                {/* Loading Text */}
                <div className="space-y-3">
                  <h3 className="text-xl font-bold text-white">Translating Document Summary</h3>
                  <p className="text-slate-300">
                    Translating all sections to <span className="font-semibold text-blue-400">{getSelectedLanguage().native_name}</span>
                  </p>
                  
                  {/* Progress Steps */}
                  <div className="mt-6 space-y-2 text-sm text-slate-400">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      <span>Preserving legal context and terminology</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse delay-300"></div>
                      <span>Translating all summary sections</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-700"></div>
                      <span>Ensuring translation quality</span>
                    </div>
                  </div>

                  {/* Estimated Time */}
                  <div className="mt-4 text-xs text-slate-500">
                    This usually takes 10-30 seconds
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default GlobalTranslationPanel;