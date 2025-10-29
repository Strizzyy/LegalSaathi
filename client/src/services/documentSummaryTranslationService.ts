import { apiService } from './apiService';
import { notificationService } from './notificationService';
import { backendReadinessService } from './backendReadinessService';

export interface DocumentSummaryContent {
  what_this_document_means?: string;
  key_points?: string[];
  risk_assessment?: string;
  what_you_should_do?: string[];
  simple_explanation?: string;

  // Alternative field names for compatibility
  jargonFreeVersion?: string;
  keyPoints?: string[];
  riskSummary?: string;
  recommendations?: string[];
  simplifiedExplanation?: string;
}

export interface TranslatedDocumentSummary {
  success: boolean;
  translated_summary?: DocumentSummaryContent;
  source_language: string;
  target_language: string;
  language_name: string;
  sections_translated: number;
  overall_confidence: number;
  failed_sections: number;
  warnings?: string[];
  error_message?: string;
  timestamp: string;
}

export interface SupportedLanguage {
  code: string;
  name: string;
  native_name: string;
  flag: string;
}

export interface EnhancedSupportedLanguagesResponse {
  success: boolean;
  languages: SupportedLanguage[];
  total_count: number;
  features: {
    document_summary_translation: boolean;
    section_specific_context: boolean;
    legal_terminology_preservation: boolean;
    confidence_scoring: boolean;
    translation_caching: boolean;
  };
  rate_limits: {
    requests_per_minute: number;
    daily_request_limit: number;
    daily_character_limit: number;
  };
}

export interface TranslationState {
  currentLanguage: string;
  translatedSummaries: Map<string, TranslatedDocumentSummary>;
  isTranslating: boolean;
  translationProgress: Map<string, boolean>; // section -> isTranslating
  supportedLanguages: SupportedLanguage[];
  lastError?: string;
}

class DocumentSummaryTranslationService {
  private state: TranslationState = {
    currentLanguage: 'en',
    translatedSummaries: new Map(),
    isTranslating: false,
    translationProgress: new Map(),
    supportedLanguages: []
  };

  private listeners: Set<() => void> = new Set();
  private cache: Map<string, TranslatedDocumentSummary> = new Map();
  private cacheExpiry: Map<string, number> = new Map();
  private readonly CACHE_TTL = 3600000; // 1 hour in milliseconds

  constructor() {
    this.loadPersistedState();
    // Load default languages immediately
    this.state.supportedLanguages = this.getDefaultLanguages();
    console.log('DocumentSummaryTranslationService initialized with', this.state.supportedLanguages.length, 'default languages');

    // Wait for backend readiness before loading enhanced languages
    this.waitForBackendAndLoadLanguages();
  }

  private async waitForBackendAndLoadLanguages(): Promise<void> {
    // Wait for backend to be ready
    const isReady = await backendReadinessService.waitForBackend(60000); // 1 minute timeout
    
    if (isReady) {
      console.log('✅ Backend ready, loading enhanced languages...');
      await this.loadSupportedLanguages();
    } else {
      console.log('⚠️ Backend not ready, using default languages');
      notificationService.warning('Using default languages. Enhanced features may be limited.', { duration: 5000 });
    }
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
    localStorage.setItem('legalSaathi_summaryLanguage', language);
    this.notify();
  }

  getCurrentLanguage(): string {
    return this.state.currentLanguage;
  }

  private loadPersistedState(): void {
    try {
      const savedLanguage = localStorage.getItem('legalSaathi_summaryLanguage');
      if (savedLanguage) {
        this.state.currentLanguage = savedLanguage;
      }

      const savedTranslations = localStorage.getItem('legalSaathi_summaryTranslations');
      if (savedTranslations) {
        const parsed = JSON.parse(savedTranslations);
        this.state.translatedSummaries = new Map(Object.entries(parsed));
      }
    } catch (error) {
      console.error('Failed to load persisted summary translation state:', error);
    }
  }

  private persistState(): void {
    try {
      const translationsObj: Record<string, any> = {};
      this.state.translatedSummaries.forEach((translation, key) => {
        translationsObj[key] = translation;
      });

      localStorage.setItem('legalSaathi_summaryTranslations', JSON.stringify(translationsObj));
    } catch (error) {
      console.error('Failed to persist summary translation state:', error);
    }
  }

  // Load supported languages (now called after backend is ready)
  private async loadSupportedLanguages(): Promise<void> {
    try {
      console.log('🔄 Loading enhanced languages from API...');
      
      const response = await apiService.get('/api/translate/languages/enhanced');
      const data = response.data;
      
      if (data && data.success && data.languages && data.languages.length > 0) {
        console.log(`✅ Loaded enhanced languages from API:`, data.languages.length);
        this.state.supportedLanguages = data.languages;
        notificationService.success('Translation service ready!', { duration: 2000 });
        this.notify();
      } else {
        console.log(`⚠️ API response invalid, using default languages`);
        notificationService.warning('Using default languages. Some features may be limited.', { duration: 3000 });
      }
    } catch (error: any) {
      console.error(`❌ Failed to load supported languages from API:`, error);
      notificationService.warning('Could not load enhanced languages. Using defaults.', { duration: 3000 });
    }
  }

  private getDefaultLanguages(): SupportedLanguage[] {
    return [
      { code: 'en', name: 'English', native_name: 'English', flag: '🇺🇸' },
      { code: 'es', name: 'Spanish', native_name: 'Español', flag: '🇪🇸' },
      { code: 'fr', name: 'French', native_name: 'Français', flag: '🇫🇷' },
      { code: 'de', name: 'German', native_name: 'Deutsch', flag: '🇩🇪' },
      { code: 'it', name: 'Italian', native_name: 'Italiano', flag: '🇮🇹' },
      { code: 'pt', name: 'Portuguese', native_name: 'Português', flag: '🇵🇹' },
      { code: 'ru', name: 'Russian', native_name: 'Русский', flag: '🇷🇺' },
      { code: 'ja', name: 'Japanese', native_name: '日本語', flag: '🇯🇵' },
      { code: 'ko', name: 'Korean', native_name: '한국어', flag: '🇰🇷' },
      { code: 'zh', name: 'Chinese', native_name: '中文', flag: '🇨🇳' },
      { code: 'ar', name: 'Arabic', native_name: 'العربية', flag: '🇸🇦' },
      { code: 'hi', name: 'Hindi', native_name: 'हिंदी', flag: '🇮🇳' },
      { code: 'nl', name: 'Dutch', native_name: 'Nederlands', flag: '🇳🇱' },
      { code: 'sv', name: 'Swedish', native_name: 'Svenska', flag: '🇸🇪' },
      { code: 'da', name: 'Danish', native_name: 'Dansk', flag: '🇩🇰' },
      { code: 'no', name: 'Norwegian', native_name: 'Norsk', flag: '🇳🇴' },
      { code: 'fi', name: 'Finnish', native_name: 'Suomi', flag: '🇫🇮' },
      { code: 'pl', name: 'Polish', native_name: 'Polski', flag: '🇵🇱' },
      { code: 'cs', name: 'Czech', native_name: 'Čeština', flag: '🇨🇿' },
      { code: 'hu', name: 'Hungarian', native_name: 'Magyar', flag: '🇭🇺' },
      { code: 'tr', name: 'Turkish', native_name: 'Türkçe', flag: '🇹🇷' },
      { code: 'he', name: 'Hebrew', native_name: 'עברית', flag: '🇮🇱' },
      { code: 'th', name: 'Thai', native_name: 'ไทย', flag: '🇹🇭' },
      { code: 'vi', name: 'Vietnamese', native_name: 'Tiếng Việt', flag: '🇻🇳' },
      { code: 'id', name: 'Indonesian', native_name: 'Bahasa Indonesia', flag: '🇮🇩' },
      { code: 'ms', name: 'Malay', native_name: 'Bahasa Melayu', flag: '🇲🇾' },
      { code: 'tl', name: 'Filipino', native_name: 'Tagalog', flag: '🇵🇭' },
      { code: 'bn', name: 'Bengali', native_name: 'বাংলা', flag: '🇧🇩' },
      { code: 'ta', name: 'Tamil', native_name: 'தமிழ்', flag: '🇮🇳' },
      { code: 'te', name: 'Telugu', native_name: 'తెలుగు', flag: '🇮🇳' },
      { code: 'ur', name: 'Urdu', native_name: 'اردو', flag: '🇵🇰' }
    ];
  }

  // Cache management
  private generateCacheKey(summaryContent: DocumentSummaryContent, targetLanguage: string): string {
    const contentStr = JSON.stringify(summaryContent);
    // Use a simple hash instead of btoa to avoid Unicode issues
    let hash = 0;
    for (let i = 0; i < contentStr.length; i++) {
      const char = contentStr.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return `summary_${targetLanguage}_${Math.abs(hash).toString(36).slice(0, 10)}`;
  }

  private getCachedTranslation(cacheKey: string): TranslatedDocumentSummary | null {
    const cached = this.cache.get(cacheKey);
    const expiry = this.cacheExpiry.get(cacheKey);

    if (cached && expiry && Date.now() < expiry) {
      return cached;
    }

    // Remove expired cache
    if (cached) {
      this.cache.delete(cacheKey);
      this.cacheExpiry.delete(cacheKey);
    }

    return null;
  }

  private setCachedTranslation(cacheKey: string, translation: TranslatedDocumentSummary): void {
    this.cache.set(cacheKey, translation);
    this.cacheExpiry.set(cacheKey, Date.now() + this.CACHE_TTL);
  }

  // Backend health check
  private async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await apiService.get('/api/translate/languages/enhanced');
      return response.data?.success === true;
    } catch (error) {
      return false;
    }
  }

  // Translation methods
  async translateDocumentSummary(
    summaryContent: DocumentSummaryContent,
    targetLanguage: string,
    sourceLanguage: string = 'en',
    userId?: string
  ): Promise<TranslatedDocumentSummary | null> {
    // Check if target language is same as source
    if (targetLanguage === sourceLanguage) {
      return {
        success: true,
        translated_summary: summaryContent,
        source_language: sourceLanguage,
        target_language: targetLanguage,
        language_name: this.getLanguageName(targetLanguage),
        sections_translated: 0,
        overall_confidence: 1.0,
        failed_sections: 0,
        timestamp: new Date().toISOString()
      };
    }

    // Check cache first
    const cacheKey = this.generateCacheKey(summaryContent, targetLanguage);
    const cached = this.getCachedTranslation(cacheKey);
    if (cached) {
      console.log('Returning cached summary translation');
      return cached;
    }

    // Check if already translating
    if (this.state.isTranslating) {
      console.log('Translation already in progress');
      return null;
    }

    this.state.isTranslating = true;
    delete this.state.lastError;
    this.notify();

    try {
      const apiResponse = await apiService.post('/api/translate/document-summary', {
        summary_content: summaryContent,
        target_language: targetLanguage,
        source_language: sourceLanguage,
        preserve_formatting: true,
        user_id: userId || 'anonymous'
      });

      const response = apiResponse.data;
      console.log('Translation API response:', response);

      if (response && response.success && response.translated_summary) {
        // Cache the result
        this.setCachedTranslation(cacheKey, response);

        // Store in state
        this.state.translatedSummaries.set(targetLanguage, response);
        this.persistState();

        notificationService.success(`Document summary translated to ${response.language_name}`);
        return response;
      } else {
        const errorMsg = response?.error_message || 'Translation failed';
        this.state.lastError = errorMsg;
        notificationService.error(errorMsg);
        return null;
      }
    } catch (error: any) {
      console.error('Document summary translation error:', error);

      let errorMessage = 'Translation service unavailable';
      const isConnectionError = error.code === 'ECONNREFUSED' || error.message?.includes('ECONNREFUSED');

      if (isConnectionError) {
        errorMessage = 'Backend is still starting up. Please wait a moment and try again.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Rate limit exceeded. Please wait before translating again.';
      } else if (error.response?.status === 503) {
        errorMessage = 'Daily translation limit exceeded. Please try again tomorrow.';
      }

      this.state.lastError = errorMessage;
      notificationService.error(errorMessage);
      return null;
    } finally {
      this.state.isTranslating = false;
      this.notify();
    }
  }

  async translateSummarySection(
    sectionContent: string,
    sectionType: string,
    targetLanguage: string,
    sourceLanguage: string = 'en',
    userId?: string
  ): Promise<any> {
    // Set section translation progress
    this.state.translationProgress.set(sectionType, true);
    this.notify();

    try {
      const apiResponse = await apiService.post('/api/translate/summary-section', {
        section_content: sectionContent,
        section_type: sectionType,
        target_language: targetLanguage,
        source_language: sourceLanguage,
        user_id: userId || 'anonymous'
      });

      const response = apiResponse.data;
      console.log('Section translation API response:', response);

      if (response && response.success && response.translated_text) {
        return response;
      } else {
        throw new Error(response?.error_message || 'Section translation failed');
      }
    } catch (error: any) {
      console.error(`Section translation error for ${sectionType}:`, error);
      throw error;
    } finally {
      this.state.translationProgress.set(sectionType, false);
      this.notify();
    }
  }

  // Real-time translation system
  async translateSummaryInRealTime(
    summaryContent: DocumentSummaryContent,
    targetLanguage: string,
    _onProgress?: (progress: { section: string; completed: boolean }) => void
  ): Promise<TranslatedDocumentSummary | null> {
    if (targetLanguage === 'en') {
      return {
        success: true,
        translated_summary: summaryContent,
        source_language: 'en',
        target_language: 'en',
        language_name: 'English',
        sections_translated: 0,
        overall_confidence: 1.0,
        failed_sections: 0,
        timestamp: new Date().toISOString()
      };
    }

    // Use the main translation method which handles caching and state
    return await this.translateDocumentSummary(summaryContent, targetLanguage, 'en');
  }

  // Public health check method
  async isBackendReady(): Promise<boolean> {
    return await this.checkBackendHealth();
  }

  // Utility methods
  getSupportedLanguages(): SupportedLanguage[] {
    return this.state.supportedLanguages;
  }

  getLanguageName(code: string): string {
    const language = this.state.supportedLanguages.find(lang => lang.code === code);
    return language?.name || code;
  }

  getLanguageNativeName(code: string): string {
    const language = this.state.supportedLanguages.find(lang => lang.code === code);
    return language?.native_name || code;
  }

  getLanguageFlag(code: string): string {
    const language = this.state.supportedLanguages.find(lang => lang.code === code);
    return language?.flag || '🌐';
  }

  isTranslating(): boolean {
    return this.state.isTranslating;
  }

  isSectionTranslating(sectionType: string): boolean {
    return this.state.translationProgress.get(sectionType) || false;
  }

  getTranslatedSummary(language: string): TranslatedDocumentSummary | null {
    return this.state.translatedSummaries.get(language) || null;
  }

  getLastError(): string | undefined {
    return this.state.lastError;
  }

  // Clear methods
  clearTranslations(): void {
    this.state.translatedSummaries.clear();
    this.cache.clear();
    this.cacheExpiry.clear();
    localStorage.removeItem('legalSaathi_summaryTranslations');
    this.notify();
  }

  clearError(): void {
    delete this.state.lastError;
    this.notify();
  }
}

export const documentSummaryTranslationService = new DocumentSummaryTranslationService();
export default documentSummaryTranslationService;