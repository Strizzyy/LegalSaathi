"""
Risk Classification System for Legal Document Analysis
Implements RED/YELLOW/GREEN risk categorization with AI and rule-based detection
"""

import os
import re
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import groq
import google.generativeai as genai
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RiskLevel(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"

class RiskCategory(Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONAL = "operational"

@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float  # 0.0 to 1.0
    reasons: List[str]
    severity: str
    confidence: float
    confidence_percentage: int  # 0-100%
    risk_categories: Dict[str, float]  # financial, legal, operational
    low_confidence_warning: bool

@dataclass
class RedFlag:
    pattern: str
    description: str
    risk_level: RiskLevel
    weight: float
    category: RiskCategory
    severity_indicator: str

class RiskClassifier:
    """
    Main risk classification system that combines AI analysis with rule-based detection
    """
    
    def __init__(self):
        # Initialize API clients
        self.groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Initialize red flag patterns
        self.red_flag_patterns = self._load_red_flag_patterns()
        
    def _load_red_flag_patterns(self) -> List[RedFlag]:
        """Load predefined red flag patterns for keyword-based detection with categories"""
        return [
            # High-risk patterns (RED)
            RedFlag(
                pattern=r"non-refundable.*deposit|deposit.*non-refundable",
                description="Non-refundable security deposit",
                risk_level=RiskLevel.RED,
                weight=0.9,
                category=RiskCategory.FINANCIAL,
                severity_indicator="Critical financial risk"
            ),
            RedFlag(
                pattern=r"unlimited.*liability|liability.*unlimited",
                description="Unlimited liability clause",
                risk_level=RiskLevel.RED,
                weight=0.95,
                category=RiskCategory.LEGAL,
                severity_indicator="Severe legal exposure"
            ),
            RedFlag(
                pattern=r"waive.*right|forfeit.*right|surrender.*right",
                description="Rights waiver clause",
                risk_level=RiskLevel.RED,
                weight=0.85,
                category=RiskCategory.LEGAL,
                severity_indicator="Major rights violation"
            ),
            RedFlag(
                pattern=r"no.*notice.*entry|entry.*without.*notice",
                description="No notice entry clause",
                risk_level=RiskLevel.RED,
                weight=0.8,
                category=RiskCategory.OPERATIONAL,
                severity_indicator="Privacy violation risk"
            ),
            RedFlag(
                pattern=r"automatic.*renewal|auto.*renew",
                description="Automatic renewal without consent",
                risk_level=RiskLevel.RED,
                weight=0.7,
                category=RiskCategory.LEGAL,
                severity_indicator="Contract trap mechanism"
            ),
            
            # Medium-risk patterns (YELLOW)
            RedFlag(
                pattern=r"late.*fee.*\$[0-9]{3,}|penalty.*\$[0-9]{3,}",
                description="Excessive late fees",
                risk_level=RiskLevel.YELLOW,
                weight=0.6,
                category=RiskCategory.FINANCIAL,
                severity_indicator="High penalty costs"
            ),
            RedFlag(
                pattern=r"inspection.*daily|daily.*inspection",
                description="Excessive inspection frequency",
                risk_level=RiskLevel.YELLOW,
                weight=0.5,
                category=RiskCategory.OPERATIONAL,
                severity_indicator="Privacy intrusion"
            ),
            RedFlag(
                pattern=r"no.*pets.*allowed|pets.*prohibited",
                description="Strict pet policy",
                risk_level=RiskLevel.YELLOW,
                weight=0.3,
                category=RiskCategory.OPERATIONAL,
                severity_indicator="Lifestyle restriction"
            ),
            RedFlag(
                pattern=r"subletting.*prohibited|no.*subletting",
                description="Subletting restrictions",
                risk_level=RiskLevel.YELLOW,
                weight=0.4,
                category=RiskCategory.OPERATIONAL,
                severity_indicator="Flexibility limitation"
            ),
            RedFlag(
                pattern=r"rent.*increase.*[0-9]{2,}%",
                description="High rent increase percentage",
                risk_level=RiskLevel.YELLOW,
                weight=0.6,
                category=RiskCategory.FINANCIAL,
                severity_indicator="Affordability risk"
            )
        ]
    
    def classify_risk_level(self, clause_text: str, ai_analysis: Dict = None) -> RiskAssessment:
        """
        Main method to classify risk level combining AI analysis and keyword matching
        Requirements: 3.1, 3.2, 3.3, 3.4
        """
        # Step 1: Keyword-based red flag detection
        keyword_risk = self._detect_keyword_red_flags(clause_text)
        
        # Step 2: AI-based risk assessment (use Groq for simple analysis)
        ai_risk = self._get_ai_risk_assessment(clause_text)
        
        # Step 3: Combine assessments
        combined_risk = self._combine_risk_assessments(keyword_risk, ai_risk)
        
        # Step 4: Store in Neo4j for learning
        self._store_risk_assessment(clause_text, combined_risk)
        
        return combined_risk
    
    def _detect_keyword_red_flags(self, text: str) -> RiskAssessment:
        """
        Detect red flags using keyword-based pattern matching with multi-dimensional analysis
        """
        text_lower = text.lower()
        detected_flags = []
        total_weight = 0.0
        max_risk_level = RiskLevel.GREEN
        
        # Initialize category scores
        category_scores = {
            RiskCategory.FINANCIAL: 0.0,
            RiskCategory.LEGAL: 0.0,
            RiskCategory.OPERATIONAL: 0.0
        }
        category_counts = {
            RiskCategory.FINANCIAL: 0,
            RiskCategory.LEGAL: 0,
            RiskCategory.OPERATIONAL: 0
        }
        
        for flag in self.red_flag_patterns:
            if re.search(flag.pattern, text_lower, re.IGNORECASE):
                detected_flags.append(f"{flag.description} ({flag.severity_indicator})")
                total_weight += flag.weight
                
                # Update category scores
                category_scores[flag.category] += flag.weight
                category_counts[flag.category] += 1
                
                # Update max risk level
                if flag.risk_level == RiskLevel.RED:
                    max_risk_level = RiskLevel.RED
                elif flag.risk_level == RiskLevel.YELLOW and max_risk_level != RiskLevel.RED:
                    max_risk_level = RiskLevel.YELLOW
        
        # Calculate risk score
        risk_score = min(total_weight, 1.0)
        
        # Normalize category scores
        risk_categories = {}
        for category, score in category_scores.items():
            if category_counts[category] > 0:
                risk_categories[category.value] = min(score / category_counts[category], 1.0)
            else:
                risk_categories[category.value] = 0.0
        
        # Determine final risk level
        if max_risk_level == RiskLevel.RED or risk_score > 0.7:
            final_level = RiskLevel.RED
            severity = "High"
        elif max_risk_level == RiskLevel.YELLOW or risk_score > 0.3:
            final_level = RiskLevel.YELLOW
            severity = "Medium"
        else:
            final_level = RiskLevel.GREEN
            severity = "Low"
        
        reasons = detected_flags if detected_flags else ["No red flags detected in keyword analysis"]
        
        # Calculate confidence percentage and low confidence warning
        confidence = 0.8  # High confidence for keyword matching
        confidence_percentage = int(confidence * 100)
        low_confidence_warning = confidence_percentage < 70
        
        return RiskAssessment(
            level=final_level,
            score=risk_score,
            reasons=reasons,
            severity=severity,
            confidence=confidence,
            confidence_percentage=confidence_percentage,
            risk_categories=risk_categories,
            low_confidence_warning=low_confidence_warning
        )
    
    def _get_ai_risk_assessment(self, clause_text: str) -> RiskAssessment:
        """
        Get AI-based risk assessment using Groq for simple analysis
        """
        try:
            # Check if Groq client is available
            if not self.groq_client:
                return self._get_gemini_risk_assessment(clause_text)
            
            # Enhanced prompt with confidence levels and multi-dimensional analysis
            prompt = f"""
            Analyze this rental agreement clause for risk level with detailed confidence assessment. Respond with JSON only:
            
            Clause: "{clause_text}"
            
            Provide assessment in this exact JSON format:
            {{
                "risk_level": "RED|YELLOW|GREEN",
                "risk_score": 0.0-1.0,
                "reasons": ["reason1", "reason2"],
                "severity": "High|Medium|Low",
                "confidence": 0.0-1.0,
                "confidence_percentage": 0-100,
                "risk_categories": {{
                    "financial": 0.0-1.0,
                    "legal": 0.0-1.0,
                    "operational": 0.0-1.0
                }},
                "low_confidence_warning": true/false
            }}
            
            Risk Guidelines:
            - RED: Unfair, illegal, or heavily biased against tenant
            - YELLOW: Concerning terms that could be improved  
            - GREEN: Fair and standard terms
            
            Risk Categories:
            - Financial: Money-related risks (deposits, fees, rent increases)
            - Legal: Rights violations, liability issues, legal compliance
            - Operational: Day-to-day living restrictions, privacy, flexibility
            
            Confidence Guidelines:
            - High confidence (80-100%): Clear legal language, well-defined terms
            - Medium confidence (50-79%): Some ambiguity but analyzable
            - Low confidence (0-49%): Unclear language, insufficient context
            """
            
            
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Groq API call timed out")
            
           
            
            response = self.groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a legal expert. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500,
            timeout=10.0 # Use the library's built-in timeout
        )
            
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(0))
                
                confidence = float(ai_data.get('confidence', 0.7))
                confidence_percentage = ai_data.get('confidence_percentage', int(confidence * 100))
                
                return RiskAssessment(
                    level=RiskLevel(ai_data.get('risk_level', 'YELLOW')),
                    score=float(ai_data.get('risk_score', 0.5)),
                    reasons=ai_data.get('reasons', ['AI analysis completed']),
                    severity=ai_data.get('severity', 'Medium'),
                    confidence=confidence,
                    confidence_percentage=confidence_percentage,
                    risk_categories=ai_data.get('risk_categories', {'financial': 0.5, 'legal': 0.5, 'operational': 0.5}),
                    low_confidence_warning=ai_data.get('low_confidence_warning', confidence_percentage < 70)
                )
            pass
            
        except Exception as e:
            print(f"Groq API error: {e}")
            # Fallback to Gemini for complex analysis
            return self._get_gemini_risk_assessment(clause_text)
        
        # Fallback assessment
        return RiskAssessment(
            level=RiskLevel.YELLOW,
            score=0.5,
            reasons=["AI analysis unavailable"],
            severity="Medium",
            confidence=0.3,
            confidence_percentage=30,
            risk_categories={'financial': 0.5, 'legal': 0.5, 'operational': 0.5},
            low_confidence_warning=True
        )
    
    def _get_gemini_risk_assessment(self, clause_text: str) -> RiskAssessment:
        """
        Fallback to Gemini API for complex analysis when Groq fails
        """
        try:
            prompt = f"""
            As a legal expert, analyze this rental agreement clause for risk:
            
            "{clause_text}"
            
            Provide a JSON response with:
            - risk_level: RED (high risk), YELLOW (medium), or GREEN (low)
            - risk_score: 0.0 to 1.0
            - reasons: list of specific concerns
            - severity: High, Medium, or Low
            - confidence: 0.0 to 1.0
            
            Focus on tenant rights, fairness, and legal compliance.
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            # Try to extract JSON from Gemini response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(0))
                
                confidence = float(ai_data.get('confidence', 0.8))
                confidence_percentage = ai_data.get('confidence_percentage', int(confidence * 100))
                
                return RiskAssessment(
                    level=RiskLevel(ai_data.get('risk_level', 'YELLOW')),
                    score=float(ai_data.get('risk_score', 0.5)),
                    reasons=ai_data.get('reasons', ['Gemini analysis completed']),
                    severity=ai_data.get('severity', 'Medium'),
                    confidence=confidence,
                    confidence_percentage=confidence_percentage,
                    risk_categories=ai_data.get('risk_categories', {'financial': 0.5, 'legal': 0.5, 'operational': 0.5}),
                    low_confidence_warning=ai_data.get('low_confidence_warning', confidence_percentage < 70)
                )
                
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        # Final fallback
        return RiskAssessment(
            level=RiskLevel.YELLOW,
            score=0.5,
            reasons=["AI services unavailable - manual review recommended"],
            severity="Medium",
            confidence=0.2,
            confidence_percentage=20,
            risk_categories={'financial': 0.5, 'legal': 0.5, 'operational': 0.5},
            low_confidence_warning=True
        )
    
    def _combine_risk_assessments(self, keyword_risk: RiskAssessment, ai_risk: RiskAssessment) -> RiskAssessment:
        """
        Combine keyword-based and AI-based risk assessments with multi-dimensional analysis
        """
        # Weight the assessments (keyword matching is more reliable for known patterns)
        keyword_weight = 0.6
        ai_weight = 0.4
        
        # Combine scores
        combined_score = (keyword_risk.score * keyword_weight) + (ai_risk.score * ai_weight)
        
        # Determine final risk level (take the higher risk)
        risk_levels_priority = {RiskLevel.GREEN: 0, RiskLevel.YELLOW: 1, RiskLevel.RED: 2}
        
        if risk_levels_priority[keyword_risk.level] >= risk_levels_priority[ai_risk.level]:
            final_level = keyword_risk.level
        else:
            final_level = ai_risk.level
        
        # Combine reasons
        combined_reasons = []
        if keyword_risk.reasons != ["No red flags detected in keyword analysis"]:
            combined_reasons.extend([f"Pattern Match: {reason}" for reason in keyword_risk.reasons])
        combined_reasons.extend([f"AI Analysis: {reason}" for reason in ai_risk.reasons])
        
        # Determine severity
        if final_level == RiskLevel.RED:
            severity = "High"
        elif final_level == RiskLevel.YELLOW:
            severity = "Medium"
        else:
            severity = "Low"
        
        # Combine confidence
        combined_confidence = (keyword_risk.confidence * keyword_weight) + (ai_risk.confidence * ai_weight)
        combined_confidence_percentage = int(combined_confidence * 100)
        
        # Combine risk categories
        combined_categories = {}
        for category in ['financial', 'legal', 'operational']:
            keyword_cat_score = keyword_risk.risk_categories.get(category, 0.0)
            ai_cat_score = ai_risk.risk_categories.get(category, 0.0)
            combined_categories[category] = (keyword_cat_score * keyword_weight) + (ai_cat_score * ai_weight)
        
        # Determine low confidence warning
        low_confidence_warning = (combined_confidence_percentage < 70 or 
                                keyword_risk.low_confidence_warning or 
                                ai_risk.low_confidence_warning)
        
        return RiskAssessment(
            level=final_level,
            score=combined_score,
            reasons=combined_reasons,
            severity=severity,
            confidence=combined_confidence,
            confidence_percentage=combined_confidence_percentage,
            risk_categories=combined_categories,
            low_confidence_warning=low_confidence_warning
        )
    
    def _store_risk_assessment(self, clause_text: str, risk_assessment: RiskAssessment):
        """
        Store risk assessment in Neo4j for learning and pattern recognition
        """
        try:
            with self.neo4j_driver.session() as session:
                session.run("""
                    CREATE (c:Clause {
                        text: $clause_text,
                        risk_level: $risk_level,
                        risk_score: $risk_score,
                        severity: $severity,
                        confidence: $confidence,
                        reasons: $reasons,
                        timestamp: datetime()
                    })
                """, 
                clause_text=clause_text,
                risk_level=risk_assessment.level.value,
                risk_score=risk_assessment.score,
                severity=risk_assessment.severity,
                confidence=risk_assessment.confidence,
                reasons=risk_assessment.reasons
                )
        except Exception as e:
            print(f"Neo4j storage error: {e}")
            # Continue without storing - don't fail the analysis
    
    def get_similar_clauses(self, clause_text: str, limit: int = 5) -> List[Dict]:
        """
        Find similar clauses from Neo4j database for pattern learning
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (c:Clause)
                    WHERE c.text CONTAINS $search_term
                    RETURN c.text as text, c.risk_level as risk_level, 
                           c.risk_score as risk_score, c.reasons as reasons
                    ORDER BY c.timestamp DESC
                    LIMIT $limit
                """, search_term=clause_text[:50], limit=limit)
                
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Neo4j query error: {e}")
            return []
    
    def close(self):
        """Close database connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

class MockTranslationService:
    """
    Mock Google Translate API integration for multilingual support
    Requirements: Add mock Google Translate API integration for multilingual support
    """
    
    def __init__(self):
        # Mock supported languages
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'hi': 'Hindi',
            'zh': 'Chinese'
        }
        
        # Mock translations for common legal terms
        self.mock_translations = {
            'es': {
                'rental agreement': 'contrato de alquiler',
                'security deposit': 'depósito de seguridad',
                'tenant': 'inquilino',
                'landlord': 'propietario',
                'high risk': 'alto riesgo',
                'medium risk': 'riesgo medio',
                'low risk': 'bajo riesgo'
            },
            'fr': {
                'rental agreement': 'contrat de location',
                'security deposit': 'dépôt de garantie',
                'tenant': 'locataire',
                'landlord': 'propriétaire',
                'high risk': 'risque élevé',
                'medium risk': 'risque moyen',
                'low risk': 'faible risque'
            }
        }
    
    def translate_text(self, text: str, target_language: str) -> Dict[str, str]:
        """Mock translation of text to target language"""
        if target_language not in self.supported_languages:
            return {
                'success': False,
                'error': f'Language {target_language} not supported',
                'translated_text': text
            }
        
        # Mock translation using predefined mappings
        translated_text = text.lower()
        if target_language in self.mock_translations:
            for english_term, translated_term in self.mock_translations[target_language].items():
                translated_text = translated_text.replace(english_term, translated_term)
        
        return {
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language,
            'language_name': self.supported_languages[target_language]
        }
    
    def detect_language(self, text: str) -> Dict[str, str]:
        """Mock language detection"""
        # Simple mock detection based on common words
        spanish_indicators = ['contrato', 'alquiler', 'inquilino', 'propietario']
        french_indicators = ['contrat', 'location', 'locataire', 'propriétaire']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in spanish_indicators):
            return {'language': 'es', 'confidence': 0.85}
        elif any(word in text_lower for word in french_indicators):
            return {'language': 'fr', 'confidence': 0.85}
        else:
            return {'language': 'en', 'confidence': 0.90}

class MockVertexAIService:
    """
    Mock Vertex AI Generative AI integration for conversational clarification
    Requirements: Add mock Vertex AI Generative AI integration for conversational clarification
    """
    
    def __init__(self):
        self.conversation_history = []
        
        # Mock responses for common questions
        self.mock_responses = {
            'what does this mean': 'This clause means that the landlord has specific rights or the tenant has certain obligations. Let me break it down in simpler terms.',
            'is this fair': 'Based on standard rental practices, this clause appears to be [fair/unfair/concerning]. Here\'s why:',
            'should i sign': 'Before signing, consider these factors: 1) Your comfort with the terms, 2) Local rental laws, 3) Alternative options available.',
            'can i negotiate': 'Yes, many rental terms are negotiable. Focus on the high-risk items we identified, especially around deposits, fees, and tenant rights.',
            'what are my rights': 'As a tenant, you typically have rights to: privacy, habitability, fair treatment, and proper notice for changes or entry.'
        }
    
    def ask_clarification(self, question: str, context: Dict = None) -> Dict[str, str]:
        """Mock conversational AI for document clarification"""
        question_lower = question.lower()
        
        # Find best matching response
        best_response = "I understand you're asking about your rental agreement. Could you be more specific about which clause or term you'd like me to explain?"
        
        for trigger, response in self.mock_responses.items():
            if trigger in question_lower:
                best_response = response
                break
        
        # Add context-aware information if available
        if context and 'risk_level' in context:
            risk_level = context['risk_level']
            if risk_level == 'RED':
                best_response += f"\n\n⚠️ This is particularly important because we identified this as a HIGH RISK clause."
            elif risk_level == 'YELLOW':
                best_response += f"\n\n⚠️ This clause has MEDIUM RISK - worth discussing with the landlord."
        
        # Store in conversation history
        self.conversation_history.append({
            'question': question,
            'response': best_response,
            'timestamp': 'mock_timestamp'
        })
        
        return {
            'success': True,
            'response': best_response,
            'confidence': 0.75,
            'follow_up_suggestions': [
                'Can you explain this in simpler terms?',
                'What should I do about this clause?',
                'Is this legal in my area?'
            ]
        }
    
    def get_conversation_summary(self) -> Dict[str, any]:
        """Get summary of conversation for context"""
        return {
            'total_questions': len(self.conversation_history),
            'recent_topics': [item['question'][:50] + '...' for item in self.conversation_history[-3:]],
            'conversation_history': self.conversation_history
        }

# Utility function for easy integration
def classify_document_risk(document_text: str) -> Dict:
    """
    Classify risk for an entire document by analyzing it in chunks
    """
    classifier = RiskClassifier()
    
    try:
        # Split document into clauses (simple sentence-based splitting)
        clauses = re.split(r'[.!?]+', document_text)
        clauses = [clause.strip() for clause in clauses if len(clause.strip()) > 20]
        
        clause_assessments = []
        overall_scores = []
        
        for i, clause in enumerate(clauses[:10]):  # Limit to first 10 clauses for performance
            assessment = classifier.classify_risk_level(clause)
            clause_assessments.append({
                'clause_id': f'clause_{i+1}',
                'text': clause,
                'assessment': assessment
            })
            overall_scores.append(assessment.score)
        
        # Calculate overall document risk
        if overall_scores:
            avg_score = sum(overall_scores) / len(overall_scores)
            max_score = max(overall_scores)
            
            # Overall risk is weighted average with emphasis on highest risk
            overall_score = (avg_score * 0.6) + (max_score * 0.4)
            
            if overall_score > 0.7:
                overall_level = RiskLevel.RED
                overall_severity = "High"
            elif overall_score > 0.4:
                overall_level = RiskLevel.YELLOW
                overall_severity = "Medium"
            else:
                overall_level = RiskLevel.GREEN
                overall_severity = "Low"
        else:
            overall_level = RiskLevel.YELLOW
            overall_severity = "Medium"
            overall_score = 0.5
        
        # Calculate overall confidence and categories
        if clause_assessments:
            overall_confidence = sum(assessment['assessment'].confidence for assessment in clause_assessments) / len(clause_assessments)
            overall_confidence_percentage = int(overall_confidence * 100)
            
            # Aggregate category scores
            overall_categories = {'financial': 0.0, 'legal': 0.0, 'operational': 0.0}
            for assessment in clause_assessments:
                for category, score in assessment['assessment'].risk_categories.items():
                    overall_categories[category] += score
            
            # Average category scores
            for category in overall_categories:
                overall_categories[category] /= len(clause_assessments)
            
            low_confidence_warning = overall_confidence_percentage < 70
        else:
            overall_confidence = 0.5
            overall_confidence_percentage = 50
            overall_categories = {'financial': 0.5, 'legal': 0.5, 'operational': 0.5}
            low_confidence_warning = True
        
        return {
            'overall_risk': {
                'level': overall_level.value,
                'score': overall_score,
                'severity': overall_severity,
                'confidence_percentage': overall_confidence_percentage,
                'risk_categories': overall_categories,
                'low_confidence_warning': low_confidence_warning
            },
            'clause_assessments': clause_assessments,
            'total_clauses_analyzed': len(clause_assessments),
            'analysis_metadata': {
                'translation_service': MockTranslationService(),
                'ai_clarification': MockVertexAIService()
            }
        }
        
    finally:
        classifier.close()