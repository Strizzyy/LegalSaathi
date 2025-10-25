"""
SMTP Email service as a fallback for Gmail API
This is simpler to set up and works with Gmail App Passwords
"""

import os
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional

from models.email_models import (
    EmailSendRequest, EmailSendResponse, EmailDeliveryStatus
)
from models.document_models import DocumentAnalysisResponse
from middleware.email_rate_limiter import email_rate_limiter

logger = logging.getLogger(__name__)


class SMTPEmailService:
    """SMTP Email service for sending emails via Gmail SMTP"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('GMAIL_SENDER_EMAIL', 'noreply@legalsaathi.com')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD', '')
        self.sender_name = os.getenv('GMAIL_SENDER_NAME', 'LegalSaathi Document Advisor')
        
        # Check if credentials are available
        self.is_configured = bool(self.sender_email and self.sender_password)
        
        if not self.is_configured:
            logger.warning("SMTP email service not configured. Set GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD in .env")
    
    def is_available(self) -> bool:
        """Check if SMTP service is available"""
        return self.is_configured
    
    def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """Check rate limiting for user"""
        return email_rate_limiter.check_rate_limit(user_id)
    
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
        """Send analysis report via SMTP email with PDF attachment"""
        
        if not self.is_available():
            return EmailSendResponse(
                success=False,
                error="SMTP email service not configured. Please check GMAIL_APP_PASSWORD in .env",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        # Check rate limits
        rate_limit_info = self.check_rate_limit(user_id)
        if rate_limit_info.get('is_rate_limited', False):
            retry_after = int((rate_limit_info['next_reset_time'] - datetime.now()).total_seconds())
            return EmailSendResponse(
                success=False,
                error=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        
        try:
            # Generate email content
            subject = self._generate_email_subject(analysis_result)
            html_content = self._generate_html_email_template(analysis_result, custom_message)
            text_content = self._generate_text_email_template(analysis_result, custom_message)
            
            # Send email
            response = await self._send_smtp_email(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                pdf_content=pdf_content
            )
            
            if response.success:
                # Increment rate limit counters
                self.increment_rate_limit(user_id)
                logger.info(f"Analysis report sent successfully to {user_email}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send analysis report: {e}")
            return EmailSendResponse(
                success=False,
                error=f"Failed to send email: {str(e)}",
                delivery_status=EmailDeliveryStatus.FAILED
            )
    
    async def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        pdf_content: Optional[bytes] = None
    ) -> EmailSendResponse:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add PDF attachment if provided
            if pdf_content and len(pdf_content) > 0:
                pdf_attachment = MIMEBase('application', 'pdf')
                pdf_attachment.set_payload(pdf_content)
                encoders.encode_base64(pdf_attachment)
                pdf_attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="legal_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                )
                pdf_attachment.add_header('Content-Type', 'application/pdf')
                msg.attach(pdf_attachment)
                logger.info(f"PDF attachment added, size: {len(pdf_content)} bytes")
            else:
                logger.warning("No PDF content to attach or PDF content is empty")
            
            # Send email
            logger.info(f"Attempting SMTP connection to {self.smtp_server}:{self.smtp_port}")
            logger.info(f"Using sender email: {self.sender_email}")
            logger.info(f"App password length: {len(self.sender_password)} characters")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable SMTP debugging
                logger.info("Starting TLS...")
                server.starttls()
                logger.info("Attempting login...")
                server.login(self.sender_email, self.sender_password)
                logger.info("Login successful, sending message...")
                server.send_message(msg)
            
            logger.info(f"SMTP email sent successfully to {to_email}")
            
            return EmailSendResponse(
                success=True,
                message_id=f"smtp_{datetime.now().timestamp()}",
                delivery_status=EmailDeliveryStatus.SENT
            )
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return EmailSendResponse(
                success=False,
                error="Email authentication failed. Please check GMAIL_APP_PASSWORD.",
                delivery_status=EmailDeliveryStatus.FAILED
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return EmailSendResponse(
                success=False,
                error=f"SMTP error: {str(e)}",
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