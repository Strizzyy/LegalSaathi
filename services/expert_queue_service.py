"""
Expert Queue Service for Human-in-the-Loop System
Manages expert review queue with database persistence and FIFO ordering
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, desc, asc, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from models.expert_queue_models import (
    Base, ExpertReviewItem, ExpertUser, ReviewMetrics,
    ReviewStatus, Priority, ExpertReviewSubmission, ExpertReviewResponse,
    ExpertReviewItemResponse, ExpertAnalysisSubmission, ExpertAnalysisResponse,
    QueueStatsResponse, QueueFilters, PaginationParams, QueueResponse,
    generate_review_id, calculate_priority, calculate_estimated_hours
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class ExpertQueueService:
    """
    Expert Queue Service for managing human-in-the-loop document reviews.
    Provides FIFO queue management with database persistence and proper indexing.
    """
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        
        # Initialize database
        self.engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info("Expert Queue Service initialized")
    
    def get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def add_to_queue(
        self,
        submission: ExpertReviewSubmission
    ) -> ExpertReviewResponse:
        """
        Add document to expert review queue with FIFO ordering.
        Stores document content, AI analysis, user email, and generates unique review_id.
        """
        try:
            db = self.get_db()
            try:
                # Generate unique review ID
                review_id = generate_review_id()
                
                # Calculate priority and estimated completion
                priority = submission.priority or calculate_priority(submission.confidence_score)
                estimated_hours = calculate_estimated_hours(submission.confidence_score, priority)
                
                # Create expert review item
                review_item = ExpertReviewItem(
                    review_id=review_id,
                    document_content=submission.document_content,
                    ai_analysis=json.dumps(submission.ai_analysis),
                    user_email=submission.user_email,
                    confidence_score=submission.confidence_score,
                    confidence_breakdown=json.dumps(submission.confidence_breakdown),
                    status=ReviewStatus.PENDING.value,
                    priority=priority.value,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    estimated_completion_hours=estimated_hours,
                    document_type=submission.document_type
                )
                
                db.add(review_item)
                db.commit()
                
                logger.info(f"Added review to queue: {review_id}, priority: {priority.value}, confidence: {submission.confidence_score}")
                
                return ExpertReviewResponse(
                    review_id=review_id,
                    status=ReviewStatus.PENDING,
                    estimated_completion_hours=estimated_hours,
                    priority=priority,
                    created_at=review_item.created_at,
                    message=f"Document queued for expert review. Estimated completion: {estimated_hours} hours."
                )
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error adding to queue: {e}")
            raise Exception(f"Failed to add document to expert queue: {str(e)}")
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            raise Exception(f"Failed to add document to expert queue: {str(e)}")
    
    async def get_next_review(self, expert_id: str) -> Optional[ExpertReviewItemResponse]:
        """
        Get next document for expert review using FIFO ordering.
        Returns the oldest pending review item and marks it as IN_REVIEW.
        """
        try:
            db = self.get_db()
            try:
                # Get the oldest pending review (FIFO)
                review_item = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.PENDING.value
                ).order_by(
                    asc(ExpertReviewItem.created_at)  # FIFO ordering by creation time
                ).first()
                
                if not review_item:
                    return None
                
                # Mark as in review and assign to expert
                review_item.status = ReviewStatus.IN_REVIEW.value
                review_item.assigned_expert_id = expert_id
                review_item.assigned_at = datetime.utcnow()
                review_item.updated_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"Assigned review {review_item.review_id} to expert {expert_id}")
                
                return self._convert_to_response(review_item, include_content=True)
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting next review: {e}")
            raise Exception(f"Failed to get next review: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting next review: {e}")
            raise Exception(f"Failed to get next review: {str(e)}")
    
    async def mark_in_review(self, review_id: str, expert_id: str) -> bool:
        """
        Mark document as being reviewed by expert to prevent duplicate reviews.
        """
        try:
            db = self.get_db()
            try:
                review_item = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id
                ).first()
                
                if not review_item:
                    logger.warning(f"Review not found: {review_id}")
                    return False
                
                if review_item.status != ReviewStatus.PENDING.value:
                    logger.warning(f"Review {review_id} is not pending (status: {review_item.status})")
                    return False
                
                # Mark as in review
                review_item.status = ReviewStatus.IN_REVIEW.value
                review_item.assigned_expert_id = expert_id
                review_item.assigned_at = datetime.utcnow()
                review_item.updated_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"Marked review {review_id} as in review by expert {expert_id}")
                return True
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error marking in review: {e}")
            return False
        except Exception as e:
            logger.error(f"Error marking in review: {e}")
            return False
    
    async def complete_review(
        self,
        submission: ExpertAnalysisSubmission,
        expert_id: str
    ) -> ExpertAnalysisResponse:
        """
        Complete expert review and update status to COMPLETED.
        """
        try:
            db = self.get_db()
            try:
                review_item = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == submission.review_id
                ).first()
                
                if not review_item:
                    raise Exception(f"Review not found: {submission.review_id}")
                
                if review_item.status != ReviewStatus.IN_REVIEW.value:
                    raise Exception(f"Review {submission.review_id} is not in review (status: {review_item.status})")
                
                if review_item.assigned_expert_id != expert_id:
                    raise Exception(f"Review {submission.review_id} is not assigned to expert {expert_id}")
                
                # Calculate confidence improvement
                original_confidence = review_item.confidence_score
                # Assume expert review improves confidence to at least 0.8
                improved_confidence = max(0.8, original_confidence + 0.2)
                confidence_improvement = improved_confidence - original_confidence
                
                # Update review item
                review_item.status = ReviewStatus.COMPLETED.value
                review_item.expert_analysis = json.dumps(submission.expert_analysis)
                review_item.expert_notes = submission.expert_notes
                review_item.completed_at = datetime.utcnow()
                review_item.updated_at = datetime.utcnow()
                review_item.review_duration_minutes = submission.review_duration_minutes
                
                # Create review metrics
                metrics = ReviewMetrics(
                    review_id=submission.review_id,
                    expert_id=expert_id,
                    review_duration_minutes=submission.review_duration_minutes,
                    clauses_modified=submission.clauses_modified,
                    confidence_improvement=confidence_improvement,
                    complexity_rating=submission.complexity_rating,
                    created_at=datetime.utcnow()
                )
                
                db.add(metrics)
                
                # Update expert user statistics
                expert_user = db.query(ExpertUser).filter(
                    ExpertUser.uid == expert_id
                ).first()
                
                if expert_user:
                    expert_user.reviews_completed += 1
                    # Update average review time
                    total_time = (expert_user.average_review_time * (expert_user.reviews_completed - 1)) + submission.review_duration_minutes
                    expert_user.average_review_time = total_time / expert_user.reviews_completed
                
                db.commit()
                
                logger.info(f"Completed review {submission.review_id} by expert {expert_id}")
                
                return ExpertAnalysisResponse(
                    review_id=submission.review_id,
                    expert_id=expert_id,
                    expert_analysis=submission.expert_analysis,
                    expert_notes=submission.expert_notes,
                    completed_at=review_item.completed_at,
                    review_duration_minutes=submission.review_duration_minutes,
                    confidence_improvement=confidence_improvement
                )
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error completing review: {e}")
            raise Exception(f"Failed to complete review: {str(e)}")
        except Exception as e:
            logger.error(f"Error completing review: {e}")
            raise Exception(f"Failed to complete review: {str(e)}")
    
    async def get_queue_items(
        self,
        filters: Optional[QueueFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> QueueResponse:
        """
        Get queue items with filtering and pagination.
        """
        try:
            db = self.get_db()
            try:
                # Build query with filters
                query = db.query(ExpertReviewItem)
                
                if filters:
                    if filters.status:
                        query = query.filter(ExpertReviewItem.status == filters.status.value)
                    if filters.priority:
                        query = query.filter(ExpertReviewItem.priority == filters.priority.value)
                    if filters.assigned_expert_id:
                        query = query.filter(ExpertReviewItem.assigned_expert_id == filters.assigned_expert_id)
                    if filters.min_confidence is not None:
                        query = query.filter(ExpertReviewItem.confidence_score >= filters.min_confidence)
                    if filters.max_confidence is not None:
                        query = query.filter(ExpertReviewItem.confidence_score <= filters.max_confidence)
                    if filters.created_after:
                        query = query.filter(ExpertReviewItem.created_at >= filters.created_after)
                    if filters.created_before:
                        query = query.filter(ExpertReviewItem.created_at <= filters.created_before)
                
                # Get total count
                total = query.count()
                
                # Apply sorting
                if pagination:
                    sort_column = getattr(ExpertReviewItem, pagination.sort_by, ExpertReviewItem.created_at)
                    if pagination.sort_order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                    
                    # Apply pagination
                    offset = (pagination.page - 1) * pagination.limit
                    query = query.offset(offset).limit(pagination.limit)
                else:
                    # Default sorting: FIFO (oldest first)
                    query = query.order_by(asc(ExpertReviewItem.created_at))
                
                items = query.all()
                
                # Convert to response models
                response_items = [self._convert_to_response(item) for item in items]
                
                # Calculate pagination info
                page = pagination.page if pagination else 1
                limit = pagination.limit if pagination else len(response_items)
                total_pages = (total + limit - 1) // limit if limit > 0 else 1
                
                return QueueResponse(
                    items=response_items,
                    total=total,
                    page=page,
                    limit=limit,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1
                )
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting queue items: {e}")
            raise Exception(f"Failed to get queue items: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting queue items: {e}")
            raise Exception(f"Failed to get queue items: {str(e)}")
    
    async def get_queue_stats(self) -> QueueStatsResponse:
        """
        Get queue statistics including counts by status and expert workload.
        """
        try:
            db = self.get_db()
            try:
                # Get counts by status
                total_items = db.query(ExpertReviewItem).count()
                pending_items = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.PENDING.value
                ).count()
                in_review_items = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.IN_REVIEW.value
                ).count()
                completed_items = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.COMPLETED.value
                ).count()
                cancelled_items = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.CANCELLED.value
                ).count()
                
                # Calculate average completion time
                completed_reviews = db.query(ExpertReviewItem).filter(
                    and_(
                        ExpertReviewItem.status == ReviewStatus.COMPLETED.value,
                        ExpertReviewItem.review_duration_minutes.isnot(None)
                    )
                ).all()
                
                avg_completion_hours = 0.0
                if completed_reviews:
                    total_minutes = sum(review.review_duration_minutes for review in completed_reviews)
                    avg_completion_hours = (total_minutes / len(completed_reviews)) / 60.0
                
                # Get oldest pending item
                oldest_pending = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.status == ReviewStatus.PENDING.value
                ).order_by(asc(ExpertReviewItem.created_at)).first()
                
                oldest_pending_time = oldest_pending.created_at if oldest_pending else None
                
                # Get expert workload
                expert_workload = {}
                workload_query = db.query(
                    ExpertReviewItem.assigned_expert_id,
                    func.count(ExpertReviewItem.id).label('count')
                ).filter(
                    ExpertReviewItem.status == ReviewStatus.IN_REVIEW.value
                ).group_by(ExpertReviewItem.assigned_expert_id).all()
                
                for expert_id, count in workload_query:
                    if expert_id:
                        expert_workload[expert_id] = count
                
                return QueueStatsResponse(
                    total_items=total_items,
                    pending_items=pending_items,
                    in_review_items=in_review_items,
                    completed_items=completed_items,
                    cancelled_items=cancelled_items,
                    average_completion_time_hours=avg_completion_hours,
                    oldest_pending_item=oldest_pending_time,
                    expert_workload=expert_workload
                )
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting queue stats: {e}")
            raise Exception(f"Failed to get queue stats: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            raise Exception(f"Failed to get queue stats: {str(e)}")
    
    async def update_review_status(
        self,
        review_id: str,
        status: ReviewStatus,
        expert_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update review status with proper state transitions.
        """
        try:
            db = self.get_db()
            try:
                review_item = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id
                ).first()
                
                if not review_item:
                    logger.warning(f"Review not found: {review_id}")
                    return False
                
                # Validate state transitions
                current_status = ReviewStatus(review_item.status)
                if not self._is_valid_status_transition(current_status, status):
                    logger.warning(f"Invalid status transition for {review_id}: {current_status} -> {status}")
                    return False
                
                # Update status
                review_item.status = status.value
                review_item.updated_at = datetime.utcnow()
                
                if expert_id:
                    review_item.assigned_expert_id = expert_id
                    if status == ReviewStatus.IN_REVIEW:
                        review_item.assigned_at = datetime.utcnow()
                
                if notes:
                    review_item.expert_notes = notes
                
                if status == ReviewStatus.COMPLETED:
                    review_item.completed_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"Updated review {review_id} status to {status.value}")
                return True
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error updating review status: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating review status: {e}")
            return False
    
    async def get_review_by_id(self, review_id: str, include_content: bool = False) -> Optional[ExpertReviewItemResponse]:
        """
        Get review item by ID.
        """
        try:
            db = self.get_db()
            try:
                review_item = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id
                ).first()
                
                if not review_item:
                    return None
                
                return self._convert_to_response(review_item, include_content=include_content)
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting review by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting review by ID: {e}")
            return None
    
    def _convert_to_response(
        self,
        review_item: ExpertReviewItem,
        include_content: bool = False
    ) -> ExpertReviewItemResponse:
        """Convert database model to response model"""
        try:
            ai_analysis = json.loads(review_item.ai_analysis) if review_item.ai_analysis else {}
            confidence_breakdown = json.loads(review_item.confidence_breakdown) if review_item.confidence_breakdown else {}
            
            return ExpertReviewItemResponse(
                review_id=review_item.review_id,
                user_email=review_item.user_email,
                confidence_score=review_item.confidence_score,
                confidence_breakdown=confidence_breakdown,
                status=ReviewStatus(review_item.status),
                priority=Priority(review_item.priority),
                created_at=review_item.created_at,
                updated_at=review_item.updated_at,
                assigned_expert_id=review_item.assigned_expert_id,
                assigned_at=review_item.assigned_at,
                completed_at=review_item.completed_at,
                estimated_completion_hours=review_item.estimated_completion_hours,
                document_type=review_item.document_type,
                expert_notes=review_item.expert_notes,
                ai_analysis=ai_analysis,
                document_content=review_item.document_content if include_content else None
            )
        except Exception as e:
            logger.error(f"Error converting to response: {e}")
            raise
    
    def _is_valid_status_transition(self, current: ReviewStatus, new: ReviewStatus) -> bool:
        """Validate status transitions"""
        valid_transitions = {
            ReviewStatus.PENDING: [ReviewStatus.IN_REVIEW, ReviewStatus.CANCELLED],
            ReviewStatus.IN_REVIEW: [ReviewStatus.COMPLETED, ReviewStatus.CANCELLED, ReviewStatus.PENDING],
            ReviewStatus.COMPLETED: [],  # Terminal state
            ReviewStatus.CANCELLED: [ReviewStatus.PENDING]  # Can be requeued
        }
        
        return new in valid_transitions.get(current, [])


# Global instance
expert_queue_service = ExpertQueueService()