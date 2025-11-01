"""
Expert Queue Controller for Human-in-the-Loop System
Manages expert review requests and queue operations
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExpertReviewSubmission(BaseModel):
    document_id: str
    user_email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    document_type: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_breakdown: dict
    document_text: str
    ai_analysis: dict


class ExpertReviewRequest(BaseModel):
    id: str
    document_id: str
    user_email: str
    document_type: str
    confidence_score: float
    confidence_breakdown: dict
    document_text: str
    ai_analysis: dict
    status: str = "pending"  # pending, assigned, in_progress, completed, cancelled
    priority: str = "medium"  # low, medium, high, urgent
    assigned_expert: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[str] = None
    expert_notes: Optional[str] = None


class ExpertQueueStats(BaseModel):
    total_requests: int
    pending_requests: int
    in_progress_requests: int
    completed_requests: int
    average_completion_time: float
    expert_workload: dict


class ExpertQueueController:
    """Controller for expert review queue operations"""
    
    def __init__(self):
        # In-memory storage for demo - in production, use database
        self.expert_requests = {}
        self.queue_stats = ExpertQueueStats(
            total_requests=0,
            pending_requests=0,
            in_progress_requests=0,
            completed_requests=0,
            average_completion_time=36.0,  # hours
            expert_workload={}
        )
    
    async def submit_for_expert_review(self, submission: ExpertReviewSubmission) -> dict:
        """Submit document for expert review"""
        try:
            request_id = str(uuid.uuid4())
            
            # Determine priority based on confidence score
            if submission.confidence_score < 0.3:
                priority = "urgent"
                estimated_hours = 12
            elif submission.confidence_score < 0.4:
                priority = "high"
                estimated_hours = 24
            elif submission.confidence_score < 0.5:
                priority = "medium"
                estimated_hours = 36
            else:
                priority = "low"
                estimated_hours = 48
            
            estimated_completion = datetime.now() + timedelta(hours=estimated_hours)
            
            # Create expert review request
            expert_request = ExpertReviewRequest(
                id=request_id,
                document_id=submission.document_id,
                user_email=submission.user_email,
                document_type=submission.document_type,
                confidence_score=submission.confidence_score,
                confidence_breakdown=submission.confidence_breakdown,
                document_text=submission.document_text,
                ai_analysis=submission.ai_analysis,
                priority=priority,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                estimated_completion=f"{estimated_hours} hours"
            )
            
            # Store request
            self.expert_requests[request_id] = expert_request
            
            # Update stats
            self.queue_stats.total_requests += 1
            self.queue_stats.pending_requests += 1
            
            logger.info(f"Expert review request submitted: {request_id}, priority: {priority}")
            
            return {
                "success": True,
                "request_id": request_id,
                "estimated_completion": f"{estimated_hours} hours"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit expert review request: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit for expert review: {str(e)}"
            )
    
    async def get_expert_requests(
        self, 
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        """Get expert review requests with pagination and filtering"""
        try:
            # Filter requests
            filtered_requests = []
            for request in self.expert_requests.values():
                if status is None or request.status == status:
                    filtered_requests.append(request)
            
            # Sort by created_at descending
            filtered_requests.sort(key=lambda x: x.created_at, reverse=True)
            
            # Pagination
            total = len(filtered_requests)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_requests = filtered_requests[start_idx:end_idx]
            
            return {
                "requests": [req.dict() for req in paginated_requests],
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get expert requests: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get expert requests: {str(e)}"
            )
    
    async def get_queue_stats(self) -> ExpertQueueStats:
        """Get expert queue statistics"""
        try:
            # Recalculate stats from current requests
            total = len(self.expert_requests)
            pending = sum(1 for req in self.expert_requests.values() if req.status == "pending")
            in_progress = sum(1 for req in self.expert_requests.values() if req.status in ["assigned", "in_progress"])
            completed = sum(1 for req in self.expert_requests.values() if req.status == "completed")
            
            self.queue_stats.total_requests = total
            self.queue_stats.pending_requests = pending
            self.queue_stats.in_progress_requests = in_progress
            self.queue_stats.completed_requests = completed
            
            return self.queue_stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get queue stats: {str(e)}"
            )
    
    async def assign_to_expert(self, request_id: str, expert_id: str) -> dict:
        """Assign request to expert"""
        try:
            if request_id not in self.expert_requests:
                raise HTTPException(status_code=404, detail="Request not found")
            
            request = self.expert_requests[request_id]
            request.assigned_expert = expert_id
            request.status = "assigned"
            request.updated_at = datetime.now()
            
            # Update stats
            self.queue_stats.pending_requests -= 1
            self.queue_stats.in_progress_requests += 1
            
            logger.info(f"Request {request_id} assigned to expert {expert_id}")
            
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign request to expert: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to assign request: {str(e)}"
            )
    
    async def update_request_status(self, request_id: str, status: str, notes: Optional[str] = None) -> dict:
        """Update request status"""
        try:
            if request_id not in self.expert_requests:
                raise HTTPException(status_code=404, detail="Request not found")
            
            request = self.expert_requests[request_id]
            old_status = request.status
            request.status = status
            request.updated_at = datetime.now()
            
            if notes:
                request.expert_notes = notes
            
            # Update stats based on status change
            if old_status == "pending" and status in ["assigned", "in_progress"]:
                self.queue_stats.pending_requests -= 1
                self.queue_stats.in_progress_requests += 1
            elif old_status in ["assigned", "in_progress"] and status == "completed":
                self.queue_stats.in_progress_requests -= 1
                self.queue_stats.completed_requests += 1
            elif old_status in ["assigned", "in_progress"] and status == "cancelled":
                self.queue_stats.in_progress_requests -= 1
            elif old_status == "pending" and status == "cancelled":
                self.queue_stats.pending_requests -= 1
            
            logger.info(f"Request {request_id} status updated from {old_status} to {status}")
            
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update request status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update request status: {str(e)}"
            )
    
    async def get_request_details(self, request_id: str) -> ExpertReviewRequest:
        """Get detailed information for a specific request"""
        try:
            if request_id not in self.expert_requests:
                raise HTTPException(status_code=404, detail="Request not found")
            
            return self.expert_requests[request_id]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get request details: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get request details: {str(e)}"
            )
    
    async def cancel_request(self, request_id: str) -> dict:
        """Cancel expert review request"""
        try:
            if request_id not in self.expert_requests:
                raise HTTPException(status_code=404, detail="Request not found")
            
            request = self.expert_requests[request_id]
            
            if request.status in ["completed", "cancelled"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel request with status: {request.status}"
                )
            
            old_status = request.status
            request.status = "cancelled"
            request.updated_at = datetime.now()
            
            # Update stats
            if old_status == "pending":
                self.queue_stats.pending_requests -= 1
            elif old_status in ["assigned", "in_progress"]:
                self.queue_stats.in_progress_requests -= 1
            
            logger.info(f"Request {request_id} cancelled")
            
            return {"success": True}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel request: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel request: {str(e)}"
            )


# Global instance
expert_queue_controller = ExpertQueueController()