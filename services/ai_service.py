"""
AI service for Groq API integration and clarification
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List

from models.ai_models import ClarificationRequest, ClarificationResponse, ConversationSummaryResponse

logger = logging.getLogger(__name__)

# Import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.error("Groq library not available - AI service will be disabled")


class AIService:
    """Enhanced AI service for document clarification using Groq API only"""
    
    def __init__(self):
        # Initialize Groq AI service
        self.groq_enabled = False
        
        # Initialize Groq service
        groq_key = os.getenv('GROQ_API_KEY')
        
        if groq_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=groq_key)
                self.groq_enabled = True
                logger.info("Groq AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq AI: {e}")
        else:
            if not groq_key:
                logger.warning("GROQ_API_KEY not found in environment")
            if not GROQ_AVAILABLE:
                logger.warning("Groq library not available")
        
        self.enabled = self.groq_enabled
        
        if not self.enabled:
            logger.warning("Groq AI service not available - using keyword fallback only")
        
        self.conversation_history = []
        self.fallback_responses = {
            'general': "I understand you're asking about your legal document. While I'm having trouble accessing my full AI capabilities right now, I'd recommend reviewing the specific clause you're concerned about and considering consultation with a legal professional if you have serious concerns.",
            'terms': "Legal terms can be complex. For specific definitions and implications, I recommend consulting with a qualified legal professional who can provide accurate interpretations based on your jurisdiction.",
            'rights': "Understanding your rights is important. While I can provide general guidance, specific rights can vary by location and situation. Consider consulting with a legal professional for personalized advice.",
            'obligations': "Legal obligations should be clearly understood before signing any document. If you're unsure about specific requirements, it's best to seek professional legal advice."
        }
    
    async def get_clarification(self, request: ClarificationRequest) -> ClarificationResponse:
        """Enhanced AI-powered conversational clarification with Groq fallback"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                raise Exception("AI service not available")
            
            # Build enhanced context from document and clause analysis
            context_text = self._build_enhanced_context(request.context)
            
            # Enhanced prompt with better structure
            prompt = f"""You are LegalSaathi, an AI legal document advisor specializing in making complex legal language accessible to everyday citizens.

{context_text}User Question: "{request.question}"

Please provide a helpful response that:
1. Directly answers the user's question in plain language
2. Explains any legal terms in simple words
3. Provides practical, actionable advice when appropriate
4. Indicates when professional legal consultation is recommended
5. Maintains a supportive, educational tone

Adapt your language complexity to the user's expertise level: {request.user_expertise_level}

Keep your response clear, concise (under 200 words), and focused on helping the user understand their document better."""

            # Try Groq API
            ai_response = None
            service_used = None
            
            if self.groq_enabled:
                try:
                    ai_response = await self._call_groq_async(prompt)
                    service_used = 'groq'
                    
                    # Check if response is generic or too short
                    if len(ai_response) < 20 or self._is_generic_response(ai_response):
                        raise ValueError("Generic or insufficient response from Groq")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(term in error_msg for term in ['quota', 'rate limit', 'exhausted', '429']):
                        logger.warning(f"Groq API quota/rate limit exceeded: {e}, using keyword fallback")
                    else:
                        logger.warning(f"Groq API failed: {e}, using keyword fallback")
                    ai_response = None
            
            # Fallback to keyword-based response if Groq failed
            if not ai_response:
                ai_response = self._get_intelligent_fallback(request.question, request.context)
                service_used = 'keyword_fallback'
            
            processing_time = time.time() - start_time
            
            # Determine confidence based on service used and response quality
            confidence_score = self._calculate_confidence(service_used, ai_response, request.context)
            
            # Store in conversation history with metadata
            conversation_entry = {
                'question': request.question,
                'response': ai_response,
                'timestamp': time.time(),
                'context_provided': bool(request.context),
                'response_length': len(ai_response),
                'confidence': 'high' if confidence_score > 70 else 'medium' if confidence_score > 40 else 'low',
                'service_used': service_used,
                'conversation_id': request.conversation_id or str(len(self.conversation_history) + 1)
            }
            self.conversation_history.append(conversation_entry)
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-25:]
            
            logger.info(f"AI clarification successful using {service_used}: {len(ai_response)} chars")
            
            return ClarificationResponse(
                success=True,
                response=ai_response,
                conversation_id=conversation_entry['conversation_id'],
                confidence_score=confidence_score,
                response_quality='high' if confidence_score > 70 else 'medium' if confidence_score > 40 else 'basic',
                processing_time=processing_time,
                fallback=service_used == 'keyword_fallback',
                service_used=service_used
            )
            
        except Exception as e:
            logger.error(f"All AI services failed: {e}, using emergency fallback")
            
            # Emergency fallback
            fallback_response = self._get_intelligent_fallback(request.question, request.context)
            processing_time = time.time() - start_time
            
            # Store fallback in history
            fallback_entry = {
                'question': request.question,
                'response': fallback_response,
                'timestamp': time.time(),
                'context_provided': bool(request.context),
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
                service_used='emergency_fallback'
            )
    
    def _build_enhanced_context(self, context: Any) -> str:
        """Build enhanced context text from request context"""
        context_text = ""
        if context:
            # Handle both dict and object formats for context
            if isinstance(context, dict):
                # Extract document context
                document_context = context.get('document', {})
                clause_context = context.get('clause', {})
                conversation_history = context.get('conversationHistory', [])
                
                # Document-level context
                document_type = document_context.get('documentType', 'legal document')
                overall_risk = document_context.get('overallRisk', 'unknown')
                document_summary = document_context.get('summary', '')
                total_clauses = document_context.get('totalClauses', 0)
                
                context_text = f"""Document Context:
- Type: {document_type}
- Overall Risk Level: {overall_risk}
- Total Clauses Analyzed: {total_clauses}
- Document Summary: {document_summary[:200]}{'...' if len(document_summary) > 200 else ''}

"""
                
                # Clause-specific context if available
                if clause_context:
                    clause_id = clause_context.get('clauseId', 'Unknown')
                    clause_text = clause_context.get('text', '')
                    clause_risk = clause_context.get('riskLevel', 'unknown')
                    clause_explanation = clause_context.get('explanation', '')
                    clause_implications = clause_context.get('implications', [])
                    clause_recommendations = clause_context.get('recommendations', [])
                    
                    context_text += f"""Specific Clause Context (Clause {clause_id}):
- Risk Level: {clause_risk}
- Clause Text: {clause_text[:300]}{'...' if len(clause_text) > 300 else ''}
- AI Explanation: {clause_explanation[:200]}{'...' if len(clause_explanation) > 200 else ''}
- Legal Implications: {'; '.join(clause_implications[:3])}
- Recommendations: {'; '.join(clause_recommendations[:3])}

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


    
    async def _call_groq_async(self, prompt: str) -> str:
        """Async wrapper for Groq API call for clarification"""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are LegalSaathi, an AI legal document advisor. Provide clear, helpful responses about legal documents in plain language."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Use updated Llama 3.1 model
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    async def _call_groq_risk_analysis(self, prompt: str) -> str:
        """Groq API call specifically for risk analysis with JSON response"""
        try:
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
                model="llama-3.1-8b-instant",  # Use available model for JSON parsing
                temperature=0.1,  # Lower temperature for more consistent JSON
                max_tokens=2000,  # More tokens for detailed analysis
                response_format={"type": "json_object"}  # Force JSON response
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
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
    
    def _calculate_confidence(self, service_used: str, response: str, context: Any) -> int:
        """Calculate confidence score based on service and response quality"""
        base_confidence = {
            'groq': 90,  # High confidence for Groq service
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
    
    def _get_intelligent_fallback(self, question: str, context: Any = None) -> str:
        """Provide intelligent fallback responses based on question content and context"""
        question_lower = question.lower()
        
        # Extract context information if available
        clause_risk = 'unknown'
        document_type = 'legal document'
        
        if context and isinstance(context, dict):
            clause_context = context.get('clause', {})
            document_context = context.get('document', {})
            clause_risk = clause_context.get('riskLevel', 'unknown')
            document_type = document_context.get('documentType', 'legal document')
        
        # Context-aware responses
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
        """Analyze document risk using Groq API with fallback to keyword analysis"""
        try:
            logger.info(f"AI Service enabled: {self.enabled}, Groq enabled: {self.groq_enabled}")
            logger.info(f"Analyzing document type: {document_type}, text length: {len(document_text)}")
            
            if not self.enabled:
                logger.info("AI service disabled, using fallback analysis")
                return await self._fallback_risk_analysis(document_text, document_type)
            
            # Build risk analysis prompt for Groq
            prompt = f"""You are a legal document risk analyzer. Analyze the following {document_type.replace('_', ' ')} for potential risks and issues.

Document Text:
{document_text[:4000]}  # Limit text length

Please provide a JSON response with the following structure:
{{
    "overall_risk": {{
        "level": "RED|YELLOW|GREEN",
        "score": 0.0-1.0,
        "severity": "high|moderate|low",
        "confidence_percentage": 0-100,
        "reasons": ["reason1", "reason2"],
        "risk_categories": {{
            "financial": 0.0-1.0,
            "legal": 0.0-1.0,
            "operational": 0.0-1.0
        }}
    }},
    "clause_assessments": [
        {{
            "clause_id": "1",
            "clause_text": "extracted clause text",
            "assessment": {{
                "level": "RED|YELLOW|GREEN",
                "score": 0.0-1.0,
                "severity": "high|moderate|low",
                "confidence_percentage": 0-100,
                "reasons": ["specific reasons"],
                "risk_categories": {{"financial": 0.0-1.0, "legal": 0.0-1.0, "operational": 0.0-1.0}},
                "low_confidence_warning": false
            }}
        }}
    ]
}}

Focus on identifying:
- Unfair or one-sided terms
- Financial risks and obligations
- Legal liability issues
- Termination and penalty clauses
- Unclear or ambiguous language

Return only valid JSON, no additional text."""

            # Use Groq API for risk analysis
            groq_response = await self._call_groq_risk_analysis(prompt)
            
            # Parse JSON response
            import json
            try:
                risk_data = json.loads(groq_response)
                logger.info("Successfully parsed Groq JSON response for risk analysis")
                return risk_data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Groq JSON response: {e}, using fallback")
                logger.info(f"Raw Groq response: {groq_response[:500]}...")
                return await self._fallback_risk_analysis(document_text, document_type)
                
        except Exception as e:
            logger.error(f"Groq risk analysis failed: {e}, using fallback")
            return await self._fallback_risk_analysis(document_text, document_type)
    
    async def _fallback_risk_analysis(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """Fallback keyword-based risk analysis with full clause text preservation"""
        logger.info("Using fallback risk analysis")
        logger.info(f"Fallback analyzing text: {document_text[:200]}...")
        # High-risk keywords
        high_risk_keywords = [
            'unlimited liability', 'sole responsibility', 'all damages', 'immediate termination',
            'without notice', 'at sole discretion', 'waive all rights', 'indemnify',
            'hold harmless', 'liquidated damages', 'penalty', 'forfeit'
        ]
        
        # Medium-risk keywords
        medium_risk_keywords = [
            'liability', 'responsible for', 'damages', 'termination', 'breach',
            'default', 'cure period', 'notice required', 'governing law'
        ]
        
        text_lower = document_text.lower()
        
        # Count risk indicators
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        
        # Calculate overall risk
        risk_score = min(1.0, (high_risk_count * 0.3 + medium_risk_count * 0.1))
        
        if risk_score > 0.7:
            risk_level = "RED"
            severity = "high"
        elif risk_score > 0.4:
            risk_level = "YELLOW"
            severity = "moderate"
        else:
            risk_level = "GREEN"
            severity = "low"
        
        # Generate basic clause assessments with full text preservation
        clauses = self._extract_basic_clauses(document_text)
        logger.info(f"Extracted {len(clauses)} clauses from document")
        
        clause_assessments = []
        
        for i, clause in enumerate(clauses[:10]):  # Limit to 10 clauses
            logger.info(f"Processing clause {i+1}: {len(clause)} characters")
            clause_risk = self._assess_clause_risk(clause, high_risk_keywords, medium_risk_keywords)
            clause_assessments.append({
                "clause_id": str(i + 1),
                "clause_text": clause,  # Preserve full clause text without truncation
                "assessment": clause_risk
            })
        
        return {
            "overall_risk": {
                "level": risk_level,
                "score": risk_score,
                "severity": severity,
                "confidence_percentage": 65,  # Slightly higher confidence for improved keyword analysis
                "reasons": [f"Keyword analysis detected {high_risk_count} high-risk and {medium_risk_count} medium-risk indicators"],
                "risk_categories": {
                    "financial": min(1.0, risk_score + 0.1),
                    "legal": risk_score,
                    "operational": max(0.0, risk_score - 0.1)
                }
            },
            "clause_assessments": clause_assessments
        }
    
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