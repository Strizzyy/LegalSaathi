"""
Feedback Collection Service for Expert Review Quality Rating
Allows users to rate and provide feedback on expert review quality
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

from models.expert_queue_models import Base, ExpertReviewItem
from services.expert_queue_service import ExpertQueueService

logger = logging.getLogger(__name__)


class ReviewFeedback(Base):
    """Database model for review feedback"""
    __tablename__ = "review_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(100), ForeignKey('expert_review_items.review_id'), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    overall_rating = Column(Integer, nullable=False)  # 1-5 scale
    accuracy_rating = Column(Integer, nullable=True)  # 1-5 scale
    clarity_rating = Column(Integer, nullable=True)  # 1-5 scale
    timeliness_rating = Column(Integer, nullable=True)  # 1-5 scale
    usefulness_rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    would_recommend = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    review = relationship("ExpertReviewItem", back_populates="feedback")


# Add feedback relationship to ExpertReviewItem
ExpertReviewItem.feedback = relationship("ReviewFeedback", back_populates="review", uselist=False)


class FeedbackService:
    """Service for collecting and managing expert review feedback"""
    
    def __init__(self):
        self.queue_service = ExpertQueueService()
        logger.info("Feedback Service initialized")
    
    def submit_feedback(
        self,
        review_id: str,
        user_email: str,
        overall_rating: int,
        accuracy_rating: Optional[int] = None,
        clarity_rating: Optional[int] = None,
        timeliness_rating: Optional[int] = None,
        usefulness_rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
        would_recommend: bool = True
    ) -> Dict[str, Any]:
        """Submit feedback for an expert review"""
        
        # Validate ratings
        if not (1 <= overall_rating <= 5):
            return {
                'success': False,
                'error': 'Overall rating must be between 1 and 5'
            }
        
        for rating in [accuracy_rating, clarity_rating, timeliness_rating, usefulness_rating]:
            if rating is not None and not (1 <= rating <= 5):
                return {
                    'success': False,
                    'error': 'All ratings must be between 1 and 5'
                }
        
        try:
            with self.queue_service.get_db() as session:
                # Verify review exists and belongs to user
                review = session.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_id,
                    ExpertReviewItem.user_email == user_email.lower()
                ).first()
                
                if not review:
                    return {
                        'success': False,
                        'error': 'Review not found or access denied'
                    }
                
                # Check if feedback already exists
                existing_feedback = session.query(ReviewFeedback).filter(
                    ReviewFeedback.review_id == review_id,
                    ReviewFeedback.user_email == user_email.lower()
                ).first()
                
                if existing_feedback:
                    # Update existing feedback
                    existing_feedback.overall_rating = overall_rating
                    existing_feedback.accuracy_rating = accuracy_rating
                    existing_feedback.clarity_rating = clarity_rating
                    existing_feedback.timeliness_rating = timeliness_rating
                    existing_feedback.usefulness_rating = usefulness_rating
                    existing_feedback.feedback_text = feedback_text
                    existing_feedback.would_recommend = would_recommend
                    existing_feedback.updated_at = datetime.utcnow()
                    
                    session.commit()
                    
                    logger.info(f"Feedback updated for review {review_id}")
                    return {
                        'success': True,
                        'message': 'Feedback updated successfully',
                        'feedback_id': existing_feedback.id
                    }
                else:
                    # Create new feedback
                    feedback = ReviewFeedback(
                        review_id=review_id,
                        user_email=user_email.lower(),
                        overall_rating=overall_rating,
                        accuracy_rating=accuracy_rating,
                        clarity_rating=clarity_rating,
                        timeliness_rating=timeliness_rating,
                        usefulness_rating=usefulness_rating,
                        feedback_text=feedback_text,
                        would_recommend=would_recommend
                    )
                    
                    session.add(feedback)
                    session.commit()
                    
                    logger.info(f"New feedback submitted for review {review_id}")
                    return {
                        'success': True,
                        'message': 'Feedback submitted successfully',
                        'feedback_id': feedback.id
                    }
                
        except Exception as e:
            logger.error(f"Failed to submit feedback for review {review_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to submit feedback: {str(e)}'
            }
    
    def get_feedback(self, review_id: str, user_email: str) -> Optional[Dict[str, Any]]:
        """Get existing feedback for a review"""
        try:
            with self.queue_service.get_db() as session:
                feedback = session.query(ReviewFeedback).filter(
                    ReviewFeedback.review_id == review_id,
                    ReviewFeedback.user_email == user_email.lower()
                ).first()
                
                if not feedback:
                    return None
                
                return {
                    'feedback_id': feedback.id,
                    'review_id': feedback.review_id,
                    'overall_rating': feedback.overall_rating,
                    'accuracy_rating': feedback.accuracy_rating,
                    'clarity_rating': feedback.clarity_rating,
                    'timeliness_rating': feedback.timeliness_rating,
                    'usefulness_rating': feedback.usefulness_rating,
                    'feedback_text': feedback.feedback_text,
                    'would_recommend': feedback.would_recommend,
                    'created_at': feedback.created_at,
                    'updated_at': feedback.updated_at
                }
                
        except Exception as e:
            logger.error(f"Failed to get feedback for review {review_id}: {e}")
            return None
    
    def get_expert_feedback_summary(self, expert_id: str) -> Dict[str, Any]:
        """Get feedback summary for a specific expert"""
        try:
            with self.queue_service.get_db() as session:
                # Get all feedback for reviews completed by this expert
                feedbacks = session.query(ReviewFeedback).join(
                    ExpertReviewItem,
                    ReviewFeedback.review_id == ExpertReviewItem.review_id
                ).filter(
                    ExpertReviewItem.assigned_expert_id == expert_id
                ).all()
                
                if not feedbacks:
                    return {
                        'expert_id': expert_id,
                        'total_reviews': 0,
                        'average_overall_rating': 0.0,
                        'average_accuracy_rating': 0.0,
                        'average_clarity_rating': 0.0,
                        'average_timeliness_rating': 0.0,
                        'average_usefulness_rating': 0.0,
                        'recommendation_rate': 0.0,
                        'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    }
                
                # Calculate averages
                total_reviews = len(feedbacks)
                overall_ratings = [f.overall_rating for f in feedbacks]
                accuracy_ratings = [f.accuracy_rating for f in feedbacks if f.accuracy_rating is not None]
                clarity_ratings = [f.clarity_rating for f in feedbacks if f.clarity_rating is not None]
                timeliness_ratings = [f.timeliness_rating for f in feedbacks if f.timeliness_rating is not None]
                usefulness_ratings = [f.usefulness_rating for f in feedbacks if f.usefulness_rating is not None]
                
                # Rating distribution
                rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for rating in overall_ratings:
                    rating_distribution[rating] += 1
                
                # Recommendation rate
                recommendations = [f.would_recommend for f in feedbacks if f.would_recommend is not None]
                recommendation_rate = (sum(recommendations) / len(recommendations) * 100) if recommendations else 0.0
                
                return {
                    'expert_id': expert_id,
                    'total_reviews': total_reviews,
                    'average_overall_rating': sum(overall_ratings) / len(overall_ratings),
                    'average_accuracy_rating': sum(accuracy_ratings) / len(accuracy_ratings) if accuracy_ratings else 0.0,
                    'average_clarity_rating': sum(clarity_ratings) / len(clarity_ratings) if clarity_ratings else 0.0,
                    'average_timeliness_rating': sum(timeliness_ratings) / len(timeliness_ratings) if timeliness_ratings else 0.0,
                    'average_usefulness_rating': sum(usefulness_ratings) / len(usefulness_ratings) if usefulness_ratings else 0.0,
                    'recommendation_rate': recommendation_rate,
                    'rating_distribution': rating_distribution
                }
                
        except Exception as e:
            logger.error(f"Failed to get expert feedback summary for {expert_id}: {e}")
            return {
                'expert_id': expert_id,
                'total_reviews': 0,
                'average_overall_rating': 0.0,
                'error': str(e)
            }
    
    def get_overall_feedback_stats(self) -> Dict[str, Any]:
        """Get overall feedback statistics across all reviews"""
        try:
            with self.queue_service.get_db() as session:
                feedbacks = session.query(ReviewFeedback).all()
                
                if not feedbacks:
                    return {
                        'total_feedback_count': 0,
                        'average_overall_rating': 0.0,
                        'recommendation_rate': 0.0,
                        'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    }
                
                # Calculate statistics
                total_count = len(feedbacks)
                overall_ratings = [f.overall_rating for f in feedbacks]
                recommendations = [f.would_recommend for f in feedbacks if f.would_recommend is not None]
                
                # Rating distribution
                rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for rating in overall_ratings:
                    rating_distribution[rating] += 1
                
                # Recent feedback (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_feedbacks = [f for f in feedbacks if f.created_at >= thirty_days_ago]
                
                return {
                    'total_feedback_count': total_count,
                    'average_overall_rating': sum(overall_ratings) / len(overall_ratings),
                    'recommendation_rate': (sum(recommendations) / len(recommendations) * 100) if recommendations else 0.0,
                    'rating_distribution': rating_distribution,
                    'recent_feedback_count': len(recent_feedbacks),
                    'recent_average_rating': sum([f.overall_rating for f in recent_feedbacks]) / len(recent_feedbacks) if recent_feedbacks else 0.0
                }
                
        except Exception as e:
            logger.error(f"Failed to get overall feedback stats: {e}")
            return {
                'total_feedback_count': 0,
                'average_overall_rating': 0.0,
                'error': str(e)
            }
    
    def get_feedback_comments(self, limit: int = 50, min_rating: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent feedback comments for analysis"""
        try:
            with self.queue_service.get_db() as session:
                query = session.query(ReviewFeedback).filter(
                    ReviewFeedback.feedback_text.isnot(None),
                    ReviewFeedback.feedback_text != ''
                )
                
                if min_rating:
                    query = query.filter(ReviewFeedback.overall_rating >= min_rating)
                
                feedbacks = query.order_by(
                    ReviewFeedback.created_at.desc()
                ).limit(limit).all()
                
                result = []
                for feedback in feedbacks:
                    result.append({
                        'review_id': feedback.review_id,
                        'overall_rating': feedback.overall_rating,
                        'feedback_text': feedback.feedback_text,
                        'would_recommend': feedback.would_recommend,
                        'created_at': feedback.created_at
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get feedback comments: {e}")
            return []
    
    def generate_feedback_report(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive feedback report"""
        try:
            # Get overall stats
            overall_stats = self.get_overall_feedback_stats()
            
            # Get expert-specific stats if requested
            expert_stats = None
            if expert_id:
                expert_stats = self.get_expert_feedback_summary(expert_id)
            
            # Get recent comments
            recent_comments = self.get_feedback_comments(limit=20, min_rating=4)
            improvement_comments = self.get_feedback_comments(limit=10, min_rating=1)
            
            return {
                'generated_at': datetime.utcnow(),
                'overall_statistics': overall_stats,
                'expert_statistics': expert_stats,
                'recent_positive_feedback': recent_comments,
                'improvement_feedback': improvement_comments,
                'summary': {
                    'total_reviews_with_feedback': overall_stats['total_feedback_count'],
                    'average_satisfaction': overall_stats['average_overall_rating'],
                    'recommendation_rate': overall_stats['recommendation_rate'],
                    'trending': 'positive' if overall_stats.get('recent_average_rating', 0) >= overall_stats['average_overall_rating'] else 'negative'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate feedback report: {e}")
            return {
                'generated_at': datetime.utcnow(),
                'error': str(e)
            }