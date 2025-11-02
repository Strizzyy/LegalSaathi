"""
AI controller for FastAPI backend
"""

import logging
from fastapi import HTTPException

from models.ai_models import (
    ClarificationRequest, ClarificationResponse,
    ConversationSummaryResponse
)
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class AIController:
    """Controller for AI clarification and chat operations"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def get_clarification(self, request: ClarificationRequest) -> ClarificationResponse:
        """Handle AI clarification requests"""
        try:
            logger.info(f"Processing AI clarification request: question='{request.question[:50]}...', context_size={len(str(request.context)) if request.context else 0}")
            
            # Check if AI service is available
            if not self.ai_service or not hasattr(self.ai_service, 'enabled') or not self.ai_service.enabled:
                raise HTTPException(
                    status_code=503,
                    detail="AI clarification service is not available"
                )
            
            # Validate request
            if not request.question or len(request.question.strip()) < 5:
                logger.warning(f"Invalid question length: {len(request.question.strip()) if request.question else 0}")
                raise HTTPException(
                    status_code=400,
                    detail="Question must be at least 5 characters long"
                )
            
            if len(request.question) > 1000:
                logger.warning(f"Question too long: {len(request.question)} characters")
                raise HTTPException(
                    status_code=400,
                    detail="Question too long (max 1000 characters)"
                )
            
            # Validate expertise level
            if request.user_expertise_level and request.user_expertise_level not in ['beginner', 'intermediate', 'expert']:
                logger.warning(f"Invalid expertise level: {request.user_expertise_level}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid expertise level. Must be 'beginner', 'intermediate', or 'expert'"
                )
            
            # Get AI clarification
            response = await self.ai_service.get_clarification(request)
            
            logger.info(f"AI clarification completed: {response.conversation_id}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI clarification failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"AI clarification failed: {str(e)}"
            )
    
    async def get_conversation_summary(self) -> ConversationSummaryResponse:
        """Get conversation summary and analytics"""
        try:
            summary = await self.ai_service.get_conversation_summary()
            
            logger.info(f"Conversation summary retrieved: {summary.total_questions} questions")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get conversation summary: {str(e)}"
            )
    
    async def clear_conversation_history(self) -> dict:
        """Clear conversation history"""
        try:
            # Clear the conversation history
            self.ai_service.conversation_history.clear()
            
            return {
                "success": True,
                "message": "Conversation history cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear conversation history: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear conversation history: {str(e)}"
            )