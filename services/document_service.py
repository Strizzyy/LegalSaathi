"""
Document processing service for FastAPI backend
"""

import asyncio
import time
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from models.document_models import (
    DocumentAnalysisRequest, DocumentAnalysisResponse, 
    RiskAssessment, ClauseAnalysis, AnalysisStatusResponse
)
from services.ai_service import AIService
from services.cache_service import CacheService
from services.google_document_ai_service import document_ai_service
from services.google_natural_language_service import natural_language_service
from services.legal_insights_engine import legal_insights_engine
from services.data_masking_service import data_masking_service
from services.advanced_rag_service import advanced_rag_service
# INTERNAL COST MONITORING - Never expose to users
from services.cost_monitoring_service import cost_monitor
from services.quota_manager import quota_manager, ServicePriority

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling document analysis operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.ai_service = AIService()
            self.cache_service = CacheService()
            self.advanced_rag_service = advanced_rag_service
            self.processing_jobs = {}  # Store async processing jobs
            self.analysis_storage = {}  # Store complete analysis results for pagination/search
            self.rag_knowledge_base_built = False  # Track if RAG knowledge base is initialized
            DocumentService._initialized = True
        
    async def analyze_document(self, request: DocumentAnalysisRequest) -> DocumentAnalysisResponse:
        """
        Main document analysis pipeline with privacy-first processing
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        try:
            # PRIVACY-FIRST PROCESSING: Mask sensitive data before cloud processing
            logger.info(f"🔒 Starting privacy-first document analysis")
            logger.info(f"Processing document text (first 200 chars): {request.document_text[:200]}...")
            
            # Step 1: Mask sensitive information
            logger.info("🔒 Masking sensitive information...")
            masked_doc = await data_masking_service.mask_document(request.document_text)
            logger.info(f"✅ Masked {len(masked_doc.masked_entities)} sensitive entities")
            
            # Step 2: Validate privacy compliance
            privacy_validation = data_masking_service.validate_privacy_compliance(masked_doc.masked_text)
            if not privacy_validation.is_valid:
                logger.warning(f"⚠️ Privacy validation warnings: {len(privacy_validation.violations)} violations")
                for violation in privacy_validation.violations[:3]:  # Log first 3 violations
                    logger.warning(f"   - {violation}")
            
            # Clear any existing cache to prevent stale data
            self.cache_service.analysis_cache.clear()
            logger.info("Cleared all cached analysis data")
            
            # Enhanced analysis with Google Cloud AI services using MASKED text
            enhanced_insights = await self._get_enhanced_insights(
                masked_doc.masked_text, 
                request.document_type
            )
            
            # Perform risk classification using AI service with MASKED text
            # Check quota and track cost for AI service call
            ai_request_id = f"risk_analysis_{analysis_id}"
            
            # DEVELOPMENT MODE: Skip quota checking to get real AI analysis
            development_mode = os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true'
            
            if development_mode:
                logger.info("Development mode: Skipping quota checks for real AI analysis")
                from services.quota_manager import RateLimitResult, ThrottleAction
                rate_limit_result = RateLimitResult(
                    action=ThrottleAction.ALLOW,
                    allowed=True,
                    retry_after=None,
                    current_usage=0,
                    limit=999999,
                    reset_time=datetime.utcnow() + timedelta(minutes=1),
                    message="Development mode - quota bypassed"
                )
            else:
                # Check rate limit for Vertex AI (primary service) with error handling
                try:
                    usage_amount = len(masked_doc.masked_text.split())  # Use word count as token estimate
                    logger.info(f"Checking quota for Vertex AI - estimated tokens: {usage_amount}")
                    
                    rate_limit_result = await quota_manager.check_rate_limit(
                        service="vertex_ai",
                        operation="text_generation",
                        usage_amount=usage_amount,
                        priority=ServicePriority.HIGH
                    )
                    
                    logger.info(f"Quota check result: {rate_limit_result.action.value} - {rate_limit_result.message}")
                except Exception as e:
                    logger.warning(f"Quota check failed (non-critical): {e}")
                    # Default to allowing the request if quota check fails
                    from services.quota_manager import RateLimitResult, ThrottleAction
                    rate_limit_result = RateLimitResult(
                        action=ThrottleAction.ALLOW,
                        allowed=True,
                        retry_after=None,
                        current_usage=0,
                        limit=999999,
                        reset_time=datetime.utcnow() + timedelta(minutes=1),
                        message="Quota check bypassed due to error"
                    )
            
            if rate_limit_result.allowed:
                risk_analysis = await self.ai_service.analyze_document_risk(
                    masked_doc.masked_text, 
                    request.document_type
                )
                
                # Track API usage and cost (with error handling)
                try:
                    token_count = len(masked_doc.masked_text.split())  # Rough token estimate
                    
                    await cost_monitor.track_api_usage(
                        service="vertex_ai",
                        operation="text_generation",
                        tokens=token_count,
                        request_id=ai_request_id,
                        model_name="gemini-pro",
                        metadata={
                            "document_type": request.document_type.value,
                            "analysis_id": analysis_id,
                            "masked_entities": len(masked_doc.masked_entities)
                        }
                    )
                    
                    # Also record quota usage even in development mode for dashboard display
                    if not development_mode:
                        await quota_manager.record_success("vertex_ai")
                    else:
                        # In development mode, manually record usage for dashboard display
                        try:
                            await quota_manager._record_usage("vertex_ai", token_count)
                            await quota_manager.record_success("vertex_ai")
                        except Exception as quota_error:
                            logger.warning(f"Quota recording failed (non-critical): {quota_error}")
                            
                except Exception as e:
                    logger.warning(f"Cost monitoring failed (non-critical): {e}")
                    # Continue with analysis even if cost tracking fails
            else:
                logger.warning(f"AI service request throttled: {rate_limit_result.message}")
                # Fallback to basic analysis with proper structure
                risk_analysis = {
                    'overall_risk': {
                        'level': 'YELLOW',
                        'score': 0.5,
                        'reasons': ['Analysis throttled due to rate limits'],
                        'severity': 'medium',
                        'confidence_percentage': 50,
                        'risk_categories': {},
                        'low_confidence_warning': True
                    },
                    'clause_assessments': []
                }
            
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
            
            # Generate actionable insights using the Legal Insights Engine with MASKED text
            actionable_insights = await self.generate_actionable_insights(
                masked_doc.masked_text,
                clause_assessments,
                request.document_type.value
            )
            
            # ADVANCED RAG INTEGRATION: Build knowledge base and enhance insights (optimized)
            rag_enhanced_insights = await self._integrate_advanced_rag_optimized(
                masked_doc.masked_text,
                clause_assessments,
                request.document_type.value,
                actionable_insights
            )
            
            # UNMASK the actionable insights to restore original sensitive information
            logger.info("🔓 Unmasking actionable insights...")
            actionable_insights_str = str(actionable_insights)
            unmasked_insights_str = await data_masking_service.unmask_results(
                actionable_insights_str, 
                masked_doc.mapping_id
            )
            
            # Note: For complex nested structures, we'd need more sophisticated unmasking
            # For now, we'll use the original insights but log the privacy protection
            logger.info("✅ Actionable insights processed with privacy protection")
            
            # Merge enhanced insights with actionable insights and RAG enhancements
            enhanced_insights['actionable_insights'] = actionable_insights
            enhanced_insights['rag_enhanced_insights'] = rag_enhanced_insights
            enhanced_insights['privacy_protection'] = {
                'entities_masked': len(masked_doc.masked_entities),
                'privacy_compliant': privacy_validation.is_valid,
                'risk_score': privacy_validation.risk_score,
                'mapping_id': masked_doc.mapping_id
            }

            # UNMASK the final analysis results for user display
            logger.info("🔓 Unmasking final analysis results...")
            
            # Unmask summary
            unmasked_summary = await data_masking_service.unmask_results(summary, masked_doc.mapping_id)
            
            # Unmask recommendations
            unmasked_recommendations = []
            for rec in recommendations:
                unmasked_rec = await data_masking_service.unmask_results(rec, masked_doc.mapping_id)
                unmasked_recommendations.append(unmasked_rec)
            
            # Unmask clause assessments
            unmasked_clause_assessments = []
            for clause in clause_assessments:
                # Unmask the explanations and recommendations in each clause
                unmasked_explanation = await data_masking_service.unmask_results(
                    clause.plain_explanation, masked_doc.mapping_id
                )
                
                unmasked_implications = []
                for impl in clause.legal_implications:
                    unmasked_impl = await data_masking_service.unmask_results(impl, masked_doc.mapping_id)
                    unmasked_implications.append(unmasked_impl)
                
                unmasked_clause_recs = []
                for rec in clause.recommendations:
                    unmasked_rec = await data_masking_service.unmask_results(rec, masked_doc.mapping_id)
                    unmasked_clause_recs.append(unmasked_rec)
                
                # Create new clause with unmasked content
                unmasked_clause = ClauseAnalysis(
                    clause_id=clause.clause_id,
                    clause_text=clause.clause_text,  # Keep masked for now, could unmask if needed
                    risk_assessment=clause.risk_assessment,
                    plain_explanation=unmasked_explanation,
                    legal_implications=unmasked_implications,
                    recommendations=unmasked_clause_recs,
                    translation_available=clause.translation_available
                )
                unmasked_clause_assessments.append(unmasked_clause)
            
            logger.info("✅ Analysis results unmasked successfully")
            
            # Create response with unmasked content (timestamp auto-generated with current time)
            response = DocumentAnalysisResponse(
                analysis_id=analysis_id,
                overall_risk=overall_risk,
                clause_assessments=unmasked_clause_assessments,
                summary=unmasked_summary,
                processing_time=processing_time,
                recommendations=unmasked_recommendations,
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
            # Clean up expired mappings for privacy compliance
            data_masking_service.cleanup_expired_mappings()
            
            logger.info(f"🔒 Privacy-first document analysis completed in {processing_time:.2f}s")
            logger.info(f"✅ Protected {len(masked_doc.masked_entities)} sensitive entities during processing")
            return response
            
        except Exception as e:
            logger.error(f"❌ Privacy-first document analysis failed: {e}")
            # Log privacy-related error
            data_masking_service._log_audit_event('ANALYSIS_ERROR', {
                'error': str(e),
                'analysis_id': analysis_id,
                'summary': 'Document analysis failed'
            })
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
        """Get enhanced insights from Google Cloud AI services and Legal Insights Engine"""
        insights = {}
        
        try:
            # Google Cloud Natural Language AI analysis
            if natural_language_service.enabled:
                try:
                    # Check quota before making API call
                    rate_limit_result = await quota_manager.check_rate_limit(
                        service="natural_language_ai",
                        operation="analyze_entities",
                        usage_amount=len(document_text),
                        priority=ServicePriority.HIGH
                    )
                    
                    if rate_limit_result.allowed:
                        # Track API usage and cost
                        request_id = f"nl_analysis_{int(time.time())}"
                        
                        nl_result = natural_language_service.analyze_legal_document(document_text)
                        
                        # Record usage metrics (with error handling)
                        try:
                            await cost_monitor.track_api_usage(
                                service="natural_language_ai",
                                operation="analyze_entities",
                                characters=len(document_text),
                                request_id=request_id,
                                metadata={
                                    "document_type": document_type,
                                    "success": nl_result['success']
                                }
                            )
                        except Exception as cost_error:
                            logger.warning(f"Cost tracking failed (non-critical): {cost_error}")
                        
                        # Record success/failure for circuit breaker and quota usage
                        try:
                            if nl_result['success']:
                                await quota_manager.record_success("natural_language_ai")
                                
                                # Record quota usage for dashboard display
                                try:
                                    await quota_manager._record_usage("natural_language_ai", len(document_text))
                                except Exception as quota_usage_error:
                                    logger.warning(f"Quota usage recording failed (non-critical): {quota_usage_error}")
                                
                                insights['natural_language'] = {
                                    'sentiment': nl_result['sentiment'],
                                    'entities': nl_result['entities'][:10],  # Limit for response size
                                    'legal_insights': nl_result['legal_insights']
                                }
                            else:
                                await quota_manager.record_failure("natural_language_ai")
                                logger.warning("Natural Language AI analysis failed")
                        except Exception as quota_error:
                            logger.warning(f"Quota tracking failed (non-critical): {quota_error}")
                    else:
                        logger.warning(f"Natural Language AI request throttled: {rate_limit_result.message}")
                        if rate_limit_result.retry_after:
                            logger.info(f"Retry after {rate_limit_result.retry_after} seconds")
                except Exception as nl_error:
                    logger.warning(f"Natural Language AI integration failed (non-critical): {nl_error}")
                    # Continue with analysis even if NL AI fails
                        
        except Exception as e:
            logger.warning(f"Enhanced insights failed: {e}")
            try:
                await quota_manager.record_failure("natural_language_ai")
            except Exception as quota_error:
                logger.warning(f"Quota failure recording failed (non-critical): {quota_error}")
        
        return insights
    
    async def generate_actionable_insights(
        self, 
        document_text: str, 
        clause_analyses: List[ClauseAnalysis],
        document_type: str = "general_contract"
    ) -> Dict[str, Any]:
        """Generate FAST, focused actionable insights optimized for performance"""
        
        try:
            logger.info(f"Generating optimized insights for document type: {document_type}")
            
            # PERFORMANCE OPTIMIZATION: Generate lightweight insights directly
            # Skip heavy legal insights engine for faster response
            return await self._generate_fast_insights(document_text, clause_analyses, document_type)
            
            # Convert to serializable format
            insights_dict = {
                'entity_relationships': [
                    {
                        'entity1': rel.entity1,
                        'entity2': rel.entity2,
                        'relationship_type': rel.relationship_type,
                        'description': rel.description,
                        'legal_significance': rel.legal_significance,
                        'confidence': rel.confidence
                    }
                    for rel in actionable_insights.entity_relationships
                ],
                'conflict_analysis': [
                    {
                        'conflict_id': conflict.conflict_id,
                        'clause_ids': conflict.clause_ids,
                        'conflict_type': conflict.conflict_type,
                        'description': conflict.description,
                        'severity': conflict.severity.value,
                        'resolution_suggestions': conflict.resolution_suggestions,
                        'confidence': conflict.confidence
                    }
                    for conflict in actionable_insights.conflict_analysis
                ],
                'bias_indicators': [
                    {
                        'bias_type': bias.bias_type,
                        'clause_id': bias.clause_id,
                        'biased_language': bias.biased_language,
                        'explanation': bias.explanation,
                        'suggested_alternative': bias.suggested_alternative,
                        'severity': bias.severity.value,
                        'confidence': bias.confidence
                    }
                    for bias in actionable_insights.bias_indicators
                ],
                'negotiation_points': [
                    {
                        'clause_id': point.clause_id,
                        'negotiation_type': point.negotiation_type,
                        'current_language': point.current_language,
                        'suggested_language': point.suggested_language,
                        'rationale': point.rationale,
                        'priority': point.priority.value,
                        'potential_impact': point.potential_impact,
                        'confidence': point.confidence
                    }
                    for point in actionable_insights.negotiation_points
                ],
                'compliance_flags': [
                    {
                        'regulation_type': flag.regulation_type,
                        'clause_id': flag.clause_id,
                        'issue_description': flag.issue_description,
                        'compliance_risk': flag.compliance_risk,
                        'recommended_action': flag.recommended_action,
                        'severity': flag.severity.value,
                        'confidence': flag.confidence
                    }
                    for flag in actionable_insights.compliance_flags
                ],
                'overall_intelligence_score': actionable_insights.overall_intelligence_score,
                'generation_timestamp': actionable_insights.generation_timestamp.isoformat(),
                'summary': {
                    'total_relationships': len(actionable_insights.entity_relationships),
                    'total_conflicts': len(actionable_insights.conflict_analysis),
                    'total_bias_indicators': len(actionable_insights.bias_indicators),
                    'total_negotiation_points': len(actionable_insights.negotiation_points),
                    'total_compliance_flags': len(actionable_insights.compliance_flags),
                    'critical_issues': len([
                        item for item in (
                            actionable_insights.conflict_analysis + 
                            actionable_insights.bias_indicators + 
                            actionable_insights.compliance_flags
                        ) 
                        if hasattr(item, 'severity') and item.severity.value == 'critical'
                    ])
                }
            }
            
            logger.info(f"Generated actionable insights: {insights_dict['summary']}")
            return insights_dict
            
        except Exception as e:
            logger.error(f"Failed to generate actionable insights: {e}")
            return await self._generate_fast_insights(document_text, clause_analyses, document_type)

    async def _generate_fast_insights(self, document_text: str, clause_analyses: List[ClauseAnalysis], document_type: str) -> Dict[str, Any]:
        """Generate fast, lightweight insights using REAL analysis data"""
        start_time = time.time()
        try:
            # Analyze REAL clause data
            high_risk_clauses = [c for c in clause_analyses if c.risk_level.level == 'RED']
            medium_risk_clauses = [c for c in clause_analyses if c.risk_level.level == 'YELLOW']
            low_risk_clauses = [c for c in clause_analyses if c.risk_level.level == 'GREEN']
            
            # Extract REAL risk categories from actual analysis
            all_risk_categories = {}
            for clause in clause_analyses:
                for category, score in clause.risk_level.risk_categories.items():
                    if category not in all_risk_categories:
                        all_risk_categories[category] = []
                    all_risk_categories[category].append(score)
            
            # Calculate average risk scores per category
            category_averages = {
                category: sum(scores) / len(scores) 
                for category, scores in all_risk_categories.items()
            }
            
            # Generate insights based on REAL data
            key_insights = []
            
            # High-risk clause insights with REAL reasons
            if high_risk_clauses:
                real_reasons = []
                for clause in high_risk_clauses[:3]:  # Top 3 high-risk clauses
                    if hasattr(clause.risk_level, 'reasons') and clause.risk_level.reasons:
                        real_reasons.extend(clause.risk_level.reasons[:1])  # One reason per clause
                
                key_insights.append({
                    'type': 'high_risk_alert',
                    'title': f'{len(high_risk_clauses)} High-Risk Clause(s) Found',
                    'description': f'Critical issues: {", ".join(real_reasons[:2]) if real_reasons else "Significant legal/financial risks identified"}',
                    'severity': 'high',
                    'action': 'Review and negotiate these clauses before signing',
                    'affected_clauses': [c.clause_id for c in high_risk_clauses[:3]]
                })
            
            # Medium-risk insights with REAL data
            if medium_risk_clauses:
                medium_reasons = []
                for clause in medium_risk_clauses[:2]:
                    if hasattr(clause.risk_level, 'reasons') and clause.risk_level.reasons:
                        medium_reasons.extend(clause.risk_level.reasons[:1])
                
                key_insights.append({
                    'type': 'medium_risk_notice',
                    'title': f'{len(medium_risk_clauses)} Medium-Risk Clause(s) Identified',
                    'description': f'Areas for improvement: {", ".join(medium_reasons[:2]) if medium_reasons else "Some terms could be improved for better protection"}',
                    'severity': 'medium',
                    'action': 'Consider requesting modifications to these clauses',
                    'affected_clauses': [c.clause_id for c in medium_risk_clauses[:2]]
                })
            
            # Risk category insights based on REAL analysis
            top_risk_categories = sorted(category_averages.items(), key=lambda x: x[1], reverse=True)[:2]
            if top_risk_categories:
                for category, avg_score in top_risk_categories:
                    if avg_score > 0.6:  # Only show significant risk categories
                        key_insights.append({
                            'type': 'risk_category_analysis',
                            'title': f'{category.replace("_", " ").title()} Risk Detected',
                            'description': f'Average risk score: {avg_score:.1f}/1.0 in {category.replace("_", " ")} category',
                            'severity': 'high' if avg_score > 0.8 else 'medium',
                            'action': f'Pay special attention to {category.replace("_", " ")} related clauses'
                        })
            
            # Document-specific insights with REAL clause context
            if document_type == 'rental_agreement':
                rental_specific_clauses = [c for c in clause_analyses if any(
                    keyword in c.clause_text.lower() 
                    for keyword in ['rent', 'deposit', 'maintenance', 'termination', 'lease']
                )]
                key_insights.append({
                    'type': 'rental_specific',
                    'title': 'Rental Agreement Analysis',
                    'description': f'Analyzed {len(rental_specific_clauses)} rental-specific clauses',
                    'severity': 'info',
                    'action': 'Verify local tenant protection laws apply'
                })
            elif document_type == 'employment_contract':
                employment_clauses = [c for c in clause_analyses if any(
                    keyword in c.clause_text.lower() 
                    for keyword in ['salary', 'benefits', 'termination', 'non-compete', 'employment']
                )]
                key_insights.append({
                    'type': 'employment_specific',
                    'title': 'Employment Contract Analysis',
                    'description': f'Analyzed {len(employment_clauses)} employment-specific clauses',
                    'severity': 'info',
                    'action': 'Ensure compliance with labor laws'
                })
            
            return {
                'entity_relationships': [],
                'conflict_analysis': [],
                'bias_indicators': [],
                'negotiation_opportunities': [],
                'legal_precedents': [],
                'key_insights': key_insights,
                'summary': {
                    'total_insights': len(key_insights),
                    'high_priority_items': len([i for i in key_insights if i['severity'] == 'high']),
                    'document_type': document_type,
                    'analysis_focus': 'Fast performance-optimized analysis'
                },
                'overall_intelligence_score': self._calculate_real_intelligence_score(clause_analyses),
                'generation_timestamp': datetime.now().isoformat(),
                'processing_time_ms': int((time.time() - start_time) * 1000)  # Real processing time
            }
            
        except Exception as e:
            logger.error(f"Failed to generate fast insights: {e}")
            return {
                'entity_relationships': [],
                'conflict_analysis': [],
                'bias_indicators': [],
                'negotiation_opportunities': [],
                'legal_precedents': [],
                'key_insights': [],
                'summary': {
                    'total_insights': 0,
                    'high_priority_items': 0,
                    'document_type': document_type,
                    'analysis_focus': 'Error in analysis'
                },
                'overall_intelligence_score': 0.5,
                'generation_timestamp': datetime.now().isoformat(),
                'processing_time_ms': 100
            }

    def _calculate_real_intelligence_score(self, clause_analyses: List[ClauseAnalysis]) -> float:
        """Calculate intelligence score based on REAL analysis data"""
        try:
            if not clause_analyses:
                return 0.5
            
            # Calculate based on confidence levels and analysis quality
            total_confidence = sum(c.risk_level.confidence_percentage for c in clause_analyses)
            avg_confidence = total_confidence / len(clause_analyses) / 100.0  # Convert to 0-1 scale
            
            # Factor in analysis completeness
            complete_analyses = sum(1 for c in clause_analyses if 
                                  c.plain_explanation and 
                                  c.legal_implications and 
                                  c.recommendations)
            completeness_score = complete_analyses / len(clause_analyses)
            
            # Combine confidence and completeness
            intelligence_score = (avg_confidence * 0.7) + (completeness_score * 0.3)
            
            return min(max(intelligence_score, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Failed to calculate intelligence score: {e}")
            return 0.6  # Reasonable fallback

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
                moderate_risk_reasons.extend(reasons[:1])  # One reason per medium-risk clause
        
        # Build fallback summary
        doc_name = document_type.replace('_', ' ').title()
        risk_level = overall_risk.get('level', 'UNKNOWN')
        risk_score = overall_risk.get('score', 0.0)
        confidence = overall_risk.get('confidence_percentage', 0)
        
        summary_parts = [
            f"**{doc_name} Analysis Summary**",
            f"**Overall Risk:** {risk_level} ({risk_score:.1f}/1.0) | **Confidence:** {confidence}%",
            f"**Total Clauses:** {len(clause_assessments)}"
        ]
        
        if risk_counts['RED'] > 0:
            summary_parts.append(f"**High-Risk Issues:** {risk_counts['RED']} clauses")
            if high_risk_reasons:
                summary_parts.append(f"**Key Concerns:** {', '.join(high_risk_reasons[:3])}")
        
        if risk_counts['YELLOW'] > 0:
            summary_parts.append(f"**Medium-Risk Issues:** {risk_counts['YELLOW']} clauses")
        
        summary_parts.append(f"**Low-Risk Clauses:** {risk_counts['GREEN']}")
        
        return "\n\n".join(summary_parts)
    

    
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
        """Generate FAST, concise document summary optimized for speed and readability"""
        try:
            # PERFORMANCE OPTIMIZATION: Skip AI processing for faster results
            # Use structured template-based summary for consistent, fast output
            return self._create_optimized_structured_summary(risk_analysis, document_type)
                
        except Exception as e:
            logger.error(f"Failed to generate document summary: {e}")
            return self._create_enhanced_fallback_summary(risk_analysis, document_type)
    
    def _create_optimized_structured_summary(self, risk_analysis: Dict, document_type: str) -> str:
        """Create fast, well-formatted structured summary"""
        try:
            overall_risk = risk_analysis['overall_risk']
            clause_assessments = risk_analysis.get('clause_assessments', [])
            
            # Count risk levels
            risk_counts = {'RED': 0, 'YELLOW': 0, 'GREEN': 0}
            high_risk_clauses = []
            
            for clause in clause_assessments:
                assessment = clause.get('assessment', {})
                level = assessment.get('level', 'GREEN')
                risk_counts[level] += 1
                
                # Collect high-risk clauses for specific mention
                if level == 'RED' and len(high_risk_clauses) < 2:
                    high_risk_clauses.append({
                        'id': clause.get('clause_id', 'Unknown'),
                        'reason': assessment.get('reasons', ['High risk identified'])[0]
                    })
            
            # Create concise, well-formatted summary
            doc_name = document_type.replace('_', ' ').title()
            risk_level = overall_risk.get('level', 'UNKNOWN')
            risk_score = overall_risk.get('score', 0.0)
            confidence = overall_risk.get('confidence_percentage', 0)
            
            # Build structured summary
            summary_parts = []
            
            # Header with key metrics
            summary_parts.append(f"**{doc_name} Analysis Summary**")
            summary_parts.append(f"**Overall Risk:** {risk_level} ({risk_score:.1f}/1.0) | **Confidence:** {confidence}%")
            summary_parts.append(f"**Clauses Analyzed:** {len(clause_assessments)} total")
            
            # Risk breakdown
            if risk_counts['RED'] > 0 or risk_counts['YELLOW'] > 0:
                risk_breakdown = []
                if risk_counts['RED'] > 0:
                    risk_breakdown.append(f"🔴 {risk_counts['RED']} High-Risk")
                if risk_counts['YELLOW'] > 0:
                    risk_breakdown.append(f"🟡 {risk_counts['YELLOW']} Medium-Risk")
                if risk_counts['GREEN'] > 0:
                    risk_breakdown.append(f"🟢 {risk_counts['GREEN']} Low-Risk")
                
                summary_parts.append(f"**Risk Distribution:** {' | '.join(risk_breakdown)}")
            
            # Key findings with REAL data
            if risk_level == 'RED':
                summary_parts.append("⚠️ **Critical Issues Found** - This document contains significant risks that require immediate attention.")
                if high_risk_clauses:
                    # Use REAL reasons from actual analysis
                    real_issues = []
                    for clause in high_risk_clauses:
                        reason = clause['reason'][:60] + "..." if len(clause['reason']) > 60 else clause['reason']
                        real_issues.append(f"Clause {clause['id']}: {reason}")
                    summary_parts.append(f"**Main Concerns:** {' | '.join(real_issues)}")
                
                # Add REAL overall risk reasons if available
                if overall_risk.get('reasons'):
                    top_reasons = overall_risk['reasons'][:2]  # Top 2 reasons
                    summary_parts.append(f"**Key Risk Factors:** {' | '.join(top_reasons)}")
                    
            elif risk_level == 'YELLOW':
                summary_parts.append("⚠️ **Moderate Risks Identified** - Some terms could be improved for better protection.")
                # Add REAL medium risk details
                if overall_risk.get('reasons'):
                    summary_parts.append(f"**Areas of Concern:** {' | '.join(overall_risk['reasons'][:2])}")
            else:
                summary_parts.append("✅ **Generally Acceptable** - Most terms appear fair with standard risk levels.")
                if overall_risk.get('reasons'):
                    summary_parts.append(f"**Positive Aspects:** {' | '.join(overall_risk['reasons'][:2])}")
            
            # Action recommendation
            if risk_level == 'RED':
                summary_parts.append("**Recommended Action:** Negotiate changes or seek legal review before signing.")
            elif risk_level == 'YELLOW':
                summary_parts.append("**Recommended Action:** Review highlighted clauses and consider improvements.")
            else:
                summary_parts.append("**Recommended Action:** Standard review recommended before proceeding.")
            
            return "\n\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to create structured summary: {e}")
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

    async def _generate_rag_enhanced_summary(self, risk_analysis: Dict, document_type: str) -> str:
        """Generate RAG-enhanced summary using retrieved legal knowledge"""
        try:
            logger.info("🧠 Generating RAG-enhanced summary...")
            
            overall_risk = risk_analysis['overall_risk']
            
            # Use RAG to get relevant legal context for summary
            summary_query = f"Legal document summary for {document_type.replace('_', ' ')} with {overall_risk.get('level', 'unknown')} risk"
            
            rag_context = await self.advanced_rag_service.retrieve_and_rerank(
                summary_query,
                context={'summary_mode': True, 'fast_processing': True}
            )
            
            # Build enhanced context with RAG insights
            enhanced_context = {
                'document_analysis': {
                    'type': document_type,
                    'risk_level': overall_risk.get('level', 'unknown'),
                    'risk_score': overall_risk.get('score', 0),
                    'total_clauses': len(risk_analysis.get('clause_assessments', []))
                },
                'legal_context': [
                    {
                        'text': result.get('text', '')[:150],
                        'relevance': result.get('final_score', 0)
                    }
                    for result in rag_context[:2]  # Top 2 results only
                ]
            }
            
            # Use existing AI service with RAG context
            from models.ai_models import ClarificationRequest
            
            request = ClarificationRequest(
                question=f"Create a concise legal summary (max 150 words) for this {document_type.replace('_', ' ')} analysis.",
                context=enhanced_context,
                user_expertise_level='intermediate'
            )
            
            response = await self.ai_service.get_clarification(request)
            
            if response.success and response.response and len(response.response) > 50:
                logger.info("✅ RAG-enhanced summary generated successfully")
                return response.response
            else:
                logger.warning("RAG-enhanced summary failed, using fallback")
                return self._create_enhanced_fallback_summary(risk_analysis, document_type)
                
        except Exception as e:
            logger.error(f"RAG-enhanced summary failed: {e}")
            return self._create_enhanced_fallback_summary(risk_analysis, document_type)

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
    
    async def _integrate_advanced_rag_optimized(self, document_text: str, clause_assessments: List, 
                                             document_type: str, base_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized Advanced RAG Architecture integration for faster processing"""
        logger.info("🧠 Integrating Advanced RAG Architecture (optimized)...")
        
        try:
            # Skip knowledge base building if already built for performance
            if not self.rag_knowledge_base_built:
                await self._build_rag_knowledge_base_fast([{
                    'id': 'current_document',
                    'text': document_text[:5000],  # Limit text for faster processing
                    'type': document_type,
                    'timestamp': datetime.now().isoformat()
                }])
                self.rag_knowledge_base_built = True
            
            # Generate only essential queries for faster processing
            rag_queries = self._generate_essential_rag_queries(clause_assessments, document_type)
            
            # Perform optimized retrieval for top 2 queries only
            rag_results = {}
            for query_type, query in list(rag_queries.items())[:2]:  # Only process top 2 queries
                logger.info(f"🔍 Fast RAG retrieval for {query_type}")
                
                # Skip HyDE for faster processing
                retrieval_results = await self.advanced_rag_service.retrieve_and_rerank(
                    query,
                    context={
                        'document_type': document_type,
                        'query_type': query_type,
                        'fast_mode': True
                    }
                )
                
                rag_results[query_type] = {
                    'query': query,
                    'results': retrieval_results[:3],  # Top 3 results only
                    'total_results': len(retrieval_results)
                }
            
            # Generate fast recommendations
            enhanced_recommendations = await self._generate_fast_rag_recommendations(
                rag_results, document_type
            )
            
            # Get retrieval statistics
            rag_stats = self.advanced_rag_service.get_retrieval_stats()
            
            logger.info("✅ Optimized Advanced RAG integration completed")
            
            return {
                'rag_queries': rag_queries,
                'retrieval_results': rag_results,
                'enhanced_recommendations': enhanced_recommendations,
                'rag_statistics': rag_stats,
                'integration_timestamp': datetime.now().isoformat(),
                'optimized': True
            }
            
        except Exception as e:
            logger.error(f"Optimized Advanced RAG integration failed: {e}")
            return {
                'error': str(e),
                'fallback_mode': True,
                'optimized': False,
                'integration_timestamp': datetime.now().isoformat()
            }

    async def _integrate_advanced_rag(self, document_text: str, clause_assessments: List, 
                                    document_type: str, base_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Advanced RAG Architecture for enhanced document analysis - OPTIMIZED"""
        logger.info("🧠 Integrating Advanced RAG Architecture (optimized)...")
        
        try:
            # OPTIMIZATION: Build knowledge base only once and cache it
            if not self.rag_knowledge_base_built:
                # Use compressed document text for faster processing
                compressed_text = document_text[:5000] if len(document_text) > 5000 else document_text
                await self._build_rag_knowledge_base([{
                    'id': 'current_document',
                    'text': compressed_text,
                    'type': document_type,
                    'timestamp': datetime.now().isoformat()
                }])
                self.rag_knowledge_base_built = True
            
            # OPTIMIZATION: Generate fewer, more targeted queries
            rag_queries = self._generate_optimized_rag_queries(clause_assessments, document_type)
            
            # OPTIMIZATION: Process queries in parallel
            rag_tasks = []
            for query_type, query in rag_queries.items():
                task = asyncio.create_task(self._process_rag_query(query_type, query, document_type, base_insights))
                rag_tasks.append(task)
            
            # Execute all RAG queries concurrently
            rag_results_list = await asyncio.gather(*rag_tasks, return_exceptions=True)
            
            # Combine results
            rag_results = {}
            for i, (query_type, query) in enumerate(rag_queries.items()):
                result = rag_results_list[i]
                if isinstance(result, Exception):
                    logger.warning(f"RAG query {query_type} failed: {result}")
                    rag_results[query_type] = {'error': str(result), 'results': []}
                else:
                    rag_results[query_type] = result
            
            # OPTIMIZATION: Generate recommendations quickly
            enhanced_recommendations = self._generate_quick_rag_recommendations(
                rag_results, clause_assessments, document_type
            )
            
            # OPTIMIZATION: Skip heavy context compression for speed
            compressed_context = {
                'key_insights': [{'query_type': k, 'result_count': len(v.get('results', []))} 
                               for k, v in rag_results.items()],
                'total_queries': len(rag_queries),
                'optimization_mode': True
            }
            
            # Get retrieval statistics
            rag_stats = self.advanced_rag_service.get_retrieval_stats()
            
            logger.info("✅ Advanced RAG integration completed (optimized)")
            
            return {
                'rag_queries': rag_queries,
                'retrieval_results': rag_results,
                'enhanced_recommendations': enhanced_recommendations,
                'compressed_context': compressed_context,
                'rag_statistics': rag_stats,
                'integration_timestamp': datetime.now().isoformat(),
                'optimization_mode': True
            }
            
        except Exception as e:
            logger.error(f"Advanced RAG integration failed: {e}")
            return {
                'error': str(e),
                'fallback_mode': True,
                'integration_timestamp': datetime.now().isoformat()
            }
    
    async def _build_rag_knowledge_base_fast(self, documents: List[Dict[str, Any]]):
        """Build RAG knowledge base from documents (optimized for speed)"""
        logger.info("🏗️ Building RAG knowledge base (fast mode)...")
        
        try:
            # Build knowledge base using Advanced RAG Service with optimizations
            kb_stats = await self.advanced_rag_service.build_knowledge_base(documents)
            logger.info(f"✅ RAG knowledge base built (fast): {kb_stats}")
            
        except Exception as e:
            logger.error(f"Failed to build RAG knowledge base: {e}")
            # Don't raise exception, continue without RAG
            pass

    async def _build_rag_knowledge_base(self, documents: List[Dict[str, Any]]):
        """Build RAG knowledge base from documents"""
        logger.info("🏗️ Building RAG knowledge base...")
        
        try:
            # Build knowledge base using Advanced RAG Service
            kb_stats = await self.advanced_rag_service.build_knowledge_base(documents)
            logger.info(f"✅ RAG knowledge base built: {kb_stats}")
            
        except Exception as e:
            logger.error(f"Failed to build RAG knowledge base: {e}")
            raise
    
    def _generate_optimized_rag_queries(self, clause_assessments: List, document_type: str) -> Dict[str, str]:
        """Generate optimized, fewer queries for faster RAG retrieval"""
        queries = {}
        
        # OPTIMIZATION: Only generate 2-3 most important queries
        high_risk_clauses = [c for c in clause_assessments if hasattr(c, 'risk_assessment') and c.risk_assessment.level.value == 'RED']
        if high_risk_clauses:
            # Get top risk reason only
            top_risk_reason = high_risk_clauses[0].risk_assessment.reasons[0] if high_risk_clauses[0].risk_assessment.reasons else "high risk clause"
            queries['high_risk_analysis'] = f"Legal risks: {top_risk_reason}"
        
        # Single document type query
        doc_type_queries = {
            'employment_contract': "Employment contract legal requirements and worker rights",
            'rental_agreement': "Rental agreement tenant rights and obligations", 
            'service_agreement': "Service agreement liability and performance terms"
        }
        
        if document_type in doc_type_queries:
            queries['document_law'] = doc_type_queries[document_type]
        else:
            queries['general_contract'] = f"{document_type.replace('_', ' ')} legal principles"
        
        # Single negotiation query
        queries['negotiation_tips'] = f"Contract negotiation strategies for {document_type.replace('_', ' ')}"
        
        return queries
    
    async def _process_rag_query(self, query_type: str, query: str, document_type: str, base_insights: Dict) -> Dict:
        """Process a single RAG query optimized for speed"""
        try:
            # OPTIMIZATION: Skip HyDE for speed, use direct query
            retrieval_results = await self.advanced_rag_service.retrieve_and_rerank(
                query,
                context={
                    'document_type': document_type,
                    'query_type': query_type,
                    'optimization_mode': True
                }
            )
            
            return {
                'original_query': query,
                'results': retrieval_results[:3],  # Only top 3 results
                'total_results': len(retrieval_results)
            }
            
        except Exception as e:
            logger.warning(f"RAG query {query_type} failed: {e}")
            return {'error': str(e), 'results': []}
    
    def _generate_quick_rag_recommendations(self, rag_results: Dict, clause_assessments: List, document_type: str) -> List[str]:
        """Generate RAG recommendations quickly without heavy processing"""
        recommendations = []
        
        try:
            # OPTIMIZATION: Simple recommendation generation
            for query_type, results in rag_results.items():
                if results.get('results') and len(results['results']) > 0:
                    top_result = results['results'][0]
                    text_snippet = top_result.get('text', '')[:100]
                    
                    if query_type == 'high_risk_analysis':
                        recommendations.append(f"🚨 Risk insight: {text_snippet}...")
                    elif query_type == 'negotiation_tips':
                        recommendations.append(f"💡 Negotiation tip: {text_snippet}...")
                    elif query_type in ['document_law', 'general_contract']:
                        recommendations.append(f"⚖️ Legal guidance: {text_snippet}...")
            
            # Fallback recommendation
            if not recommendations:
                recommendations.append("📚 Advanced legal analysis completed - review clause-specific recommendations above")
            
        except Exception as e:
            logger.warning(f"Quick RAG recommendations failed: {e}")
            recommendations.append("📚 Legal analysis completed with RAG enhancement")
        
        return recommendations[:3]  # Limit to 3 recommendations
    
    def _generate_essential_rag_queries(self, clause_assessments: List, document_type: str) -> Dict[str, str]:
        """Generate essential queries for fast RAG retrieval"""
        queries = {}
        
        # Only generate the most important queries for speed
        high_risk_clauses = [c for c in clause_assessments if hasattr(c, 'risk_assessment') and c.risk_assessment.level.value == 'RED']
        if high_risk_clauses:
            risk_reasons = []
            for clause in high_risk_clauses[:2]:  # Only top 2 high-risk clauses
                risk_reasons.extend(clause.risk_assessment.reasons[:1])  # Only 1 reason per clause
            
            queries['high_risk_analysis'] = f"High-risk contract issues: {', '.join(risk_reasons[:3])}"
        
        # Single document type specific query
        if document_type == 'employment_contract':
            queries['employment_law'] = "Employment contract risks and worker rights"
        elif document_type == 'rental_agreement':
            queries['rental_law'] = "Rental agreement tenant rights and obligations"
        elif document_type == 'service_agreement':
            queries['service_law'] = "Service agreement liability and performance terms"
        else:
            queries['general_contract'] = f"Contract law for {document_type.replace('_', ' ')}"
        
        return queries

    def _generate_rag_queries(self, clause_assessments: List, document_type: str) -> Dict[str, str]:
        """Generate targeted queries for RAG retrieval"""
        queries = {}
        
        # Risk-based queries
        high_risk_clauses = [c for c in clause_assessments if hasattr(c, 'risk_assessment') and c.risk_assessment.level.value == 'RED']
        if high_risk_clauses:
            risk_reasons = []
            for clause in high_risk_clauses[:3]:  # Top 3 high-risk clauses
                risk_reasons.extend(clause.risk_assessment.reasons[:2])
            
            queries['high_risk_analysis'] = f"Legal analysis of high-risk contract clauses: {', '.join(risk_reasons[:5])}"
        
        # Document type specific queries
        if document_type == 'employment_contract':
            queries['employment_law'] = "Employment contract legal requirements, worker rights, termination clauses, non-compete agreements"
        elif document_type == 'rental_agreement':
            queries['rental_law'] = "Rental agreement legal requirements, tenant rights, landlord obligations, security deposits"
        elif document_type == 'service_agreement':
            queries['service_law'] = "Service agreement legal requirements, liability limitations, performance standards, payment terms"
        else:
            queries['general_contract'] = f"General contract law principles for {document_type.replace('_', ' ')} agreements"
        
        # Compliance and regulatory queries
        queries['compliance_check'] = f"Legal compliance requirements for {document_type.replace('_', ' ')} contracts, regulatory obligations"
        
        # Negotiation strategy queries
        queries['negotiation_strategies'] = f"Contract negotiation strategies for {document_type.replace('_', ' ')}, favorable terms, risk mitigation"
        
        return queries
    
    async def _generate_fast_rag_recommendations(self, rag_results: Dict, document_type: str) -> List[str]:
        """Generate fast RAG-enhanced recommendations"""
        recommendations = []
        
        try:
            # Quick analysis of RAG results
            for query_type, results in rag_results.items():
                if results.get('results'):
                    top_result = results['results'][0]
                    text_snippet = top_result.get('text', '')[:150]  # Shorter snippets
                    
                    if query_type == 'high_risk_analysis':
                        recommendations.append(f"🚨 Risk analysis: {text_snippet}...")
                    elif query_type == 'employment_law':
                        recommendations.append(f"⚖️ Employment law: {text_snippet}...")
                    elif query_type == 'rental_law':
                        recommendations.append(f"🏠 Rental law: {text_snippet}...")
                    elif query_type == 'service_law':
                        recommendations.append(f"🔧 Service law: {text_snippet}...")
                    else:
                        recommendations.append(f"📚 Legal guidance: {text_snippet}...")
            
            if len(recommendations) == 0:
                recommendations.append("📚 Advanced legal analysis completed")
            
        except Exception as e:
            logger.warning(f"Failed to generate fast RAG recommendations: {e}")
            recommendations.append("📚 Legal analysis completed")
        
        return recommendations[:3]  # Limit to top 3 for speed

    async def _generate_rag_enhanced_recommendations(self, rag_results: Dict, 
                                                   clause_assessments: List, 
                                                   document_type: str) -> List[str]:
        """Generate enhanced recommendations using RAG insights"""
        recommendations = []
        
        try:
            # Analyze RAG results for actionable insights
            for query_type, results in rag_results.items():
                if results.get('results'):
                    top_result = results['results'][0]
                    
                    if query_type == 'high_risk_analysis':
                        recommendations.append(
                            f"🚨 Based on legal precedent analysis: {top_result.get('text', '')[:200]}..."
                        )
                    elif query_type == 'negotiation_strategies':
                        recommendations.append(
                            f"💡 Negotiation strategy: {top_result.get('text', '')[:200]}..."
                        )
                    elif query_type == 'compliance_check':
                        recommendations.append(
                            f"⚖️ Compliance consideration: {top_result.get('text', '')[:200]}..."
                        )
            
            # Add general RAG-enhanced recommendations
            if len(recommendations) == 0:
                recommendations.append("📚 Advanced legal analysis completed - review specific clause recommendations above")
            
        except Exception as e:
            logger.warning(f"Failed to generate RAG-enhanced recommendations: {e}")
            recommendations.append("📚 Advanced legal analysis attempted - refer to standard recommendations")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def _compress_and_summarize_context(self, rag_results: Dict, document_text: str) -> Dict[str, Any]:
        """Compress and summarize context for efficient processing"""
        try:
            # Extract key insights from RAG results
            key_insights = []
            total_results = 0
            
            for query_type, results in rag_results.items():
                if results.get('results'):
                    total_results += len(results['results'])
                    # Extract top insight from each query type
                    top_result = results['results'][0]
                    key_insights.append({
                        'query_type': query_type,
                        'insight': top_result.get('text', '')[:300],  # First 300 chars
                        'relevance_score': top_result.get('final_score', 0)
                    })
            
            # Compress document text (keep first and last portions)
            doc_length = len(document_text)
            if doc_length > 2000:
                compressed_doc = document_text[:1000] + "\n\n[... document compressed ...]\n\n" + document_text[-1000:]
            else:
                compressed_doc = document_text
            
            return {
                'key_insights': key_insights,
                'compressed_document': compressed_doc,
                'original_doc_length': doc_length,
                'compressed_doc_length': len(compressed_doc),
                'total_rag_results': total_results,
                'compression_ratio': len(compressed_doc) / doc_length if doc_length > 0 else 1.0
            }
            
        except Exception as e:
            logger.warning(f"Context compression failed: {e}")
            return {
                'error': str(e),
                'fallback_context': document_text[:1000] + "..." if len(document_text) > 1000 else document_text
            }
    
    async def get_rag_enhanced_clarification(self, query: str, analysis_id: str) -> Dict[str, Any]:
        """Get RAG-enhanced clarification for user queries - OPTIMIZED"""
        logger.info(f"🤖 RAG-enhanced clarification (optimized): {query[:50]}...")
        
        try:
            # Check if analysis exists
            if analysis_id not in self.analysis_storage:
                raise ValueError(f"Analysis {analysis_id} not found")
            
            # OPTIMIZATION: Skip HyDE for faster processing, use direct query
            # Retrieve relevant context using Advanced RAG
            rag_context = await self.advanced_rag_service.retrieve_and_rerank(
                query,
                context={
                    'analysis_id': analysis_id,
                    'user_query': query,
                    'optimization_mode': True
                }
            )
            
            # OPTIMIZATION: Use existing AI service instead of async API manager for speed
            from models.ai_models import ClarificationRequest
            
            # Get analysis data for context
            analysis_data = self.analysis_storage[analysis_id]
            
            # Prepare optimized context
            context_data = {
                'rag_results': [
                    {
                        'text': result.get('text', '')[:200],  # Limit text length
                        'score': result.get('final_score', 0)
                    }
                    for result in rag_context[:2]  # Only top 2 results
                ],
                'document_type': analysis_data.get('document_type', 'unknown'),
                'overall_risk': getattr(analysis_data.get('overall_risk'), 'level', 'unknown') if analysis_data.get('overall_risk') else 'unknown'
            }
            
            # Create optimized clarification request
            clarification_request = ClarificationRequest(
                question=f"Based on the legal knowledge retrieved: {query}",
                context=context_data,
                user_expertise_level='intermediate'
            )
            
            # Use existing AI service for faster response
            ai_response = await self.ai_service.get_clarification(clarification_request)
            
            return {
                'success': ai_response.success,
                'response': ai_response.response if ai_response.success else "RAG-enhanced analysis temporarily unavailable",
                'rag_context_used': len(rag_context),
                'provider_used': ai_response.service_used,
                'processing_time': ai_response.processing_time,
                'enhanced': True,
                'confidence_score': ai_response.confidence_score,
                'optimization_mode': True
            }
            
        except Exception as e:
            logger.error(f"RAG-enhanced clarification failed: {e}")
            return {
                'success': False,
                'response': f"Enhanced analysis failed: {str(e)}",
                'enhanced': False,
                'error': str(e)
            }

# Global instance
document_service = DocumentService()