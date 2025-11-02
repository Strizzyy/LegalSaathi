"""
Dual Vision Service for Enhanced Document Processing
Integrates Google Cloud Vision API for images and Document AI for PDFs with intelligent fallback
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from services.google_document_ai_service import document_ai_service
from services.google_cloud_vision_service import vision_service

logger = logging.getLogger(__name__)

class ProcessingMethod(Enum):
    """Document processing methods"""
    DOCUMENT_AI = "document_ai"
    VISION_API = "vision_api"
    FALLBACK = "fallback"

@dataclass
class ProcessingResult:
    """Result of document processing operation"""
    success: bool
    text: str
    method_used: ProcessingMethod
    confidence_scores: Dict[str, float]
    processing_time: float
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    fallback_used: bool = False

class DualVisionService:
    """
    Dual vision service that intelligently routes documents to optimal processing method
    - Uses Document AI for PDF files
    - Uses Vision API for image files (JPEG, PNG, WEBP)
    - Implements fallback mechanisms for both services
    """
    
    def __init__(self):
        self.document_ai = document_ai_service
        self.vision_api = vision_service
        
        # File type routing configuration
        self.pdf_mime_types = {
            'application/pdf',
            'application/x-pdf',
            'application/acrobat',
            'applications/vnd.pdf',
            'text/pdf',
            'text/x-pdf'
        }
        
        self.image_mime_types = {
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/webp',
            'image/bmp',
            'image/gif'
        }
        
        # Processing preferences
        self.prefer_document_ai_for_pdf = True
        self.prefer_vision_api_for_images = True
        self.enable_fallback = True
        
        logger.info("Dual Vision Service initialized")
    
    async def process_document(
        self, 
        file_content: bytes, 
        mime_type: str,
        user_id: str,
        filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process document using optimal service based on file type with fallback
        
        Args:
            file_content: Raw file bytes
            mime_type: Document MIME type
            user_id: User ID for rate limiting
            filename: Optional filename for additional context
            
        Returns:
            ProcessingResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Determine optimal processing method
            processing_method = self._determine_processing_method(mime_type, filename)
            
            logger.info(f"Processing document with {processing_method.value} - MIME: {mime_type}, Size: {len(file_content)} bytes")
            
            # Route to appropriate service
            if processing_method == ProcessingMethod.DOCUMENT_AI:
                result = await self._process_with_document_ai(file_content, mime_type, user_id)
            elif processing_method == ProcessingMethod.VISION_API:
                result = await self._process_with_vision_api(file_content, mime_type, user_id)
            else:
                result = await self._process_with_fallback(file_content, mime_type)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            logger.info(f"Document processing completed in {processing_time:.2f}s using {result.method_used.value}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Document processing failed: {e}")
            
            # Try fallback if enabled and not already used
            if self.enable_fallback:
                try:
                    logger.info("Attempting fallback processing")
                    fallback_result = await self._process_with_fallback(file_content, mime_type)
                    fallback_result.processing_time = processing_time
                    fallback_result.fallback_used = True
                    return fallback_result
                except Exception as fallback_error:
                    logger.error(f"Fallback processing also failed: {fallback_error}")
            
            return ProcessingResult(
                success=False,
                text="",
                method_used=ProcessingMethod.FALLBACK,
                confidence_scores={'overall_extraction': 0.0},
                processing_time=processing_time,
                metadata={'error': str(e)},
                error_message=f"Document processing failed: {str(e)}",
                fallback_used=True
            )
    
    def _determine_processing_method(self, mime_type: str, filename: Optional[str] = None) -> ProcessingMethod:
        """Determine optimal processing method based on file type"""
        
        # Check MIME type first
        if mime_type in self.pdf_mime_types and self.document_ai.enabled:
            return ProcessingMethod.DOCUMENT_AI
        
        if mime_type in self.image_mime_types and self.vision_api.enabled:
            return ProcessingMethod.VISION_API
        
        # Fallback to filename extension if MIME type is unclear
        if filename:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if file_ext == 'pdf' and self.document_ai.enabled:
                return ProcessingMethod.DOCUMENT_AI
            
            if file_ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'] and self.vision_api.enabled:
                return ProcessingMethod.VISION_API
        
        # Default fallback
        return ProcessingMethod.FALLBACK
    
    async def _process_with_document_ai(
        self, 
        file_content: bytes, 
        mime_type: str, 
        user_id: str
    ) -> ProcessingResult:
        """Process document using Document AI"""
        try:
            # Use existing Document AI service
            doc_ai_result = self.document_ai.process_legal_document(file_content, mime_type)
            
            if doc_ai_result['success']:
                return ProcessingResult(
                    success=True,
                    text=doc_ai_result['text'],
                    method_used=ProcessingMethod.DOCUMENT_AI,
                    confidence_scores=doc_ai_result['confidence_scores'],
                    processing_time=0.0,  # Will be set by caller
                    metadata={
                        'entities': len(doc_ai_result.get('entities', [])),
                        'tables': len(doc_ai_result.get('tables', [])),
                        'key_value_pairs': len(doc_ai_result.get('key_value_pairs', [])),
                        'legal_clauses': len(doc_ai_result.get('legal_clauses', [])),
                        'api_used': 'Google Document AI',
                        'fallback_used': doc_ai_result.get('fallback_used', False)
                    }
                )
            else:
                raise Exception(doc_ai_result.get('error', 'Document AI processing failed'))
                
        except Exception as e:
            logger.error(f"Document AI processing failed: {e}")
            
            # Try Vision API as fallback for PDFs if enabled
            if self.enable_fallback and self.vision_api.enabled:
                logger.info("Falling back to Vision API for PDF processing")
                try:
                    return await self._process_with_vision_api(file_content, mime_type, user_id, fallback=True)
                except Exception as vision_error:
                    logger.error(f"Vision API fallback also failed: {vision_error}")
            
            raise e
    
    async def _process_with_vision_api(
        self, 
        file_content: bytes, 
        mime_type: str, 
        user_id: str,
        fallback: bool = False
    ) -> ProcessingResult:
        """Process document using Vision API"""
        try:
            # Determine image format from MIME type
            image_format = self._mime_to_image_format(mime_type)
            
            # Use Vision API service
            vision_result = await self.vision_api.detect_text_in_image(
                file_content, 
                user_id, 
                image_format, 
                preprocess=True
            )
            
            if vision_result['success']:
                return ProcessingResult(
                    success=True,
                    text=vision_result['text'],
                    method_used=ProcessingMethod.VISION_API,
                    confidence_scores=vision_result['confidence_scores'],
                    processing_time=0.0,  # Will be set by caller
                    metadata={
                        'text_annotations': len(vision_result.get('text_annotations', [])),
                        'bounding_boxes': len(vision_result.get('bounding_boxes', [])),
                        'legal_sections': len(vision_result.get('legal_sections', [])),
                        'api_used': 'Google Cloud Vision API',
                        'image_preprocessing_applied': True,
                        'fallback_used': fallback
                    }
                )
            else:
                raise Exception(vision_result.get('error', 'Vision API processing failed'))
                
        except Exception as e:
            logger.error(f"Vision API processing failed: {e}")
            
            # Try Document AI as fallback for images if enabled and not already fallback
            if self.enable_fallback and not fallback and self.document_ai.enabled:
                logger.info("Falling back to Document AI for image processing")
                try:
                    return await self._process_with_document_ai(file_content, mime_type, user_id)
                except Exception as doc_ai_error:
                    logger.error(f"Document AI fallback also failed: {doc_ai_error}")
            
            raise e
    
    async def _process_with_fallback(self, file_content: bytes, mime_type: str) -> ProcessingResult:
        """Basic fallback processing when both services are unavailable"""
        try:
            # Try basic text extraction for PDFs
            if mime_type in self.pdf_mime_types:
                text = self._extract_pdf_text_fallback(file_content)
                if text:
                    return ProcessingResult(
                        success=True,
                        text=text,
                        method_used=ProcessingMethod.FALLBACK,
                        confidence_scores={'overall_extraction': 0.5},
                        processing_time=0.0,
                        metadata={
                            'api_used': 'Fallback PDF extraction',
                            'method': 'PyPDF2'
                        },
                        fallback_used=True
                    )
            
            # For images, we can't extract text without OCR services
            if mime_type in self.image_mime_types:
                return ProcessingResult(
                    success=False,
                    text="",
                    method_used=ProcessingMethod.FALLBACK,
                    confidence_scores={'overall_extraction': 0.0},
                    processing_time=0.0,
                    metadata={
                        'api_used': 'Fallback (no OCR available)',
                        'message': 'Image text extraction requires Vision API'
                    },
                    error_message="Image text extraction not available - Vision API not configured",
                    fallback_used=True
                )
            
            # Unknown file type
            return ProcessingResult(
                success=False,
                text="",
                method_used=ProcessingMethod.FALLBACK,
                confidence_scores={'overall_extraction': 0.0},
                processing_time=0.0,
                metadata={'api_used': 'Fallback'},
                error_message=f"Unsupported file type: {mime_type}",
                fallback_used=True
            )
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return ProcessingResult(
                success=False,
                text="",
                method_used=ProcessingMethod.FALLBACK,
                confidence_scores={'overall_extraction': 0.0},
                processing_time=0.0,
                metadata={'api_used': 'Fallback'},
                error_message=f"All processing methods failed: {str(e)}",
                fallback_used=True
            )
    
    def _extract_pdf_text_fallback(self, file_content: bytes) -> str:
        """Fallback PDF text extraction using PyPDF2"""
        try:
            import io
            from PyPDF2 import PdfReader
            
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Fallback PDF extraction failed: {e}")
            return ""
    
    def _mime_to_image_format(self, mime_type: str) -> str:
        """Convert MIME type to image format string"""
        mime_to_format = {
            'image/jpeg': 'JPEG',
            'image/jpg': 'JPEG',
            'image/png': 'PNG',
            'image/webp': 'WEBP',
            'image/bmp': 'BMP',
            'image/gif': 'GIF'
        }
        
        return mime_to_format.get(mime_type, 'JPEG')
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all integrated services"""
        status = {
            'dual_vision_service': {
                'enabled': True,
                'fallback_enabled': self.enable_fallback
            },
            'document_ai': {
                'enabled': self.document_ai.enabled,
                'project_id': self.document_ai.project_id,
                'location': self.document_ai.location
            },
            'vision_api': {
                'enabled': self.vision_api.enabled,
                'project_id': self.vision_api.project_id,
                'location': self.vision_api.location
            }
        }
        
        # Test connectivity if services are enabled
        if self.document_ai.enabled:
            try:
                doc_ai_status = await self.document_ai.verify_credentials()
                status['document_ai']['connectivity'] = 'connected' if doc_ai_status else 'failed'
            except Exception as e:
                status['document_ai']['connectivity'] = f'error: {str(e)}'
        
        if self.vision_api.enabled:
            try:
                vision_status = await self.vision_api.verify_credentials()
                status['vision_api']['connectivity'] = 'connected' if vision_status else 'failed'
            except Exception as e:
                status['vision_api']['connectivity'] = f'error: {str(e)}'
        
        return status
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats for each service"""
        return {
            'document_ai': list(self.pdf_mime_types),
            'vision_api': list(self.image_mime_types),
            'all_supported': list(self.pdf_mime_types | self.image_mime_types)
        }


# Global instance
dual_vision_service = DualVisionService()