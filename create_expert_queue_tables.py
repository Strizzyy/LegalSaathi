#!/usr/bin/env python3
"""
Database migration script for Expert Queue tables
Creates all necessary tables with proper indexing for FIFO queue management
"""

import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from models.expert_queue_models import Base, ExpertReviewItem, ExpertUser, ReviewMetrics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_expert_queue_database():
    """Create expert queue database and tables with proper indexing"""
    try:
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        
        logger.info(f"Creating expert queue database: {database_url}")
        
        # Create engine
        engine = create_engine(database_url, echo=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create additional indexes for performance
        with engine.connect() as conn:
            # Index for FIFO ordering (most important)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_review_items_fifo 
                ON expert_review_items (status, created_at ASC)
            """))
            
            # Index for expert workload queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_review_items_expert_status 
                ON expert_review_items (assigned_expert_id, status)
            """))
            
            # Index for confidence-based queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_review_items_confidence 
                ON expert_review_items (confidence_score, status)
            """))
            
            # Index for priority-based queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_review_items_priority 
                ON expert_review_items (priority, status, created_at ASC)
            """))
            
            # Index for user email lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_review_items_user_email 
                ON expert_review_items (user_email, status)
            """))
            
            # Index for review metrics queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_review_metrics_expert 
                ON review_metrics (expert_id, created_at DESC)
            """))
            
            # Index for expert user lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expert_users_active 
                ON expert_users (active, role)
            """))
            
            conn.commit()
        
        logger.info("✅ Expert queue database created successfully with proper indexing")
        logger.info("📊 Tables created:")
        logger.info("   - expert_review_items (main queue table)")
        logger.info("   - expert_users (expert management)")
        logger.info("   - review_metrics (performance tracking)")
        logger.info("🚀 Database is ready for FIFO queue operations")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create expert queue database: {e}")
        return False


def verify_database_structure():
    """Verify that all tables and indexes were created correctly"""
    try:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if tables exist
            tables_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = conn.execute(tables_query).fetchall()
            
            logger.info("📋 Database tables:")
            for table in tables:
                logger.info(f"   ✓ {table[0]}")
            
            # Check if indexes exist
            indexes_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = conn.execute(indexes_query).fetchall()
            
            logger.info("📊 Database indexes:")
            for index in indexes:
                logger.info(f"   ✓ {index[0]}")
        
        logger.info("✅ Database structure verification completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Expert Queue Database Migration")
    
    # Create database and tables
    if create_expert_queue_database():
        # Verify structure
        if verify_database_structure():
            logger.info("🎉 Expert Queue database migration completed successfully!")
        else:
            logger.error("❌ Database verification failed")
            exit(1)
    else:
        logger.error("❌ Database creation failed")
        exit(1)