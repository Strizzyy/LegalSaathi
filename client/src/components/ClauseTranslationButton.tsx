import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Loader2, ChevronDown, ChevronUp, Copy, CheckCircle } from 'lucide-react';
import { translationService, type ClauseData, type TranslatedClause } from '../services/translationService';
import { notificationService } from '../services/notificationService';

interface ClauseTranslationButtonProps {
  clauseData: ClauseData;
  className?: string;
}

export function ClauseTranslationButton({ clauseData, className = '' }: ClauseTranslationButtonProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('es');
  const [translations, setTranslations] = useState<Map<string, TranslatedClause>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [copiedLanguage, setCopiedLanguage] = useState<string | null>(null);

  const clauseKey = `${clauseData.id}_${clauseData.index}`;

  useEffect(() => {
    const unsubscribe = translationService.subscribe(() => {
      setTranslations(translationService.getClauseTranslations(clauseKey));
      setIsLoading(translationService.isTranslationLoading(clauseKey, selectedLanguage));
    });

    // Initial load
    setTranslations(translationService.getClauseTranslations(clauseKey));
    
    return unsubscribe;
  }, [clauseKey, selectedLanguage]);

  const handleTranslate = async () => {
    if (isLoading) return;

    const existingTranslation = translations.get(selectedLanguage);
    if (existingTranslation) {
      setIsExpanded(true);
      return;
    }

    const result = await translationService.translateClause(clauseData, selectedLanguage);
    if (result) {
      setIsExpanded(true);
    }
  };

  const handleCopy = async (text: string, language: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedLanguage(language);
      notificationService.success('Translation copied to clipboard');
      setTimeout(() => setCopiedLanguage(null), 2000);
    } catch (error) {
      console.error('Copy error:', error);
      notificationService.error('Failed to copy translation');
    }
  };

  const availableLanguages = translationService.getAvailableLanguages();
  const hasTranslations = translations.size > 0;
  const currentTranslation = translations.get(selectedLanguage);

  return (
    <div className={`clause-translation-container ${className}`}>
      {/* Translation Button */}
      <div className="flex items-center space-x-2 mb-2">
        <select
          value={selectedLanguage}
          onChange={(e) => setSelectedLanguage(e.target.value)}
          className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-xs focus:border-cyan-500 focus:outline-none"
        >
          {availableLanguages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.name}
            </option>
          ))}
        </select>

        <button
          onClick={handleTranslate}
          disabled={isLoading}
          className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-400 hover:to-cyan-400 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
              Translating...
            </>
          ) : (
            <>
              <Globe className="w-3 h-3 mr-1" />
              {currentTranslation ? 'View Translation' : 'Translate'}
            </>
          )}
        </button>

        {hasTranslations && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center px-2 py-1 bg-slate-600 text-slate-300 rounded hover:bg-slate-500 transition-colors text-xs"
          >
            {isExpanded ? (
              <ChevronUp className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
          </button>
        )}
      </div>

      {/* Translation Display */}
      <AnimatePresence>
        {isExpanded && hasTranslations && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="translation-display"
          >
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-4">
              {/* Side-by-side display for current translation */}
              {currentTranslation && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-white">Original (English)</h4>
                    </div>
                    <div className="bg-slate-700/50 border border-slate-600 rounded p-3">
                      <p className="text-sm text-slate-200">{clauseData.text}</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-white">
                        {translationService.getLanguageFlag(selectedLanguage)} {translationService.getLanguageName(selectedLanguage)}
                      </h4>
                      <button
                        onClick={() => handleCopy(currentTranslation.translatedText, selectedLanguage)}
                        className="inline-flex items-center px-2 py-1 text-xs bg-slate-600 text-slate-300 rounded hover:bg-slate-500 transition-colors"
                      >
                        {copiedLanguage === selectedLanguage ? (
                          <>
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3 mr-1" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
                      <p className="text-sm text-blue-100">{currentTranslation.translatedText}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* All available translations */}
              {translations.size > 1 && (
                <div>
                  <h4 className="text-sm font-medium text-white mb-2">All Translations</h4>
                  <div className="space-y-2">
                    {Array.from(translations.entries()).map(([lang, translation]) => (
                      <div key={lang} className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm">
                            {translationService.getLanguageFlag(lang)} {translationService.getLanguageName(lang)}
                          </span>
                          <span className="text-xs text-slate-400">
                            {translation.timestamp.toLocaleDateString()}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedLanguage(lang)}
                            className="text-xs text-cyan-400 hover:text-cyan-300"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleCopy(translation.translatedText, lang)}
                            className="text-xs text-slate-400 hover:text-slate-300"
                          >
                            {copiedLanguage === lang ? (
                              <CheckCircle className="w-3 h-3" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}