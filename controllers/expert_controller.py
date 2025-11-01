"""
Consolidated Expert Controller
Combines expert authentication, queue management, portal, and review functionality
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends, Header, Form, UploadFile, File
from fastapi.responses import JSONResponse

from models.support_models import (
    SupportTicketRequest, SupportTicketResponse, 
    ExpertProfile, SupportTicket, TicketResolution
)

logger = logging.getLogger(__name__)

# Router for expert endpoints
router = APIRouter(prefix="/api/expert", tags=["expert"])

class ExpertController:
    """Consolidated expert management controller"""
    
    def __init__(self):
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        
        # Initialize expert services
        try:
            from services.expert_auth_service import expert_auth_service
            from services.expert_queue_service import expert_queue_service
            from services.review_tracking_service import review_tracking_service
            
            self.auth_service = expert_auth_service
            self.queue_service = expert_queue_service
            self.review_service = review_tracking_service
            
            logger.info("✅ Expert services initialized")
            
        except ImportError as e:
            logger.warning(f"Expert services not available: {e}")
            self.auth_service = None
            self.queue_service = None
            self.review_service = None
    
    # Expert Authentication Methods
    async def authenticate_expert(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate expert user"""
        if not self.auth_service:
            return {"success": False, "error": "Expert authentication service not available"}
        
        try:
            return await self.auth_service.authenticate_expert(credentials)
        except Exception as e:
            logger.error(f"Expert authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Expert Queue Management Methods
    async def get_expert_queue(self, expert_id: str, status_filter: str = None) -> Dict[str, Any]:
        """Get expert review queue"""
        if not self.queue_service:
            return {"success": False, "error": "Expert queue service not available"}
        
        try:
            return await self.queue_service.get_expert_queue(expert_id, status_filter)
        except Exception as e:
            logger.error(f"Failed to get expert queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def assign_review_to_expert(self, review_id: str, expert_id: str) -> Dict[str, Any]:
        """Assign review to expert"""
        if not self.queue_service:
            return {"success": False, "error": "Expert queue service not available"}
        
        try:
            return await self.queue_service.assign_review_to_expert(review_id, expert_id)
        except Exception as e:
            logger.error(f"Failed to assign review: {e}")
            return {"success": False, "error": str(e)}
    
    # Expert Review Methods
    async def submit_expert_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit expert review"""
        if not self.review_service:
            return {"success": False, "error": "Expert review service not available"}
        
        try:
            return await self.review_service.submit_expert_review(review_data)
        except Exception as e:
            logger.error(f"Failed to submit expert review: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_expert_reviews(self, expert_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get expert's submitted reviews"""
        if not self.review_service:
            return {"success": False, "error": "Expert review service not available"}
        
        try:
            return await self.review_service.get_expert_reviews(expert_id, limit)
        except Exception as e:
            logger.error(f"Failed to get expert reviews: {e}")
            return {"success": False, "error": str(e)}
    
    # Support Ticket Methods (from support_controller.py)
    async def get_available_experts(self) -> Dict[str, Any]:
        """Get list of available experts"""
        try:
            # Mock expert profiles for demo
            experts = [
                {
                    "id": "expert_1",
                    "name": "Sarah Chen",
                    "specialty": "Contract Law",
                    "rating": 4.8,
                    "response_time": "2-4 hours",
                    "languages": ["English", "Spanish"],
                    "expertise_areas": ["Employment Contracts", "NDAs", "General Contracts"],
                    "availability_status": "available",
                    "bio": "Experienced contract attorney with 10+ years in employment and business law."
                },
                {
                    "id": "expert_2", 
                    "name": "Michael Rodriguez",
                    "specialty": "Real Estate Law",
                    "rating": 4.9,
                    "response_time": "1-3 hours",
                    "languages": ["English", "Spanish"],
                    "expertise_areas": ["Rental Agreements", "Lease Contracts", "Property Law"],
                    "availability_status": "available",
                    "bio": "Real estate attorney specializing in residential and commercial lease agreements."
                },
                {
                    "id": "expert_3",
                    "name": "Dr. Priya Sharma",
                    "specialty": "Corporate Law",
                    "rating": 4.7,
                    "response_time": "4-6 hours",
                    "languages": ["English", "Hindi"],
                    "expertise_areas": ["Partnership Agreements", "Loan Agreements", "Corporate Contracts"],
                    "availability_status": "busy",
                    "bio": "Corporate law expert with extensive experience in business partnerships and financing."
                }
            ]
            
            available_experts = [expert for expert in experts if expert["availability_status"] == "available"]
            
            return {
                "success": True,
                "experts": available_experts,
                "total_available": len(available_experts)
            }
        except Exception as e:
            logger.error(f"Error getting experts: {e}")
            return {"success": False, "error": str(e)}


# Global instance
expert_controller = ExpertController()

# Router endpoints
@router.post("/auth/login")
async def expert_login(credentials: Dict[str, Any]):
    """Expert login endpoint"""
    return await expert_controller.authenticate_expert(credentials)

@router.get("/queue/{expert_id}")
async def get_expert_queue(expert_id: str, status: str = None):
    """Get expert review queue"""
    return await expert_controller.get_expert_queue(expert_id, status)

@router.post("/queue/assign")
async def assign_review(assignment_data: Dict[str, Any]):
    """Assign review to expert"""
    review_id = assignment_data.get("review_id")
    expert_id = assignment_data.get("expert_id")
    return await expert_controller.assign_review_to_expert(review_id, expert_id)

@router.post("/review/submit")
async def submit_review(review_data: Dict[str, Any]):
    """Submit expert review"""
    return await expert_controller.submit_expert_review(review_data)

@router.get("/reviews/{expert_id}")
async def get_expert_reviews(expert_id: str, limit: int = 10):
    """Get expert's reviews"""
    return await expert_controller.get_expert_reviews(expert_id, limit)

@router.get("/available")
async def get_available_experts():
    """Get available experts"""
    return await expert_controller.get_available_experts()