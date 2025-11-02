import { useState } from 'react';
import { motion } from 'framer-motion';
import { Globe, Loader2, Copy, CheckCircle } from 'lucide-react';
import { Modal } from './Modal';
import { apiService } from '../services/apiService';
import { notificationService } from '../services/notificationService';

interface TranslationModalProps {
  isOpen: boolean;
  onClose: () => void;
  originalText: string;
  title: string;
}

const SUPPORTED_LANGUAGES = [
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
];

export function TranslationModal({ isOpen, onClose, originalText, title }: TranslationModalProps) {
  const [selectedLanguage, setSelectedLanguage] = useState('es');
  const [translatedText, setTranslatedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleTranslate = async () => {
    if (!selectedLanguage || isLoading) return;

    setIsLoading(true);
    try {
      const result = await apiService.translateText(originalText, selectedLanguage, 'en');
      
      if (result.success && result.translated_text) {
        setTranslatedText(result.translated_text);
        notificationService.translationSuccess();
      } else {
        notificationService.translationError();
      }
    } catch (error) {
      console.error('Translation error:', error);
      notificationService.translationError();
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!translatedText) return;

    try {
      await navigator.clipboard.writeText(translatedText);
      setCopied(true);
      notificationService.copySuccess();
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy error:', error);
      notificationService.copyError();
    }
  };

  const selectedLang = SUPPORTED_LANGUAGES.find(lang => lang.code === selectedLanguage);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Translate: ${title}`} maxWidth="xl">
      <div className="space-y-6">
        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-white mb-3">
            <Globe className="w-4 h-4 inline mr-2" />
            Select Target Language
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {SUPPORTED_LANGUAGES.map((language) => (
              <button
                key={language.code}
                onClick={() => setSelectedLanguage(language.code)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedLanguage === language.code
                    ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                    : 'border-slate-600 bg-slate-700/50 text-slate-300 hover:border-slate-500'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{language.flag}</span>
                  <span className="text-sm font-medium">{language.name}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Original Text */}
        <div>
          <label className="block text-sm font-medium text-white mb-3 flex items-center">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
            Original Text (English)
          </label>
          <div className="bg-gradient-to-r from-slate-700/60 to-slate-600/60 border border-slate-500/50 rounded-xl p-6 max-h-40 overflow-y-auto backdrop-blur-sm">
            <div className="prose prose-invert max-w-none">
              <div className="text-slate-300 leading-relaxed space-y-3">
                {originalText.split('\n\n').map((paragraph, index) => (
                  <p key={index} className="text-sm leading-7 mb-3 last:mb-0">
                    {paragraph.trim()}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Translate Button */}
        <div className="flex justify-center">
          <button
            onClick={handleTranslate}
            disabled={isLoading}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Translating...
              </>
            ) : (
              <>
                <Globe className="w-4 h-4 mr-2" />
                Translate to {selectedLang?.name}
              </>
            )}
          </button>
        </div>

        {/* Translated Text */}
        {translatedText && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-white flex items-center">
                <Globe className="w-4 h-4 mr-2 text-cyan-400" />
                Translated Text ({selectedLang?.name})
              </label>
              <button
                onClick={handleCopy}
                className="inline-flex items-center px-3 py-2 text-xs bg-gradient-to-r from-slate-700 to-slate-600 text-slate-300 rounded-lg hover:from-slate-600 hover:to-slate-500 transition-all duration-300 border border-slate-600"
              >
                {copied ? (
                  <>
                    <CheckCircle className="w-3 h-3 mr-1 text-green-400" />
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
            <div className="bg-gradient-to-r from-slate-700/60 to-slate-600/60 border border-slate-500/50 rounded-xl p-6 max-h-60 overflow-y-auto backdrop-blur-sm">
              <div className="prose prose-invert max-w-none">
                <div className="text-slate-100 leading-relaxed space-y-4">
                  {translatedText.split('\n\n').map((paragraph, index) => (
                    <p key={index} className="text-sm leading-7 mb-4 last:mb-0">
                      {paragraph.trim()}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </Modal>
  );
}

export default TranslationModal;