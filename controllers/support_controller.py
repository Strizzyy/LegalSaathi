"""
Support controller for handling human expert support requests
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import asyncio

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.support_models import (
    SupportTicketRequest, SupportTicketResponse, 
    ExpertProfile, SupportTicket, TicketResolution
)

# Create router and limiter
router = APIRouter(prefix="/api/support", tags=["support"])
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


class SupportController:
    """Controller for handling support ticket operations"""
    
    def __init__(self):
        # In-memory storage for demo purposes
        # In production, this would use a database
        self.tickets: Dict[str, SupportTicket] = {}
        self.experts = self._initialize_experts()
    
    def _initialize_experts(self) -> List[ExpertProfile]:
        """Initialize mock expert profiles for demo"""
        return [
            ExpertProfile(
                id="expert_1",
                name="Sarah Chen",
                specialty="Contract Law",
                rating=4.9,
                response_time="2-4 hours",
                languages=["English", "Spanish"],
                expertise_areas=["Employment Contracts", "NDAs", "General Contracts"],
                availability_status="available",
                bio="Experienced contract attorney with 10+ years in employment and business law."
            ),
            ExpertProfile(
                id="expert_2", 
                name="Michael Rodriguez",
                specialty="Real Estate Law",
                rating=4.8,
                response_time="1-3 hours",
                languages=["English", "Spanish"],
                expertise_areas=["Rental Agreements", "Lease Contracts", "Property Law"],
                availability_status="available",
                bio="Real estate attorney specializing in residential and commercial lease agreements."
            ),
            ExpertProfile(
                id="expert_3",
                name="Dr. Priya Sharma",
                specialty="Corporate Law",
                rating=4.9,
                response_time="4-6 hours",
                languages=["English", "Hindi"],
                expertise_areas=["Partnership Agreements", "Loan Agreements", "Corporate Contracts"],
                availability_status="busy",
                bio="Corporate law expert with extensive experience in business partnerships and financing."
            )
        ]
    
    async def get_available_experts(self) -> Dict[str, Any]:
        """Get list of available experts"""
        try:
            available_experts = [
                expert for expert in self.experts 
                if expert.availability_status == "available"
            ]
            
            return {
                "success": True,
                "experts": [expert.dict() for expert in available_experts],
                "total_available": len(available_experts)
            }
        except Exception as e:
            logger.error(f"Error getting experts: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available experts")
    
    async def create_support_ticket(self, request: SupportTicketRequest) -> SupportTicketResponse:
        """Create a new support ticket"""
        try:
            ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"
            
            # Assign expert based on document type and urgency
            assigned_expert = self._assign_expert(
                request.document_context.documentType if request.document_context else "general_contract",
                request.urgency_level
            )
            
            # Estimate response time based on urgency and expert availability
            estimated_response = self._calculate_response_time(
                request.urgency_level, 
                assigned_expert.response_time if assigned_expert else "4-8 hours"
            )
            
            # Create ticket
            ticket = SupportTicket(
                id=ticket_id,
                document_id=request.document_id,
                clause_id=request.clause_id,
                user_question=request.user_question,
                urgency_level=request.urgency_level,
                category=request.category,
                status="assigned",
                priority=request.urgency_level,
                created_at=datetime.now(),
                expert_id=assigned_expert.id if assigned_expert else None,
                expert_name=assigned_expert.name if assigned_expert else "Being assigned...",
                expert_specialty=assigned_expert.specialty if assigned_expert else None,
                estimated_response=estimated_response,
                document_context=request.document_context,
                clause_context=request.clause_context,
                user_context=request.user_context
            )
            
            # Store ticket
            self.tickets[ticket_id] = ticket
            
            # Simulate expert response for demo (in production, this would be real)
            if assigned_expert:
                self._schedule_expert_response(ticket_id, estimated_response)
            
            return SupportTicketResponse(
                success=True,
                ticket=ticket,
                message=f"Support ticket created successfully. Expert {assigned_expert.name if assigned_expert else 'assignment'} will respond within {estimated_response}."
            )
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create support ticket: {str(e)}")
    
    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        """Get status of a specific ticket"""
        try:
            if ticket_id not in self.tickets:
                raise HTTPException(status_code=404, detail="Ticket not found")
            
            ticket = self.tickets[ticket_id]
            
            return {
                "success": True,
                "ticket": ticket.dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get ticket status")
    
    async def get_user_tickets(self) -> List[SupportTicket]:
        """Get all tickets for the current user"""
        try:
            # In production, this would filter by user ID
            # For demo, return all tickets sorted by creation date
            tickets = list(self.tickets.values())
            tickets.sort(key=lambda t: t.created_at, reverse=True)
            
            return tickets
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user tickets")
    
    def _assign_expert(self, document_type: str, urgency: str) -> Optional[ExpertProfile]:
        """Assign expert based on document type and availability"""
        # Map document types to expert specialties
        specialty_mapping = {
            "rental_agreement": "Real Estate Law",
            "employment_contract": "Contract Law", 
            "nda": "Contract Law",
            "loan_agreement": "Corporate Law",
            "partnership_agreement": "Corporate Law",
            "general_contract": "Contract Law"
        }
        
        preferred_specialty = specialty_mapping.get(document_type, "Contract Law")
        
        # Find available expert with matching specialty
        available_experts = [
            expert for expert in self.experts 
            if expert.availability_status == "available"
        ]
        
        # First try to match specialty
        for expert in available_experts:
            if expert.specialty == preferred_specialty:
                return expert
        
        # If no specialty match, return first available expert
        if available_experts:
            return available_experts[0]
        
        # If no available experts, return busy expert (they'll respond later)
        busy_experts = [
            expert for expert in self.experts 
            if expert.specialty == preferred_specialty
        ]
        
        return busy_experts[0] if busy_experts else self.experts[0]
    
    def _calculate_response_time(self, urgency: str, expert_response_time: str) -> str:
        """Calculate estimated response time"""
        if urgency == "high":
            return "< 2 hours"
        elif urgency == "medium":
            return expert_response_time
        else:  # low
            return "24-48 hours"
    
    def _schedule_expert_response(self, ticket_id: str, estimated_response: str):
        """Schedule a simulated expert response for demo purposes"""
        # In production, this would integrate with expert notification system
        # For demo, we'll simulate responses after a delay
        
        # Parse response time to determine delay
        if "< 2 hours" in estimated_response:
            delay_minutes = 5  # 5 minutes for demo
        elif "2-4 hours" in estimated_response:
            delay_minutes = 10  # 10 minutes for demo
        else:
            delay_minutes = 15  # 15 minutes for demo
        
        # In a real system, this would be handled by a background task queue
        # For demo, we'll just mark it as in_progress and provide a resolution
        import asyncio
        asyncio.create_task(self._simulate_expert_response(ticket_id, delay_minutes))
    
    async def _simulate_expert_response(self, ticket_id: str, delay_minutes: int):
        """Simulate expert response for demo"""
        try:
            # Wait for the delay
            await asyncio.sleep(delay_minutes * 60)  # Convert to seconds
            
            if ticket_id not in self.tickets:
                return
            
            ticket = self.tickets[ticket_id]
            
            # Generate simulated expert response
            resolution = self._generate_expert_response(ticket)
            
            # Update ticket with resolution
            ticket.status = "resolved"
            ticket.resolution = resolution
            ticket.resolved_at = datetime.now()
            
            self.tickets[ticket_id] = ticket
            
            logger.info(f"Simulated expert response generated for ticket {ticket_id}")
            
        except Exception as e:
            logger.error(f"Error simulating expert response: {e}")
    
    def _generate_expert_response(self, ticket: SupportTicket) -> TicketResolution:
        """Generate a simulated expert response based on the ticket"""
        # This would be replaced by actual expert input in production
        
        document_type = ticket.document_context.documentType if ticket.document_context else "contract"
        urgency = ticket.urgency_level
        question = ticket.user_question.lower()
        
        # Generate contextual response
        if "risk" in question or "dangerous" in question:
            summary = f"I've reviewed your {document_type} and the specific clause you're concerned about. The risk level appears to be manageable with proper precautions."
            recommendations = [
                "Consider adding a liability cap clause to limit your exposure",
                "Request clarification on any ambiguous terms before signing",
                "Have the other party provide written confirmation of key verbal agreements",
                "Consider consulting with a local attorney for jurisdiction-specific advice"
            ]
        elif "negotiate" in question or "change" in question:
            summary = f"Your {document_type} has several terms that could be improved through negotiation. I've identified specific areas where you have leverage."
            recommendations = [
                "Focus on the most important terms first - don't try to change everything",
                "Propose specific alternative language rather than just asking for changes",
                "Be prepared to offer concessions in less important areas",
                "Document all agreed changes in writing before finalizing"
            ]
        elif "understand" in question or "confus" in question:
            summary = f"I can help clarify the complex language in your {document_type}. Legal documents often use technical terms that can be simplified."
            recommendations = [
                "Focus on understanding your key obligations and rights",
                "Ask for a plain-language summary of critical terms",
                "Don't hesitate to ask for clarification on anything unclear",
                "Consider having key terms explained in writing"
            ]
        else:
            summary = f"I've reviewed your {document_type} and your specific question. Here's my professional assessment and recommendations."
            recommendations = [
                "The document appears to follow standard industry practices",
                "Pay special attention to termination and penalty clauses",
                "Ensure you understand all financial obligations",
                "Keep detailed records of all communications and agreements"
            ]
        
        return TicketResolution(
            summary=summary,
            recommendations=recommendations,
            expert_notes=f"Reviewed by {ticket.expert_name} - {ticket.expert_specialty} specialist",
            follow_up_needed=urgency == "high",
            estimated_review_time="15-30 minutes"
        )

# Initialize controller instance
support_controller = SupportController()


# Route handlers
@router.get("/experts", response_model=Dict[str, Any])
async def get_available_experts():
    """Get list of available experts"""
    return await support_controller.get_available_experts()


@router.post("/tickets", response_model=SupportTicketResponse)
@limiter.limit("5/minute")
async def create_support_ticket(request: Request, ticket_request: SupportTicketRequest):
    """Create a new support ticket"""
    return await support_controller.create_support_ticket(ticket_request)


@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_ticket_status(ticket_id: str):
    """Get status of a specific ticket"""
    return await support_controller.get_ticket_status(ticket_id)


@router.get("/tickets", response_model=List[SupportTicket])
async def get_user_tickets():
    """Get all tickets for the current user"""
    return await support_controller.get_user_tickets()