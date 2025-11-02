"""
File processing service for FastAPI backend
Enhanced with dual vision service for optimal document processing
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import PyPDF2
from io import BytesIO

from services.dual_vision_service import dual_vision_service

logger = logging.getLogger(__name__)


@dataclass
class FileProcessingResult:
    """Result of file processing operation"""
    success: bool
    text_content: str
    error_message: Optional[str]
    file_info: Dict[str, Any]
    warnings: list


class FileService:
    """Service for processing uploaded files with enhanced image support"""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB (increased for images)
    MAX_TEXT_LENGTH = 50000  # characters
    
    # Supported file types (expanded for images)
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    SUPPORTED_MIME_TYPES = {
        'text/plain',
        'application/pdf',
        'application/x-pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'image/bmp',
        'image/gif'
    }
    
    def __init__(self):
        self.dual_vision = dual_vision_service
    
    async def process_file_content_enhanced(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        user_id: str = "anonymous"
    ) -> FileProcessingResult:
        """Enhanced file processing using dual vision service for optimal text extraction"""
        try:
            # Validate file size
            if len(file_content) > self.MAX_FILE_SIZE:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=f"File size exceeds maximum limit of {self.MAX_FILE_SIZE // (1024*1024)}MB",
                    file_info={"filename": filename, "size": len(file_content)},
                    warnings=[]
                )
            
            # Validate file type
            file_extension = self._get_file_extension(filename)
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=f"Unsupported file type: {file_extension}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                    file_info={"filename": filename, "extension": file_extension},
                    warnings=[]
                )
            
            # Use dual vision service for enhanced processing
            processing_result = await self.dual_vision.process_document(
                file_content=file_content,
                mime_type=content_type,
                user_id=user_id,
                filename=filename
            )
            
            if not processing_result.success:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=processing_result.error_message or "Document processing failed",
                    file_info={
                        "filename": filename,
                        "size": len(file_content),
                        "extension": file_extension,
                        "processing_method": processing_result.method_used.value,
                        "fallback_used": processing_result.fallback_used
                    },
                    warnings=[]
                )
            
            text_content = processing_result.text
            
            # Validate extracted text
            if not text_content or len(text_content.strip()) < 100:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message="Document text must be at least 100 characters long for meaningful analysis",
                    file_info={
                        "filename": filename, 
                        "text_length": len(text_content),
                        "processing_method": processing_result.method_used.value,
                        "confidence_scores": processing_result.confidence_scores
                    },
                    warnings=[]
                )
            
            # Handle text length limits
            warnings = []
            if len(text_content) > self.MAX_TEXT_LENGTH:
                text_content = text_content[:self.MAX_TEXT_LENGTH]
                warnings.append(f"Document text was truncated to {self.MAX_TEXT_LENGTH} characters")
            
            # Validate content appears to be legal document
            if not self._validate_legal_content(text_content):
                warnings.append("This document may not contain typical legal language")
            
            # Add processing method information to warnings if fallback was used
            if processing_result.fallback_used:
                warnings.append(f"Used fallback processing method: {processing_result.method_used.value}")
            
            return FileProcessingResult(
                success=True,
                text_content=text_content,
                error_message=None,
                file_info={
                    "filename": filename,
                    "size": len(file_content),
                    "extension": file_extension,
                    "text_length": len(text_content),
                    "processing_method": processing_result.method_used.value,
                    "processing_time": processing_result.processing_time,
                    "confidence_scores": processing_result.confidence_scores,
                    "metadata": processing_result.metadata,
                    "fallback_used": processing_result.fallback_used
                },
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Enhanced file processing failed: {e}")
            return FileProcessingResult(
                success=False,
                text_content="",
                error_message=f"Failed to process file: {str(e)}",
                file_info={"filename": filename},
                warnings=[]
            )

    def process_file_content(self, file_content: bytes, filename: str, content_type: str) -> FileProcessingResult:
        """Process file content and extract text"""
        try:
            # Validate file size
            if len(file_content) > self.MAX_FILE_SIZE:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=f"File size exceeds maximum limit of {self.MAX_FILE_SIZE // (1024*1024)}MB",
                    file_info={"filename": filename, "size": len(file_content)},
                    warnings=[]
                )
            
            # Validate file type
            file_extension = self._get_file_extension(filename)
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=f"Unsupported file type: {file_extension}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                    file_info={"filename": filename, "extension": file_extension},
                    warnings=[]
                )
            
            # Extract text based on file type
            if file_extension == '.pdf':
                text_content = self._extract_pdf_text(file_content)
            elif file_extension == '.txt':
                text_content = self._extract_text_content(file_content)
            else:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message=f"Unsupported file type: {file_extension}",
                    file_info={"filename": filename, "extension": file_extension},
                    warnings=[]
                )
            
            # Validate extracted text
            if not text_content or len(text_content.strip()) < 100:
                return FileProcessingResult(
                    success=False,
                    text_content="",
                    error_message="Document text must be at least 100 characters long for meaningful analysis",
                    file_info={"filename": filename, "text_length": len(text_content)},
                    warnings=[]
                )
            
            if len(text_content) > self.MAX_TEXT_LENGTH:
                # Truncate text but warn user
                text_content = text_content[:self.MAX_TEXT_LENGTH]
                warnings = [f"Document text was truncated to {self.MAX_TEXT_LENGTH} characters"]
            else:
                warnings = []
            
            # Validate content appears to be legal document
            if not self._validate_legal_content(text_content):
                warnings.append("This document may not contain typical legal language")
            
            return FileProcessingResult(
                success=True,
                text_content=text_content,
                error_message=None,
                file_info={
                    "filename": filename,
                    "size": len(file_content),
                    "extension": file_extension,
                    "text_length": len(text_content)
                },
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            return FileProcessingResult(
                success=False,
                text_content="",
                error_message=f"Failed to process file: {str(e)}",
                file_info={"filename": filename},
                warnings=[]
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if '.' not in filename:
            return ''
        return '.' + filename.split('.')[-1].lower()
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_text_content(self, file_content: bytes) -> str:
        """Extract text from text file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text_content = file_content.decode(encoding)
                    return text_content.strip()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with error handling
            text_content = file_content.decode('utf-8', errors='replace')
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _validate_legal_content(self, text: str) -> bool:
        """Basic validation to check if content appears to be legal document"""
        legal_keywords = [
            'agreement', 'contract', 'party', 'parties', 'terms', 'conditions',
            'shall', 'hereby', 'whereas', 'therefore', 'obligations', 'rights',
            'liability', 'breach', 'termination', 'effective', 'binding', 'legal'
        ]
        
        text_lower = text.lower()
        found_keywords = [keyword for keyword in legal_keywords if keyword in text_lower]
        
        # Require at least 2 legal keywords for basic validation
        return len(found_keywords) >= 2