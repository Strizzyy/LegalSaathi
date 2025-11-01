"""
Confidence Calculator Service for Human-in-the-Loop System
Calculates weighted average confidence scores from AI analysis components
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceComponent(Enum):
    """Components that contribute to overall confidence calculation"""
    CLAUSE_ANALYSIS = "clause_analysis"
    DOCUMENT_SUMMARY = "document_summary"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class ConfidenceBreakdown:
    """Detailed breakdown of confidence calculation"""
    overall_confidence: float
    clause_confidences: Dict[str, float]
    section_confidences: Dict[str, float]
    component_weights: Dict[str, float]
    factors_affecting_confidence: List[str]
    improvement_suggestions: List[str]


class ConfidenceCalculatorService:
    """Service for calculating AI confidence scores and determining expert review routing"""
    
    def __init__(self):
        # Default confidence weights - can be adjusted based on analysis
        self.confidence_weights = {
            ConfidenceComponent.CLAUSE_ANALYSIS.value: 0.4,
            ConfidenceComponent.DOCUMENT_SUMMARY.value: 0.3,
            ConfidenceComponent.RISK_ASSESSMENT.value: 0.3
        }
        
        # Threshold for expert review routing
        self.expert_review_threshold = 0.99
        
        # Minimum confidence thresholds for each component
        self.component_thresholds = {
            ConfidenceComponent.CLAUSE_ANALYSIS.value: 0.99,
            ConfidenceComponent.DOCUMENT_SUMMARY.value: 0.99,
            ConfidenceComponent.RISK_ASSESSMENT.value: 0.99
        }
    
    def calculate_overall_confidence(self, analysis_result: Dict[str, Any]) -> float:
        """
        Calculate weighted average confidence score from AI analysis components
        
        Args:
            analysis_result: Dictionary containing AI analysis with confidence scores
            
        Returns:
            float: Overall confidence score (0.0 to 1.0)
        """
        try:
            component_confidences = self._extract_component_confidences(analysis_result)
            
            if not component_confidences:
                logger.warning("No confidence scores found in analysis result")
                return 0.0
            
            # Calculate weighted average
            weighted_sum = 0.0
            total_weight = 0.0
            
            for component, confidence in component_confidences.items():
                weight = self.confidence_weights.get(component, 0.0)
                weighted_sum += confidence * weight
                total_weight += weight
            
            # Normalize by total weight to handle missing components
            overall_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
            
            # Apply penalty for missing critical components
            penalty = self._calculate_missing_component_penalty(component_confidences)
            overall_confidence = max(0.0, overall_confidence - penalty)
            
            logger.info(f"Calculated overall confidence: {overall_confidence:.3f}")
            return round(overall_confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {e}")
            return 0.0
    
    def should_route_to_expert(self, confidence: float) -> bool:
        """
        Determine if document should be routed to expert based on confidence
        
        Args:
            confidence: Overall confidence score (0.0 to 1.0)
            
        Returns:
            bool: True if should route to expert, False otherwise
        """
        return confidence < self.expert_review_threshold
    
    def get_confidence_breakdown(self, analysis_result: Dict[str, Any]) -> ConfidenceBreakdown:
        """
        Get detailed breakdown of confidence calculation
        
        Args:
            analysis_result: Dictionary containing AI analysis with confidence scores
            
        Returns:
            ConfidenceBreakdown: Detailed confidence analysis
        """
        try:
            component_confidences = self._extract_component_confidences(analysis_result)
            clause_confidences = self._extract_clause_confidences(analysis_result)
            section_confidences = self._extract_section_confidences(analysis_result)
            
            overall_confidence = self.calculate_overall_confidence(analysis_result)
            
            factors_affecting_confidence = self._identify_confidence_factors(
                component_confidences, clause_confidences
            )
            
            improvement_suggestions = self._generate_improvement_suggestions(
                component_confidences, overall_confidence
            )
            
            return ConfidenceBreakdown(
                overall_confidence=overall_confidence,
                clause_confidences=clause_confidences,
                section_confidences=section_confidences,
                component_weights=self.confidence_weights,
                factors_affecting_confidence=factors_affecting_confidence,
                improvement_suggestions=improvement_suggestions
            )
            
        except Exception as e:
            logger.error(f"Error generating confidence breakdown: {e}")
            return ConfidenceBreakdown(
                overall_confidence=0.0,
                clause_confidences={},
                section_confidences={},
                component_weights=self.confidence_weights,
                factors_affecting_confidence=["Error calculating confidence"],
                improvement_suggestions=["Please try analyzing the document again"]
            )
    
    def _extract_component_confidences(self, analysis_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract confidence scores for each analysis component"""
        confidences = {}
        
        try:
            # Extract clause analysis confidence
            if 'clause_analysis' in analysis_result:
                clause_data = analysis_result['clause_analysis']
                if isinstance(clause_data, list):
                    # Average confidence across all clauses
                    clause_confidences = []
                    for clause in clause_data:
                        if isinstance(clause, dict) and 'confidence_percentage' in clause:
                            clause_confidences.append(clause['confidence_percentage'] / 100.0)
                        elif isinstance(clause, dict) and 'risk_level' in clause:
                            risk_level = clause['risk_level']
                            if isinstance(risk_level, dict) and 'confidence_percentage' in risk_level:
                                clause_confidences.append(risk_level['confidence_percentage'] / 100.0)
                    
                    if clause_confidences:
                        confidences[ConfidenceComponent.CLAUSE_ANALYSIS.value] = sum(clause_confidences) / len(clause_confidences)
            
            # Extract document summary confidence
            if 'document_summary' in analysis_result:
                summary_data = analysis_result['document_summary']
                if isinstance(summary_data, dict):
                    if 'confidence_score' in summary_data:
                        confidences[ConfidenceComponent.DOCUMENT_SUMMARY.value] = summary_data['confidence_score']
                    elif 'confidence_percentage' in summary_data:
                        confidences[ConfidenceComponent.DOCUMENT_SUMMARY.value] = summary_data['confidence_percentage'] / 100.0
            
            # Extract risk assessment confidence
            if 'risk_assessment' in analysis_result:
                risk_data = analysis_result['risk_assessment']
                if isinstance(risk_data, dict):
                    if 'confidence_score' in risk_data:
                        confidences[ConfidenceComponent.RISK_ASSESSMENT.value] = risk_data['confidence_score']
                    elif 'confidence_percentage' in risk_data:
                        confidences[ConfidenceComponent.RISK_ASSESSMENT.value] = risk_data['confidence_percentage'] / 100.0
            
            # Fallback: look for overall confidence in response
            if not confidences and 'confidence_score' in analysis_result:
                # Use overall confidence for all components if individual scores not available
                overall_conf = analysis_result['confidence_score']
                if isinstance(overall_conf, (int, float)):
                    conf_value = overall_conf / 100.0 if overall_conf > 1.0 else overall_conf
                    for component in self.confidence_weights.keys():
                        confidences[component] = conf_value
            
        except Exception as e:
            logger.error(f"Error extracting component confidences: {e}")
        
        return confidences
    
    def _extract_clause_confidences(self, analysis_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract confidence scores for individual clauses"""
        clause_confidences = {}
        
        try:
            if 'clause_analysis' in analysis_result:
                clause_data = analysis_result['clause_analysis']
                if isinstance(clause_data, list):
                    for i, clause in enumerate(clause_data):
                        if isinstance(clause, dict):
                            clause_id = clause.get('clause_id', f'clause_{i+1}')
                            
                            # Try different confidence field names
                            confidence = None
                            if 'confidence_percentage' in clause:
                                confidence = clause['confidence_percentage'] / 100.0
                            elif 'risk_level' in clause and isinstance(clause['risk_level'], dict):
                                risk_level = clause['risk_level']
                                if 'confidence_percentage' in risk_level:
                                    confidence = risk_level['confidence_percentage'] / 100.0
                            
                            if confidence is not None:
                                clause_confidences[clause_id] = confidence
        
        except Exception as e:
            logger.error(f"Error extracting clause confidences: {e}")
        
        return clause_confidences
    
    def _extract_section_confidences(self, analysis_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract confidence scores for document sections"""
        section_confidences = {}
        
        try:
            # Group clauses by section if section information is available
            if 'clause_analysis' in analysis_result:
                clause_data = analysis_result['clause_analysis']
                if isinstance(clause_data, list):
                    section_groups = {}
                    
                    for clause in clause_data:
                        if isinstance(clause, dict):
                            section = clause.get('section', 'general')
                            if section not in section_groups:
                                section_groups[section] = []
                            
                            # Get clause confidence
                            confidence = None
                            if 'confidence_percentage' in clause:
                                confidence = clause['confidence_percentage'] / 100.0
                            elif 'risk_level' in clause and isinstance(clause['risk_level'], dict):
                                risk_level = clause['risk_level']
                                if 'confidence_percentage' in risk_level:
                                    confidence = risk_level['confidence_percentage'] / 100.0
                            
                            if confidence is not None:
                                section_groups[section].append(confidence)
                    
                    # Calculate average confidence per section
                    for section, confidences in section_groups.items():
                        if confidences:
                            section_confidences[section] = sum(confidences) / len(confidences)
        
        except Exception as e:
            logger.error(f"Error extracting section confidences: {e}")
        
        return section_confidences
    
    def _calculate_missing_component_penalty(self, component_confidences: Dict[str, float]) -> float:
        """Calculate penalty for missing critical analysis components"""
        penalty = 0.0
        
        # Penalty for each missing component
        for component in self.confidence_weights.keys():
            if component not in component_confidences:
                penalty += 0.1  # 10% penalty per missing component
        
        return penalty
    
    def _identify_confidence_factors(self, component_confidences: Dict[str, float], 
                                   clause_confidences: Dict[str, float]) -> List[str]:
        """Identify factors that are affecting confidence scores"""
        factors = []
        
        try:
            # Check component-level factors
            for component, confidence in component_confidences.items():
                threshold = self.component_thresholds.get(component, 0.6)
                if confidence < threshold:
                    component_name = component.replace('_', ' ').title()
                    factors.append(f"Low {component_name} confidence ({confidence:.1%})")
            
            # Check clause-level factors
            low_confidence_clauses = [
                clause_id for clause_id, confidence in clause_confidences.items()
                if confidence < 0.6
            ]
            
            if low_confidence_clauses:
                if len(low_confidence_clauses) == 1:
                    factors.append(f"Low confidence in {low_confidence_clauses[0]}")
                else:
                    factors.append(f"Low confidence in {len(low_confidence_clauses)} clauses")
            
            # Check for missing components
            missing_components = [
                comp for comp in self.confidence_weights.keys()
                if comp not in component_confidences
            ]
            
            if missing_components:
                factors.append(f"Missing analysis for {', '.join(missing_components)}")
            
        except Exception as e:
            logger.error(f"Error identifying confidence factors: {e}")
            factors.append("Error analyzing confidence factors")
        
        return factors
    
    def _generate_improvement_suggestions(self, component_confidences: Dict[str, float], 
                                        overall_confidence: float) -> List[str]:
        """Generate suggestions for improving confidence"""
        suggestions = []
        
        try:
            if overall_confidence < self.expert_review_threshold:
                suggestions.append("Consider expert review for more accurate analysis")
            
            # Component-specific suggestions
            for component, confidence in component_confidences.items():
                threshold = self.component_thresholds.get(component, 0.6)
                if confidence < threshold:
                    if component == ConfidenceComponent.CLAUSE_ANALYSIS.value:
                        suggestions.append("Document contains complex clauses requiring expert interpretation")
                    elif component == ConfidenceComponent.DOCUMENT_SUMMARY.value:
                        suggestions.append("Document structure or content is unclear")
                    elif component == ConfidenceComponent.RISK_ASSESSMENT.value:
                        suggestions.append("Risk factors are difficult to assess automatically")
            
            # General suggestions
            if overall_confidence < 0.4:
                suggestions.append("Document may require specialized legal expertise")
            elif overall_confidence < 0.6:
                suggestions.append("Some sections may benefit from human review")
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
            suggestions.append("Unable to generate specific suggestions")
        
        return suggestions


# Global instance
confidence_calculator = ConfidenceCalculatorService()