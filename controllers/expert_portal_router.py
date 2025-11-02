"""
Expert Portal Router for Human-in-the-Loop System
FastAPI router for expert authentication and dashboard endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query, Body
from pydantic import BaseModel

from controllers.expert_auth_controller import expert_auth_controller
from controllers.expert_queue_controller import expert_queue_controller
from models.auth_models import FirebaseTokenRequest
from models.expert_queue_models import (
    ExpertAnalysisSubmission, ReviewStatus, Priority,
    PaginationParams, QueueFilters
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/expert", tags=["Expert Portal"])


# Request/Response Models
class ExpertLoginRequest(BaseModel):
    token: str


class ExpertRoleAssignmentRequest(BaseModel):
    user_id: str
    role: str
    specializations: Optional[List[str]] = None


class PermissionCheckRequest(BaseModel):
    permission: str


# Authentication Endpoints
@router.post("/auth/login")
async def expert_login(request: ExpertLoginRequest):
    """
    Expert login endpoint with role verification.
    Authenticates expert using Firebase token and verifies expert role.
    """
    try:
        token_request = FirebaseTokenRequest(token=request.token)
        result = await expert_auth_controller.authenticate_expert(token_request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Expert login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Expert login failed"
        )


@router.get("/auth/verify")
async def verify_expert_token(request: Request):
    """
    Verify expert token and return expert information.
    Used for maintaining expert session state.
    """
    try:
        result = await expert_auth_controller.verify_expert_token(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Token verification failed"
        )


@router.get("/auth/profile")
async def get_expert_profile(request: Request):
    """
    Get expert profile information.
    Returns expert details, role, permissions, and statistics.
    """
    try:
        result = await expert_auth_controller.get_expert_profile(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get expert profile"
        )


@router.post("/auth/check-permission")
async def check_expert_permission(request: Request, permission_request: PermissionCheckRequest):
    """
    Check if expert has specific permission.
    Used for role-based access control in the frontend.
    """
    try:
        result = await expert_auth_controller.check_expert_permission(
            request, permission_request.permission
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permission check error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Permission check failed"
        )


# Queue Management Endpoints
@router.get("/queue/next")
async def get_next_review(request: Request):
    """
    Get next document for expert review using FIFO ordering.
    Assigns the oldest pending review to the authenticated expert.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        expert_id = expert_info['uid']
        
        # Check review permission
        has_permission = await expert_auth_controller.check_expert_permission(
            request, "review_documents"
        )
        
        if not has_permission['has_permission']:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for document review"
            )
        
        # Get next review
        review = await expert_queue_controller.get_next_review_for_expert(expert_id)
        
        if not review:
            return {
                'success': True,
                'review': None,
                'message': 'No pending reviews available'
            }
        
        return {
            'success': True,
            'review': review,
            'message': 'Review assigned successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get next review error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get next review"
        )


@router.get("/queue/list")
async def get_expert_queue(
    request: Request,
    status: Optional[ReviewStatus] = Query(None),
    priority: Optional[Priority] = Query(None),
    assigned_expert_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    """
    Get expert review queue with filtering and pagination.
    Shows queue of pending reviews in first-come-first-serve order.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        
        # Get queue items
        result = await expert_queue_controller.get_expert_requests(
            status=status,
            priority=priority,
            assigned_expert_id=assigned_expert_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            'success': True,
            'queue': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get queue error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get expert queue"
        )


@router.get("/queue/stats")
async def get_queue_statistics(request: Request):
    """
    Get expert queue statistics.
    Returns counts by status, average completion time, and expert workload.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        
        # Get queue stats
        stats = await expert_queue_controller.get_queue_stats()
        
        return {
            'success': True,
            'stats': stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get queue stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get queue statistics"
        )


@router.get("/review/{review_id}")
async def get_review_details(request: Request, review_id: str):
    """
    Get detailed information for a specific review.
    Displays original document, AI analysis, and confidence breakdown.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        
        # Check review permission
        has_permission = await expert_auth_controller.check_expert_permission(
            request, "review_documents"
        )
        
        if not has_permission['has_permission']:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for document review"
            )
        
        # Get review details with content
        review = await expert_queue_controller.get_review_details(
            review_id, include_content=True
        )
        
        return {
            'success': True,
            'review': review,
            'expert_info': {
                'uid': expert_info['uid'],
                'role': expert_info['role'],
                'permissions': expert_info['permissions']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get review details error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get review details"
        )


@router.get("/review/{review_id}/preview")
async def preview_review_details(request: Request, review_id: str):
    """
    Get preview of review details without full document content.
    Used for quick view in dashboard.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        
        # Get review details without full content
        review = await expert_queue_controller.get_review_details(
            review_id, include_content=False
        )
        
        # Add summary information
        preview_data = {
            'review_id': review.review_id,
            'user_email': review.user_email,
            'confidence_score': review.confidence_score,
            'status': review.status,
            'priority': review.priority,
            'created_at': review.created_at,
            'document_type': review.document_type,
            'estimated_completion_hours': review.estimated_completion_hours,
            'ai_analysis_summary': {
                'summary': review.ai_analysis.get('summary', ''),
                'overall_risk': review.ai_analysis.get('overall_risk', {}),
                'clause_count': len(review.ai_analysis.get('analysis_results', [])),
                'processing_time': review.ai_analysis.get('processing_time', 0)
            },
            'confidence_breakdown': review.confidence_breakdown
        }
        
        return {
            'success': True,
            'preview': preview_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview review details error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get review preview"
        )


@router.post("/review/{review_id}/assign")
async def assign_review_to_expert(request: Request, review_id: str):
    """
    Assign review to authenticated expert.
    Marks document as IN_REVIEW to prevent duplicate assignments.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        expert_id = expert_info['uid']
        
        # Check review permission
        has_permission = await expert_auth_controller.check_expert_permission(
            request, "review_documents"
        )
        
        if not has_permission['has_permission']:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for document review"
            )
        
        # Assign review
        result = await expert_queue_controller.assign_to_expert(review_id, expert_id)
        
        return {
            'success': True,
            'message': f'Review {review_id} assigned to expert {expert_id}'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign review error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assign review"
        )


@router.post("/review/{review_id}/complete")
async def complete_expert_review(
    request: Request, 
    review_id: str, 
    analysis_submission: ExpertAnalysisSubmission
):
    """
    Complete expert review and submit analysis.
    Validates completeness and updates status to COMPLETED.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        expert_id = expert_info['uid']
        
        # Check submit permission
        has_permission = await expert_auth_controller.check_expert_permission(
            request, "submit_analysis"
        )
        
        if not has_permission['has_permission']:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to submit analysis"
            )
        
        # Validate review_id matches
        if analysis_submission.review_id != review_id:
            raise HTTPException(
                status_code=400,
                detail="Review ID mismatch"
            )
        
        # Complete review
        result = await expert_queue_controller.complete_expert_review(
            analysis_submission, expert_id
        )
        
        return {
            'success': True,
            'analysis': result,
            'message': f'Expert review completed for {review_id}'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete review error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to complete expert review"
        )


@router.post("/review/{review_id}/cancel")
async def cancel_expert_review(request: Request, review_id: str):
    """
    Cancel expert review.
    Returns review to pending status or cancels it entirely.
    """
    try:
        # Verify expert authentication
        verification_result = await expert_auth_controller.verify_expert_token(request)
        expert_info = verification_result['expert']
        
        # Cancel review
        result = await expert_queue_controller.cancel_review(review_id)
        
        return {
            'success': True,
            'message': f'Review {review_id} cancelled'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel review error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel review"
        )


# Admin Endpoints
@router.get("/admin/experts")
async def list_all_experts(request: Request):
    """
    List all expert users (admin only).
    Returns expert accounts with roles and statistics.
    """
    try:
        result = await expert_auth_controller.list_all_experts(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List experts error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list experts"
        )


@router.post("/admin/assign-role")
async def assign_expert_role(request: Request, role_request: ExpertRoleAssignmentRequest):
    """
    Assign expert role to user (admin only).
    Creates expert account with proper role assignment.
    """
    try:
        result = await expert_auth_controller.assign_expert_role(
            request,
            role_request.user_id,
            role_request.role,
            role_request.specializations
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign role error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assign expert role"
        )


@router.delete("/admin/remove-role/{user_id}")
async def remove_expert_role(request: Request, user_id: str):
    """
    Remove expert role from user (admin only).
    Deactivates expert account and removes permissions.
    """
    try:
        result = await expert_auth_controller.remove_expert_role(request, user_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove role error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to remove expert role"
        )


@router.get("/admin/roles")
async def get_available_roles():
    """
    Get list of available expert roles and their permissions.
    Used for role assignment interface.
    """
    try:
        result = await expert_auth_controller.get_available_roles()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get roles error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get available roles"
        )


# Health Check
@router.get("/health")
async def expert_portal_health():
    """
    Expert portal health check endpoint.
    """
    return {
        'success': True,
        'service': 'Expert Portal',
        'status': 'healthy',
        'timestamp': logger.info("Expert portal health check")
    }