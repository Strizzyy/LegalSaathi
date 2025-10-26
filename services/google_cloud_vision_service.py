"""
Google Cloud Vision API Service for Enhanced Image Text Extraction
Uses Vision API to extract text from JPEG/PNG images with OCR optimization for legal documents
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from google.cloud import vision
from google.api_core.client_options import ClientOptions
from PIL import Image, ImageEnhance, ImageFilter
import io
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GoogleCloudVisionService:
    """
    Google Cloud Vision API service for legal document image processing
    Extracts text from images with OCR confidence scoring and legal document optimization
    """
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # Set up authentication
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-cloud-credentials.json')
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        else:
            logger.warning(f"Google Cloud credentials not found at {credentials_path}")
        
        # Initialize rate limiting and cost monitoring regardless of enabled status
        self.rate_limiter = VisionAPIRateLimiter()
        self.cost_monitor = VisionAPICostMonitor()
        self.response_cache = VisionAPICache()
        
        if not self.project_id:
            logger.warning("Google Cloud Vision API not configured - missing project ID")
            self.enabled = False
            return
            
        try:
            # Initialize Vision API client
            self.client = vision.ImageAnnotatorClient()
            
            # OCR confidence threshold for legal documents
            self.min_confidence_threshold = 0.7
            
            # Supported image formats
            self.supported_formats = {'JPEG', 'PNG', 'WEBP', 'BMP', 'GIF'}
            self.max_file_size = 20 * 1024 * 1024  # 20MB
            self.max_resolution = (4096, 4096)  # 4K max resolution
            
            self.enabled = True
            logger.info("Google Cloud Vision API service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vision API: {e}")
            logger.warning("Vision API will use fallback processing")
            self.enabled = False
    
    async def detect_text_in_image(
        self, 
        image_content: bytes, 
        user_id: str,
        image_format: str = "JPEG",
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Detect and extract text from image using Vision API with legal document optimization
        
        Args:
            image_content: Raw image bytes
            user_id: User ID for rate limiting
            image_format: Image format (JPEG, PNG, WEBP)
            preprocess: Whether to apply image preprocessing for legal documents
            
        Returns:
            Dict containing extracted text, confidence scores, and bounding boxes
        """
        if not self.enabled:
            logger.info("Vision API not available, using fallback processing")
            return self._fallback_image_processing(image_content)
        
        try:
            # Check rate limits
            if not self.rate_limiter.check_rate_limit(user_id):
                raise Exception("Rate limit exceeded for Vision API (max 100 requests per user per day)")
            
            # Check cost limits
            if not self.cost_monitor.check_cost_limit(user_id):
                raise Exception("Daily cost limit exceeded for Vision API")
            
            # Validate image
            validation_result = self._validate_image(image_content, image_format)
            if not validation_result['valid']:
                raise Exception(validation_result['error'])
            
            # Check cache first
            cache_key = self._generate_cache_key(image_content, preprocess)
            cached_result = self.response_cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached Vision API result")
                return cached_result
            
            # Preprocess image for legal document optimization
            if preprocess:
                processed_image = self._preprocess_legal_document_image(image_content)
            else:
                processed_image = image_content
            
            logger.info(f"Processing image with Vision API - format: {image_format}, size: {len(processed_image)} bytes")
            
            # Create Vision API image object
            image = vision.Image(content=processed_image)
            
            # Perform text detection with document-specific features
            features = [
                vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.client.annotate_image(request=request)
            
            # Check for errors
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract and process results
            extracted_data = self._process_vision_response(response)
            
            # Update rate limiting and cost monitoring
            self.rate_limiter.record_request(user_id)
            self.cost_monitor.record_request(user_id)
            
            # Cache the result
            self.response_cache.set(cache_key, extracted_data)
            
            logger.info(f"Vision API processing successful - extracted {len(extracted_data['text'])} characters")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Vision API processing failed: {e}")
            logger.info("Falling back to basic image processing")
            return self._fallback_image_processing(image_content)
    
    def _validate_image(self, image_content: bytes, image_format: str) -> Dict[str, Any]:
        """Validate image format, size, and resolution"""
        try:
            # Check file size
            if len(image_content) > self.max_file_size:
                return {
                    'valid': False,
                    'error': f"Image size exceeds maximum limit of {self.max_file_size // (1024*1024)}MB"
                }
            
            # Check format
            if image_format.upper() not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f"Unsupported image format: {image_format}. Supported: {', '.join(self.supported_formats)}"
                }
            
            # Check image validity and resolution
            try:
                image = Image.open(io.BytesIO(image_content))
                width, height = image.size
                
                if width > self.max_resolution[0] or height > self.max_resolution[1]:
                    return {
                        'valid': False,
                        'error': f"Image resolution {width}x{height} exceeds maximum {self.max_resolution[0]}x{self.max_resolution[1]}"
                    }
                
                # Check if image has content
                if width < 100 or height < 100:
                    return {
                        'valid': False,
                        'error': "Image too small for meaningful text extraction (minimum 100x100 pixels)"
                    }
                
                return {'valid': True, 'width': width, 'height': height}
                
            except Exception as e:
                return {
                    'valid': False,
                    'error': f"Invalid or corrupted image file: {str(e)}"
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f"Image validation failed: {str(e)}"
            }
    
    def _preprocess_legal_document_image(self, image_content: bytes) -> bytes:
        """
        Preprocess image for optimal legal document text extraction
        Applies contrast enhancement, rotation detection, and noise reduction
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply legal document optimizations
            
            # 1. Contrast enhancement for better text visibility
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)  # Increase contrast by 20%
            
            # 2. Sharpness enhancement for clearer text
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)  # Increase sharpness by 10%
            
            # 3. Noise reduction using median filter
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # 4. Auto-rotation detection (basic implementation)
            # This is a simplified version - in production, you might want more sophisticated rotation detection
            image = self._detect_and_correct_rotation(image)
            
            # Convert back to bytes
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=95, optimize=True)
            processed_content = output_buffer.getvalue()
            
            logger.info(f"Image preprocessing completed - original: {len(image_content)} bytes, processed: {len(processed_content)} bytes")
            return processed_content
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image_content
    
    def _detect_and_correct_rotation(self, image: Image.Image) -> Image.Image:
        """
        Basic rotation detection and correction for legal documents
        This is a simplified implementation - more sophisticated methods could be used
        """
        try:
            # For now, we'll skip rotation detection as it requires more complex algorithms
            # In a production environment, you might use libraries like OpenCV for better rotation detection
            return image
        except Exception as e:
            logger.warning(f"Rotation detection failed: {e}")
            return image
    
    def _process_vision_response(self, response) -> Dict[str, Any]:
        """Process Vision API response and extract structured data"""
        try:
            # Extract full document text
            full_text = ""
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
            
            # Extract text annotations with confidence scores
            text_annotations = []
            bounding_boxes = []
            confidence_scores = []
            
            for annotation in response.text_annotations:
                # Skip the first annotation as it's the full text
                if annotation == response.text_annotations[0]:
                    continue
                
                text_annotations.append({
                    'text': annotation.description,
                    'confidence': getattr(annotation, 'confidence', 0.0),
                    'bounding_poly': self._extract_bounding_poly(annotation.bounding_poly)
                })
                
                # Extract bounding box coordinates
                if annotation.bounding_poly:
                    vertices = [(vertex.x, vertex.y) for vertex in annotation.bounding_poly.vertices]
                    bounding_boxes.append(vertices)
                
                # Collect confidence scores
                confidence = getattr(annotation, 'confidence', 0.0)
                confidence_scores.append(confidence)
            
            # Calculate overall confidence metrics
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            high_confidence_ratio = len([c for c in confidence_scores if c > self.min_confidence_threshold]) / len(confidence_scores) if confidence_scores else 0.0
            
            # Filter text based on confidence threshold
            high_confidence_text = self._filter_by_confidence(text_annotations, self.min_confidence_threshold)
            
            # Identify potential legal document sections
            legal_sections = self._identify_legal_sections(full_text)
            
            return {
                'success': True,
                'text': full_text,
                'high_confidence_text': high_confidence_text,
                'text_annotations': text_annotations[:50],  # Limit for response size
                'bounding_boxes': bounding_boxes[:50],
                'confidence_scores': {
                    'average_confidence': avg_confidence,
                    'high_confidence_ratio': high_confidence_ratio,
                    'min_confidence_threshold': self.min_confidence_threshold,
                    'total_text_blocks': len(text_annotations),
                    'high_confidence_blocks': len([c for c in confidence_scores if c > self.min_confidence_threshold])
                },
                'legal_sections': legal_sections,
                'processing_metadata': {
                    'api_used': 'Google Cloud Vision API',
                    'processing_time': 0.0,  # Will be calculated by caller
                    'image_preprocessing_applied': True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process Vision API response: {e}")
            return {
                'success': False,
                'text': "",
                'error': f"Failed to process Vision API response: {str(e)}"
            }
    
    def _extract_bounding_poly(self, bounding_poly) -> List[Tuple[int, int]]:
        """Extract bounding polygon coordinates"""
        if not bounding_poly or not bounding_poly.vertices:
            return []
        
        return [(vertex.x, vertex.y) for vertex in bounding_poly.vertices]
    
    def _filter_by_confidence(self, text_annotations: List[Dict], min_confidence: float) -> str:
        """Filter text annotations by confidence threshold"""
        high_confidence_texts = [
            annotation['text'] 
            for annotation in text_annotations 
            if annotation['confidence'] >= min_confidence
        ]
        
        return ' '.join(high_confidence_texts)
    
    def _identify_legal_sections(self, text: str) -> List[Dict[str, Any]]:
        """Identify potential legal document sections in extracted text"""
        legal_patterns = {
            'header': ['agreement', 'contract', 'terms and conditions', 'legal notice'],
            'parties': ['party', 'parties', 'between', 'whereas'],
            'terms': ['terms', 'conditions', 'obligations', 'responsibilities'],
            'liability': ['liability', 'damages', 'indemnification', 'limitation'],
            'termination': ['termination', 'expiration', 'end', 'cancel'],
            'governing_law': ['governing law', 'jurisdiction', 'applicable law'],
            'signatures': ['signature', 'signed', 'executed', 'date']
        }
        
        sections = []
        text_lower = text.lower()
        
        for section_type, keywords in legal_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Find the position and extract surrounding context
                    start_pos = text_lower.find(keyword)
                    if start_pos != -1:
                        # Extract context around the keyword (100 characters before and after)
                        context_start = max(0, start_pos - 100)
                        context_end = min(len(text), start_pos + len(keyword) + 100)
                        context = text[context_start:context_end].strip()
                        
                        sections.append({
                            'section_type': section_type,
                            'keyword': keyword,
                            'position': start_pos,
                            'context': context
                        })
                        break  # Only add one match per section type
        
        return sections
    
    def _generate_cache_key(self, image_content: bytes, preprocess: bool) -> str:
        """Generate cache key for image content"""
        content_hash = hashlib.md5(image_content).hexdigest()
        return f"vision_api_{content_hash}_{preprocess}"
    
    def _fallback_image_processing(self, image_content: bytes) -> Dict[str, Any]:
        """Fallback processing when Vision API is not available"""
        try:
            # Basic image validation
            image = Image.open(io.BytesIO(image_content))
            width, height = image.size
            
            return {
                'success': False,
                'text': "",
                'high_confidence_text': "",
                'text_annotations': [],
                'bounding_boxes': [],
                'confidence_scores': {
                    'average_confidence': 0.0,
                    'high_confidence_ratio': 0.0,
                    'min_confidence_threshold': self.min_confidence_threshold,
                    'total_text_blocks': 0,
                    'high_confidence_blocks': 0
                },
                'legal_sections': [],
                'processing_metadata': {
                    'api_used': 'Fallback (Vision API not available)',
                    'processing_time': 0.0,
                    'image_preprocessing_applied': False
                },
                'fallback_used': True,
                'error': 'Vision API not configured - image text extraction not available',
                'image_info': {
                    'width': width,
                    'height': height,
                    'size_bytes': len(image_content)
                }
            }
        except Exception as e:
            logger.error(f"Fallback image processing failed: {e}")
            return {
                'success': False,
                'text': "",
                'error': f'Image processing failed - Vision API not available and fallback failed: {str(e)}',
                'fallback_used': True
            }
    
    async def verify_credentials(self) -> bool:
        """Verify if Google Cloud Vision API credentials are valid and service is accessible"""
        if not self.enabled:
            return False
            
        if not self.project_id:
            logger.warning("Vision API not properly configured - missing project ID")
            return False
            
        try:
            # Test with a small dummy image
            test_image_content = self._create_test_image()
            
            image = vision.Image(content=test_image_content)
            features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]
            request = vision.AnnotateImageRequest(image=image, features=features)
            
            response = self.client.annotate_image(request=request)
            
            if response.error.message:
                logger.error(f"Vision API test failed: {response.error.message}")
                return False
            
            logger.info("Successfully connected to Vision API")
            return True
            
        except Exception as e:
            logger.error(f"Vision API service verification failed: {str(e)}")
            return False
    
    def _create_test_image(self) -> bytes:
        """Create a small test image for credential verification"""
        try:
            # Create a simple 100x50 white image with black text
            image = Image.new('RGB', (100, 50), color='white')
            
            # Convert to bytes
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG')
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create test image: {e}")
            # Return minimal JPEG header if PIL fails
            return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x002\x00d\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'


class VisionAPIRateLimiter:
    """Rate limiter for Vision API calls (max 100 requests per user per day)"""
    
    def __init__(self):
        self.user_requests = {}  # user_id -> {'count': int, 'reset_time': datetime}
        self.max_requests_per_day = 100
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.now()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = {
                'count': 0,
                'reset_time': now + timedelta(days=1)
            }
        
        user_data = self.user_requests[user_id]
        
        # Reset counter if day has passed
        if now >= user_data['reset_time']:
            user_data['count'] = 0
            user_data['reset_time'] = now + timedelta(days=1)
        
        return user_data['count'] < self.max_requests_per_day
    
    def record_request(self, user_id: str):
        """Record a request for rate limiting"""
        if user_id in self.user_requests:
            self.user_requests[user_id]['count'] += 1


class VisionAPICostMonitor:
    """Cost monitor for Vision API calls with daily usage limits"""
    
    def __init__(self):
        self.user_costs = {}  # user_id -> {'cost': float, 'reset_time': datetime}
        self.cost_per_request = 0.0015  # Approximate cost per Vision API request
        self.max_daily_cost = 1.50  # $1.50 per user per day
    
    def check_cost_limit(self, user_id: str) -> bool:
        """Check if user has exceeded daily cost limit"""
        now = datetime.now()
        
        if user_id not in self.user_costs:
            self.user_costs[user_id] = {
                'cost': 0.0,
                'reset_time': now + timedelta(days=1)
            }
        
        user_data = self.user_costs[user_id]
        
        # Reset cost if day has passed
        if now >= user_data['reset_time']:
            user_data['cost'] = 0.0
            user_data['reset_time'] = now + timedelta(days=1)
        
        return user_data['cost'] < self.max_daily_cost
    
    def record_request(self, user_id: str):
        """Record a request for cost monitoring"""
        if user_id in self.user_costs:
            self.user_costs[user_id]['cost'] += self.cost_per_request


class VisionAPICache:
    """Cache for Vision API responses (1 hour TTL)"""
    
    def __init__(self):
        self.cache = {}  # cache_key -> {'data': dict, 'expiry': datetime}
        self.ttl_hours = 1
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired"""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() < cache_entry['expiry']:
                return cache_entry['data']
            else:
                # Remove expired entry
                del self.cache[cache_key]
        return None
    
    def set(self, cache_key: str, data: Dict[str, Any]):
        """Cache result with TTL"""
        self.cache[cache_key] = {
            'data': data,
            'expiry': datetime.now() + timedelta(hours=self.ttl_hours)
        }
    
    def clear_expired(self):
        """Clear expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if now >= value['expiry']
        ]
        for key in expired_keys:
            del self.cache[key]


# Global instance
vision_service = GoogleCloudVisionService()