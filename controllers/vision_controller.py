"""
Vision API controller for FastAPI backend
Handles image processing and text extraction operations
"""

import logging
from fastapi import HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List

from services.dual_vision_service import dual_vision_service
from services.google_cloud_vision_service import vision_service

logger = logging.getLogger(__name__)


class VisionController:
    """Controller for Vision API operations"""
    
    def __init__(self):
        self.dual_vision = dual_vision_service
        self.vision_service = vision_service
    
    async def extract_text_from_image(
        self,
        file: UploadFile = File(...),
        user_id: str = "anonymous",
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """Extract text from uploaded image using Vision API"""
        try:
            logger.info(f"Processing image for text extraction: {file.filename}")
            
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            # Validate file type
            supported_image_types = {
                'image/jpeg', 'image/jpg', 'image/png', 
                'image/webp', 'image/bmp', 'image/gif'
            }
            
            content_type = file.content_type or 'application/octet-stream'
            logger.info(f"Image content type: {content_type}")
            
            if content_type not in supported_image_types:
                # Check file extension as fallback
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                if file_ext not in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif']:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Unsupported image type: {content_type}. Supported types: JPEG, PNG, WEBP, BMP, GIF"
                    )
                # Map extension to MIME type
                ext_to_mime = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'webp': 'image/webp',
                    'bmp': 'image/bmp',
                    'gif': 'image/gif'
                }
                content_type = ext_to_mime.get(file_ext, 'image/jpeg')
            
            try:
                # Read file content with size limit (20MB)
                file_content = await file.read(20 * 1024 * 1024)  # 20MB limit
                if len(file_content) == 20 * 1024 * 1024:
                    raise HTTPException(
                        status_code=422,
                        detail="Image size exceeds maximum limit of 20MB"
                    )
            except Exception as e:
                logger.error(f"Error reading image file: {e}")
                raise HTTPException(
                    status_code=422,
                    detail="Error reading image file. Please ensure the file is not corrupted."
                )
            
            # Extract image format from content type
            image_format = content_type.split('/')[-1].upper()
            if image_format == 'JPG':
                image_format = 'JPEG'
            
            # Use Vision API to extract text
            result = await self.vision_service.detect_text_in_image(
                image_content=file_content,
                user_id=user_id,
                image_format=image_format,
                preprocess=preprocess
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Text extraction failed')
                )
            
            # Return structured response
            response = {
                "success": True,
                "filename": file.filename,
                "extracted_text": result['text'],
                "high_confidence_text": result.get('high_confidence_text', ''),
                "confidence_scores": result['confidence_scores'],
                "text_blocks_detected": len(result.get('text_annotations', [])),
                "legal_sections_identified": len(result.get('legal_sections', [])),
                "processing_metadata": result.get('processing_metadata', {}),
                "warnings": []
            }
            
            # Add warnings based on confidence scores
            avg_confidence = result['confidence_scores'].get('average_confidence', 0.0)
            if avg_confidence < 0.7:
                response['warnings'].append(f"Low average confidence ({avg_confidence:.1%}). Text extraction may be inaccurate.")
            
            high_conf_ratio = result['confidence_scores'].get('high_confidence_ratio', 0.0)
            if high_conf_ratio < 0.5:
                response['warnings'].append(f"Only {high_conf_ratio:.1%} of text blocks have high confidence. Consider using a clearer image.")
            
            if result.get('fallback_used'):
                response['warnings'].append("Vision API not available - using fallback processing")
            
            logger.info(f"Text extraction completed: {file.filename}, {len(result['text'])} characters extracted")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image text extraction failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Text extraction failed: {str(e)}"
            )
    
    async def get_vision_service_status(self) -> Dict[str, Any]:
        """Get status of Vision API services"""
        try:
            status = await self.dual_vision.get_service_status()
            
            # Add additional Vision API specific information
            if self.vision_service.enabled:
                status['vision_api_details'] = {
                    'supported_formats': list(self.vision_service.supported_formats),
                    'max_file_size_mb': self.vision_service.max_file_size // (1024 * 1024),
                    'max_resolution': self.vision_service.max_resolution,
                    'min_confidence_threshold': self.vision_service.min_confidence_threshold,
                    'rate_limit_per_day': 100,  # From rate limiter
                    'cache_ttl_hours': 1
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get vision service status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get service status: {str(e)}"
            )
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """Get list of supported file formats"""
        try:
            formats = self.dual_vision.get_supported_formats()
            
            return {
                "success": True,
                "supported_formats": {
                    "images": [
                        "image/jpeg", "image/jpg", "image/png", 
                        "image/webp", "image/bmp", "image/gif"
                    ],
                    "documents": [
                        "application/pdf", "application/x-pdf",
                        "application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "text/plain"
                    ]
                },
                "file_size_limits": {
                    "images": "20MB",
                    "documents": "20MB"
                },
                "processing_methods": {
                    "images": "Google Cloud Vision API",
                    "pdfs": "Google Document AI",
                    "fallback": "Basic text extraction"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get supported formats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get supported formats: {str(e)}"
            )
    
    async def analyze_multiple_image_documents(
        self,
        files: List[UploadFile] = File(...),
        document_type: str = Form("general_contract"),
        user_expertise_level: str = Form("beginner"),
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Analyze multiple legal document images using Vision API + document analysis pipeline
        Combines text from all images and performs unified document analysis
        """
        try:
            logger.info(f"Analyzing {len(files)} legal document images")
            
            if len(files) > 10:  # Reasonable limit
                raise HTTPException(
                    status_code=400,
                    detail="Maximum 10 images allowed per analysis"
                )
            
            combined_text = ""
            extraction_results = []
            total_confidence_scores = []
            
            # Process each image
            for i, file in enumerate(files):
                logger.info(f"Processing image {i+1}/{len(files)}: {file.filename}")
                
                # Extract text using Vision API
                text_extraction_result = await self.extract_text_from_image(
                    file=file,
                    user_id=user_id,
                    preprocess=True
                )
                
                if not text_extraction_result['success']:
                    logger.warning(f"Failed to extract text from {file.filename}")
                    continue
                
                extracted_text = text_extraction_result['extracted_text']
                
                # Add to combined text with page separator
                if extracted_text.strip():
                    if combined_text:
                        combined_text += f"\n\n--- Page {i+1} ({file.filename}) ---\n\n"
                    combined_text += extracted_text
                    
                    extraction_results.append({
                        "filename": file.filename,
                        "page_number": i + 1,
                        "extracted_text_length": len(extracted_text),
                        "confidence_scores": text_extraction_result['confidence_scores'],
                        "text_blocks_detected": text_extraction_result['text_blocks_detected']
                    })
                    
                    total_confidence_scores.append(text_extraction_result['confidence_scores']['average_confidence'])
            
            if not combined_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No readable text found in any of the uploaded images"
                )
            
            # Validate combined text length
            if len(combined_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Combined extracted text is too short for meaningful legal analysis (minimum 100 characters)"
                )
            
            # Import here to avoid circular imports
            from models.document_models import DocumentAnalysisRequest
            from services.document_service import DocumentService
            
            # Create document analysis request with combined text
            analysis_request = DocumentAnalysisRequest(
                document_text=combined_text,
                document_type=document_type,
                user_expertise_level=user_expertise_level
            )
            
            # Perform document analysis
            document_service = DocumentService()
            analysis_result = await document_service.analyze_document(analysis_request)
            
            # Calculate overall confidence
            overall_confidence = sum(total_confidence_scores) / len(total_confidence_scores) if total_confidence_scores else 0
            
            # Combine results
            combined_result = {
                "success": True,
                "analysis_id": analysis_result.analysis_id,
                "total_images_processed": len(extraction_results),
                "images_with_text": len(extraction_results),
                "text_extraction": {
                    "method": "Google Cloud Vision API (Multiple Images)",
                    "combined_text_length": len(combined_text),
                    "overall_confidence": overall_confidence,
                    "image_results": extraction_results
                },
                "document_analysis": {
                    "overall_risk": {
                        "level": analysis_result.overall_risk.level.value,
                        "score": analysis_result.overall_risk.score,
                        "severity": analysis_result.overall_risk.severity,
                        "confidence_percentage": analysis_result.overall_risk.confidence_percentage
                    },
                    "total_clauses": len(analysis_result.clause_assessments),
                    "processing_time": analysis_result.processing_time,
                    "summary": analysis_result.summary
                },
                "warnings": []
            }
            
            # Add warnings based on confidence scores
            if overall_confidence < 0.7:
                combined_result['warnings'].append(f"Low overall confidence ({overall_confidence:.1%}). Text extraction may be inaccurate.")
            
            if overall_confidence < 0.8:
                combined_result['warnings'].append(
                    "Text extraction confidence is below 80%. Legal analysis may be affected by OCR inaccuracies."
                )
            
            # Check for images with no text
            images_without_text = len(files) - len(extraction_results)
            if images_without_text > 0:
                combined_result['warnings'].append(
                    f"{images_without_text} image(s) contained no readable text and were skipped."
                )
            
            logger.info(f"Multiple image document analysis completed: {len(files)} images processed")
            return combined_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Multiple image document analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Multiple image document analysis failed: {str(e)}"
            )

    async def analyze_image_document(
        self,
        file: UploadFile = File(...),
        document_type: str = Form("general_contract"),
        user_expertise_level: str = Form("beginner"),
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Analyze legal document from image using Vision API + document analysis pipeline
        This integrates Vision API text extraction with the existing document analysis
        """
        try:
            logger.info(f"Analyzing legal document from image: {file.filename}")
            
            # First extract text using Vision API
            text_extraction_result = await self.extract_text_from_image(
                file=file,
                user_id=user_id,
                preprocess=True
            )
            
            if not text_extraction_result['success']:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to extract text from image"
                )
            
            extracted_text = text_extraction_result['extracted_text']
            
            # Validate extracted text length
            if len(extracted_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Extracted text is too short for meaningful legal analysis (minimum 100 characters)"
                )
            
            # Import here to avoid circular imports
            from models.document_models import DocumentAnalysisRequest
            from services.document_service import DocumentService
            
            # Create document analysis request
            analysis_request = DocumentAnalysisRequest(
                document_text=extracted_text,
                document_type=document_type,
                user_expertise_level=user_expertise_level
            )
            
            # Perform document analysis
            document_service = DocumentService()
            analysis_result = await document_service.analyze_document(analysis_request)
            
            # Combine results
            combined_result = {
                "success": True,
                "analysis_id": analysis_result.analysis_id,
                "filename": file.filename,
                "text_extraction": {
                    "method": "Google Cloud Vision API",
                    "extracted_text_length": len(extracted_text),
                    "confidence_scores": text_extraction_result['confidence_scores'],
                    "text_blocks_detected": text_extraction_result['text_blocks_detected'],
                    "legal_sections_identified": text_extraction_result['legal_sections_identified']
                },
                "document_analysis": {
                    "overall_risk": {
                        "level": analysis_result.overall_risk.level.value,
                        "score": analysis_result.overall_risk.score,
                        "severity": analysis_result.overall_risk.severity,
                        "confidence_percentage": analysis_result.overall_risk.confidence_percentage
                    },
                    "total_clauses": len(analysis_result.clause_assessments),
                    "processing_time": analysis_result.processing_time,
                    "summary": analysis_result.summary
                },
                "warnings": text_extraction_result.get('warnings', [])
            }
            
            # Add analysis-specific warnings
            if text_extraction_result['confidence_scores']['average_confidence'] < 0.8:
                combined_result['warnings'].append(
                    "Text extraction confidence is below 80%. Legal analysis may be affected by OCR inaccuracies."
                )
            
            logger.info(f"Image document analysis completed: {file.filename}")
            return combined_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image document analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Image document analysis failed: {str(e)}"
            )