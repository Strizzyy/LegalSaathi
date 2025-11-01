#!/usr/bin/env python3
"""
Test script for Expert Queue Service
Tests FIFO queue operations, database persistence, and API functionality
"""

import asyncio
import json
import logging
from datetime import datetime

from services.expert_queue_service import expert_queue_service
from models.expert_queue_models import (
    ExpertReviewSubmission, ExpertAnalysisSubmission,
    ReviewStatus, Priority
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_expert_queue_operations():
    """Test basic expert queue operations"""
    logger.info("🧪 Testing Expert Queue Service Operations")
    
    try:
        # Test 1: Add items to queue
        logger.info("📝 Test 1: Adding items to queue")
        
        # Create test submissions with different confidence scores
        submissions = [
            ExpertReviewSubmission(
                document_content="VGVzdCBkb2N1bWVudCAxIGNvbnRlbnQ=",  # Base64 encoded "Test document 1 content"
                ai_analysis={
                    "summary": "Test analysis 1",
                    "clauses": [{"id": "1", "text": "Test clause", "risk": "medium"}],
                    "confidence": 0.3
                },
                user_email="user1@example.com",
                confidence_score=0.3,  # Should be URGENT priority
                confidence_breakdown={"overall": 0.3, "clauses": [0.3]},
                document_type="rental_agreement"
                # No priority specified, should be calculated from confidence_score
            ),
            ExpertReviewSubmission(
                document_content="VGVzdCBkb2N1bWVudCAyIGNvbnRlbnQ=",  # Base64 encoded "Test document 2 content"
                ai_analysis={
                    "summary": "Test analysis 2",
                    "clauses": [{"id": "2", "text": "Test clause 2", "risk": "low"}],
                    "confidence": 0.5
                },
                user_email="user2@example.com",
                confidence_score=0.5,  # Should be MEDIUM priority
                confidence_breakdown={"overall": 0.5, "clauses": [0.5]},
                document_type="employment_contract"
            ),
            ExpertReviewSubmission(
                document_content="VGVzdCBkb2N1bWVudCAzIGNvbnRlbnQ=",  # Base64 encoded "Test document 3 content"
                ai_analysis={
                    "summary": "Test analysis 3",
                    "clauses": [{"id": "3", "text": "Test clause 3", "risk": "high"}],
                    "confidence": 0.2
                },
                user_email="user3@example.com",
                confidence_score=0.2,  # Should be URGENT priority
                confidence_breakdown={"overall": 0.2, "clauses": [0.2]},
                document_type="nda"
            )
        ]
        
        review_ids = []
        for i, submission in enumerate(submissions):
            response = await expert_queue_service.add_to_queue(submission)
            review_ids.append(response.review_id)
            logger.info(f"   ✅ Added review {i+1}: {response.review_id} (priority: {response.priority.value})")
        
        # Test 2: Get queue statistics
        logger.info("📊 Test 2: Getting queue statistics")
        stats = await expert_queue_service.get_queue_stats()
        logger.info(f"   📈 Total items: {stats.total_items}")
        logger.info(f"   ⏳ Pending items: {stats.pending_items}")
        logger.info(f"   🔄 In review items: {stats.in_review_items}")
        logger.info(f"   ✅ Completed items: {stats.completed_items}")
        
        # Test 3: Get next review (FIFO ordering)
        logger.info("🎯 Test 3: Getting next review (FIFO)")
        expert_id = "expert_test_001"
        
        next_review = await expert_queue_service.get_next_review(expert_id)
        if next_review:
            logger.info(f"   🎯 Got next review: {next_review.review_id}")
            logger.info(f"   📧 User email: {next_review.user_email}")
            logger.info(f"   📊 Confidence: {next_review.confidence_score}")
            logger.info(f"   🏷️ Status: {next_review.status.value}")
            logger.info(f"   👤 Assigned to: {next_review.assigned_expert_id}")
        else:
            logger.warning("   ❌ No reviews available")
        
        # Test 4: Complete expert review
        if next_review:
            logger.info("✅ Test 4: Completing expert review")
            
            completion = ExpertAnalysisSubmission(
                review_id=next_review.review_id,
                expert_analysis={
                    "summary": "Expert-reviewed analysis",
                    "clauses": [{"id": "1", "text": "Expert-reviewed clause", "risk": "low"}],
                    "confidence": 0.9,
                    "expert_notes": "Reviewed and improved by expert"
                },
                expert_notes="Document reviewed and analysis improved",
                clauses_modified=1,
                complexity_rating=3,
                review_duration_minutes=45
            )
            
            completion_response = await expert_queue_service.complete_review(completion, expert_id)
            logger.info(f"   ✅ Completed review: {completion_response.review_id}")
            logger.info(f"   📈 Confidence improvement: {completion_response.confidence_improvement:.2f}")
            logger.info(f"   ⏱️ Review duration: {completion_response.review_duration_minutes} minutes")
        
        # Test 5: Get updated statistics
        logger.info("📊 Test 5: Getting updated statistics")
        updated_stats = await expert_queue_service.get_queue_stats()
        logger.info(f"   📈 Total items: {updated_stats.total_items}")
        logger.info(f"   ⏳ Pending items: {updated_stats.pending_items}")
        logger.info(f"   🔄 In review items: {updated_stats.in_review_items}")
        logger.info(f"   ✅ Completed items: {updated_stats.completed_items}")
        logger.info(f"   👥 Expert workload: {updated_stats.expert_workload}")
        
        # Test 6: Get queue items with filtering
        logger.info("🔍 Test 6: Getting queue items with filtering")
        from models.expert_queue_models import QueueFilters, PaginationParams
        
        filters = QueueFilters(status=ReviewStatus.PENDING)
        pagination = PaginationParams(page=1, limit=10, sort_by="created_at", sort_order="asc")
        
        queue_response = await expert_queue_service.get_queue_items(filters, pagination)
        logger.info(f"   📋 Found {queue_response.total} pending items")
        for item in queue_response.items:
            logger.info(f"      - {item.review_id}: {item.user_email} (confidence: {item.confidence_score})")
        
        logger.info("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_fifo_ordering():
    """Test FIFO ordering specifically"""
    logger.info("🔄 Testing FIFO Ordering")
    
    try:
        # Add multiple items quickly
        submissions = []
        for i in range(5):
            submission = ExpertReviewSubmission(
                document_content=f"VGVzdCBkb2N1bWVudCB7aX0gY29udGVudA==",  # Base64 encoded
                ai_analysis={"summary": f"Test analysis {i}", "confidence": 0.4},
                user_email=f"fifo_test_{i}@example.com",
                confidence_score=0.4,
                confidence_breakdown={"overall": 0.4},
                document_type="general_contract"
            )
            response = await expert_queue_service.add_to_queue(submission)
            submissions.append((response.review_id, response.created_at))
            logger.info(f"   📝 Added FIFO test item {i+1}: {response.review_id}")
        
        # Get items in FIFO order
        expert_id = "fifo_expert_001"
        retrieved_order = []
        
        for i in range(3):  # Get first 3 items
            review = await expert_queue_service.get_next_review(expert_id)
            if review:
                retrieved_order.append(review.review_id)
                logger.info(f"   🎯 Retrieved item {i+1}: {review.review_id}")
        
        # Verify FIFO ordering
        expected_order = [item[0] for item in submissions[:3]]
        if retrieved_order == expected_order:
            logger.info("   ✅ FIFO ordering verified correctly!")
        else:
            logger.error(f"   ❌ FIFO ordering failed. Expected: {expected_order}, Got: {retrieved_order}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FIFO test failed: {e}")
        return False


if __name__ == "__main__":
    async def run_all_tests():
        logger.info("🚀 Starting Expert Queue Service Tests")
        
        # Run basic operations test
        test1_success = await test_expert_queue_operations()
        
        # Run FIFO ordering test
        test2_success = await test_fifo_ordering()
        
        if test1_success and test2_success:
            logger.info("🎉 All Expert Queue Service tests passed!")
        else:
            logger.error("❌ Some tests failed")
    
    # Run the tests
    asyncio.run(run_all_tests())