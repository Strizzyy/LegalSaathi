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
        self.analysis_storage = {}  # Store complete analysis results for pagination/search
        
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
            
            # OPTIMIZATION: Parallel processing of clause conversions
            overall_risk = self._convert_risk_assessment(risk_analysis['overall_risk'])
            
            logger.info(f"🔄 Converting {len(risk_analysis['clause_assessments'])} clause assessments in parallel")
            
            # PARALLEL PROCESSING: Convert all clauses concurrently
            clause_conversion_tasks = [
                self._convert_clause_analysis(
                    clause_assessment, 
                    request.user_expertise_level,
                    request.document_type
                )
                for clause_assessment in risk_analysis['clause_assessments']
            ]
            
            # Execute all conversions in parallel
            clause_assessments = await asyncio.gather(*clause_conversion_tasks)
            logger.info(f"✅ Converted {len(clause_assessments)} clauses in parallel")
            
            # OPTIMIZATION: Generate summary and recommendations concurrently
            summary_task = self._generate_concise_summary(risk_analysis, request.document_type)
            recommendations_task = self._generate_recommendations(risk_analysis, request.user_expertise_level)
            
            summary, recommendations = await asyncio.gather(summary_task, recommendations_task)
            
            processing_time = time.time() - start_time
            
            # OPTIMIZATION: Validate response quality and fix timestamps
            processing_time = time.time() - start_time
            
            # Response validation
            if not self._validate_analysis_quality(overall_risk, clause_assessments, summary):
                logger.warning("⚠️ Analysis quality validation failed - retrying with enhanced parameters")
                # Could implement retry logic here if needed
            
            # Create response (timestamp auto-generated with current time)
            response = DocumentAnalysisResponse(
                analysis_id=analysis_id,
                overall_risk=overall_risk,
                clause_assessments=clause_assessments,
                summary=summary,
                processing_time=processing_time,
                recommendations=recommendations,
                enhanced_insights=enhanced_insights,
                document_text=request.document_text,  # Include original text for comparison
                document_type=request.document_type.value  # Include document type for comparison
            )
            
            # Store complete analysis results for pagination/search/filtering
            self.analysis_storage[analysis_id] = {
                'response': response,
                'clause_assessments': clause_assessments,
                'overall_risk': overall_risk,
                'document_type': request.document_type,
                'user_expertise_level': request.user_expertise_level,
                'timestamp': datetime.now(),
                'total_clauses': len(clause_assessments)
            }
            
            logger.info(f"📚 Stored analysis {analysis_id} with {len(clause_assessments)} clauses for pagination/search")
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
    
    async def _convert_clause_analysis(self, clause_assessment: Dict, expertise_level: str, document_type: str) -> ClauseAnalysis:
        """OPTIMIZED: Convert clause assessment with concise output (max 150 words)"""
        assessment = clause_assessment['assessment']
        
        # OPTIMIZATION: Generate concise explanations in parallel
        explanation, implications, recommendations = await self._generate_concise_explanations(
            clause_assessment.get('clause_text', ''), 
            clause_assessment.get('clause_title', f"Clause {clause_assessment['clause_id']}"),
            assessment, 
            expertise_level, 
            document_type
        )
        
        return ClauseAnalysis(
            clause_id=clause_assessment['clause_id'],
            clause_text=clause_assessment.get('clause_text', ''),  # Already truncated in AI service
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
    
    async def _generate_concise_explanations(self, clause_text: str, clause_title: str, assessment, expertise_level: str, document_type: str) -> tuple:
        """OPTIMIZED: Generate concise explanations (max 150 words total)"""
        
        # Get risk details
        risk_level = assessment.get('level', 'GREEN')
        risk_score = assessment.get('score', 0.0)
        reasons = assessment.get('reasons', [])
        confidence = assessment.get('confidence_percentage', 50)
        
        # OPTIMIZATION: Create structured, concise explanations
        if risk_level == 'RED':
            explanation = f"🚨 HIGH RISK ({risk_score:.1f}/1.0): {clause_title} - {reasons[0] if reasons else 'Significant legal/financial risks identified'}"
            implications = [f"Could result in financial loss or legal complications", f"Terms strongly favor the other party"]
            recommendations = [f"Negotiate changes before signing", f"Get legal review for this clause"]
            
        elif risk_level == 'YELLOW':
            explanation = f"⚠️ MODERATE RISK ({risk_score:.1f}/1.0): {clause_title} - {reasons[0] if reasons else 'Some unfavorable terms identified'}"
            implications = [f"Terms could be more balanced", f"May create minor disadvantages"]
            recommendations = [f"Consider negotiating improvements", f"Clarify terms if unclear"]
            
        else:  # GREEN
            explanation = f"✅ LOW RISK ({risk_score:.1f}/1.0): {clause_title} - Standard terms with acceptable risk level"
            implications = [f"Terms appear fair and balanced", f"Standard for this type of agreement"]
            recommendations = [f"Terms are acceptable as written", f"Proceed with normal review"]
        
        # Add confidence indicator if low
        if confidence < 70:
            explanation += f" (⚠️ {confidence}% confidence)"
        
        return explanation, implications, recommendations

    async def _generate_explanations_legacy(self, clause_text: str, assessment, expertise_level: str, document_type: str) -> tuple:
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
                # Generate AI-powered specific explanation instead of generic response
                specific_reasons = reasons[:2] if len(reasons) >= 2 else reasons
                explanation = await self._generate_ai_explanation(clause_text, assessment, specific_reasons, 'beginner')
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
            elif assessment['level'] == 'YELLOW':
                # Generate AI-powered specific explanation instead of generic response
                specific_reasons = reasons[:2] if len(reasons) >= 2 else reasons
                explanation = await self._generate_ai_explanation(clause_text, assessment, specific_reasons, 'beginner')
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
            else:
                # Generate AI-powered specific explanation instead of generic response
                specific_reasons = reasons[:2] if len(reasons) >= 2 else reasons
                explanation = await self._generate_ai_explanation(clause_text, assessment, specific_reasons, 'beginner')
                implications = self._get_specific_implications(assessment['level'], primary_risk, document_type, 'beginner')
                recommendations = self._get_specific_recommendations(assessment['level'], primary_risk, document_type, 'beginner')
        
        return explanation, implications, recommendations
    
    async def _generate_ai_explanation(self, clause_text: str, assessment: dict, reasons: list, expertise_level: str) -> str:
        """Generate AI-powered specific explanation for clause"""
        try:
            from models.ai_models import ClarificationRequest
            
            # Build context for AI explanation
            context = {
                'clause': {
                    'text': clause_text,
                    'riskLevel': assessment.get('level', 'UNKNOWN'),
                    'riskScore': assessment.get('score', 0),
                    'confidence': assessment.get('confidence_percentage', 0),
                    'reasons': reasons,
                    'riskCategories': assessment.get('risk_categories', {})
                }
            }
            
            # Create specific question for explanation
            risk_level = assessment.get('level', 'UNKNOWN')
            if risk_level == 'RED':
                question = f"Explain why this clause is HIGH RISK and what specific problems it creates for the user. Provide concrete examples and specific actions they should take."
            elif risk_level == 'YELLOW':
                question = f"Explain why this clause has MODERATE RISK and what specific concerns exist. Provide concrete examples and specific improvements they should negotiate."
            else:
                question = f"Explain why this clause is LOW RISK and what makes it fair. Provide specific details about what protections it offers."
            
            # Get AI explanation
            request = ClarificationRequest(
                question=question,
                context=context,
                user_expertise_level=expertise_level
            )
            
            response = await self.ai_service.get_clarification(request)
            
            if response.success and response.response and len(response.response) > 50 and not response.fallback:
                # Use AI response but limit length for display
                ai_explanation = response.response[:300] + "..." if len(response.response) > 300 else response.response
                return ai_explanation
            else:
                # Fallback to improved generic response
                return self._create_improved_fallback_explanation(risk_level, reasons, expertise_level)
                
        except Exception as e:
            logger.warning(f"Failed to generate AI explanation: {e}")
            return self._create_improved_fallback_explanation(assessment.get('level', 'UNKNOWN'), reasons, expertise_level)
    
    def _create_improved_fallback_explanation(self, risk_level: str, reasons: list, expertise_level: str) -> str:
        """Create improved fallback explanation with specific details"""
        confidence_indicator = ""
        
        if risk_level == 'RED':
            if reasons:
                specific_reason = reasons[0] if reasons else "it creates unfair obligations"
                return f"🚨 HIGH RISK: This clause is problematic because {specific_reason}. This could result in financial loss or legal complications."
            else:
                return f"🚨 HIGH RISK: This clause contains terms that strongly favor the other party and could result in significant disadvantages."
        elif risk_level == 'YELLOW':
            if reasons:
                specific_reason = reasons[0] if reasons else "the terms could be more balanced"
                return f"⚠️ MODERATE RISK: This clause has concerns because {specific_reason}. Consider negotiating for better terms."
            else:
                return f"⚠️ MODERATE RISK: This clause has some unfavorable terms that could be improved through negotiation."
        else:
            return f"✅ LOW RISK: This clause appears to have standard, fair terms that provide reasonable protection for both parties."
    
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
                    'beginner': ["Request specific criteria for what counts as 'confidential'", "Ask to remove overly broad language like 'includes but not limited to'", "Negotiate a time limit on confidentiality obligations"]
                },
                'GREEN': {
                    'expert': ["Legal terms are acceptable", "Proceed with standard review"],
                    'intermediate': ["Legal terms look fair", "Normal review is sufficient"],
                    'beginner': ["This clause provides good protection for both parties", "The terms are fair and standard for this type of agreement"]
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
    
    async def _generate_concise_summary(self, risk_analysis: Dict, document_type: str) -> str:
        """Generate AI-powered document summary using actual clause analysis data"""
        try:
            from models.ai_models import ClarificationRequest
            
            overall_risk = risk_analysis['overall_risk']
            clause_assessments = risk_analysis.get('clause_assessments', [])
            
            # Build comprehensive context from actual analysis data
            context = {
                'document': {
                    'documentType': document_type.replace('_', ' ').title(),
                    'overallRisk': overall_risk.get('level', 'UNKNOWN'),
                    'riskScore': overall_risk.get('score', 0.0),
                    'confidenceLevel': overall_risk.get('confidence_percentage', 0),
                    'totalClauses': len(clause_assessments),
                    'hasLowConfidenceWarning': overall_risk.get('low_confidence_warning', False),
                    'riskReasons': overall_risk.get('reasons', []),
                    'severity': overall_risk.get('severity', 'unknown'),
                    'riskCategories': overall_risk.get('risk_categories', {})
                },
                'clauseExamples': []
            }
            
            # Count risk levels and extract key clause examples
            risk_counts = {'RED': 0, 'YELLOW': 0, 'GREEN': 0}
            high_risk_clauses = []
            moderate_risk_clauses = []
            
            for clause in clause_assessments:
                assessment = clause.get('assessment', {})
                level = assessment.get('level', 'GREEN')
                risk_counts[level] += 1
                
                clause_data = {
                    'id': clause.get('clause_id', 'unknown'),
                    'text': clause.get('clause_text', '')[:200],  # First 200 chars
                    'risk': level,
                    'score': assessment.get('score', 0),
                    'reasons': assessment.get('reasons', []),
                    'confidence': assessment.get('confidence_percentage', 0),
                    'explanation': assessment.get('reasons', [''])[0] if assessment.get('reasons') else ''
                }
                
                if level == 'RED':
                    high_risk_clauses.append(clause_data)
                elif level == 'YELLOW':
                    moderate_risk_clauses.append(clause_data)
                
                # Add to clause examples (prioritize high risk)
                if len(context['clauseExamples']) < 5:
                    context['clauseExamples'].append(clause_data)
            
            # Update risk breakdown
            context['document']['riskBreakdown'] = {
                'high': risk_counts['RED'],
                'medium': risk_counts['YELLOW'], 
                'low': risk_counts['GREEN']
            }
            
            # Add key insights
            context['keyInsights'] = {
                'severityIndicators': [],
                'mainRecommendations': []
            }
            
            # Extract severity indicators from high-risk clauses
            for clause in high_risk_clauses[:3]:  # Top 3 high-risk clauses
                if clause.get('reasons'):
                    context['keyInsights']['severityIndicators'].extend(clause['reasons'][:1])
            
            # Generate main recommendations based on risk level
            if overall_risk.get('level') == 'RED':
                context['keyInsights']['mainRecommendations'] = [
                    "Do not sign without legal review and negotiations",
                    "Address all high-risk clauses before proceeding",
                    "Consider alternative agreements or additional protections"
                ]
            elif overall_risk.get('level') == 'YELLOW':
                context['keyInsights']['mainRecommendations'] = [
                    "Review and negotiate problematic terms before signing",
                    "Seek clarification on moderate-risk clauses",
                    "Consider professional review for complex terms"
                ]
            else:
                context['keyInsights']['mainRecommendations'] = [
                    "Proceed with normal due diligence",
                    "Standard terms appear acceptable",
                    "Review any specific concerns you may have"
                ]
            
            # Create AI request for document summary
            question = f"Summarize this {document_type.replace('_', ' ')} document analysis. Explain what this document means, the key risks found, and what the user should do. Use the specific clause analysis data provided in the context."
            
            request = ClarificationRequest(
                question=question,
                context=context,
                user_expertise_level='intermediate'  # Use intermediate for balanced detail
            )
            
            # Get AI-generated summary
            response = await self.ai_service.get_clarification(request)
            
            if response.success and response.response and len(response.response) > 100 and not response.fallback:
                logger.info("Generated AI-powered document summary using actual analysis data")
                return response.response
            else:
                logger.warning("AI summary failed, using enhanced fallback with actual data")
                return self._create_enhanced_fallback_summary(risk_analysis, document_type)
                
        except Exception as e:
            logger.error(f"Failed to generate AI document summary: {e}")
            return self._create_enhanced_fallback_summary(risk_analysis, document_type)
    
    def _create_enhanced_fallback_summary(self, risk_analysis: Dict, document_type: str) -> str:
        """Create enhanced fallback summary using actual analysis data"""
        overall_risk = risk_analysis['overall_risk']
        clause_assessments = risk_analysis.get('clause_assessments', [])
        
        # Count risk levels and extract specific details
        risk_counts = {'RED': 0, 'YELLOW': 0, 'GREEN': 0}
        high_risk_reasons = []
        moderate_risk_reasons = []
        
        for clause in clause_assessments:
            assessment = clause.get('assessment', {})
            level = assessment.get('level', 'GREEN')
            risk_counts[level] += 1
            
            reasons = assessment.get('reasons', [])
            if level == 'RED' and reasons:
                high_risk_reasons.extend(reasons[:1])  # One reason per high-risk clause
            elif level == 'YELLOW' and reasons:
                moderate_risk_reasons.extend(reasons[:1])  # One reason per moderate-risk clause
        
        # Create structured summary with actual data
        doc_name = document_type.replace('_', ' ').title()
        risk_level = overall_risk['level']
        risk_score = overall_risk.get('score', 0.0)
        confidence = overall_risk.get('confidence_percentage', 0)
        
        summary = f"## Document Analysis Summary\n\n"
        
        if risk_level == 'RED':
            summary += f"🚨 **HIGH RISK {doc_name}** (Risk Score: {risk_score:.1f}/1.0, Confidence: {confidence}%)\n\n"
            summary += f"**Critical Issues Found:**\n"
            if high_risk_reasons:
                for i, reason in enumerate(high_risk_reasons[:3], 1):
                    summary += f"{i}. {reason}\n"
            else:
                summary += "Multiple high-risk clauses require immediate attention.\n"
            summary += f"\n**Analysis:** {risk_counts['RED']} high-risk, {risk_counts['YELLOW']} moderate-risk, {risk_counts['GREEN']} acceptable clauses.\n"
            summary += f"**Recommendation:** Do not sign without legal review and negotiations.\n"
            
        elif risk_level == 'YELLOW':
            summary += f"⚠️ **MODERATE RISK {doc_name}** (Risk Score: {risk_score:.1f}/1.0, Confidence: {confidence}%)\n\n"
            summary += f"**Issues Identified:**\n"
            if moderate_risk_reasons:
                for i, reason in enumerate(moderate_risk_reasons[:3], 1):
                    summary += f"{i}. {reason}\n"
            if high_risk_reasons:
                summary += f"\n**High-Risk Issues:**\n"
                for i, reason in enumerate(high_risk_reasons[:2], 1):
                    summary += f"{i}. {reason}\n"
            summary += f"\n**Analysis:** {risk_counts['RED']} high-risk, {risk_counts['YELLOW']} moderate-risk, {risk_counts['GREEN']} acceptable clauses.\n"
            summary += f"**Recommendation:** Review and negotiate problematic terms before signing.\n"
            
        else:
            summary += f"✅ **LOW RISK {doc_name}** (Risk Score: {risk_score:.1f}/1.0, Confidence: {confidence}%)\n\n"
            summary += f"**Analysis:** This document contains {len(clause_assessments)} clauses that are mostly standard and acceptable.\n"
            if moderate_risk_reasons:
                summary += f"**Minor Concerns:** {moderate_risk_reasons[0]}\n"
            summary += f"**Breakdown:** {risk_counts['RED']} high-risk, {risk_counts['YELLOW']} moderate-risk, {risk_counts['GREEN']} acceptable clauses.\n"
            summary += f"**Recommendation:** Proceed with normal due diligence.\n"
        
        return summary

    async def _generate_summary_legacy(self, risk_analysis: Dict, document_type: str) -> str:
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
    
    def _validate_analysis_quality(self, overall_risk: RiskAssessment, clause_assessments: List, summary: str) -> bool:
        """OPTIMIZATION: Validate analysis quality to prevent generic responses"""
        
        # Check if we have sufficient clause analysis
        if len(clause_assessments) < 3:
            logger.warning(f"Insufficient clause analysis: only {len(clause_assessments)} clauses")
            return False
        
        # Check summary quality (should not be too generic)
        generic_summary_indicators = [
            "general information only",
            "consult a lawyer",
            "review carefully",
            "may have issues"
        ]
        
        summary_lower = summary.lower()
        if any(indicator in summary_lower for indicator in generic_summary_indicators):
            logger.warning("Summary contains generic language")
            return False
        
        # Check if explanations are sufficiently detailed
        generic_explanation_count = 0
        for clause in clause_assessments:
            explanation = clause.plain_explanation.lower()
            if len(explanation) < 50 or "consult" in explanation:
                generic_explanation_count += 1
        
        if generic_explanation_count > len(clause_assessments) * 0.5:
            logger.warning(f"Too many generic explanations: {generic_explanation_count}/{len(clause_assessments)}")
            return False
        
        logger.info("✅ Analysis quality validation passed")
        return True
    
    async def get_paginated_clauses(self, analysis_id: str, page: int = 1, page_size: int = 10, 
                                  risk_filter: str = None, sort_by: str = 'risk_score') -> Dict[str, Any]:
        """COMPLETE: Get paginated clause results with filtering and sorting"""
        
        if analysis_id not in self.analysis_storage:
            raise ValueError(f"Analysis {analysis_id} not found")
        
        stored_analysis = self.analysis_storage[analysis_id]
        all_clauses = stored_analysis['clause_assessments']
        
        logger.info(f"📄 Paginating {len(all_clauses)} clauses - Page {page}, Size {page_size}")
        
        # FILTERING: Apply risk level filter if specified
        filtered_clauses = all_clauses
        if risk_filter:
            risk_filter_upper = risk_filter.upper()
            filtered_clauses = [
                clause for clause in all_clauses 
                if clause.risk_assessment.level.value == risk_filter_upper
            ]
            logger.info(f"🔍 Filtered to {len(filtered_clauses)} clauses with {risk_filter_upper} risk")
        
        # SORTING: Sort clauses by specified criteria
        if sort_by == 'risk_score':
            filtered_clauses.sort(key=lambda x: x.risk_assessment.score, reverse=True)
        elif sort_by == 'risk_level':
            # Sort by risk level priority: RED > YELLOW > GREEN
            risk_priority = {'RED': 3, 'YELLOW': 2, 'GREEN': 1}
            filtered_clauses.sort(key=lambda x: risk_priority.get(x.risk_assessment.level.value, 0), reverse=True)
        elif sort_by == 'clause_id':
            filtered_clauses.sort(key=lambda x: int(x.clause_id) if x.clause_id.isdigit() else 999)
        elif sort_by == 'confidence':
            filtered_clauses.sort(key=lambda x: x.risk_assessment.confidence_percentage, reverse=True)
        
        logger.info(f"📊 Sorted clauses by {sort_by}")
        
        # PAGINATION: Calculate pagination parameters
        total_filtered = len(filtered_clauses)
        total_pages = (total_filtered + page_size - 1) // page_size  # Ceiling division
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_filtered)
        
        # Get paginated slice
        paginated_clauses = filtered_clauses[start_idx:end_idx]
        
        # Convert to serializable format
        clause_data = []
        for clause in paginated_clauses:
            clause_data.append({
                'clause_id': clause.clause_id,
                'clause_text': clause.clause_text,
                'risk_level': clause.risk_assessment.level.value,
                'risk_score': clause.risk_assessment.score,
                'severity': clause.risk_assessment.severity,
                'confidence_percentage': clause.risk_assessment.confidence_percentage,
                'reasons': clause.risk_assessment.reasons,
                'plain_explanation': clause.plain_explanation,
                'legal_implications': clause.legal_implications,
                'recommendations': clause.recommendations,
                'risk_categories': clause.risk_assessment.risk_categories
            })
        
        result = {
            "clauses": clause_data,
            "total_clauses": len(all_clauses),
            "filtered_clauses": total_filtered,
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_more": page < total_pages,
            "has_previous": page > 1,
            "filters_applied": {"risk_level": risk_filter} if risk_filter else {},
            "sort_criteria": sort_by,
            "analysis_id": analysis_id,
            "pagination_info": {
                "showing_start": start_idx + 1 if paginated_clauses else 0,
                "showing_end": end_idx,
                "showing_total": total_filtered
            }
        }
        
        logger.info(f"✅ Paginated result: Page {page}/{total_pages}, showing {len(paginated_clauses)} clauses")
        return result
    
    async def search_clauses(self, analysis_id: str, search_query: str, 
                           search_fields: List[str] = None) -> Dict[str, Any]:
        """COMPLETE: Search within analyzed clauses with full-text search"""
        
        if analysis_id not in self.analysis_storage:
            raise ValueError(f"Analysis {analysis_id} not found")
        
        if not search_query or len(search_query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        stored_analysis = self.analysis_storage[analysis_id]
        all_clauses = stored_analysis['clause_assessments']
        
        search_query_lower = search_query.lower().strip()
        search_fields = search_fields or ['clause_text', 'plain_explanation', 'legal_implications', 'recommendations', 'reasons']
        
        logger.info(f"🔍 Searching {len(all_clauses)} clauses for '{search_query}' in fields: {search_fields}")
        
        search_results = []
        
        for clause in all_clauses:
            matches = []
            total_relevance_score = 0
            
            # Search in clause text
            if 'clause_text' in search_fields and search_query_lower in clause.clause_text.lower():
                match_count = clause.clause_text.lower().count(search_query_lower)
                matches.append({
                    'field': 'clause_text',
                    'match_count': match_count,
                    'snippet': self._extract_search_snippet(clause.clause_text, search_query, 100)
                })
                total_relevance_score += match_count * 3  # Higher weight for clause text matches
            
            # Search in explanation
            if 'plain_explanation' in search_fields and search_query_lower in clause.plain_explanation.lower():
                match_count = clause.plain_explanation.lower().count(search_query_lower)
                matches.append({
                    'field': 'plain_explanation',
                    'match_count': match_count,
                    'snippet': self._extract_search_snippet(clause.plain_explanation, search_query, 100)
                })
                total_relevance_score += match_count * 2
            
            # Search in legal implications
            if 'legal_implications' in search_fields:
                implications_text = ' '.join(clause.legal_implications).lower()
                if search_query_lower in implications_text:
                    match_count = implications_text.count(search_query_lower)
                    matches.append({
                        'field': 'legal_implications',
                        'match_count': match_count,
                        'snippet': self._extract_search_snippet(' '.join(clause.legal_implications), search_query, 100)
                    })
                    total_relevance_score += match_count * 2
            
            # Search in recommendations
            if 'recommendations' in search_fields:
                recommendations_text = ' '.join(clause.recommendations).lower()
                if search_query_lower in recommendations_text:
                    match_count = recommendations_text.count(search_query_lower)
                    matches.append({
                        'field': 'recommendations',
                        'match_count': match_count,
                        'snippet': self._extract_search_snippet(' '.join(clause.recommendations), search_query, 100)
                    })
                    total_relevance_score += match_count * 2
            
            # Search in risk reasons
            if 'reasons' in search_fields:
                reasons_text = ' '.join(clause.risk_assessment.reasons).lower()
                if search_query_lower in reasons_text:
                    match_count = reasons_text.count(search_query_lower)
                    matches.append({
                        'field': 'reasons',
                        'match_count': match_count,
                        'snippet': self._extract_search_snippet(' '.join(clause.risk_assessment.reasons), search_query, 100)
                    })
                    total_relevance_score += match_count * 1
            
            # If matches found, add to results
            if matches:
                search_results.append({
                    'clause_id': clause.clause_id,
                    'clause_text': clause.clause_text[:200] + "..." if len(clause.clause_text) > 200 else clause.clause_text,
                    'risk_level': clause.risk_assessment.level.value,
                    'risk_score': clause.risk_assessment.score,
                    'confidence_percentage': clause.risk_assessment.confidence_percentage,
                    'matches': matches,
                    'total_matches': sum(m['match_count'] for m in matches),
                    'relevance_score': total_relevance_score,
                    'plain_explanation': clause.plain_explanation
                })
        
        # Sort by relevance score (highest first)
        search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        result = {
            "search_query": search_query,
            "search_fields": search_fields,
            "results": search_results,
            "total_matches": len(search_results),
            "total_clauses_searched": len(all_clauses),
            "analysis_id": analysis_id,
            "search_summary": {
                "high_risk_matches": len([r for r in search_results if r['risk_level'] == 'RED']),
                "medium_risk_matches": len([r for r in search_results if r['risk_level'] == 'YELLOW']),
                "low_risk_matches": len([r for r in search_results if r['risk_level'] == 'GREEN']),
                "avg_relevance_score": sum(r['relevance_score'] for r in search_results) / len(search_results) if search_results else 0
            }
        }
        
        logger.info(f"✅ Search completed: {len(search_results)} matches found in {len(all_clauses)} clauses")
        return result
    
    def _extract_search_snippet(self, text: str, search_query: str, max_length: int = 100) -> str:
        """Extract a snippet around the search query match"""
        text_lower = text.lower()
        query_lower = search_query.lower()
        
        match_index = text_lower.find(query_lower)
        if match_index == -1:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Calculate snippet boundaries
        start = max(0, match_index - max_length // 2)
        end = min(len(text), match_index + len(search_query) + max_length // 2)
        
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet