"""
Document processing service for FastAPI backend
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.document_models import (
    DocumentAnalysisRequest, DocumentAnalysisResponse, 
    RiskAssessment, ClauseAnalysis, AnalysisStatusResponse
)
from services.ai_service import AIService
from services.cache_service import CacheService
from services.google_document_ai_service import document_ai_service
from services.google_natural_language_service import natural_language_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling document analysis operations"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.cache_service = CacheService()
        self.processing_jobs = {}  # Store async processing jobs
        
    async def analyze_document(self, request: DocumentAnalysisRequest) -> DocumentAnalysisResponse:
        """
        Main document analysis pipeline with async processing
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        try:
            # COMPLETELY DISABLE CACHING - Force fresh analysis every time
            logger.info(f"Forcing fresh analysis - caching disabled")
            logger.info(f"Processing document text (first 200 chars): {request.document_text[:200]}...")
            
            # Clear any existing cache to prevent stale data
            self.cache_service.analysis_cache.clear()
            logger.info("Cleared all cached analysis data")
            
            # Enhanced analysis with Google Cloud AI services
            enhanced_insights = await self._get_enhanced_insights(
                request.document_text, 
                request.document_type
            )
            
            # Perform risk classification using AI service
            risk_analysis = await self.ai_service.analyze_document_risk(
                request.document_text, 
                request.document_type
            )
            
            # Convert to response format
            overall_risk = self._convert_risk_assessment(risk_analysis['overall_risk'])
            
            clause_assessments = []
            logger.info(f"Converting {len(risk_analysis['clause_assessments'])} clause assessments")
            
            for i, clause_assessment in enumerate(risk_analysis['clause_assessments']):
                logger.info(f"Processing clause {i+1}: {clause_assessment.get('clause_text', 'NO TEXT')[:100]}...")
                
                clause_analysis = self._convert_clause_analysis(
                    clause_assessment, 
                    request.user_expertise_level,
                    request.document_type
                )
                clause_assessments.append(clause_analysis)
                
                logger.info(f"Converted clause {i+1} with text: {clause_analysis.clause_text[:100]}...")
            
            # Generate summary and recommendations
            summary = await self._generate_summary(risk_analysis, request.document_type)
            recommendations = await self._generate_recommendations(
                risk_analysis, 
                request.user_expertise_level
            )
            
            processing_time = time.time() - start_time
            
            # Create response
            response = DocumentAnalysisResponse(
                analysis_id=analysis_id,
                overall_risk=overall_risk,
                clause_assessments=clause_assessments,
                summary=summary,
                processing_time=processing_time,
                recommendations=recommendations,
                enhanced_insights=enhanced_insights
            )
            
            # DISABLE: Cache the result
            # await self.cache_service.store_analysis(cache_key, response)
            logger.info("Skipping cache storage - caching disabled")
            
            logger.info(f"Document analysis completed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise Exception(f"Analysis failed: {str(e)}")
    
    async def start_async_analysis(self, request: DocumentAnalysisRequest) -> str:
        """Start async document analysis and return job ID"""
        job_id = str(uuid.uuid4())
        
        # Store job status
        self.processing_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'started_at': datetime.now(),
            'result': None,
            'error': None
        }
        
        # Start background task
        asyncio.create_task(self._process_document_background(job_id, request))
        
        return job_id
    
    async def get_analysis_status(self, analysis_id: str) -> AnalysisStatusResponse:
        """Get status of ongoing analysis"""
        if analysis_id not in self.processing_jobs:
            raise ValueError(f"Analysis job {analysis_id} not found")
        
        job = self.processing_jobs[analysis_id]
        
        # Estimate completion time
        estimated_completion = None
        if job['status'] == 'processing':
            elapsed = (datetime.now() - job['started_at']).total_seconds()
            estimated_total = 30  # Estimate 30 seconds total
            if elapsed < estimated_total:
                estimated_completion = datetime.now().timestamp() + (estimated_total - elapsed)
        
        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=job['status'],
            progress=job['progress'],
            estimated_completion=estimated_completion,
            result=job['result'],
            error_message=job['error']
        )
    
    async def _process_document_background(self, job_id: str, request: DocumentAnalysisRequest):
        """Background processing task"""
        try:
            # Update progress
            self.processing_jobs[job_id]['progress'] = 25
            
            result = await self.analyze_document(request)
            
            # Update job completion
            self.processing_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Background analysis failed for job {job_id}: {e}")
            self.processing_jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            })
    
    async def _get_enhanced_insights(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """Get enhanced insights from Google Cloud AI services"""
        insights = {}
        
        try:
            # Google Cloud Natural Language AI analysis
            if natural_language_service.enabled:
                nl_result = natural_language_service.analyze_legal_document(document_text)
                if nl_result['success']:
                    insights['natural_language'] = {
                        'sentiment': nl_result['sentiment'],
                        'entities': nl_result['entities'][:10],  # Limit for response size
                        'legal_insights': nl_result['legal_insights']
                    }
        except Exception as e:
            logger.warning(f"Enhanced insights failed: {e}")
        
        return insights
    

    
    def _convert_risk_assessment(self, risk_data: Dict) -> RiskAssessment:
        """Convert classifier risk assessment to API format"""
        # Handle both dict and object formats
        if isinstance(risk_data, dict):
            return RiskAssessment(
                level=risk_data['level'],
                score=risk_data['score'],
                reasons=risk_data.get('reasons', []),
                severity=risk_data['severity'],
                confidence_percentage=risk_data['confidence_percentage'],
                risk_categories=risk_data['risk_categories'],
                low_confidence_warning=risk_data.get('low_confidence_warning', False)
            )
        else:
            # Handle object format (if risk_data has attributes)
            return RiskAssessment(
                level=getattr(risk_data, 'level', 'GREEN'),
                score=getattr(risk_data, 'score', 0.0),
                reasons=getattr(risk_data, 'reasons', []),
                severity=getattr(risk_data, 'severity', 'low'),
                confidence_percentage=getattr(risk_data, 'confidence_percentage', 50),
                risk_categories=getattr(risk_data, 'risk_categories', {}),
                low_confidence_warning=getattr(risk_data, 'low_confidence_warning', False)
            )
    
    def _convert_clause_analysis(self, clause_assessment: Dict, expertise_level: str, document_type: str) -> ClauseAnalysis:
        """Convert clause assessment to API format"""
        assessment = clause_assessment['assessment']
        
        # Generate explanations based on expertise level
        explanation, implications, recommendations = self._generate_explanations(
            assessment, expertise_level, document_type
        )
        
        return ClauseAnalysis(
            clause_id=clause_assessment['clause_id'],
            clause_text=clause_assessment['clause_text'],
            risk_assessment=RiskAssessment(
                level=assessment['level'],
                score=assessment['score'],
                reasons=assessment['reasons'],
                severity=assessment['severity'],
                confidence_percentage=assessment['confidence_percentage'],
                risk_categories=assessment['risk_categories'],
                low_confidence_warning=assessment.get('low_confidence_warning', False)
            ),
            plain_explanation=explanation,
            legal_implications=implications,
            recommendations=recommendations,
            translation_available=True
        )
    
    def _generate_explanations(self, assessment, expertise_level: str, document_type: str) -> tuple:
        """Generate explanations based on user expertise level with more specific context"""
        confidence_indicator = ""
        if assessment.get('low_confidence_warning', False):
            confidence_indicator = f" (⚠️ Low Confidence: {assessment['confidence_percentage']}%)"
        
        # Get specific reasons for more targeted explanations
        reasons = assessment.get('reasons', [])
        risk_categories = assessment.get('risk_categories', {})
        
        # Identify primary risk type
        primary_risk = 'general'
        if risk_categories:
            primary_risk = max(risk_categories.keys(), key=lambda k: risk_categories[k])
        
        if expertise_level == 'expert':
            if assessment['level'] == 'RED':
                specific_reason = f" Specific concerns: {', '.join(reasons[:2])}" if reasons else ""
                explanation = f"🚨 HIGH RISK{confidence_indicator}: Legal analysis indicates significant disadvantage in {primary_risk} aspects.{specific_reason}"
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'expert')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'expert')
            elif assessment['level'] == 'YELLOW':
                specific_reason = f" Issues identified: {', '.join(reasons[:2])}" if reasons else ""
                explanation = f"⚠️ MODERATE RISK{confidence_indicator}: Analysis shows suboptimal terms in {primary_risk} provisions.{specific_reason}"
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'expert')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'expert')
            else:
                explanation = f"✅ ACCEPTABLE TERMS{confidence_indicator}: Clause aligns with standard {document_type} practices."
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'expert')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'expert')
        
        elif expertise_level == 'intermediate':
            if assessment['level'] == 'RED':
                specific_issue = f" Main issues: {', '.join(reasons[:2])}" if reasons else ""
                explanation = f"🚨 HIGH RISK{confidence_indicator}: This clause creates {primary_risk} disadvantages for you.{specific_issue}"
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'intermediate')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'intermediate')
            elif assessment['level'] == 'YELLOW':
                explanation = f"⚠️ MODERATE CONCERN{confidence_indicator}: This clause has {primary_risk} issues that could be improved."
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'intermediate')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'intermediate')
            else:
                explanation = f"✅ FAIR TERMS{confidence_indicator}: This appears to be reasonable and standard for a {document_type}."
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'intermediate')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'intermediate')
        
        else:  # beginner
            if assessment['level'] == 'RED':
                simple_reason = self._simplify_reason(reasons[0]) if reasons else "it's unfair to you"
                explanation = f"🚨 DANGER{confidence_indicator}: This part is bad for you because {simple_reason}!"
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
            elif assessment['level'] == 'YELLOW':
                explanation = f"⚠️ BE CAREFUL{confidence_indicator}: This part could be better for you - it has some problems."
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
            else:
                explanation = f"✅ LOOKS GOOD{confidence_indicator}: This part seems fair and normal for this type of agreement."
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
        
        return explanation, implications, recommendations
    
    def _get_specific_implications(self, risk_level: str, risk_type: str, document_type: str, expertise: str) -> List[str]:
        """Get specific implications based on risk type and document type"""
        implications_map = {
            'financial': {
                'RED': {
                    'expert': ["Significant financial exposure beyond standard limits", "Potential for unlimited liability", "Unfavorable payment terms"],
                    'intermediate': ["You could lose more money than expected", "Payment terms favor the other party", "Financial risks are higher than normal"],
                    'beginner': ["This could cost you a lot of money", "You might have to pay more than you should", "The money parts are unfair to you"]
                },
                'YELLOW': {
                    'expert': ["Moderate financial risk above market standards", "Payment terms could be more balanced"],
                    'intermediate': ["Some financial terms could be better", "Payment requirements are somewhat unfavorable"],
                    'beginner': ["The money parts could be better for you", "You might pay a bit more than you should"]
                },
                'GREEN': {
                    'expert': ["Financial terms within acceptable parameters", "Standard payment provisions"],
                    'intermediate': ["Financial terms appear fair and balanced", "Payment requirements are reasonable"],
                    'beginner': ["The money parts look fair", "Payment terms seem normal"]
                }
            },
            'legal': {
                'RED': {
                    'expert': ["Significant legal liability exposure", "Waiver of important legal protections", "Jurisdiction/governing law disadvantages"],
                    'intermediate': ["You could be legally responsible for things that aren't your fault", "You might lose important legal rights", "Legal terms strongly favor the other party"],
                    'beginner': ["You could get in legal trouble", "You might lose important rights", "The legal parts are bad for you"]
                },
                'YELLOW': {
                    'expert': ["Moderate legal risk requiring attention", "Some protective provisions could be strengthened"],
                    'intermediate': ["Some legal terms could be more protective", "Legal responsibilities are somewhat unbalanced"],
                    'beginner': ["Some legal parts could be better", "You might have more responsibilities than you should"]
                },
                'GREEN': {
                    'expert': ["Legal terms provide adequate protection", "Standard liability allocation"],
                    'intermediate': ["Legal terms appear balanced and fair", "Your rights and responsibilities are reasonable"],
                    'beginner': ["The legal parts look fair", "Your rights seem protected"]
                }
            },
            'operational': {
                'RED': {
                    'expert': ["Operational restrictions significantly limit flexibility", "Performance requirements may be unrealistic", "Termination provisions heavily favor counterparty"],
                    'intermediate': ["Rules about how you operate are very strict", "Requirements might be hard to meet", "The other party can end this more easily than you"],
                    'beginner': ["Too many rules about what you can do", "Hard requirements to follow", "The other person can quit easier than you"]
                },
                'YELLOW': {
                    'expert': ["Some operational constraints exceed standard practice", "Performance metrics could be more reasonable"],
                    'intermediate': ["Some rules and requirements could be more flexible", "Performance expectations are somewhat high"],
                    'beginner': ["Some rules could be more flexible", "Some requirements might be hard"]
                },
                'GREEN': {
                    'expert': ["Operational terms provide reasonable flexibility", "Standard performance requirements"],
                    'intermediate': ["Rules and requirements seem reasonable", "Performance expectations are fair"],
                    'beginner': ["Rules seem fair", "Requirements look normal"]
                }
            }
        }
        
        return implications_map.get(risk_type, implications_map['legal']).get(risk_level, implications_map['legal']['GREEN']).get(expertise, ["Standard terms for this type of agreement"])
    
    def _get_specific_recommendations(self, risk_level: str, risk_type: str, document_type: str, expertise: str) -> List[str]:
        """Get specific recommendations based on risk type and document type"""
        recommendations_map = {
            'financial': {
                'RED': {
                    'expert': ["Negotiate liability caps and limitations", "Review indemnification clauses", "Consider insurance requirements"],
                    'intermediate': ["Ask to limit how much money you could lose", "Try to change payment terms", "Get legal advice about money risks"],
                    'beginner': ["Ask to change the money parts", "Get help understanding what you might have to pay", "Don't sign until money parts are fixed"]
                },
                'YELLOW': {
                    'expert': ["Seek more balanced payment terms", "Clarify financial obligations"],
                    'intermediate': ["Try to improve payment terms", "Make sure you understand all costs"],
                    'beginner': ["Ask if money terms can be better", "Make sure you know what you'll pay"]
                },
                'GREEN': {
                    'expert': ["Financial terms are acceptable as written", "Standard due diligence recommended"],
                    'intermediate': ["Financial terms look fair", "Normal review is fine"],
                    'beginner': ["Money parts are okay", "This looks normal"]
                }
            },
            'legal': {
                'RED': {
                    'expert': ["Seek legal counsel for clause modification", "Review governing law implications", "Consider additional protective provisions"],
                    'intermediate': ["Get legal help to change this clause", "Understand what laws apply", "Ask for better protection"],
                    'beginner': ["Get legal help before signing", "Ask to change the legal parts", "Don't sign until this is fixed"]
                },
                'YELLOW': {
                    'expert': ["Consider strengthening protective provisions", "Clarify legal obligations"],
                    'intermediate': ["Try to get better legal protection", "Make sure you understand your responsibilities"],
                    'beginner': ["Ask for better protection", "Make sure you understand what you're agreeing to"]
                },
                'GREEN': {
                    'expert': ["Legal terms are acceptable", "Proceed with standard review"],
                    'intermediate': ["Legal terms look fair", "Normal review is sufficient"],
                    'beginner': ["Legal parts are okay", "This looks safe"]
                }
            },
            'operational': {
                'RED': {
                    'expert': ["Negotiate more flexible operational terms", "Seek realistic performance standards", "Balance termination provisions"],
                    'intermediate': ["Ask for more flexible rules", "Try to make requirements more realistic", "Make ending the agreement more fair"],
                    'beginner': ["Ask for fewer strict rules", "Make requirements easier", "Make it fair for both sides to quit"]
                },
                'YELLOW': {
                    'expert': ["Seek more reasonable operational flexibility", "Clarify performance expectations"],
                    'intermediate': ["Ask for more flexibility in rules", "Make sure requirements are clear"],
                    'beginner': ["Ask for more flexibility", "Make sure you can do what's required"]
                },
                'GREEN': {
                    'expert': ["Operational terms are reasonable", "Standard implementation recommended"],
                    'intermediate': ["Rules and requirements look fair", "Should be manageable"],
                    'beginner': ["Rules look okay", "You should be able to do this"]
                }
            }
        }
        
        return recommendations_map.get(risk_type, recommendations_map['legal']).get(risk_level, recommendations_map['legal']['GREEN']).get(expertise, ["Standard review recommended"])
    
    def _simplify_reason(self, reason: str) -> str:
        """Simplify technical reasons for beginner users"""
        simplifications = {
            'unlimited liability': 'you could lose everything',
            'indemnification': 'you have to pay for their problems',
            'liquidated damages': 'you have to pay a penalty',
            'sole discretion': 'they decide everything',
            'without notice': 'they don\'t have to tell you first',
            'waive all rights': 'you give up your rights',
            'hold harmless': 'you protect them from problems'
        }
        
        reason_lower = reason.lower()
        for technical, simple in simplifications.items():
            if technical in reason_lower:
                return simple
        
        return reason.lower()
    
    async def _generate_summary(self, risk_analysis: Dict, document_type: str) -> str:
        """Generate document summary"""
        overall_risk = risk_analysis['overall_risk']
        clause_count = len(risk_analysis['clause_assessments'])
        
        risk_counts = {'RED': 0, 'YELLOW': 0, 'GREEN': 0}
        for clause in risk_analysis['clause_assessments']:
            risk_counts[clause['assessment']['level']] += 1
        
        summary = f"Analysis of {document_type.replace('_', ' ').title()} completed. "
        summary += f"Overall risk level: {overall_risk['level']} ({overall_risk['severity']}). "
        summary += f"Analyzed {clause_count} clauses: {risk_counts['RED']} high-risk, "
        summary += f"{risk_counts['YELLOW']} moderate-risk, {risk_counts['GREEN']} low-risk."
        
        return summary
    
    async def _generate_recommendations(self, risk_analysis: Dict, expertise_level: str) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        overall_risk = risk_analysis['overall_risk']
        
        if overall_risk['level'] == 'RED':
            if expertise_level == 'beginner':
                recommendations.extend([
                    "⚠️ This contract has serious problems - don't sign it as-is",
                    "Get help from a lawyer or legal expert before proceeding",
                    "Ask the other party to fix the dangerous parts"
                ])
            else:
                recommendations.extend([
                    "Significant legal risks identified - professional review recommended",
                    "Multiple clauses require negotiation or modification",
                    "Consider alternative agreements or additional protections"
                ])
        elif overall_risk['level'] == 'YELLOW':
            recommendations.extend([
                "Some clauses could be improved through negotiation",
                "Review highlighted concerns before signing",
                "Consider seeking clarification on moderate-risk items"
            ])
        else:
            recommendations.extend([
                "Document appears to have fair and balanced terms",
                "Standard legal language with acceptable risk levels",
                "Proceed with normal due diligence"
            ])
        
        return recommendations