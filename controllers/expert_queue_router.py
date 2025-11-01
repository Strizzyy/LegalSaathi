"""
Expert Queue Router for Human-in-the-Loop System
FastAPI routes for expert review queue management
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from controllers.expert_queue_controller import (
    expert_queue_controller, 
    ExpertReviewSubmission
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/api/expert-queue/submit")
async def submit_for_expert_review(submission: ExpertReviewSubmission):
    """Submit document for expert review"""
    try:
        result = await expert_queue_controller.submit_for_expert_review(submission)
        return result
    except Exception as e:
        logger.error(f"Expert review submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/expert-queue/requests")
async def get_expert_requests(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Get expert review requests (admin only)"""
    try:
        # TODO: Add admin authentication check
        result = await expert_queue_controller.get_expert_requests(status, page, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to get expert requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/expert-queue/stats")
async def get_queue_stats():
    """Get expert queue statistics (admin only)"""
    try:
        # TODO: Add admin authentication check
        result = await expert_queue_controller.get_queue_stats()
        return result
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/expert-queue/assign/{request_id}")
async def assign_to_expert(request_id: str, assignment_data: dict):
    """Assign request to expert (admin only)"""
    try:
        # TODO: Add admin authentication check
        expert_id = assignment_data.get("expert_id")
        if not expert_id:
            raise HTTPException(status_code=400, detail="expert_id is required")
        
        result = await expert_queue_controller.assign_to_expert(request_id, expert_id)
        return result
    except Exception as e:
        logger.error(f"Failed to assign request to expert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/admin/expert-queue/status/{request_id}")
async def update_request_status(request_id: str, status_data: dict):
    """Update request status (admin only)"""
    try:
        # TODO: Add admin authentication check
        status = status_data.get("status")
        notes = status_data.get("notes")
        
        if not status:
            raise HTTPException(status_code=400, detail="status is required")
        
        result = await expert_queue_controller.update_request_status(request_id, status, notes)
        return result
    except Exception as e:
        logger.error(f"Failed to update request status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/expert-queue/request/{request_id}")
async def get_request_details(request_id: str):
    """Get request details (admin/expert only)"""
    try:
        # TODO: Add admin/expert authentication check
        result = await expert_queue_controller.get_request_details(request_id)
        return result.dict()
    except Exception as e:
        logger.error(f"Failed to get request details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/expert-queue/cancel/{request_id}")
async def cancel_request(request_id: str):
    """Cancel expert review request"""
    try:
        # TODO: Add user authentication check (user should own the request)
        result = await expert_queue_controller.cancel_request(request_id)
        return result
    except Exception as e:
        logger.error(f"Failed to cancel request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check for expert queue system
@router.get("/api/expert-queue/health")
async def expert_queue_health():
    """Health check for expert queue system"""
    try:
        stats = await expert_queue_controller.get_queue_stats()
        return {
            "status": "healthy",
            "total_requests": stats.total_requests,
            "pending_requests": stats.pending_requests,
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
    except Exception as e:
        logger.error(f"Expert queue health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }