#!/usr/bin/env python3
"""
Test data insertion for HITL Dashboard
Creates sample expert review requests for testing
"""

import os
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.expert_queue_models import Base, ExpertReviewItem, ExpertUser, Priority, ReviewStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_data():
    """Create sample expert review requests for testing"""
    try:
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./expert_queue.db')
        
        logger.info(f"Connecting to database: {database_url}")
        
        # Create engine and session
        engine = create_engine(database_url)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Sample AI analysis data
            sample_ai_analysis = {
                "summary": "This contract contains several high-risk clauses that require expert review, including liability limitations and termination conditions.",
                "overall_risk": {
                    "level": "YELLOW",
                    "score": 0.65,
                    "confidence_percentage": 35
                },
                "analysis_results": [
                    {
                        "clause_id": "clause_1",
                        "clause_text": "The Company shall not be liable for any indirect, incidental, or consequential damages.",
                        "risk_level": {
                            "level": "RED",
                            "score": 0.85,
                            "confidence_percentage": 30
                        },
                        "plain_explanation": "This clause limits the company's liability for certain types of damages.",
                        "legal_implications": ["May prevent recovery of significant damages", "Could be unenforceable in some jurisdictions"],
                        "recommendations": ["Consider mutual liability limitations", "Add exceptions for gross negligence"]
                    },
                    {
                        "clause_id": "clause_2", 
                        "clause_text": "Either party may terminate this agreement with 30 days written notice.",
                        "risk_level": {
                            "level": "YELLOW",
                            "score": 0.45,
                            "confidence_percentage": 40
                        },
                        "plain_explanation": "This allows either party to end the contract with one month's notice.",
                        "legal_implications": ["Provides flexibility but may create uncertainty"],
                        "recommendations": ["Consider longer notice period for key contracts"]
                    }
                ]
            }
            
            sample_confidence_breakdown = {
                "overall_confidence": 0.35,
                "clause_confidences": {
                    "clause_1": 0.30,
                    "clause_2": 0.40
                },
                "component_weights": {
                    "legal_complexity": 0.4,
                    "clause_clarity": 0.3,
                    "risk_assessment": 0.3
                },
                "factors_affecting_confidence": [
                    "Complex legal terminology detected",
                    "Ambiguous clause structure",
                    "Limited training data for this contract type"
                ]
            }
            
            # Create sample review items
            sample_reviews = [
                {
                    "review_id": f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_001",
                    "document_content": "VGhpcyBpcyBhIHNhbXBsZSBjb250cmFjdCBkb2N1bWVudCBmb3IgdGVzdGluZyBwdXJwb3Nlcy4=",  # Base64 encoded
                    "ai_analysis": json.dumps(sample_ai_analysis),
                    "user_email": "user1@example.com",
                    "confidence_score": 0.35,
                    "confidence_breakdown": json.dumps(sample_confidence_breakdown),
                    "status": ReviewStatus.PENDING.value,
                    "priority": Priority.HIGH.value,
                    "document_type": "Service Agreement",
                    "estimated_completion_hours": 6
                },
                {
                    "review_id": f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_002",
                    "document_content": "QW5vdGhlciBzYW1wbGUgZG9jdW1lbnQgZm9yIGV4cGVydCByZXZpZXcgdGVzdGluZy4=",  # Base64 encoded
                    "ai_analysis": json.dumps({
                        **sample_ai_analysis,
                        "summary": "Employment contract with potentially problematic non-compete clauses requiring expert analysis.",
                        "overall_risk": {"level": "RED", "score": 0.8, "confidence_percentage": 25}
                    }),
                    "user_email": "user2@example.com", 
                    "confidence_score": 0.25,
                    "confidence_breakdown": json.dumps({
                        **sample_confidence_breakdown,
                        "overall_confidence": 0.25
                    }),
                    "status": ReviewStatus.PENDING.value,
                    "priority": Priority.URGENT.value,
                    "document_type": "Employment Contract",
                    "estimated_completion_hours": 4
                },
                {
                    "review_id": f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_003",
                    "document_content": "VGhpcmQgc2FtcGxlIGRvY3VtZW50IGZvciB0ZXN0aW5nIEhJVEwgZGFzaGJvYXJkLg==",  # Base64 encoded
                    "ai_analysis": json.dumps({
                        **sample_ai_analysis,
                        "summary": "Lease agreement with standard terms but some unclear provisions that need expert clarification.",
                        "overall_risk": {"level": "YELLOW", "score": 0.55, "confidence_percentage": 45}
                    }),
                    "user_email": "user3@example.com",
                    "confidence_score": 0.45,
                    "confidence_breakdown": json.dumps({
                        **sample_confidence_breakdown,
                        "overall_confidence": 0.45
                    }),
                    "status": ReviewStatus.PENDING.value,
                    "priority": Priority.MEDIUM.value,
                    "document_type": "Lease Agreement",
                    "estimated_completion_hours": 8
                }
            ]
            
            # Insert sample data
            for review_data in sample_reviews:
                # Check if review already exists
                existing = db.query(ExpertReviewItem).filter(
                    ExpertReviewItem.review_id == review_data["review_id"]
                ).first()
                
                if not existing:
                    review_item = ExpertReviewItem(
                        review_id=review_data["review_id"],
                        document_content=review_data["document_content"],
                        ai_analysis=review_data["ai_analysis"],
                        user_email=review_data["user_email"],
                        confidence_score=review_data["confidence_score"],
                        confidence_breakdown=review_data["confidence_breakdown"],
                        status=review_data["status"],
                        priority=review_data["priority"],
                        created_at=datetime.utcnow() - timedelta(hours=len(sample_reviews) - sample_reviews.index(review_data)),
                        updated_at=datetime.utcnow(),
                        estimated_completion_hours=review_data["estimated_completion_hours"],
                        document_type=review_data["document_type"]
                    )
                    
                    db.add(review_item)
                    logger.info(f"Created sample review: {review_data['review_id']}")
            
            # Create sample expert users
            sample_experts = [
                {
                    "uid": "expert_001",
                    "email": "expert1@legalsaathi.com",
                    "display_name": "Senior Legal Expert",
                    "role": "senior_expert",
                    "specializations": json.dumps(["Contract Law", "Employment Law"]),
                    "active": True,
                    "reviews_completed": 15,
                    "average_review_time": 180.0
                },
                {
                    "uid": "expert_002", 
                    "email": "expert2@legalsaathi.com",
                    "display_name": "Contract Specialist",
                    "role": "legal_expert",
                    "specializations": json.dumps(["Commercial Contracts", "Real Estate"]),
                    "active": True,
                    "reviews_completed": 8,
                    "average_review_time": 240.0
                },
                {
                    "uid": "admin_001",
                    "email": "admin@legalsaathi.com", 
                    "display_name": "Admin Expert",
                    "role": "admin",
                    "specializations": json.dumps(["All Legal Areas"]),
                    "active": True,
                    "reviews_completed": 25,
                    "average_review_time": 150.0
                }
            ]
            
            for expert_data in sample_experts:
                existing_expert = db.query(ExpertUser).filter(
                    ExpertUser.uid == expert_data["uid"]
                ).first()
                
                if not existing_expert:
                    expert_user = ExpertUser(
                        uid=expert_data["uid"],
                        email=expert_data["email"],
                        display_name=expert_data["display_name"],
                        role=expert_data["role"],
                        specializations=expert_data["specializations"],
                        active=expert_data["active"],
                        created_at=datetime.utcnow(),
                        reviews_completed=expert_data["reviews_completed"],
                        average_review_time=expert_data["average_review_time"]
                    )
                    
                    db.add(expert_user)
                    logger.info(f"Created sample expert: {expert_data['email']}")
            
            # Commit all changes
            db.commit()
            logger.info("✅ Sample data created successfully!")
            
            # Print summary
            total_reviews = db.query(ExpertReviewItem).count()
            pending_reviews = db.query(ExpertReviewItem).filter(
                ExpertReviewItem.status == ReviewStatus.PENDING.value
            ).count()
            total_experts = db.query(ExpertUser).count()
            
            logger.info(f"📊 Database Summary:")
            logger.info(f"   Total Reviews: {total_reviews}")
            logger.info(f"   Pending Reviews: {pending_reviews}")
            logger.info(f"   Total Experts: {total_experts}")
            
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Creating sample data for HITL Dashboard testing")
    
    if create_sample_data():
        logger.info("🎉 Sample data creation completed successfully!")
        logger.info("💡 You can now test the HITL Dashboard at http://localhost:3000/hitl")
    else:
        logger.error("❌ Sample data creation failed")
        exit(1)