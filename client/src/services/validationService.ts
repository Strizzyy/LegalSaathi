export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

class ValidationService {
  validateField(value: any, rules: ValidationRule, fieldName: string): string | null {
    // Required validation
    if (rules.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
      return `${fieldName} is required`;
    }

    // Skip other validations if value is empty and not required
    if (!value || (typeof value === 'string' && value.trim() === '')) {
      return null;
    }

    // String-specific validations
    if (typeof value === 'string') {
      // Min length validation
      if (rules.minLength && value.length < rules.minLength) {
        return `${fieldName} must be at least ${rules.minLength} characters`;
      }

      // Max length validation
      if (rules.maxLength && value.length > rules.maxLength) {
        return `${fieldName} must not exceed ${rules.maxLength} characters`;
      }

      // Pattern validation
      if (rules.pattern && !rules.pattern.test(value)) {
        return `${fieldName} format is invalid`;
      }
    }

    // Custom validation
    if (rules.custom) {
      return rules.custom(value);
    }

    return null;
  }

  validateForm(data: Record<string, any>, rules: Record<string, ValidationRule>): ValidationResult {
    const errors: Record<string, string> = {};

    Object.entries(rules).forEach(([fieldName, rule]) => {
      const value = data[fieldName];
      const error = this.validateField(value, rule, fieldName);
      
      if (error) {
        errors[fieldName] = error;
      }
    });

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    };
  }

  // Document upload specific validations
  validateDocumentUpload(formData: FormData): ValidationResult {
    const documentText = formData.get('document_text') as string;
    const documentFile = formData.get('document_file') as File;
    const expertiseLevel = formData.get('expertise_level') as string;

    const rules: Record<string, ValidationRule> = {
      documentContent: {
        required: true,
        custom: (_value) => {
          // Either file or text must be provided
          if (!documentFile && (!documentText || documentText.trim().length < 100)) {
            return 'Please provide a document file or text (minimum 100 characters)';
          }
          return null;
        }
      },
      documentText: {
        maxLength: 50000,
        custom: (value) => {
          if (value && value.length > 0 && value.length < 100) {
            return 'Document text must be at least 100 characters';
          }
          return null;
        }
      },
      documentFile: {
        custom: (value) => {
          if (value && value instanceof File) {
            // File size validation (10MB)
            if (value.size > 10 * 1024 * 1024) {
              return 'File size must be less than 10MB';
            }
            
            // File type validation
            const allowedTypes = ['application/pdf', 'text/plain'];
            if (!allowedTypes.includes(value.type)) {
              return 'Only PDF and text files are supported';
            }
          }
          return null;
        }
      },
      expertiseLevel: {
        custom: (value) => {
          const validLevels = ['beginner', 'intermediate', 'expert'];
          if (value && !validLevels.includes(value)) {
            return 'Invalid expertise level';
          }
          return null;
        }
      }
    };

    return this.validateForm({
      documentContent: documentFile || documentText,
      documentText,
      documentFile,
      expertiseLevel,
    }, rules);
  }

  // File validation helpers
  validateFileType(file: File, allowedTypes: string[]): string | null {
    if (!allowedTypes.includes(file.type)) {
      const typeNames = allowedTypes.map(type => {
        switch (type) {
          case 'application/pdf': return 'PDF';
          case 'text/plain': return 'Text';
          case 'application/msword': return 'Word';
          case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': return 'Word';
          default: return type;
        }
      }).join(', ');
      
      return `Only ${typeNames} files are supported`;
    }
    return null;
  }

  validateFileSize(file: File, maxSizeBytes: number): string | null {
    if (file.size > maxSizeBytes) {
      const maxSizeMB = Math.round(maxSizeBytes / (1024 * 1024));
      return `File size must be less than ${maxSizeMB}MB`;
    }
    return null;
  }

  // Email validation
  validateEmail(email: string): string | null {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
      return 'Please enter a valid email address';
    }
    return null;
  }

  // URL validation
  validateURL(url: string): string | null {
    try {
      new URL(url);
      return null;
    } catch {
      return 'Please enter a valid URL';
    }
  }

  // Sanitization helpers
  sanitizeText(text: string): string {
    return text
      .trim()
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/[<>]/g, ''); // Remove potential HTML tags
  }

  sanitizeFilename(filename: string): string {
    return filename
      .replace(/[^a-zA-Z0-9.-]/g, '_') // Replace special chars with underscore
      .replace(/_{2,}/g, '_') // Replace multiple underscores with single
      .replace(/^_|_$/g, ''); // Remove leading/trailing underscores
  }
}

export const validationService = new ValidationService();
export default validationService;