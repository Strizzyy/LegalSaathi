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

@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float  # 0.0 to 1.0
    reasons: List[str]
    severity: str
    confidence: float

@dataclass
class RedFlag:
    pattern: str
    description: str
    risk_level: RiskLevel
    weight: float

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
        """Load predefined red flag patterns for keyword-based detection"""
        return [
            # High-risk patterns (RED)
            RedFlag(
                pattern=r"non-refundable.*deposit|deposit.*non-refundable",
                description="Non-refundable security deposit",
                risk_level=RiskLevel.RED,
                weight=0.9
            ),
            RedFlag(
                pattern=r"unlimited.*liability|liability.*unlimited",
                description="Unlimited liability clause",
                risk_level=RiskLevel.RED,
                weight=0.95
            ),
            RedFlag(
                pattern=r"waive.*right|forfeit.*right|surrender.*right",
                description="Rights waiver clause",
                risk_level=RiskLevel.RED,
                weight=0.85
            ),
            RedFlag(
                pattern=r"no.*notice.*entry|entry.*without.*notice",
                description="No notice entry clause",
                risk_level=RiskLevel.RED,
                weight=0.8
            ),
            RedFlag(
                pattern=r"automatic.*renewal|auto.*renew",
                description="Automatic renewal without consent",
                risk_level=RiskLevel.RED,
                weight=0.7
            ),
            
            # Medium-risk patterns (YELLOW)
            RedFlag(
                pattern=r"late.*fee.*\$[0-9]{3,}|penalty.*\$[0-9]{3,}",
                description="Excessive late fees",
                risk_level=RiskLevel.YELLOW,
                weight=0.6
            ),
            RedFlag(
                pattern=r"inspection.*daily|daily.*inspection",
                description="Excessive inspection frequency",
                risk_level=RiskLevel.YELLOW,
                weight=0.5
            ),
            RedFlag(
                pattern=r"no.*pets.*allowed|pets.*prohibited",
                description="Strict pet policy",
                risk_level=RiskLevel.YELLOW,
                weight=0.3
            ),
            RedFlag(
                pattern=r"subletting.*prohibited|no.*subletting",
                description="Subletting restrictions",
                risk_level=RiskLevel.YELLOW,
                weight=0.4
            ),
            RedFlag(
                pattern=r"rent.*increase.*[0-9]{2,}%",
                description="High rent increase percentage",
                risk_level=RiskLevel.YELLOW,
                weight=0.6
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
        Detect red flags using keyword-based pattern matching
        """
        text_lower = text.lower()
        detected_flags = []
        total_weight = 0.0
        max_risk_level = RiskLevel.GREEN
        
        for flag in self.red_flag_patterns:
            if re.search(flag.pattern, text_lower, re.IGNORECASE):
                detected_flags.append(flag.description)
                total_weight += flag.weight
                
                # Update max risk level
                if flag.risk_level == RiskLevel.RED:
                    max_risk_level = RiskLevel.RED
                elif flag.risk_level == RiskLevel.YELLOW and max_risk_level != RiskLevel.RED:
                    max_risk_level = RiskLevel.YELLOW
        
        # Calculate risk score
        risk_score = min(total_weight, 1.0)
        
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
        
        return RiskAssessment(
            level=final_level,
            score=risk_score,
            reasons=reasons,
            severity=severity,
            confidence=0.8  # High confidence for keyword matching
        )
    
    def _get_ai_risk_assessment(self, clause_text: str) -> RiskAssessment:
        """
        Get AI-based risk assessment using Groq for simple analysis
        """
        try:
            # Use Groq for quick risk assessment
            prompt = f"""
            Analyze this rental agreement clause for risk level. Respond with JSON only:
            
            Clause: "{clause_text}"
            
            Provide assessment in this exact JSON format:
            {{
                "risk_level": "RED|YELLOW|GREEN",
                "risk_score": 0.0-1.0,
                "reasons": ["reason1", "reason2"],
                "severity": "High|Medium|Low",
                "confidence": 0.0-1.0
            }}
            
            Risk Guidelines:
            - RED: Unfair, illegal, or heavily biased against tenant
            - YELLOW: Concerning terms that could be improved
            - GREEN: Fair and standard terms
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a legal expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(0))
                
                return RiskAssessment(
                    level=RiskLevel(ai_data.get('risk_level', 'YELLOW')),
                    score=float(ai_data.get('risk_score', 0.5)),
                    reasons=ai_data.get('reasons', ['AI analysis completed']),
                    severity=ai_data.get('severity', 'Medium'),
                    confidence=float(ai_data.get('confidence', 0.7))
                )
            
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
            confidence=0.3
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
                
                return RiskAssessment(
                    level=RiskLevel(ai_data.get('risk_level', 'YELLOW')),
                    score=float(ai_data.get('risk_score', 0.5)),
                    reasons=ai_data.get('reasons', ['Gemini analysis completed']),
                    severity=ai_data.get('severity', 'Medium'),
                    confidence=float(ai_data.get('confidence', 0.8))
                )
                
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        # Final fallback
        return RiskAssessment(
            level=RiskLevel.YELLOW,
            score=0.5,
            reasons=["AI services unavailable - manual review recommended"],
            severity="Medium",
            confidence=0.2
        )
    
    def _combine_risk_assessments(self, keyword_risk: RiskAssessment, ai_risk: RiskAssessment) -> RiskAssessment:
        """
        Combine keyword-based and AI-based risk assessments
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
            combined_reasons.extend([f"Keyword: {reason}" for reason in keyword_risk.reasons])
        combined_reasons.extend([f"AI: {reason}" for reason in ai_risk.reasons])
        
        # Determine severity
        if final_level == RiskLevel.RED:
            severity = "High"
        elif final_level == RiskLevel.YELLOW:
            severity = "Medium"
        else:
            severity = "Low"
        
        # Combine confidence
        combined_confidence = (keyword_risk.confidence * keyword_weight) + (ai_risk.confidence * ai_weight)
        
        return RiskAssessment(
            level=final_level,
            score=combined_score,
            reasons=combined_reasons,
            severity=severity,
            confidence=combined_confidence
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
        
        return {
            'overall_risk': {
                'level': overall_level.value,
                'score': overall_score,
                'severity': overall_severity
            },
            'clause_assessments': clause_assessments,
            'total_clauses_analyzed': len(clause_assessments)
        }
        
    finally:
        classifier.close()