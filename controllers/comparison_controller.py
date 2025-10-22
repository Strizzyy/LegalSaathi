"""
Document comparison controller for FastAPI backend
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException

from models.comparison_models import (
    DocumentComparisonRequest, DocumentComparisonResponse,
    ComparisonSummaryResponse
)
from services.comparison_service import ComparisonService

logger = logging.getLogger(__name__)


class ComparisonController:
    """Controller for document comparison operations"""
    
    def __init__(self):
        self.comparison_service = ComparisonService()
    
    async def compare_documents(self, request: DocumentComparisonRequest) -> DocumentComparisonResponse:
        """Handle document comparison requests"""
        try:
            logger.info(f"Starting document comparison: {request.document1_type} vs {request.document2_type}")
            
            # Validate documents
            if len(request.document1_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Document 1 text must be at least 100 characters long"
                )
            
            if len(request.document2_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Document 2 text must be at least 100 characters long"
                )
            
            # Perform comparison
            result = await self.comparison_service.compare_documents(request)
            
            logger.info(f"Document comparison completed: {result.comparison_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Comparison failed: {str(e)}"
            )
    
    async def get_comparison_summary(self, comparison_id: str) -> ComparisonSummaryResponse:
        """Get summary of a previous comparison"""
        try:
            # This would typically fetch from a database
            # For now, return a placeholder response
            return ComparisonSummaryResponse(
                comparison_id=comparison_id,
                document1_type="rental_agreement",
                document2_type="rental_agreement",
                overall_verdict="Document 2 is safer",
                key_insights=[
                    "Document 2 has fewer high-risk clauses",
                    "Better termination terms in Document 2",
                    "Similar payment structures"
                ],
                risk_score_difference=-0.15,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get comparison summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get comparison summary: {str(e)}"
            )
    
    async def export_comparison_report(
        self, 
        comparison_result: DocumentComparisonResponse,
        format: str = "pdf"
    ) -> bytes:
        """Export comparison report in specified format"""
        try:
            logger.info(f"Exporting comparison report: {comparison_result.comparison_id} in {format} format")
            
            # Validate format
            supported_formats = await self.comparison_service.get_export_formats()
            if format.lower() not in supported_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {format}. Supported formats: {supported_formats}"
                )
            
            # Export the report
            exported_data = await self.comparison_service.export_comparison_report(
                comparison_result, format
            )
            
            logger.info(f"Comparison report exported successfully: {len(exported_data)} bytes")
            return exported_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to export comparison report: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Export failed: {str(e)}"
            )
    
    async def get_export_formats(self) -> Dict[str, Any]:
        """Get available export formats"""
        try:
            formats = await self.comparison_service.get_export_formats()
            return {
                "supported_formats": formats,
                "default_format": "pdf",
                "format_descriptions": {
                    "pdf": "Portable Document Format - Best for viewing and printing",
                    "docx": "Microsoft Word Document - Best for editing and collaboration",
                    "word": "Microsoft Word Document (alias for docx)"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get export formats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get export formats: {str(e)}"
            )