"""
Enhanced Experience Level Service for LegalSaathi
Provides intelligent legal term detection and explanation based on user experience level
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    nltk = None
    word_tokenize = None
    sent_tokenize = None
    stopwords = None
    WordNetLemmatizer = None
    NLTK_AVAILABLE = False

class ExperienceLevel(Enum):
    """User experience levels for legal document analysis"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

@dataclass
class LegalTerm:
    """Represents a legal term with its metadata"""
    term: str
    definition: str
    complexity_level: int  # 1-5 scale
    domain: str  # contract, tort, property, etc.
    examples: List[str]
    related_terms: List[str]
    confidence: float = 0.0

@dataclass
class TermExplanation:
    """Explanation of a legal term adapted for experience level"""
    term: str
    explanation: str
    example: Optional[str]
    level_adapted: ExperienceLevel
    confidence: float

@dataclass
class AdaptedResponse:
    """Response adapted for user experience level"""
    original_response: str
    adapted_response: str
    terms_explained: List[TermExplanation]
    adaptation_level: ExperienceLevel
    complexity_score: float

class LegalTermDetector:
    """Detects legal terms in text using NLP techniques"""
    
    def __init__(self):
        self.nlp = None
        self.lemmatizer = None
        self.stop_words = set()
        self._initialize_nlp()
        
        # Legal term patterns for regex-based detection
        self.legal_patterns = {
            'contract_terms': [
                r'\b(?:indemnif(?:y|ication)|liability|breach|covenant|warranty)\b',
                r'\b(?:consideration|jurisdiction|arbitration|damages|remedy)\b',
                r'\b(?:force majeure|intellectual property|confidentiality)\b',
                r'\b(?:termination|assignment|novation|estoppel)\b'
            ],
            'property_terms': [
                r'\b(?:lien|mortgage|easement|deed|title|escrow)\b',
                r'\b(?:foreclosure|encumbrance|servitude|usufruct)\b'
            ],
            'tort_terms': [
                r'\b(?:negligence|defamation|trespass|nuisance)\b',
                r'\b(?:strict liability|proximate cause|duty of care)\b'
            ],
            'corporate_terms': [
                r'\b(?:fiduciary|shareholder|board of directors)\b',
                r'\b(?:merger|acquisition|due diligence|compliance)\b'
            ]
        }
    
    def _initialize_nlp(self):
        """Initialize NLP models and resources"""
        if not SPACY_AVAILABLE:
            logging.warning("NLP libraries not available, using fallback methods")
            return
            
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logging.info("spaCy model loaded successfully")
            except OSError:
                logging.warning("spaCy model not found, attempting to download...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], 
                             capture_output=True)
                self.nlp = spacy.load("en_core_web_sm")
                
        except Exception as e:
            logging.error(f"Failed to initialize NLP models: {e}")
            self.nlp = None
    
    def detect_legal_terms(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Detect legal terms in text
        Returns: List of (term, domain, confidence) tuples
        """
        detected_terms = []
        
        # Regex-based detection
        for domain, patterns in self.legal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    term = match.group().lower()
                    confidence = 0.8  # High confidence for regex matches
                    detected_terms.append((term, domain, confidence))
        
        # NLP-based detection if available
        if self.nlp:
            detected_terms.extend(self._nlp_based_detection(text))
        
        # Remove duplicates and sort by confidence
        unique_terms = {}
        for term, domain, confidence in detected_terms:
            if term not in unique_terms or unique_terms[term][1] < confidence:
                unique_terms[term] = (domain, confidence)
        
        return [(term, domain, conf) for term, (domain, conf) in unique_terms.items()]
    
    def _nlp_based_detection(self, text: str) -> List[Tuple[str, str, float]]:
        """Use spaCy for advanced legal term detection"""
        detected_terms = []
        
        try:
            doc = self.nlp(text)
            
            # Look for legal entities and terms
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'LAW', 'PERSON']:
                    # Check if it's a legal term
                    if self._is_legal_term(ent.text):
                        detected_terms.append((ent.text.lower(), 'general', 0.7))
            
            # Look for noun phrases that might be legal terms
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit to reasonable term length
                    if self._is_legal_term(chunk.text):
                        detected_terms.append((chunk.text.lower(), 'general', 0.6))
                        
        except Exception as e:
            logging.error(f"NLP-based detection failed: {e}")
        
        return detected_terms
    
    def _is_legal_term(self, term: str) -> bool:
        """Check if a term is likely a legal term"""
        legal_indicators = [
            'law', 'legal', 'court', 'contract', 'agreement', 'clause',
            'liability', 'damages', 'breach', 'remedy', 'jurisdiction',
            'statute', 'regulation', 'compliance', 'fiduciary'
        ]
        
        term_lower = term.lower()
        return any(indicator in term_lower for indicator in legal_indicators)

class LegalGlossary:
    """Comprehensive legal glossary with definitions and examples"""
    
    def __init__(self):
        self.terms = self._load_legal_glossary()
    
    def _load_legal_glossary(self) -> Dict[str, LegalTerm]:
        """Load comprehensive legal glossary"""
        # Core legal terms with definitions and examples
        glossary_data = {
            'indemnification': {
                'definition': 'A contractual obligation to compensate for harm or loss',
                'complexity': 3,
                'domain': 'contract',
                'examples': [
                    'The contractor agreed to indemnify the client against any third-party claims',
                    'Like insurance, indemnification protects you from financial loss'
                ],
                'related_terms': ['liability', 'damages', 'compensation']
            },
            'liability': {
                'definition': 'Legal responsibility for one\'s acts or omissions',
                'complexity': 2,
                'domain': 'general',
                'examples': [
                    'The company has liability for employee injuries at work',
                    'Think of liability as being legally responsible for something that goes wrong'
                ],
                'related_terms': ['negligence', 'damages', 'duty of care']
            },
            'breach': {
                'definition': 'Failure to perform a duty or obligation as required',
                'complexity': 2,
                'domain': 'contract',
                'examples': [
                    'Not paying rent on time is a breach of the lease agreement',
                    'A breach is like breaking a promise you legally made'
                ],
                'related_terms': ['contract', 'damages', 'remedy']
            },
            'covenant': {
                'definition': 'A formal agreement or promise in a contract',
                'complexity': 3,
                'domain': 'contract',
                'examples': [
                    'The loan agreement included a covenant to maintain insurance',
                    'A covenant is a serious promise that\'s part of a legal agreement'
                ],
                'related_terms': ['contract', 'agreement', 'obligation']
            },
            'warranty': {
                'definition': 'A guarantee or assurance about the quality or condition of something',
                'complexity': 2,
                'domain': 'contract',
                'examples': [
                    'The seller provided a warranty that the car had no major defects',
                    'Like a product guarantee, a warranty promises something is as described'
                ],
                'related_terms': ['guarantee', 'representation', 'contract']
            },
            'consideration': {
                'definition': 'Something of value exchanged to make a contract legally binding',
                'complexity': 3,
                'domain': 'contract',
                'examples': [
                    'Money is the most common form of consideration in contracts',
                    'Consideration is what each party gives up to make the deal fair and legal'
                ],
                'related_terms': ['contract', 'exchange', 'value']
            },
            'jurisdiction': {
                'definition': 'The authority of a court to hear and decide a case',
                'complexity': 3,
                'domain': 'procedural',
                'examples': [
                    'The federal court has jurisdiction over interstate commerce disputes',
                    'Jurisdiction determines which court has the power to handle your case'
                ],
                'related_terms': ['court', 'authority', 'venue']
            },
            'arbitration': {
                'definition': 'Private dispute resolution outside of court',
                'complexity': 3,
                'domain': 'procedural',
                'examples': [
                    'The contract required arbitration instead of going to court',
                    'Arbitration is like having a private judge decide your dispute'
                ],
                'related_terms': ['mediation', 'dispute resolution', 'alternative dispute resolution']
            },
            'damages': {
                'definition': 'Money awarded to compensate for loss or injury',
                'complexity': 2,
                'domain': 'remedies',
                'examples': [
                    'The court awarded damages for the breach of contract',
                    'Damages are money paid to make up for harm or loss caused'
                ],
                'related_terms': ['compensation', 'remedy', 'loss']
            },
            'remedy': {
                'definition': 'Legal solution or relief for a wrong or injury',
                'complexity': 2,
                'domain': 'general',
                'examples': [
                    'The remedy for breach of contract may be damages or specific performance',
                    'A remedy is the legal fix for when someone wrongs you'
                ],
                'related_terms': ['relief', 'damages', 'injunction']
            },
            'force majeure': {
                'definition': 'Unforeseeable circumstances that prevent contract performance',
                'complexity': 4,
                'domain': 'contract',
                'examples': [
                    'The pandemic was considered a force majeure event',
                    'Force majeure covers "acts of God" like natural disasters that make contracts impossible to fulfill'
                ],
                'related_terms': ['impossibility', 'frustration', 'excuse']
            },
            'intellectual property': {
                'definition': 'Legal rights to creations of the mind',
                'complexity': 3,
                'domain': 'intellectual_property',
                'examples': [
                    'Patents and trademarks are types of intellectual property',
                    'Intellectual property protects your ideas, inventions, and creative works'
                ],
                'related_terms': ['patent', 'trademark', 'copyright']
            },
            'confidentiality': {
                'definition': 'Obligation to keep information secret',
                'complexity': 2,
                'domain': 'contract',
                'examples': [
                    'The employee signed a confidentiality agreement',
                    'Confidentiality means keeping private information secret'
                ],
                'related_terms': ['non-disclosure', 'secrecy', 'privacy']
            },
            'termination': {
                'definition': 'The ending of a contract or legal relationship',
                'complexity': 2,
                'domain': 'contract',
                'examples': [
                    'The contract allows termination with 30 days notice',
                    'Termination is the formal end of a legal agreement'
                ],
                'related_terms': ['expiration', 'cancellation', 'dissolution']
            },
            'assignment': {
                'definition': 'Transfer of rights or obligations to another party',
                'complexity': 3,
                'domain': 'contract',
                'examples': [
                    'The tenant assigned the lease to a new renter',
                    'Assignment is like passing your rights or duties to someone else'
                ],
                'related_terms': ['transfer', 'delegation', 'novation']
            },
            'novation': {
                'definition': 'Replacement of a contract with a new one',
                'complexity': 4,
                'domain': 'contract',
                'examples': [
                    'The parties agreed to novation rather than amendment',
                    'Novation creates a completely new contract to replace the old one'
                ],
                'related_terms': ['substitution', 'replacement', 'modification']
            },
            'estoppel': {
                'definition': 'Legal principle preventing someone from contradicting previous statements or actions',
                'complexity': 4,
                'domain': 'general',
                'examples': [
                    'The landlord was estopped from denying the tenant\'s right to renew',
                    'Estoppel stops people from going back on their word when others relied on it'
                ],
                'related_terms': ['reliance', 'waiver', 'prohibition']
            },
            'lien': {
                'definition': 'Legal claim on property as security for debt',
                'complexity': 3,
                'domain': 'property',
                'examples': [
                    'The contractor placed a lien on the house for unpaid work',
                    'A lien is like a legal hold on property until a debt is paid'
                ],
                'related_terms': ['security interest', 'encumbrance', 'mortgage']
            },
            'mortgage': {
                'definition': 'Loan secured by real estate property',
                'complexity': 2,
                'domain': 'property',
                'examples': [
                    'They took out a mortgage to buy their home',
                    'A mortgage lets you borrow money using your house as collateral'
                ],
                'related_terms': ['loan', 'security', 'foreclosure']
            },
            'easement': {
                'definition': 'Right to use another person\'s property for a specific purpose',
                'complexity': 3,
                'domain': 'property',
                'examples': [
                    'The utility company has an easement to run power lines across the property',
                    'An easement gives you the right to use part of someone else\'s land'
                ],
                'related_terms': ['right of way', 'servitude', 'access']
            },
            'negligence': {
                'definition': 'Failure to exercise reasonable care, resulting in harm',
                'complexity': 2,
                'domain': 'tort',
                'examples': [
                    'The driver\'s negligence caused the accident',
                    'Negligence is not being careful enough and causing harm to others'
                ],
                'related_terms': ['duty of care', 'breach', 'causation']
            },
            'fiduciary': {
                'definition': 'Person with legal duty to act in another\'s best interest',
                'complexity': 4,
                'domain': 'general',
                'examples': [
                    'A trustee has a fiduciary duty to the beneficiaries',
                    'A fiduciary must put your interests before their own'
                ],
                'related_terms': ['trust', 'duty', 'loyalty']
            }
        }
        
        # Convert to LegalTerm objects
        terms = {}
        for term_key, data in glossary_data.items():
            terms[term_key] = LegalTerm(
                term=term_key,
                definition=data['definition'],
                complexity_level=data['complexity'],
                domain=data['domain'],
                examples=data['examples'],
                related_terms=data['related_terms']
            )
        
        return terms
    
    def get_term(self, term: str) -> Optional[LegalTerm]:
        """Get legal term definition"""
        return self.terms.get(term.lower())
    
    def search_terms(self, query: str) -> List[LegalTerm]:
        """Search for terms matching query"""
        query_lower = query.lower()
        matches = []
        
        for term_key, term_obj in self.terms.items():
            if (query_lower in term_key or 
                query_lower in term_obj.definition.lower() or
                any(query_lower in example.lower() for example in term_obj.examples)):
                matches.append(term_obj)
        
        return matches

class ExampleGenerator:
    """Generates contextual real-world examples for legal concepts"""
    
    def __init__(self):
        self.example_templates = {
            'contract': [
                "Like when you sign a lease for an apartment - you promise to pay rent, the landlord promises you can live there",
                "Similar to buying a car - you pay money, the dealer gives you the car and title",
                "Think of hiring a contractor - they promise to do the work, you promise to pay them"
            ],
            'property': [
                "Imagine owning a house - you have rights to use it, sell it, or rent it out",
                "Like having a parking space - you can use it but others cannot",
                "Think of a fence around your yard - it shows the boundaries of what you own"
            ],
            'tort': [
                "Like a car accident caused by texting while driving",
                "Similar to a store not cleaning up a spill and someone slipping",
                "Think of a doctor making a mistake during surgery"
            ],
            'general': [
                "In everyday life, this is like...",
                "You might encounter this when...",
                "A common example would be..."
            ]
        }
    
    def generate_example(self, term: LegalTerm, context: str = "") -> str:
        """Generate contextual example for a legal term"""
        # Use existing examples from the term if available
        if term.examples:
            return term.examples[0]  # Return the first (usually simplest) example
        
        # Generate based on domain
        templates = self.example_templates.get(term.domain, self.example_templates['general'])
        return templates[0] if templates else "This concept applies in many legal situations."

class EnhancedExperienceLevelService:
    """Main service for enhanced experience level adaptation"""
    
    def __init__(self):
        self.term_detector = LegalTermDetector()
        self.glossary = LegalGlossary()
        self.example_generator = ExampleGenerator()
        
        # Complexity thresholds for different experience levels
        self.complexity_thresholds = {
            ExperienceLevel.BEGINNER: 2,      # Explain terms with complexity <= 2
            ExperienceLevel.INTERMEDIATE: 3,   # Explain terms with complexity <= 3
            ExperienceLevel.EXPERT: 5         # Don't explain any terms
        }
    
    async def adapt_response_for_level(
        self, 
        response: str, 
        level: ExperienceLevel,
        legal_context: Optional[Dict[str, Any]] = None
    ) -> AdaptedResponse:
        """
        Adapt response based on user experience level
        """
        try:
            # Detect legal terms in the response
            detected_terms = self.term_detector.detect_legal_terms(response)
            
            # Generate explanations based on experience level
            terms_explained = []
            adapted_response = response
            
            if level != ExperienceLevel.EXPERT:
                threshold = self.complexity_thresholds[level]
                
                for term, domain, confidence in detected_terms:
                    legal_term = self.glossary.get_term(term)
                    
                    if legal_term and legal_term.complexity_level <= threshold:
                        explanation = self.generate_term_explanation(legal_term, level)
                        terms_explained.append(explanation)
                        
                        # Insert explanation into response
                        adapted_response = self._insert_explanation(
                            adapted_response, term, explanation, level
                        )
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(detected_terms)
            
            return AdaptedResponse(
                original_response=response,
                adapted_response=adapted_response,
                terms_explained=terms_explained,
                adaptation_level=level,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            logging.error(f"Error adapting response for experience level: {e}")
            # Return original response on error
            return AdaptedResponse(
                original_response=response,
                adapted_response=response,
                terms_explained=[],
                adaptation_level=level,
                complexity_score=0.0
            )
    
    def generate_term_explanation(self, term: LegalTerm, level: ExperienceLevel) -> TermExplanation:
        """Generate explanation appropriate for experience level"""
        
        if level == ExperienceLevel.BEGINNER:
            # Provide definition + simple example
            example = self.example_generator.generate_example(term)
            explanation = f"{term.definition}. {example}"
            
        elif level == ExperienceLevel.INTERMEDIATE:
            # Provide definition + implications, no basic examples
            explanation = f"{term.definition}. This has important legal implications for contract performance and liability."
            example = None
            
        else:  # Expert level
            # No explanation needed
            explanation = ""
            example = None
        
        return TermExplanation(
            term=term.term,
            explanation=explanation,
            example=example,
            level_adapted=level,
            confidence=0.9
        )
    
    def _insert_explanation(self, text: str, term: str, explanation: TermExplanation, level: ExperienceLevel) -> str:
        """Insert explanation into text appropriately"""
        
        if level == ExperienceLevel.EXPERT:
            return text  # No modifications for experts
        
        # Find the term in text (case insensitive)
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        
        def replace_func(match):
            matched_term = match.group()
            if level == ExperienceLevel.BEGINNER:
                return f"{matched_term} ({explanation.explanation})"
            else:  # Intermediate
                return f"{matched_term} (a legal concept involving {explanation.explanation.split('.')[0].lower()})"
        
        # Replace first occurrence only to avoid cluttering
        return pattern.sub(replace_func, text, count=1)
    
    def _calculate_complexity_score(self, detected_terms: List[Tuple[str, str, float]]) -> float:
        """Calculate overall complexity score of the text"""
        if not detected_terms:
            return 0.0
        
        total_complexity = 0
        total_terms = 0
        
        for term, domain, confidence in detected_terms:
            legal_term = self.glossary.get_term(term)
            if legal_term:
                total_complexity += legal_term.complexity_level * confidence
                total_terms += 1
        
        return total_complexity / max(total_terms, 1)
    
    def get_term_definition(self, term: str) -> Optional[LegalTerm]:
        """Get definition for a specific legal term"""
        return self.glossary.get_term(term)
    
    def search_legal_terms(self, query: str) -> List[LegalTerm]:
        """Search for legal terms matching query"""
        return self.glossary.search_terms(query)
    
    def validate_experience_level(self, level: str) -> ExperienceLevel:
        """Validate and convert experience level string"""
        try:
            return ExperienceLevel(level.lower())
        except ValueError:
            logging.warning(f"Invalid experience level: {level}, defaulting to intermediate")
            return ExperienceLevel.INTERMEDIATE

# Global service instance
enhanced_experience_service = EnhancedExperienceLevelService()