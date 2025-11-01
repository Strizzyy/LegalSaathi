#!/usr/bin/env python3
"""
Test script for Expert Queue API endpoints
Tests the REST API functionality
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def test_expert_queue_api():
    """Test Expert Queue API endpoints"""
    logger.info("🧪 Testing Expert Queue API Endpoints")
    
    try:
        # Test 1: Health check
        logger.info("🏥 Test 1: Health check")
        response = requests.get(f"{BASE_URL}/api/expert-queue/health")
        if response.status_code == 200:
            logger.info("   ✅ Health check passed")
            logger.info(f"   📊 Response: {response.json()}")
        else:
            logger.error(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Submit document for expert review
        logger.info("📝 Test 2: Submit document for expert review")
        
        submission_data = {
            "document_content": "This is a test rental agreement with some clauses that need expert review.",
            "ai_analysis": {
                "summary": "Test rental agreement analysis",
                "clauses": [
                    {"id": "1", "text": "Monthly rent clause", "risk": "medium", "confidence": 0.3}
                ],
                "overall_confidence": 0.3
            },
            "user_email": "test@example.com",
            "confidence_score": 0.3,
            "confidence_breakdown": {
                "overall": 0.3,
                "clauses": [0.3],
                "factors": ["Complex legal language", "Ambiguous terms"]
            },
            "document_type": "rental_agreement"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/expert-queue/submit",
            json=submission_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            submission_result = response.json()
            review_id = submission_result["review_id"]
            logger.info(f"   ✅ Document submitted successfully")
            logger.info(f"   🆔 Review ID: {review_id}")
            logger.info(f"   ⏱️ Estimated completion: {submission_result['estimated_completion_hours']} hours")
            logger.info(f"   🏷️ Priority: {submission_result['priority']}")
        else:
            logger.error(f"   ❌ Submission failed: {response.status_code}")
            logger.error(f"   📄 Response: {response.text}")
            return False
        
        # Test 3: Get queue statistics
        logger.info("📊 Test 3: Get queue statistics")
        response = requests.get(f"{BASE_URL}/api/expert-queue/stats")
        
        if response.status_code == 200:
            stats = response.json()
            logger.info("   ✅ Statistics retrieved successfully")
            logger.info(f"   📈 Total items: {stats['total_items']}")
            logger.info(f"   ⏳ Pending items: {stats['pending_items']}")
            logger.info(f"   🔄 In review items: {stats['in_review_items']}")
            logger.info(f"   ✅ Completed items: {stats['completed_items']}")
        else:
            logger.error(f"   ❌ Statistics failed: {response.status_code}")
            return False
        
        # Test 4: Get queue items
        logger.info("📋 Test 4: Get queue items")
        response = requests.get(f"{BASE_URL}/api/expert-queue/queue?status=pending&limit=5")
        
        if response.status_code == 200:
            queue_data = response.json()
            logger.info("   ✅ Queue items retrieved successfully")
            logger.info(f"   📊 Total items: {queue_data['total']}")
            logger.info(f"   📄 Page: {queue_data['page']}")
            
            for item in queue_data['items'][:3]:  # Show first 3 items
                logger.info(f"      - {item['review_id']}: {item['user_email']} (confidence: {item['confidence_score']})")
        else:
            logger.error(f"   ❌ Queue items failed: {response.status_code}")
            return False
        
        # Test 5: Get next review for expert
        logger.info("🎯 Test 5: Get next review for expert")
        expert_id = "test_expert_001"
        response = requests.get(f"{BASE_URL}/api/expert-queue/next-review/{expert_id}")
        
        if response.status_code == 200:
            next_review = response.json()
            if next_review:
                logger.info("   ✅ Next review retrieved successfully")
                logger.info(f"   🆔 Review ID: {next_review['review_id']}")
                logger.info(f"   📧 User email: {next_review['user_email']}")
                logger.info(f"   📊 Confidence: {next_review['confidence_score']}")
                logger.info(f"   🏷️ Status: {next_review['status']}")
                
                assigned_review_id = next_review['review_id']
            else:
                logger.info("   ℹ️ No reviews available for assignment")
                assigned_review_id = None
        else:
            logger.error(f"   ❌ Next review failed: {response.status_code}")
            return False
        
        # Test 6: Get review details
        if assigned_review_id:
            logger.info("🔍 Test 6: Get review details")
            response = requests.get(f"{BASE_URL}/api/expert-queue/review/{assigned_review_id}?include_content=true")
            
            if response.status_code == 200:
                review_details = response.json()
                logger.info("   ✅ Review details retrieved successfully")
                logger.info(f"   🆔 Review ID: {review_details['review_id']}")
                logger.info(f"   👤 Assigned expert: {review_details['assigned_expert_id']}")
                logger.info(f"   📅 Created: {review_details['created_at']}")
                logger.info(f"   📄 Has content: {'document_content' in review_details and review_details['document_content'] is not None}")
            else:
                logger.error(f"   ❌ Review details failed: {response.status_code}")
                return False
        
        # Test 7: Complete expert review
        if assigned_review_id:
            logger.info("✅ Test 7: Complete expert review")
            
            completion_data = {
                "review_id": assigned_review_id,
                "expert_analysis": {
                    "summary": "Expert-reviewed rental agreement analysis",
                    "clauses": [
                        {
                            "id": "1",
                            "text": "Monthly rent clause",
                            "risk": "low",
                            "confidence": 0.9,
                            "expert_notes": "Reviewed and clarified by expert"
                        }
                    ],
                    "overall_confidence": 0.9,
                    "expert_certification": True
                },
                "expert_notes": "Document thoroughly reviewed. Clarified ambiguous terms and reduced risk assessment.",
                "clauses_modified": 1,
                "complexity_rating": 3,
                "review_duration_minutes": 30
            }
            
            response = requests.post(
                f"{BASE_URL}/api/expert-queue/review/complete?expert_id={expert_id}",
                json=completion_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                completion_result = response.json()
                logger.info("   ✅ Expert review completed successfully")
                logger.info(f"   🆔 Review ID: {completion_result['review_id']}")
                logger.info(f"   👤 Expert ID: {completion_result['expert_id']}")
                logger.info(f"   📈 Confidence improvement: {completion_result['confidence_improvement']:.2f}")
                logger.info(f"   ⏱️ Review duration: {completion_result['review_duration_minutes']} minutes")
            else:
                logger.error(f"   ❌ Review completion failed: {response.status_code}")
                logger.error(f"   📄 Response: {response.text}")
                return False
        
        # Test 8: Get updated statistics
        logger.info("📊 Test 8: Get updated statistics")
        response = requests.get(f"{BASE_URL}/api/expert-queue/stats")
        
        if response.status_code == 200:
            updated_stats = response.json()
            logger.info("   ✅ Updated statistics retrieved successfully")
            logger.info(f"   📈 Total items: {updated_stats['total_items']}")
            logger.info(f"   ⏳ Pending items: {updated_stats['pending_items']}")
            logger.info(f"   🔄 In review items: {updated_stats['in_review_items']}")
            logger.info(f"   ✅ Completed items: {updated_stats['completed_items']}")
            logger.info(f"   👥 Expert workload: {updated_stats['expert_workload']}")
        else:
            logger.error(f"   ❌ Updated statistics failed: {response.status_code}")
            return False
        
        logger.info("🎉 All API tests completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection failed. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        logger.error(f"❌ API test failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Expert Queue API Tests")
    logger.info("📋 Make sure the FastAPI server is running on http://localhost:8000")
    logger.info("   You can start it with: python -m uvicorn main:app --reload")
    
    # Wait a moment for user to start server if needed
    input("Press Enter when the server is ready...")
    
    if test_expert_queue_api():
        logger.info("🎉 All Expert Queue API tests passed!")
    else:
        logger.error("❌ Some API tests failed")