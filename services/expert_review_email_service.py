"""
Expert Review Email Service for Human-in-the-Loop System
Handles email notifications for expert review queue and results
"""

import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from jinja2 import Template, Environment, BaseLoader

from models.email_models import (
    EmailSendRequest, EmailSendResponse, EmailDeliveryStatus, 
    EmailAttachment, EmailPriority
)
from models.expert_queue_models import (
    ExpertReviewItemResponse, ExpertAnalysisResponse, ReviewStatus
)
from models.document_models import DocumentAnalysisResponse
from services.gmail_service import GmailService
from services.smtp_email_service import SMTPEmailService

logger = logging.getLogger(__name__)


class ExpertReviewEmailService:
    """Enhanced email service for expert review notifications"""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.smtp_service = SMTPEmailService()
        self.template_env = Environment(loader=BaseLoader())
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Email templates
        self.templates = {
            'review_queued': self._get_review_queued_template(),
            'expert_results': self._get_expert_results_template(),
            'review_status_update': self._get_status_update_template()
        }
        
        logger.info("Expert Review Email Service initialized")
    
    def is_available(self) -> bool:
        """Check if email service is available"""
        return self.gmail_service.is_available() or self.smtp_service.is_available()
    
    async def send_review_queued_notification(
        self,
        user_email: str,
        review_id: str,
        estimated_time_hours: int = 24,
        confidence_score: float = 0.0,
        user_id: Optional[str] = None
    ) -> EmailSendResponse:
        """Send notification that document is queued for expert review"""
        
        if not self.is_available():
            return EmailSendResponse(
                success=False,
                error="Email service not available",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        try:
            # Generate email content
            template_vars = {
                'review_id': review_id,
                'estimated_time': f"{estimated_time_hours} hours",
                'confidence_score': round(confidence_score * 100, 1),
                'tracking_url': f"{os.getenv('BASE_URL', 'https://legalsaathi.com')}/track/{review_id}",
                'current_year': datetime.now().year
            }
            
            subject = "Your Document is Being Reviewed by a Legal Expert"
            html_content = self.templates['review_queued'].render(**template_vars)
            text_content = self._generate_review_queued_text(**template_vars)
            
            # Send with retry logic
            return await self._send_email_with_retry(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                user_id=user_id or user_email,
                priority=EmailPriority.HIGH
            )
            
        except Exception as e:
            logger.error(f"Failed to send review queued notification: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Failed to send notification: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    async def send_expert_analysis_results(
        self,
        user_email: str,
        expert_analysis: ExpertAnalysisResponse,
        pdf_content: bytes,
        user_id: Optional[str] = None
    ) -> EmailSendResponse:
        """Send expert-reviewed analysis results to user"""
        
        if not self.is_available():
            return EmailSendResponse(
                success=False,
                error="Email service not available",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        try:
            # Generate email content
            template_vars = {
                'review_id': expert_analysis.review_id,
                'expert_id': expert_analysis.expert_id,
                'completed_at': expert_analysis.completed_at.strftime('%B %d, %Y at %I:%M %p'),
                'review_duration': expert_analysis.review_duration_minutes,
                'confidence_improvement': round(expert_analysis.confidence_improvement * 100, 1),
                'feedback_url': f"{os.getenv('BASE_URL', 'https://legalsaathi.com')}/feedback/{expert_analysis.review_id}",
                'current_year': datetime.now().year
            }
            
            subject = "Expert Legal Analysis Complete - Your Document Review"
            html_content = self.templates['expert_results'].render(**template_vars)
            text_content = self._generate_expert_results_text(**template_vars)
            
            # Create expert-certified PDF attachment
            attachment = EmailAttachment(
                filename=f"expert_analysis_{expert_analysis.review_id}.pdf",
                content_type="application/pdf",
                size=len(pdf_content),
                data=pdf_content
            )
            
            # Send with retry logic
            return await self._send_email_with_retry(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=[attachment],
                user_id=user_id or user_email,
                priority=EmailPriority.HIGH
            )
            
        except Exception as e:
            logger.error(f"Failed to send expert analysis results: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Failed to send results: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    async def send_review_status_update(
        self,
        user_email: str,
        review_id: str,
        status: ReviewStatus,
        expert_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> EmailSendResponse:
        """Send status update notification to user"""
        
        if not self.is_available():
            return EmailSendResponse(
                success=False,
                error="Email service not available",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        try:
            # Generate email content based on status
            status_messages = {
                ReviewStatus.IN_REVIEW: "Your document is now being reviewed by a legal expert",
                ReviewStatus.COMPLETED: "Your expert review has been completed",
                ReviewStatus.CANCELLED: "Your review request has been cancelled"
            }
            
            template_vars = {
                'review_id': review_id,
                'status': status.value.replace('_', ' ').title(),
                'status_message': status_messages.get(status, f"Status updated to {status.value}"),
                'expert_name': expert_name or "Legal Expert",
                'tracking_url': f"{os.getenv('BASE_URL', 'https://legalsaathi.com')}/track/{review_id}",
                'current_year': datetime.now().year
            }
            
            subject = f"Review Status Update - {review_id}"
            html_content = self.templates['review_status_update'].render(**template_vars)
            text_content = self._generate_status_update_text(**template_vars)
            
            # Send with retry logic
            return await self._send_email_with_retry(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                user_id=user_id or user_email,
                priority=EmailPriority.NORMAL
            )
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Failed to send update: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    async def _send_email_with_retry(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        attachments: List[EmailAttachment] = None,
        user_id: str = None,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> EmailSendResponse:
        """Send email with retry logic (3 attempts)"""
        
        attachments = attachments or []
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Email send attempt {attempt}/{self.max_retries} to {to_email}")
                
                # Try SMTP first (more reliable)
                if self.smtp_service.is_available():
                    if attachments and len(attachments) > 0:
                        # Use SMTP for emails with attachments
                        response = await self._send_via_smtp_with_attachment(
                            to_email, subject, html_content, text_content, 
                            attachments[0].data if attachments else None, user_id
                        )
                    else:
                        # Use SMTP for simple emails
                        response = await self._send_via_smtp_simple(
                            to_email, subject, html_content, text_content, user_id
                        )
                    
                    if response.success:
                        logger.info(f"Email sent successfully via SMTP on attempt {attempt}")
                        return response
                    else:
                        last_error = response.error
                
                # Fallback to Gmail API
                elif self.gmail_service.is_available():
                    email_request = EmailSendRequest(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        attachments=attachments,
                        priority=priority
                    )
                    
                    response = await self.gmail_service._send_email(email_request)
                    
                    if response.success:
                        logger.info(f"Email sent successfully via Gmail API on attempt {attempt}")
                        return response
                    else:
                        last_error = response.error
                
                else:
                    return EmailSendResponse(
                        success=False,
                        error="No email service available",
                        delivery_status=EmailDeliveryStatus.FAILED
                    )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Email send attempt {attempt} failed: {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * attempt)
        
        # All attempts failed
        logger.error(f"All {self.max_retries} email send attempts failed. Last error: {last_error}")
        return EmailSendResponse(
            success=False,
            error=f"Failed after {self.max_retries} attempts: {last_error}",
            delivery_status=EmailDeliveryStatus.FAILED
        )
    
    async def _send_via_smtp_with_attachment(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        pdf_content: Optional[bytes],
        user_id: str
    ) -> EmailSendResponse:
        """Send email via SMTP with PDF attachment"""
        return await self.smtp_service._send_smtp_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            pdf_content=pdf_content
        )
    
    async def _send_via_smtp_simple(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        user_id: str
    ) -> EmailSendResponse:
        """Send simple email via SMTP without attachments"""
        return await self.smtp_service._send_smtp_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            pdf_content=None
        ) 
   
    def _get_review_queued_template(self) -> Template:
        """Get HTML template for review queued notification"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Queued for Expert Review</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }
        .content { padding: 30px; }
        .expert-badge { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 25px 0; }
        .expert-badge h2 { margin: 0 0 10px 0; font-size: 24px; }
        .expert-badge p { margin: 0; opacity: 0.9; }
        .review-info { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin: 25px 0; }
        .info-row { display: flex; justify-content: space-between; margin: 10px 0; }
        .info-label { font-weight: 600; color: #475569; }
        .info-value { color: #1e293b; }
        .timeline { background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0; }
        .timeline h3 { margin: 0 0 15px 0; color: #1d4ed8; }
        .timeline-item { margin: 10px 0; padding-left: 20px; position: relative; }
        .timeline-item:before { content: '•'; position: absolute; left: 0; color: #3b82f6; font-weight: bold; }
        .tracking-section { background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center; }
        .tracking-link { display: inline-block; background-color: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px; }
        .tracking-link:hover { background-color: #d97706; }
        .footer { background-color: #1e293b; color: white; padding: 25px; text-align: center; }
        .footer p { margin: 5px 0; }
        .disclaimer { font-size: 12px; color: #94a3b8; margin-top: 15px; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Expert Review Requested</h1>
            <p>Your Document is Being Reviewed by Legal Professionals</p>
        </div>
        
        <div class="content">
            <p>Dear Client,</p>
            <p>Thank you for choosing LegalSaathi for your document analysis needs. Due to the complexity of your document, we have assigned it to one of our qualified legal experts for professional review to ensure you receive the most accurate and comprehensive analysis possible.</p>
            
            <div class="expert-badge">
                <h2>Expert Review in Progress</h2>
                <p>Your document will be reviewed by a certified legal professional</p>
            </div>
            
            <div class="review-info">
                <h3>Review Details</h3>
                <div class="info-row">
                    <span class="info-label">Review ID:</span>
                    <span class="info-value">{{ review_id }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Estimated Review Time:</span>
                    <span class="info-value">{{ estimated_time }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value">Queued for Expert Review</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Priority:</span>
                    <span class="info-value">High (Low AI Confidence)</span>
                </div>
            </div>
            
            <div class="timeline">
                <h3>What Happens Next</h3>
                <div class="timeline-item">Your document is assigned to the next available expert</div>
                <div class="timeline-item">Expert conducts thorough legal analysis</div>
                <div class="timeline-item">Analysis is reviewed and certified</div>
                <div class="timeline-item">You receive expert-reviewed results via email</div>
            </div>
            
            <div class="tracking-section">
                <h3>Track Your Review</h3>
                <p>You can check the status of your review at any time using your Review ID.</p>
                <a href="{{ tracking_url }}" class="tracking-link">Track Review Status</a>
            </div>
            
            <p><strong>Why Expert Review?</strong></p>
            <ul>
                <li><strong>Higher Accuracy:</strong> Human experts catch nuances AI might miss</li>
                <li><strong>Complex Analysis:</strong> Professional interpretation of legal language</li>
                <li><strong>Quality Assurance:</strong> Double-checked results you can trust</li>
                <li><strong>Expert Certification:</strong> Analysis backed by legal professionals</li>
            </ul>
            
            <p>You will receive your comprehensive expert-reviewed analysis via email once the review is complete. We will notify you immediately when your professional analysis is ready.</p>
            
            <p>Sincerely,<br>
            <strong>The LegalSaathi Expert Review Team</strong></p>
        </div>
        
        <div class="footer">
            <p><strong>LegalSaathi Document Advisor</strong></p>
            <p>Professional Legal Analysis with Expert Human Oversight</p>
            <div class="disclaimer">
                Expert reviews are conducted by qualified legal professionals. This service provides 
                legal analysis for informational purposes and does not constitute an attorney-client 
                relationship or legal advice. Please consult with a licensed attorney for specific legal matters.
            </div>
        </div>
    </div>
</body>
</html>
        """
        return self.template_env.from_string(template_str.strip())
    
    def _get_expert_results_template(self) -> Template:
        """Get HTML template for expert results notification"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expert Legal Analysis Complete</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }
        .content { padding: 30px; }
        .expert-certification { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; margin: 25px 0; }
        .expert-certification h2 { margin: 0 0 10px 0; font-size: 24px; }
        .expert-certification p { margin: 0; opacity: 0.9; font-size: 16px; }
        .certification-badge { display: inline-block; background-color: rgba(255, 255, 255, 0.2); padding: 8px 16px; border-radius: 20px; margin-top: 10px; font-weight: 600; }
        .review-summary { background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 25px 0; }
        .summary-row { display: flex; justify-content: space-between; margin: 10px 0; }
        .summary-label { font-weight: 600; color: #166534; }
        .summary-value { color: #15803d; }
        .attachment-info { background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center; }
        .attachment-info h3 { margin: 0 0 15px 0; color: #92400e; }
        .attachment-features { text-align: left; margin: 15px 0; }
        .attachment-features li { margin: 8px 0; }
        .feedback-section { background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center; }
        .feedback-link { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px; }
        .feedback-link:hover { background-color: #2563eb; }
        .footer { background-color: #1e293b; color: white; padding: 25px; text-align: center; }
        .footer p { margin: 5px 0; }
        .disclaimer { font-size: 12px; color: #94a3b8; margin-top: 15px; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Expert Analysis Complete</h1>
            <p>Your Document Has Been Professionally Reviewed</p>
        </div>
        
        <div class="content">
            <p>Dear Client,</p>
            <p>We are pleased to inform you that your legal document analysis has been completed by our expert legal team. The comprehensive professional review is now ready and attached to this email.</p>
            
            <div class="expert-certification">
                <h2>Expert Certified Analysis</h2>
                <p>Reviewed and approved by qualified legal professionals</p>
                <div class="certification-badge">EXPERT VERIFIED</div>
            </div>
            
            <div class="review-summary">
                <h3>Review Summary</h3>
                <div class="summary-row">
                    <span class="summary-label">Review ID:</span>
                    <span class="summary-value">{{ review_id }}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Completed:</span>
                    <span class="summary-value">{{ completed_at }}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Review Duration:</span>
                    <span class="summary-value">{{ review_duration }} minutes</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Confidence Improvement:</span>
                    <span class="summary-value">+{{ confidence_improvement }}%</span>
                </div>
            </div>
            
            <div class="attachment-info">
                <h3>Expert-Certified Report Attached</h3>
                <p>Your comprehensive legal analysis is attached as a professionally formatted PDF document.</p>
                <div class="attachment-features">
                    <strong>This expert-reviewed report includes:</strong>
                    <ul>
                        <li>Expert-verified clause analysis with professional insights</li>
                        <li>Enhanced risk assessment with legal precedent context</li>
                        <li>Detailed recommendations from legal professionals</li>
                        <li>Improved accuracy and confidence ratings</li>
                        <li>Expert certification and review credentials</li>
                        <li>Professional legal opinion and guidance</li>
                    </ul>
                </div>
            </div>
            
            <p><strong>What Makes This Different?</strong></p>
            <ul>
                <li><strong>Human Expertise:</strong> Reviewed by qualified legal professionals</li>
                <li><strong>Enhanced Accuracy:</strong> {{ confidence_improvement }}% improvement in analysis confidence</li>
                <li><strong>Legal Context:</strong> Professional interpretation with legal precedent</li>
                <li><strong>Quality Assured:</strong> Double-checked and certified by experts</li>
            </ul>
            
            <div class="feedback-section">
                <h3>Help Us Improve</h3>
                <p>Your feedback helps us provide better expert review services.</p>
                <a href="{{ feedback_url }}" class="feedback-link">Rate This Review</a>
            </div>
            
            <p>Should you have any questions regarding this expert analysis or require further clarification on any aspect of the review, please feel free to contact our professional support team.</p>
            
            <p>Thank you for choosing LegalSaathi's expert review service.</p>
            
            <p>Sincerely,<br>
            <strong>The LegalSaathi Expert Review Team</strong></p>
        </div>
        
        <div class="footer">
            <p><strong>LegalSaathi Document Advisor</strong></p>
            <p>Professional Legal Analysis with Expert Human Oversight</p>
            <div class="disclaimer">
                This expert analysis is provided by qualified legal professionals for informational 
                purposes and does not constitute an attorney-client relationship or legal advice. 
                For specific legal matters requiring professional representation, please consult 
                with a licensed attorney in your jurisdiction.
            </div>
        </div>
    </div>
</body>
</html>
        """
        return self.template_env.from_string(template_str.strip())
    
    def _get_status_update_template(self) -> Template:
        """Get HTML template for status update notifications"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Status Update</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }
        .content { padding: 30px; }
        .status-update { background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0; }
        .status-update h3 { margin: 0 0 10px 0; color: #1d4ed8; }
        .tracking-section { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center; }
        .tracking-link { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px; }
        .tracking-link:hover { background-color: #2563eb; }
        .footer { background-color: #1e293b; color: white; padding: 25px; text-align: center; }
        .footer p { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Review Status Update</h1>
            <p>Your Document Review Progress</p>
        </div>
        
        <div class="content">
            <p>Hello,</p>
            <p>We wanted to update you on the status of your document review.</p>
            
            <div class="status-update">
                <h3>Status Update</h3>
                <p><strong>Review ID:</strong> {{ review_id }}</p>
                <p><strong>New Status:</strong> {{ status }}</p>
                <p><strong>Update:</strong> {{ status_message }}</p>
                {% if expert_name %}
                <p><strong>Assigned Expert:</strong> {{ expert_name }}</p>
                {% endif %}
            </div>
            
            <div class="tracking-section">
                <h3>Track Your Review</h3>
                <p>For real-time updates and detailed status information:</p>
                <a href="{{ tracking_url }}" class="tracking-link">View Review Status</a>
            </div>
            
            <p>We'll continue to keep you updated as your review progresses. You'll receive another notification when your expert analysis is complete.</p>
            
            <p>Best regards,<br>
            <strong>LegalSaathi Expert Review Team</strong></p>
        </div>
        
        <div class="footer">
            <p><strong>LegalSaathi Document Advisor</strong></p>
            <p>AI-Powered Legal Analysis with Expert Human Oversight</p>
        </div>
    </div>
</body>
</html>
        """
        return self.template_env.from_string(template_str.strip())
    
    def _generate_review_queued_text(self, **kwargs) -> str:
        """Generate plain text version of review queued email"""
        return f"""
DOCUMENT QUEUED FOR EXPERT REVIEW
=================================

Dear Client,

Thank you for choosing LegalSaathi for your document analysis needs. Due to 
the complexity of your document, we have assigned it to one of our qualified 
legal experts for professional review to ensure you receive the most accurate 
and comprehensive analysis possible.

EXPERT REVIEW IN PROGRESS
Your document will be reviewed by a certified legal professional

REVIEW DETAILS
==============
Review ID: {kwargs['review_id']}
Estimated Review Time: {kwargs['estimated_time']}
Status: Queued for Expert Review
Priority: Professional Review Required

WHAT HAPPENS NEXT
=================
• Your document is assigned to the next available expert
• Expert conducts thorough legal analysis
• Analysis is reviewed and certified
• You receive expert-reviewed results via email

TRACK YOUR REVIEW
=================
You can check the status of your review at any time using your Review ID.
Track Review Status: {kwargs['tracking_url']}

WHY EXPERT REVIEW?
==================
• Higher Accuracy: Human experts catch nuances that automated systems might miss
• Complex Analysis: Professional interpretation of legal language
• Quality Assurance: Double-checked results you can trust
• Expert Certification: Analysis backed by legal professionals

You will receive your comprehensive expert-reviewed analysis via email once 
the review is complete. We will notify you immediately when your professional 
analysis is ready.

Sincerely,
The LegalSaathi Expert Review Team

---
LegalSaathi Document Advisor
Professional Legal Analysis with Expert Human Oversight

DISCLAIMER: Expert reviews are conducted by qualified legal professionals. 
This service provides legal analysis for informational purposes and does not 
constitute an attorney-client relationship or legal advice. Please consult with 
a licensed attorney for specific legal matters.
        """.strip()
    
    def _generate_expert_results_text(self, **kwargs) -> str:
        """Generate plain text version of expert results email"""
        return f"""
EXPERT LEGAL ANALYSIS COMPLETE
==============================

Dear Client,

We are pleased to inform you that your legal document analysis has been 
completed by our expert legal team. The comprehensive professional review 
is now ready and attached to this email.

EXPERT CERTIFIED ANALYSIS
Reviewed and approved by qualified legal professionals
EXPERT VERIFIED

REVIEW SUMMARY
==============
Review ID: {kwargs['review_id']}
Completed: {kwargs['completed_at']}
Review Duration: {kwargs['review_duration']} minutes
Confidence Improvement: +{kwargs['confidence_improvement']}%

EXPERT-CERTIFIED REPORT ATTACHED
================================
Your comprehensive legal analysis is attached as a professionally 
formatted PDF document.

This expert-reviewed report includes:
• Expert-verified clause analysis with professional insights
• Enhanced risk assessment with legal precedent context
• Detailed recommendations from legal professionals
• Improved accuracy and confidence ratings
• Expert certification and review credentials
• Professional legal opinion and guidance

WHAT MAKES THIS DIFFERENT?
==========================
• Human Expertise: Reviewed by qualified legal professionals
• Enhanced Accuracy: {kwargs['confidence_improvement']}% improvement in analysis confidence
• Legal Context: Professional interpretation with legal precedent
• Quality Assured: Double-checked and certified by experts

HELP US IMPROVE
===============
Your feedback helps us provide better expert review services.
Rate This Review: {kwargs['feedback_url']}

Should you have any questions regarding this expert analysis or require 
further clarification on any aspect of the review, please feel free to 
contact our professional support team.

Thank you for choosing LegalSaathi's expert review service.

Sincerely,
The LegalSaathi Expert Review Team

---
LegalSaathi Document Advisor
Professional Legal Analysis with Expert Human Oversight

DISCLAIMER: This expert analysis is provided by qualified legal professionals 
for informational purposes and does not constitute an attorney-client relationship 
or legal advice. For specific legal matters requiring professional representation, 
please consult with a licensed attorney in your jurisdiction.
        """.strip()
    
    def _generate_status_update_text(self, **kwargs) -> str:
        """Generate plain text version of status update email"""
        expert_info = f"\nAssigned Expert: {kwargs['expert_name']}" if kwargs.get('expert_name') else ""
        
        return f"""
REVIEW STATUS UPDATE
===================

Dear Client,

We would like to update you on the status of your document review.

STATUS UPDATE
=============
Review ID: {kwargs['review_id']}
New Status: {kwargs['status']}
Update: {kwargs['status_message']}{expert_info}

TRACK YOUR REVIEW
=================
For real-time updates and detailed status information:
{kwargs['tracking_url']}

We will continue to keep you updated as your review progresses. You will receive 
another notification when your expert analysis is complete.

Sincerely,
The LegalSaathi Expert Review Team

---
LegalSaathi Document Advisor
Professional Legal Analysis with Expert Human Oversight
        """.strip()