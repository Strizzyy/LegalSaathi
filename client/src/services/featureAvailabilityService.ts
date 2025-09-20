/**
 * Service to manage feature availability and graceful degradation
 */

interface FeatureStatus {
  available: boolean;
  lastChecked: Date;
  errorCount: number;
  fallbackMessage?: string | undefined;
}

class FeatureAvailabilityService {
  private features: Map<string, FeatureStatus> = new Map();
  private maxErrorCount = 3;

  constructor() {
    this.initializeFeatures();
  }

  private initializeFeatures() {
    const defaultFeatures = [
      'export_pdf',
      'export_word', 
      'translation',
      'ai_chat',
      'human_support',
      'document_comparison',
      'nl_analysis',
      'clause_summary'
    ];

    defaultFeatures.forEach(feature => {
      this.features.set(feature, {
        available: true,
        lastChecked: new Date(),
        errorCount: 0
      });
    });
  }

  isFeatureAvailable(featureName: string): boolean {
    const feature = this.features.get(featureName);
    return feature ? feature.available : false;
  }

  recordFeatureError(featureName: string, error?: Error) {
    const feature = this.features.get(featureName);
    if (!feature) return;

    feature.errorCount++;
    feature.lastChecked = new Date();

    // Disable feature if too many errors
    if (feature.errorCount >= this.maxErrorCount) {
      feature.available = false;
      feature.fallbackMessage = this.getFallbackMessage(featureName, error);
    }

    this.features.set(featureName, feature);
  }

  recordFeatureSuccess(featureName: string) {
    const feature = this.features.get(featureName);
    if (!feature) return;

    feature.errorCount = 0;
    feature.available = true;
    feature.lastChecked = new Date();
    feature.fallbackMessage = undefined;

    this.features.set(featureName, feature);
  }

  getFallbackMessage(featureName: string, _error?: Error): string {
    const fallbackMessages: Record<string, string> = {
      'export_pdf': 'PDF export is temporarily unavailable. You can copy the results to clipboard or print the page instead.',
      'export_word': 'Word export is temporarily unavailable. You can copy the results to clipboard or use PDF export instead.',
      'translation': 'Translation service is temporarily unavailable. Please try again later or contact support.',
      'ai_chat': 'AI chat is temporarily unavailable. You can contact human support for assistance.',
      'human_support': 'Human support system is temporarily unavailable. Please try again later or contact us directly.',
      'document_comparison': 'Document comparison feature is temporarily unavailable. Please analyze documents individually.',
      'nl_analysis': 'Advanced NL analysis is temporarily unavailable. Basic analysis results are still available.',
      'clause_summary': 'Clause summary generation is temporarily unavailable. You can view the detailed analysis instead.'
    };

    return fallbackMessages[featureName] || 'This feature is temporarily unavailable. Please try again later.';
  }

  getFeatureStatus(featureName: string): FeatureStatus | null {
    return this.features.get(featureName) || null;
  }

  getAllFeatureStatuses(): Record<string, FeatureStatus> {
    const statuses: Record<string, FeatureStatus> = {};
    this.features.forEach((status, name) => {
      statuses[name] = status;
    });
    return statuses;
  }

  resetFeature(featureName: string) {
    const feature = this.features.get(featureName);
    if (!feature) return;

    feature.available = true;
    feature.errorCount = 0;
    feature.fallbackMessage = undefined;
    feature.lastChecked = new Date();

    this.features.set(featureName, feature);
  }

  // Check if critical features are available
  areCriticalFeaturesAvailable(): boolean {
    const criticalFeatures = ['translation', 'ai_chat'];
    return criticalFeatures.every(feature => this.isFeatureAvailable(feature));
  }

  // Get degraded mode message
  getDegradedModeMessage(): string {
    const unavailableFeatures = Array.from(this.features.entries())
      .filter(([_, status]) => !status.available)
      .map(([name, _]) => name);

    if (unavailableFeatures.length === 0) {
      return '';
    }

    return `Some features are temporarily unavailable: ${unavailableFeatures.join(', ')}. Core analysis functionality remains available.`;
  }
}

export const featureAvailabilityService = new FeatureAvailabilityService();
export default featureAvailabilityService;