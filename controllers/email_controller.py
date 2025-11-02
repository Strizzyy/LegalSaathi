"""
Email controller for sending analysis reports via Gmail
"""

import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, Depends

from models.email_models import (
    EmailNotificationRequest, EmailNotificationResponse,
    EmailRateLimitInfo, EmailDeliveryStatus
)
from models.document_models import DocumentAnalysisResponse
from services.gmail_service import GmailService
from controllers.export_controller import ExportController
# Remove the incorrect import - we'll get user from request.state instead

logger = logging.getLogger(__name__)


class EmailController:
    """Controller for email notification operations"""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.export_controller = ExportController()
        self.temp_files = []  # Track temporary files for cleanup
    
    async def send_analysis_email(
        self, 
        request: EmailNotificationRequest,
        analysis_data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None
    ) -> EmailNotificationResponse:
        """Send analysis report via email with PDF attachment"""
        
        try:
            # Validate Gmail service availability
            if not self.gmail_service.is_available():
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message="Email service is currently unavailable. Please try again later or contact support."
                )
            
            # Get user ID for rate limiting
            user_id = current_user.get('uid', 'anonymous') if current_user else 'anonymous'
            
            # Check rate limits
            rate_limit_info = self.gmail_service.check_rate_limit(user_id)
            if rate_limit_info.is_rate_limited:
                retry_after = int((rate_limit_info.next_reset_time - datetime.now()).total_seconds())
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message=f"Rate limit exceeded. You can send {rate_limit_info.hourly_limit} emails per hour. Please try again in {retry_after} seconds."
                )
            
            # Parse analysis data
            try:
                analysis_dict = analysis_data.get('analysis')
                if not isinstance(analysis_dict, dict):
                    raise ValueError("Invalid analysis data format")
                
                # Convert frontend format to backend format
                converted_analysis = self._convert_frontend_to_backend_format(analysis_dict)
                analysis = DocumentAnalysisResponse(**converted_analysis)
                
            except Exception as e:
                logger.error(f"Failed to parse analysis data: {e}")
                logger.error(f"Analysis data structure: {analysis_data}")
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message="Invalid analysis data. Please regenerate the analysis."
                )
            
            # Generate PDF content
            try:
                if request.include_pdf:
                    pdf_content = await self.export_controller.generate_enhanced_pdf(analysis)
                    if not pdf_content or len(pdf_content) == 0:
                        logger.warning("PDF generation returned empty content, trying fallback")
                        # Try fallback PDF generation
                        pdf_content = await self.export_controller._generate_simple_pdf_content({'analysis': analysis.model_dump()})
                        if not pdf_content or len(pdf_content) == 0:
                            raise Exception("Both enhanced and simple PDF generation failed")
                    logger.info(f"PDF generated successfully, size: {len(pdf_content)} bytes")
                else:
                    pdf_content = b""  # Empty PDF content if not requested
                    
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message="Failed to generate PDF report. Please try again."
                )
            
            # Send email
            try:
                email_response = await self.gmail_service.send_analysis_report(
                    user_email=request.user_email,
                    analysis_result=analysis,
                    pdf_content=pdf_content,
                    user_id=user_id,
                    custom_message=request.custom_message
                )
                
                if email_response.success:
                    logger.info(f"Analysis email sent successfully to {request.user_email}")
                    return EmailNotificationResponse(
                        success=True,
                        message_id=email_response.message_id,
                        delivery_status=EmailDeliveryStatus.SENT.value
                    )
                else:
                    logger.error(f"Email sending failed: {email_response.error}")
                    return EmailNotificationResponse(
                        success=False,
                        delivery_status=EmailDeliveryStatus.FAILED.value,
                        error_message=email_response.error or "Failed to send email"
                    )
                    
            except Exception as e:
                logger.error(f"Email sending error: {e}")
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message=f"Email sending failed: {str(e)}"
                )
            
        except Exception as e:
            logger.error(f"Unexpected error in send_analysis_email: {e}")
            return EmailNotificationResponse(
                success=False,
                delivery_status=EmailDeliveryStatus.FAILED.value,
                error_message="An unexpected error occurred. Please try again."
            )
        finally:
            # Cleanup temporary files
            await self._cleanup_temp_files()
    
    async def get_email_rate_limit_info(self, user_id: str) -> EmailRateLimitInfo:
        """Get rate limit information for user"""
        return self.gmail_service.check_rate_limit(user_id)
    
    async def test_email_service(self) -> Dict[str, Any]:
        """Test email service availability and configuration"""
        try:
            is_available = self.gmail_service.is_available()
            smtp_available = self.gmail_service.smtp_service and self.gmail_service.smtp_service.is_available()
            gmail_api_available = self.gmail_service.gmail_client is not None
            
            return {
                "success": True,
                "email_service_available": is_available,
                "smtp_service_available": smtp_available,
                "smtp_configured": smtp_available,
                "gmail_api_available": gmail_api_available,
                "gmail_client_initialized": self.gmail_service.gmail_client is not None,
                "credentials_available": self.gmail_service.credentials is not None,
                "primary_service": "SMTP" if smtp_available else "Gmail API" if gmail_api_available else "None",
                "sender_email": self.gmail_service.smtp_service.sender_email if smtp_available else "Not configured",
                "message": "Email service ready (SMTP)" if smtp_available else "Email service ready (Gmail API)" if gmail_api_available else "Email service not configured"
            }
        except Exception as e:
            logger.error(f"Email service test failed: {e}")
            return {
                "success": False,
                "email_service_available": False,
                "error": str(e),
                "message": "Email service test failed"
            }
    
    def _convert_frontend_to_backend_format(self, frontend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Convert frontend AnalysisResult format to backend DocumentAnalysisResponse format"""
        
        # Convert clause data from frontend format to backend format
        clause_assessments = []
        for clause in frontend_analysis.get('analysis_results', []):
            # Convert risk_level to risk_assessment
            risk_level = clause.get('risk_level', {})
            risk_assessment = {
                'level': risk_level.get('level', 'GREEN'),
                'score': risk_level.get('score', 0.0),
                'reasons': [],  # Frontend doesn't have this, use empty list
                'severity': risk_level.get('severity', 'low'),
                'confidence_percentage': risk_level.get('confidence_percentage', 0),
                'risk_categories': risk_level.get('risk_categories', {}),
                'low_confidence_warning': risk_level.get('low_confidence_warning', False)
            }
            
            clause_assessment = {
                'clause_id': clause.get('clause_id', ''),
                'clause_text': clause.get('clause_text', ''),
                'risk_assessment': risk_assessment,
                'plain_explanation': clause.get('plain_explanation', ''),
                'legal_implications': clause.get('legal_implications', []),
                'recommendations': clause.get('recommendations', []),
                'translation_available': False
            }
            clause_assessments.append(clause_assessment)
        
        # Convert overall risk
        overall_risk = frontend_analysis.get('overall_risk', {})
        backend_overall_risk = {
            'level': overall_risk.get('level', 'GREEN'),
            'score': overall_risk.get('score', 0.0),
            'reasons': [],  # Frontend doesn't have this, use empty list
            'severity': 'low',  # Frontend doesn't have this, use default
            'confidence_percentage': overall_risk.get('confidence_percentage', 0),
            'risk_categories': overall_risk.get('risk_categories', {}),
            'low_confidence_warning': overall_risk.get('low_confidence_warning', False)
        }
        
        # Create backend format
        backend_analysis = {
            'analysis_id': f"analysis_{datetime.now().timestamp()}",
            'overall_risk': backend_overall_risk,
            'clause_assessments': clause_assessments,
            'summary': frontend_analysis.get('summary', ''),
            'processing_time': frontend_analysis.get('processing_time', 0.0),
            'recommendations': [],  # Frontend doesn't have top-level recommendations
            'timestamp': datetime.now().isoformat(),
            'enhanced_insights': frontend_analysis.get('enhanced_insights')
        }
        
        return backend_analysis

    async def _cleanup_temp_files(self):
        """Clean up temporary files created during email processing"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def _create_temp_file(self, content: bytes, suffix: str = ".pdf") -> str:
        """Create a temporary file and track it for cleanup"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            self.temp_files.append(temp_file_path)
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Failed to create temporary file: {e}")
            raise
    
    async def send_test_email(
        self, 
        user_email: str, 
        user_id: str,
        subject: str = "LegalSaathi Test Email"
    ) -> EmailNotificationResponse:
        """Send a test email to verify email functionality"""
        
        if not self.gmail_service.is_available():
            return EmailNotificationResponse(
                success=False,
                delivery_status=EmailDeliveryStatus.FAILED.value,
                error_message="Email service not available"
            )
        
        # Check rate limits
        rate_limit_info = self.gmail_service.check_rate_limit(user_id)
        if rate_limit_info.is_rate_limited:
            return EmailNotificationResponse(
                success=False,
                delivery_status=EmailDeliveryStatus.FAILED.value,
                error_message="Rate limit exceeded"
            )
        
        try:
            # Use SMTP service directly for test emails
            if self.gmail_service.smtp_service and self.gmail_service.smtp_service.is_available():
                logger.info("Using SMTP service for test email")
                
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #0ea5e9;">🧪 LegalSaathi Email Test</h2>
                        <p>This is a test email from LegalSaathi to verify email functionality.</p>
                        <p>If you received this email, the SMTP email service is working correctly!</p>
                        
                        <div style="background-color: #f0fdf4; border: 1px solid #10b981; border-radius: 8px; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #065f46;"><strong>✅ Email Configuration Status:</strong></p>
                            <ul style="margin: 10px 0; color: #065f46;">
                                <li>SMTP Server: Gmail (smtp.gmail.com:587)</li>
                                <li>Authentication: App Password</li>
                                <li>Sender: {self.gmail_service.smtp_service.sender_email}</li>
                            </ul>
                        </div>
                        
                        <p>You can now send analysis reports with PDF attachments!</p>
                        <br>
                        <p>Best regards,<br><strong>LegalSaathi Team</strong></p>
                    </div>
                </body>
                </html>
                """
                
                text_content = f"""
                LegalSaathi Email Test
                
                This is a test email from LegalSaathi to verify email functionality.
                If you received this email, the SMTP email service is working correctly!
                
                Email Configuration Status:
                - SMTP Server: Gmail (smtp.gmail.com:587)
                - Authentication: App Password
                - Sender: {self.gmail_service.smtp_service.sender_email}
                
                You can now send analysis reports with PDF attachments!
                
                Best regards,
                LegalSaathi Team
                """
                
                response = await self.gmail_service.smtp_service._send_smtp_email(
                    to_email=user_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    pdf_content=None  # No PDF for test email
                )
            else:
                # Fallback to Gmail API
                logger.info("Using Gmail API for test email")
                from models.email_models import EmailSendRequest, EmailPriority
                
                html_content = """
                <html>
                <body>
                    <h2>LegalSaathi Email Test</h2>
                    <p>This is a test email from LegalSaathi to verify email functionality.</p>
                    <p>If you received this email, the email service is working correctly.</p>
                    <br>
                    <p>Best regards,<br>LegalSaathi Team</p>
                </body>
                </html>
                """
                
                text_content = """
                LegalSaathi Email Test
                
                This is a test email from LegalSaathi to verify email functionality.
                If you received this email, the email service is working correctly.
                
                Best regards,
                LegalSaathi Team
                """
                
                email_request = EmailSendRequest(
                    to_email=user_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    priority=EmailPriority.NORMAL
                )
                
                response = await self.gmail_service._send_email(email_request)
            
            if response.success:
                self.gmail_service.increment_rate_limit(user_id)
                return EmailNotificationResponse(
                    success=True,
                    message_id=response.message_id,
                    delivery_status=EmailDeliveryStatus.SENT.value
                )
            else:
                return EmailNotificationResponse(
                    success=False,
                    delivery_status=EmailDeliveryStatus.FAILED.value,
                    error_message=response.error
                )
                
        except Exception as e:
            logger.error(f"Test email failed: {e}")
            return EmailNotificationResponse(
                success=False,
                delivery_status=EmailDeliveryStatus.FAILED.value,
                error_message=f"Test email failed: {str(e)}"
            )