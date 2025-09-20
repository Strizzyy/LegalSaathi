"""
Export controller for FastAPI backend
"""

import logging
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class ExportController:
    """Controller for document export operations"""
    
    def __init__(self):
        pass
    
    async def export_to_pdf(self, data: Dict[str, Any]) -> StreamingResponse:
        """Export analysis results to PDF"""
        try:
            logger.info("Generating PDF export")
            
            # Generate PDF content
            pdf_content = await self._generate_pdf_content(data)
            
            # Create streaming response
            pdf_stream = io.BytesIO(pdf_content)
            
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                }
            )
            
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"PDF export failed: {str(e)}"
            )
    
    async def export_to_word(self, data: Dict[str, Any]) -> StreamingResponse:
        """Export analysis results to Word document"""
        try:
            logger.info("Generating Word export")
            
            # Generate Word content
            word_content = await self._generate_word_content(data)
            
            return StreamingResponse(
                io.BytesIO(word_content),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename=legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                }
            )
            
        except Exception as e:
            logger.error(f"Word export failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Word export failed: {str(e)}"
            )
    
    async def _generate_pdf_content(self, data: Dict[str, Any]) -> bytes:
        """Generate PDF content from analysis data"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Build content
            content = []
            
            # Title
            content.append(Paragraph("Legal Document Analysis Report", title_style))
            content.append(Spacer(1, 20))
            
            # Analysis summary
            analysis = data.get('analysis', {})
            if analysis:
                content.append(Paragraph("Analysis Summary", heading_style))
                
                overall_risk = analysis.get('overall_risk', {})
                if overall_risk:
                    risk_level = overall_risk.get('level', 'Unknown')
                    risk_score = overall_risk.get('score', 0)
                    confidence = overall_risk.get('confidence_percentage', 0)
                    
                    content.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level}", styles['Normal']))
                    content.append(Paragraph(f"<b>Risk Score:</b> {risk_score:.2f}", styles['Normal']))
                    content.append(Paragraph(f"<b>Confidence:</b> {confidence}%", styles['Normal']))
                    content.append(Spacer(1, 12))
                
                # Summary text
                summary = analysis.get('summary', '')
                if summary:
                    content.append(Paragraph("Summary", heading_style))
                    content.append(Paragraph(summary, styles['Normal']))
                    content.append(Spacer(1, 12))
                
                # Clause analysis
                clause_results = analysis.get('analysis_results', [])
                if clause_results:
                    content.append(Paragraph("Clause Analysis", heading_style))
                    
                    for i, clause in enumerate(clause_results[:10]):  # Limit to 10 clauses
                        content.append(Paragraph(f"<b>Clause {i+1}</b>", styles['Heading3']))
                        
                        risk_level = clause.get('risk_level', {}).get('level', 'Unknown')
                        content.append(Paragraph(f"Risk Level: {risk_level}", styles['Normal']))
                        
                        explanation = clause.get('plain_explanation', '')
                        if explanation:
                            content.append(Paragraph(f"Explanation: {explanation}", styles['Normal']))
                        
                        content.append(Spacer(1, 8))
            
            # Footer
            content.append(Spacer(1, 30))
            content.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            content.append(Paragraph("Legal Saathi Document Advisor", styles['Normal']))
            
            # Build PDF
            doc.build(content)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except ImportError:
            # Fallback if reportlab is not available
            logger.warning("ReportLab not available, generating simple PDF")
            return await self._generate_simple_pdf_content(data)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    async def _generate_simple_pdf_content(self, data: Dict[str, Any]) -> bytes:
        """Generate simple PDF content as fallback"""
        # Simple text-based PDF content
        content = f"""Legal Document Analysis Report
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Analysis Summary:
{json.dumps(data.get('analysis', {}), indent=2)}

Generated by Legal Saathi Document Advisor
"""
        
        # Convert to bytes (this is a simplified approach)
        return content.encode('utf-8')
    
    async def _generate_word_content(self, data: Dict[str, Any]) -> bytes:
        """Generate Word document content from analysis data"""
        try:
            from docx import Document
            from docx.shared import Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            
            # Create document
            doc = Document()
            
            # Title
            title = doc.add_heading('Legal Document Analysis Report', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Analysis summary
            analysis = data.get('analysis', {})
            if analysis:
                doc.add_heading('Analysis Summary', level=1)
                
                overall_risk = analysis.get('overall_risk', {})
                if overall_risk:
                    risk_level = overall_risk.get('level', 'Unknown')
                    risk_score = overall_risk.get('score', 0)
                    confidence = overall_risk.get('confidence_percentage', 0)
                    
                    p = doc.add_paragraph()
                    p.add_run('Overall Risk Level: ').bold = True
                    p.add_run(f'{risk_level}\n')
                    p.add_run('Risk Score: ').bold = True
                    p.add_run(f'{risk_score:.2f}\n')
                    p.add_run('Confidence: ').bold = True
                    p.add_run(f'{confidence}%')
                
                # Summary text
                summary = analysis.get('summary', '')
                if summary:
                    doc.add_heading('Summary', level=1)
                    doc.add_paragraph(summary)
                
                # Clause analysis
                clause_results = analysis.get('analysis_results', [])
                if clause_results:
                    doc.add_heading('Clause Analysis', level=1)
                    
                    for i, clause in enumerate(clause_results[:10]):  # Limit to 10 clauses
                        doc.add_heading(f'Clause {i+1}', level=2)
                        
                        risk_level = clause.get('risk_level', {}).get('level', 'Unknown')
                        p = doc.add_paragraph()
                        p.add_run('Risk Level: ').bold = True
                        p.add_run(risk_level)
                        
                        explanation = clause.get('plain_explanation', '')
                        if explanation:
                            p = doc.add_paragraph()
                            p.add_run('Explanation: ').bold = True
                            p.add_run(explanation)
            
            # Footer
            doc.add_page_break()
            footer_para = doc.add_paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_para = doc.add_paragraph("Legal Saathi Document Advisor")
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Save to buffer
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            word_bytes = buffer.getvalue()
            buffer.close()
            
            return word_bytes
            
        except ImportError:
            # Fallback if python-docx is not available
            logger.warning("python-docx not available, generating simple Word content")
            return await self._generate_simple_word_content(data)
        except Exception as e:
            logger.error(f"Word generation failed: {e}")
            raise
    
    async def _generate_simple_word_content(self, data: Dict[str, Any]) -> bytes:
        """Generate simple Word content as fallback"""
        # Simple text-based content
        content = f"""Legal Document Analysis Report
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Analysis Summary:
{json.dumps(data.get('analysis', {}), indent=2)}

Generated by Legal Saathi Document Advisor
"""
        
        # Convert to bytes (this is a simplified approach)
        return content.encode('utf-8')