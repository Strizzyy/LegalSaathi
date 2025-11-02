"""
Privacy-First Data Masking Service for LegalSaathi
Implements comprehensive PII detection and secure masking/unmasking
"""

import re
import uuid
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Conditional import for Cloud Run compatibility
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class EntityType(str, Enum):
    """Types of sensitive entities that can be masked"""
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    FINANCIAL = "FINANCIAL"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    LEGAL_ENTITY = "LEGAL_ENTITY"
    DATE = "DATE"
    CUSTOM = "CUSTOM"

@dataclass
class SensitiveEntity:
    """Represents a detected sensitive entity"""
    entity_type: EntityType
    original_text: str
    start_pos: int
    end_pos: int
    confidence: float
    masked_token: str
    context: str = ""

@dataclass
class MaskedDocument:
    """Represents a document with masked sensitive information"""
    masked_text: str
    mapping_id: str
    original_length: int
    masked_entities: List[SensitiveEntity]
    processing_timestamp: datetime
    expires_at: datetime

class PrivacyValidationResult(BaseModel):
    """Result of privacy validation check"""
    is_valid: bool
    violations: List[str] = Field(default_factory=list)
    risk_score: float = 0.0
    recommendations: List[str] = Field(default_factory=list)

class DataMaskingService:
    """
    Privacy-First Data Masking Service
    
    Provides comprehensive PII detection, secure masking, and unmasking capabilities
    with GDPR compliance features and audit trails.
    """
    
    def __init__(self):
        self.nlp = None
        self.cipher_suite = None
        self.mapping_store: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []
        self._initialize_nlp()
        self._initialize_encryption()
        
        # Regex patterns for PII detection
        self.patterns = {
            EntityType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            EntityType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            EntityType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
            EntityType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            EntityType.ADDRESS: r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b',
            EntityType.FINANCIAL: r'\$[\d,]+\.?\d*|\b\d+\.\d{2}\s*(?:USD|dollars?)\b',
            EntityType.DATE: r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        }
        
        # Legal entity patterns
        self.legal_entity_patterns = [
            r'\b[A-Z][A-Za-z\s&]+(?:LLC|Inc|Corp|Corporation|Company|Co\.|Ltd|Limited|LLP|LP)\b',
            r'\b(?:The\s+)?[A-Z][A-Za-z\s&]+(?:\s+(?:LLC|Inc|Corp|Corporation|Company|Co\.|Ltd|Limited|LLP|LP))\b'
        ]
        
    def _initialize_nlp(self):
        """Initialize spaCy NLP model with graceful fallback"""
        if not SPACY_AVAILABLE:
            logger.warning("📝 spaCy not available - using regex-based entity detection only")
            self.nlp = None
            return
            
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded successfully")
        except OSError as e:
            logger.warning(f"⚠️ spaCy model not available: {e}")
            logger.warning("📝 Falling back to regex-based entity detection")
            logger.info("💡 To enable advanced NLP features, install: python -m spacy download en_core_web_sm")
            self.nlp = None  # Use fallback methods
    
    def _initialize_encryption(self):
        """Initialize encryption for secure mapping storage"""
        try:
            # Generate a key from environment or create new one
            password = os.getenv('MASKING_PASSWORD', 'default-masking-key-change-in-production').encode()
            salt = os.getenv('MASKING_SALT', 'default-salt-change-in-production').encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher_suite = Fernet(key)
            logger.info("✅ Encryption initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption: {e}")
            raise Exception(f"Encryption initialization failed: {e}")
    
    def _log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log audit event for GDPR compliance"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'session_id': str(uuid.uuid4())[:8]
        }
        self.audit_log.append(audit_entry)
        logger.info(f"📝 Audit: {event_type} - {details.get('summary', 'No summary')}")
    
    def detect_entities_with_spacy(self, text: str) -> List[SensitiveEntity]:
        """Detect entities using spaCy NLP"""
        if not self.nlp:
            logger.warning("spaCy not available, returning empty entities list")
            return []
            
        entities = []
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                entity_type = None
                confidence = 0.8  # Default confidence for spaCy entities
                
                # Map spaCy labels to our entity types
                if ent.label_ == "PERSON":
                    entity_type = EntityType.PERSON
                elif ent.label_ in ["ORG", "NORP"]:
                    entity_type = EntityType.LEGAL_ENTITY
                elif ent.label_ == "DATE":
                    entity_type = EntityType.DATE
                elif ent.label_ in ["MONEY", "PERCENT"]:
                    entity_type = EntityType.FINANCIAL
                
                if entity_type:
                    masked_token = f"[{entity_type.value}_{len(entities) + 1}]"
                    
                    entity = SensitiveEntity(
                        entity_type=entity_type,
                        original_text=ent.text,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=confidence,
                        masked_token=masked_token,
                        context=text[max(0, ent.start_char-20):ent.end_char+20]
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.warning(f"⚠️ spaCy entity detection failed: {e}")
        
        return entities
    
    def detect_entities_with_regex(self, text: str) -> List[SensitiveEntity]:
        """Detect entities using regex patterns"""
        entities = []
        
        # Standard PII patterns
        for entity_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                masked_token = f"[{entity_type.value}_{len(entities) + 1}]"
                
                entity = SensitiveEntity(
                    entity_type=entity_type,
                    original_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,  # High confidence for regex matches
                    masked_token=masked_token,
                    context=text[max(0, match.start()-20):match.end()+20]
                )
                entities.append(entity)
        
        # Legal entity patterns
        for pattern in self.legal_entity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                masked_token = f"[{EntityType.LEGAL_ENTITY.value}_{len(entities) + 1}]"
                
                entity = SensitiveEntity(
                    entity_type=EntityType.LEGAL_ENTITY,
                    original_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.85,
                    masked_token=masked_token,
                    context=text[max(0, match.start()-20):match.end()+20]
                )
                entities.append(entity)
        
        return entities
    
    def _merge_and_deduplicate_entities(self, spacy_entities: List[SensitiveEntity], 
                                      regex_entities: List[SensitiveEntity]) -> List[SensitiveEntity]:
        """Merge and deduplicate entities from different detection methods"""
        all_entities = spacy_entities + regex_entities
        
        # Sort by start position
        all_entities.sort(key=lambda x: x.start_pos)
        
        # Remove overlapping entities (keep higher confidence)
        merged_entities = []
        for entity in all_entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in merged_entities:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Overlap detected
                    if entity.confidence > existing.confidence:
                        # Replace with higher confidence entity
                        merged_entities.remove(existing)
                        merged_entities.append(entity)
                    overlaps = True
                    break
            
            if not overlaps:
                merged_entities.append(entity)
        
        # Re-sort and update token numbers
        merged_entities.sort(key=lambda x: x.start_pos)
        for i, entity in enumerate(merged_entities):
            entity.masked_token = f"[{entity.entity_type.value}_{i + 1}]"
        
        return merged_entities
    
    async def mask_document(self, document_text: str, expires_hours: int = 24) -> MaskedDocument:
        """
        Mask sensitive information in document text
        
        Args:
            document_text: Original document text
            expires_hours: Hours until mapping expires (for privacy)
            
        Returns:
            MaskedDocument with masked text and metadata
        """
        try:
            # Detect entities using both methods
            spacy_entities = self.detect_entities_with_spacy(document_text)
            regex_entities = self.detect_entities_with_regex(document_text)
            
            # Merge and deduplicate
            entities = self._merge_and_deduplicate_entities(spacy_entities, regex_entities)
            
            # Create masked text
            masked_text = document_text
            offset = 0
            
            for entity in entities:
                # Adjust positions for previous replacements
                start_pos = entity.start_pos + offset
                end_pos = entity.end_pos + offset
                
                # Replace original text with masked token
                masked_text = (masked_text[:start_pos] + 
                             entity.masked_token + 
                             masked_text[end_pos:])
                
                # Update offset
                offset += len(entity.masked_token) - len(entity.original_text)
            
            # Generate mapping ID and store securely
            mapping_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # Create secure mapping
            mapping_data = {
                'entities': [
                    {
                        'entity_type': entity.entity_type.value,
                        'original_text': entity.original_text,
                        'masked_token': entity.masked_token,
                        'start_pos': entity.start_pos,
                        'end_pos': entity.end_pos,
                        'confidence': entity.confidence,
                        'context': entity.context
                    }
                    for entity in entities
                ],
                'original_length': len(document_text),
                'masked_length': len(masked_text),
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            # Encrypt and store mapping
            encrypted_mapping = self.cipher_suite.encrypt(str(mapping_data).encode())
            self.mapping_store[mapping_id] = {
                'encrypted_data': encrypted_mapping,
                'expires_at': expires_at,
                'entity_count': len(entities)
            }
            
            # Create masked document
            masked_doc = MaskedDocument(
                masked_text=masked_text,
                mapping_id=mapping_id,
                original_length=len(document_text),
                masked_entities=entities,
                processing_timestamp=datetime.now(),
                expires_at=expires_at
            )
            
            # Log audit event
            self._log_audit_event('DOCUMENT_MASKED', {
                'mapping_id': mapping_id,
                'entity_count': len(entities),
                'original_length': len(document_text),
                'masked_length': len(masked_text),
                'expires_at': expires_at.isoformat(),
                'summary': f'Masked {len(entities)} entities'
            })
            
            logger.info(f"✅ Document masked successfully: {len(entities)} entities, mapping_id: {mapping_id}")
            return masked_doc
            
        except Exception as e:
            logger.error(f"❌ Document masking failed: {e}")
            self._log_audit_event('MASKING_ERROR', {
                'error': str(e),
                'summary': 'Document masking failed'
            })
            raise Exception(f"Document masking failed: {e}")
    
    async def unmask_results(self, masked_results: str, mapping_id: str) -> str:
        """
        Restore original information in analysis results
        
        Args:
            masked_results: Results containing masked tokens
            mapping_id: ID to retrieve original mappings
            
        Returns:
            Results with original sensitive information restored
        """
        try:
            # Check if mapping exists and is not expired
            if mapping_id not in self.mapping_store:
                logger.warning(f"⚠️ Mapping {mapping_id} not found")
                return masked_results
            
            mapping_entry = self.mapping_store[mapping_id]
            
            # Check expiration
            if datetime.now() > mapping_entry['expires_at']:
                logger.warning(f"⚠️ Mapping {mapping_id} has expired")
                del self.mapping_store[mapping_id]
                return masked_results
            
            # Decrypt mapping data
            try:
                decrypted_data = self.cipher_suite.decrypt(mapping_entry['encrypted_data'])
                mapping_data = eval(decrypted_data.decode())  # Note: In production, use json.loads
            except Exception as e:
                logger.error(f"❌ Failed to decrypt mapping {mapping_id}: {e}")
                return masked_results
            
            # Restore original text
            unmasked_results = masked_results
            
            for entity_data in mapping_data['entities']:
                masked_token = entity_data['masked_token']
                original_text = entity_data['original_text']
                
                # Replace all occurrences of masked token with original text
                unmasked_results = unmasked_results.replace(masked_token, original_text)
            
            # Log audit event
            self._log_audit_event('RESULTS_UNMASKED', {
                'mapping_id': mapping_id,
                'entity_count': len(mapping_data['entities']),
                'summary': f'Unmasked {len(mapping_data["entities"])} entities'
            })
            
            logger.info(f"✅ Results unmasked successfully: {mapping_id}")
            return unmasked_results
            
        except Exception as e:
            logger.error(f"❌ Results unmasking failed: {e}")
            self._log_audit_event('UNMASKING_ERROR', {
                'mapping_id': mapping_id,
                'error': str(e),
                'summary': 'Results unmasking failed'
            })
            return masked_results  # Return masked results if unmasking fails
    
    def validate_privacy_compliance(self, text: str) -> PrivacyValidationResult:
        """
        Validate that text doesn't contain sensitive information
        
        Args:
            text: Text to validate
            
        Returns:
            PrivacyValidationResult with compliance status
        """
        violations = []
        risk_score = 0.0
        recommendations = []
        
        try:
            # Detect any remaining sensitive entities
            spacy_entities = self.detect_entities_with_spacy(text)
            regex_entities = self.detect_entities_with_regex(text)
            all_entities = self._merge_and_deduplicate_entities(spacy_entities, regex_entities)
            
            # Check for violations
            for entity in all_entities:
                violation = f"{entity.entity_type.value}: '{entity.original_text}' (confidence: {entity.confidence:.2f})"
                violations.append(violation)
                
                # Calculate risk score based on entity type and confidence
                entity_risk = {
                    EntityType.SSN: 1.0,
                    EntityType.CREDIT_CARD: 0.9,
                    EntityType.EMAIL: 0.7,
                    EntityType.PHONE: 0.6,
                    EntityType.PERSON: 0.5,
                    EntityType.ADDRESS: 0.6,
                    EntityType.FINANCIAL: 0.4,
                    EntityType.LEGAL_ENTITY: 0.3,
                    EntityType.DATE: 0.2
                }.get(entity.entity_type, 0.3)
                
                risk_score += entity_risk * entity.confidence
            
            # Normalize risk score
            risk_score = min(risk_score, 1.0)
            
            # Generate recommendations
            if violations:
                recommendations.append("Remove or mask detected sensitive information before processing")
                recommendations.append("Implement additional data sanitization steps")
                recommendations.append("Review data handling procedures for GDPR compliance")
            
            is_valid = len(violations) == 0
            
            # Log validation
            self._log_audit_event('PRIVACY_VALIDATION', {
                'is_valid': is_valid,
                'violation_count': len(violations),
                'risk_score': risk_score,
                'summary': f'Privacy validation: {"PASS" if is_valid else "FAIL"}'
            })
            
            return PrivacyValidationResult(
                is_valid=is_valid,
                violations=violations,
                risk_score=risk_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ Privacy validation failed: {e}")
            return PrivacyValidationResult(
                is_valid=False,
                violations=[f"Validation error: {str(e)}"],
                risk_score=1.0,
                recommendations=["Manual review required due to validation error"]
            )
    
    def cleanup_expired_mappings(self):
        """Clean up expired mappings for privacy compliance"""
        current_time = datetime.now()
        expired_mappings = []
        
        for mapping_id, mapping_entry in self.mapping_store.items():
            if current_time > mapping_entry['expires_at']:
                expired_mappings.append(mapping_id)
        
        for mapping_id in expired_mappings:
            del self.mapping_store[mapping_id]
            logger.info(f"🗑️ Cleaned up expired mapping: {mapping_id}")
        
        if expired_mappings:
            self._log_audit_event('CLEANUP_EXPIRED_MAPPINGS', {
                'cleaned_count': len(expired_mappings),
                'summary': f'Cleaned up {len(expired_mappings)} expired mappings'
            })
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get audit log for compliance reporting"""
        return self.audit_log[-limit:]
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """Get statistics about current mappings"""
        current_time = datetime.now()
        active_mappings = 0
        expired_mappings = 0
        total_entities = 0
        
        for mapping_entry in self.mapping_store.values():
            if current_time <= mapping_entry['expires_at']:
                active_mappings += 1
                total_entities += mapping_entry['entity_count']
            else:
                expired_mappings += 1
        
        return {
            'active_mappings': active_mappings,
            'expired_mappings': expired_mappings,
            'total_entities_protected': total_entities,
            'audit_log_entries': len(self.audit_log)
        }

# Global instance
data_masking_service = DataMaskingService()