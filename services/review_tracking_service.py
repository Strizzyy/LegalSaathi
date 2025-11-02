"""
Review Tracking Service for Human-in-the-Loop System
Allows users to track status of their expert reviews via unique review ID
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.expert_queue_models import (
    ExpertReviewItem, ReviewStatus, ExpertUser, ReviewMetrics,
    ExpertReviewItemResponse, QueueStatsResponse
)
from services.expert_queue_service import ExpertQueueService

logger = logging.getLogger(__name__)


class ReviewTrackingService:
    """Service for tracking expert review status and progress"""
    
    def __init__(self):
        self.queue_service = ExpertQueueService()
        logger.info("Review Tracking Service initialized")
    
    def get_review_status(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get current status and details of a review by ID"""
        try:
            with self.queue_service.get_db() as session:
                review = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id
                ).first()
                
                if not review:
                    return None
                
                # Get expert info if assigned
                expert_info = None
                if review.assigned_expert_id:
                    expert = session.query(ExpertUser).filter(
                        ExpertUser.uid == review.assigned_expert_id
                    ).first()
                    if expert:
                        expert_info = {
                            'name': expert.display_name or 'Legal Expert',
                            'specializations': expert.specializations,
                            'reviews_completed': expert.reviews_completed
                        }
                
                # Calculate progress and estimates
                progress_info = self._calculate_progress(review)
                
                return {
                    'review_id': review.review_id,
                    'status': review.status,
                    'created_at': review.created_at,
                    'updated_at': review.updated_at,
                    'assigned_at': review.assigned_at,
                    'completed_at': review.completed_at,
                    'estimated_completion_hours': review.estimated_completion_hours,
                    'confidence_score': review.confidence_score,
                    'priority': review.priority,
                    'document_type': review.document_type,
                    'expert_info': expert_info,
                    'progress': progress_info,
                    'timeline': self._generate_timeline(review)
                }
                
        except Exception as e:
            logger.error(f"Failed to get review status for {review_id}: {e}")
            return None
    
    def get_user_reviews(self, user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all reviews for a specific user email"""
        try:
            with self.queue_service.get_db() as session:
                reviews = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.user_email == user_email.lower()
                ).order_by(ExpertReviewItem.created_at.desc()).limit(limit).all()
                
                result = []
                for review in reviews:
                    review_data = {
                        'review_id': review.review_id,
                        'status': review.status,
                        'created_at': review.created_at,
                        'updated_at': review.updated_at,
                        'completed_at': review.completed_at,
                        'confidence_score': review.confidence_score,
                        'priority': review.priority,
                        'document_type': review.document_type,
                        'progress': self._calculate_progress(review)
                    }
                    result.append(review_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get user reviews for {user_email}: {e}")
            return []
    
    def get_queue_statistics(self) -> QueueStatsResponse:
        """Get overall queue statistics and metrics"""
        try:
            with self.queue_service.get_db() as session:
                # Count items by status
                total_items = session.query(ExpertReviewItem).count()
                pending_items = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.PENDING.value
                ).count()
                in_review_items = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.IN_REVIEW.value
                ).count()
                completed_items = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.COMPLETED.value
                ).count()
                cancelled_items = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.CANCELLED.value
                ).count()
                
                # Calculate average completion time
                completed_reviews = session.query(ExpertReviewItem).filter(
                    and_(
                        ExpertReviewItem.status == ReviewStatus.COMPLETED.value,
                        ExpertReviewItem.completed_at.isnot(None),
                        ExpertReviewItem.created_at.isnot(None)
                    )
                ).all()
                
                avg_completion_time = 0.0
                if completed_reviews:
                    total_hours = sum([
                        (review.completed_at - review.created_at).total_seconds() / 3600
                        for review in completed_reviews
                    ])
                    avg_completion_time = total_hours / len(completed_reviews)
                
                # Get oldest pending item
                oldest_pending = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.PENDING.value
                ).order_by(ExpertReviewItem.created_at.asc()).first()
                
                # Expert workload
                expert_workload = {}
                active_assignments = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.IN_REVIEW.value
                ).all()
                
                for assignment in active_assignments:
                    expert_id = assignment.assigned_expert_id
                    if expert_id:
                        expert_workload[expert_id] = expert_workload.get(expert_id, 0) + 1
                
                return QueueStatsResponse(
                    total_items=total_items,
                    pending_items=pending_items,
                    in_review_items=in_review_items,
                    completed_items=completed_items,
                    cancelled_items=cancelled_items,
                    average_completion_time_hours=avg_completion_time,
                    oldest_pending_item=oldest_pending.created_at if oldest_pending else None,
                    expert_workload=expert_workload
                )
                
        except Exception as e:
            logger.error(f"Failed to get queue statistics: {e}")
            return QueueStatsResponse(
                total_items=0, pending_items=0, in_review_items=0,
                completed_items=0, cancelled_items=0,
                average_completion_time_hours=0.0,
                oldest_pending_item=None, expert_workload={}
            )
    
    def update_review_status(
        self,
        review_id: str,
        new_status: ReviewStatus,
        expert_id: Optional[str] = None,
        expert_notes: Optional[str] = None
    ) -> bool:
        """Update review status and related fields"""
        try:
            with self.queue_service.get_db() as session:
                review = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id
                ).first()
                
                if not review:
                    logger.warning(f"Review {review_id} not found for status update")
                    return False
                
                # Update status
                old_status = review.status
                review.status = new_status.value
                review.updated_at = datetime.utcnow()
                
                # Handle status-specific updates
                if new_status == ReviewStatus.IN_REVIEW:
                    review.assigned_expert_id = expert_id
                    review.assigned_at = datetime.utcnow()
                elif new_status == ReviewStatus.COMPLETED:
                    review.completed_at = datetime.utcnow()
                    if expert_notes:
                        review.expert_notes = expert_notes
                
                session.commit()
                
                logger.info(f"Review {review_id} status updated from {old_status} to {new_status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update review status for {review_id}: {e}")
            return False
    
    def _calculate_progress(self, review: ExpertReviewItem) -> Dict[str, Any]:
        """Calculate review progress and estimates"""
        now = datetime.utcnow()
        
        # Calculate elapsed time
        elapsed_hours = (now - review.created_at).total_seconds() / 3600
        
        # Calculate progress percentage based on status and time
        progress_percentage = 0
        estimated_remaining_hours = review.estimated_completion_hours
        
        if review.status == ReviewStatus.PENDING.value:
            # Progress based on queue position (estimated)
            progress_percentage = min(10, (elapsed_hours / review.estimated_completion_hours) * 20)
        elif review.status == ReviewStatus.IN_REVIEW.value:
            # Progress based on time since assignment
            if review.assigned_at:
                review_elapsed = (now - review.assigned_at).total_seconds() / 3600
                progress_percentage = 20 + min(70, (review_elapsed / review.estimated_completion_hours) * 70)
                estimated_remaining_hours = max(0, review.estimated_completion_hours - review_elapsed)
            else:
                progress_percentage = 20
        elif review.status == ReviewStatus.COMPLETED.value:
            progress_percentage = 100
            estimated_remaining_hours = 0
        elif review.status == ReviewStatus.CANCELLED.value:
            progress_percentage = 0
            estimated_remaining_hours = 0
        
        # Estimate completion time
        estimated_completion = None
        if estimated_remaining_hours > 0:
            estimated_completion = now + timedelta(hours=estimated_remaining_hours)
        
        return {
            'percentage': round(progress_percentage, 1),
            'elapsed_hours': round(elapsed_hours, 1),
            'estimated_remaining_hours': round(estimated_remaining_hours, 1),
            'estimated_completion': estimated_completion,
            'is_overdue': elapsed_hours > review.estimated_completion_hours and review.status != ReviewStatus.COMPLETED.value
        }
    
    def _generate_timeline(self, review: ExpertReviewItem) -> List[Dict[str, Any]]:
        """Generate timeline of review events"""
        timeline = []
        
        # Created event
        timeline.append({
            'event': 'Review Requested',
            'timestamp': review.created_at,
            'status': 'completed',
            'description': 'Document submitted for expert review'
        })
        
        # Assigned event
        if review.assigned_at and review.assigned_expert_id:
            timeline.append({
                'event': 'Expert Assigned',
                'timestamp': review.assigned_at,
                'status': 'completed',
                'description': f'Review assigned to expert {review.assigned_expert_id}'
            })
        
        # In review event
        if review.status in [ReviewStatus.IN_REVIEW.value, ReviewStatus.COMPLETED.value]:
            timeline.append({
                'event': 'Review In Progress',
                'timestamp': review.assigned_at or review.updated_at,
                'status': 'completed' if review.status == ReviewStatus.COMPLETED.value else 'active',
                'description': 'Expert is conducting detailed analysis'
            })
        
        # Completed event
        if review.completed_at:
            timeline.append({
                'event': 'Review Completed',
                'timestamp': review.completed_at,
                'status': 'completed',
                'description': 'Expert analysis completed and delivered'
            })
        else:
            # Future completion event
            estimated_completion = review.created_at + timedelta(hours=review.estimated_completion_hours)
            timeline.append({
                'event': 'Review Completion',
                'timestamp': estimated_completion,
                'status': 'pending',
                'description': 'Estimated completion time'
            })
        
        return timeline
    
    def search_reviews(
        self,
        query: str,
        status: Optional[ReviewStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search reviews by various criteria"""
        try:
            with self.queue_service.get_db() as session:
                # Build query
                query_filter = session.query(ExpertReviewItem)
                
                # Text search in review_id, user_email, or expert_notes
                if query:
                    query_filter = query_filter.filter(
                        or_(
                            ExpertReviewItem.review_id.ilike(f'%{query}%'),
                            ExpertReviewItem.user_email.ilike(f'%{query}%'),
                            ExpertReviewItem.expert_notes.ilike(f'%{query}%')
                        )
                    )
                
                # Status filter
                if status:
                    query_filter = query_filter.filter(ExpertReviewItem.status == status.value)
                
                # Date range filter
                if date_from:
                    query_filter = query_filter.filter(ExpertReviewItem.created_at >= date_from)
                if date_to:
                    query_filter = query_filter.filter(ExpertReviewItem.created_at <= date_to)
                
                # Execute query
                reviews = query_filter.order_by(
                    ExpertReviewItem.created_at.desc()
                ).limit(limit).all()
                
                # Format results
                result = []
                for review in reviews:
                    result.append({
                        'review_id': review.review_id,
                        'user_email': review.user_email,
                        'status': review.status,
                        'created_at': review.created_at,
                        'updated_at': review.updated_at,
                        'confidence_score': review.confidence_score,
                        'priority': review.priority,
                        'assigned_expert_id': review.assigned_expert_id
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to search reviews: {e}")
            return []