"""
Analysis Enhancement Services
Combines confidence calculation, personalization, and enhanced experience functionality
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ExperienceLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class AnalysisEnhancementServices:
    """Consolidated services for analysis enhancement, confidence calculation, and personalization"""
    
    def __init__(self):
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        self.user_profiles = {}  # In production, use database
        logger.info("✅ Analysis enhancement services initialized")
    
    # Confidence Calculation Methods
    def calculate_confidence_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for analysis results"""
        try:
            factors = []
            
            # Text length factor
            text_length = len(analysis_data.get('text', ''))
            if text_length > 1000:
                factors.append(0.9)
            elif text_length > 500:
                factors.append(0.7)
            else:
                factors.append(0.5)
            
            # Number of clauses factor
            clauses_count = len(analysis_data.get('clauses', []))
            if clauses_count > 10:
                factors.append(0.9)
            elif clauses_count > 5:
                factors.append(0.7)
            else:
                factors.append(0.6)
            
            # AI service availability factor
            ai_services_used = analysis_data.get('services_used', [])
            if len(ai_services_used) >= 2:
                factors.append(0.9)
            elif len(ai_services_used) == 1:
                factors.append(0.7)
            else:
                factors.append(0.4)
            
            # Processing time factor (faster = higher confidence in simple cases)
            processing_time = analysis_data.get('processing_time', 0)
            if processing_time < 5:
                factors.append(0.8)
            elif processing_time < 15:
                factors.append(0.9)
            else:
                factors.append(0.7)
            
            # Calculate weighted average
            confidence = sum(factors) / len(factors) if factors else 0.5
            return min(0.95, max(0.1, confidence))  # Clamp between 0.1 and 0.95
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5  # Default confidence
    
    def calculate_overall_confidence(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall confidence for expert review routing"""
        try:
            # Extract components for confidence calculation
            clauses = analysis_data.get('clauses', [])
            document_summary = analysis_data.get('document_summary', {})
            risk_assessment = analysis_data.get('risk_assessment', {})
            
            # Component weights (as per your specification)
            clause_weight = 0.4  # 40%
            summary_weight = 0.3  # 30%
            risk_weight = 0.3    # 30%
            
            # Calculate clause analysis confidence
            clause_confidences = []
            for clause in clauses:
                clause_conf = self.calculate_clause_confidence(clause)
                clause_confidences.append(clause_conf)
            
            clause_confidence = sum(clause_confidences) / len(clause_confidences) if clause_confidences else 0.5
            
            # Calculate document summary confidence
            summary_confidence = 0.8  # Default high confidence for summary
            if document_summary:
                summary_length = len(str(document_summary))
                if summary_length > 200:
                    summary_confidence = 0.9
                elif summary_length > 100:
                    summary_confidence = 0.8
                else:
                    summary_confidence = 0.6
            
            # Calculate risk assessment confidence
            risk_confidence = 0.7  # Default confidence
            if risk_assessment:
                risk_level = risk_assessment.get('level', 'medium')
                risk_factors = risk_assessment.get('factors', [])
                
                if len(risk_factors) >= 3:
                    risk_confidence = 0.9
                elif len(risk_factors) >= 1:
                    risk_confidence = 0.8
                else:
                    risk_confidence = 0.6
            
            # Calculate weighted overall confidence
            overall_confidence = (
                clause_confidence * clause_weight +
                summary_confidence * summary_weight +
                risk_confidence * risk_weight
            )
            
            # Determine if expert review is needed (threshold < 0.6)
            needs_expert_review = overall_confidence < 0.6
            
            # Determine priority level
            if overall_confidence < 0.4:
                priority = "HIGH"
            elif overall_confidence < 0.6:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            return {
                'overall_confidence': overall_confidence,
                'component_confidences': {
                    'clause_analysis': clause_confidence,
                    'document_summary': summary_confidence,
                    'risk_assessment': risk_confidence
                },
                'needs_expert_review': needs_expert_review,
                'expert_priority': priority,
                'confidence_threshold': 0.6,
                'calculation_method': 'weighted_average'
            }
            
        except Exception as e:
            logger.error(f"Overall confidence calculation failed: {e}")
            return {
                'overall_confidence': 0.5,
                'component_confidences': {
                    'clause_analysis': 0.5,
                    'document_summary': 0.5,
                    'risk_assessment': 0.5
                },
                'needs_expert_review': True,
                'expert_priority': "MEDIUM",
                'confidence_threshold': 0.6,
                'calculation_method': 'fallback'
            }

    def calculate_clause_confidence(self, clause_data: Dict[str, Any]) -> float:
        """Calculate confidence score for individual clause analysis"""
        try:
            factors = []
            
            # Risk level certainty
            risk_level = clause_data.get('risk_level', 'medium')
            risk_keywords = clause_data.get('risk_keywords', [])
            
            if len(risk_keywords) >= 3:
                factors.append(0.9)
            elif len(risk_keywords) >= 1:
                factors.append(0.7)
            else:
                factors.append(0.5)
            
            # Clause length and complexity
            clause_text = clause_data.get('text', '')
            if len(clause_text) > 200:
                factors.append(0.8)
            elif len(clause_text) > 50:
                factors.append(0.7)
            else:
                factors.append(0.6)
            
            # Legal term detection
            legal_terms = clause_data.get('legal_terms', [])
            if len(legal_terms) >= 2:
                factors.append(0.8)
            elif len(legal_terms) >= 1:
                factors.append(0.6)
            else:
                factors.append(0.4)
            
            return sum(factors) / len(factors) if factors else 0.5
            
        except Exception as e:
            logger.error(f"Clause confidence calculation failed: {e}")
            return 0.5
    
    # Personalization Methods
    def personalize_analysis(self, analysis_data: Dict[str, Any], user_expertise: str, user_id: str = None) -> Dict[str, Any]:
        """Personalize analysis results based on user expertise level"""
        try:
            expertise_level = ExperienceLevel(user_expertise.lower())
            
            # Get or create user profile
            if user_id:
                profile = self._get_user_profile(user_id)
                profile['last_analysis'] = datetime.now().isoformat()
                profile['expertise_level'] = user_expertise
                self.user_profiles[user_id] = profile
            
            # Personalize based on expertise level
            if expertise_level == ExperienceLevel.BEGINNER:
                return self._personalize_for_beginner(analysis_data)
            elif expertise_level == ExperienceLevel.INTERMEDIATE:
                return self._personalize_for_intermediate(analysis_data)
            elif expertise_level == ExperienceLevel.ADVANCED:
                return self._personalize_for_advanced(analysis_data)
            else:  # EXPERT
                return self._personalize_for_expert(analysis_data)
                
        except Exception as e:
            logger.error(f"Personalization failed: {e}")
            return analysis_data  # Return original if personalization fails
    
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'analysis_count': 0,
                'expertise_level': 'beginner',
                'preferences': {}
            }
        
        profile = self.user_profiles[user_id]
        profile['analysis_count'] = profile.get('analysis_count', 0) + 1
        return profile
    
    def _personalize_for_beginner(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize for beginner users"""
        # Add explanations and simplify language
        personalized = analysis_data.copy()
        
        # Add beginner-friendly explanations
        if 'clauses' in personalized:
            for clause in personalized['clauses']:
                clause['beginner_explanation'] = self._generate_beginner_explanation(clause)
                clause['simplified_risk'] = self._simplify_risk_explanation(clause.get('risk_level', 'medium'))
        
        # Add overall guidance
        personalized['beginner_guidance'] = {
            'next_steps': [
                "Review each highlighted clause carefully",
                "Pay special attention to high-risk items",
                "Consider consulting a legal professional for complex terms",
                "Ask questions about anything you don't understand"
            ],
            'learning_resources': [
                "Legal terminology glossary available in help section",
                "Common contract clause explanations",
                "When to seek professional legal advice"
            ]
        }
        
        return personalized
    
    def _personalize_for_intermediate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize for intermediate users"""
        personalized = analysis_data.copy()
        
        # Add intermediate-level insights
        if 'clauses' in personalized:
            for clause in personalized['clauses']:
                clause['negotiation_tips'] = self._generate_negotiation_tips(clause)
                clause['alternative_language'] = self._suggest_alternative_language(clause)
        
        # Add strategic guidance
        personalized['strategic_guidance'] = {
            'negotiation_priorities': self._identify_negotiation_priorities(analysis_data),
            'risk_mitigation': self._suggest_risk_mitigation(analysis_data),
            'market_standards': "Consider industry-standard terms for similar agreements"
        }
        
        return personalized
    
    def _personalize_for_advanced(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize for advanced users"""
        personalized = analysis_data.copy()
        
        # Add advanced legal analysis
        if 'clauses' in personalized:
            for clause in personalized['clauses']:
                clause['legal_precedents'] = self._find_relevant_precedents(clause)
                clause['compliance_considerations'] = self._analyze_compliance(clause)
        
        # Add sophisticated insights
        personalized['advanced_insights'] = {
            'legal_strategy': self._develop_legal_strategy(analysis_data),
            'regulatory_compliance': self._check_regulatory_compliance(analysis_data),
            'cross_references': self._find_clause_cross_references(analysis_data)
        }
        
        return personalized
    
    def _personalize_for_expert(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize for expert users"""
        personalized = analysis_data.copy()
        
        # Add expert-level analysis
        personalized['expert_analysis'] = {
            'technical_accuracy': self._assess_technical_accuracy(analysis_data),
            'jurisdictional_considerations': self._analyze_jurisdictional_issues(analysis_data),
            'drafting_suggestions': self._provide_drafting_suggestions(analysis_data),
            'case_law_references': self._find_case_law_references(analysis_data)
        }
        
        return personalized
    
    # Helper methods for personalization
    def _generate_beginner_explanation(self, clause: Dict[str, Any]) -> str:
        """Generate beginner-friendly explanation for a clause"""
        risk_level = clause.get('risk_level', 'medium')
        clause_type = clause.get('type', 'general')
        
        explanations = {
            'liability': "This clause determines who is responsible if something goes wrong.",
            'termination': "This clause explains how and when the agreement can be ended.",
            'payment': "This clause covers when and how payments should be made.",
            'confidentiality': "This clause protects sensitive information from being shared.",
            'intellectual_property': "This clause determines who owns ideas and creations."
        }
        
        return explanations.get(clause_type, "This clause contains important terms that affect your rights and obligations.")
    
    def _simplify_risk_explanation(self, risk_level: str) -> str:
        """Simplify risk level explanation"""
        explanations = {
            'high': "⚠️ High Risk: This could significantly impact you. Consider legal advice.",
            'medium': "⚡ Medium Risk: Important to understand. May need clarification.",
            'low': "✅ Low Risk: Standard terms, but still worth reviewing."
        }
        return explanations.get(risk_level, "Review this clause carefully.")
    
    def _generate_negotiation_tips(self, clause: Dict[str, Any]) -> List[str]:
        """Generate negotiation tips for intermediate users"""
        return [
            "Consider proposing mutual terms where applicable",
            "Ask for specific timeframes instead of vague language",
            "Ensure terms are balanced for both parties"
        ]
    
    def _suggest_alternative_language(self, clause: Dict[str, Any]) -> str:
        """Suggest alternative language for clauses"""
        return "Consider more balanced language that protects both parties' interests."
    
    def _identify_negotiation_priorities(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Identify key negotiation priorities"""
        return [
            "Focus on high-risk clauses first",
            "Ensure payment terms are clear and fair",
            "Clarify termination conditions"
        ]
    
    def _suggest_risk_mitigation(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Suggest risk mitigation strategies"""
        return [
            "Add liability caps where appropriate",
            "Include force majeure provisions",
            "Ensure clear dispute resolution mechanisms"
        ]
    
    # Placeholder methods for advanced features
    def _find_relevant_precedents(self, clause: Dict[str, Any]) -> List[str]:
        return ["Relevant case law and precedents would be analyzed here"]
    
    def _analyze_compliance(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "compliant", "notes": "Standard compliance analysis"}
    
    def _develop_legal_strategy(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"strategy": "Comprehensive legal strategy would be developed here"}
    
    def _check_regulatory_compliance(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "compliant", "regulations": []}
    
    def _find_clause_cross_references(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    def _assess_technical_accuracy(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"accuracy": "high", "notes": "Technical accuracy assessment"}
    
    def _analyze_jurisdictional_issues(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"jurisdiction": "standard", "considerations": []}
    
    def _provide_drafting_suggestions(self, analysis_data: Dict[str, Any]) -> List[str]:
        return ["Expert drafting suggestions would be provided here"]
    
    def _find_case_law_references(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []


# Global instance
analysis_enhancement_services = AnalysisEnhancementServices()