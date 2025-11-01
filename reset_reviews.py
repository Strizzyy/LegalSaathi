#!/usr/bin/env python3
"""
Reset some reviews back to pending status for testing
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.expert_queue_models import Base, ExpertReviewItem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_reviews():
    """Reset some reviews back to pending status"""
    try:
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        
        logger.info(f"Connecting to database: {database_url}")
        
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Reset some in_review reviews back to pending
            in_review_items = db.query(ExpertReviewItem).filter(
                ExpertReviewItem.status == 'in_review'
            ).limit(5).all()
            
            reset_count = 0
            for item in in_review_items:
                item.status = 'pending'
                item.assigned_expert_id = None
                item.assigned_at = None
                reset_count += 1
                logger.info(f"Reset review {item.review_id} to pending status")
            
            db.commit()
            
            logger.info(f"✅ Reset {reset_count} reviews to pending status")
            
            # Show current pending count
            pending_count = db.query(ExpertReviewItem).filter(
                ExpertReviewItem.status == 'pending'
            ).count()
            
            logger.info(f"📊 Total pending reviews: {pending_count}")
            
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset reviews: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔄 Resetting reviews to pending status")
    reset_reviews()