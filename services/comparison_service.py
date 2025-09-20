"""
Document comparison service for FastAPI backend
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.comparison_models import (
    DocumentComparisonRequest, DocumentComparisonResponse,
    DocumentDifference, ClauseComparison, ComparisonSummaryResponse
)
from models.document_models import DocumentAnalysisRequest, RiskAssessment, ClauseAnalysis
from services.document_service import DocumentService
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing legal documents"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.ai_service = AIService()
    
    async def compare_documents(self, request: DocumentComparisonRequest) -> DocumentComparisonResponse:
        """Compare two legal documents and identify key differences"""
        start_time = time.time()
        comparison_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting document comparison: {comparison_id}")
            
            # Validate document content
            if not request.document1_text or not request.document1_text.strip():
                raise ValueError("Document 1 is empty or contains no text")
            
            if not request.document2_text or not request.document2_text.strip():
                raise ValueError("Document 2 is empty or contains no text")
            
            if len(request.document1_text.strip()) < 100:
                raise ValueError("Document 1 must be at least 100 characters long")
            
            if len(request.document2_text.strip()) < 100:
                raise ValueError("Document 2 must be at least 100 characters long")
            
            # Extract meaningful text content
            doc1_text = self._extract_document_text(request.document1_text)
            doc2_text = self._extract_document_text(request.document2_text)
            
            if not doc1_text or not doc2_text:
                raise ValueError("Unable to extract meaningful text from one or both documents")
            
            # Analyze both documents separately
            doc1_request = DocumentAnalysisRequest(
                document_text=request.document1_text,
                document_type=request.document1_type,
                user_expertise_level="intermediate"  # Use intermediate for comparison
            )
            
            doc2_request = DocumentAnalysisRequest(
                document_text=request.document2_text,
                document_type=request.document2_type,
                user_expertise_level="intermediate"
            )
            
            # Perform parallel analysis
            doc1_analysis = await self.document_service.analyze_document(doc1_request)
            doc2_analysis = await self.document_service.analyze_document(doc2_request)
            
            # Compare overall risk levels
            overall_risk_comparison = self._compare_overall_risk(
                doc1_analysis.overall_risk,
                doc2_analysis.overall_risk
            )
            
            # Identify key differences
            key_differences = await self._identify_key_differences(
                doc1_analysis, doc2_analysis, request.comparison_focus
            )
            
            # Compare clauses
            clause_comparisons = self._compare_clauses(
                doc1_analysis.clause_assessments,
                doc2_analysis.clause_assessments
            )
            
            # Generate recommendation summary
            recommendation_summary = await self._generate_comparison_summary(
                doc1_analysis, doc2_analysis, key_differences
            )
            
            # Determine safer document
            safer_document = self._determine_safer_document(
                doc1_analysis.overall_risk,
                doc2_analysis.overall_risk
            )
            
            processing_time = time.time() - start_time
            
            response = DocumentComparisonResponse(
                comparison_id=comparison_id,
                document1_summary={
                    "type": request.document1_type,
                    "overall_risk": doc1_analysis.overall_risk.dict(),
                    "clause_count": len(doc1_analysis.clause_assessments),
                    "processing_time": doc1_analysis.processing_time
                },
                document2_summary={
                    "type": request.document2_type,
                    "overall_risk": doc2_analysis.overall_risk.dict(),
                    "clause_count": len(doc2_analysis.clause_assessments),
                    "processing_time": doc2_analysis.processing_time
                },
                overall_risk_comparison=overall_risk_comparison,
                key_differences=key_differences,
                clause_comparisons=clause_comparisons,
                recommendation_summary=recommendation_summary,
                safer_document=safer_document,
                processing_time=processing_time
            )
            
            logger.info(f"Document comparison completed: {comparison_id}")
            return response
            
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise Exception(f"Comparison failed: {str(e)}")
    
    def _compare_overall_risk(self, risk1: RiskAssessment, risk2: RiskAssessment) -> Dict[str, Any]:
        """Compare overall risk assessments"""
        risk_score_diff = risk1.score - risk2.score
        
        comparison = {
            "document1_risk": {
                "level": risk1.level,
                "score": risk1.score,
                "confidence": risk1.confidence_percentage
            },
            "document2_risk": {
                "level": risk2.level,
                "score": risk2.score,
                "confidence": risk2.confidence_percentage
            },
            "risk_score_difference": risk_score_diff,
            "verdict": self._get_risk_verdict(risk_score_diff),
            "category_differences": self._compare_risk_categories(
                risk1.risk_categories, 
                risk2.risk_categories
            )
        }
        
        return comparison
    
    def _get_risk_verdict(self, risk_diff: float) -> str:
        """Get verdict based on risk difference"""
        if abs(risk_diff) < 0.1:
            return "Similar risk levels"
        elif risk_diff > 0.3:
            return "Document 1 is significantly riskier"
        elif risk_diff > 0.1:
            return "Document 1 is moderately riskier"
        elif risk_diff < -0.3:
            return "Document 2 is significantly riskier"
        elif risk_diff < -0.1:
            return "Document 2 is moderately riskier"
        else:
            return "Slight risk difference"
    
    def _compare_risk_categories(self, categories1: Dict[str, float], categories2: Dict[str, float]) -> Dict[str, float]:
        """Compare risk categories between documents"""
        differences = {}
        all_categories = set(categories1.keys()) | set(categories2.keys())
        
        for category in all_categories:
            score1 = categories1.get(category, 0.0)
            score2 = categories2.get(category, 0.0)
            differences[category] = score1 - score2
        
        return differences
    
    async def _identify_key_differences(
        self, 
        doc1_analysis, 
        doc2_analysis, 
        focus: str
    ) -> List[DocumentDifference]:
        """Identify key differences between documents"""
        differences = []
        
        # Risk level differences
        if doc1_analysis.overall_risk.level != doc2_analysis.overall_risk.level:
            differences.append(DocumentDifference(
                type="risk_level",
                description="Overall risk levels differ between documents",
                document1_value=doc1_analysis.overall_risk.level,
                document2_value=doc2_analysis.overall_risk.level,
                severity="high" if abs(doc1_analysis.overall_risk.score - doc2_analysis.overall_risk.score) > 0.3 else "medium",
                impact="Different risk exposure levels may affect decision making",
                recommendation="Review the document with lower risk or negotiate terms in the riskier document"
            ))
        
        # Clause count differences
        clause_diff = len(doc1_analysis.clause_assessments) - len(doc2_analysis.clause_assessments)
        if abs(clause_diff) > 2:
            differences.append(DocumentDifference(
                type="clause",
                description=f"Significant difference in number of clauses ({abs(clause_diff)} clauses)",
                document1_value=str(len(doc1_analysis.clause_assessments)),
                document2_value=str(len(doc2_analysis.clause_assessments)),
                severity="medium",
                impact="More clauses may indicate more detailed terms or additional obligations",
                recommendation="Review additional clauses for hidden terms or obligations"
            ))
        
        # High-risk clause differences
        doc1_high_risk = sum(1 for clause in doc1_analysis.clause_assessments if clause.risk_assessment.level == "RED")
        doc2_high_risk = sum(1 for clause in doc2_analysis.clause_assessments if clause.risk_assessment.level == "RED")
        
        if doc1_high_risk != doc2_high_risk:
            differences.append(DocumentDifference(
                type="risk_clauses",
                description="Different number of high-risk clauses",
                document1_value=f"{doc1_high_risk} high-risk clauses",
                document2_value=f"{doc2_high_risk} high-risk clauses",
                severity="high" if abs(doc1_high_risk - doc2_high_risk) > 2 else "medium",
                impact="More high-risk clauses increase overall document risk",
                recommendation="Choose document with fewer high-risk clauses or negotiate problematic terms"
            ))
        
        return differences
    
    def _compare_clauses(
        self, 
        clauses1: List[ClauseAnalysis], 
        clauses2: List[ClauseAnalysis]
    ) -> List[ClauseComparison]:
        """Compare clauses between documents"""
        comparisons = []
        
        # Group clauses by type/topic for comparison
        clause_groups1 = self._group_clauses_by_topic(clauses1)
        clause_groups2 = self._group_clauses_by_topic(clauses2)
        
        all_topics = set(clause_groups1.keys()) | set(clause_groups2.keys())
        
        for topic in all_topics:
            clause1 = clause_groups1.get(topic)
            clause2 = clause_groups2.get(topic)
            
            if clause1 and clause2:
                # Both documents have this clause type
                risk_diff = clause1.risk_assessment.score - clause2.risk_assessment.score
                
                comparisons.append(ClauseComparison(
                    clause_type=topic,
                    document1_clause=clause1,
                    document2_clause=clause2,
                    risk_difference=risk_diff,
                    comparison_notes=self._generate_clause_comparison_notes(clause1, clause2, risk_diff),
                    recommendation=self._generate_clause_recommendation(clause1, clause2, risk_diff)
                ))
            elif clause1:
                # Only document 1 has this clause
                comparisons.append(ClauseComparison(
                    clause_type=topic,
                    document1_clause=clause1,
                    document2_clause=None,
                    risk_difference=clause1.risk_assessment.score,
                    comparison_notes=f"This clause only exists in document 1",
                    recommendation="Consider if this clause is necessary or adds unwanted obligations"
                ))
            elif clause2:
                # Only document 2 has this clause
                comparisons.append(ClauseComparison(
                    clause_type=topic,
                    document1_clause=None,
                    document2_clause=clause2,
                    risk_difference=-clause2.risk_assessment.score,
                    comparison_notes=f"This clause only exists in document 2",
                    recommendation="Consider if this clause provides needed protections or adds obligations"
                ))
        
        return comparisons[:10]  # Limit to top 10 comparisons
    
    def _extract_document_text(self, document_text: str) -> str:
        """Extract and clean meaningful text from document"""
        import re
        
        # Remove excessive whitespace
        cleaned_text = re.sub(r'\s+', ' ', document_text.strip())
        
        # Remove common document artifacts
        cleaned_text = re.sub(r'Page \d+', '', cleaned_text)
        cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text)  # Remove bracketed content
        
        # Ensure minimum content
        if len(cleaned_text.strip()) < 50:
            return None
        
        return cleaned_text.strip()
    
    def _group_clauses_by_topic(self, clauses: List[ClauseAnalysis]) -> Dict[str, ClauseAnalysis]:
        """Group clauses by topic/type for comparison"""
        # Simple topic extraction based on keywords
        topics = {}
        
        for clause in clauses:
            topic = self._extract_clause_topic(clause.clause_text)
            if topic not in topics or clause.risk_assessment.score > topics[topic].risk_assessment.score:
                topics[topic] = clause
        
        return topics
    
    def _extract_clause_topic(self, clause_text: str) -> str:
        """Extract topic from clause text"""
        text_lower = clause_text.lower()
        
        if any(word in text_lower for word in ['payment', 'rent', 'fee', 'deposit', 'money']):
            return "payment_terms"
        elif any(word in text_lower for word in ['termination', 'end', 'cancel', 'expire']):
            return "termination"
        elif any(word in text_lower for word in ['liability', 'responsible', 'damage', 'loss']):
            return "liability"
        elif any(word in text_lower for word in ['maintenance', 'repair', 'upkeep']):
            return "maintenance"
        elif any(word in text_lower for word in ['privacy', 'confidential', 'disclosure']):
            return "privacy"
        elif any(word in text_lower for word in ['dispute', 'arbitration', 'court', 'legal']):
            return "dispute_resolution"
        else:
            return "general_terms"
    
    def _generate_clause_comparison_notes(self, clause1: ClauseAnalysis, clause2: ClauseAnalysis, risk_diff: float) -> str:
        """Generate comparison notes for clauses"""
        if abs(risk_diff) < 0.1:
            return "Both clauses have similar risk levels"
        elif risk_diff > 0.2:
            return "Document 1's clause is significantly riskier"
        elif risk_diff > 0:
            return "Document 1's clause is moderately riskier"
        elif risk_diff < -0.2:
            return "Document 2's clause is significantly riskier"
        else:
            return "Document 2's clause is moderately riskier"
    
    def _generate_clause_recommendation(self, clause1: ClauseAnalysis, clause2: ClauseAnalysis, risk_diff: float) -> str:
        """Generate recommendation for clause comparison"""
        if abs(risk_diff) < 0.1:
            return "Both clauses are acceptable"
        elif risk_diff > 0.2:
            return "Prefer document 2's version of this clause"
        elif risk_diff > 0:
            return "Document 2's clause is slightly better"
        elif risk_diff < -0.2:
            return "Prefer document 1's version of this clause"
        else:
            return "Document 1's clause is slightly better"
    
    async def _generate_comparison_summary(
        self, 
        doc1_analysis, 
        doc2_analysis, 
        differences: List[DocumentDifference]
    ) -> str:
        """Generate overall comparison summary"""
        risk_diff = doc1_analysis.overall_risk.score - doc2_analysis.overall_risk.score
        
        if abs(risk_diff) < 0.1:
            summary = "Both documents have similar risk levels. "
        elif risk_diff > 0.3:
            summary = "Document 1 is significantly riskier than Document 2. "
        elif risk_diff > 0.1:
            summary = "Document 1 is moderately riskier than Document 2. "
        elif risk_diff < -0.3:
            summary = "Document 2 is significantly riskier than Document 1. "
        elif risk_diff < -0.1:
            summary = "Document 2 is moderately riskier than Document 1. "
        else:
            summary = "Documents have slight risk differences. "
        
        high_severity_diffs = [d for d in differences if d.severity == "high"]
        if high_severity_diffs:
            summary += f"There are {len(high_severity_diffs)} major differences that require attention. "
        
        summary += "Review the detailed comparison to understand specific clause differences and make an informed decision."
        
        return summary
    
    def _determine_safer_document(self, risk1: RiskAssessment, risk2: RiskAssessment) -> str:
        """Determine which document is safer"""
        risk_diff = risk1.score - risk2.score
        
        if abs(risk_diff) < 0.05:
            return "similar"
        elif risk_diff > 0:
            return "document2"
        else:
            return "document1"