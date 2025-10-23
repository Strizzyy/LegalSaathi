/**
 * Service for managing user experience level preferences
 */

export type ExperienceLevel = 'beginner' | 'intermediate' | 'expert';

export interface ExperienceLevelInfo {
  level: ExperienceLevel;
  label: string;
  description: string;
  characteristics: string[];
}

class ExperienceLevelService {
  private static readonly STORAGE_KEY = 'userExperienceLevel';
  private static readonly DEFAULT_LEVEL: ExperienceLevel = 'beginner';
  
  private listeners: Set<(level: ExperienceLevel) => void> = new Set();

  /**
   * Get available experience levels with descriptions
   */
  getAvailableLevels(): ExperienceLevelInfo[] {
    return [
      {
        level: 'beginner',
        label: 'Beginner',
        description: 'New to legal documents',
        characteristics: [
          'Simple, everyday language',
          'Step-by-step explanations',
          'Practical examples and analogies',
          'Clear guidance on when to seek help'
        ]
      },
      {
        level: 'intermediate',
        label: 'Intermediate',
        description: 'Some experience with contracts',
        characteristics: [
          'Balanced technical and plain language',
          'Contextual legal explanations',
          'Risk-benefit analysis',
          'Options and alternatives'
        ]
      },
      {
        level: 'expert',
        label: 'Expert',
        description: 'Experienced with legal documents',
        characteristics: [
          'Precise legal terminology',
          'Comprehensive analysis',
          'Statutory and case law references',
          'Strategic considerations'
        ]
      }
    ];
  }

  /**
   * Get current user experience level
   */
  getCurrentLevel(): ExperienceLevel {
    try {
      const stored = localStorage.getItem(ExperienceLevelService.STORAGE_KEY);
      if (stored && this.isValidLevel(stored)) {
        return stored as ExperienceLevel;
      }
    } catch (error) {
      console.warn('Failed to read experience level from localStorage:', error);
    }
    
    return ExperienceLevelService.DEFAULT_LEVEL;
  }

  /**
   * Set user experience level
   */
  setLevel(level: ExperienceLevel): void {
    if (!this.isValidLevel(level)) {
      throw new Error(`Invalid experience level: ${level}`);
    }

    try {
      localStorage.setItem(ExperienceLevelService.STORAGE_KEY, level);
      this.notifyListeners(level);
    } catch (error) {
      console.error('Failed to save experience level to localStorage:', error);
      throw error;
    }
  }

  /**
   * Get information about a specific experience level
   */
  getLevelInfo(level: ExperienceLevel): ExperienceLevelInfo | null {
    return this.getAvailableLevels().find(info => info.level === level) || null;
  }

  /**
   * Get information about current experience level
   */
  getCurrentLevelInfo(): ExperienceLevelInfo {
    const currentLevel = this.getCurrentLevel();
    return this.getLevelInfo(currentLevel) || this.getAvailableLevels()[0];
  }

  /**
   * Check if a level string is valid
   */
  isValidLevel(level: string): level is ExperienceLevel {
    return ['beginner', 'intermediate', 'expert'].includes(level);
  }

  /**
   * Subscribe to experience level changes
   */
  subscribe(listener: (level: ExperienceLevel) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Notify all listeners of level change
   */
  private notifyListeners(level: ExperienceLevel): void {
    this.listeners.forEach(listener => {
      try {
        listener(level);
      } catch (error) {
        console.error('Error in experience level listener:', error);
      }
    });
  }

  /**
   * Reset to default level
   */
  reset(): void {
    this.setLevel(ExperienceLevelService.DEFAULT_LEVEL);
  }

  /**
   * Get experience level for API requests
   */
  getLevelForAPI(): string {
    return this.getCurrentLevel();
  }

  /**
   * Update level and return success status
   */
  updateLevel(level: string): boolean {
    if (!this.isValidLevel(level)) {
      return false;
    }

    try {
      this.setLevel(level);
      return true;
    } catch (error) {
      console.error('Failed to update experience level:', error);
      return false;
    }
  }

  /**
   * Get personalization context for the current level
   */
  getPersonalizationContext(): { experienceLevel: ExperienceLevel; levelInfo: ExperienceLevelInfo } {
    const level = this.getCurrentLevel();
    const levelInfo = this.getCurrentLevelInfo();
    
    return {
      experienceLevel: level,
      levelInfo
    };
  }
}

export const experienceLevelService = new ExperienceLevelService();
export default experienceLevelService;