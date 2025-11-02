"""
Caching service for FastAPI backend
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional
import json

from models.document_models import DocumentAnalysisResponse

logger = logging.getLogger(__name__)


class CacheService:
    """In-memory caching service to replace Neo4j functionality"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.translation_cache = {}
        self.pattern_storage = {}
        self.cache_expiry = 3600  # 1 hour
        
    def get_cache_key(self, text: str, analysis_type: str = "analysis") -> str:
        """Generate cache key for analysis results"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{analysis_type}:{text_hash}"
    
    async def get_cached_analysis(self, cache_key: str) -> Optional[DocumentAnalysisResponse]:
        """Get analysis result from cache if not expired"""
        if cache_key in self.analysis_cache:
            cached_data = self.analysis_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_expiry:
                logger.info(f"Cache hit for key: {cache_key}")
                return cached_data['data']
            else:
                # Remove expired cache entry
                del self.analysis_cache[cache_key]
                logger.info(f"Cache expired for key: {cache_key}")
        return None
    
    async def store_analysis(self, cache_key: str, data: DocumentAnalysisResponse) -> None:
        """Store analysis result in cache"""
        self.analysis_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Stored in cache: {cache_key}")
    
    async def get_cached_translation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get translation result from cache if not expired"""
        if cache_key in self.translation_cache:
            cached_data = self.translation_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_expiry:
                logger.info(f"Translation cache hit for key: {cache_key}")
                return cached_data['data']
            else:
                del self.translation_cache[cache_key]
                logger.info(f"Translation cache expired for key: {cache_key}")
        return None
    
    async def store_translation(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store translation result in cache"""
        self.translation_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Stored translation in cache: {cache_key}")
    
    async def learn_from_analysis(self, analysis: DocumentAnalysisResponse) -> None:
        """Store patterns for future learning (replaces Neo4j)"""
        try:
            # Extract patterns from analysis for future use
            pattern_key = f"pattern_{analysis.overall_risk.level}_{len(analysis.clause_assessments)}"
            
            pattern_data = {
                'risk_level': analysis.overall_risk.level,
                'risk_score': analysis.overall_risk.score,
                'clause_count': len(analysis.clause_assessments),
                'risk_categories': analysis.overall_risk.risk_categories,
                'timestamp': time.time()
            }
            
            self.pattern_storage[pattern_key] = pattern_data
            logger.info(f"Stored learning pattern: {pattern_key}")
            
        except Exception as e:
            logger.warning(f"Failed to store learning pattern: {e}")
    
    async def find_similar_patterns(self, risk_level: str, clause_count: int) -> list:
        """Find similar patterns using stored data (replaces Neo4j queries)"""
        try:
            similar_patterns = []
            
            for key, pattern in self.pattern_storage.items():
                if (pattern['risk_level'] == risk_level and 
                    abs(pattern['clause_count'] - clause_count) <= 2):
                    similar_patterns.append(pattern)
            
            # Sort by timestamp (most recent first)
            similar_patterns.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return similar_patterns[:5]  # Return top 5 similar patterns
            
        except Exception as e:
            logger.warning(f"Failed to find similar patterns: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'analysis_cache_size': len(self.analysis_cache),
            'translation_cache_size': len(self.translation_cache),
            'pattern_storage_size': len(self.pattern_storage),
            'cache_expiry_seconds': self.cache_expiry
        }
    
    def clear_expired_cache(self) -> None:
        """Clear expired cache entries"""
        current_time = time.time()
        
        # Clear expired analysis cache
        expired_keys = [
            key for key, data in self.analysis_cache.items()
            if current_time - data['timestamp'] > self.cache_expiry
        ]
        for key in expired_keys:
            del self.analysis_cache[key]
        
        # Clear expired translation cache
        expired_keys = [
            key for key, data in self.translation_cache.items()
            if current_time - data['timestamp'] > self.cache_expiry
        ]
        for key in expired_keys:
            del self.translation_cache[key]
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")