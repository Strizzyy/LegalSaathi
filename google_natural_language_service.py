"""
Google Cloud Natural Language AI Service for Legal Document Analysis
Uses Natural Language AI for sentiment, entity extraction, and classification
"""

import os
from typing import Dict, List, Any, Optional
from google.cloud import language_v1
import logging

logger = logging.getLogger(__name__)

class GoogleNaturalLanguageService:
    """
    Google Cloud Natural Language AI service for legal document analysis
    Provides sentiment analysis, entity extraction, and content classification
    """
    
    def __init__(self):
        try:
            # Set up authentication
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            self.client = language_v1.LanguageServiceClient()
            self.enabled = True
            logger.info("Google Natural Language AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Natural Language AI: {e}")
            self.enabled = False
    
    def analyze_legal_document(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of legal document using Natural Language AI
        
        Args:
            text: Legal document text to analyze
            
        Returns:
            Dict containing sentiment, entities, syntax, and classification results
        """
        if not self.enabled:
            return self._fallback_analysis(text)
        
        try:
            document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
            
            # Perform multiple analyses
            results = {
                'success': True,
                'sentiment': self._analyze_sentiment(document),
                'entities': self._extract_entities(document),
                'syntax': self._analyze_syntax(document),
                'classification': self._classify_content(document),
                'legal_insights': self._extract_legal_insights(text, document)
            }
            
            logger.info("Natural Language AI analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Natural Language AI analysis failed: {e}")
            return self._fallback_analysis(text)
    
    def _analyze_sentiment(self, document) -> Dict[str, Any]:
        """Analyze sentiment of the legal document"""
        try:
            response = self.client.analyze_sentiment(
                request={'document': document}
            )
            
            sentiment = response.document_sentiment
            
            # Interpret sentiment for legal context
            legal_tone = self._interpret_legal_sentiment(sentiment.score, sentiment.magnitude)
            
            return {
                'score': sentiment.score,
                'magnitude': sentiment.magnitude,
                'legal_tone': legal_tone,
                'sentences': [
                    {
                        'text': sentence.text.content,
                        'sentiment_score': sentence.sentiment.score,
                        'magnitude': sentence.sentiment.magnitude
                    }
                    for sentence in response.sentences[:10]  # Limit to first 10 sentences
                ]
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {'score': 0.0, 'magnitude': 0.0, 'legal_tone': 'neutral'}
    
    def _extract_entities(self, document) -> List[Dict[str, Any]]:
        """Extract named entities relevant to legal documents"""
        try:
            response = self.client.analyze_entities(
                request={'document': document}
            )
            
            entities = []
            for entity in response.entities:
                try:
                    # Handle different entity type formats
                    entity_type = entity.type_.name if hasattr(entity.type_, 'name') else str(entity.type_)
                    
                    # Focus on entities relevant to legal documents
                    if self._is_legal_entity(entity_type, entity.name):
                        entity_mentions = []
                        for mention in entity.mentions[:3]:  # Limit mentions
                            try:
                                mention_type = mention.type_.name if hasattr(mention.type_, 'name') else str(mention.type_)
                                entity_mentions.append({
                                    'text': mention.text.content,
                                    'type': mention_type,
                                    'sentiment': {
                                        'score': mention.sentiment.score if mention.sentiment else 0.0,
                                        'magnitude': mention.sentiment.magnitude if mention.sentiment else 0.0
                                    }
                                })
                            except Exception as mention_error:
                                logger.warning(f"Error processing mention: {mention_error}")
                                continue
                        
                        entities.append({
                            'name': entity.name,
                            'type': entity_type,
                            'salience': entity.salience,
                            'mentions': entity_mentions,
                            'metadata': dict(entity.metadata) if entity.metadata else {},
                            'legal_relevance': self._assess_legal_relevance(entity.name, entity_type)
                        })
                except Exception as entity_error:
                    logger.warning(f"Error processing entity: {entity_error}")
                    continue
            
            return sorted(entities, key=lambda x: x['salience'], reverse=True)[:20]  # Top 20 entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def _analyze_syntax(self, document) -> Dict[str, Any]:
        """Analyze syntax to identify complex legal language"""
        try:
            response = self.client.analyze_syntax(
                request={'document': document}
            )
            
            # Analyze sentence complexity
            sentence_lengths = []
            complex_sentences = 0
            
            for sentence in response.sentences:
                length = len(sentence.text.content.split())
                sentence_lengths.append(length)
                if length > 30:  # Consider sentences over 30 words as complex
                    complex_sentences += 1
            
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
            
            # Analyze token complexity
            complex_tokens = 0
            legal_terms = 0
            
            for token in response.tokens:
                if len(token.text.content) > 12:  # Long words
                    complex_tokens += 1
                if self._is_legal_term(token.text.content):
                    legal_terms += 1
            
            return {
                'avg_sentence_length': avg_sentence_length,
                'complex_sentences': complex_sentences,
                'complexity_ratio': complex_sentences / len(response.sentences) if response.sentences else 0,
                'complex_tokens': complex_tokens,
                'legal_terms': legal_terms,
                'readability_score': self._calculate_readability_score(avg_sentence_length, complex_tokens, len(response.tokens))
            }
            
        except Exception as e:
            logger.error(f"Syntax analysis failed: {e}")
            return {'avg_sentence_length': 0, 'complexity_ratio': 0, 'readability_score': 0}
    
    def _classify_content(self, document) -> Dict[str, Any]:
        """Classify document content into legal categories"""
        try:
            response = self.client.classify_text(
                request={'document': document}
            )
            
            categories = []
            for category in response.categories:
                categories.append({
                    'name': category.name,
                    'confidence': category.confidence,
                    'legal_category': self._map_to_legal_category(category.name)
                })
            
            return {
                'categories': sorted(categories, key=lambda x: x['confidence'], reverse=True),
                'primary_category': categories[0] if categories else None
            }
            
        except Exception as e:
            logger.error(f"Content classification failed: {e}")
            return {'categories': [], 'primary_category': None}
    
    def _extract_legal_insights(self, text: str, document) -> Dict[str, Any]:
        """Extract specific legal insights from the analysis"""
        insights = {
            'document_complexity': 'low',
            'legal_language_density': 0.0,
            'potential_risk_indicators': [],
            'readability_assessment': 'good',
            'recommended_expertise_level': 'beginner'
        }
        
        # Calculate legal language density
        legal_terms_count = len([word for word in text.lower().split() if self._is_legal_term(word)])
        total_words = len(text.split())
        insights['legal_language_density'] = legal_terms_count / total_words if total_words > 0 else 0.0
        
        # Assess document complexity
        if insights['legal_language_density'] > 0.15:
            insights['document_complexity'] = 'high'
            insights['recommended_expertise_level'] = 'expert'
        elif insights['legal_language_density'] > 0.08:
            insights['document_complexity'] = 'medium'
            insights['recommended_expertise_level'] = 'intermediate'
        
        # Identify potential risk indicators
        risk_terms = [
            'indemnify', 'liability', 'damages', 'penalty', 'forfeit', 'waive',
            'irrevocable', 'unconditional', 'sole discretion', 'liquidated damages'
        ]
        
        for term in risk_terms:
            if term.lower() in text.lower():
                insights['potential_risk_indicators'].append(term)
        
        # Readability assessment
        avg_sentence_length = len(text.split()) / len(text.split('.')) if '.' in text else 0
        if avg_sentence_length > 25:
            insights['readability_assessment'] = 'poor'
        elif avg_sentence_length > 15:
            insights['readability_assessment'] = 'fair'
        
        return insights
    
    def _interpret_legal_sentiment(self, score: float, magnitude: float) -> str:
        """Interpret sentiment in legal context"""
        if magnitude < 0.3:
            return 'neutral'
        elif score > 0.3:
            return 'favorable'
        elif score < -0.3:
            return 'unfavorable'
        else:
            return 'mixed'
    
    def _is_legal_entity(self, entity_type: str, entity_name: str) -> bool:
        """Check if entity is relevant to legal documents"""
        legal_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'DATE', 'NUMBER', 'PRICE']
        legal_keywords = ['court', 'law', 'legal', 'contract', 'agreement', 'party', 'clause']
        
        return (entity_type in legal_types or 
                any(keyword in entity_name.lower() for keyword in legal_keywords))
    
    def _assess_legal_relevance(self, entity_name: str, entity_type: str) -> str:
        """Assess the legal relevance of an entity"""
        high_relevance_terms = ['contract', 'agreement', 'party', 'court', 'law', 'legal']
        medium_relevance_types = ['PERSON', 'ORGANIZATION', 'DATE', 'PRICE']
        
        if any(term in entity_name.lower() for term in high_relevance_terms):
            return 'high'
        elif entity_type in medium_relevance_types:
            return 'medium'
        else:
            return 'low'
    
    def _is_legal_term(self, word: str) -> bool:
        """Check if a word is a legal term"""
        legal_terms = {
            'whereas', 'hereby', 'heretofore', 'hereinafter', 'notwithstanding',
            'indemnify', 'liability', 'covenant', 'warranty', 'representation',
            'jurisdiction', 'arbitration', 'mediation', 'liquidated', 'damages',
            'breach', 'default', 'termination', 'severability', 'waiver'
        }
        return word.lower() in legal_terms
    
    def _calculate_readability_score(self, avg_sentence_length: float, complex_tokens: int, total_tokens: int) -> float:
        """Calculate a simple readability score (0-100, higher is more readable)"""
        if total_tokens == 0:
            return 0.0
        
        # Simple formula based on sentence length and complex words
        complexity_ratio = complex_tokens / total_tokens
        sentence_penalty = max(0, (avg_sentence_length - 15) * 2)  # Penalty for long sentences
        complexity_penalty = complexity_ratio * 50  # Penalty for complex words
        
        score = 100 - sentence_penalty - complexity_penalty
        return max(0, min(100, score))
    
    def _map_to_legal_category(self, category_name: str) -> str:
        """Map Google's categories to legal document categories"""
        legal_mapping = {
            '/Law & Government': 'Legal Document',
            '/Business & Industrial': 'Commercial Agreement',
            '/Finance': 'Financial Agreement',
            '/Real Estate': 'Real Estate Contract',
            '/Jobs & Education': 'Employment Contract'
        }
        
        for key, value in legal_mapping.items():
            if key in category_name:
                return value
        
        return 'General Legal Document'
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis when Natural Language AI is not available"""
        return {
            'success': False,
            'sentiment': {'score': 0.0, 'magnitude': 0.0, 'legal_tone': 'neutral'},
            'entities': [],
            'syntax': {'avg_sentence_length': 0, 'complexity_ratio': 0, 'readability_score': 0},
            'classification': {'categories': [], 'primary_category': None},
            'legal_insights': {
                'document_complexity': 'unknown',
                'legal_language_density': 0.0,
                'potential_risk_indicators': [],
                'readability_assessment': 'unknown',
                'recommended_expertise_level': 'intermediate'
            },
            'error': 'Google Natural Language AI not available'
        }

# Global instance
natural_language_service = GoogleNaturalLanguageService()