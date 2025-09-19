"""
File Processing Module with PDF Support and Validation
Handles file uploads, PDF text extraction, and validation
"""

import os
import re
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from werkzeug.datastructures import FileStorage
import PyPDF2
from io import BytesIO

@dataclass
class FileProcessingResult:
    """Dataclass to hold the result of file processing."""
    success: bool
    text_content: str
    error_message: Optional[str]
    file_info: Dict[str, Any]
    warnings: list

class FileProcessor:
    """
    Enhanced file processing with PDF support and validation.
    Reads the uploaded file only once for efficiency and stability.
    """
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TEXT_LENGTH = 50000  # characters
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf'}
    SUPPORTED_MIME_TYPES = {
        'text/plain',
        'application/pdf',
        'application/x-pdf'
    }
    
    def __init__(self):
        pass
    
    def process_uploaded_file(self, file: FileStorage) -> FileProcessingResult:
        """
        Process uploaded file with comprehensive validation and text extraction.
        """
        result = FileProcessingResult(
            success=False,
            text_content="",
            error_message=None,
            file_info={},
            warnings=[]
        )
        
        try:
            # --- FIX: Read the file content ONCE into a BytesIO buffer ---
            file_content = file.read()
            file_buffer = BytesIO(file_content)
            file_size = len(file_content)
            
            # Pass the file's metadata to the validator, not the stream object
            validation_result = self._validate_file(file.filename, file.content_type, file_size)

            if not validation_result[0]:
                result.error_message = validation_result[1]
                return result

            # Extract file information
            result.file_info = {
                'filename': file.filename,
                'size': file_size,  # --- FIX: Use the pre-calculated size ---
                'content_type': file.content_type
            }
            
            # Extract text based on file type, passing the buffer
            if file.filename.lower().endswith('.pdf'):
                text_result = self._extract_pdf_text(file_buffer)
            else:
                text_result = self._extract_text_file(file_buffer)
            
            if not text_result[0]:
                result.error_message = text_result[1]
                return result
            
            result.text_content = text_result[1]
            
            # Validate extracted text
            text_validation = self._validate_extracted_text(result.text_content)
            if not text_validation[0]:
                result.error_message = text_validation[1]
                return result
            
            # Add any warnings
            result.warnings = text_validation[2] if len(text_validation) > 2 else []
            
            result.success = True
            return result
            
        except Exception as e:
            result.error_message = f"Unexpected error processing file: {str(e)}"
            return result
    
    def _validate_file(self, filename: str, content_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        --- MODIFIED: Validates uploaded file metadata instead of the file stream ---
        """
        if not filename:
            return False, "No file selected. Please choose a file to upload."
        
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type '{file_ext}'. Please upload a PDF or TXT file."
        
        if content_type and content_type not in self.SUPPORTED_MIME_TYPES:
            return False, f"Invalid file format. Expected PDF or text file, got '{content_type}'."
        
        if file_size == 0:
            return False, "File is empty. Please upload a file with content."
        
        if file_size > self.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large ({size_mb:.1f}MB). Maximum size is {self.MAX_FILE_SIZE // (1024 * 1024)}MB."
        
        return True, None
    
    def _extract_pdf_text(self, file_buffer: BytesIO) -> Tuple[bool, str]:
        """
        --- MODIFIED: Extracts text from a BytesIO buffer ---
        """
        try:
            # Pass the BytesIO buffer directly to the reader
            pdf_reader = PyPDF2.PdfReader(file_buffer)
            
            if pdf_reader.is_encrypted:
                return False, "PDF file is password protected. Please upload an unprotected PDF."
            
            extracted_text = ""
            total_pages = len(pdf_reader.pages)
            
            if total_pages == 0:
                return False, "PDF file contains no pages."
            
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                except Exception as e:
                    print(f"Error extracting text from page {page_num + 1}: {e}")
                    continue
            
            if not extracted_text.strip():
                return False, "Could not extract text from PDF. The file may contain only images or be corrupted."
            
            return True, extracted_text.strip()
            
        except Exception as e:
            return False, f"Error reading PDF file: {str(e)}. Please ensure the file is a valid PDF."
    
    def _extract_text_file(self, file_buffer: BytesIO) -> Tuple[bool, str]:
        """
        --- MODIFIED: Extracts text from a BytesIO buffer ---
        """
        try:
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    file_buffer.seek(0)
                    content = file_buffer.read().decode(encoding)
                    return True, content
                except UnicodeDecodeError:
                    continue
            
            return False, "Could not read text file. Please ensure the file uses UTF-8 or standard text encoding."
            
        except Exception as e:
            return False, f"Error reading text file: {str(e)}"
    
    def _validate_extracted_text(self, text: str) -> Tuple[bool, Optional[str], list]:
        """Validate extracted text content"""
        warnings = []
        
        if not text or not text.strip():
            return False, "No text content found in the file.", warnings
        
        text_length = len(text.strip())
        
        if text_length < 100:
            return False, "Document text is too short (less than 100 characters). Please upload a complete legal document.", warnings
        
        if text_length > self.MAX_TEXT_LENGTH:
            warnings.append(f"Document is very long ({text_length:,} characters). Analysis will be limited to the first {self.MAX_TEXT_LENGTH:,} characters.")
            text = text[:self.MAX_TEXT_LENGTH]
        
        special_char_ratio = len(re.findall(r'[^\w\s\.,;:\!\?\-\(\)]', text)) / len(text)
        if special_char_ratio > 0.1:
            warnings.append("Document may contain OCR errors or special formatting. Analysis accuracy may be reduced.")
        
        word_count = len(text.split())
        if word_count < 50:
            return False, "Document appears to contain insufficient text for meaningful analysis.", warnings
        
        legal_indicators = ['agreement', 'contract', 'terms', 'conditions', 'party', 'parties', 'shall', 'hereby']
        found_indicators = sum(1 for indicator in legal_indicators if indicator.lower() in text.lower())
        
        if found_indicators < 2:
            warnings.append("Document may not be a legal document. Analysis may be limited.")
        
        return True, None, warnings
    
    def get_file_info_summary(self, file_info: Dict[str, Any]) -> str:
        """Generate a summary of file information"""
        if not file_info:
            return "No file information available"
        
        size_mb = file_info.get('size', 0) / (1024 * 1024)
        return f"File: {file_info.get('filename', 'Unknown')} ({size_mb:.1f}MB, {file_info.get('content_type', 'Unknown type')})"