"""
Expert Review Email Controller
Handles API endpoints for expert review email notifications and tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, EmailStr, Field

from models.expert_queue_models import (
    ExpertAnalysisResponse, ReviewStatus, ExpertReviewItemResponse
)
from models.email_models import EmailSendResponse
from services.expert_review_email_service import ExpertReviewEmailService
from services.expert_pdf_generator import ExpertPDFGenerator
from services.review_tracking_service import ReviewTrackingService
from services.feedback_service import FeedbackService
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expert-review", tags=["Expert Review Email"])


# Dependency function to get current user from request
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request state (set by auth middleware)"""
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user
    else:
        # Return anonymous user for non-authenticated requests
        return {
            'uid': 'anonymous',
            'email': None,
            'admin': False,
            'expert_role': None
        }

# Initialize services
email_service = ExpertReviewEmailService()
pdf_generator = ExpertPDFGenerator()
tracking_service = ReviewTrackingService()
feedback_service = FeedbackService()


# Request/Response Models
class ReviewQueuedNotificationRequest(BaseModel):
    user_email: EmailStr
    review_id: str
    estimated_time_hours: int = Field(default=24, ge=1, le=168)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ExpertResultsNotificationRequest(BaseModel):
    user_email: EmailStr
    expert_analysis: Dict[str, Any]
    review_id: str
    expert_id: str
    expert_name: str = "Legal Expert"
    expert_credentials: str = "J.D., Licensed Attorney"


class StatusUpdateNotificationRequest(BaseModel):
    user_email: EmailStr
    review_id: str
    status: ReviewStatus
    expert_name: Optional[str] = None


class FeedbackSubmissionRequest(BaseModel):
    review_id: str
    overall_rating: int = Field(ge=1, le=5)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    clarity_rating: Optional[int] = Field(None, ge=1, le=5)
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5)
    usefulness_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    would_recommend: bool = True


class TrackingResponse(BaseModel):
    review_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: Dict[str, Any]
    timeline: list
    expert_info: Optional[Dict[str, Any]] = None


@router.post("/send-queued-notification")
async def send_review_queued_notification(
    request: ReviewQueuedNotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> EmailSendResponse:
    """Send notification that document is queued for expert review"""
    
    try:
        logger.info(f"Sending review queued notification for {request.review_id}")
        
        response = await email_service.send_review_queued_notification(
            user_email=request.user_email,
            review_id=request.review_id,
            estimated_time_hours=request.estimated_time_hours,
            confidence_score=request.confidence_score,
            user_id=current_user.get('uid', request.user_email)
        )
        
        if response.success:
            logger.info(f"Review queued notification sent successfully to {request.user_email}")
        else:
            logger.error(f"Failed to send review queued notification: {response.error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending review queued notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/send-expert-results")
async def send_expert_results_notification(
    request: ExpertResultsNotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> EmailSendResponse:
    """Send expert-reviewed analysis results to user"""
    
    try:
        logger.info(f"Sending expert results notification for {request.review_id}")
        
        # Create ExpertAnalysisResponse object
        expert_analysis = ExpertAnalysisResponse(
            review_id=request.review_id,
            expert_id=request.expert_id,
            expert_analysis=request.expert_analysis,
            completed_at=datetime.utcnow(),
            review_duration_minutes=request.expert_analysis.get('review_duration_minutes', 60),
            confidence_improvement=request.expert_analysis.get('confidence_improvement', 0.2)
        )
        
        # Generate expert-certified PDF
        pdf_content = pdf_generator.generate_expert_certified_report(
            expert_analysis=expert_analysis,
            original_ai_analysis=None,  # Would need to fetch from database
            review_id=request.review_id,
            expert_name=request.expert_name,
            expert_credentials=request.expert_credentials
        )
        
        # Send email with PDF attachment
        response = await email_service.send_expert_analysis_results(
            user_email=request.user_email,
            expert_analysis=expert_analysis,
            pdf_content=pdf_content,
            user_id=current_user.get('uid', request.user_email)
        )
        
        if response.success:
            logger.info(f"Expert results notification sent successfully to {request.user_email}")
        else:
            logger.error(f"Failed to send expert results notification: {response.error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending expert results notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send results: {str(e)}")


@router.post("/send-status-update")
async def send_status_update_notification(
    request: StatusUpdateNotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> EmailSendResponse:
    """Send review status update notification to user"""
    
    try:
        logger.info(f"Sending status update notification for {request.review_id}")
        
        response = await email_service.send_review_status_update(
            user_email=request.user_email,
            review_id=request.review_id,
            status=request.status,
            expert_name=request.expert_name,
            user_id=current_user.get('uid', request.user_email)
        )
        
        if response.success:
            logger.info(f"Status update notification sent successfully to {request.user_email}")
        else:
            logger.error(f"Failed to send status update notification: {response.error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending status update notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send update: {str(e)}")


@router.get("/track/{review_id}")
async def track_review_status(
    review_id: str = Path(..., description="Review ID to track")
) -> TrackingResponse:
    """Get current status and progress of a review"""
    
    try:
        logger.info(f"Tracking review status for {review_id}")
        
        review_data = tracking_service.get_review_status(review_id)
        
        if not review_data:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return TrackingResponse(
            review_id=review_data['review_id'],
            status=review_data['status'],
            created_at=review_data['created_at'],
            updated_at=review_data['updated_at'],
            progress=review_data['progress'],
            timeline=review_data['timeline'],
            expert_info=review_data.get('expert_info')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking review {review_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track review: {str(e)}")


@router.get("/user-reviews")
async def get_user_reviews(
    user_email: EmailStr = Query(..., description="User email to get reviews for"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all reviews for a specific user"""
    
    try:
        # Verify user can access these reviews
        if current_user.get('email') != user_email and not current_user.get('admin', False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"Getting reviews for user {user_email}")
        
        reviews = tracking_service.get_user_reviews(user_email, limit)
        
        return {
            'user_email': user_email,
            'reviews': reviews,
            'total_count': len(reviews)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user reviews for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")


@router.get("/queue-stats")
async def get_queue_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get overall queue statistics and metrics"""
    
    try:
        logger.info("Getting queue statistics")
        
        stats = tracking_service.get_queue_statistics()
        
        return {
            'statistics': stats.dict(),
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submit feedback for an expert review"""
    
    try:
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(status_code=401, detail="User email required")
        
        logger.info(f"Submitting feedback for review {request.review_id}")
        
        result = feedback_service.submit_feedback(
            review_id=request.review_id,
            user_email=user_email,
            overall_rating=request.overall_rating,
            accuracy_rating=request.accuracy_rating,
            clarity_rating=request.clarity_rating,
            timeliness_rating=request.timeliness_rating,
            usefulness_rating=request.usefulness_rating,
            feedback_text=request.feedback_text,
            would_recommend=request.would_recommend
        )
        
        if result['success']:
            logger.info(f"Feedback submitted successfully for review {request.review_id}")
        else:
            logger.error(f"Failed to submit feedback: {result.get('error')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/feedback/{review_id}")
async def get_feedback(
    review_id: str = Path(..., description="Review ID to get feedback for"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get existing feedback for a review"""
    
    try:
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(status_code=401, detail="User email required")
        
        logger.info(f"Getting feedback for review {review_id}")
        
        feedback = feedback_service.get_feedback(review_id, user_email)
        
        if not feedback:
            return {'feedback': None, 'message': 'No feedback found'}
        
        return {'feedback': feedback}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback for {review_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@router.get("/feedback-stats")
async def get_feedback_statistics(
    expert_id: Optional[str] = Query(None, description="Expert ID for specific stats"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get feedback statistics (admin or expert only)"""
    
    try:
        # Check permissions
        user_role = current_user.get('expert_role')
        is_admin = current_user.get('admin', False)
        
        if not (is_admin or user_role in ['legal_expert', 'senior_expert', 'admin']):
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"Getting feedback statistics for expert {expert_id}")
        
        if expert_id:
            stats = feedback_service.get_expert_feedback_summary(expert_id)
        else:
            stats = feedback_service.get_overall_feedback_stats()
        
        return {
            'statistics': stats,
            'generated_at': datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/feedback-report")
async def generate_feedback_report(
    expert_id: Optional[str] = Query(None, description="Expert ID for specific report"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate comprehensive feedback report (admin only)"""
    
    try:
        # Check admin permissions
        if not current_user.get('admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        logger.info(f"Generating feedback report for expert {expert_id}")
        
        report = feedback_service.generate_feedback_report(expert_id)
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feedback report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for expert review email service"""
    
    try:
        email_available = email_service.is_available()
        
        return {
            'status': 'healthy' if email_available else 'degraded',
            'email_service_available': email_available,
            'timestamp': datetime.utcnow(),
            'services': {
                'expert_email_service': email_available,
                'pdf_generator': True,  # Always available
                'tracking_service': True,
                'feedback_service': True
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow()
        }