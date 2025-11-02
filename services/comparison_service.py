"""
Enhanced document comparison service with Vertex AI embeddings for semantic analysis
"""

import uuid
import time
import logging
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from cachetools import TTLCache

from models.comparison_models import (
    DocumentComparisonRequest, DocumentComparisonResponse,
    DocumentDifference, ClauseComparison, ComparisonSummaryResponse
)
from models.document_models import DocumentAnalysisRequest, RiskAssessment, ClauseAnalysis
from services.document_service import DocumentService
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class ComparisonService:
    """Enhanced service for comparing legal documents with semantic analysis"""
    
    def __init__(self):
        self.document_service = DocumentService()  # Now uses singleton
        self.ai_service = AIService()
        
        # Cache for embeddings and comparison results
        self.embedding_cache = TTLCache(maxsize=500, ttl=7200)  # 2 hour TTL
        self.comparison_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour TTL
        
        # Semantic similarity thresholds
        self.SIMILARITY_THRESHOLDS = {
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
    
    async def compare_documents(self, request: DocumentComparisonRequest) -> DocumentComparisonResponse:
        """OPTIMIZED: Compare documents with full analysis but better performance"""
        start_time = time.time()
        comparison_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🚀 Starting OPTIMIZED document comparison: {comparison_id}")
            
            # Set timeout for the entire comparison process (45 seconds max)
            return await asyncio.wait_for(
                self._perform_optimized_comparison(request, comparison_id, start_time),
                timeout=45.0
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Document comparison timed out after 45 seconds: {comparison_id}")
            logger.info("Falling back to lightweight comparison...")
            return await self._perform_fallback_comparison(request, comparison_id, start_time)
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            logger.info("Falling back to lightweight comparison...")
            try:
                return await self._perform_fallback_comparison(request, comparison_id, start_time)
            except Exception as fallback_error:
                logger.error(f"Fallback comparison also failed: {fallback_error}")
                raise Exception(f"Comparison failed: {str(e)}")
    
    async def compare_documents_with_progress(self, request: DocumentComparisonRequest) -> DocumentComparisonResponse:
        """OPTIMIZED: Compare two legal documents with performance improvements and timeout"""
        start_time = time.time()
        comparison_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🚀 Starting OPTIMIZED document comparison: {comparison_id}")
            
            # Set timeout for the entire comparison process (60 seconds max)
            return await asyncio.wait_for(
                self._perform_comparison(request, comparison_id, start_time),
                timeout=60.0
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Document comparison timed out after 60 seconds: {comparison_id}")
            raise Exception("Document comparison timed out. Please try again with smaller documents or contact support.")
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise Exception(f"Comparison failed: {str(e)}")
    
    async def _perform_optimized_comparison(self, request: DocumentComparisonRequest, comparison_id: str, start_time: float) -> DocumentComparisonResponse:
        """OPTIMIZED comparison using full analysis with performance improvements"""
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
        
        # OPTIMIZATION: Use asyncio.gather for parallel document analysis
        logger.info("⚡ Starting OPTIMIZED parallel document analysis...")
        analysis_start = time.time()
        
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
        
        # PARALLEL EXECUTION: Analyze both documents simultaneously
        doc1_analysis, doc2_analysis = await asyncio.gather(
            self.document_service.analyze_document(doc1_request),
            self.document_service.analyze_document(doc2_request)
        )
        
        analysis_time = time.time() - analysis_start
        logger.info(f"✅ Parallel document analysis completed in {analysis_time:.2f}s")
        
        # OPTIMIZATION: Parallel processing of comparison tasks
        logger.info("⚡ Starting parallel comparison analysis...")
        comparison_start = time.time()
        
        # Execute comparison tasks in parallel
        overall_risk_comparison_task = asyncio.create_task(
            self._compare_overall_risk_async(doc1_analysis.overall_risk, doc2_analysis.overall_risk)
        )
        
        key_differences_task = asyncio.create_task(
            self._identify_key_differences(doc1_analysis, doc2_analysis, request.comparison_focus)
        )
        
        # OPTIMIZATION: Use optimized clause comparison (not the lightweight one)
        clause_comparisons_task = asyncio.create_task(
            self._compare_clauses_optimized(doc1_analysis.clause_assessments, doc2_analysis.clause_assessments)
        )
        
        recommendation_summary_task = asyncio.create_task(
            self._generate_comparison_summary(doc1_analysis, doc2_analysis, [])  # Pass empty for now
        )
        
        # Wait for all comparison tasks to complete
        overall_risk_comparison, key_differences, clause_comparisons, recommendation_summary = await asyncio.gather(
            overall_risk_comparison_task,
            key_differences_task,
            clause_comparisons_task,
            recommendation_summary_task
        )
        
        comparison_time = time.time() - comparison_start
        logger.info(f"✅ Parallel comparison analysis completed in {comparison_time:.2f}s")
        
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
        
        logger.info(f"🎉 OPTIMIZED comparison completed: {comparison_id} in {processing_time:.2f}s")
        return response
    
    async def _perform_comparison(self, request: DocumentComparisonRequest, comparison_id: str, start_time: float) -> DocumentComparisonResponse:
        """Perform the actual comparison logic"""
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
        
        # OPTIMIZATION: Use asyncio.gather for parallel document analysis
        logger.info("⚡ Starting parallel document analysis...")
        analysis_start = time.time()
        
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
        
        # PARALLEL EXECUTION: Analyze both documents simultaneously
        doc1_analysis, doc2_analysis = await asyncio.gather(
            self.document_service.analyze_document(doc1_request),
            self.document_service.analyze_document(doc2_request)
        )
        
        analysis_time = time.time() - analysis_start
        logger.info(f"✅ Parallel document analysis completed in {analysis_time:.2f}s")
        
        # OPTIMIZATION: Parallel processing of comparison tasks
        logger.info("⚡ Starting parallel comparison analysis...")
        comparison_start = time.time()
        
        # Execute comparison tasks in parallel
        overall_risk_comparison_task = asyncio.create_task(
            self._compare_overall_risk_async(doc1_analysis.overall_risk, doc2_analysis.overall_risk)
        )
        
        key_differences_task = asyncio.create_task(
            self._identify_key_differences(doc1_analysis, doc2_analysis, request.comparison_focus)
        )
        
        # OPTIMIZATION: Use fast clause comparison instead of expensive semantic analysis
        clause_comparisons_task = asyncio.create_task(
            self._compare_clauses_fast(doc1_analysis.clause_assessments, doc2_analysis.clause_assessments)
        )
        
        recommendation_summary_task = asyncio.create_task(
            self._generate_comparison_summary(doc1_analysis, doc2_analysis, [])  # Pass empty for now
        )
        
        # Wait for all comparison tasks to complete
        overall_risk_comparison, key_differences, clause_comparisons, recommendation_summary = await asyncio.gather(
            overall_risk_comparison_task,
            key_differences_task,
            clause_comparisons_task,
            recommendation_summary_task
        )
        
        comparison_time = time.time() - comparison_start
        logger.info(f"✅ Parallel comparison analysis completed in {comparison_time:.2f}s")
        
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
        
        logger.info(f"🎉 OPTIMIZED document comparison completed: {comparison_id} in {processing_time:.2f}s")
        return response
    
    async def _compare_overall_risk_async(self, risk1: RiskAssessment, risk2: RiskAssessment) -> Dict[str, Any]:
        """Async version of overall risk comparison"""
        return self._compare_overall_risk(risk1, risk2)
    
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
    
    async def _compare_clauses_fast(
        self, 
        clauses1: List[ClauseAnalysis], 
        clauses2: List[ClauseAnalysis]
    ) -> List[ClauseComparison]:
        """OPTIMIZED: Fast clause comparison without expensive semantic analysis"""
        logger.info(f"🚀 Starting FAST clause comparison: {len(clauses1)} vs {len(clauses2)} clauses")
        
        # Use keyword-based matching instead of semantic embeddings for speed
        comparisons = []
        
        # Group clauses by topic for faster matching
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
        
        # Sort by risk difference (highest risk differences first)
        comparisons.sort(key=lambda x: abs(x.risk_difference), reverse=True)
        
        logger.info(f"✅ FAST clause comparison completed: {len(comparisons)} comparisons generated")
        return comparisons[:10]  # Limit to top 10 comparisons for performance
    
    async def _compare_clauses_optimized(
        self, 
        clauses1: List[ClauseAnalysis], 
        clauses2: List[ClauseAnalysis]
    ) -> List[ClauseComparison]:
        """OPTIMIZED: Fast clause comparison using full analysis data but without expensive semantic analysis"""
        logger.info(f"🚀 Starting OPTIMIZED clause comparison: {len(clauses1)} vs {len(clauses2)} clauses")
        
        # Use the existing _compare_clauses method which uses full analysis data
        # but skip the expensive semantic analysis part
        comparisons = self._compare_clauses(clauses1, clauses2)
        
        logger.info(f"✅ OPTIMIZED clause comparison completed: {len(comparisons)} comparisons generated")
        return comparisons
    
    async def _lightweight_document_analysis(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """ULTRA-FAST: Lightweight document analysis without full AI processing"""
        logger.info("⚡ Performing lightweight document analysis...")
        
        # Extract basic clauses using simple text parsing
        clauses = self._extract_clauses_fast(document_text)
        
        # Calculate basic risk assessment
        overall_risk = self._calculate_basic_risk(document_text, clauses, document_type)
        
        return {
            'overall_risk': overall_risk,
            'clauses': clauses,
            'document_type': document_type,
            'text_length': len(document_text)
        }
    
    def _extract_clauses_fast(self, document_text: str) -> List[Dict[str, Any]]:
        """Fast clause extraction using regex patterns"""
        import re
        
        clauses = []
        
        # Pattern to match numbered clauses (1., 2., 3., etc.)
        clause_pattern = r'(\d+\.)\s*([^0-9]+?)(?=\d+\.|$)'
        matches = re.findall(clause_pattern, document_text, re.DOTALL)
        
        for i, (number, text) in enumerate(matches):
            clause_text = text.strip()
            if len(clause_text) > 20:  # Only include substantial clauses
                risk_score = self._calculate_clause_risk_fast(clause_text)
                risk_level = "RED" if risk_score > 0.7 else "YELLOW" if risk_score > 0.4 else "GREEN"
                
                clauses.append({
                    'clause_id': str(i + 1),
                    'clause_text': clause_text[:500],  # Limit text length
                    'risk_assessment': RiskAssessment(
                        level=risk_level,
                        score=risk_score,
                        reasons=[f"Fast analysis indicates {risk_level.lower()} risk"],
                        severity=risk_level.lower(),
                        confidence_percentage=75,  # Lower confidence for fast analysis
                        risk_categories={'general': risk_score},
                        low_confidence_warning=True
                    )
                })
        
        # If no numbered clauses found, split by paragraphs
        if not clauses:
            paragraphs = [p.strip() for p in document_text.split('\n\n') if len(p.strip()) > 50]
            for i, paragraph in enumerate(paragraphs[:10]):  # Limit to 10 paragraphs
                risk_score = self._calculate_clause_risk_fast(paragraph)
                risk_level = "RED" if risk_score > 0.7 else "YELLOW" if risk_score > 0.4 else "GREEN"
                
                clauses.append({
                    'clause_id': str(i + 1),
                    'clause_text': paragraph[:500],
                    'risk_assessment': RiskAssessment(
                        level=risk_level,
                        score=risk_score,
                        reasons=[f"Fast analysis indicates {risk_level.lower()} risk"],
                        severity=risk_level.lower(),
                        confidence_percentage=70,
                        risk_categories={'general': risk_score},
                        low_confidence_warning=True
                    )
                })
        
        return clauses[:15]  # Limit to 15 clauses for performance
    
    def _calculate_clause_risk_fast(self, clause_text: str) -> float:
        """Fast risk calculation using keyword analysis"""
        text_lower = clause_text.lower()
        
        # High-risk keywords
        high_risk_keywords = [
            'terminate', 'penalty', 'forfeit', 'liable', 'damages', 'breach', 
            'default', 'evict', 'sue', 'legal action', 'court', 'attorney fees',
            'indemnify', 'hold harmless', 'waive', 'disclaim', 'sole discretion'
        ]
        
        # Medium-risk keywords
        medium_risk_keywords = [
            'deposit', 'fee', 'charge', 'payment', 'due', 'interest', 'late',
            'notice', 'inspect', 'repair', 'maintain', 'comply', 'restrict'
        ]
        
        # Low-risk keywords
        low_risk_keywords = [
            'standard', 'normal', 'reasonable', 'mutual', 'agree', 'consent',
            'notify', 'written', 'business days', 'good faith'
        ]
        
        high_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        low_count = sum(1 for keyword in low_risk_keywords if keyword in text_lower)
        
        # Calculate risk score
        total_words = len(clause_text.split())
        if total_words == 0:
            return 0.5
        
        risk_score = (high_count * 0.8 + medium_count * 0.4 + low_count * 0.1) / max(total_words / 10, 1)
        return min(max(risk_score, 0.1), 0.9)  # Clamp between 0.1 and 0.9
    
    def _calculate_basic_risk(self, document_text: str, clauses: List[Dict], document_type: str) -> RiskAssessment:
        """Calculate basic overall risk assessment"""
        if not clauses:
            return RiskAssessment(
                level="YELLOW",
                score=0.5,
                reasons=["Unable to analyze document structure"],
                severity="medium",
                confidence_percentage=50,
                risk_categories={'general': 0.5},
                low_confidence_warning=True
            )
        
        # Calculate average risk from clauses
        total_risk = sum(clause['risk_assessment'].score for clause in clauses)
        avg_risk = total_risk / len(clauses)
        
        # Adjust based on document type
        type_multiplier = {
            'rental_agreement': 1.1,
            'employment_contract': 1.2,
            'nda': 0.9,
            'loan_agreement': 1.3,
            'general_contract': 1.0
        }.get(document_type, 1.0)
        
        final_risk = min(avg_risk * type_multiplier, 0.95)
        
        if final_risk > 0.7:
            level = "RED"
            severity = "high"
        elif final_risk > 0.4:
            level = "YELLOW"
            severity = "medium"
        else:
            level = "GREEN"
            severity = "low"
        
        return RiskAssessment(
            level=level,
            score=final_risk,
            reasons=[f"Fast analysis of {len(clauses)} clauses indicates {level.lower()} risk"],
            severity=severity,
            confidence_percentage=75,
            risk_categories={'general': final_risk},
            low_confidence_warning=True
        )
    
    async def _identify_lightweight_differences(self, doc1_analysis: Dict, doc2_analysis: Dict) -> List[DocumentDifference]:
        """Fast difference identification"""
        differences = []
        
        # Risk level differences
        risk1 = doc1_analysis['overall_risk']
        risk2 = doc2_analysis['overall_risk']
        
        if risk1.level != risk2.level:
            differences.append(DocumentDifference(
                type="risk_level",
                description="Overall risk levels differ between documents",
                document1_value=risk1.level,
                document2_value=risk2.level,
                severity="high" if abs(risk1.score - risk2.score) > 0.3 else "medium",
                impact="Different risk exposure levels may affect decision making",
                recommendation="Review the document with lower risk or negotiate terms in the riskier document"
            ))
        
        # Clause count differences
        clause_diff = len(doc1_analysis['clauses']) - len(doc2_analysis['clauses'])
        if abs(clause_diff) > 2:
            differences.append(DocumentDifference(
                type="clause_count",
                description=f"Significant difference in number of clauses ({abs(clause_diff)} clauses)",
                document1_value=str(len(doc1_analysis['clauses'])),
                document2_value=str(len(doc2_analysis['clauses'])),
                severity="medium",
                impact="More clauses may indicate more detailed terms or additional obligations",
                recommendation="Review additional clauses for hidden terms or obligations"
            ))
        
        return differences
    
    async def _compare_clauses_lightweight(self, clauses1: List[Dict], clauses2: List[Dict]) -> List[ClauseComparison]:
        """Fast clause comparison"""
        comparisons = []
        
        # Simple comparison based on clause position and content similarity
        max_clauses = min(len(clauses1), len(clauses2), 8)  # Limit for performance
        
        for i in range(max_clauses):
            clause1 = clauses1[i] if i < len(clauses1) else None
            clause2 = clauses2[i] if i < len(clauses2) else None
            
            if clause1 and clause2:
                risk_diff = clause1['risk_assessment'].score - clause2['risk_assessment'].score
                
                # Convert dict to ClauseAnalysis objects for compatibility
                clause1_obj = ClauseAnalysis(
                    clause_id=clause1['clause_id'],
                    clause_text=clause1['clause_text'],
                    risk_assessment=clause1['risk_assessment'],
                    plain_explanation=f"Fast analysis: {clause1['risk_assessment'].level} risk clause",
                    legal_implications=[f"Risk level: {clause1['risk_assessment'].level}"],
                    recommendations=[f"Review this {clause1['risk_assessment'].level.lower()} risk clause"],
                    translation_available=False
                )
                
                clause2_obj = ClauseAnalysis(
                    clause_id=clause2['clause_id'],
                    clause_text=clause2['clause_text'],
                    risk_assessment=clause2['risk_assessment'],
                    plain_explanation=f"Fast analysis: {clause2['risk_assessment'].level} risk clause",
                    legal_implications=[f"Risk level: {clause2['risk_assessment'].level}"],
                    recommendations=[f"Review this {clause2['risk_assessment'].level.lower()} risk clause"],
                    translation_available=False
                )
                
                comparisons.append(ClauseComparison(
                    clause_type=f"clause_{i+1}",
                    document1_clause=clause1_obj,
                    document2_clause=clause2_obj,
                    risk_difference=risk_diff,
                    comparison_notes=f"Fast comparison: Risk difference of {risk_diff:.2f}",
                    recommendation="Review both versions for specific language preferences"
                ))
        
        return comparisons[:6]  # Limit to 6 comparisons for speed
    
    def _generate_fast_summary(self, doc1_analysis: Dict, doc2_analysis: Dict) -> str:
        """Generate fast comparison summary"""
        risk1 = doc1_analysis['overall_risk']
        risk2 = doc2_analysis['overall_risk']
        
        risk_diff = risk1.score - risk2.score
        
        if abs(risk_diff) < 0.1:
            return "Both documents have similar risk levels based on fast analysis. Review detailed comparison for specific differences."
        elif risk_diff > 0.2:
            return "Document 1 appears to have higher risk than Document 2 based on fast analysis. Consider choosing Document 2."
        elif risk_diff < -0.2:
            return "Document 2 appears to have higher risk than Document 1 based on fast analysis. Consider choosing Document 1."
        else:
            return "Documents have slight risk differences. Review the detailed comparison to make an informed decision."
    
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
    
    async def _compare_clauses_with_semantics(
        self, 
        clauses1: List[ClauseAnalysis], 
        clauses2: List[ClauseAnalysis]
    ) -> List[ClauseComparison]:
        """Enhanced clause comparison with semantic analysis using Vertex AI embeddings"""
        try:
            logger.info(f"Starting semantic clause comparison: {len(clauses1)} vs {len(clauses2)} clauses")
            
            # Get embeddings for all clauses
            embeddings1 = await self._get_clause_embeddings(clauses1)
            embeddings2 = await self._get_clause_embeddings(clauses2)
            
            # Find semantic matches between clauses
            semantic_matches = self._find_semantic_matches(
                clauses1, clauses2, embeddings1, embeddings2
            )
            
            comparisons = []
            processed_clauses2 = set()
            
            # Process matched clauses
            for i, clause1 in enumerate(clauses1):
                best_match = semantic_matches.get(i)
                
                if best_match and best_match['similarity'] >= self.SIMILARITY_THRESHOLDS['low']:
                    j = best_match['index']
                    clause2 = clauses2[j]
                    processed_clauses2.add(j)
                    
                    # Calculate risk difference
                    risk_diff = clause1.risk_assessment.score - clause2.risk_assessment.score
                    
                    # Generate semantic comparison notes
                    comparison_notes = self._generate_semantic_comparison_notes(
                        clause1, clause2, best_match['similarity'], risk_diff
                    )
                    
                    comparisons.append(ClauseComparison(
                        clause_type=self._extract_clause_topic(clause1.clause_text),
                        document1_clause=clause1,
                        document2_clause=clause2,
                        risk_difference=risk_diff,
                        comparison_notes=comparison_notes,
                        recommendation=self._generate_semantic_recommendation(
                            clause1, clause2, best_match['similarity'], risk_diff
                        )
                    ))
                else:
                    # Clause only exists in document 1
                    comparisons.append(ClauseComparison(
                        clause_type=self._extract_clause_topic(clause1.clause_text),
                        document1_clause=clause1,
                        document2_clause=None,
                        risk_difference=clause1.risk_assessment.score,
                        comparison_notes="This clause is unique to Document 1 - no semantic equivalent found in Document 2",
                        recommendation=self._generate_unique_clause_recommendation(clause1, "document1")
                    ))
            
            # Process unmatched clauses from document 2
            for j, clause2 in enumerate(clauses2):
                if j not in processed_clauses2:
                    comparisons.append(ClauseComparison(
                        clause_type=self._extract_clause_topic(clause2.clause_text),
                        document1_clause=None,
                        document2_clause=clause2,
                        risk_difference=-clause2.risk_assessment.score,
                        comparison_notes="This clause is unique to Document 2 - no semantic equivalent found in Document 1",
                        recommendation=self._generate_unique_clause_recommendation(clause2, "document2")
                    ))
            
            # Sort by risk difference (highest risk differences first)
            comparisons.sort(key=lambda x: abs(x.risk_difference), reverse=True)
            
            logger.info(f"Semantic clause comparison completed: {len(comparisons)} comparisons generated")
            return comparisons[:15]  # Limit to top 15 most significant comparisons
            
        except Exception as e:
            logger.error(f"Semantic clause comparison failed: {e}")
            # Fallback to basic comparison
            return self._compare_clauses(clauses1, clauses2)
    
    async def _get_clause_embeddings(self, clauses: List[ClauseAnalysis]) -> List[Optional[List[float]]]:
        """Get embeddings for a list of clauses with caching"""
        embeddings = []
        
        for clause in clauses:
            # Create cache key based on clause text
            import hashlib
            cache_key = f"clause_embedding:{hashlib.md5(clause.clause_text.encode()).hexdigest()}"
            
            # Check cache first
            cached_embedding = self.embedding_cache.get(cache_key)
            if cached_embedding:
                embeddings.append(cached_embedding)
                continue
            
            # Get embedding from AI service
            embedding = await self.ai_service.get_document_embeddings(clause.clause_text)
            
            # Cache the result
            if embedding:
                self.embedding_cache[cache_key] = embedding
            
            embeddings.append(embedding)
        
        return embeddings
    
    def _find_semantic_matches(
        self, 
        clauses1: List[ClauseAnalysis], 
        clauses2: List[ClauseAnalysis],
        embeddings1: List[Optional[List[float]]], 
        embeddings2: List[Optional[List[float]]]
    ) -> Dict[int, Dict[str, Any]]:
        """Find semantic matches between clauses using cosine similarity"""
        matches = {}
        
        for i, (clause1, emb1) in enumerate(zip(clauses1, embeddings1)):
            if not emb1:
                continue
                
            best_similarity = 0
            best_match_idx = -1
            
            for j, (clause2, emb2) in enumerate(zip(clauses2, embeddings2)):
                if not emb2:
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(emb1, emb2)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = j
            
            if best_match_idx >= 0 and best_similarity >= self.SIMILARITY_THRESHOLDS['low']:
                matches[i] = {
                    'index': best_match_idx,
                    'similarity': best_similarity,
                    'clause': clauses2[best_match_idx]
                }
        
        return matches
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays for efficient computation
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _generate_semantic_comparison_notes(
        self, 
        clause1: ClauseAnalysis, 
        clause2: ClauseAnalysis, 
        similarity: float, 
        risk_diff: float
    ) -> str:
        """Generate comparison notes based on semantic similarity and risk difference"""
        similarity_level = "high" if similarity >= self.SIMILARITY_THRESHOLDS['high'] else \
                          "medium" if similarity >= self.SIMILARITY_THRESHOLDS['medium'] else "low"
        
        notes = f"Clauses are semantically {similarity_level}ly similar (similarity: {similarity:.2f}). "
        
        if abs(risk_diff) < 0.1:
            notes += "Both clauses have similar risk levels despite semantic similarity."
        elif risk_diff > 0.2:
            notes += "Document 1's clause is significantly riskier despite semantic similarity."
        elif risk_diff > 0:
            notes += "Document 1's clause is moderately riskier with similar content."
        elif risk_diff < -0.2:
            notes += "Document 2's clause is significantly riskier despite semantic similarity."
        else:
            notes += "Document 2's clause is moderately riskier with similar content."
        
        return notes
    
    def _generate_semantic_recommendation(
        self, 
        clause1: ClauseAnalysis, 
        clause2: ClauseAnalysis, 
        similarity: float, 
        risk_diff: float
    ) -> str:
        """Generate recommendation based on semantic analysis and risk assessment"""
        if abs(risk_diff) < 0.1:
            return "Both clauses are semantically similar with comparable risk levels - either version is acceptable"
        elif risk_diff > 0.3:
            return "Choose Document 2's version - significantly lower risk with similar meaning"
        elif risk_diff > 0.1:
            return "Prefer Document 2's version - moderately lower risk with similar content"
        elif risk_diff < -0.3:
            return "Choose Document 1's version - significantly lower risk with similar meaning"
        elif risk_diff < -0.1:
            return "Prefer Document 1's version - moderately lower risk with similar content"
        else:
            return "Risk levels are similar - review both versions for specific language preferences"
    
    def _generate_unique_clause_recommendation(self, clause: ClauseAnalysis, document: str) -> str:
        """Generate recommendation for clauses that appear in only one document"""
        risk_level = clause.risk_assessment.level
        doc_name = "Document 1" if document == "document1" else "Document 2"
        
        if risk_level == "RED":
            return f"High-risk clause unique to {doc_name} - consider negotiating or removing this clause"
        elif risk_level == "YELLOW":
            return f"Medium-risk clause unique to {doc_name} - review carefully and consider if necessary"
        else:
            return f"Low-risk clause unique to {doc_name} - generally acceptable but review for relevance"
    
    async def generate_comparison_report(
        self, 
        comparison_result: DocumentComparisonResponse,
        format: str = "detailed"
    ) -> Dict[str, Any]:
        """Generate a comprehensive comparison report for export"""
        try:
            # Generate visual differences for side-by-side comparison
            visual_differences = await self._generate_visual_differences(comparison_result)
            
            # Calculate change impact assessment
            impact_assessment = await self.calculate_change_impact_assessment(comparison_result)
            
            report = {
                "comparison_id": comparison_result.comparison_id,
                "timestamp": comparison_result.timestamp,
                "executive_summary": {
                    "verdict": comparison_result.overall_risk_comparison["verdict"],
                    "recommendation": comparison_result.recommendation_summary,
                    "safer_document": comparison_result.safer_document,
                    "risk_score_difference": comparison_result.overall_risk_comparison["risk_score_difference"],
                    "impact_level": impact_assessment.get("overall_impact", "low"),
                    "key_insights": self._extract_key_insights(comparison_result)
                },
                "document_summaries": {
                    "document1": comparison_result.document1_summary,
                    "document2": comparison_result.document2_summary
                },
                "risk_analysis": {
                    "overall_comparison": comparison_result.overall_risk_comparison,
                    "category_breakdown": comparison_result.overall_risk_comparison.get("category_differences", {}),
                    "impact_assessment": impact_assessment
                },
                "visual_differences": visual_differences,
                "key_differences": [
                    {
                        "type": diff.type,
                        "description": diff.description,
                        "severity": diff.severity,
                        "impact": diff.impact,
                        "recommendation": diff.recommendation,
                        "document1_value": diff.document1_value,
                        "document2_value": diff.document2_value
                    }
                    for diff in comparison_result.key_differences
                ],
                "clause_analysis": [
                    {
                        "clause_type": comp.clause_type,
                        "risk_difference": comp.risk_difference,
                        "comparison_notes": comp.comparison_notes,
                        "recommendation": comp.recommendation,
                        "semantic_similarity": self._get_semantic_similarity_score(comp),
                        "document1_clause": {
                            "text": comp.document1_clause.clause_text if comp.document1_clause else None,
                            "risk_level": comp.document1_clause.risk_assessment.level if comp.document1_clause else None,
                            "risk_score": comp.document1_clause.risk_assessment.score if comp.document1_clause else None,
                            "confidence": comp.document1_clause.risk_assessment.confidence_percentage if comp.document1_clause else None
                        } if comp.document1_clause else None,
                        "document2_clause": {
                            "text": comp.document2_clause.clause_text if comp.document2_clause else None,
                            "risk_level": comp.document2_clause.risk_assessment.level if comp.document2_clause else None,
                            "risk_score": comp.document2_clause.risk_assessment.score if comp.document2_clause else None,
                            "confidence": comp.document2_clause.risk_assessment.confidence_percentage if comp.document2_clause else None
                        } if comp.document2_clause else None
                    }
                    for comp in comparison_result.clause_comparisons
                ],
                "processing_metrics": {
                    "total_processing_time": comparison_result.processing_time,
                    "document1_processing_time": comparison_result.document1_summary.get("processing_time", 0),
                    "document2_processing_time": comparison_result.document2_summary.get("processing_time", 0),
                    "semantic_analysis_enabled": True,
                    "embeddings_used": len([c for c in comparison_result.clause_comparisons if "semantic" in c.comparison_notes.lower()])
                },
                "export_metadata": {
                    "format": format,
                    "generated_at": datetime.now().isoformat(),
                    "version": "2.0",
                    "features": ["semantic_analysis", "visual_differences", "impact_assessment", "export_ready"]
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate comparison report: {e}")
            raise Exception(f"Report generation failed: {str(e)}")
    
    async def calculate_change_impact_assessment(
        self, 
        comparison_result: DocumentComparisonResponse
    ) -> Dict[str, Any]:
        """Calculate the impact of changes between documents"""
        try:
            impact_assessment = {
                "overall_impact": "low",
                "risk_impact": {
                    "score_change": comparison_result.overall_risk_comparison["risk_score_difference"],
                    "level_change": None,
                    "category_impacts": []
                },
                "clause_impacts": [],
                "recommendations": []
            }
            
            # Assess overall risk impact
            risk_diff = comparison_result.overall_risk_comparison["risk_score_difference"]
            if abs(risk_diff) > 0.3:
                impact_assessment["overall_impact"] = "high"
                impact_assessment["recommendations"].append(
                    "Significant risk level changes detected - thorough review recommended"
                )
            elif abs(risk_diff) > 0.1:
                impact_assessment["overall_impact"] = "medium"
                impact_assessment["recommendations"].append(
                    "Moderate risk changes - review key differences carefully"
                )
            
            # Assess clause-level impacts
            high_impact_clauses = 0
            for comp in comparison_result.clause_comparisons:
                clause_impact = "low"
                if abs(comp.risk_difference) > 0.3:
                    clause_impact = "high"
                    high_impact_clauses += 1
                elif abs(comp.risk_difference) > 0.1:
                    clause_impact = "medium"
                
                impact_assessment["clause_impacts"].append({
                    "clause_type": comp.clause_type,
                    "impact_level": clause_impact,
                    "risk_change": comp.risk_difference,
                    "recommendation": comp.recommendation
                })
            
            # Generate overall recommendations
            if high_impact_clauses > 3:
                impact_assessment["recommendations"].append(
                    f"Multiple high-impact clause changes detected ({high_impact_clauses} clauses) - legal review strongly recommended"
                )
            elif high_impact_clauses > 0:
                impact_assessment["recommendations"].append(
                    f"Some high-impact clause changes detected - review these clauses carefully"
                )
            
            return impact_assessment
            
        except Exception as e:
            logger.error(f"Failed to calculate change impact assessment: {e}")
            return {"error": f"Impact assessment failed: {str(e)}"}
    
    async def _generate_visual_differences(self, comparison_result: DocumentComparisonResponse) -> Dict[str, Any]:
        """Generate visual differences for side-by-side comparison interface"""
        try:
            logger.info("Generating visual differences for side-by-side comparison")
            
            # Extract document texts from the comparison result
            doc1_clauses = [comp.document1_clause for comp in comparison_result.clause_comparisons if comp.document1_clause]
            doc2_clauses = [comp.document2_clause for comp in comparison_result.clause_comparisons if comp.document2_clause]
            
            # Generate side-by-side diff with highlighting
            side_by_side_diff = {
                "document1_sections": [],
                "document2_sections": [],
                "matched_pairs": [],
                "unique_to_doc1": [],
                "unique_to_doc2": []
            }
            
            # Process clause comparisons for visual highlighting
            for i, comp in enumerate(comparison_result.clause_comparisons):
                if comp.document1_clause and comp.document2_clause:
                    # Matched clauses - highlight differences
                    similarity_score = self._get_semantic_similarity_score(comp)
                    risk_diff = abs(comp.risk_difference)
                    
                    highlight_level = "high" if risk_diff > 0.3 else "medium" if risk_diff > 0.1 else "low"
                    
                    side_by_side_diff["matched_pairs"].append({
                        "index": i,
                        "clause_type": comp.clause_type,
                        "document1_text": comp.document1_clause.clause_text[:500] + "..." if len(comp.document1_clause.clause_text) > 500 else comp.document1_clause.clause_text,
                        "document2_text": comp.document2_clause.clause_text[:500] + "..." if len(comp.document2_clause.clause_text) > 500 else comp.document2_clause.clause_text,
                        "risk_difference": comp.risk_difference,
                        "highlight_level": highlight_level,
                        "semantic_similarity": similarity_score,
                        "comparison_notes": comp.comparison_notes,
                        "recommendation": comp.recommendation
                    })
                elif comp.document1_clause:
                    # Unique to document 1
                    side_by_side_diff["unique_to_doc1"].append({
                        "index": i,
                        "clause_type": comp.clause_type,
                        "text": comp.document1_clause.clause_text[:500] + "..." if len(comp.document1_clause.clause_text) > 500 else comp.document1_clause.clause_text,
                        "risk_level": comp.document1_clause.risk_assessment.level,
                        "risk_score": comp.document1_clause.risk_assessment.score,
                        "recommendation": comp.recommendation
                    })
                elif comp.document2_clause:
                    # Unique to document 2
                    side_by_side_diff["unique_to_doc2"].append({
                        "index": i,
                        "clause_type": comp.clause_type,
                        "text": comp.document2_clause.clause_text[:500] + "..." if len(comp.document2_clause.clause_text) > 500 else comp.document2_clause.clause_text,
                        "risk_level": comp.document2_clause.risk_assessment.level,
                        "risk_score": comp.document2_clause.risk_assessment.score,
                        "recommendation": comp.recommendation
                    })
            
            # Generate highlighted changes summary
            highlighted_changes = []
            
            # Risk level changes
            for comp in comparison_result.clause_comparisons:
                if comp.document1_clause and comp.document2_clause:
                    if comp.document1_clause.risk_assessment.level != comp.document2_clause.risk_assessment.level:
                        highlighted_changes.append({
                            "type": "risk_level_change",
                            "clause_type": comp.clause_type,
                            "from_level": comp.document1_clause.risk_assessment.level,
                            "to_level": comp.document2_clause.risk_assessment.level,
                            "impact": "high" if abs(comp.risk_difference) > 0.3 else "medium"
                        })
            
            # Missing clauses
            for comp in comparison_result.clause_comparisons:
                if comp.document1_clause and not comp.document2_clause:
                    highlighted_changes.append({
                        "type": "clause_removed",
                        "clause_type": comp.clause_type,
                        "risk_level": comp.document1_clause.risk_assessment.level,
                        "impact": "high" if comp.document1_clause.risk_assessment.level == "RED" else "medium"
                    })
                elif comp.document2_clause and not comp.document1_clause:
                    highlighted_changes.append({
                        "type": "clause_added",
                        "clause_type": comp.clause_type,
                        "risk_level": comp.document2_clause.risk_assessment.level,
                        "impact": "high" if comp.document2_clause.risk_assessment.level == "RED" else "medium"
                    })
            
            return {
                "side_by_side_diff": side_by_side_diff,
                "highlighted_changes": highlighted_changes,
                "total_changes": len(highlighted_changes),
                "high_impact_changes": len([c for c in highlighted_changes if c["impact"] == "high"]),
                "visual_diff_metadata": {
                    "matched_clauses": len(side_by_side_diff["matched_pairs"]),
                    "unique_to_doc1": len(side_by_side_diff["unique_to_doc1"]),
                    "unique_to_doc2": len(side_by_side_diff["unique_to_doc2"]),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate visual differences: {e}")
            return {"error": f"Visual diff generation failed: {str(e)}"}
    
    def _extract_key_insights(self, comparison_result: DocumentComparisonResponse) -> List[str]:
        """Extract key insights from comparison results"""
        insights = []
        
        # Risk-based insights
        risk_diff = comparison_result.overall_risk_comparison["risk_score_difference"]
        if abs(risk_diff) > 0.2:
            if risk_diff > 0:
                insights.append("Document 1 has significantly higher risk levels than Document 2")
            else:
                insights.append("Document 2 has significantly higher risk levels than Document 1")
        
        # Clause count insights
        doc1_clauses = comparison_result.document1_summary["clause_count"]
        doc2_clauses = comparison_result.document2_summary["clause_count"]
        clause_diff = abs(doc1_clauses - doc2_clauses)
        
        if clause_diff > 3:
            if doc1_clauses > doc2_clauses:
                insights.append(f"Document 1 has {clause_diff} more clauses than Document 2")
            else:
                insights.append(f"Document 2 has {clause_diff} more clauses than Document 1")
        
        # High-risk clause insights
        high_risk_clauses = len([c for c in comparison_result.clause_comparisons if abs(c.risk_difference) > 0.3])
        if high_risk_clauses > 0:
            insights.append(f"{high_risk_clauses} clauses show significant risk differences")
        
        # Semantic similarity insights
        semantic_comparisons = [c for c in comparison_result.clause_comparisons if "semantic" in c.comparison_notes.lower()]
        if semantic_comparisons:
            insights.append(f"Semantic analysis identified {len(semantic_comparisons)} similar clause pairs")
        
        # Key differences insights
        high_severity_diffs = len([d for d in comparison_result.key_differences if d.severity == "high"])
        if high_severity_diffs > 0:
            insights.append(f"{high_severity_diffs} high-severity differences require immediate attention")
        
        # Document type insights
        if comparison_result.document1_summary["type"] != comparison_result.document2_summary["type"]:
            insights.append("Documents are of different types - comparison may have limited applicability")
        
        return insights[:6]  # Limit to top 6 insights
    
    def _get_semantic_similarity_score(self, comparison: ClauseComparison) -> Optional[float]:
        """Extract semantic similarity score from comparison notes"""
        try:
            # Look for similarity score in comparison notes
            import re
            match = re.search(r'similarity: ([\d.]+)', comparison.comparison_notes)
            if match:
                return float(match.group(1))
        except:
            pass
        return None

    async def _perform_fallback_comparison(self, request: DocumentComparisonRequest, comparison_id: str, start_time: float) -> DocumentComparisonResponse:
        """Fallback comparison method that doesn't require full document analysis"""
        try:
            logger.info(f"🔄 Starting fallback document comparison: {comparison_id}")
            
            # Validate document content
            if not request.document1_text or not request.document1_text.strip():
                raise ValueError("Document 1 is empty or contains no text")
            
            if not request.document2_text or not request.document2_text.strip():
                raise ValueError("Document 2 is empty or contains no text")
            
            # Extract meaningful text content
            doc1_text = self._extract_document_text(request.document1_text)
            doc2_text = self._extract_document_text(request.document2_text)
            
            if not doc1_text or not doc2_text:
                raise ValueError("Unable to extract meaningful text from one or both documents")
            
            # Perform lightweight analysis
            logger.info("⚡ Performing lightweight document analysis...")
            doc1_analysis = await self._lightweight_document_analysis(request.document1_text, request.document1_type)
            doc2_analysis = await self._lightweight_document_analysis(request.document2_text, request.document2_type)
            
            # Basic risk comparison
            overall_risk_comparison = {
                "risk_score_difference": doc1_analysis['overall_risk'].score - doc2_analysis['overall_risk'].score,
                "verdict": self._get_risk_verdict(doc1_analysis['overall_risk'].score - doc2_analysis['overall_risk'].score),
                "document1_risk": doc1_analysis['overall_risk'].score,
                "document2_risk": doc2_analysis['overall_risk'].score
            }
            
            # Identify key differences
            key_differences = await self._identify_lightweight_differences(doc1_analysis, doc2_analysis)
            
            # Compare clauses
            clause_comparisons = await self._compare_clauses_lightweight(
                doc1_analysis['clauses'], 
                doc2_analysis['clauses']
            )
            
            # Generate summary
            recommendation_summary = self._generate_fast_summary(doc1_analysis, doc2_analysis)
            
            # Determine safer document
            safer_document = self._determine_safer_document(
                doc1_analysis['overall_risk'], 
                doc2_analysis['overall_risk']
            )
            
            # Create response
            response = DocumentComparisonResponse(
                comparison_id=comparison_id,
                document1_summary={
                    "type": request.document1_type,
                    "overall_risk": doc1_analysis['overall_risk'],
                    "clause_count": len(doc1_analysis['clauses']),
                    "key_clauses": doc1_analysis['clauses'][:5]
                },
                document2_summary={
                    "type": request.document2_type,
                    "overall_risk": doc2_analysis['overall_risk'],
                    "clause_count": len(doc2_analysis['clauses']),
                    "key_clauses": doc2_analysis['clauses'][:5]
                },
                overall_risk_comparison=overall_risk_comparison,
                key_differences=key_differences,
                clause_comparisons=clause_comparisons,
                recommendation_summary=recommendation_summary,
                safer_document=safer_document,
                comparison_timestamp=datetime.now(),
                processing_time=time.time() - start_time,
                comparison_focus=request.comparison_focus,
                confidence_score=0.75  # Lower confidence for fallback method
            )
            
            total_time = time.time() - start_time
            logger.info(f"✅ Fallback document comparison completed in {total_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Fallback comparison failed: {e}")
            raise Exception(f"Fallback comparison failed: {str(e)}")

    async def export_comparison_report(
        self, 
        comparison_result: DocumentComparisonResponse,
        format: str = "pdf"
    ) -> bytes:
        """Export comparison report in specified format (PDF/Word)"""
        try:
            logger.info(f"Exporting comparison report in {format} format: {comparison_result.comparison_id}")
            
            # Import export service here to avoid circular imports
            from services.export_service import ExportService
            export_service = ExportService()
            
            # Generate comprehensive report data
            report_data = await self.generate_comparison_report(comparison_result, "detailed")
            
            # Export in requested format
            exported_data = await export_service.export_report(report_data, format)
            
            logger.info(f"Comparison report exported successfully in {format} format")
            return exported_data
            
        except Exception as e:
            logger.error(f"Failed to export comparison report: {e}")
            raise Exception(f"Export failed: {str(e)}")
    
    async def get_export_formats(self) -> List[str]:
        """Get supported export formats"""
        try:
            from services.export_service import ExportService
            export_service = ExportService()
            return export_service.get_supported_formats()
        except Exception as e:
            logger.error(f"Failed to get export formats: {e}")
            return ['pdf']  # Fallback to PDF only

    def get_comparison_statistics(self) -> Dict[str, Any]:
        """Get statistics about comparison service usage"""
        return {
            "embedding_cache_size": len(self.embedding_cache),
            "comparison_cache_size": len(self.comparison_cache),
            "cache_hit_rates": {
                "embeddings": getattr(self.embedding_cache, 'hits', 0) / max(getattr(self.embedding_cache, 'misses', 1), 1),
                "comparisons": getattr(self.comparison_cache, 'hits', 0) / max(getattr(self.comparison_cache, 'misses', 1), 1)
            },
            "similarity_thresholds": self.SIMILARITY_THRESHOLDS,
            "export_formats_available": ["pdf", "docx", "word"]
        }