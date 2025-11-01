"""
Database migration script for Expert Review Feedback System
Creates tables for collecting and managing user feedback on expert reviews
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models.expert_queue_models import Base
from services.feedback_service import ReviewFeedback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_feedback_tables():
    """Create feedback tables in the database"""
    
    try:
        # Get database URL from environment
        database_url = os.getenv('EXPERT_QUEUE_DATABASE_URL', 'sqlite:///expert_queue.db')
        
        # Create engine
        engine = create_engine(database_url, echo=True)
        
        # Create all tables
        logger.info("Creating feedback tables...")
        Base.metadata.create_all(engine, tables=[ReviewFeedback.__table__])
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Add indexes for better performance
            logger.info("Adding database indexes...")
            
            # Index on review_id for faster lookups
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_feedback_review_id 
                ON review_feedback(review_id)
            """))
            
            # Index on user_email for user-specific queries
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_feedback_user_email 
                ON review_feedback(user_email)
            """))
            
            # Index on created_at for time-based queries
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_feedback_created_at 
                ON review_feedback(created_at)
            """))
            
            # Index on overall_rating for statistics
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_feedback_overall_rating 
                ON review_feedback(overall_rating)
            """))
            
            # Composite index for user + review lookups
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_feedback_user_review 
                ON review_feedback(user_email, review_id)
            """))
            
            session.commit()
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")
            session.rollback()
        
        finally:
            session.close()
        
        logger.info("Feedback tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='review_feedback'
            """))
            
            if result.fetchone():
                logger.info("✅ review_feedback table verified")
            else:
                logger.error("❌ review_feedback table not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create feedback tables: {e}")
        return False


def add_sample_feedback():
    """Add sample feedback data for testing"""
    
    try:
        database_url = os.getenv('EXPERT_QUEUE_DATABASE_URL', 'sqlite:///expert_queue.db')
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Check if sample data already exists
            existing_feedback = session.query(ReviewFeedback).first()
            if existing_feedback:
                logger.info("Sample feedback data already exists")
                return True
            
            # Create sample feedback entries
            sample_feedbacks = [
                ReviewFeedback(
                    review_id="review_20241101_120000_abc123",
                    user_email="user1@example.com",
                    overall_rating=5,
                    accuracy_rating=5,
                    clarity_rating=4,
                    timeliness_rating=5,
                    usefulness_rating=5,
                    feedback_text="Excellent expert review! Very thorough and helpful analysis.",
                    would_recommend=True
                ),
                ReviewFeedback(
                    review_id="review_20241101_130000_def456",
                    user_email="user2@example.com",
                    overall_rating=4,
                    accuracy_rating=4,
                    clarity_rating=4,
                    timeliness_rating=3,
                    usefulness_rating=4,
                    feedback_text="Good analysis, but took longer than expected.",
                    would_recommend=True
                ),
                ReviewFeedback(
                    review_id="review_20241101_140000_ghi789",
                    user_email="user3@example.com",
                    overall_rating=3,
                    accuracy_rating=3,
                    clarity_rating=3,
                    timeliness_rating=4,
                    usefulness_rating=3,
                    feedback_text="Average review. Could use more detailed explanations.",
                    would_recommend=False
                )
            ]
            
            # Add sample data
            for feedback in sample_feedbacks:
                session.add(feedback)
            
            session.commit()
            logger.info(f"Added {len(sample_feedbacks)} sample feedback entries")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to add sample feedback: {e}")
        return False


def verify_feedback_system():
    """Verify the feedback system is working correctly"""
    
    try:
        from services.feedback_service import FeedbackService
        
        feedback_service = FeedbackService()
        
        # Test feedback submission
        logger.info("Testing feedback submission...")
        result = feedback_service.submit_feedback(
            review_id="test_review_123",
            user_email="test@example.com",
            overall_rating=5,
            accuracy_rating=5,
            clarity_rating=4,
            timeliness_rating=5,
            usefulness_rating=5,
            feedback_text="Test feedback submission",
            would_recommend=True
        )
        
        if result['success']:
            logger.info("✅ Feedback submission test passed")
        else:
            logger.error(f"❌ Feedback submission test failed: {result.get('error')}")
            return False
        
        # Test feedback retrieval
        logger.info("Testing feedback retrieval...")
        feedback = feedback_service.get_feedback("test_review_123", "test@example.com")
        
        if feedback and feedback['overall_rating'] == 5:
            logger.info("✅ Feedback retrieval test passed")
        else:
            logger.error("❌ Feedback retrieval test failed")
            return False
        
        # Test statistics
        logger.info("Testing feedback statistics...")
        stats = feedback_service.get_overall_feedback_stats()
        
        if stats and 'total_feedback_count' in stats:
            logger.info("✅ Feedback statistics test passed")
        else:
            logger.error("❌ Feedback statistics test failed")
            return False
        
        logger.info("🎉 All feedback system tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Feedback system verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting feedback system setup...")
    
    # Create tables
    if create_feedback_tables():
        logger.info("✅ Feedback tables created")
    else:
        logger.error("❌ Failed to create feedback tables")
        exit(1)
    
    # Add sample data
    if add_sample_feedback():
        logger.info("✅ Sample feedback data added")
    else:
        logger.warning("⚠️ Could not add sample feedback data")
    
    # Verify system
    if verify_feedback_system():
        logger.info("✅ Feedback system verification passed")
    else:
        logger.error("❌ Feedback system verification failed")
        exit(1)
    
    logger.info("🎉 Feedback system setup completed successfully!")
    
    print("\n" + "="*60)
    print("EXPERT REVIEW FEEDBACK SYSTEM SETUP COMPLETE")
    print("="*60)
    print("✅ Database tables created")
    print("✅ Indexes added for performance")
    print("✅ Sample data populated")
    print("✅ System verification passed")
    print("\nThe feedback system is ready to collect user ratings!")
    print("="*60)