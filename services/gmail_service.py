"""
Gmail service for sending email notifications with PDF attachments
"""

import os
import logging
import base64
import json
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from models.email_models import (
    EmailSendRequest, EmailSendResponse, EmailAttachment,
    EmailDeliveryStatus, EmailRateLimitInfo, EmailPriority
)
from models.document_models import DocumentAnalysisResponse
from middleware.email_rate_limiter import email_rate_limiter

logger = logging.getLogger(__name__)

# Try to import SMTP fallback
try:
    from services.smtp_email_service import SMTPEmailService
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False
    logger.warning("SMTP email service not available")


class GmailService:
    """Gmail API service for sending analysis reports via email"""
    
    def __init__(self):
        self.gmail_client = None
        self.credentials = None
        self.rate_limits = {}  # User-based rate limiting
        self.daily_limits = {}  # Daily usage tracking
        self._initialize_gmail_client()
        
        # Initialize SMTP fallback
        self.smtp_service = None
        if SMTP_AVAILABLE:
            try:
                self.smtp_service = SMTPEmailService()
                if self.smtp_service.is_available():
                    logger.info("SMTP email service initialized as fallback")
            except Exception as e:
                logger.warning(f"SMTP email service initialization failed: {e}")
                self.smtp_service = None
    
    def _initialize_gmail_client(self):
        """Initialize Gmail API client with OAuth2 authentication"""
        try:
            # Check for OAuth2 credentials (JSON string first, then file path)
            oauth_credentials = os.getenv('GMAIL_OAUTH_CREDENTIALS')
            if oauth_credentials and oauth_credentials.strip():
                try:
                    credentials_dict = json.loads(oauth_credentials)
                    self.credentials = Credentials.from_authorized_user_info(credentials_dict)
                    
                    # Refresh credentials if needed
                    if self.credentials.expired and self.credentials.refresh_token:
                        self.credentials.refresh(Request())
                    
                    # Build Gmail service
                    self.gmail_client = build('gmail', 'v1', credentials=self.credentials)
                    logger.info("Gmail service initialized successfully with OAuth2 credentials from environment JSON")
                    return
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid Gmail OAuth credentials JSON: {e}")
            
            # Fallback to file path
            oauth_credentials_path = os.getenv('GMAIL_OAUTH_CREDENTIALS_PATH')
            if oauth_credentials_path and os.path.exists(oauth_credentials_path):
                try:
                    with open(oauth_credentials_path, 'r') as f:
                        credentials_dict = json.load(f)
                    self.credentials = Credentials.from_authorized_user_info(credentials_dict)
                    
                    # Refresh credentials if needed
                    if self.credentials.expired and self.credentials.refresh_token:
                        self.credentials.refresh(Request())
                    
                    # Build Gmail service
                    self.gmail_client = build('gmail', 'v1', credentials=self.credentials)
                    logger.info(f"Gmail service initialized successfully with OAuth2 credentials from {oauth_credentials_path}")
                    return
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid Gmail OAuth credentials JSON: {e}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gmail with OAuth2: {e}")
            
            # Check for service account credentials (fallback, but limited functionality)
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if credentials_json:
                logger.warning("Gmail API with service account has limited functionality. OAuth2 recommended.")
                # Service accounts can't send emails on behalf of users for Gmail API
                # This is kept for potential future use with other Google services
            
            # No valid credentials found
            logger.warning("Gmail OAuth2 credentials not found. Email functionality will be limited.")
            logger.info("To enable email functionality, run: python setup_gmail.py")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gmail client: {e}")
            self.gmail_client = None
    
    def is_available(self) -> bool:
        """Check if Gmail service is available (Gmail API or SMTP fallback)"""
        return (self.gmail_client is not None) or (self.smtp_service and self.smtp_service.is_available())
    
    def check_rate_limit(self, user_id: str) -> EmailRateLimitInfo:
        """Check rate limiting for user"""
        rate_limit_data = email_rate_limiter.check_rate_limit(user_id)
        
        return EmailRateLimitInfo(
            user_id=rate_limit_data['user_id'],
            emails_sent_today=rate_limit_data['emails_sent_today'],
            emails_sent_this_hour=rate_limit_data['emails_sent_this_hour'],
            daily_limit=rate_limit_data['daily_limit'],
            hourly_limit=rate_limit_data['hourly_limit'],
            next_reset_time=rate_limit_data['next_reset_time'],
            is_rate_limited=rate_limit_data['is_rate_limited']
        )
    
    def increment_rate_limit(self, user_id: str):
        """Increment rate limit counters for user"""
        email_rate_limiter.increment_counter(user_id)
    
    async def send_analysis_report(
        self, 
        user_email: str, 
        analysis_result: DocumentAnalysisResponse,
        pdf_content: bytes,
        user_id: str,
        custom_message: Optional[str] = None
    ) -> EmailSendResponse:
        """Send analysis report via email with PDF attachment"""
        
        if not self.is_available():
            return EmailSendResponse(
                success=False,
                error="Gmail service not available. Please check configuration.",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        # Check rate limits
        rate_limit_info = self.check_rate_limit(user_id)
        if rate_limit_info.is_rate_limited:
            retry_after = int((rate_limit_info.next_reset_time - datetime.now()).total_seconds())
            return EmailSendResponse(
                success=False,
                error=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        try:
            # Try Gmail API first, then SMTP fallback
            if self.gmail_client is not None:
                # Use Gmail API
                subject = self._generate_email_subject(analysis_result)
                html_content = self._generate_html_email_template(analysis_result, custom_message)
                text_content = self._generate_text_email_template(analysis_result, custom_message)
                
                # Create attachment
                attachment = EmailAttachment(
                    filename=f"legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    content_type="application/pdf",
                    size=len(pdf_content),
                    data=pdf_content
                )
                
                # Send email
                email_request = EmailSendRequest(
                    to_email=user_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    attachments=[attachment],
                    priority=EmailPriority.NORMAL
                )
                
                response = await self._send_email(email_request)
                
                if response.success:
                    # Increment rate limit counters
                    self.increment_rate_limit(user_id)
                    logger.info(f"Analysis report sent successfully via Gmail API to {user_email}")
                
                return response
                
            elif self.smtp_service and self.smtp_service.is_available():
                # Use SMTP fallback
                logger.info("Using SMTP fallback for email sending")
                response = await self.smtp_service.send_analysis_report(
                    user_email=user_email,
                    analysis_result=analysis_result,
                    pdf_content=pdf_content,
                    user_id=user_id,
                    custom_message=custom_message
                )
                
                if response.success:
                    logger.info(f"Analysis report sent successfully via SMTP to {user_email}")
                
                return response
            
            else:
                return EmailSendResponse(
                    success=False,
                    error="No email service available. Please configure Gmail API or SMTP.",
                    delivery_status=EmailDeliveryStatus.FAILED
                )
            
        except Exception as e:
            logger.error(f"Failed to send analysis report: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Failed to send email: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    async def _send_email(self, email_request: EmailSendRequest) -> EmailSendResponse:
        """Send email using Gmail API or log in development mode"""
        
        # Development mode: log email instead of sending
        if not self.gmail_client:
            return await self._log_email_for_development(email_request)
        
        try:
            # Create MIME message
            message = MIMEMultipart('alternative')
            message['To'] = email_request.to_email
            message['Subject'] = email_request.subject
            
            # Configure sender email from environment
            sender_email = os.getenv('GMAIL_SENDER_EMAIL', 'noreply@legalsaathi.com')
            sender_name = os.getenv('GMAIL_SENDER_NAME', 'LegalSaathi Document Advisor')
            message['From'] = f"{sender_name} <{sender_email}>"
            
            if email_request.reply_to:
                message['Reply-To'] = email_request.reply_to
            
            # Add priority header
            if email_request.priority == EmailPriority.HIGH:
                message['X-Priority'] = '1'
                message['X-MSMail-Priority'] = 'High'
            elif email_request.priority == EmailPriority.LOW:
                message['X-Priority'] = '5'
                message['X-MSMail-Priority'] = 'Low'
            
            # Add text and HTML parts
            text_part = MIMEText(email_request.text_content, 'plain', 'utf-8')
            html_part = MIMEText(email_request.html_content, 'html', 'utf-8')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add attachments
            for attachment in email_request.attachments:
                if attachment.content_type == "application/pdf":
                    part = MIMEBase('application', 'pdf')
                else:
                    part = MIMEBase('application', 'octet-stream')
                
                part.set_payload(attachment.data)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment.filename}"'
                )
                if attachment.content_type:
                    part.add_header('Content-Type', attachment.content_type)
                message.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            gmail_message = {'raw': raw_message}
            result = self.gmail_client.users().messages().send(
                userId='me', 
                body=gmail_message
            ).execute()
            
            message_id = result.get('id')
            logger.info(f"Email sent successfully. Message ID: {message_id}")
            
            return EmailSendResponse(
                success=True,
                message_id=message_id,
                delivery_status=EmailDeliveryStatus.SENT
            )
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Email send error: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    def _generate_email_subject(self, analysis: DocumentAnalysisResponse) -> str:
        """Generate email subject line"""
        risk_level = analysis.overall_risk.level
        risk_emoji = "🔴" if risk_level == "RED" else "🟡" if risk_level == "YELLOW" else "🟢"
        
        return f"{risk_emoji} Legal Document Analysis Report - {risk_level} Risk Level"
    
    def _generate_html_email_template(
        self, 
        analysis: DocumentAnalysisResponse, 
        custom_message: Optional[str] = None
    ) -> str:
        """Generate professional HTML email template"""
        
        risk_color = "#ef4444" if analysis.overall_risk.level == "RED" else "#f59e0b" if analysis.overall_risk.level == "YELLOW" else "#10b981"
        risk_bg_color = "#fef2f2" if analysis.overall_risk.level == "RED" else "#fffbeb" if analysis.overall_risk.level == "YELLOW" else "#f0fdf4"
        
        high_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "RED"])
        moderate_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "YELLOW"])
        low_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "GREEN"])
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Legal Document Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
        .content {{ padding: 30px; }}
        .risk-summary {{ background-color: {risk_bg_color}; border-left: 4px solid {risk_color}; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .risk-level {{ color: {risk_color}; font-weight: 700; font-size: 18px; margin-bottom: 10px; }}
        .summary-text {{ font-size: 16px; line-height: 1.6; margin-bottom: 15px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 25px 0; }}
        .stat-card {{ text-align: center; padding: 15px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }}
        .stat-number {{ font-size: 24px; font-weight: 700; margin-bottom: 5px; }}
        .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
        .red {{ color: #ef4444; }}
        .yellow {{ color: #f59e0b; }}
        .green {{ color: #10b981; }}
        .attachment-info {{ background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin: 25px 0; }}
        .attachment-info h3 {{ margin: 0 0 10px 0; color: #1e293b; }}
        .footer {{ background-color: #1e293b; color: white; padding: 25px; text-align: center; }}
        .footer p {{ margin: 5px 0; }}
        .disclaimer {{ font-size: 12px; color: #94a3b8; margin-top: 15px; line-height: 1.4; }}
        .custom-message {{ background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .custom-message h3 {{ margin: 0 0 10px 0; color: #1d4ed8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Legal Document Analysis Report</h1>
            <p>AI-Powered Risk Assessment & Analysis</p>
        </div>
        
        <div class="content">
            <p>Hello,</p>
            <p>Your legal document analysis has been completed. Please find the detailed report attached as a PDF.</p>
            
            {f'''
            <div class="custom-message">
                <h3>📝 Personal Message</h3>
                <p>{custom_message}</p>
            </div>
            ''' if custom_message else ''}
            
            <div class="risk-summary">
                <div class="risk-level">Overall Risk Level: {analysis.overall_risk.level}</div>
                <div class="summary-text">{analysis.summary}</div>
                <p><strong>Confidence Level:</strong> {analysis.overall_risk.confidence_percentage}%</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number red">{high_risk_clauses}</div>
                    <div class="stat-label">High Risk Clauses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number yellow">{moderate_risk_clauses}</div>
                    <div class="stat-label">Moderate Risk</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number green">{low_risk_clauses}</div>
                    <div class="stat-label">Low Risk</div>
                </div>
            </div>
            
            <div class="attachment-info">
                <h3>📎 Attached Report</h3>
                <p>The complete analysis report is attached as a PDF document containing:</p>
                <ul>
                    <li>Detailed clause-by-clause analysis</li>
                    <li>Risk assessment and explanations</li>
                    <li>Legal implications and recommendations</li>
                    <li>Visual risk indicators and charts</li>
                </ul>
            </div>
            
            <p>If you have any questions about this analysis or need further clarification, please don't hesitate to contact our support team.</p>
            
            <p>Best regards,<br>
            <strong>LegalSaathi AI Analysis Team</strong></p>
        </div>
        
        <div class="footer">
            <p><strong>LegalSaathi Document Advisor</strong></p>
            <p>AI-Powered Legal Document Analysis Platform</p>
            <div class="disclaimer">
                This analysis is generated by AI and is for informational purposes only. 
                It does not constitute legal advice. Please consult with a qualified attorney 
                for legal matters requiring professional judgment.
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template.strip()
    
    def _generate_text_email_template(
        self, 
        analysis: DocumentAnalysisResponse, 
        custom_message: Optional[str] = None
    ) -> str:
        """Generate plain text email template"""
        
        high_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "RED"])
        moderate_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "YELLOW"])
        low_risk_clauses = len([r for r in analysis.clause_assessments if r.risk_assessment.level == "GREEN"])
        
        text_template = f"""
LEGAL DOCUMENT ANALYSIS REPORT
==============================

Hello,

Your legal document analysis has been completed. Please find the detailed report attached as a PDF.

{f'''
PERSONAL MESSAGE
================
{custom_message}

''' if custom_message else ''}

OVERALL RISK ASSESSMENT
=======================
Risk Level: {analysis.overall_risk.level}
Confidence: {analysis.overall_risk.confidence_percentage}%

Summary: {analysis.summary}

CLAUSE BREAKDOWN
================
High Risk Clauses: {high_risk_clauses}
Moderate Risk Clauses: {moderate_risk_clauses}
Low Risk Clauses: {low_risk_clauses}

ATTACHED REPORT
===============
The complete analysis report is attached as a PDF document containing:
- Detailed clause-by-clause analysis
- Risk assessment and explanations
- Legal implications and recommendations
- Visual risk indicators and charts

If you have any questions about this analysis or need further clarification, 
please don't hesitate to contact our support team.

Best regards,
LegalSaathi AI Analysis Team

---
LegalSaathi Document Advisor
AI-Powered Legal Document Analysis Platform

DISCLAIMER: This analysis is generated by AI and is for informational purposes only. 
It does not constitute legal advice. Please consult with a qualified attorney 
for legal matters requiring professional judgment.
        """
        
        return text_template.strip()
    
    async def _log_email_for_development(self, email_request: EmailSendRequest) -> EmailSendResponse:
        """Log email content for development mode when Gmail API is not configured"""
        try:
            logger.info("=== DEVELOPMENT MODE: EMAIL WOULD BE SENT ===")
            logger.info(f"To: {email_request.to_email}")
            logger.info(f"Subject: {email_request.subject}")
            logger.info(f"Priority: {email_request.priority}")
            logger.info(f"Attachments: {len(email_request.attachments)} files")
            
            if email_request.attachments:
                for i, attachment in enumerate(email_request.attachments):
                    logger.info(f"  Attachment {i+1}: {attachment.filename} ({attachment.size} bytes)")
            
            logger.info("--- Email Text Content ---")
            logger.info(email_request.text_content[:500] + "..." if len(email_request.text_content) > 500 else email_request.text_content)
            logger.info("=== END DEVELOPMENT EMAIL ===")
            
            # Return success response with fake message ID
            fake_message_id = f"dev_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email_request.to_email) % 10000}"
            
            return EmailSendResponse(
                success=True,
                message_id=fake_message_id,
                delivery_status=EmailDeliveryStatus.SENT
            )
            
        except Exception as e:
            logger.error(f"Development email logging failed: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Development mode error: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )