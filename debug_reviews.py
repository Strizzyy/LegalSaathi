#!/usr/bin/env python3
"""
Debug script to check what reviews are in the database
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.expert_queue_models import Base, ExpertReviewItem, ExpertUser

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_reviews():
    """Check what reviews are in the database"""
    try:
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        
        logger.info(f"Connecting to database: {database_url}")
        
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Get all reviews
            reviews = db.query(ExpertReviewItem).all()
            
            logger.info(f"Found {len(reviews)} reviews in database:")
            
            for review in reviews:
                logger.info(f"  Review ID: {review.review_id}")
                logger.info(f"    Status: {review.status}")
                logger.info(f"    User: {review.user_email}")
                logger.info(f"    Confidence: {review.confidence_score}")
                logger.info(f"    Created: {review.created_at}")
                logger.info(f"    Priority: {review.priority}")
                logger.info("    ---")
            
            # Get pending reviews specifically
            pending_reviews = db.query(ExpertReviewItem).filter(
                ExpertReviewItem.status == 'pending'
            ).all()
            
            logger.info(f"\nPending reviews ({len(pending_reviews)}):")
            for review in pending_reviews:
                logger.info(f"  {review.review_id} - {review.user_email} - {review.confidence_score}")
            
            # Get experts
            experts = db.query(ExpertUser).all()
            logger.info(f"\nFound {len(experts)} experts:")
            for expert in experts:
                logger.info(f"  {expert.uid} - {expert.email} - {expert.role}")
            
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to debug reviews: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔍 Debugging expert queue database")
    debug_reviews()