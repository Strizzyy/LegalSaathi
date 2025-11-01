"""
Consolidated Email Services
Combines Gmail API and SMTP email functionality
"""

import os
import logging
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class EmailProvider(Enum):
    GMAIL_API = "gmail_api"
    SMTP = "smtp"

class DeliveryStatus(Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"

class EmailServices:
    """Consolidated email services with Gmail API and SMTP support"""
    
    def __init__(self):
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        self.rate_limit_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
        
        # Initialize SMTP configuration
        self.smtp_config = {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'use_tls': True
        }
        
        # Initialize Gmail API (if available)
        self.gmail_service = None
        try:
            if not self.is_cloud_run:  # Gmail API not needed for Cloud Run
                self._init_gmail_api()
        except Exception as e:
            logger.warning(f"Gmail API initialization failed: {e}")
        
        # Rate limiting configuration
        self.rate_limits = {
            'per_user_per_hour': 10,
            'per_user_per_day': 50,
            'global_per_hour': 1000
        }
        
        logger.info("✅ Email services initialized")
    
    def _init_gmail_api(self):
        """Initialize Gmail API service"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            # This would require OAuth2 setup - simplified for Cloud Run
            logger.info("Gmail API would be initialized here with proper OAuth2 setup")
            
        except ImportError:
            logger.warning("Gmail API libraries not available")
    
    async def send_email(self, 
                        to_email: str, 
                        subject: str, 
                        html_content: str = None,
                        text_content: str = None,
                        pdf_content: bytes = None,
                        user_id: str = 'anonymous') -> Dict[str, Any]:
        """Send email using available provider"""
        
        # Check rate limits
        if not self._check_rate_limit(user_id):
            return {
                'success': False,
                'error': 'Rate limit exceeded',
                'delivery_status': DeliveryStatus.FAILED.value
            }
        
        # Try SMTP first (more reliable for Cloud Run)
        if self._is_smtp_available():
            result = await self._send_smtp_email(to_email, subject, html_content, text_content, pdf_content)
            if result['success']:
                self._update_rate_limit(user_id)
                return result
        
        # Fallback to Gmail API (if available)
        if self.gmail_service:
            result = await self._send_gmail_api_email(to_email, subject, html_content, text_content, pdf_content)
            if result['success']:
                self._update_rate_limit(user_id)
                return result
        
        return {
            'success': False,
            'error': 'No email service available',
            'delivery_status': DeliveryStatus.FAILED.value
        }
    
    async def _send_smtp_email(self, 
                              to_email: str, 
                              subject: str, 
                              html_content: str = None,
                              text_content: str = None,
                              pdf_content: bytes = None) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            if not self._is_smtp_available():
                return {'success': False, 'error': 'SMTP not configured'}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['username']
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add PDF attachment
            if pdf_content:
                pdf_part = MIMEApplication(pdf_content, _subtype='pdf')
                pdf_part.add_header('Content-Disposition', 'attachment', filename='legal_analysis.pdf')
                msg.attach(pdf_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            return {
                'success': True,
                'message_id': f"smtp_{datetime.now().timestamp()}",
                'delivery_status': DeliveryStatus.SENT.value,
                'provider': EmailProvider.SMTP.value,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SMTP email failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': DeliveryStatus.FAILED.value,
                'provider': EmailProvider.SMTP.value
            }
    
    async def _send_gmail_api_email(self, 
                                   to_email: str, 
                                   subject: str, 
                                   html_content: str = None,
                                   text_content: str = None,
                                   pdf_content: bytes = None) -> Dict[str, Any]:
        """Send email using Gmail API"""
        try:
            # Gmail API implementation would go here
            # For now, return not implemented
            return {
                'success': False,
                'error': 'Gmail API not implemented',
                'delivery_status': DeliveryStatus.FAILED.value,
                'provider': EmailProvider.GMAIL_API.value
            }
            
        except Exception as e:
            logger.error(f"Gmail API email failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': DeliveryStatus.FAILED.value,
                'provider': EmailProvider.GMAIL_API.value
            }
    
    def _is_smtp_available(self) -> bool:
        """Check if SMTP is properly configured"""
        return (self.smtp_config['username'] and 
                self.smtp_config['password'] and 
                self.smtp_config['server'])
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits"""
        now = datetime.now()
        
        # Get user's rate limit data
        user_key = f"user_{user_id}"
        if user_key not in self.rate_limit_cache:
            self.rate_limit_cache[user_key] = {
                'hourly_count': 0,
                'daily_count': 0,
                'last_hour_reset': now,
                'last_day_reset': now
            }
        
        user_data = self.rate_limit_cache[user_key]
        
        # Reset counters if needed
        if (now - user_data['last_hour_reset']).total_seconds() >= 3600:
            user_data['hourly_count'] = 0
            user_data['last_hour_reset'] = now
        
        if (now - user_data['last_day_reset']).total_seconds() >= 86400:
            user_data['daily_count'] = 0
            user_data['last_day_reset'] = now
        
        # Check limits
        if user_data['hourly_count'] >= self.rate_limits['per_user_per_hour']:
            return False
        
        if user_data['daily_count'] >= self.rate_limits['per_user_per_day']:
            return False
        
        return True
    
    def _update_rate_limit(self, user_id: str):
        """Update rate limit counters"""
        user_key = f"user_{user_id}"
        if user_key in self.rate_limit_cache:
            self.rate_limit_cache[user_key]['hourly_count'] += 1
            self.rate_limit_cache[user_key]['daily_count'] += 1
    
    async def send_analysis_report(self, 
                                  to_email: str, 
                                  analysis_data: Dict[str, Any],
                                  user_id: str = 'anonymous') -> Dict[str, Any]:
        """Send legal analysis report via email"""
        try:
            # Generate email content
            subject = f"Legal Document Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            html_content = self._generate_analysis_html(analysis_data)
            text_content = self._generate_analysis_text(analysis_data)
            
            # Generate PDF if needed
            pdf_content = None
            if analysis_data.get('include_pdf', False):
                pdf_content = await self._generate_analysis_pdf(analysis_data)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                pdf_content=pdf_content,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Analysis report email failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': DeliveryStatus.FAILED.value
            }
    
    def _generate_analysis_html(self, analysis_data: Dict[str, Any]) -> str:
        """Generate HTML content for analysis report"""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0ea5e9;">📋 Legal Document Analysis Report</h2>
                
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1e40af;">Document Summary</h3>
                    <p><strong>Document Type:</strong> {analysis_data.get('document_type', 'Unknown')}</p>
                    <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Total Clauses:</strong> {len(analysis_data.get('clauses', []))}</p>
                </div>
                
                <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #dc2626;">⚠️ Key Findings</h3>
                    <p>{analysis_data.get('summary', 'No summary available')}</p>
                </div>
                
                <p style="margin-top: 30px; font-size: 12px; color: #6b7280;">
                    This analysis is for informational purposes only and does not constitute legal advice. 
                    Please consult with a qualified legal professional for specific guidance.
                </p>
                
                <p style="font-size: 12px; color: #6b7280;">
                    Best regards,<br>
                    <strong>LegalSaathi Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_analysis_text(self, analysis_data: Dict[str, Any]) -> str:
        """Generate plain text content for analysis report"""
        text = f"""
Legal Document Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Document Summary:
- Document Type: {analysis_data.get('document_type', 'Unknown')}
- Total Clauses: {len(analysis_data.get('clauses', []))}

Key Findings:
{analysis_data.get('summary', 'No summary available')}

---
This analysis is for informational purposes only and does not constitute legal advice.
Please consult with a qualified legal professional for specific guidance.

Best regards,
LegalSaathi Team
        """
        return text.strip()
    
    async def _generate_analysis_pdf(self, analysis_data: Dict[str, Any]) -> bytes:
        """Generate PDF content for analysis report"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import io
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Add content to PDF
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, height - 100, "Legal Document Analysis Report")
            
            p.setFont("Helvetica", 12)
            p.drawString(100, height - 140, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            p.drawString(100, height - 160, f"Document Type: {analysis_data.get('document_type', 'Unknown')}")
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, height - 200, "Summary:")
            
            p.setFont("Helvetica", 10)
            # Simple text wrapping for summary
            summary = analysis_data.get('summary', 'No summary available')
            y_position = height - 220
            for line in summary.split('\n'):
                if len(line) > 80:
                    # Simple word wrap
                    words = line.split(' ')
                    current_line = ''
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + ' '
                        else:
                            p.drawString(100, y_position, current_line.strip())
                            y_position -= 15
                            current_line = word + ' '
                    if current_line:
                        p.drawString(100, y_position, current_line.strip())
                        y_position -= 15
                else:
                    p.drawString(100, y_position, line)
                    y_position -= 15
            
            p.showPage()
            p.save()
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
    
    async def test_email_service(self) -> Dict[str, Any]:
        """Test email service availability"""
        status = {
            'smtp_available': self._is_smtp_available(),
            'gmail_api_available': self.gmail_service is not None,
            'rate_limits': self.rate_limits,
            'is_cloud_run': self.is_cloud_run
        }
        
        return {
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_rate_limit_info(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit information for user"""
        user_key = f"user_{user_id}"
        user_data = self.rate_limit_cache.get(user_key, {
            'hourly_count': 0,
            'daily_count': 0
        })
        
        return {
            'user_id': user_id,
            'hourly_usage': user_data.get('hourly_count', 0),
            'hourly_limit': self.rate_limits['per_user_per_hour'],
            'daily_usage': user_data.get('daily_count', 0),
            'daily_limit': self.rate_limits['per_user_per_day'],
            'can_send': self._check_rate_limit(user_id)
        }


# Global instance
_email_services = None

def get_email_services() -> EmailServices:
    """Get global email services instance"""
    global _email_services
    if _email_services is None:
        _email_services = EmailServices()
    return _email_services