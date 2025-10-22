"""
Enhanced AI service with Gemini API primary integration and minimal Vertex AI support
"""

import os
import time
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cachetools import TTLCache

from models.ai_models import ClarificationRequest, ClarificationResponse, ConversationSummaryResponse
from services.personalization_engine import PersonalizationEngine

# Configure enhanced logging for AI service
logger = logging.getLogger(__name__)

# Create a separate logger for request/response debugging
debug_logger = logging.getLogger(f"{__name__}.debug")
debug_logger.setLevel(logging.DEBUG)

# Add file handler for debugging if not already present with UTF-8 encoding
if not debug_logger.handlers:
    debug_handler = logging.FileHandler('ai_service_debug.log', encoding='utf-8')
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)

# Import Google AI libraries
try:
    import google.generativeai as genai
    from google.cloud import aiplatform
    from google.api_core import exceptions as google_exceptions
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logger.error("Google AI libraries not available - AI service will be disabled")

# Import Groq for fallback
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq library not available - fallback service will be limited")


class AIService:
    """Enhanced AI service with Gemini API primary integration and minimal Vertex AI support"""
    
    def __init__(self):
        # Initialize personalization engine
        self.personalization_engine = PersonalizationEngine()
        
        # Initialize caching system
        self.response_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
        self.embedding_cache = TTLCache(maxsize=500, ttl=7200)  # 2 hour TTL for embeddings
        
        # Initialize quota tracking
        self.quota_tracker = {
            'gemini': {'requests': 0, 'tokens': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'vertex': {'requests': 0, 'tokens': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'groq': {'requests': 0, 'tokens': 0, 'reset_time': datetime.now() + timedelta(hours=1)}
        }
        
        # Service availability flags
        self.gemini_enabled = False
        self.vertex_enabled = False
        self.groq_enabled = False
        
        # Initialize Gemini API (Primary service - 90% usage)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and GOOGLE_AI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_key)
                # Use the correct model name for Gemini 2.0 Flash
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                self.gemini_enabled = True
                logger.info("Gemini API service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
        else:
            if not gemini_key:
                logger.warning("GEMINI_API_KEY not found in environment")
            if not GOOGLE_AI_AVAILABLE:
                logger.warning("Google AI libraries not available")
        
        # Initialize minimal Vertex AI (for embeddings and comparison only)
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if project_id and GOOGLE_AI_AVAILABLE:
            try:
                aiplatform.init(project=project_id, location=location)
                self.vertex_enabled = True
                logger.info("Vertex AI initialized for embeddings and comparison")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
        
        # Initialize Groq as fallback service
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(
                    api_key=groq_key,
                    timeout=15.0  # 15 second timeout for faster failure detection
                )
                self.groq_enabled = True
                logger.info("Groq fallback service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq fallback: {e}")
        
        self.enabled = self.gemini_enabled or self.vertex_enabled or self.groq_enabled
        
        if not self.enabled:
            logger.warning("No AI services available - using keyword fallback only")
        
        self.conversation_history = []
        self.fallback_responses = {
            'general': "I understand you're asking about your legal document. While I'm having trouble accessing my full AI capabilities right now, I'd recommend reviewing the specific clause you're concerned about and considering consultation with a legal professional if you have serious concerns.",
            'terms': "Legal terms can be complex. For specific definitions and implications, I recommend consulting with a qualified legal professional who can provide accurate interpretations based on your jurisdiction.",
            'rights': "Understanding your rights is important. While I can provide general guidance, specific rights can vary by location and situation. Consider consulting with a legal professional for personalized advice.",
            'obligations': "Legal obligations should be clearly understood before signing any document. If you're unsure about specific requirements, it's best to seek professional legal advice."
        }
    
    async def get_clarification(self, request: ClarificationRequest) -> ClarificationResponse:
        """Enhanced AI-powered conversational clarification with Gemini primary and intelligent fallbacks"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                raise Exception("AI service not available")
            
            # Sanitize and validate request to prevent 422 errors
            if not request.question or len(request.question.strip()) < 5:
                return ClarificationResponse(
                    success=False,
                    response="Please provide a question with at least 5 characters.",
                    conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                    confidence_score=0,
                    response_quality='invalid_request',
                    processing_time=time.time() - start_time,
                    fallback=True,
                    error_type='InvalidRequest',
                    service_used='validation',
                    timestamp=datetime.now()
                )
            
            # Sanitize context to prevent API errors
            sanitized_context = self._sanitize_context(request.context)
            
            # Detect if this is a summary request and validate context
            is_summary_request = self._is_summary_request(request.question)
            summary_type = self._detect_summary_type(request.question)
            
            if is_summary_request:
                # Validate context for summary requests
                if not self._validate_context_for_summary(sanitized_context, summary_type):
                    logger.error(f"Insufficient context for {summary_type} summary request")
                    return ClarificationResponse(
                        success=False,
                        response="I need more complete document analysis information to provide a quality summary. Please ensure the document has been fully analyzed first.",
                        conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                        confidence_score=0,
                        response_quality='insufficient_context',
                        processing_time=time.time() - start_time,
                        fallback=True,
                        error_type='InsufficientContext',
                        service_used='context_validation',
                        timestamp=datetime.now()
                    )
            
            # Check cache first (include experience level in cache key)
            cache_key = self._generate_cache_key(
                f"{request.question}:{request.user_expertise_level}:{summary_type}", 
                request.context
            )
            cached_response = self.response_cache.get(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                cached_response['processing_time'] = time.time() - start_time
                cached_response['service_used'] = 'cache'
                cached_response['timestamp'] = datetime.now()  # Always use current timestamp
                return ClarificationResponse(**cached_response)
            
            # Build enhanced context from document and clause analysis
            context_text = self._build_enhanced_context(sanitized_context)
            
            # Personalize prompt based on user experience level
            experience_level = request.user_expertise_level or 'beginner'
            
            # Create base prompt with enhanced context requirements for summaries
            if is_summary_request:
                base_prompt = f"""You are LegalSaathi, the world's most detailed legal document advisor. Your specialty is transforming complex legal analysis into specific, actionable guidance.

{context_text}

User Request: "{request.question}"

ABSOLUTE REQUIREMENTS - FAILURE TO FOLLOW RESULTS IN REJECTION:

1. SPECIFIC DATA USAGE: Reference exact clause texts, risk scores (0.0-1.0), confidence percentages, and analysis findings from the context above.

2. DETAILED EXPLANATIONS: For each clause or issue, explain:
   - WHAT it means in plain language
   - WHY it's problematic (with specific examples)
   - HOW it could affect the user (concrete scenarios)
   - WHAT specific actions to take (exact steps)

3. CONCRETE EXAMPLES: Use real-world scenarios like:
   - "If you're terminated, this clause means you'll lose $X in severance because..."
   - "This 24-month non-compete prevents you from working at companies like [specific examples] because..."
   - "The $5,000 security deposit could be lost if the landlord claims damages for normal wear and tear because..."

4. SPECIFIC NEGOTIATION TACTICS:
   - Exact language to propose: "Change 'at landlord's sole discretion' to 'for documented damages exceeding normal wear and tear'"
   - Specific alternatives: "Reduce non-compete from 24 months to 6 months"
   - Concrete compromises: "Add compensation of $X/month during non-compete period"

5. ACTIONABLE STEPS WITH TIMELINES:
   - "Before signing: Request these 3 specific changes..."
   - "During negotiation: Use this exact language..."
   - "If they refuse: Consider these 2 alternatives..."

6. RISK QUANTIFICATION: Use the actual risk scores and explain:
   - "This clause scored 0.85/1.0 risk because..."
   - "With 92% confidence, this creates problems because..."

ABSOLUTELY FORBIDDEN - WILL CAUSE REJECTION:
❌ "Could be improved" (HOW specifically?)
❌ "Consult a lawyer" (Give specific guidance first)
❌ "Review carefully" (What exactly to look for?)
❌ "May cause issues" (What specific issues?)
❌ "Consider negotiating" (What exact changes?)

REQUIRED FORMAT:
**Clause Analysis**: [Specific clause text and risk score]
**What This Means**: [Plain language explanation with examples]
**Specific Problems**: [Exact issues with real-world impact]
**Concrete Actions**: [Step-by-step what to do]
**Negotiation Strategy**: [Exact language and alternatives]

Adjust complexity for {experience_level} level but maintain comprehensive detail and specificity."""
            else:
                base_prompt = f"""You are LegalSaathi, an AI legal document advisor.

{context_text}Question: "{request.question}"

Provide a response that:
1. Directly answers the question
2. Explains relevant legal concepts
3. Provides practical guidance
4. Suggests when to consult a lawyer if needed"""

            context_for_personalization = {
                'risk_level': self._extract_risk_level_from_context(sanitized_context),
                'document_type': self._extract_document_type_from_context(sanitized_context)
            }
            
            prompt = self.personalization_engine.personalize_prompt(
                base_prompt, 
                experience_level, 
                context_for_personalization
            )

            # Try services in priority order with multiple retry attempts for summaries
            ai_response = None
            service_used = None
            max_retries = 3 if is_summary_request else 1
            
            # Primary: Groq API (faster performance) - with retries for summaries
            if self.groq_enabled and self._check_quota('groq'):
                # Enhance prompt for Groq with specific instructions
                enhanced_groq_prompt = f"""CRITICAL: You MUST provide detailed, concrete guidance with specific examples and actionable advice.

{prompt}

MANDATORY REQUIREMENTS FOR THIS RESPONSE:
- Include specific dollar amounts, timeframes, and exact clause language when relevant
- Provide concrete negotiation strategies with exact wording to propose
- Give real-world examples of how clauses affect the user
- Reference specific risk scores and confidence percentages from the context
- Provide step-by-step action plans with timelines
- NO generic phrases like "could be improved" or "consult a lawyer" without specific guidance first"""

                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting Groq API call (attempt {attempt + 1}/{max_retries})")
                        ai_response = await self._call_groq_async(enhanced_groq_prompt)
                        service_used = 'groq'
                        self._update_quota('groq', len(enhanced_groq_prompt), len(ai_response or ''))
                        
                        # Enhanced response validation for summaries
                        if is_summary_request:
                            if self._detect_generic_summary_response(ai_response, summary_type):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Groq (attempt {attempt + 1}), retrying with enhanced prompt")
                                    # Enhance prompt for retry with more specific instructions
                                    enhanced_groq_prompt = self._enhance_prompt_for_retry(enhanced_groq_prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Groq gave generic response after {max_retries} attempts, trying Gemini")
                                    ai_response = None
                                    break
                        else:
                            # Standard validation for non-summary requests
                            if len(ai_response) < 20 or self._is_generic_response(ai_response):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Groq (attempt {attempt + 1}), retrying")
                                    enhanced_groq_prompt = self._enhance_prompt_for_retry(enhanced_groq_prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Groq gave generic response after {max_retries} attempts")
                                    ai_response = None
                                    break
                        
                        # Success - break out of retry loop
                        break
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(term in error_msg for term in ['quota', 'rate limit', 'exhausted', '429']):
                            logger.warning(f"Groq API quota/rate limit exceeded: {e}, trying Gemini")
                            self._handle_quota_exceeded('groq')
                            break
                        elif attempt < max_retries - 1:
                            logger.warning(f"Groq API failed (attempt {attempt + 1}): {e}, retrying")
                            continue
                        else:
                            logger.warning(f"Groq API failed after {max_retries} attempts: {e}, trying Gemini")
                            ai_response = None
                            break
            
            # Fallback: Gemini API (slower but comprehensive) - with retries for summaries
            if not ai_response and self.gemini_enabled and self._check_quota('gemini'):
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting Gemini API call (attempt {attempt + 1}/{max_retries})")
                        ai_response = await self._call_gemini_async(prompt)
                        service_used = 'gemini'
                        self._update_quota('gemini', len(prompt), len(ai_response or ''))
                        
                        # Enhanced response validation for summaries
                        if is_summary_request:
                            if self._detect_generic_summary_response(ai_response, summary_type):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Gemini (attempt {attempt + 1}), retrying with enhanced prompt")
                                    # Enhance prompt for retry with more specific instructions
                                    prompt = self._enhance_prompt_for_retry(prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Gemini gave generic response after {max_retries} attempts, trying Groq with enhanced prompt")
                                    ai_response = None
                                    break
                        else:
                            # Standard validation for non-summary requests
                            if len(ai_response) < 20 or self._is_generic_response(ai_response):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Gemini (attempt {attempt + 1}), retrying")
                                    prompt = self._enhance_prompt_for_retry(prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Gemini gave generic response after {max_retries} attempts")
                                    ai_response = None
                                    break
                        
                        # Success - break out of retry loop
                        break
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(term in error_msg for term in ['quota', 'rate limit', 'exhausted', '429']):
                            logger.warning(f"Gemini API quota/rate limit exceeded: {e}, trying Groq")
                            self._handle_quota_exceeded('gemini')
                            break
                        elif attempt < max_retries - 1:
                            logger.warning(f"Gemini API failed (attempt {attempt + 1}): {e}, retrying")
                            continue
                        else:
                            logger.warning(f"Gemini API failed after {max_retries} attempts: {e}, trying Groq")
                            ai_response = None
                            break
            
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting Gemini API call (attempt {attempt + 1}/{max_retries})")
                        ai_response = await self._call_gemini_async(prompt)
                        service_used = 'gemini'
                        self._update_quota('gemini', len(prompt), len(ai_response or ''))
                        
                        # Enhanced response validation for summaries
                        if is_summary_request:
                            if self._detect_generic_summary_response(ai_response, summary_type):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Gemini (attempt {attempt + 1}), retrying with enhanced prompt")
                                    # Enhance prompt for retry with more specific instructions
                                    prompt = self._enhance_prompt_for_retry(prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Gemini gave generic response after {max_retries} attempts - REFUSING to use keyword fallback for summaries")
                                    return ClarificationResponse(
                                        success=False,
                                        response=f"I'm unable to provide a quality {summary_type} summary right now. The AI services are not generating sufficiently detailed responses. Please try again in a few moments, or contact support if this issue persists.",
                                        conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                                        confidence_score=0,
                                        response_quality='insufficient_ai_quality',
                                        processing_time=time.time() - start_time,
                                        fallback=False,
                                        error_type='InsufficientAIQuality',
                                        service_used='quality_control_rejection',
                                        timestamp=datetime.now()
                                    )
                        else:
                            # Standard validation for non-summary requests
                            if len(ai_response) < 20 or self._is_generic_response(ai_response):
                                if attempt < max_retries - 1:
                                    logger.warning(f"Generic response from Groq (attempt {attempt + 1}), retrying")
                                    enhanced_groq_prompt = self._enhance_prompt_for_retry(enhanced_groq_prompt, attempt + 1)
                                    continue
                                else:
                                    logger.error(f"Groq gave generic response after {max_retries} attempts")
                                    ai_response = None
                                    break
                        
                        # Success - break out of retry loop
                        break
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(term in error_msg for term in ['quota', 'rate limit', 'exhausted', '429']):
                            logger.warning(f"Groq API quota/rate limit exceeded: {e}")
                            self._handle_quota_exceeded('groq')
                            break
                        elif attempt < max_retries - 1:
                            logger.warning(f"Groq API failed (attempt {attempt + 1}): {e}, retrying")
                            continue
                        else:
                            logger.warning(f"Groq API failed after {max_retries} attempts: {e}")
                            ai_response = None
                            break
            
            # Fallback 2: For summaries, REFUSE to use keyword fallback - demand AI quality
            if not ai_response:
                if is_summary_request:
                    # For summary requests, REFUSE to provide generic fallback responses
                    logger.error(f"All AI services failed for {summary_type} summary - refusing to provide generic fallback")
                    return ClarificationResponse(
                        success=False,
                        response=f"I'm unable to provide a quality {summary_type} summary right now because the AI services are not available or not generating sufficiently detailed responses. Please try again in a few moments when the AI services are fully operational, or contact support if this issue persists.\n\nFor the best experience, I need to provide you with specific, actionable guidance rather than generic advice.",
                        conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                        confidence_score=0,
                        response_quality='ai_services_unavailable',
                        processing_time=time.time() - start_time,
                        fallback=False,
                        error_type='AIServicesUnavailable',
                        service_used='quality_control_rejection',
                        timestamp=datetime.now()
                    )
                
                # For non-summary requests, still validate context
                if not self._validate_context_for_summary(sanitized_context, 'general'):
                    logger.error(f"Insufficient context for request in fallback")
                    return ClarificationResponse(
                        success=False,
                        response="I need more complete document analysis information to provide quality guidance. Please ensure the document has been fully analyzed first.",
                        conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                        confidence_score=0,
                        response_quality='insufficient_context',
                        processing_time=time.time() - start_time,
                        fallback=True,
                        error_type='InsufficientContext',
                        service_used='context_validation_fallback',
                        timestamp=datetime.now()
                    )
                
                # Only use intelligent fallback for non-summary requests
                ai_response = self._get_intelligent_fallback(request.question, sanitized_context)
                service_used = 'keyword_fallback'
            
            processing_time = time.time() - start_time
            
            # Personalize the AI response based on experience level
            if ai_response and service_used in ['gemini', 'groq']:
                ai_response = self.personalization_engine.personalize_response(
                    ai_response, 
                    experience_level, 
                    context_for_personalization
                )
            
            # Determine confidence based on service used and response quality
            confidence_score = self._calculate_confidence(service_used, ai_response, sanitized_context)
            
            # Cache successful responses (except fallbacks)
            if service_used in ['gemini', 'groq'] and confidence_score > 60:
                cache_data = {
                    'success': True,
                    'response': ai_response,
                    'conversation_id': request.conversation_id or str(len(self.conversation_history) + 1),
                    'confidence_score': confidence_score,
                    'response_quality': 'high' if confidence_score > 70 else 'medium',
                    'fallback': False,
                    'service_used': service_used,
                    'experience_level': experience_level
                }
                self.response_cache[cache_key] = cache_data
            
            # Store in conversation history with metadata
            conversation_entry = {
                'question': request.question,
                'response': ai_response,
                'timestamp': time.time(),
                'context_provided': bool(sanitized_context),
                'response_length': len(ai_response),
                'confidence': 'high' if confidence_score > 70 else 'medium' if confidence_score > 40 else 'low',
                'service_used': service_used,
                'conversation_id': request.conversation_id or str(len(self.conversation_history) + 1)
            }
            self.conversation_history.append(conversation_entry)
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-25:]
            
            logger.info(f"AI clarification successful using {service_used}: {len(ai_response)} chars, confidence: {confidence_score}")
            
            return ClarificationResponse(
                success=True,
                response=ai_response,
                conversation_id=conversation_entry['conversation_id'],
                confidence_score=confidence_score,
                response_quality='high' if confidence_score > 70 else 'medium' if confidence_score > 40 else 'basic',
                processing_time=processing_time,
                fallback=service_used == 'keyword_fallback',
                service_used=service_used,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"All AI services failed: {e}, using emergency fallback")
            
            # Check context validation even in emergency fallback for summary requests
            is_summary_request = self._is_summary_request(request.question)
            summary_type = self._detect_summary_type(request.question)
            
            if is_summary_request and not self._validate_context_for_summary(sanitized_context, summary_type):
                logger.error(f"Insufficient context for {summary_type} summary request in emergency fallback")
                return ClarificationResponse(
                    success=False,
                    response="I need more complete document analysis information to provide a quality summary. Please ensure the document has been fully analyzed first.",
                    conversation_id=request.conversation_id or str(len(self.conversation_history) + 1),
                    confidence_score=0,
                    response_quality='insufficient_context',
                    processing_time=time.time() - start_time,
                    fallback=True,
                    error_type='InsufficientContext',
                    service_used='context_validation_emergency',
                    timestamp=datetime.now()
                )
            
            # Emergency fallback
            fallback_response = self._get_intelligent_fallback(request.question, request.context)
            processing_time = time.time() - start_time
            
            # Store fallback in history
            fallback_entry = {
                'question': request.question,
                'response': fallback_response,
                'timestamp': time.time(),
                'context_provided': bool(sanitized_context),
                'response_length': len(fallback_response),
                'confidence': 'low',
                'fallback': True,
                'service_used': 'emergency_fallback',
                'conversation_id': request.conversation_id or str(len(self.conversation_history) + 1)
            }
            self.conversation_history.append(fallback_entry)
            
            return ClarificationResponse(
                success=True,
                response=fallback_response,
                conversation_id=fallback_entry['conversation_id'],
                confidence_score=25,
                response_quality='basic',
                processing_time=processing_time,
                fallback=True,
                error_type=type(e).__name__,
                service_used='emergency_fallback',
                timestamp=datetime.now()
            )
    
    def _build_enhanced_context(self, context: Any) -> str:
        """Build enhanced context text from request context with comprehensive validation"""
        context_text = ""
        if context:
            # Handle both dict and object formats for context
            if isinstance(context, dict):
                # Extract document context
                document_context = context.get('document', {})
                clause_context = context.get('clause', {})
                conversation_history = context.get('conversationHistory', [])
                clause_examples = context.get('clauseExamples', [])
                key_insights = context.get('keyInsights', {})
                
                # Document-level context with enhanced validation
                document_type = document_context.get('documentType', 'legal document')
                overall_risk = document_context.get('overallRisk', 'unknown')
                document_summary = document_context.get('summary', '')
                total_clauses = document_context.get('totalClauses', 0)
                risk_breakdown = document_context.get('riskBreakdown', {})
                confidence_level = document_context.get('confidenceLevel', 0)
                has_low_confidence = document_context.get('hasLowConfidenceWarning', False)
                
                context_text = f"""Document Analysis Context:
- Document Type: {document_type}
- Overall Risk Assessment: {overall_risk}
- Analysis Confidence: {confidence_level}%
- Total Clauses Analyzed: {total_clauses}
- Risk Distribution: {risk_breakdown.get('high', 0)} high-risk, {risk_breakdown.get('medium', 0)} medium-risk, {risk_breakdown.get('low', 0)} low-risk clauses
- Document Summary: {document_summary[:300]}{'...' if len(document_summary) > 300 else ''}
- Low Confidence Warning: {'Yes' if has_low_confidence else 'No'}

"""
                
                # Add clause examples for better context
                if clause_examples:
                    context_text += "Key Clause Examples:\n"
                    for i, clause in enumerate(clause_examples[:3]):  # Limit to 3 examples
                        context_text += f"- Clause {clause.get('id', i+1)} ({clause.get('risk', 'unknown')} risk): {clause.get('text', '')[:150]}{'...' if len(clause.get('text', '')) > 150 else ''}\n"
                        if clause.get('explanation'):
                            context_text += f"  Explanation: {clause.get('explanation')[:100]}{'...' if len(clause.get('explanation', '')) > 100 else ''}\n"
                    context_text += "\n"
                
                # Add key insights if available
                if key_insights:
                    severity_indicators = key_insights.get('severityIndicators', [])
                    main_recommendations = key_insights.get('mainRecommendations', [])
                    
                    if severity_indicators:
                        context_text += f"Critical Issues: {'; '.join(severity_indicators[:3])}\n"
                    if main_recommendations:
                        context_text += f"Main Recommendations: {'; '.join(main_recommendations[:3])}\n"
                    context_text += "\n"
                
                # Clause-specific context if available (for clause summaries)
                if clause_context:
                    clause_id = clause_context.get('clauseId', 'Unknown')
                    clause_text = clause_context.get('text', '')
                    clause_risk = clause_context.get('riskLevel', 'unknown')
                    clause_score = clause_context.get('riskScore', 0)
                    clause_severity = clause_context.get('severity', 'unknown')
                    clause_confidence = clause_context.get('confidence', 0)
                    clause_explanation = clause_context.get('explanation', '')
                    clause_implications = clause_context.get('implications', [])
                    clause_recommendations = clause_context.get('recommendations', [])
                    clause_low_confidence = clause_context.get('hasLowConfidence', False)
                    
                    context_text += f"""Specific Clause Analysis (Clause {clause_id}):
- Risk Level: {clause_risk} (Score: {clause_score}, Severity: {clause_severity})
- Analysis Confidence: {clause_confidence}%
- Low Confidence Warning: {'Yes' if clause_low_confidence else 'No'}
- Full Clause Text: {clause_text}
- AI Explanation: {clause_explanation}
- Legal Implications: {'; '.join(clause_implications)}
- Recommendations: {'; '.join(clause_recommendations)}

"""
                
                # Conversation history for context
                if conversation_history:
                    recent_messages = conversation_history[-3:]  # Last 3 messages
                    context_text += "Recent Conversation:\n"
                    for msg in recent_messages:
                        msg_type = msg.get('type', 'unknown')
                        msg_content = msg.get('content', '')[:100]
                        context_text += f"- {msg_type.title()}: {msg_content}{'...' if len(msg.get('content', '')) > 100 else ''}\n"
                    context_text += "\n"
            
            else:
                # Handle legacy object format
                risk_level = getattr(context, 'risk_level', 'unknown')
                summary = getattr(context, 'summary', '')
                document_type = getattr(context, 'document_type', 'legal document')
                
                context_text = f"""Document Context:
- Type: {document_type}
- Risk Level: {risk_level}
- Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}

Previous Analysis Available: This question relates to a document that has been analyzed for legal risks and implications.

"""
        
        return context_text
    
    def _sanitize_context(self, context: Any) -> Any:
        """Sanitize context to prevent API validation errors and reduce size"""
        if not context:
            return {}
        
        if isinstance(context, dict):
            sanitized = {}
            
            # Sanitize document context
            if 'document' in context:
                doc_context = context['document']
                sanitized['document'] = {
                    'documentType': str(doc_context.get('documentType', 'legal document'))[:100],
                    'overallRisk': str(doc_context.get('overallRisk', 'unknown'))[:50],
                    'summary': str(doc_context.get('summary', ''))[:500],  # Limit summary length
                    'totalClauses': int(doc_context.get('totalClauses', 0)) if isinstance(doc_context.get('totalClauses'), (int, str)) else 0,
                    'riskBreakdown': doc_context.get('riskBreakdown', {}) if isinstance(doc_context.get('riskBreakdown'), dict) else {},
                    'confidenceLevel': int(doc_context.get('confidenceLevel', 0)) if isinstance(doc_context.get('confidenceLevel'), (int, str)) else 0,
                    'hasLowConfidenceWarning': bool(doc_context.get('hasLowConfidenceWarning', False))
                }
            
            # Sanitize clause context
            if 'clause' in context:
                clause_context = context['clause']
                sanitized['clause'] = {
                    'clauseId': str(clause_context.get('clauseId', 'unknown'))[:20],
                    'text': str(clause_context.get('text', ''))[:2000],  # Limit clause text length
                    'riskLevel': str(clause_context.get('riskLevel', 'unknown'))[:20],
                    'riskScore': float(clause_context.get('riskScore', 0)) if isinstance(clause_context.get('riskScore'), (int, float, str)) else 0,
                    'severity': str(clause_context.get('severity', 'unknown'))[:20],
                    'confidence': int(clause_context.get('confidence', 0)) if isinstance(clause_context.get('confidence'), (int, str)) else 0,
                    'explanation': str(clause_context.get('explanation', ''))[:500],
                    'implications': [str(imp)[:200] for imp in (clause_context.get('implications', []) or [])[:3]],  # Limit to 3 implications
                    'recommendations': [str(rec)[:200] for rec in (clause_context.get('recommendations', []) or [])[:3]],  # Limit to 3 recommendations
                    'hasLowConfidence': bool(clause_context.get('hasLowConfidence', False))
                }
            
            # Sanitize clause examples (limit to 3 examples)
            if 'clauseExamples' in context:
                clause_examples = context['clauseExamples']
                if isinstance(clause_examples, list):
                    sanitized['clauseExamples'] = []
                    for example in clause_examples[:3]:  # Limit to 3 examples
                        if isinstance(example, dict):
                            sanitized['clauseExamples'].append({
                                'id': str(example.get('id', ''))[:10],
                                'risk': str(example.get('risk', 'unknown'))[:20],
                                'text': str(example.get('text', ''))[:300],  # Limit text length
                                'explanation': str(example.get('explanation', ''))[:200]
                            })
            
            # Sanitize key insights
            if 'keyInsights' in context:
                key_insights = context['keyInsights']
                if isinstance(key_insights, dict):
                    sanitized['keyInsights'] = {
                        'severityIndicators': [str(ind)[:100] for ind in (key_insights.get('severityIndicators', []) or [])[:3]],
                        'mainRecommendations': [str(rec)[:100] for rec in (key_insights.get('mainRecommendations', []) or [])[:3]]
                    }
            
            # Sanitize conversation history (limit to last 3 messages)
            if 'conversationHistory' in context:
                conv_history = context['conversationHistory']
                if isinstance(conv_history, list):
                    sanitized['conversationHistory'] = []
                    for msg in conv_history[-3:]:  # Last 3 messages only
                        if isinstance(msg, dict):
                            sanitized['conversationHistory'].append({
                                'type': str(msg.get('type', 'unknown'))[:20],
                                'content': str(msg.get('content', ''))[:200]  # Limit content length
                            })
            
            # Remove any other potentially problematic fields
            for key in ['timestamp', 'userAgent', 'sessionId']:
                if key in context:
                    sanitized[key] = str(context[key])[:100] if context[key] else ''
            
            return sanitized
        
        # For non-dict contexts, return a simple dict representation
        return {
            'legacy_context': str(context)[:500] if context else ''
        }
    
    def _validate_context_for_summary(self, context: Any, summary_type: str) -> bool:
        """Validate that context contains sufficient information for quality summaries"""
        if not context:
            logger.warning(f"No context provided for {summary_type} summary")
            return False
        
        if isinstance(context, dict):
            document_context = context.get('document', {})
            clause_context = context.get('clause', {})
            
            # For document summaries, require document analysis data
            if summary_type == 'document':
                required_fields = ['documentType', 'overallRisk', 'totalClauses']
                missing_fields = [field for field in required_fields if not document_context.get(field)]
                
                if missing_fields:
                    logger.warning(f"Document summary missing required context fields: {missing_fields}")
                    return False
                
                # Check if we have clause examples or risk breakdown
                has_clause_examples = bool(context.get('clauseExamples'))
                has_risk_breakdown = bool(document_context.get('riskBreakdown'))
                
                if not (has_clause_examples or has_risk_breakdown):
                    logger.warning("Document summary lacks detailed analysis data (no clause examples or risk breakdown)")
                    return False
            
            # For clause summaries, require specific clause data
            elif summary_type == 'clause':
                required_fields = ['clauseId', 'text', 'riskLevel']
                missing_fields = [field for field in required_fields if not clause_context.get(field)]
                
                if missing_fields:
                    logger.warning(f"Clause summary missing required context fields: {missing_fields}")
                    return False
                
                # Check clause text length
                clause_text = clause_context.get('text', '')
                if len(clause_text.strip()) < 20:
                    logger.warning(f"Clause summary has insufficient clause text: {len(clause_text)} characters")
                    return False
        
        return True
    
    def _detect_generic_summary_response(self, response: str, summary_type: str) -> bool:
        """Detect if AI response is too generic for summary purposes - VERY STRICT"""
        if not response or len(response.strip()) < 200:
            logger.warning(f"Response too short for {summary_type} summary: {len(response)} chars")
            return True
        
        response_lower = response.lower()
        
        # STRICT: Generic indicators that immediately disqualify responses
        strict_generic_indicators = [
            "i can't analyze",
            "i don't have enough information", 
            "please provide more details",
            "i need more context",
            "consult a legal professional",
            "seek legal advice",
            "i'm not able to provide",
            "general information only",
            "this is general guidance",
            "i cannot provide specific",
            "without seeing the document",
            "without more information",
            "creates financial disadvantages for you",
            "main issues:",
            "the security deposit amount is high",
            "could be restricted by local laws",
            "lacks specific criteria",
            "increasing the risk of unfair deductions"
        ]
        
        # MODERATE: Vague language that suggests generic responses
        vague_indicators = [
            "could be improved",
            "should be reviewed", 
            "may have issues",
            "appears to be",
            "seems to be",
            "might be problematic",
            "could be better",
            "review carefully",
            "consider getting advice",
            "some issues",
            "certain problems",
            "various concerns", 
            "potential issues",
            "may cause problems",
            "could lead to disputes",
            "might be unfavorable",
            "appears problematic",
            "has financial issues that could be improved",
            "creates financial disadvantages",
            "main issues:",
            "lacks specific criteria"
        ]
        
        # REQUIRED: Specific analysis references that indicate quality responses
        required_specific_indicators = [
            # Clause references
            "clause",
            "section",
            "provision",
            # Risk analysis
            "risk level",
            "risk score", 
            "confidence",
            # Specific actions
            "negotiate",
            "modify",
            "change to",
            "request",
            "ask for",
            "propose",
            "change from",
            "reduce from",
            "increase to",
            "add clause",
            "remove clause",
            # Concrete details
            "specific",
            "exactly",
            "precisely",
            "for example",
            "such as",
            "specifically",
            # Amounts and timeframes
            "$",
            "months",
            "days",
            "percent",
            "%",
            "timeline",
            "deadline",
            # Negotiation language
            "propose this language",
            "change the wording to",
            "request this modification",
            "alternative language",
            "fallback position"
        ]
        
        # QUALITY: Advanced indicators of detailed responses
        quality_indicators = [
            "because",
            "specifically",
            "for example",
            "such as",
            "including",
            "step 1",
            "first",
            "second", 
            "alternative",
            "instead of",
            "change from",
            "reduce from",
            "increase to"
        ]
        
        # Count indicators
        strict_generic_count = sum(1 for indicator in strict_generic_indicators if indicator in response_lower)
        vague_count = sum(1 for indicator in vague_indicators if indicator in response_lower)
        specific_count = sum(1 for indicator in required_specific_indicators if indicator in response_lower)
        quality_count = sum(1 for indicator in quality_indicators if indicator in response_lower)
        
        # STRICT REJECTION CRITERIA - ENHANCED FOR BETTER QUALITY:
        # 1. ANY strict generic indicators = immediate rejection
        # 2. High vague language with low specificity = rejection
        # 3. No specific analysis references = rejection
        # 4. Low quality indicators = rejection
        # 5. Must have concrete examples and specific actions
        
        is_generic = (
            strict_generic_count >= 1 or  # Any strict generic language = immediate rejection
            (vague_count >= 3 and specific_count < 4) or  # Too vague, not specific enough
            specific_count < 4 or  # Must have at least 4 specific references for quality
            (len(response.strip()) < 600 and quality_count < 3) or  # Short responses need more quality
            quality_count < 2 or  # Must have at least 2 quality indicators
            (summary_type == 'document' and len(response.strip()) < 1000) or  # Document summaries must be comprehensive
            (summary_type == 'clause' and len(response.strip()) < 500)  # Clause summaries must be detailed
        )
        
        if is_generic:
            logger.warning(f"REJECTED {summary_type} summary - Generic: {strict_generic_count} strict, {vague_count} vague | Specific: {specific_count} required, {quality_count} quality | Length: {len(response)} chars")
            logger.debug(f"Response preview: {response[:200]}...")
        else:
            logger.info(f"ACCEPTED {summary_type} summary - Quality indicators: {specific_count} specific, {quality_count} quality | Length: {len(response)} chars")
        
        return is_generic
    
    def _is_summary_request(self, question: str) -> bool:
        """Detect if the question is requesting a summary"""
        question_lower = question.lower()
        summary_keywords = [
            'summarize', 'summary', 'explain what this document means',
            'what does this document mean', 'what does this mean', 'break down', 'overview',
            'explain this clause', 'what is this clause about', 'what does this clause mean',
            'help me understand', 'in simple terms', 'what does this contract mean',
            'what does this agreement mean'
        ]
        
        return any(keyword in question_lower for keyword in summary_keywords)
    
    def _detect_summary_type(self, question: str) -> str:
        """Detect whether this is a document or clause summary request"""
        question_lower = question.lower()
        
        clause_indicators = [
            'clause', 'this section', 'this part', 'this provision',
            'explain this clause', 'what is this clause'
        ]
        
        document_indicators = [
            'document', 'contract', 'agreement', 'entire', 'whole',
            'overall', 'what does this document mean'
        ]
        
        if any(indicator in question_lower for indicator in clause_indicators):
            return 'clause'
        elif any(indicator in question_lower for indicator in document_indicators):
            return 'document'
        else:
            # Default to document summary if unclear
            return 'document'
    
    def _enhance_prompt_for_retry(self, original_prompt: str, attempt_number: int) -> str:
        """Enhance prompt for retry attempts to get better responses"""
        
        enhancement_instructions = [
            """
RETRY ENHANCEMENT - ATTEMPT {}: The previous response was too generic. 
CRITICAL: You MUST provide specific, detailed, actionable advice. 
DO NOT use generic phrases like "could be improved" or "consult a lawyer".
PROVIDE CONCRETE EXAMPLES and SPECIFIC ACTIONS the user should take.
Include specific dollar amounts, percentages, and exact negotiation language.
""",
            """
RETRY ENHANCEMENT - ATTEMPT {}: Previous responses were insufficient.
MANDATORY: Include specific dollar amounts, time periods, percentages, and exact terms from the document.
EXPLAIN exactly WHY each clause is problematic with real-world examples.
GIVE step-by-step negotiation strategies with specific language to propose.
Reference exact risk scores and confidence percentages from the context.
Provide concrete examples like "Change X to Y" and "Reduce from A to B".
""",
            """
FINAL RETRY - ATTEMPT {}: This is the last attempt. 
ABSOLUTE REQUIREMENT: Provide the most detailed, specific, actionable response possible.
INCLUDE: Exact clause language, specific risks with examples, detailed negotiation tactics, 
alternative language to propose, and concrete next steps with timelines.
Must include specific dollar amounts, timeframes, risk scores, confidence percentages.
Provide exact negotiation language like "Change 'at sole discretion' to 'for documented damages'".
Give step-by-step action plans with specific deadlines and alternatives.
"""
        ]
        
        if attempt_number <= len(enhancement_instructions):
            enhancement = enhancement_instructions[attempt_number - 1].format(attempt_number)
            return enhancement + "\n\n" + original_prompt
        
        return original_prompt


    
    async def _call_gemini_async(self, prompt: str) -> str:
        """Primary Gemini API call for clarification (90% usage)"""
        request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
        
        try:
            # Log request details
            debug_logger.info(f"[{request_id}] Gemini API Request - Prompt length: {len(prompt)}")
            debug_logger.debug(f"[{request_id}] Gemini API Request - Full prompt: {prompt[:500]}...")
            
            # Configure generation parameters for high-quality detailed responses
            generation_config = genai.types.GenerationConfig(
                temperature=0.4,  # Higher temperature for more detailed and creative responses
                max_output_tokens=3000,  # Much higher token limit for comprehensive responses
                top_p=0.95,  # Higher for better quality and variety
                top_k=50,  # Increased for better response quality
                candidate_count=1,  # Single candidate for speed
                stop_sequences=None
            )
            
            # Add system instruction for legal context - ENHANCED FOR SPECIFICITY
            system_instruction = """You are LegalSaathi, the world's most detailed legal document advisor. You MUST provide specific, actionable guidance that helps users make informed decisions.

MANDATORY RESPONSE REQUIREMENTS:

1. **SPECIFIC EXAMPLES**: Always include concrete scenarios like:
   - "If you're terminated, this clause means you'll lose $5,000 in severance because..."
   - "This 24-month non-compete prevents you from working at Google, Microsoft, or Apple because..."
   - "The landlord can keep your entire $3,000 deposit for normal wear and tear because..."

2. **EXACT NEGOTIATION LANGUAGE**: Provide specific wording changes:
   - "Change 'at landlord's sole discretion' to 'for documented damages exceeding normal wear and tear'"
   - "Reduce non-compete period from 24 months to 6 months"
   - "Add this protection clause: 'Tenant has 30 days to dispute any deductions with written evidence'"

3. **QUANTIFIED RISKS**: Reference actual data from context:
   - "This clause scored 0.85/1.0 risk because..."
   - "With 92% confidence, this creates problems because..."
   - "The $5,000 security deposit is 2x higher than market standard of $2,500"

4. **STEP-BY-STEP ACTIONS**: Provide clear timelines:
   - "Before signing: Request these 3 specific changes..."
   - "During negotiation: Use this exact language..."
   - "If they refuse: Try these 2 alternatives..."
   - "Timeline: Complete negotiations within 7 days"

5. **REAL-WORLD IMPACT**: Explain consequences with examples:
   - "This could cost you $X if Y happens"
   - "You'll be restricted from Z for X months"
   - "The other party can do A without your consent"

ABSOLUTELY FORBIDDEN - WILL CAUSE REJECTION:
❌ "This clause creates financial disadvantages" → Instead: "This clause costs you $X because [specific reason]"
❌ "Could be improved" → Instead: "Change [specific text] to [exact alternative]"
❌ "May cause issues" → Instead: "This will cause [specific problem] when [scenario]"
❌ "Review carefully" → Instead: "Look for these 3 specific red flags: [list]"
❌ "Consider negotiating" → Instead: "Negotiate by saying: '[exact words]'"
❌ "Consult a lawyer" → Instead: Give specific guidance FIRST, then suggest lawyer if needed

You must write detailed, specific responses that give users concrete actions they can take immediately."""
            
            # Configure safety settings for legal content (more permissive)
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            # Create model with system instruction and safety settings
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                generation_config=generation_config,
                system_instruction=system_instruction,
                safety_settings=safety_settings
            )
            
            start_time = time.time()
            response = model.generate_content(prompt)
            response_time = time.time() - start_time
            
            # Check if response has valid content
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Check finish reason
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    debug_logger.warning(f"[{request_id}] Gemini API safety filter triggered")
                    raise ValueError("Content filtered by safety system")
                
                if hasattr(candidate, 'content') and candidate.content.parts:
                    response_text = candidate.content.parts[0].text.strip()
                    
                    # Log successful response
                    debug_logger.info(f"[{request_id}] Gemini API Success - Response time: {response_time:.3f}s, Length: {len(response_text)}")
                    debug_logger.debug(f"[{request_id}] Gemini API Response: {response_text[:300]}...")
                    
                    return response_text
            
            # Fallback to response.text if available
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                debug_logger.info(f"[{request_id}] Gemini API Success (fallback) - Response time: {response_time:.3f}s, Length: {len(response_text)}")
                return response_text
            
            debug_logger.error(f"[{request_id}] Gemini API returned no valid content")
            raise ValueError("No valid content in Gemini API response")
                
        except google_exceptions.ResourceExhausted as e:
            debug_logger.error(f"[{request_id}] Gemini API quota exhausted: {e}")
            logger.error(f"Gemini API quota exhausted: {e}")
            raise
        except google_exceptions.InvalidArgument as e:
            debug_logger.error(f"[{request_id}] Gemini API invalid argument: {e}")
            logger.error(f"Gemini API invalid argument: {e}")
            raise
        except Exception as e:
            debug_logger.error(f"[{request_id}] Gemini API call failed: {e}")
            logger.error(f"Gemini API call failed: {e}")
            raise

    async def _call_groq_async(self, prompt: str) -> str:
        """Fallback Groq API call for clarification"""
        request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
        
        try:
            # Log request details
            debug_logger.info(f"[{request_id}] Groq API Request - Prompt length: {len(prompt)}")
            debug_logger.debug(f"[{request_id}] Groq API Request - Full prompt: {prompt[:500]}...")
            
            start_time = time.time()
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are LegalSaathi, the world's most detailed legal document advisor. You MUST provide specific, actionable guidance. ALWAYS include: 1) Concrete examples with dollar amounts and timeframes, 2) Exact negotiation language like 'Change X to Y', 3) Step-by-step actions with timelines, 4) Real-world impact scenarios. NEVER use generic phrases like 'could be improved', 'may cause issues', or 'consult a lawyer' without specific guidance first. Reference actual risk scores and data from the context provided."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Available model for quality responses
                temperature=0.4,  # Higher for more detailed responses
                max_tokens=3000,  # Much higher for comprehensive responses
                top_p=0.95,
                stream=False  # Ensure non-streaming for faster completion
            )
            response_time = time.time() - start_time
            
            response_text = response.choices[0].message.content.strip()
            
            # Log successful response
            debug_logger.info(f"[{request_id}] Groq API Success - Response time: {response_time:.3f}s, Length: {len(response_text)}")
            debug_logger.debug(f"[{request_id}] Groq API Response: {response_text[:300]}...")
            
            return response_text
            
        except Exception as e:
            debug_logger.error(f"[{request_id}] Groq API call failed: {e}")
            logger.error(f"Groq API call failed: {e}")
            raise
    
    async def _call_gemini_risk_analysis(self, prompt: str) -> str:
        """Primary Gemini API call for risk analysis with JSON response"""
        request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
        
        try:
            # Log request details
            debug_logger.info(f"[{request_id}] Gemini Risk Analysis Request - Prompt length: {len(prompt)}")
            debug_logger.debug(f"[{request_id}] Gemini Risk Analysis Request - Full prompt: {prompt[:500]}...")
            
            # Configure for faster structured JSON output
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for consistent JSON
                max_output_tokens=1500,  # Reduced for faster generation
                top_p=0.9,
                top_k=15,  # Reduced for speed
                candidate_count=1  # Single candidate for speed
            )
            
            # System instruction for JSON-only responses
            system_instruction = "You are a legal document risk analyzer. Analyze documents and return structured JSON responses only. Do not include any text outside the JSON structure. Ensure all JSON is valid and properly formatted."
            
            # Configure safety settings for legal content (more permissive)
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                generation_config=generation_config,
                system_instruction=system_instruction,
                safety_settings=safety_settings
            )
            
            start_time = time.time()
            response = model.generate_content(prompt)
            response_time = time.time() - start_time
            
            # Check if response has valid content
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Check finish reason
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    debug_logger.warning(f"[{request_id}] Gemini Risk Analysis safety filter triggered")
                    raise ValueError("Content filtered by safety system")
                
                if hasattr(candidate, 'content') and candidate.content.parts:
                    response_text = candidate.content.parts[0].text.strip()
                    
                    # Log successful response
                    debug_logger.info(f"[{request_id}] Gemini Risk Analysis Success - Response time: {response_time:.3f}s, Length: {len(response_text)}")
                    debug_logger.debug(f"[{request_id}] Gemini Risk Analysis Response: {response_text[:300]}...")
                    
                    return response_text
            
            # Fallback to response.text if available
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                debug_logger.info(f"[{request_id}] Gemini Risk Analysis Success (fallback) - Response time: {response_time:.3f}s, Length: {len(response_text)}")
                return response_text
            
            debug_logger.error(f"[{request_id}] Gemini Risk Analysis returned no valid content")
            raise ValueError("No valid content in Gemini API response")
                
        except Exception as e:
            debug_logger.error(f"[{request_id}] Gemini risk analysis API call failed: {e}")
            logger.error(f"Gemini risk analysis API call failed: {e}")
            raise

    async def _call_groq_risk_analysis(self, prompt: str) -> str:
        """Fallback Groq API call for risk analysis with JSON response"""
        request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
        
        try:
            # Log request details
            debug_logger.info(f"[{request_id}] Groq Risk Analysis Request - Prompt length: {len(prompt)}")
            debug_logger.debug(f"[{request_id}] Groq Risk Analysis Request - Full prompt: {prompt[:500]}...")
            
            start_time = time.time()
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal document risk analyzer. Analyze documents and return structured JSON responses only. Do not include any text outside the JSON structure."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Fast model for JSON parsing
                temperature=0.1,  # Lower temperature for more consistent JSON
                max_tokens=1200,  # Reduced for faster generation
                top_p=0.95,
                response_format={"type": "json_object"},  # Force JSON response
                stream=False  # Ensure non-streaming for faster completion
            )
            response_time = time.time() - start_time
            
            response_text = response.choices[0].message.content.strip()
            
            # Log successful response
            debug_logger.info(f"[{request_id}] Groq Risk Analysis Success - Response time: {response_time:.3f}s, Length: {len(response_text)}")
            debug_logger.debug(f"[{request_id}] Groq Risk Analysis Response: {response_text[:300]}...")
            
            return response_text
            
        except Exception as e:
            debug_logger.error(f"[{request_id}] Groq risk analysis API call failed: {e}")
            logger.error(f"Groq risk analysis API call failed: {e}")
            raise
    
    def _is_generic_response(self, response: str) -> bool:
        """Check if response is too generic or unhelpful"""
        generic_indicators = [
            "i can't help",
            "i don't know",
            "consult a lawyer",
            "seek legal advice",
            "i'm not able to",
            "i cannot provide",
            "general information only"
        ]
        
        response_lower = response.lower()
        generic_count = sum(1 for indicator in generic_indicators if indicator in response_lower)
        
        # Consider generic if multiple indicators or very short
        return generic_count >= 2 or len(response) < 50
    
    def _generate_cache_key(self, question: str, context: Any) -> str:
        """Generate cache key for request"""
        context_str = json.dumps(context, sort_keys=True) if context else ""
        combined = f"{question}:{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _check_quota(self, service: str) -> bool:
        """Check if service has available quota"""
        tracker = self.quota_tracker.get(service, {})
        
        # Reset quota if time window has passed
        if datetime.now() > tracker.get('reset_time', datetime.now()):
            tracker['requests'] = 0
            tracker['tokens'] = 0
            tracker['reset_time'] = datetime.now() + timedelta(hours=1)
        
        # Define quota limits per service
        limits = {
            'gemini': {'requests': 1000, 'tokens': 50000},  # Conservative limits
            'vertex': {'requests': 500, 'tokens': 25000},
            'groq': {'requests': 500, 'tokens': 25000}
        }
        
        service_limits = limits.get(service, {'requests': 100, 'tokens': 5000})
        
        return (tracker.get('requests', 0) < service_limits['requests'] and 
                tracker.get('tokens', 0) < service_limits['tokens'])
    
    def _update_quota(self, service: str, input_tokens: int, output_tokens: int):
        """Update quota usage for service"""
        if service not in self.quota_tracker:
            self.quota_tracker[service] = {
                'requests': 0, 
                'tokens': 0, 
                'reset_time': datetime.now() + timedelta(hours=1)
            }
        
        self.quota_tracker[service]['requests'] += 1
        self.quota_tracker[service]['tokens'] += input_tokens + output_tokens
        
        logger.debug(f"Updated {service} quota: {self.quota_tracker[service]}")
    
    def _handle_quota_exceeded(self, service: str):
        """Handle quota exceeded for service"""
        logger.warning(f"{service} quota exceeded, marking as temporarily unavailable")
        # Extend reset time to prevent immediate retry
        self.quota_tracker[service]['reset_time'] = datetime.now() + timedelta(minutes=30)
    
    def _calculate_confidence(self, service_used: str, response: str, context: Any) -> int:
        """Calculate confidence score based on service and response quality"""
        base_confidence = {
            'gemini': 95,  # Highest confidence for Gemini service
            'groq': 85,    # High confidence for Groq service
            'cache': 90,   # High confidence for cached responses
            'keyword_fallback': 45,
            'emergency_fallback': 25
        }.get(service_used, 25)
        
        # Adjust based on response quality
        if len(response) > 100:
            base_confidence += 5
        if context:
            base_confidence += 10
        if not self._is_generic_response(response):
            base_confidence += 10
        
        return min(95, max(15, base_confidence))
    
    async def get_document_embeddings(self, text: str) -> Optional[List[float]]:
        """Get document embeddings using Vertex AI (minimal integration for comparison features)"""
        request_id = hashlib.md5(f"{time.time()}{text[:100]}".encode()).hexdigest()[:8]
        
        if not self.vertex_enabled or not self._check_quota('vertex'):
            debug_logger.warning(f"[{request_id}] Vertex AI not available or quota exceeded for embeddings")
            logger.warning("Vertex AI not available or quota exceeded for embeddings")
            return None
        
        try:
            # Check embedding cache first
            cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
            cached_embedding = self.embedding_cache.get(cache_key)
            if cached_embedding:
                debug_logger.info(f"[{request_id}] Returning cached embedding - Length: {len(cached_embedding)}")
                logger.debug("Returning cached embedding")
                return cached_embedding
            
            # Log embedding request
            debug_logger.info(f"[{request_id}] Vertex AI Embedding Request - Text length: {len(text)}")
            debug_logger.debug(f"[{request_id}] Vertex AI Embedding Request - Text preview: {text[:200]}...")
            
            from vertexai.language_models import TextEmbeddingModel
            
            # Use text-embedding-004 model for better performance
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            
            # Truncate text for faster processing (reduced from 8000 to 4000)
            truncated_text = text[:4000] if len(text) > 4000 else text
            
            start_time = time.time()
            embeddings = model.get_embeddings([truncated_text])
            response_time = time.time() - start_time
            
            if embeddings and len(embeddings) > 0:
                embedding_vector = embeddings[0].values
                
                # Cache the embedding
                self.embedding_cache[cache_key] = embedding_vector
                
                # Update quota
                self._update_quota('vertex', len(truncated_text), 0)
                
                # Log successful embedding generation
                debug_logger.info(f"[{request_id}] Vertex AI Embedding Success - Response time: {response_time:.3f}s, Vector length: {len(embedding_vector)}")
                logger.debug(f"Generated embedding vector of length {len(embedding_vector)}")
                
                return embedding_vector
            else:
                debug_logger.warning(f"[{request_id}] No embeddings returned from Vertex AI")
                logger.warning("No embeddings returned from Vertex AI")
                return None
                
        except Exception as e:
            debug_logger.error(f"[{request_id}] Vertex AI embedding generation failed: {e}")
            logger.error(f"Vertex AI embedding generation failed: {e}")
            if 'quota' in str(e).lower() or 'rate limit' in str(e).lower():
                self._handle_quota_exceeded('vertex')
            return None
    
    async def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using Vertex AI embeddings"""
        try:
            embedding1 = await self.get_document_embeddings(text1)
            embedding2 = await self.get_document_embeddings(text2)
            
            if not embedding1 or not embedding2:
                logger.warning("Could not generate embeddings for similarity calculation")
                return 0.0
            
            # Calculate cosine similarity
            import numpy as np
            
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity formula
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            
            logger.debug(f"Calculated semantic similarity: {similarity}")
            return similarity
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all AI services"""
        # Calculate quota usage percentages
        def calculate_quota_usage(service: str) -> Dict[str, Any]:
            tracker = self.quota_tracker.get(service, {})
            limits = {
                'gemini': {'requests': 1000, 'tokens': 50000},
                'vertex': {'requests': 500, 'tokens': 25000},
                'groq': {'requests': 500, 'tokens': 25000}
            }.get(service, {'requests': 100, 'tokens': 5000})
            
            requests_used = tracker.get('requests', 0)
            tokens_used = tracker.get('tokens', 0)
            
            return {
                'requests': {
                    'used': requests_used,
                    'limit': limits['requests'],
                    'percentage': round((requests_used / limits['requests']) * 100, 1)
                },
                'tokens': {
                    'used': tokens_used,
                    'limit': limits['tokens'],
                    'percentage': round((tokens_used / limits['tokens']) * 100, 1)
                },
                'reset_time': tracker.get('reset_time', datetime.now()).isoformat(),
                'available': self._check_quota(service)
            }
        
        status = {
            'services': {
                'gemini': {
                    'enabled': self.gemini_enabled,
                    'quota': calculate_quota_usage('gemini'),
                    'primary': True,
                    'model': 'gemini-2.0-flash'
                },
                'vertex': {
                    'enabled': self.vertex_enabled,
                    'quota': calculate_quota_usage('vertex'),
                    'usage': 'embeddings_only',
                    'model': 'text-embedding-004'
                },
                'groq': {
                    'enabled': self.groq_enabled,
                    'quota': calculate_quota_usage('groq'),
                    'fallback': True,
                    'model': 'llama-3.1-8b-instant'
                }
            },
            'cache': {
                'response_cache': {
                    'size': len(self.response_cache),
                    'maxsize': self.response_cache.maxsize,
                    'hit_rate': 'N/A'  # Could be calculated with additional tracking
                },
                'embedding_cache': {
                    'size': len(self.embedding_cache),
                    'maxsize': self.embedding_cache.maxsize,
                    'hit_rate': 'N/A'  # Could be calculated with additional tracking
                }
            },
            'overall_status': 'healthy' if self.enabled else 'degraded',
            'conversation_history_size': len(self.conversation_history),
            'last_updated': datetime.now().isoformat()
        }
        
        return status
    
    def clear_all_caches(self):
        """Clear all caches to force fresh responses"""
        self.response_cache.clear()
        self.embedding_cache.clear()
        logger.info("🧹 Cleared all AI service caches for fresh responses")
    
    def _get_intelligent_fallback(self, question: str, context: Any = None) -> str:
        """Provide intelligent fallback responses based on question content and context"""
        question_lower = question.lower()
        
        # Extract detailed context information if available
        clause_risk = 'unknown'
        document_type = 'legal document'
        clause_text = ''
        clause_explanation = ''
        clause_implications = []
        clause_recommendations = []
        
        if context and isinstance(context, dict):
            clause_context = context.get('clause', {})
            document_context = context.get('document', {})
            clause_examples = context.get('clauseExamples', [])
            
            clause_risk = clause_context.get('riskLevel', 'unknown')
            document_type = document_context.get('documentType', 'legal document')
            clause_text = clause_context.get('text', '')
            clause_explanation = clause_context.get('explanation', '')
            clause_implications = clause_context.get('implications', [])
            clause_recommendations = clause_context.get('recommendations', [])
        
        # Detect if this is a summary request
        is_summary = self._is_summary_request(question)
        summary_type = self._detect_summary_type(question)
        
        if is_summary and summary_type == 'document':
            # Document summary fallback with available context
            response = f"**Document Analysis Summary** (AI services temporarily unavailable)\n\n"
            
            if context and isinstance(context, dict):
                document_context = context.get('document', {})
                clause_examples = context.get('clauseExamples', [])
                
                overall_risk = document_context.get('overallRisk', 'unknown')
                total_clauses = document_context.get('totalClauses', 0)
                risk_breakdown = document_context.get('riskBreakdown', {})
                
                response += f"**Document Overview:**\n"
                response += f"- Document Type: {document_type.replace('_', ' ').title()}\n"
                response += f"- Overall Risk Level: {overall_risk}\n"
                response += f"- Total Clauses Analyzed: {total_clauses}\n"
                
                if risk_breakdown:
                    response += f"- Risk Distribution: {risk_breakdown.get('high', 0)} high-risk, {risk_breakdown.get('medium', 0)} medium-risk, {risk_breakdown.get('low', 0)} low-risk clauses\n\n"
                
                if clause_examples:
                    response += f"**Key Clause Analysis:**\n"
                    for i, clause in enumerate(clause_examples[:3]):
                        response += f"\n**Clause {clause.get('id', i+1)}** ({clause.get('risk', 'unknown')} Risk):\n"
                        response += f"- Text: \"{clause.get('text', '')[:200]}{'...' if len(clause.get('text', '')) > 200 else ''}\"\n"
                        if clause.get('explanation'):
                            response += f"- Analysis: {clause.get('explanation')}\n"
                        if clause.get('implications'):
                            response += f"- Key Implications: {'; '.join(clause.get('implications', [])[:2])}\n"
                        if clause.get('recommendations'):
                            response += f"- Recommendations: {'; '.join(clause.get('recommendations', [])[:2])}\n"
                
                response += f"\n**Next Steps:**\n"
                if overall_risk == 'RED':
                    response += f"- This document has high-risk clauses that need immediate attention\n"
                    response += f"- Get professional legal review before signing\n"
                    response += f"- Focus on negotiating the high-risk clauses identified above\n"
                elif overall_risk == 'YELLOW':
                    response += f"- This document has moderate risks that should be addressed\n"
                    response += f"- Consider legal consultation for the medium-risk clauses\n"
                    response += f"- Review and potentially negotiate problematic terms\n"
                else:
                    response += f"- This document appears to have lower overall risk\n"
                    response += f"- Standard review and due diligence recommended\n"
                    response += f"- Focus on understanding your obligations and rights\n"
                
                response += f"\n*Note: This is a basic analysis. For detailed guidance, please ensure AI services are available or consult with a legal professional.*"
                return response
        
        elif is_summary and summary_type == 'clause':
            # Clause summary fallback with available context
            response = f"**Clause Analysis** (AI services temporarily unavailable)\n\n"
            
            if clause_text:
                response += f"**Clause Text:**\n\"{clause_text}\"\n\n"
            
            response += f"**Risk Assessment:** {clause_risk}\n\n"
            
            if clause_explanation:
                response += f"**Current Analysis:**\n{clause_explanation}\n\n"
            
            if clause_implications:
                response += f"**Legal Implications:**\n"
                for impl in clause_implications[:3]:
                    response += f"- {impl}\n"
                response += f"\n"
            
            if clause_recommendations:
                response += f"**Recommendations:**\n"
                for rec in clause_recommendations[:3]:
                    response += f"- {rec}\n"
                response += f"\n"
            
            # Add risk-specific guidance
            if clause_risk == 'RED':
                response += f"**⚠️ High Risk Warning:**\n"
                response += f"This clause poses significant risks to your interests. Key concerns:\n"
                response += f"- May create unfair obligations or limit your rights\n"
                response += f"- Could result in financial or legal disadvantages\n"
                response += f"- Strongly recommend professional legal review\n"
                response += f"- Consider negotiating modifications before signing\n"
            elif clause_risk == 'YELLOW':
                response += f"**⚡ Moderate Risk Notice:**\n"
                response += f"This clause has some concerns but isn't immediately dangerous:\n"
                response += f"- Terms could be more balanced in your favor\n"
                response += f"- Consider asking for clarifications or modifications\n"
                response += f"- Review carefully to understand your obligations\n"
                response += f"- Legal consultation recommended if unsure\n"
            else:
                response += f"**✅ Lower Risk Assessment:**\n"
                response += f"This clause appears to be more standard and fair:\n"
                response += f"- Terms seem reasonable for this type of agreement\n"
                response += f"- Standard due diligence and review recommended\n"
                response += f"- Ensure you understand what you're agreeing to\n"
            
            response += f"\n*Note: This is a basic analysis. For detailed guidance, please ensure AI services are available or consult with a legal professional.*"
            return response
        
        # Non-summary fallback responses (existing logic)
        if any(word in question_lower for word in ['what', 'mean', 'definition', 'explain']):
            if clause_risk == 'RED':
                return f"This clause in your {document_type} appears to have high risk. The specific terms may put you at a disadvantage. I recommend having a legal professional review this clause to explain the exact implications and suggest alternatives."
            elif clause_risk == 'YELLOW':
                return f"This clause in your {document_type} has moderate risk. While not immediately dangerous, the terms could be more balanced. Consider asking the other party if this clause can be modified to be more fair."
            else:
                return f"Legal terms in {document_type}s can be complex. For specific definitions and implications, I recommend consulting with a qualified legal professional who can provide accurate interpretations based on your jurisdiction."
        
        elif any(word in question_lower for word in ['right', 'rights', 'can i', 'allowed']):
            if clause_risk == 'RED':
                return f"High-risk clauses often limit your rights significantly. This clause may restrict what you can do or require you to give up important protections. Please consult with a legal professional to understand your rights under this agreement."
            else:
                return f"Understanding your rights in a {document_type} is important. While I can provide general guidance, specific rights can vary by location and situation. Consider consulting with a legal professional for personalized advice about your rights."
        
        elif any(word in question_lower for word in ['must', 'have to', 'required', 'obligation']):
            if clause_risk == 'RED':
                return f"High-risk clauses often create unfair obligations. This clause may require you to do things that put you at a disadvantage. Before agreeing to these obligations, please have a legal professional review what you're committing to."
            else:
                return f"Legal obligations in a {document_type} should be clearly understood before signing. If you're unsure about specific requirements, it's best to seek professional legal advice to understand what you're agreeing to do."
        
        elif any(word in question_lower for word in ['risk', 'dangerous', 'problem', 'concern']):
            if clause_risk == 'RED':
                return f"You're right to be concerned about this high-risk clause. It could create significant problems for you. I strongly recommend having a legal professional review this clause and suggest safer alternatives before you sign."
            elif clause_risk == 'YELLOW':
                return f"This clause does have some risk, but it's not immediately dangerous. However, it could be improved. Consider discussing modifications with the other party or getting legal advice on how to make it more balanced."
            else:
                return f"It's good that you're being cautious about your {document_type}. While this clause appears to have lower risk, if you have specific concerns, a legal professional can provide detailed guidance."
        
        else:
            # General response with context
            if clause_risk == 'RED':
                return f"I understand you're asking about a high-risk clause in your {document_type}. While I'm having trouble accessing my full AI capabilities right now, I strongly recommend consulting with a legal professional about this clause, as it appears to have significant risks."
            elif clause_risk == 'YELLOW':
                return f"I understand you're asking about your {document_type}. This clause has moderate risk, so while it's not immediately dangerous, you may want to consider getting legal advice to understand your options for improvement."
            else:
                return f"I understand you're asking about your {document_type}. While I'm having trouble accessing my full AI capabilities right now, I'd recommend reviewing the specific clause you're concerned about and considering consultation with a legal professional if you have serious concerns."
    
    async def analyze_document_risk(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """OPTIMIZED: Analyze document risk with parallel processing and smart caching"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 OPTIMIZED Analysis - Document type: {document_type}, text length: {len(document_text)}")
            
            if not self.enabled:
                logger.info("AI service disabled, using optimized fallback analysis")
                return await self._optimized_fallback_risk_analysis(document_text, document_type)
            
            # Smart content-based caching with hash
            content_hash = hashlib.md5(document_text.encode()).hexdigest()
            cache_key = f"risk_analysis_v2:{document_type}:{content_hash}"
            cached_result = self.response_cache.get(cache_key)
            if cached_result:
                logger.info(f"⚡ Returning cached analysis (saved ~25s)")
                return cached_result
            
            # PARALLEL PROCESSING: Extract clauses first, then batch analyze
            clauses = await self._extract_optimized_clauses(document_text)
            logger.info(f"📄 Extracted {len(clauses)} clauses for parallel analysis")
            
            # Use Groq as primary for speed (1-2s vs Gemini 9-11s)
            if self.groq_enabled and self._check_quota('groq'):
                try:
                    # BATCH PROCESSING: Analyze multiple clauses in single API call
                    result = await self._batch_analyze_with_groq(clauses, document_type)
                    
                    # Cache successful analysis
                    self.response_cache[cache_key] = result
                    
                    processing_time = time.time() - start_time
                    logger.info(f"✅ OPTIMIZED Analysis completed in {processing_time:.2f}s (target: <30s)")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Groq batch analysis failed: {e}, trying Gemini")
            
            # Fallback to Gemini if Groq fails
            if self.gemini_enabled and self._check_quota('gemini'):
                try:
                    result = await self._batch_analyze_with_gemini(clauses, document_type)
                    self.response_cache[cache_key] = result
                    
                    processing_time = time.time() - start_time
                    logger.info(f"✅ Gemini Analysis completed in {processing_time:.2f}s")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Gemini batch analysis failed: {e}, using optimized fallback")
            
            # Final optimized fallback
            result = await self._optimized_fallback_risk_analysis(document_text, document_type)
            processing_time = time.time() - start_time
            logger.info(f"✅ Fallback Analysis completed in {processing_time:.2f}s")
            return result
                
        except Exception as e:
            logger.error(f"All optimized analysis services failed: {e}, using emergency fallback")
            return await self._optimized_fallback_risk_analysis(document_text, document_type)
    
    async def _extract_optimized_clauses(self, document_text: str) -> List[Dict[str, str]]:
        """ENHANCED: Extract clauses with comprehensive parsing strategies"""
        import re
        
        # Smart clause extraction with multiple strategies
        clauses = []
        
        # Strategy 1: Numbered clauses with "That" (3. That the Tenant shall pay...)
        numbered_that_pattern = r'(\d+\.\s+That\s+[^0-9]+?)(?=\d+\.\s+That|\d+\.\s+[A-Z]|$)'
        numbered_that_matches = re.findall(numbered_that_pattern, document_text, re.MULTILINE | re.DOTALL)
        
        # Strategy 2: General numbered sections (1., 2., 3., etc.)
        general_numbered_pattern = r'(\d+\.\s+[A-Z][^0-9]*?)(?=\d+\.\s+[A-Z]|\n\s*\n|$)'
        general_numbered_matches = re.findall(general_numbered_pattern, document_text, re.MULTILINE | re.DOTALL)
        
        # Strategy 3: Numbered sections without capital requirement (more flexible)
        flexible_numbered_pattern = r'(\d+\.\s+[^0-9\n]{10,}?)(?=\d+\.\s+|\n\s*\n|$)'
        flexible_numbered_matches = re.findall(flexible_numbered_pattern, document_text, re.MULTILINE | re.DOTALL)
        
        # Strategy 4: Lettered sections (a), b), (i), (ii), etc.)
        lettered_pattern = r'(\([a-z]+\)\s+[^(]{20,}?)(?=\([a-z]+\)|\n\s*\n|$)'
        lettered_matches = re.findall(lettered_pattern, document_text, re.MULTILINE | re.DOTALL)
        
        # Strategy 5: Roman numeral sections (i), ii), iii), etc.)
        roman_pattern = r'(\([ivxlcdm]+\)\s+[^(]{20,}?)(?=\([ivxlcdm]+\)|\n\s*\n|$)'
        roman_matches = re.findall(roman_pattern, document_text, re.MULTILINE | re.DOTALL)
        
        # Strategy 6: Header-based sections (ALL CAPS headers)
        header_pattern = r'([A-Z][A-Z\s]{3,}:?\s*\n[^A-Z\n]*(?:\n[^A-Z\n]*)*)'
        header_matches = re.findall(header_pattern, document_text, re.MULTILINE)
        
        # Strategy 7: Sentence-based extraction (sentences ending with periods)
        sentence_pattern = r'([A-Z][^.!?]*[.!?](?:\s+[A-Z][^.!?]*[.!?])*)'
        sentence_matches = re.findall(sentence_pattern, document_text, re.MULTILINE)
        # Filter sentences to get substantial clauses (100+ chars)
        sentence_matches = [s.strip() for s in sentence_matches if len(s.strip()) > 100]
        
        # Strategy 8: Paragraph-based (double line breaks) - enhanced
        paragraphs = []
        for p in document_text.split('\n\n'):
            p = p.strip()
            if len(p) > 50:  # Lowered threshold to catch more content
                # Split long paragraphs into sentences if they're too long
                if len(p) > 800:
                    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', p)
                    for sentence in sentences:
                        if len(sentence.strip()) > 50:
                            paragraphs.append(sentence.strip())
                else:
                    paragraphs.append(p)
        
        # Strategy 9: Line-based extraction for structured documents
        lines = [line.strip() for line in document_text.split('\n') if len(line.strip()) > 80]
        
        # Combine all matches, prioritizing numbered clauses
        all_clauses = (numbered_that_matches + general_numbered_matches + 
                      flexible_numbered_matches + lettered_matches + 
                      roman_matches + header_matches + sentence_matches + 
                      paragraphs + lines)
        
        # Enhanced deduplication and filtering with importance scoring
        seen_hashes = set()
        seen_content = set()
        
        # Define comprehensive importance keywords for prioritizing clauses
        critical_importance_keywords = [
            'liability', 'unlimited liability', 'termination', 'immediate termination', 
            'payment', 'rent', 'deposit', 'security deposit', 'damages', 'liquidated damages',
            'penalty', 'indemnify', 'hold harmless', 'breach', 'material breach', 'default',
            'governing law', 'arbitration', 'jurisdiction', 'waiver', 'force majeure'
        ]
        
        high_importance_keywords = [
            'confidential', 'non-disclosure', 'non-compete', 'assignment', 'modification',
            'amendment', 'notice', 'cure period', 'insurance', 'compliance', 'audit',
            'intellectual property', 'proprietary', 'trade secret', 'ownership'
        ]
        
        medium_importance_keywords = [
            'maintenance', 'repair', 'utilities', 'inspection', 'subletting',
            'pets', 'parking', 'storage', 'common areas', 'rules', 'regulations',
            'access', 'use', 'restrictions', 'obligations', 'rights'
        ]
        
        # Score and sort clauses by importance
        scored_clauses = []
        for clause_text in all_clauses:
            clause_text = clause_text.strip()
            
            # Skip very short clauses
            if len(clause_text) < 30:  # Increased minimum for quality
                continue
            
            # Calculate importance score
            text_lower = clause_text.lower()
            high_score = sum(2 for kw in high_importance_keywords if kw in text_lower)
            medium_score = sum(1 for kw in medium_importance_keywords if kw in text_lower)
            length_bonus = min(2, len(clause_text) // 200)  # Bonus for substantial clauses
            
            importance_score = high_score + medium_score + length_bonus
            scored_clauses.append((importance_score, clause_text))
        
        # Sort by importance score (highest first)
        scored_clauses.sort(key=lambda x: x[0], reverse=True)
        
        for importance_score, clause_text in scored_clauses:
            # Skip if we've seen similar content (first 80 chars for better deduplication)
            content_signature = clause_text[:80].lower().replace(' ', '').replace('\n', '').replace('\t', '')
            if content_signature in seen_content:
                continue
            seen_content.add(content_signature)
                
            # Create content hash for deduplication
            clause_hash = hashlib.md5(clause_text.encode()).hexdigest()[:8]
            if clause_hash in seen_hashes:
                continue
            seen_hashes.add(clause_hash)
            
            # Enhanced title extraction
            title = f"Clause {len(clauses) + 1}"
            
            # Try to extract a meaningful title from the clause
            if re.match(r'^\d+\.', clause_text):
                # For numbered clauses like "3. That the Tenant shall pay..."
                title_match = re.match(r'^(\d+\.\s+[^.]{0,60})', clause_text)
                if title_match:
                    title = title_match.group(1).strip()
                    # Clean up title
                    if len(title) > 60:
                        title = title[:57] + "..."
            elif clause_text.startswith('('):
                # For lettered/roman clauses like "(a) The tenant must..."
                title_match = re.match(r'^(\([^)]+\)\s+[^.]{0,40})', clause_text)
                if title_match:
                    title = title_match.group(1).strip()
            elif re.match(r'^[A-Z][A-Z\s]{3,}:', clause_text):
                # For header-based clauses
                title_match = re.match(r'^([A-Z][A-Z\s]{3,}:?)', clause_text)
                if title_match:
                    title = title_match.group(1).strip()
            else:
                # For other clauses, use first meaningful words
                words = clause_text.split()[:10]
                # Filter out common stop words for better titles
                meaningful_words = [w for w in words if w.lower() not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']]
                if meaningful_words:
                    title = ' '.join(meaningful_words[:8]) + ('...' if len(meaningful_words) > 8 else '')
                else:
                    title = ' '.join(words[:8]) + ('...' if len(words) > 8 else '')
            
            clauses.append({
                'id': str(len(clauses) + 1),
                'title': title[:150],
                'text': clause_text,
                'hash': clause_hash
            })
            
            # Optimized limit - focus on important clauses to save API costs
            if len(clauses) >= 25:  # Reduced from 75 to 25 for API efficiency
                break
        
        logger.info(f"🔍 Extracted {len(clauses)} unique clauses using optimized parsing")
        
        # Log first few clauses for debugging
        for i, clause in enumerate(clauses[:3]):
            logger.debug(f"Clause {i+1}: {clause['title'][:50]}...")
        
        return clauses
    
    async def _batch_analyze_with_groq(self, clauses: List[Dict], document_type: str) -> Dict[str, Any]:
        """OPTIMIZED: Batch analyze clauses with Groq for speed (1-2s response time)"""
        
        # Process important clauses in smaller batches for better quality and API efficiency
        all_clause_assessments = []
        batch_size = 10  # Reduced from 15 to 10 for better analysis quality and API efficiency
        
        for batch_start in range(0, len(clauses), batch_size):
            batch_clauses = clauses[batch_start:batch_start + batch_size]
            
            # Create batch prompt for this batch of clauses
            clauses_text = "\n\n".join([
                f"CLAUSE {clause['id']}: {clause['title']}\n{clause['text'][:400]}{'...' if len(clause['text']) > 400 else ''}"
                for clause in batch_clauses
            ])
            
            prompt = f"""LEGAL ANALYSIS: Analyze this {document_type.replace('_', ' ')} and provide detailed risk assessment in clean JSON format.

DOCUMENT CLAUSES TO ANALYZE (Batch {batch_start//batch_size + 1}):
{clauses_text}

ANALYSIS REQUIREMENTS:
1. Analyze ALL {len(batch_clauses)} clauses provided above
2. For each clause, provide specific risk assessment with clear reasoning
3. Focus on practical implications and actionable insights
4. Use precise language and avoid generic responses
5. Include specific examples where possible

RESPONSE FORMAT (Clean JSON only):
{{
    "clause_assessments": [
        {{
            "clause_id": "1",
            "clause_title": "Descriptive title based on clause content",
            "assessment": {{
                "level": "RED|YELLOW|GREEN",
                "score": 0.0-1.0,
                "severity": "high|moderate|low",
                "confidence_percentage": 70-95,
                "reasons": [
                    "Specific reason with concrete details",
                    "Another specific concern with examples"
                ],
                "risk_categories": {{
                    "financial": 0.0-1.0,
                    "legal": 0.0-1.0,
                    "operational": 0.0-1.0,
                    "compliance": 0.0-1.0
                }}
            }}
        }}
    ]
}}

CRITICAL INSTRUCTIONS:
- Provide assessment for ALL {len(batch_clauses)} clauses
- Be specific and detailed in reasons (avoid generic phrases)
- Include concrete examples and dollar amounts when relevant
- Focus on practical business/legal implications
- Ensure JSON is properly formatted and complete"""

            try:
                request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
                debug_logger.info(f"[{request_id}] Groq BATCH Analysis - Batch {batch_start//batch_size + 1}, {len(batch_clauses)} clauses")
                
                start_time = time.time()
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert legal risk analyst specializing in contract analysis. Provide detailed, specific risk assessments with concrete examples and actionable insights. Return only properly formatted JSON. Avoid generic responses - be specific about risks, amounts, timeframes, and implications. Analyze every clause thoroughly."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.2,  # Lower for consistency
                    max_tokens=4000,  # Increased to handle more clauses
                    top_p=0.9,
                    stream=False
                )
                response_time = time.time() - start_time
                
                response_text = response.choices[0].message.content.strip()
                debug_logger.info(f"[{request_id}] Groq BATCH Success - {response_time:.2f}s, {len(response_text)} chars")
                
                # Parse batch response and add to all assessments
                batch_data = self._parse_batch_response(response_text, batch_clauses)
                if batch_data and 'clause_assessments' in batch_data:
                    all_clause_assessments.extend(batch_data['clause_assessments'])
                    logger.info(f"✅ Processed batch {batch_start//batch_size + 1}: {len(batch_data['clause_assessments'])} clauses analyzed")
                else:
                    logger.warning(f"⚠️ Batch {batch_start//batch_size + 1} failed to parse, using fallback")
                    # Use fallback for this batch
                    fallback_assessments = self._create_fallback_assessments(batch_clauses)
                    all_clause_assessments.extend(fallback_assessments)
                
            except Exception as e:
                logger.warning(f"Batch {batch_start//batch_size + 1} failed: {e}, using fallback")
                # Use fallback for this batch
                fallback_assessments = self._create_fallback_assessments(batch_clauses)
                all_clause_assessments.extend(fallback_assessments)
        
        # Calculate overall risk from all clause assessments
        overall_risk = self._calculate_overall_risk(all_clause_assessments)
        
        # Update quota for all batches
        total_tokens = sum(len(clause['text']) for clause in clauses)
        self._update_quota('groq', total_tokens, len(str(all_clause_assessments)))
        
        logger.info(f"✅ Successfully analyzed ALL {len(all_clause_assessments)} clauses in {len(range(0, len(clauses), batch_size))} batches")
        
        return {
            "overall_risk": overall_risk,
            "clause_assessments": all_clause_assessments
        }

        try:
            request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
            debug_logger.info(f"[{request_id}] Groq BATCH Analysis - {len(clauses)} clauses")
            
            start_time = time.time()
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fast legal risk analyzer. Return concise JSON only. No explanations outside JSON. Focus on key risks only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.2,  # Lower for consistency
                max_tokens=4000,  # Increased to handle more clauses
                top_p=0.9,
                stream=False
            )
            response_time = time.time() - start_time
            
            response_text = response.choices[0].message.content.strip()
            debug_logger.info(f"[{request_id}] Groq BATCH Success - {response_time:.2f}s, {len(response_text)} chars")
            
            # Parse and enhance JSON response
            risk_data = self._parse_and_enhance_batch_response(response_text, clauses)
            self._update_quota('groq', len(prompt), len(response_text))
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Groq batch analysis failed: {e}")
            raise
    
    async def _batch_analyze_with_gemini(self, clauses: List[Dict], document_type: str) -> Dict[str, Any]:
        """OPTIMIZED: Batch analyze clauses with Gemini (fallback)"""
        
        # Process ALL clauses in batches to avoid token limits
        all_clause_assessments = []
        batch_size = 12  # Process 12 clauses at a time for Gemini
        
        for batch_start in range(0, len(clauses), batch_size):
            batch_clauses = clauses[batch_start:batch_start + batch_size]
            
            clauses_text = "\n\n".join([
                f"CLAUSE {clause['id']}: {clause['title']}\n{clause['text'][:500]}{'...' if len(clause['text']) > 500 else ''}"
                for clause in batch_clauses
            ])
            
            prompt = f"""Analyze this {document_type.replace('_', ' ')} and return concise JSON.

CLAUSES TO ANALYZE (Batch {batch_start//batch_size + 1}):
{clauses_text}

REQUIREMENTS - ANALYZE ALL {len(batch_clauses)} CLAUSES:
1. EVERY clause: risk level, score, 1-2 key reasons
2. NO full clause text repetition in output
3. Return assessment for ALL clauses provided

JSON format:
{{
    "clause_assessments": [
        {{
            "clause_id": "1",
            "clause_title": "Brief title",
            "assessment": {{
                "level": "RED|YELLOW|GREEN",
                "score": 0.0-1.0,
                "severity": "high|moderate|low", 
                "confidence_percentage": 85,
                "reasons": ["reason 1", "reason 2"],
                "risk_categories": {{"financial": 0.0-1.0, "legal": 0.0-1.0, "operational": 0.0-1.0}}
            }}
        }}
    ]
}}

CRITICAL: Return assessment for ALL {len(batch_clauses)} clauses."""

            try:
                request_id = hashlib.md5(f"{time.time()}{prompt[:100]}".encode()).hexdigest()[:8]
                debug_logger.info(f"[{request_id}] Gemini BATCH Analysis - Batch {batch_start//batch_size + 1}, {len(batch_clauses)} clauses")
                
                generation_config = genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=3000,  # Increased for more clauses
                    top_p=0.9,
                    candidate_count=1
                )
                
                model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash',
                    generation_config=generation_config,
                    system_instruction="You are a legal risk analyzer. Return concise JSON only. ANALYZE EVERY CLAUSE PROVIDED."
                )
                
                start_time = time.time()
                response = model.generate_content(prompt)
                response_time = time.time() - start_time
                
                response_text = response.text.strip() if hasattr(response, 'text') else ""
                debug_logger.info(f"[{request_id}] Gemini BATCH Success - {response_time:.2f}s")
                
                # Parse batch response and add to all assessments
                batch_data = self._parse_batch_response(response_text, batch_clauses)
                if batch_data and 'clause_assessments' in batch_data:
                    all_clause_assessments.extend(batch_data['clause_assessments'])
                    logger.info(f"✅ Processed Gemini batch {batch_start//batch_size + 1}: {len(batch_data['clause_assessments'])} clauses analyzed")
                else:
                    logger.warning(f"⚠️ Gemini batch {batch_start//batch_size + 1} failed to parse, using fallback")
                    # Use fallback for this batch
                    fallback_assessments = self._create_fallback_assessments(batch_clauses)
                    all_clause_assessments.extend(fallback_assessments)
                
            except Exception as e:
                logger.warning(f"Gemini batch {batch_start//batch_size + 1} failed: {e}, using fallback")
                # Use fallback for this batch
                fallback_assessments = self._create_fallback_assessments(batch_clauses)
                all_clause_assessments.extend(fallback_assessments)
        
        # Calculate overall risk from all clause assessments
        overall_risk = self._calculate_overall_risk(all_clause_assessments)
        
        # Update quota for all batches
        total_tokens = sum(len(clause['text']) for clause in clauses)
        self._update_quota('gemini', total_tokens, len(str(all_clause_assessments)))
        
        logger.info(f"✅ Gemini successfully analyzed ALL {len(all_clause_assessments)} clauses in {len(range(0, len(clauses), batch_size))} batches")
        
        return {
            "overall_risk": overall_risk,
            "clause_assessments": all_clause_assessments
        }
    
    def _parse_batch_response(self, response_text: str, batch_clauses: List[Dict]) -> Dict[str, Any]:
        """Enhanced parsing of batch response with better error handling"""
        try:
            # Clean JSON response more thoroughly
            cleaned_response = response_text.strip()
            
            # Remove markdown code blocks
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            # Remove any leading/trailing whitespace and newlines
            cleaned_response = cleaned_response.strip()
            
            # Try to find JSON content if wrapped in other text
            if not cleaned_response.startswith('{'):
                json_start = cleaned_response.find('{')
                if json_start != -1:
                    cleaned_response = cleaned_response[json_start:]
            
            if not cleaned_response.endswith('}'):
                json_end = cleaned_response.rfind('}')
                if json_end != -1:
                    cleaned_response = cleaned_response[:json_end + 1]
            
            batch_data = json.loads(cleaned_response)
            
            # Enhance clause assessments with original clause text and better formatting
            if 'clause_assessments' in batch_data:
                for i, clause_assessment in enumerate(batch_data['clause_assessments']):
                    if i < len(batch_clauses):
                        original_clause = batch_clauses[i]
                        
                        # Keep more clause text for better context (increased from 300 to 500)
                        clause_text = original_clause['text']
                        if len(clause_text) > 500:
                            # Try to break at sentence boundary
                            truncated = clause_text[:500]
                            last_period = truncated.rfind('.')
                            if last_period > 400:  # If we can find a good break point
                                clause_text = truncated[:last_period + 1] + "..."
                            else:
                                clause_text = truncated + "..."
                        
                        clause_assessment['clause_text'] = clause_text
                        clause_assessment['clause_title'] = original_clause['title']
                        
                        # Ensure required fields with better defaults
                        if 'assessment' in clause_assessment:
                            assessment = clause_assessment['assessment']
                            
                            # Ensure all required fields exist
                            if 'level' not in assessment:
                                assessment['level'] = 'GREEN'
                            if 'score' not in assessment:
                                assessment['score'] = 0.3
                            if 'severity' not in assessment:
                                assessment['severity'] = 'low'
                            if 'confidence_percentage' not in assessment:
                                assessment['confidence_percentage'] = 75
                            if 'reasons' not in assessment:
                                assessment['reasons'] = ['Standard clause with typical terms']
                            
                            # Enhanced risk categories
                            if 'risk_categories' not in assessment:
                                score = assessment.get('score', 0.3)
                                assessment['risk_categories'] = {
                                    "financial": score,
                                    "legal": max(0.0, score - 0.1),
                                    "operational": max(0.0, score - 0.2),
                                    "compliance": max(0.0, score - 0.1)
                                }
            
            return batch_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse batch JSON response: {e}")
            logger.debug(f"Raw response: {response_text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing batch response: {e}")
            return None
    
    def _create_fallback_assessments(self, batch_clauses: List[Dict]) -> List[Dict]:
        """Create enhanced fallback assessments for a batch of clauses"""
        high_risk_keywords = [
            'unlimited liability', 'sole responsibility', 'all damages', 'immediate termination',
            'without notice', 'at sole discretion', 'waive all rights', 'indemnify',
            'hold harmless', 'liquidated damages', 'penalty', 'forfeit', 'irrevocable',
            'non-refundable', 'personal guarantee', 'joint and several', 'strict liability'
        ]
        
        medium_risk_keywords = [
            'liability', 'responsible for', 'damages', 'termination', 'breach',
            'default', 'cure period', 'notice required', 'governing law', 'arbitration',
            'confidential', 'non-compete', 'exclusive', 'assignment', 'modification'
        ]
        
        low_risk_keywords = [
            'standard', 'reasonable', 'mutual', 'written notice', 'good faith',
            'commercially reasonable', 'industry standard', 'best efforts'
        ]
        
        assessments = []
        
        for clause in batch_clauses:
            clause_text = clause['text'].lower()
            
            high_risk_count = sum(1 for kw in high_risk_keywords if kw in clause_text)
            medium_risk_count = sum(1 for kw in medium_risk_keywords if kw in clause_text)
            low_risk_count = sum(1 for kw in low_risk_keywords if kw in clause_text)
            
            # Enhanced scoring algorithm
            clause_score = min(1.0, (high_risk_count * 0.35 + medium_risk_count * 0.15 - low_risk_count * 0.05))
            clause_score = max(0.1, clause_score)  # Minimum score
            
            if clause_score > 0.6:
                level, severity = "RED", "high"
                reasons = [f"Contains {high_risk_count} high-risk terms", "Requires careful legal review"]
            elif clause_score > 0.3:
                level, severity = "YELLOW", "moderate"
                reasons = [f"Contains {medium_risk_count} moderate-risk terms", "Review recommended"]
            else:
                level, severity = "GREEN", "low"
                reasons = ["Standard terms with acceptable risk level", "Generally favorable language"]
            
            # Enhanced clause text handling (increased from 300 to 500 chars)
            display_text = clause['text']
            if len(display_text) > 500:
                # Try to break at sentence boundary
                truncated = display_text[:500]
                last_period = truncated.rfind('.')
                if last_period > 400:
                    display_text = truncated[:last_period + 1] + "..."
                else:
                    display_text = truncated + "..."
            
            assessments.append({
                "clause_id": clause['id'],
                "clause_text": display_text,
                "clause_title": clause['title'],
                "assessment": {
                    "level": level,
                    "score": clause_score,
                    "severity": severity,
                    "confidence_percentage": 70,
                    "reasons": [f"Keyword analysis: {high_risk_count} high-risk, {medium_risk_count} medium-risk indicators"],
                    "risk_categories": {
                        "financial": clause_score,
                        "legal": clause_score,
                        "operational": max(0.0, clause_score - 0.1)
                    }
                }
            })
        
        return assessments
    
    def _calculate_overall_risk(self, clause_assessments: List[Dict]) -> Dict[str, Any]:
        """Calculate overall risk from all clause assessments"""
        if not clause_assessments:
            return {
                "level": "GREEN",
                "score": 0.0,
                "severity": "low",
                "confidence_percentage": 50,
                "reasons": ["No clauses analyzed"],
                "risk_categories": {"financial": 0.0, "legal": 0.0, "operational": 0.0}
            }
        
        # Calculate average risk score
        total_score = 0
        risk_counts = {'RED': 0, 'YELLOW': 0, 'GREEN': 0}
        high_risk_reasons = []
        
        for clause_assessment in clause_assessments:
            assessment = clause_assessment.get('assessment', {})
            score = assessment.get('score', 0.0)
            level = assessment.get('level', 'GREEN')
            reasons = assessment.get('reasons', [])
            
            total_score += score
            risk_counts[level] += 1
            
            # Collect high-risk reasons
            if level == 'RED' and reasons:
                high_risk_reasons.extend(reasons[:1])  # Take first reason from each high-risk clause
        
        avg_score = total_score / len(clause_assessments)
        
        # Determine overall risk level
        if risk_counts['RED'] > 0 or avg_score > 0.6:
            overall_level, overall_severity = "RED", "high"
            main_reasons = high_risk_reasons[:2] if high_risk_reasons else ["Multiple high-risk clauses identified"]
        elif risk_counts['YELLOW'] > len(clause_assessments) * 0.3 or avg_score > 0.3:
            overall_level, overall_severity = "YELLOW", "moderate"
            main_reasons = ["Multiple moderate-risk clauses need attention"]
        else:
            overall_level, overall_severity = "GREEN", "low"
            main_reasons = ["Most clauses have acceptable risk levels"]
        
        # Calculate confidence based on number of clauses analyzed
        confidence = min(95, 60 + (len(clause_assessments) * 2))  # Higher confidence with more clauses
        
        return {
            "level": overall_level,
            "score": round(avg_score, 2),
            "severity": overall_severity,
            "confidence_percentage": confidence,
            "reasons": main_reasons,
            "risk_categories": {
                "financial": round(avg_score, 2),
                "legal": round(avg_score, 2),
                "operational": round(max(0.0, avg_score - 0.1), 2)
            }
        }
    
    def _parse_and_enhance_batch_response(self, response_text: str, original_clauses: List[Dict]) -> Dict[str, Any]:
        """Parse batch response and enhance with original clause data - LEGACY METHOD"""
        try:
            # Clean JSON response
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            risk_data = json.loads(cleaned_response.strip())
            
            # Enhance clause assessments with original clause text (TRUNCATED for performance)
            if 'clause_assessments' in risk_data:
                for i, clause_assessment in enumerate(risk_data['clause_assessments']):
                    if i < len(original_clauses):
                        original_clause = original_clauses[i]
                        # OPTIMIZATION: Truncate clause text to max 300 chars for display
                        clause_text = original_clause['text']
                        if len(clause_text) > 300:
                            clause_text = clause_text[:300] + "..."
                        
                        clause_assessment['clause_text'] = clause_text
                        clause_assessment['clause_title'] = original_clause['title']
                        
                        # Ensure required fields
                        if 'assessment' in clause_assessment:
                            assessment = clause_assessment['assessment']
                            if 'risk_categories' not in assessment:
                                score = assessment.get('score', 0.5)
                                assessment['risk_categories'] = {
                                    "financial": score,
                                    "legal": score,
                                    "operational": max(0.0, score - 0.1)
                                }
            
            # Ensure overall risk has required fields
            if 'overall_risk' in risk_data and 'risk_categories' not in risk_data['overall_risk']:
                score = risk_data['overall_risk'].get('score', 0.5)
                risk_data['overall_risk']['risk_categories'] = {
                    "financial": score,
                    "legal": score,
                    "operational": max(0.0, score - 0.1)
                }
            
            logger.info(f"✅ Successfully parsed batch response with {len(risk_data.get('clause_assessments', []))} clauses")
            return risk_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse batch JSON response: {e}")
            # Fallback to optimized keyword analysis
            return self._create_fallback_from_clauses(original_clauses)
    
    def _create_fallback_from_clauses(self, clauses: List[Dict]) -> Dict[str, Any]:
        """Create fallback analysis from extracted clauses"""
        high_risk_keywords = [
            'unlimited liability', 'sole responsibility', 'all damages', 'immediate termination',
            'without notice', 'at sole discretion', 'waive all rights', 'indemnify',
            'hold harmless', 'liquidated damages', 'penalty', 'forfeit'
        ]
        
        medium_risk_keywords = [
            'liability', 'responsible for', 'damages', 'termination', 'breach',
            'default', 'cure period', 'notice required', 'governing law'
        ]
        
        clause_assessments = []
        total_risk_score = 0
        
        for clause in clauses[:10]:  # Limit for performance
            clause_text = clause['text'].lower()
            
            high_risk_count = sum(1 for kw in high_risk_keywords if kw in clause_text)
            medium_risk_count = sum(1 for kw in medium_risk_keywords if kw in clause_text)
            
            clause_score = min(1.0, (high_risk_count * 0.4 + medium_risk_count * 0.2))
            total_risk_score += clause_score
            
            if clause_score > 0.6:
                level, severity = "RED", "high"
            elif clause_score > 0.3:
                level, severity = "YELLOW", "moderate"
            else:
                level, severity = "GREEN", "low"
            
            # OPTIMIZATION: Truncate clause text for display
            display_text = clause['text']
            if len(display_text) > 300:
                display_text = display_text[:300] + "..."
            
            clause_assessments.append({
                "clause_id": clause['id'],
                "clause_text": display_text,  # Truncated for performance
                "clause_title": clause['title'],
                "assessment": {
                    "level": level,
                    "score": clause_score,
                    "severity": severity,
                    "confidence_percentage": 70,
                    "reasons": [f"Keyword analysis: {high_risk_count} high-risk, {medium_risk_count} medium-risk indicators"],
                    "risk_categories": {
                        "financial": clause_score,
                        "legal": clause_score,
                        "operational": max(0.0, clause_score - 0.1)
                    }
                }
            })
        
        # Calculate overall risk
        avg_risk = total_risk_score / len(clauses) if clauses else 0
        if avg_risk > 0.6:
            overall_level, overall_severity = "RED", "high"
        elif avg_risk > 0.3:
            overall_level, overall_severity = "YELLOW", "moderate"
        else:
            overall_level, overall_severity = "GREEN", "low"
        
        return {
            "overall_risk": {
                "level": overall_level,
                "score": avg_risk,
                "severity": overall_severity,
                "confidence_percentage": 70,
                "reasons": [f"Analyzed {len(clauses)} clauses with keyword-based risk detection"],
                "risk_categories": {
                    "financial": avg_risk,
                    "legal": avg_risk,
                    "operational": max(0.0, avg_risk - 0.1)
                }
            },
            "clause_assessments": clause_assessments
        }

    async def _optimized_fallback_risk_analysis(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """OPTIMIZED: Fast fallback analysis with parallel processing and concise output"""
        logger.info("🔄 Using OPTIMIZED fallback risk analysis")
        
        # Extract clauses using optimized method
        clauses = await self._extract_optimized_clauses(document_text)
        logger.info(f"⚡ Extracted {len(clauses)} clauses for optimized analysis")
        
        # Use the optimized fallback method
        return self._create_fallback_from_clauses(clauses)
    
    def _extract_basic_clauses(self, text: str) -> List[str]:
        """Extract basic clauses from document text"""
        # Simple clause extraction based on sentence patterns
        import re
        
        # Split by common clause indicators
        clause_patterns = [
            r'\d+\.\s+',  # Numbered clauses
            r'[A-Z][A-Z\s]+:',  # ALL CAPS headers
            r'\n\n',  # Paragraph breaks
        ]
        
        clauses = []
        current_text = text
        
        for pattern in clause_patterns:
            parts = re.split(pattern, current_text)
            if len(parts) > 1:
                clauses.extend([part.strip() for part in parts if len(part.strip()) > 50])
                break
        
        if not clauses:
            # Fallback: split by sentences
            sentences = text.split('.')
            clauses = [s.strip() for s in sentences if len(s.strip()) > 50]
        
        return clauses[:20]  # Limit number of clauses
    
    def _assess_clause_risk(self, clause: str, high_risk_keywords: List[str], medium_risk_keywords: List[str]) -> Dict[str, Any]:
        """Assess risk for individual clause"""
        clause_lower = clause.lower()
        
        high_risk_found = [kw for kw in high_risk_keywords if kw in clause_lower]
        medium_risk_found = [kw for kw in medium_risk_keywords if kw in clause_lower]
        
        if high_risk_found:
            level = "RED"
            score = 0.8
            severity = "high"
            reasons = [f"Contains high-risk language: {', '.join(high_risk_found[:2])}"]
        elif len(medium_risk_found) >= 2:
            level = "YELLOW"
            score = 0.6
            severity = "moderate"
            reasons = [f"Contains multiple risk indicators: {', '.join(medium_risk_found[:2])}"]
        elif medium_risk_found:
            level = "YELLOW"
            score = 0.4
            severity = "moderate"
            reasons = [f"Contains risk indicator: {medium_risk_found[0]}"]
        else:
            level = "GREEN"
            score = 0.2
            severity = "low"
            reasons = ["No significant risk indicators found"]
        
        return {
            "level": level,
            "score": score,
            "severity": severity,
            "confidence_percentage": 55,  # Lower confidence for keyword analysis
            "reasons": reasons,
            "risk_categories": {
                "financial": score,
                "legal": score,
                "operational": max(0.0, score - 0.2)
            },
            "low_confidence_warning": True
        }

    def _extract_risk_level_from_context(self, context: Any) -> str:
        """Extract risk level from context for personalization"""
        if not context:
            return 'unknown'
        
        if isinstance(context, dict):
            # Check clause context first
            clause_context = context.get('clause', {})
            if clause_context and 'riskLevel' in clause_context:
                return clause_context['riskLevel']
            
            # Check document context
            document_context = context.get('document', {})
            if document_context and 'overallRisk' in document_context:
                return document_context['overallRisk']
        
        # Legacy format
        return getattr(context, 'risk_level', 'unknown')
    
    def _extract_document_type_from_context(self, context: Any) -> str:
        """Extract document type from context for personalization"""
        if not context:
            return 'legal document'
        
        if isinstance(context, dict):
            document_context = context.get('document', {})
            if document_context and 'documentType' in document_context:
                return document_context['documentType']
        
        # Legacy format
        return getattr(context, 'document_type', 'legal document')

    async def get_conversation_summary(self) -> ConversationSummaryResponse:
        """Enhanced conversation summary with analytics"""
        if not self.conversation_history:
            return ConversationSummaryResponse(
                success=True,
                total_questions=0,
                recent_questions=[],
                analytics={
                    'avg_response_length': 0,
                    'fallback_rate': 0,
                    'high_confidence_rate': 0
                }
            )
        
        # Calculate analytics
        total_questions = len(self.conversation_history)
        fallback_count = sum(1 for item in self.conversation_history if item.get('fallback', False))
        high_confidence_count = sum(1 for item in self.conversation_history if item.get('confidence') == 'high')
        avg_length = sum(item['response_length'] for item in self.conversation_history) / total_questions
        
        return ConversationSummaryResponse(
            success=True,
            total_questions=total_questions,
            recent_questions=[item['question'] for item in self.conversation_history[-5:]],
            analytics={
                'avg_response_length': round(avg_length, 1),
                'fallback_rate': round((fallback_count / total_questions) * 100, 1),
                'high_confidence_rate': round((high_confidence_count / total_questions) * 100, 1)
            },
            last_activity=max(item['timestamp'] for item in self.conversation_history) if self.conversation_history else None
        )