"""
File processing service for FastAPI backend
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import PyPDF2
from io import BytesIO

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
    """Service for processing uploaded files"""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TEXT_LENGTH = 50000  # characters
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx'}
    SUPPORTED_MIME_TYPES = {
        'text/plain',
        'application/pdf',
        'application/x-pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    def __init__(self):
        pass
    
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