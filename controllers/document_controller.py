"""
Document controller for FastAPI backend
"""

import logging
from fastapi import HTTPException, UploadFile, File, Form
from typing import Optional

from models.document_models import (
    DocumentAnalysisRequest, DocumentAnalysisResponse, 
    AnalysisStatusResponse, ErrorResponse
)
from services.document_service import DocumentService
from services.file_service import FileService

logger = logging.getLogger(__name__)


class DocumentController:
    """Controller for document analysis operations"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.file_service = FileService()
    
    async def analyze_document(self, request: DocumentAnalysisRequest) -> DocumentAnalysisResponse:
        """Handle document analysis requests with async processing"""
        try:
            logger.info(f"Starting document analysis for type: {request.document_type}")
            logger.info(f"Document text preview: {request.document_text[:200]}...")
            
            # Validate document text
            if not request.document_text or len(request.document_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Document text must be at least 100 characters long"
                )
            
            if len(request.document_text) > 50000:
                raise HTTPException(
                    status_code=400,
                    detail="Document text exceeds maximum length of 50,000 characters"
                )
            
            # Perform analysis
            result = await self.document_service.analyze_document(request)
            
            logger.info(f"Document analysis completed: {result.analysis_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )
    
    async def analyze_document_file(
        self,
        file: UploadFile = File(...),
        document_type: str = Form(...),
        user_expertise_level: str = Form("beginner")
    ) -> DocumentAnalysisResponse:
        """Handle file upload and analysis"""
        try:
            logger.info(f"Processing uploaded file: {file.filename}")
            
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            # Read file content
            file_content = await file.read()
            
            # Process file using file service
            processing_result = self.file_service.process_file_content(
                file_content, 
                file.filename, 
                file.content_type
            )
            
            if not processing_result.success:
                raise HTTPException(
                    status_code=400,
                    detail=processing_result.error_message
                )
            
            # Create analysis request
            request = DocumentAnalysisRequest(
                document_text=processing_result.text_content,
                document_type=document_type,
                user_expertise_level=user_expertise_level
            )
            
            # Perform analysis
            result = await self.document_service.analyze_document(request)
            
            logger.info(f"File analysis completed: {result.analysis_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"File analysis failed: {str(e)}"
            )
    
    async def start_async_analysis(self, request: DocumentAnalysisRequest) -> dict:
        """Start async document analysis and return job ID"""
        try:
            job_id = await self.document_service.start_async_analysis(request)
            
            return {
                "success": True,
                "job_id": job_id,
                "message": "Analysis started successfully",
                "status_endpoint": f"/api/analysis/status/{job_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to start async analysis: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start analysis: {str(e)}"
            )
    
    async def get_analysis_status(self, analysis_id: str) -> AnalysisStatusResponse:
        """Get status of ongoing analysis"""
        try:
            status = await self.document_service.get_analysis_status(analysis_id)
            return status
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get analysis status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get status: {str(e)}"
            )
    
    async def export_analysis(self, analysis_id: str, format: str = "pdf") -> dict:
        """Export analysis results to PDF or Word format"""
        try:
            # This would integrate with the existing export functionality
            # For now, return a placeholder response
            return {
                "success": True,
                "message": f"Export to {format} format initiated",
                "download_url": f"/api/analysis/{analysis_id}/download/{format}"
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Export failed: {str(e)}"
            )