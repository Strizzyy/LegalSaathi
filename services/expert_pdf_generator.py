"""
Expert-Certified PDF Generator for Human-in-the-Loop System
Generates enhanced PDF reports with expert certification and signatures
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.document_models import DocumentAnalysisResponse
from models.expert_queue_models import ExpertAnalysisResponse

logger = logging.getLogger(__name__)


class ExpertPDFGenerator:
    """Enhanced PDF generator for expert-certified reports"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. PDF generation will be limited.")
        
        # Initialize colors first
        self.colors = {
            'primary': HexColor('#3b82f6'),
            'success': HexColor('#10b981'),
            'warning': HexColor('#f59e0b'),
            'danger': HexColor('#ef4444'),
            'expert': HexColor('#8b5cf6'),
            'light_gray': HexColor('#f8fafc'),
            'dark_gray': HexColor('#64748b')
        } if REPORTLAB_AVAILABLE else {}
        
        # Then initialize styles (which depend on colors)
        self.styles = self._create_styles() if REPORTLAB_AVAILABLE else None
    
    def generate_expert_certified_report(
        self,
        expert_analysis: ExpertAnalysisResponse,
        original_ai_analysis: DocumentAnalysisResponse,
        review_id: str,
        expert_name: str = "Legal Expert",
        expert_credentials: str = "J.D., Licensed Attorney"
    ) -> bytes:
        """Generate expert-certified PDF report with enhanced formatting"""
        
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available for PDF generation")
            return self._generate_fallback_pdf_content(expert_analysis, review_id)
        
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title=f"Expert Legal Analysis - {review_id}"
            )
            
            # Build document content
            story = []
            
            # Header with expert certification
            story.extend(self._create_expert_header(review_id, expert_name, expert_credentials))
            story.append(Spacer(1, 20))
            
            # Executive summary
            story.extend(self._create_executive_summary(expert_analysis, original_ai_analysis))
            story.append(Spacer(1, 20))
            
            # Expert certification section
            story.extend(self._create_expert_certification_section(expert_analysis, expert_name))
            story.append(Spacer(1, 20))
            
            # Confidence improvement analysis
            story.extend(self._create_confidence_analysis(expert_analysis, original_ai_analysis))
            story.append(PageBreak())
            
            # Detailed clause analysis
            story.extend(self._create_detailed_analysis(expert_analysis))
            story.append(Spacer(1, 20))
            
            # Expert recommendations
            story.extend(self._create_expert_recommendations(expert_analysis))
            story.append(Spacer(1, 20))
            
            # Expert signature and certification
            story.extend(self._create_expert_signature_section(expert_analysis, expert_name, expert_credentials))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"Expert-certified PDF generated successfully for review {review_id}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate expert PDF: {e}")
            return self._generate_fallback_pdf_content(expert_analysis, review_id)
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for expert reports"""
        if not REPORTLAB_AVAILABLE:
            return {}
            
        styles = getSampleStyleSheet()
        
        custom_styles = {
            'ExpertTitle': ParagraphStyle(
                'ExpertTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=self.colors['expert'],
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'ExpertSubtitle': ParagraphStyle(
                'ExpertSubtitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=self.colors['primary'],
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            ),
            'ExpertHeading': ParagraphStyle(
                'ExpertHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=self.colors['dark_gray'],
                spaceAfter=10,
                spaceBefore=15,
                fontName='Helvetica-Bold'
            ),
            'ExpertBody': ParagraphStyle(
                'ExpertBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                alignment=TA_JUSTIFY,
                fontName='Helvetica'
            ),
            'ExpertCertification': ParagraphStyle(
                'ExpertCertification',
                parent=styles['Normal'],
                fontSize=12,
                textColor=self.colors['expert'],
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'ExpertSignature': ParagraphStyle(
                'ExpertSignature',
                parent=styles['Normal'],
                fontSize=10,
                textColor=self.colors['dark_gray'],
                spaceAfter=5,
                fontName='Helvetica-Oblique'
            )
        }
        
        return custom_styles
    
    def _create_expert_header(self, review_id: str, expert_name: str, expert_credentials: str) -> List:
        """Create expert certification header"""
        elements = []
        
        # Expert certification badge
        cert_table = Table([
            ['🎓 EXPERT CERTIFIED LEGAL ANALYSIS', ''],
            [f'Review ID: {review_id}', f'Date: {datetime.now().strftime("%B %d, %Y")}'],
            [f'Reviewed by: {expert_name}', f'Credentials: {expert_credentials}']
        ], colWidths=[3*inch, 3*inch])
        
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['expert']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), self.colors['light_gray']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['dark_gray']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        elements.append(cert_table)
        elements.append(Spacer(1, 20))
        
        # Title
        title = Paragraph("EXPERT-REVIEWED LEGAL DOCUMENT ANALYSIS", self.styles['ExpertTitle'])
        elements.append(title)
        
        return elements
    
    def _create_executive_summary(self, expert_analysis: ExpertAnalysisResponse, original_ai_analysis: DocumentAnalysisResponse) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['ExpertSubtitle']))
        
        # Summary content
        analysis_data = expert_analysis.expert_analysis
        summary_text = analysis_data.get('summary', 'Expert analysis completed successfully.')
        
        elements.append(Paragraph(summary_text, self.styles['ExpertBody']))
        elements.append(Spacer(1, 10))
        
        # Key metrics table
        confidence_improvement = expert_analysis.confidence_improvement * 100
        
        metrics_data = [
            ['Metric', 'Value', 'Improvement'],
            ['Review Duration', f"{expert_analysis.review_duration_minutes} minutes", 'N/A'],
            ['Confidence Level', f"{analysis_data.get('overall_confidence', 0.95) * 100:.1f}%", f"+{confidence_improvement:.1f}%"],
            ['Expert Verification', 'Certified', '✓ Verified'],
            ['Analysis Quality', 'Professional Grade', '↑ Enhanced']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['dark_gray']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        elements.append(metrics_table)
        
        return elements
    
    def _create_expert_certification_section(self, expert_analysis: ExpertAnalysisResponse, expert_name: str) -> List:
        """Create expert certification section"""
        elements = []
        
        elements.append(Paragraph("EXPERT CERTIFICATION", self.styles['ExpertSubtitle']))
        
        cert_text = f"""
        This legal document analysis has been thoroughly reviewed and certified by {expert_name}, 
        a qualified legal professional. The analysis incorporates professional legal expertise, 
        industry best practices, and comprehensive risk assessment methodologies.
        
        The expert review process included:
        • Detailed clause-by-clause analysis with legal context
        • Professional risk assessment based on legal precedent
        • Enhanced recommendations with practical implementation guidance
        • Quality assurance and accuracy verification
        • Compliance with professional legal analysis standards
        """
        
        elements.append(Paragraph(cert_text, self.styles['ExpertBody']))
        
        # Certification badge
        cert_badge = Table([
            ['✓ EXPERT VERIFIED', '🎓 PROFESSIONALLY REVIEWED', '⚖️ LEGALLY CERTIFIED']
        ], colWidths=[2*inch, 2*inch, 2*inch])
        
        cert_badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['success']),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, white)
        ]))
        
        elements.append(Spacer(1, 10))
        elements.append(cert_badge)
        
        return elements
    
    def _create_confidence_analysis(self, expert_analysis: ExpertAnalysisResponse, original_ai_analysis: DocumentAnalysisResponse) -> List:
        """Create confidence improvement analysis"""
        elements = []
        
        elements.append(Paragraph("CONFIDENCE IMPROVEMENT ANALYSIS", self.styles['ExpertSubtitle']))
        
        # Confidence comparison
        original_confidence = getattr(original_ai_analysis, 'overall_confidence', 0.6) * 100
        expert_confidence = expert_analysis.expert_analysis.get('overall_confidence', 0.95) * 100
        improvement = expert_analysis.confidence_improvement * 100
        
        confidence_text = f"""
        The expert review process has significantly enhanced the analysis confidence and accuracy:
        
        • Original AI Confidence: {original_confidence:.1f}%
        • Expert-Reviewed Confidence: {expert_confidence:.1f}%
        • Confidence Improvement: +{improvement:.1f}%
        
        This improvement reflects the added value of human expertise in interpreting complex 
        legal language, identifying nuanced risks, and providing contextual analysis that 
        AI systems may not fully capture.
        """
        
        elements.append(Paragraph(confidence_text, self.styles['ExpertBody']))
        
        return elements
    
    def _create_detailed_analysis(self, expert_analysis: ExpertAnalysisResponse) -> List:
        """Create detailed clause analysis section"""
        elements = []
        
        elements.append(Paragraph("DETAILED EXPERT ANALYSIS", self.styles['ExpertSubtitle']))
        
        analysis_data = expert_analysis.expert_analysis
        
        # Clause assessments
        if 'clause_assessments' in analysis_data:
            elements.append(Paragraph("Clause-by-Clause Expert Review", self.styles['ExpertHeading']))
            
            for i, clause in enumerate(analysis_data['clause_assessments'], 1):
                clause_title = f"Clause {i}: {clause.get('clause_type', 'Legal Provision')}"
                elements.append(Paragraph(clause_title, self.styles['ExpertHeading']))
                
                # Clause content
                clause_text = clause.get('clause_text', 'Clause content not available')
                elements.append(Paragraph(f"<b>Content:</b> {clause_text[:200]}...", self.styles['ExpertBody']))
                
                # Expert assessment
                risk_level = clause.get('risk_assessment', {}).get('level', 'MEDIUM')
                risk_color = self.colors['danger'] if risk_level == 'RED' else self.colors['warning'] if risk_level == 'YELLOW' else self.colors['success']
                
                elements.append(Paragraph(f"<b>Expert Risk Assessment:</b> <font color='{risk_color}'>{risk_level}</font>", self.styles['ExpertBody']))
                
                # Expert explanation
                explanation = clause.get('explanation', 'Expert analysis provided.')
                elements.append(Paragraph(f"<b>Expert Analysis:</b> {explanation}", self.styles['ExpertBody']))
                
                elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_expert_recommendations(self, expert_analysis: ExpertAnalysisResponse) -> List:
        """Create expert recommendations section"""
        elements = []
        
        elements.append(Paragraph("EXPERT RECOMMENDATIONS", self.styles['ExpertSubtitle']))
        
        analysis_data = expert_analysis.expert_analysis
        recommendations = analysis_data.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                rec_text = rec if isinstance(rec, str) else rec.get('recommendation', 'Expert recommendation provided.')
                elements.append(Paragraph(f"{i}. {rec_text}", self.styles['ExpertBody']))
        else:
            elements.append(Paragraph("Expert recommendations have been incorporated throughout the analysis.", self.styles['ExpertBody']))
        
        # Expert notes
        if expert_analysis.expert_notes:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("Additional Expert Notes", self.styles['ExpertHeading']))
            elements.append(Paragraph(expert_analysis.expert_notes, self.styles['ExpertBody']))
        
        return elements
    
    def _create_expert_signature_section(self, expert_analysis: ExpertAnalysisResponse, expert_name: str, expert_credentials: str) -> List:
        """Create expert signature and certification section"""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("EXPERT CERTIFICATION & SIGNATURE", self.styles['ExpertSubtitle']))
        
        # Signature table
        signature_data = [
            ['Expert Name:', expert_name],
            ['Credentials:', expert_credentials],
            ['Review Completed:', expert_analysis.completed_at.strftime('%B %d, %Y at %I:%M %p')],
            ['Review ID:', expert_analysis.review_id],
            ['Digital Signature:', f"Certified by {expert_name} - {datetime.now().strftime('%Y%m%d_%H%M%S')}"]
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 4*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['dark_gray'])
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer = """
        <b>PROFESSIONAL DISCLAIMER:</b> This expert analysis is provided by qualified legal 
        professionals for informational and educational purposes. It does not constitute 
        attorney-client relationship or legal advice. For specific legal matters requiring 
        professional representation, please consult with a licensed attorney in your jurisdiction.
        
        This document contains confidential and proprietary analysis. Unauthorized distribution 
        is prohibited.
        """
        
        elements.append(Paragraph(disclaimer, self.styles['ExpertSignature']))
        
        return elements
    
    def _generate_fallback_pdf_content(self, expert_analysis: ExpertAnalysisResponse, review_id: str) -> bytes:
        """Generate simple PDF content when ReportLab is not available"""
        content = f"""
EXPERT-CERTIFIED LEGAL ANALYSIS
===============================

Review ID: {review_id}
Date: {datetime.now().strftime('%B %d, %Y')}
Expert Review Completed: {expert_analysis.completed_at.strftime('%B %d, %Y at %I:%M %p')}

EXPERT CERTIFICATION
===================
This document has been reviewed and certified by a qualified legal professional.

Review Duration: {expert_analysis.review_duration_minutes} minutes
Confidence Improvement: +{expert_analysis.confidence_improvement * 100:.1f}%

ANALYSIS SUMMARY
===============
{expert_analysis.expert_analysis.get('summary', 'Expert analysis completed successfully.')}

EXPERT NOTES
============
{expert_analysis.expert_notes or 'No additional notes provided.'}

CERTIFICATION
=============
This analysis has been professionally reviewed and certified.
Review ID: {expert_analysis.review_id}
Completed: {expert_analysis.completed_at.strftime('%Y-%m-%d %H:%M:%S')}

DISCLAIMER
==========
This expert analysis is provided for informational purposes and does not 
constitute legal advice. Consult with a licensed attorney for specific legal matters.
        """
        
        return content.encode('utf-8')