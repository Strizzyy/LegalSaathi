"""
Expert Queue Controller for Human-in-the-Loop System
Manages expert review requests and queue operations with database persistence
"""

import logging
import base64
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException

from services.expert_queue_service import expert_queue_service
from models.expert_queue_models import (
    ExpertReviewSubmission, ExpertReviewResponse, ExpertReviewItemResponse,
    ExpertAnalysisSubmission, ExpertAnalysisResponse, QueueStatsResponse,
    QueueFilters, PaginationParams, QueueResponse, ReviewStatus, Priority
)

logger = logging.getLogger(__name__)


class ExpertQueueController:
    """Controller for expert review queue operations with database persistence"""
    
    def __init__(self):
        self.queue_service = expert_queue_service
    
    async def submit_for_expert_review(
        self, 
        document_content: str,
        ai_analysis: dict,
        user_email: str,
        confidence_score: float,
        confidence_breakdown: dict,
        document_type: Optional[str] = None
    ) -> ExpertReviewResponse:
        """Submit document for expert review with database persistence"""
        try:
            # Encode document content as base64 for storage
            if isinstance(document_content, str):
                document_content_b64 = base64.b64encode(document_content.encode('utf-8')).decode('utf-8')
            else:
                document_content_b64 = base64.b64encode(document_content).decode('utf-8')
            
            submission = ExpertReviewSubmission(
                document_content=document_content_b64,
                ai_analysis=ai_analysis,
                user_email=user_email,
                confidence_score=confidence_score,
                confidence_breakdown=confidence_breakdown,
                document_type=document_type
            )
            
            response = await self.queue_service.add_to_queue(submission)
            
            logger.info(f"Expert review request submitted: {response.review_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to submit expert review request: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit for expert review: {str(e)}"
            )
    
    async def get_expert_requests(
        self, 
        status: Optional[ReviewStatus] = None,
        priority: Optional[Priority] = None,
        assigned_expert_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> QueueResponse:
        """Get expert review requests with filtering and pagination"""
        try:
            filters = QueueFilters(
                status=status,
                priority=priority,
                assigned_expert_id=assigned_expert_id
            )
            
            pagination = PaginationParams(
                page=page,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            response = await self.queue_service.get_queue_items(filters, pagination)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get expert requests: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get expert requests: {str(e)}"
            )
    
    async def get_queue_stats(self) -> QueueStatsResponse:
        """Get expert queue statistics from database"""
        try:
            stats = await self.queue_service.get_queue_stats()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get queue stats: {str(e)}"
            )
    
    async def get_next_review_for_expert(self, expert_id: str) -> Optional[ExpertReviewItemResponse]:
        """Get next review for expert using FIFO ordering"""
        try:
            review = await self.queue_service.get_next_review(expert_id)
            return review
            
        except Exception as e:
            logger.error(f"Failed to get next review for expert: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get next review: {str(e)}"
            )
    
    async def assign_to_expert(self, review_id: str, expert_id: str) -> dict:
        """Assign review to expert"""
        try:
            success = await self.queue_service.mark_in_review(review_id, expert_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Review not found or not available")
            
            logger.info(f"Review {review_id} assigned to expert {expert_id}")
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign review to expert: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to assign review: {str(e)}"
            )
    
    async def update_review_status(
        self, 
        review_id: str, 
        status: ReviewStatus, 
        expert_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """Update review status with proper state transitions"""
        try:
            success = await self.queue_service.update_review_status(
                review_id, status, expert_id, notes
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Review not found or invalid status transition")
            
            logger.info(f"Review {review_id} status updated to {status.value}")
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update review status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update review status: {str(e)}"
            )
    
    async def get_review_details(self, review_id: str, include_content: bool = False) -> ExpertReviewItemResponse:
        """Get detailed information for a specific review"""
        try:
            review = await self.queue_service.get_review_by_id(review_id, include_content)
            
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")
            
            return review
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get review details: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get review details: {str(e)}"
            )
    
    async def complete_expert_review(
        self, 
        submission: ExpertAnalysisSubmission,
        expert_id: str
    ) -> ExpertAnalysisResponse:
        """Complete expert review and update status"""
        try:
            response = await self.queue_service.complete_review(submission, expert_id)
            
            logger.info(f"Expert review completed: {submission.review_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to complete expert review: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to complete expert review: {str(e)}"
            )
    
    async def cancel_review(self, review_id: str) -> dict:
        """Cancel expert review"""
        try:
            success = await self.queue_service.update_review_status(
                review_id, ReviewStatus.CANCELLED
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Review not found or cannot be cancelled")
            
            logger.info(f"Review {review_id} cancelled")
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel review: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel review: {str(e)}"
            )


# Global instance
expert_queue_controller = ExpertQueueController()