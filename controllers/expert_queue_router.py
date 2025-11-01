"""
FastAPI Router for Expert Queue Management API Endpoints
Provides REST API for human-in-the-loop expert review system
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel

from controllers.expert_queue_controller import ExpertQueueController
from models.expert_queue_models import (
    ExpertReviewSubmission, ExpertReviewResponse, ExpertReviewItemResponse,
    ExpertAnalysisSubmission, ExpertAnalysisResponse, QueueStatsResponse,
    QueueResponse, ReviewStatus, Priority
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/expert-queue", tags=["Expert Queue"])

# Initialize controller
expert_queue_controller = ExpertQueueController()


class SubmitReviewRequest(BaseModel):
    """Request model for submitting document for expert review"""
    document_content: str
    ai_analysis: dict
    user_email: str
    confidence_score: float
    confidence_breakdown: dict
    document_type: Optional[str] = None


@router.post("/submit", response_model=ExpertReviewResponse)
async def submit_for_expert_review(request: SubmitReviewRequest):
    """
    Submit document for expert review.
    
    - **document_content**: The document text content
    - **ai_analysis**: AI analysis results
    - **user_email**: User's email address
    - **confidence_score**: AI confidence score (0.0 to 1.0)
    - **confidence_breakdown**: Detailed confidence breakdown
    - **document_type**: Optional document type classification
    """
    try:
        response = await expert_queue_controller.submit_for_expert_review(
            document_content=request.document_content,
            ai_analysis=request.ai_analysis,
            user_email=request.user_email,
            confidence_score=request.confidence_score,
            confidence_breakdown=request.confidence_breakdown,
            document_type=request.document_type
        )
        return response
    except Exception as e:
        logger.error(f"Error submitting for expert review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue", response_model=QueueResponse)
async def get_queue_items(
    status: Optional[ReviewStatus] = Query(None, description="Filter by review status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    assigned_expert_id: Optional[str] = Query(None, description="Filter by assigned expert"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Get expert review queue items with filtering and pagination.
    
    - **status**: Filter by review status (pending, in_review, completed, cancelled)
    - **priority**: Filter by priority (low, medium, high, urgent)
    - **assigned_expert_id**: Filter by assigned expert ID
    - **page**: Page number for pagination
    - **limit**: Number of items per page
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order (asc or desc)
    """
    try:
        response = await expert_queue_controller.get_expert_requests(
            status=status,
            priority=priority,
            assigned_expert_id=assigned_expert_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return response
    except Exception as e:
        logger.error(f"Error getting queue items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_statistics():
    """
    Get expert queue statistics.
    
    Returns counts by status, average completion time, and expert workload.
    """
    try:
        stats = await expert_queue_controller.get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next-review/{expert_id}", response_model=Optional[ExpertReviewItemResponse])
async def get_next_review_for_expert(expert_id: str):
    """
    Get next review for expert using FIFO ordering.
    
    - **expert_id**: Expert's unique identifier
    
    Returns the oldest pending review and assigns it to the expert.
    """
    try:
        review = await expert_queue_controller.get_next_review_for_expert(expert_id)
        return review
    except Exception as e:
        logger.error(f"Error getting next review for expert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/{review_id}", response_model=ExpertReviewItemResponse)
async def get_review_details(
    review_id: str,
    include_content: bool = Query(False, description="Include document content in response")
):
    """
    Get detailed information for a specific review.
    
    - **review_id**: Unique review identifier
    - **include_content**: Whether to include document content (for assigned experts)
    """
    try:
        review = await expert_queue_controller.get_review_details(review_id, include_content)
        return review
    except Exception as e:
        logger.error(f"Error getting review details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/review/{review_id}/assign/{expert_id}")
async def assign_review_to_expert(review_id: str, expert_id: str):
    """
    Assign review to expert.
    
    - **review_id**: Unique review identifier
    - **expert_id**: Expert's unique identifier
    """
    try:
        result = await expert_queue_controller.assign_to_expert(review_id, expert_id)
        return result
    except Exception as e:
        logger.error(f"Error assigning review to expert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/review/{review_id}/status")
async def update_review_status(
    review_id: str,
    status: ReviewStatus = Body(..., description="New review status"),
    expert_id: Optional[str] = Body(None, description="Expert ID (if assigning)"),
    notes: Optional[str] = Body(None, description="Optional notes")
):
    """
    Update review status with proper state transitions.
    
    - **review_id**: Unique review identifier
    - **status**: New status (pending, in_review, completed, cancelled)
    - **expert_id**: Expert ID if assigning review
    - **notes**: Optional notes about the status change
    """
    try:
        result = await expert_queue_controller.update_review_status(
            review_id, status, expert_id, notes
        )
        return result
    except Exception as e:
        logger.error(f"Error updating review status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/complete", response_model=ExpertAnalysisResponse)
async def complete_expert_review(
    submission: ExpertAnalysisSubmission,
    expert_id: str = Query(..., description="Expert's unique identifier")
):
    """
    Complete expert review and submit analysis.
    
    - **submission**: Expert analysis submission with review results
    - **expert_id**: Expert's unique identifier
    """
    try:
        response = await expert_queue_controller.complete_expert_review(submission, expert_id)
        return response
    except Exception as e:
        logger.error(f"Error completing expert review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/review/{review_id}/cancel")
async def cancel_review(review_id: str):
    """
    Cancel expert review.
    
    - **review_id**: Unique review identifier
    """
    try:
        result = await expert_queue_controller.cancel_review(review_id)
        return result
    except Exception as e:
        logger.error(f"Error cancelling review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for expert queue service"""
    try:
        stats = await expert_queue_controller.get_queue_stats()
        return {
            "status": "healthy",
            "service": "expert_queue",
            "queue_items": stats.total_items,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")