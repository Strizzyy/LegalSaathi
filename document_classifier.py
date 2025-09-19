"""
Document Type Classifier for Legal Documents
Simple keyword-based classification for different document types
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class DocumentType(Enum):
    RENTAL_AGREEMENT = "rental_agreement"
    EMPLOYMENT_CONTRACT = "employment_contract"
    NDA = "nda"
    TERMS_OF_SERVICE = "terms_of_service"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float  # 0.0 to 1.0
    matched_keywords: List[str]
    suggestions: List[str]

class DocumentClassifier:
    """
    Simple keyword-based document type classifier
    Requirements: 7.2 - Create simple keyword-based document type classifier
    """
    
    def __init__(self):
        # Define keyword patterns for each document type
        self.classification_patterns = {
            DocumentType.RENTAL_AGREEMENT: {
                'keywords': [
                    'rent', 'lease', 'tenant', 'landlord', 'property', 'premises',
                    'rental', 'deposit', 'security deposit', 'monthly rent',
                    'lease term', 'rental period', 'eviction', 'utilities',
                    'maintenance', 'repairs', 'occupancy', 'subletting'
                ],
                'required_keywords': ['rent', 'tenant', 'landlord'],
                'weight': 1.0
            },
            DocumentType.EMPLOYMENT_CONTRACT: {
                'keywords': [
                    'employment', 'employee', 'employer', 'salary', 'wages',
                    'job title', 'position', 'duties', 'responsibilities',
                    'termination', 'resignation', 'benefits', 'vacation',
                    'sick leave', 'probation', 'performance', 'work hours',
                    'overtime', 'confidentiality', 'non-compete'
                ],
                'required_keywords': ['employee', 'employer', 'employment'],
                'weight': 1.0
            },
            DocumentType.NDA: {
                'keywords': [
                    'non-disclosure', 'confidential', 'confidentiality',
                    'proprietary', 'trade secret', 'disclosure', 'recipient',
                    'disclosing party', 'receiving party', 'confidential information',
                    'non-disclosure agreement', 'secrecy', 'proprietary information',
                    'unauthorized disclosure', 'breach of confidentiality'
                ],
                'required_keywords': ['confidential', 'disclosure', 'non-disclosure'],
                'weight': 1.0
            },
            DocumentType.TERMS_OF_SERVICE: {
                'keywords': [
                    'terms of service', 'terms of use', 'user agreement',
                    'service agreement', 'website', 'platform', 'user',
                    'service provider', 'acceptable use', 'prohibited conduct',
                    'account', 'registration', 'privacy policy', 'cookies',
                    'intellectual property', 'limitation of liability',
                    'indemnification', 'governing law'
                ],
                'required_keywords': ['terms', 'service', 'user'],
                'weight': 1.0
            }
        }
    
    def classify_document(self, document_text: str) -> ClassificationResult:
        """
        Classify document type based on keyword analysis
        """
        if not document_text or not document_text.strip():
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                matched_keywords=[],
                suggestions=["Document text is empty or invalid"]
            )
        
        text_lower = document_text.lower()
        classification_scores = {}
        all_matched_keywords = {}
        
        # Calculate scores for each document type
        for doc_type, patterns in self.classification_patterns.items():
            matched_keywords = []
            required_matches = 0
            total_matches = 0
            
            # Check for keyword matches
            for keyword in patterns['keywords']:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
                    total_matches += 1
                    
                    # Check if it's a required keyword
                    if keyword.lower() in [req.lower() for req in patterns['required_keywords']]:
                        required_matches += 1
            
            # Calculate confidence score
            keyword_ratio = total_matches / len(patterns['keywords'])
            required_ratio = required_matches / len(patterns['required_keywords'])
            
            # Weighted score (required keywords are more important)
            confidence = (keyword_ratio * 0.4) + (required_ratio * 0.6)
            
            classification_scores[doc_type] = confidence
            all_matched_keywords[doc_type] = matched_keywords
        
        # Find the best match
        best_type = max(classification_scores.keys(), key=lambda k: classification_scores[k])
        best_confidence = classification_scores[best_type]
        best_keywords = all_matched_keywords[best_type]
        
        # If confidence is too low, classify as unknown
        if best_confidence < 0.3:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=best_confidence,
                matched_keywords=best_keywords,
                suggestions=self._generate_suggestions(classification_scores)
            )
        
        return ClassificationResult(
            document_type=best_type,
            confidence=best_confidence,
            matched_keywords=best_keywords,
            suggestions=[]
        )
    
    def _generate_suggestions(self, scores: Dict[DocumentType, float]) -> List[str]:
        """Generate suggestions when document type is unclear"""
        suggestions = []
        
        # Sort by confidence
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_scores[0][1] > 0.1:
            suggestions.append(f"This might be a {sorted_scores[0][0].value.replace('_', ' ')} (confidence: {sorted_scores[0][1]:.1%})")
        
        if len(sorted_scores) > 1 and sorted_scores[1][1] > 0.1:
            suggestions.append(f"Could also be a {sorted_scores[1][0].value.replace('_', ' ')} (confidence: {sorted_scores[1][1]:.1%})")
        
        if not suggestions:
            suggestions.append("Unable to determine document type - please ensure you've uploaded a legal document")
        
        return suggestions
    
    def is_supported_document_type(self, document_type: DocumentType) -> bool:
        """Check if the document type is supported for analysis"""
        # Currently only rental agreements are fully supported
        return document_type == DocumentType.RENTAL_AGREEMENT
    
    def get_analysis_message(self, classification: ClassificationResult) -> str:
        """Get appropriate message based on document classification"""
        if classification.document_type == DocumentType.RENTAL_AGREEMENT:
            if classification.confidence > 0.7:
                return "✅ Rental agreement detected - proceeding with full analysis"
            else:
                return "⚠️ Possible rental agreement detected - analysis may be limited"
        
        elif classification.document_type == DocumentType.EMPLOYMENT_CONTRACT:
            return "📋 Employment contract detected - currently only rental agreements are supported for full analysis"
        
        elif classification.document_type == DocumentType.NDA:
            return "🤐 Non-disclosure agreement detected - currently only rental agreements are supported for full analysis"
        
        elif classification.document_type == DocumentType.TERMS_OF_SERVICE:
            return "📱 Terms of service detected - currently only rental agreements are supported for full analysis"
        
        else:
            return "❓ Document type unclear - for best results, please upload a rental agreement"