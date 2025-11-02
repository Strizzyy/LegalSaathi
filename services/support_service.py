"""
Support service for managing expert profiles and support tickets
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.support_models import (
    ExpertProfile, SupportTicket, SupportTicketRequest, 
    ExpertAvailability, TicketStatus, TicketPriority, SupportCategory
)

logger = logging.getLogger(__name__)


class SupportService:
    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, we'll use in-memory storage that can be replaced with DB calls
        self._experts = self._initialize_experts()
        self._tickets: Dict[str, SupportTicket] = {}
        self._requests: Dict[str, SupportTicketRequest] = {}
    
    def _initialize_experts(self) -> List[ExpertProfile]:
        """Initialize expert profiles - in production, this would come from database"""
        return [
            ExpertProfile(
                id="expert_1",
                name="Sarah Chen",
                specialty=["Contract Law", "Employment Law", "Business Agreements"],
                rating=4.9,
                response_time="< 2 hours",
                availability=ExpertAvailability.AVAILABLE,
                total_cases=156,
                success_rate=96.8,
                languages=["English", "Mandarin"],
                bio="Senior legal expert with 12+ years in contract law and business agreements."
            ),
            ExpertProfile(
                id="expert_2",
                name="Michael Rodriguez",
                specialty=["Real Estate", "Property Law", "Lease Agreements"],
                rating=4.8,
                response_time="< 4 hours",
                availability=ExpertAvailability.AVAILABLE,
                total_cases=203,
                success_rate=94.2,
                languages=["English", "Spanish"],
                bio="Real estate law specialist with extensive experience in residential and commercial properties."
            ),
            ExpertProfile(
                id="expert_3",
                name="Dr. Priya Sharma",
                specialty=["Intellectual Property", "Technology Law", "Privacy"],
                rating=4.9,
                response_time="< 1 hour",
                availability=ExpertAvailability.BUSY,
                total_cases=89,
                success_rate=98.1,
                languages=["English", "Hindi"],
                bio="IP and technology law expert with PhD in Legal Technology and 8+ years experience."
            ),
            ExpertProfile(
                id="expert_4",
                name="James Thompson",
                specialty=["Corporate Law", "Mergers & Acquisitions", "Securities"],
                rating=4.7,
                response_time="< 6 hours",
                availability=ExpertAvailability.AVAILABLE,
                total_cases=134,
                success_rate=92.5,
                languages=["English"],
                bio="Corporate law attorney specializing in M&A transactions and securities compliance."
            ),
            ExpertProfile(
                id="expert_5",
                name="Maria Gonzalez",
                specialty=["Immigration Law", "Family Law", "Consumer Protection"],
                rating=4.8,
                response_time="< 3 hours",
                availability=ExpertAvailability.AVAILABLE,
                total_cases=178,
                success_rate=95.3,
                languages=["English", "Spanish", "Portuguese"],
                bio="Immigration and family law expert with focus on consumer protection and civil rights."
            )
        ]
    
    async def get_available_experts(self) -> List[ExpertProfile]:
        """Get list of available experts"""
        try:
            # Filter experts by availability
            available_experts = [
                expert for expert in self._experts 
                if expert.availability in [ExpertAvailability.AVAILABLE, ExpertAvailability.BUSY]
            ]
            
            # Sort by rating and availability
            available_experts.sort(key=lambda x: (
                0 if x.availability == ExpertAvailability.AVAILABLE else 1,
                -x.rating
            ))
            
            return available_experts
        except Exception as e:
            logger.error(f"Error getting available experts: {e}")
            return []
    
    async def get_expert_by_id(self, expert_id: str) -> Optional[ExpertProfile]:
        """Get expert by ID"""
        try:
            for expert in self._experts:
                if expert.id == expert_id:
                    return expert
            return None
        except Exception as e:
            logger.error(f"Error getting expert {expert_id}: {e}")
            return None
    
    async def create_support_ticket(self, request: SupportTicketRequest) -> SupportTicket:
        """Create a new support ticket"""
        try:
            # Generate IDs
            request_id = f"req_{uuid.uuid4().hex[:8]}"
            ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"
            
            # Store the request
            self._requests[request_id] = request
            
            # Find best expert for this request
            expert = await self._find_best_expert(request)
            
            # Determine priority and estimated response
            priority = self._determine_priority(request)
            estimated_response = self._calculate_estimated_response(priority, expert)
            
            # Create ticket
            ticket = SupportTicket(
                id=ticket_id,
                request_id=request_id,
                status=TicketStatus.ASSIGNED if expert else TicketStatus.PENDING,
                priority=priority,
                estimated_response=estimated_response,
                expert_id=expert.id if expert else None,
                expert_name=expert.name if expert else None,
                expert_specialty=", ".join(expert.specialty[:2]) if expert else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store ticket
            self._tickets[ticket_id] = ticket
            
            # Simulate expert assignment notification
            if expert:
                logger.info(f"Ticket {ticket_id} assigned to expert {expert.name}")
            
            return ticket
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            raise
    
    async def get_ticket_status(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get ticket status by ID"""
        try:
            ticket = self._tickets.get(ticket_id)
            if ticket:
                # Simulate ticket progress for demo
                await self._simulate_ticket_progress(ticket)
            return ticket
        except Exception as e:
            logger.error(f"Error getting ticket status {ticket_id}: {e}")
            return None
    
    async def get_user_tickets(self, limit: int = 10) -> List[SupportTicket]:
        """Get user's tickets (in real app, would filter by user ID)"""
        try:
            tickets = list(self._tickets.values())
            tickets.sort(key=lambda x: x.created_at, reverse=True)
            return tickets[:limit]
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    async def _find_best_expert(self, request: SupportTicketRequest) -> Optional[ExpertProfile]:
        """Find the best available expert for the request"""
        try:
            available_experts = await self.get_available_experts()
            if not available_experts:
                return None
            
            # Score experts based on specialty match and availability
            scored_experts = []
            
            for expert in available_experts:
                score = expert.rating * 10  # Base score from rating
                
                # Bonus for specialty match
                if self._matches_specialty(expert, request):
                    score += 20
                
                # Penalty for being busy
                if expert.availability == ExpertAvailability.BUSY:
                    score -= 10
                
                # Bonus for fast response time
                if "< 1 hour" in expert.response_time:
                    score += 15
                elif "< 2 hour" in expert.response_time:
                    score += 10
                
                scored_experts.append((expert, score))
            
            # Sort by score and return best match
            scored_experts.sort(key=lambda x: x[1], reverse=True)
            return scored_experts[0][0] if scored_experts else None
            
        except Exception as e:
            logger.error(f"Error finding best expert: {e}")
            return None
    
    def _matches_specialty(self, expert: ExpertProfile, request: SupportTicketRequest) -> bool:
        """Check if expert specialty matches request"""
        try:
            category = request.category.value.lower()
            doc_type = ""
            
            if request.document_context:
                doc_type = request.document_context.get("documentType", "").lower()
            
            for specialty in expert.specialty:
                specialty_lower = specialty.lower()
                
                # Direct category matches
                if category == "contract_terms" and "contract" in specialty_lower:
                    return True
                if category == "legal_clarification" and "law" in specialty_lower:
                    return True
                if category == "risk_assessment" and any(term in specialty_lower for term in ["contract", "law", "legal"]):
                    return True
                
                # Document type matches
                if "employment" in doc_type and "employment" in specialty_lower:
                    return True
                if "real estate" in doc_type and "real estate" in specialty_lower:
                    return True
                if "lease" in doc_type and "lease" in specialty_lower:
                    return True
                if "property" in doc_type and "property" in specialty_lower:
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error matching specialty: {e}")
            return False
    
    def _determine_priority(self, request: SupportTicketRequest) -> TicketPriority:
        """Determine ticket priority based on request"""
        try:
            urgency = request.urgency_level.lower()
            
            if urgency == "high":
                return TicketPriority.URGENT
            elif urgency == "medium":
                return TicketPriority.HIGH
            elif urgency == "low":
                return TicketPriority.MEDIUM
            
            # Check for high-risk indicators in the question
            question_lower = request.user_question.lower()
            high_risk_terms = ["urgent", "deadline", "court", "lawsuit", "penalty", "terminate", "breach"]
            
            if any(term in question_lower for term in high_risk_terms):
                return TicketPriority.HIGH
            
            return TicketPriority.MEDIUM
            
        except Exception as e:
            logger.error(f"Error determining priority: {e}")
            return TicketPriority.MEDIUM
    
    def _calculate_estimated_response(self, priority: TicketPriority, expert: Optional[ExpertProfile]) -> str:
        """Calculate estimated response time"""
        try:
            if not expert:
                return "24-48 hours (pending expert assignment)"
            
            base_time = expert.response_time
            
            if priority == TicketPriority.URGENT:
                return "< 30 minutes"
            elif priority == TicketPriority.HIGH:
                return "< 1 hour"
            elif priority == TicketPriority.MEDIUM:
                return base_time
            else:  # LOW
                return "4-8 hours"
                
        except Exception as e:
            logger.error(f"Error calculating estimated response: {e}")
            return "4-8 hours"
    
    async def _simulate_ticket_progress(self, ticket: SupportTicket) -> None:
        """Simulate ticket progress for demo purposes"""
        try:
            # Check if ticket is old enough to be "resolved"
            time_since_creation = datetime.utcnow() - ticket.created_at
            
            if (ticket.status == TicketStatus.ASSIGNED and 
                time_since_creation > timedelta(minutes=2)):  # 2 minutes for demo
                
                ticket.status = TicketStatus.RESOLVED
                ticket.updated_at = datetime.utcnow()
                ticket.resolution = {
                    "summary": "Your question has been reviewed by our legal expert.",
                    "recommendations": [
                        "Consider consulting with a local attorney for jurisdiction-specific advice",
                        "Review the clause with the other party before signing",
                        "Keep documentation of all communications regarding this agreement"
                    ],
                    "follow_up_required": False,
                    "expert_notes": "Standard legal language with acceptable risk levels. No immediate concerns identified."
                }
                
                # Update the stored ticket
                self._tickets[ticket.id] = ticket
                
        except Exception as e:
            logger.error(f"Error simulating ticket progress: {e}")
    
    async def update_expert_availability(self, expert_id: str, availability: ExpertAvailability) -> bool:
        """Update expert availability status"""
        try:
            for expert in self._experts:
                if expert.id == expert_id:
                    expert.availability = availability
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating expert availability: {e}")
            return False