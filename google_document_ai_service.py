"""
Google Cloud Document AI Service for Enhanced Legal Document Processing
Uses Document AI to extract structured data from legal documents
"""

import os
import json
from typing import Dict, List, Any, Optional
from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import logging

logger = logging.getLogger(__name__)

class GoogleDocumentAIService:
    """
    Google Cloud Document AI service for legal document processing
    Extracts entities, tables, and structured data from legal documents
    """
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')  # us, eu
        self.processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
        
        # Set up authentication
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        if not self.project_id:
            logger.warning("Google Document AI not configured - missing project ID, using fallback processing")
            self.enabled = False
            return
            
        try:
            # Initialize Document AI client
            opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
            self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
            
            # For now, we'll use a general processor or create one if processor_id is not set
            if self.processor_id:
                self.processor_name = self.client.processor_path(
                    self.project_id, self.location, self.processor_id
                )
            else:
                # Use a fallback approach without specific processor
                self.processor_name = None
                logger.info("Document AI initialized without specific processor - will use basic processing")
            
            self.enabled = True
            logger.info("Google Document AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Document AI: {e}")
            self.enabled = False
    
    def process_legal_document(self, document_content: bytes, mime_type: str = "application/pdf") -> Dict[str, Any]:
        """
        Process legal document using Google Document AI
        
        Args:
            document_content: Raw document bytes
            mime_type: Document MIME type (application/pdf, image/jpeg, etc.)
            
        Returns:
            Dict containing extracted entities, tables, and structured data
        """
        if not self.enabled:
            return self._fallback_processing(document_content)
            
        try:
            # Configure the process request
            raw_document = documentai.RawDocument(content=document_content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=self.processor_name, raw_document=raw_document)
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract structured information
            extracted_data = {
                'success': True,
                'text': document.text,
                'entities': self._extract_entities(document),
                'tables': self._extract_tables(document),
                'key_value_pairs': self._extract_key_value_pairs(document),
                'legal_clauses': self._identify_legal_clauses(document),
                'confidence_scores': self._get_confidence_scores(document),
                'processing_time': 0.0  # Will be calculated by caller
            }
            
            logger.info(f"Document AI processing successful - extracted {len(extracted_data['entities'])} entities")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Document AI processing failed: {e}")
            return self._fallback_processing(document_content)
    
    def _extract_entities(self, document) -> List[Dict[str, Any]]:
        """Extract named entities from the document"""
        entities = []
        
        for entity in document.entities:
            entities.append({
                'type': entity.type_,
                'text': entity.text_anchor.content if entity.text_anchor else entity.mention_text,
                'confidence': entity.confidence,
                'page_refs': [page_ref.page for page_ref in entity.page_anchor.page_refs] if entity.page_anchor else [],
                'normalized_value': entity.normalized_value.text if entity.normalized_value else None
            })
        
        return entities
    
    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """Extract tables from the document"""
        tables = []
        
        for page in document.pages:
            for table in page.tables:
                table_data = {
                    'headers': [],
                    'rows': [],
                    'page_number': page.page_number if hasattr(page, 'page_number') else 0
                }
                
                # Extract table headers and rows
                for row_idx, row in enumerate(table.header_rows):
                    header_row = []
                    for cell in row.cells:
                        header_row.append(self._get_text_from_layout(cell.layout, document.text))
                    table_data['headers'].append(header_row)
                
                for row in table.body_rows:
                    body_row = []
                    for cell in row.cells:
                        body_row.append(self._get_text_from_layout(cell.layout, document.text))
                    table_data['rows'].append(body_row)
                
                tables.append(table_data)
        
        return tables
    
    def _extract_key_value_pairs(self, document) -> List[Dict[str, Any]]:
        """Extract key-value pairs (form fields) from the document"""
        key_value_pairs = []
        
        for page in document.pages:
            for form_field in page.form_fields:
                key_text = self._get_text_from_layout(form_field.field_name.layout, document.text) if form_field.field_name else ""
                value_text = self._get_text_from_layout(form_field.field_value.layout, document.text) if form_field.field_value else ""
                
                key_value_pairs.append({
                    'key': key_text.strip(),
                    'value': value_text.strip(),
                    'confidence': form_field.field_name.confidence if form_field.field_name else 0.0
                })
        
        return key_value_pairs
    
    def _identify_legal_clauses(self, document) -> List[Dict[str, Any]]:
        """Identify and extract legal clauses using Document AI insights"""
        clauses = []
        
        # Look for common legal clause patterns
        legal_patterns = [
            'termination', 'liability', 'indemnification', 'confidentiality',
            'non-disclosure', 'payment terms', 'governing law', 'dispute resolution',
            'force majeure', 'intellectual property', 'warranties', 'representations'
        ]
        
        for entity in document.entities:
            entity_text = entity.text_anchor.content if entity.text_anchor else entity.mention_text
            entity_lower = entity_text.lower()
            
            for pattern in legal_patterns:
                if pattern in entity_lower:
                    clauses.append({
                        'type': pattern.replace('_', ' ').title(),
                        'text': entity_text,
                        'confidence': entity.confidence,
                        'location': self._get_entity_location(entity)
                    })
                    break
        
        return clauses
    
    def _get_confidence_scores(self, document) -> Dict[str, float]:
        """Calculate overall confidence scores for different aspects"""
        entity_confidences = [entity.confidence for entity in document.entities if entity.confidence > 0]
        
        return {
            'overall_extraction': sum(entity_confidences) / len(entity_confidences) if entity_confidences else 0.0,
            'entity_detection': len([c for c in entity_confidences if c > 0.8]) / len(entity_confidences) if entity_confidences else 0.0,
            'text_quality': 0.9 if document.text and len(document.text.strip()) > 100 else 0.5
        }
    
    def _get_text_from_layout(self, layout, document_text: str) -> str:
        """Extract text from layout object"""
        if not layout or not layout.text_anchor:
            return ""
        
        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(document_text)
            text_segments.append(document_text[start_index:end_index])
        
        return "".join(text_segments)
    
    def _get_entity_location(self, entity) -> Dict[str, Any]:
        """Get location information for an entity"""
        if not entity.page_anchor:
            return {}
        
        return {
            'pages': [page_ref.page for page_ref in entity.page_anchor.page_refs],
            'bounding_boxes': [
                {
                    'vertices': [(vertex.x, vertex.y) for vertex in page_ref.bounding_poly.vertices]
                } for page_ref in entity.page_anchor.page_refs if page_ref.bounding_poly
            ]
        }
    
    def _fallback_processing(self, document_content: bytes) -> Dict[str, Any]:
        """Fallback processing when Document AI is not available"""
        return {
            'success': False,
            'text': "",
            'entities': [],
            'tables': [],
            'key_value_pairs': [],
            'legal_clauses': [],
            'confidence_scores': {'overall_extraction': 0.0},
            'error': 'Google Document AI not available - using basic text processing'
        }

# Global instance
document_ai_service = GoogleDocumentAIService()