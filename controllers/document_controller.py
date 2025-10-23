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
            
            # Validate file type
            allowed_types = {
                'pdf': [
                    'application/pdf',
                    'application/x-pdf',
                    'application/acrobat',
                    'applications/vnd.pdf',
                    'text/pdf',
                    'text/x-pdf'
                ],
                'doc': [
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ],
                'txt': ['text/plain']
            }
            
            content_type = file.content_type or 'application/octet-stream'
            logger.info(f"File content type: {content_type}")
            
            # Check if the content type matches any of our allowed types
            content_type_allowed = any(
                content_type in types
                for types in allowed_types.values()
            )
            
            if not content_type_allowed:
                logger.warning(f"Unsupported file type received: {content_type}")
                # Check file extension as fallback
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                if file_ext in allowed_types:
                    # If extension is valid, assume it's the correct type
                    logger.info(f"Using file extension {file_ext} to determine type")
                    content_type = allowed_types[file_ext][0]  # Use the primary MIME type
                else:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Unsupported file type: {content_type}. Supported types: PDF, DOC, DOCX, TXT"
                    )
            
            try:
                # Read file content with size limit (10MB)
                file_content = await file.read(10 * 1024 * 1024)  # 10MB limit
                if len(file_content) == 10 * 1024 * 1024:
                    # File might be larger than 10MB
                    raise HTTPException(
                        status_code=422,
                        detail="File size exceeds maximum limit of 10MB"
                    )
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                raise HTTPException(
                    status_code=422,
                    detail="Error reading file. Please ensure the file is not corrupted."
                )
            
            # Process file using file service
            processing_result = self.file_service.process_file_content(
                file_content, 
                file.filename, 
                content_type
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
    
    async def get_paginated_clauses(
        self, 
        analysis_id: str, 
        page: int = 1, 
        page_size: int = 10,
        risk_filter: Optional[str] = None,
        sort_by: str = "risk_score"
    ) -> dict:
        """Get paginated clause results with filtering and sorting"""
        try:
            # Validate parameters
            if page < 1:
                raise HTTPException(status_code=400, detail="Page must be >= 1")
            if page_size < 1 or page_size > 50:
                raise HTTPException(status_code=400, detail="Page size must be between 1 and 50")
            
            valid_risk_filters = ['red', 'yellow', 'green']
            if risk_filter and risk_filter.lower() not in valid_risk_filters:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid risk filter. Must be one of: {valid_risk_filters}"
                )
            
            valid_sort_options = ['risk_score', 'risk_level', 'clause_id', 'confidence']
            if sort_by not in valid_sort_options:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sort option. Must be one of: {valid_sort_options}"
                )
            
            result = await self.document_service.get_paginated_clauses(
                analysis_id=analysis_id,
                page=page,
                page_size=page_size,
                risk_filter=risk_filter,
                sort_by=sort_by
            )
            
            logger.info(f"Paginated clauses retrieved: {analysis_id}, page {page}")
            return result
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get paginated clauses: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get clauses: {str(e)}"
            )
    
    async def search_clauses(
        self,
        analysis_id: str,
        search_query: str,
        search_fields: Optional[str] = None
    ) -> dict:
        """Search within analyzed clauses"""
        try:
            # Validate search query
            if not search_query or len(search_query.strip()) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Search query must be at least 2 characters long"
                )
            
            if len(search_query) > 200:
                raise HTTPException(
                    status_code=400,
                    detail="Search query too long (max 200 characters)"
                )
            
            # Parse search fields
            fields_list = None
            if search_fields:
                valid_fields = ['clause_text', 'plain_explanation', 'legal_implications', 'recommendations', 'reasons']
                fields_list = [f.strip() for f in search_fields.split(',')]
                invalid_fields = [f for f in fields_list if f not in valid_fields]
                if invalid_fields:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid search fields: {invalid_fields}. Valid fields: {valid_fields}"
                    )
            
            result = await self.document_service.search_clauses(
                analysis_id=analysis_id,
                search_query=search_query,
                search_fields=fields_list
            )
            
            logger.info(f"Clause search completed: {analysis_id}, query '{search_query}', {result['total_matches']} matches")
            return result
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Clause search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )
    
    async def get_clause_details(self, analysis_id: str, clause_id: str) -> dict:
        """Get detailed information for a specific clause"""
        try:
            if analysis_id not in self.document_service.analysis_storage:
                raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
            
            stored_analysis = self.document_service.analysis_storage[analysis_id]
            clause_assessments = stored_analysis['clause_assessments']
            
            # Find the specific clause
            target_clause = None
            for clause in clause_assessments:
                if clause.clause_id == clause_id:
                    target_clause = clause
                    break
            
            if not target_clause:
                raise HTTPException(status_code=404, detail=f"Clause {clause_id} not found")
            
            # Return detailed clause information
            result = {
                'clause_id': target_clause.clause_id,
                'clause_text': target_clause.clause_text,
                'risk_assessment': {
                    'level': target_clause.risk_assessment.level.value,
                    'score': target_clause.risk_assessment.score,
                    'severity': target_clause.risk_assessment.severity,
                    'confidence_percentage': target_clause.risk_assessment.confidence_percentage,
                    'reasons': target_clause.risk_assessment.reasons,
                    'risk_categories': target_clause.risk_assessment.risk_categories,
                    'low_confidence_warning': target_clause.risk_assessment.low_confidence_warning
                },
                'plain_explanation': target_clause.plain_explanation,
                'legal_implications': target_clause.legal_implications,
                'recommendations': target_clause.recommendations,
                'translation_available': target_clause.translation_available,
                'analysis_id': analysis_id
            }
            
            logger.info(f"Clause details retrieved: {analysis_id}, clause {clause_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get clause details: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get clause details: {str(e)}"
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