"""
Lightweight RAG Service for Cloud Run Deployment
Provides basic retrieval functionality without heavy ML dependencies
"""

import os
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import hashlib
import re

logger = logging.getLogger(__name__)

class LightweightRAGService:
    """Lightweight RAG service using keyword-based retrieval"""
    
    def __init__(self):
        self.legal_knowledge_base = {}
        self.conversation_memory = []
        self.feedback_scores = {}
        self.document_chunks = []
        self.chunk_metadata = []
        
        # Configuration
        self.max_chunks_per_retrieval = 5
        self.final_top_k = 3
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
        logger.info("✅ Lightweight RAG service initialized")
    
    def _initialize_knowledge_base(self):
        """Initialize basic legal knowledge base"""
        self.legal_knowledge_base = {
            'contract_fundamentals': {
                'keywords': ['agreement', 'contract', 'party', 'parties', 'obligation', 'consideration', 'mutual'],
                'guidance': 'A contract requires offer, acceptance, consideration, and mutual assent. All parties must have legal capacity to enter into the agreement.',
                'risk_factors': ['unclear terms', 'missing signatures', 'lack of consideration']
            },
            'termination_clauses': {
                'keywords': ['terminate', 'termination', 'end', 'cancel', 'cancellation', 'breach', 'default'],
                'guidance': 'Termination clauses should specify conditions, notice periods, and consequences. Consider both termination for cause and convenience.',
                'risk_factors': ['immediate termination', 'no cure period', 'unclear termination conditions']
            },
            'liability_limitation': {
                'keywords': ['liability', 'liable', 'damages', 'limitation', 'cap', 'indemnify', 'indemnification'],
                'guidance': 'Liability limitations should be reasonable and enforceable. Consider caps on damages and exclusions for certain types of harm.',
                'risk_factors': ['unlimited liability', 'broad indemnification', 'no damage caps']
            },
            'payment_terms': {
                'keywords': ['payment', 'pay', 'fee', 'compensation', 'invoice', 'due', 'penalty', 'interest'],
                'guidance': 'Payment terms should specify amounts, due dates, late fees, and acceptable payment methods. Include dispute resolution procedures.',
                'risk_factors': ['immediate payment', 'excessive late fees', 'unclear payment schedule']
            },
            'confidentiality': {
                'keywords': ['confidential', 'non-disclosure', 'nda', 'proprietary', 'trade secret', 'information'],
                'guidance': 'Confidentiality clauses should define what information is protected, duration of protection, and permitted disclosures.',
                'risk_factors': ['overly broad scope', 'indefinite duration', 'no exceptions for required disclosures']
            },
            'intellectual_property': {
                'keywords': ['intellectual property', 'ip', 'copyright', 'trademark', 'patent', 'ownership', 'license'],
                'guidance': 'IP clauses should clearly define ownership, licensing rights, and protection of existing and newly created intellectual property.',
                'risk_factors': ['unclear ownership', 'broad IP assignments', 'no protection for existing IP']
            },
            'dispute_resolution': {
                'keywords': ['dispute', 'arbitration', 'mediation', 'litigation', 'court', 'jurisdiction', 'governing law'],
                'guidance': 'Dispute resolution clauses should specify the process, jurisdiction, and applicable law. Consider cost-effective alternatives to litigation.',
                'risk_factors': ['mandatory arbitration', 'inconvenient jurisdiction', 'unclear governing law']
            },
            'force_majeure': {
                'keywords': ['force majeure', 'act of god', 'unforeseeable', 'beyond control', 'natural disaster'],
                'guidance': 'Force majeure clauses excuse performance during extraordinary circumstances. Define covered events and required notice procedures.',
                'risk_factors': ['overly narrow scope', 'no notice requirements', 'unclear relief provisions']
            },
            'warranties_representations': {
                'keywords': ['warranty', 'warrant', 'represent', 'representation', 'guarantee', 'assure'],
                'guidance': 'Warranties and representations should be specific, accurate, and include appropriate disclaimers for excluded matters.',
                'risk_factors': ['overly broad warranties', 'no disclaimers', 'impossible to fulfill representations']
            },
            'compliance_regulatory': {
                'keywords': ['comply', 'compliance', 'regulation', 'law', 'legal', 'regulatory', 'statute'],
                'guidance': 'Compliance clauses should address applicable laws, regulatory requirements, and consequences of non-compliance.',
                'risk_factors': ['unclear compliance obligations', 'no regulatory updates', 'broad compliance warranties']
            }
        }
    
    async def get_enhanced_insights(self, query: str, document_context: str = "", 
                                  conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Get enhanced insights using lightweight retrieval"""
        try:
            start_time = time.time()
            
            # Retrieve relevant knowledge
            retrieved_knowledge = await self._lightweight_retrieve(query, document_context)
            
            # Generate contextual response
            response = self._generate_contextual_response(query, retrieved_knowledge, document_context)
            
            # Add to conversation memory
            if conversation_history:
                self.conversation_memory.extend(conversation_history[-5:])  # Keep last 5 exchanges
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'enhanced_response': response,
                'retrieved_knowledge': retrieved_knowledge,
                'confidence_score': self._calculate_confidence(query, retrieved_knowledge),
                'processing_time': processing_time,
                'method_used': 'lightweight_rag'
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced insights generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'enhanced_response': "Unable to generate enhanced insights at this time.",
                'retrieved_knowledge': [],
                'confidence_score': 0.0,
                'processing_time': 0.0,
                'method_used': 'error'
            }
    
    async def _lightweight_retrieve(self, query: str, context: str = "") -> List[Dict[str, Any]]:
        """Lightweight retrieval using keyword matching"""
        query_lower = query.lower()
        context_lower = context.lower() if context else ""
        combined_text = f"{query_lower} {context_lower}"
        
        results = []
        
        # Score each knowledge category
        for category, knowledge in self.legal_knowledge_base.items():
            relevance_score = 0
            matched_keywords = []
            
            # Check keyword matches
            for keyword in knowledge['keywords']:
                if keyword in combined_text:
                    relevance_score += 1
                    matched_keywords.append(keyword)
            
            # Boost score for multiple matches
            if len(matched_keywords) > 1:
                relevance_score *= 1.5
            
            # Add partial matches (stemming-like)
            for keyword in knowledge['keywords']:
                if len(keyword) > 4:  # Only for longer keywords
                    stem = keyword[:4]
                    if stem in combined_text and keyword not in matched_keywords:
                        relevance_score += 0.5
                        matched_keywords.append(f"{keyword}*")
            
            if relevance_score > 0:
                results.append({
                    'category': category,
                    'content': knowledge['guidance'],
                    'risk_factors': knowledge['risk_factors'],
                    'matched_keywords': matched_keywords,
                    'relevance_score': relevance_score,
                    'metadata': {
                        'category': category,
                        'keyword_count': len(matched_keywords),
                        'total_keywords': len(knowledge['keywords'])
                    }
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top results
        return results[:self.final_top_k]
    
    def _generate_contextual_response(self, query: str, retrieved_knowledge: List[Dict], 
                                    document_context: str = "") -> str:
        """Generate contextual response based on retrieved knowledge"""
        if not retrieved_knowledge:
            return "For specific legal questions, please consult with a qualified legal professional who can provide advice tailored to your situation."
        
        # Build response from retrieved knowledge
        response_parts = []
        
        # Add main guidance
        top_result = retrieved_knowledge[0]
        response_parts.append(f"**{top_result['category'].replace('_', ' ').title()} Guidance:**")
        response_parts.append(top_result['content'])
        
        # Add risk factors if available
        if top_result.get('risk_factors'):
            response_parts.append("\n**Key Risk Factors to Consider:**")
            for risk in top_result['risk_factors'][:3]:  # Top 3 risks
                response_parts.append(f"• {risk}")
        
        # Add additional relevant insights
        if len(retrieved_knowledge) > 1:
            response_parts.append("\n**Additional Considerations:**")
            for result in retrieved_knowledge[1:]:
                if result['relevance_score'] > 0.5:  # Only high-relevance additional insights
                    response_parts.append(f"• {result['category'].replace('_', ' ').title()}: {result['content'][:100]}...")
        
        # Add matched keywords for transparency
        all_keywords = []
        for result in retrieved_knowledge:
            all_keywords.extend(result['matched_keywords'])
        
        if all_keywords:
            unique_keywords = list(set(all_keywords))[:5]  # Top 5 unique keywords
            response_parts.append(f"\n*Based on analysis of: {', '.join(unique_keywords)}*")
        
        return "\n".join(response_parts)
    
    def _calculate_confidence(self, query: str, retrieved_knowledge: List[Dict]) -> float:
        """Calculate confidence score for the response"""
        if not retrieved_knowledge:
            return 0.1
        
        # Base confidence on top result's relevance
        top_score = retrieved_knowledge[0]['relevance_score']
        
        # Normalize score (assuming max possible score is around 10)
        normalized_score = min(top_score / 10.0, 1.0)
        
        # Boost confidence if multiple relevant results
        if len(retrieved_knowledge) > 1:
            normalized_score *= 1.2
        
        # Boost confidence for longer queries (more context)
        if len(query.split()) > 5:
            normalized_score *= 1.1
        
        return min(normalized_score, 0.95)  # Cap at 95%
    
    async def add_document_chunks(self, chunks: List[str], metadata: List[Dict] = None):
        """Add document chunks for retrieval (lightweight implementation)"""
        try:
            self.document_chunks.extend(chunks)
            if metadata:
                self.chunk_metadata.extend(metadata)
            else:
                # Generate basic metadata
                for i, chunk in enumerate(chunks):
                    self.chunk_metadata.append({
                        'chunk_id': len(self.document_chunks) - len(chunks) + i,
                        'length': len(chunk),
                        'word_count': len(chunk.split())
                    })
            
            logger.info(f"✅ Added {len(chunks)} document chunks to lightweight RAG")
            
        except Exception as e:
            logger.error(f"❌ Failed to add document chunks: {e}")
    
    async def search_document_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search document chunks using keyword matching"""
        if not self.document_chunks:
            return []
        
        query_lower = query.lower()
        results = []
        
        for i, chunk in enumerate(self.document_chunks):
            chunk_lower = chunk.lower()
            
            # Simple keyword matching score
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if word in chunk_lower)
            
            if matches > 0:
                score = matches / len(query_words)
                
                results.append({
                    'chunk_id': i,
                    'content': chunk,
                    'score': score,
                    'metadata': self.chunk_metadata[i] if i < len(self.chunk_metadata) else {}
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_conversation_context(self, limit: int = 5) -> List[Dict]:
        """Get recent conversation context"""
        return self.conversation_memory[-limit:] if self.conversation_memory else []
    
    def add_feedback(self, query: str, response: str, rating: float, feedback: str = ""):
        """Add user feedback for improvement"""
        feedback_id = hashlib.md5(f"{query}{response}".encode()).hexdigest()[:8]
        
        self.feedback_scores[feedback_id] = {
            'query': query,
            'response': response,
            'rating': rating,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📝 Added feedback: {rating}/5.0 for query about {query[:50]}...")
    
    async def build_knowledge_base(self, document_chunks: List[str], metadata: List[Dict] = None) -> Dict[str, Any]:
        """Build knowledge base from document chunks (lightweight implementation)"""
        try:
            # Add chunks to our simple storage
            await self.add_document_chunks(document_chunks, metadata)
            
            # Extract key terms from chunks for better retrieval
            key_terms = set()
            for chunk in document_chunks:
                # Simple term extraction
                words = chunk.lower().split()
                legal_terms = [word for word in words if len(word) > 4 and any(
                    legal_word in word for legal_word in ['contract', 'agreement', 'clause', 'term', 'condition', 'liability', 'obligation']
                )]
                key_terms.update(legal_terms[:5])  # Top 5 terms per chunk
            
            logger.info(f"✅ Built lightweight knowledge base with {len(document_chunks)} chunks and {len(key_terms)} key terms")
            
            return {
                'success': True,
                'chunks_processed': len(document_chunks),
                'key_terms_extracted': len(key_terms),
                'method': 'lightweight_keyword_extraction'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to build knowledge base: {e}")
            return {
                'success': False,
                'error': str(e),
                'chunks_processed': 0,
                'key_terms_extracted': 0
            }
    
    async def retrieve_and_rerank(self, query: str, top_k: int = 5, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve and rerank relevant information (lightweight implementation)"""
        try:
            # First, get enhanced insights
            insights = await self.get_enhanced_insights(query, context=context)
            
            if not insights.get('success', False):
                return []
            
            # Convert insights to retrieval format
            retrieved_knowledge = insights.get('retrieved_knowledge', [])
            
            # Simple reranking based on relevance score
            reranked_results = []
            for i, knowledge in enumerate(retrieved_knowledge[:top_k]):
                reranked_results.append({
                    'content': knowledge.get('content', ''),
                    'metadata': knowledge.get('metadata', {}),
                    'relevance_score': knowledge.get('relevance_score', 0.5),
                    'rerank_score': knowledge.get('relevance_score', 0.5) * (1.0 - i * 0.1),  # Slight penalty for lower positions
                    'source': 'lightweight_rag',
                    'rank': i + 1
                })
            
            # Sort by rerank score
            reranked_results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            logger.info(f"✅ Retrieved and reranked {len(reranked_results)} results for query: {query[:50]}...")
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"❌ Retrieve and rerank failed: {e}")
            return []

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        avg_rating = 0.0
        if self.feedback_scores:
            ratings = [f['rating'] for f in self.feedback_scores.values()]
            avg_rating = sum(ratings) / len(ratings)
        
        return {
            'service_type': 'lightweight_rag',
            'knowledge_categories': len(self.legal_knowledge_base),
            'document_chunks': len(self.document_chunks),
            'conversation_memory': len(self.conversation_memory),
            'feedback_entries': len(self.feedback_scores),
            'average_rating': avg_rating,
            'capabilities': [
                'keyword_based_retrieval',
                'legal_knowledge_base',
                'contextual_responses',
                'document_chunk_search',
                'conversation_memory',
                'build_knowledge_base',
                'retrieve_and_rerank'
            ]
        }

# Global instance
lightweight_rag_service = LightweightRAGService()

# Compatibility alias for existing code
advanced_rag_service = lightweight_rag_service