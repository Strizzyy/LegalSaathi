import { apiService } from './apiService';
import { notificationService } from './notificationService';

export interface ClauseData {
  id: string;
  text: string;
  index: number;
}

export interface TranslatedClause {
  clauseId: string;
  originalText: string;
  translatedText: string;
  language: string;
  timestamp: Date;
}

export interface TranslationState {
  translations: Map<string, Map<string, TranslatedClause>>;
  currentLanguage: string;
  isLoading: Set<string>;
}

export interface SupportedLanguage {
  code: string;
  name: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
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

class TranslationService {
  private state: TranslationState = {
    translations: new Map(),
    currentLanguage: 'en',
    isLoading: new Set(),
  };

  private listeners: Set<() => void> = new Set();

  constructor() {
    this.loadPersistedState();
  }

  // State management
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener());
  }

  getState(): TranslationState {
    return { ...this.state };
  }

  // Language preference persistence
  setCurrentLanguage(language: string): void {
    this.state.currentLanguage = language;
    localStorage.setItem('legalSaathi_preferredLanguage', language);
    this.notify();
  }

  getCurrentLanguage(): string {
    return this.state.currentLanguage;
  }

  private loadPersistedState(): void {
    try {
      const savedLanguage = localStorage.getItem('legalSaathi_preferredLanguage');
      if (savedLanguage) {
        this.state.currentLanguage = savedLanguage;
      }

      const savedTranslations = localStorage.getItem('legalSaathi_translations');
      if (savedTranslations) {
        const parsed = JSON.parse(savedTranslations);
        this.state.translations = new Map(
          Object.entries(parsed).map(([clauseId, translations]: [string, any]) => [
            clauseId,
            new Map(
              Object.entries(translations).map(([lang, data]: [string, any]) => [
                lang,
                {
                  ...data,
                  timestamp: new Date(data.timestamp)
                }
              ])
            )
          ])
        );
      }
    } catch (error) {
      console.error('Failed to load persisted translation state:', error);
    }
  }

  private persistState(): void {
    try {
      const translationsObj: Record<string, Record<string, any>> = {};
      
      this.state.translations.forEach((clauseTranslations, clauseId) => {
        translationsObj[clauseId] = {};
        clauseTranslations.forEach((translation, lang) => {
          translationsObj[clauseId][lang] = {
            ...translation,
            timestamp: translation.timestamp.toISOString()
          };
        });
      });

      localStorage.setItem('legalSaathi_translations', JSON.stringify(translationsObj));
    } catch (error) {
      console.error('Failed to persist translation state:', error);
    }
  }

  // Translation methods
  async translateClause(clauseData: ClauseData, targetLanguage: string): Promise<TranslatedClause | null> {
    const clauseKey = `${clauseData.id}_${clauseData.index}`;
    
    // Check if translation already exists
    const existing = this.getTranslation(clauseKey, targetLanguage);
    if (existing) {
      return existing;
    }

    // Check if already loading
    if (this.state.isLoading.has(`${clauseKey}_${targetLanguage}`)) {
      return null;
    }

    this.state.isLoading.add(`${clauseKey}_${targetLanguage}`);
    this.notify();

    try {
      const result = await apiService.translateText(clauseData.text, targetLanguage, 'en');
      
      if (result.success && result.translated_text) {
        const translation: TranslatedClause = {
          clauseId: clauseKey,
          originalText: clauseData.text,
          translatedText: result.translated_text,
          language: targetLanguage,
          timestamp: new Date()
        };

        this.storeTranslation(translation);
        notificationService.success(`Clause translated to ${this.getLanguageName(targetLanguage)}`);
        return translation;
      } else {
        notificationService.error('Translation failed. Please try again.');
        return null;
      }
    } catch (error) {
      console.error('Translation error:', error);
      notificationService.error('Translation service unavailable');
      return null;
    } finally {
      this.state.isLoading.delete(`${clauseKey}_${targetLanguage}`);
      this.notify();
    }
  }

  async translateMultipleClauses(clauses: ClauseData[], targetLanguage: string): Promise<TranslatedClause[]> {
    const results: TranslatedClause[] = [];
    
    for (const clause of clauses) {
      const translation = await this.translateClause(clause, targetLanguage);
      if (translation) {
        results.push(translation);
      }
    }

    return results;
  }

  private storeTranslation(translation: TranslatedClause): void {
    if (!this.state.translations.has(translation.clauseId)) {
      this.state.translations.set(translation.clauseId, new Map());
    }
    
    const clauseTranslations = this.state.translations.get(translation.clauseId)!;
    clauseTranslations.set(translation.language, translation);
    
    this.persistState();
    this.notify();
  }

  getTranslation(clauseId: string, language: string): TranslatedClause | null {
    const clauseTranslations = this.state.translations.get(clauseId);
    return clauseTranslations?.get(language) || null;
  }

  getClauseTranslations(clauseId: string): Map<string, TranslatedClause> {
    return this.state.translations.get(clauseId) || new Map();
  }

  isTranslationLoading(clauseId: string, language: string): boolean {
    return this.state.isLoading.has(`${clauseId}_${language}`);
  }

  // Utility methods
  getAvailableLanguages(): SupportedLanguage[] {
    return SUPPORTED_LANGUAGES;
  }

  getLanguageName(code: string): string {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === code)?.name || code;
  }

  getLanguageFlag(code: string): string {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === code)?.flag || '🌐';
  }

  // Clear methods
  clearClauseTranslations(clauseId: string): void {
    this.state.translations.delete(clauseId);
    this.persistState();
    this.notify();
  }

  clearAllTranslations(): void {
    this.state.translations.clear();
    localStorage.removeItem('legalSaathi_translations');
    this.notify();
  }
}

export const translationService = new TranslationService();
export default translationService;