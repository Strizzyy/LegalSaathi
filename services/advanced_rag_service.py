"""
Advanced RAG Service with Multi-Stage Retrieval and Comprehensive Reranking
Implements dense vector search + sparse BM25 + cross-encoder reranking
"""

import os
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import warnings
# Suppress FAISS AVX warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import faiss

logger = logging.getLogger(__name__)

class AdvancedRAGService:
    """Advanced RAG service with multi-stage retrieval and comprehensive reranking"""
    
    def __init__(self):
        self.embedding_model = None
        self.cross_encoder = None
        self.vector_store = None
        self.bm25_retriever = None
        self.document_chunks = []
        self.chunk_metadata = []
        self.legal_knowledge_base = {}
        self.conversation_memory = []
        self.feedback_scores = {}
        
        # Configuration - Ultra-optimized for speed
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        self.max_chunks_per_retrieval = 10  # Further reduced for speed
        self.reranking_top_k = 5  # Further reduced for speed
        self.final_top_k = 3  # Further reduced for speed
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize embedding and reranking models"""
        try:
            logger.info("🧠 Initializing Advanced RAG models...")
            
            # Initialize sentence transformer for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence transformer loaded")
            
            # Initialize cross-encoder for reranking (using correct model name)
            try:
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("✅ Cross-encoder loaded")
            except Exception as e:
                logger.warning(f"Cross-encoder loading failed: {e}, using fallback scoring")
                self.cross_encoder = None
            
            # Initialize FAISS vector store
            self.vector_store = faiss.IndexFlatIP(self.embedding_dim)
            logger.info("✅ FAISS vector store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG models: {e}")
            raise
    
    async def build_knowledge_base(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build vector store and BM25 index from legal documents"""
        logger.info(f"🏗️ Building knowledge base from {len(documents)} documents...")
        
        try:
            # Clear existing data
            self.document_chunks = []
            self.chunk_metadata = []
            
            # Process documents with hierarchical chunking
            all_chunks = []
            all_metadata = []
            
            for doc_idx, document in enumerate(documents):
                chunks, metadata = await self._hierarchical_chunk_document(document, doc_idx)
                all_chunks.extend(chunks)
                all_metadata.extend(metadata)
            
            self.document_chunks = all_chunks
            self.chunk_metadata = all_metadata
            
            logger.info(f"📄 Created {len(all_chunks)} chunks from documents")
            
            # Build dense vector embeddings
            await self._build_vector_store(all_chunks)
            
            # Build sparse BM25 index
            await self._build_bm25_index(all_chunks)
            
            # Build legal knowledge graph
            await self._build_legal_knowledge_graph(documents)
            
            logger.info("✅ Knowledge base built successfully")
            
            return {
                'total_documents': len(documents),
                'total_chunks': len(all_chunks),
                'vector_store_size': self.vector_store.ntotal,
                'bm25_corpus_size': len(all_chunks) if self.bm25_retriever else 0,
                'knowledge_graph_entities': len(self.legal_knowledge_base)
            }
            
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}")
            raise
    
    async def _hierarchical_chunk_document(self, document: Dict[str, Any], doc_idx: int) -> Tuple[List[str], List[Dict]]:
        """Hierarchical chunking with legal structure awareness"""
        chunks = []
        metadata = []
        
        doc_text = document.get('text', '')
        doc_type = document.get('type', 'general_contract')
        doc_id = document.get('id', f'doc_{doc_idx}')
        
        # Semantic boundary chunking with legal structure awareness
        if doc_type in ['contract', 'agreement']:
            # Contract-specific chunking
            contract_chunks = self._chunk_contract_by_sections(doc_text, doc_id)
            chunks.extend([chunk['text'] for chunk in contract_chunks])
            metadata.extend(contract_chunks)
        elif doc_type in ['statute', 'regulation']:
            # Legal document chunking
            legal_chunks = self._chunk_legal_document(doc_text, doc_id)
            chunks.extend([chunk['text'] for chunk in legal_chunks])
            metadata.extend(legal_chunks)
        else:
            # General document chunking
            general_chunks = self._chunk_general_document(doc_text, doc_id, doc_type)
            chunks.extend([chunk['text'] for chunk in general_chunks])
            metadata.extend(general_chunks)
        
        return chunks, metadata
    
    def _chunk_contract_by_sections(self, text: str, doc_id: str) -> List[Dict]:
        """Chunk contract by sections, clauses, and sub-clauses"""
        chunks = []
        
        # Simple section-based chunking (can be enhanced with NLP)
        sections = text.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:  # Skip very short sections
                continue
                
            # Detect section type
            section_type = self._detect_section_type(section)
            
            # Create chunk with metadata
            chunk = {
                'text': section.strip(),
                'doc_id': doc_id,
                'chunk_id': f"{doc_id}_section_{i}",
                'section_type': section_type,
                'chunk_type': 'section',
                'hierarchy_level': 1,
                'legal_importance': self._assess_legal_importance(section, section_type),
                'timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
            
            # Further chunk long sections
            if len(section) > 1000:
                sub_chunks = self._create_sub_chunks(section, chunk)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_legal_document(self, text: str, doc_id: str) -> List[Dict]:
        """Chunk legal documents (statutes, regulations)"""
        chunks = []
        
        # Split by legal markers (Article, Section, Subsection, etc.)
        import re
        legal_markers = r'(Article|Section|Subsection|Paragraph|Clause)\s+\d+'
        sections = re.split(legal_markers, text)
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:
                continue
                
            chunk = {
                'text': section.strip(),
                'doc_id': doc_id,
                'chunk_id': f"{doc_id}_legal_{i}",
                'section_type': 'legal_provision',
                'chunk_type': 'legal_section',
                'hierarchy_level': 1,
                'legal_importance': 0.8,  # Legal documents are generally important
                'timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_general_document(self, text: str, doc_id: str, doc_type: str) -> List[Dict]:
        """General document chunking with dynamic context windowing"""
        chunks = []
        
        # Dynamic chunking based on document length
        chunk_size = min(800, max(400, len(text) // 10))  # Adaptive chunk size
        overlap = chunk_size // 4  # 25% overlap
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            
            if len(chunk_text.strip()) < 100:  # Skip very short chunks
                continue
            
            chunk = {
                'text': chunk_text.strip(),
                'doc_id': doc_id,
                'chunk_id': f"{doc_id}_chunk_{i // (chunk_size - overlap)}",
                'section_type': 'general',
                'chunk_type': 'text_chunk',
                'hierarchy_level': 1,
                'legal_importance': 0.5,
                'timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        return chunks
    
    def _detect_section_type(self, section: str) -> str:
        """Detect the type of contract section"""
        section_lower = section.lower()
        
        if any(term in section_lower for term in ['payment', 'fee', 'cost', 'price', 'compensation']):
            return 'financial'
        elif any(term in section_lower for term in ['liability', 'indemnif', 'damages', 'loss']):
            return 'liability'
        elif any(term in section_lower for term in ['termination', 'end', 'expire', 'cancel']):
            return 'termination'
        elif any(term in section_lower for term in ['confidential', 'proprietary', 'non-disclosure']):
            return 'confidentiality'
        elif any(term in section_lower for term in ['intellectual property', 'copyright', 'patent', 'trademark']):
            return 'intellectual_property'
        elif any(term in section_lower for term in ['dispute', 'arbitration', 'litigation', 'court']):
            return 'dispute_resolution'
        else:
            return 'general'
    
    def _assess_legal_importance(self, section: str, section_type: str) -> float:
        """Assess the legal importance of a section"""
        importance_weights = {
            'liability': 0.9,
            'financial': 0.8,
            'termination': 0.8,
            'dispute_resolution': 0.7,
            'intellectual_property': 0.7,
            'confidentiality': 0.6,
            'general': 0.5
        }
        
        base_importance = importance_weights.get(section_type, 0.5)
        
        # Adjust based on risk indicators
        risk_terms = ['unlimited', 'sole discretion', 'without notice', 'waive', 'indemnify']
        risk_count = sum(1 for term in risk_terms if term in section.lower())
        
        return min(1.0, base_importance + (risk_count * 0.1))
    
    def _create_sub_chunks(self, section: str, parent_chunk: Dict) -> List[Dict]:
        """Create sub-chunks for long sections"""
        sub_chunks = []
        chunk_size = 500
        overlap = 100
        
        for i in range(0, len(section), chunk_size - overlap):
            sub_text = section[i:i + chunk_size]
            
            if len(sub_text.strip()) < 100:
                continue
            
            sub_chunk = parent_chunk.copy()
            sub_chunk.update({
                'text': sub_text.strip(),
                'chunk_id': f"{parent_chunk['chunk_id']}_sub_{i // (chunk_size - overlap)}",
                'chunk_type': 'sub_section',
                'hierarchy_level': 2,
                'parent_chunk_id': parent_chunk['chunk_id']
            })
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    async def _build_vector_store(self, chunks: List[str]):
        """Build FAISS vector store with embeddings"""
        logger.info("🔢 Building vector embeddings...")
        
        # Generate embeddings in optimized batches for maximum speed
        batch_size = 8  # Smaller batches for faster processing
        all_embeddings = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = self.embedding_model.encode(
                batch, 
                convert_to_numpy=True,
                show_progress_bar=False,  # Disable progress bar
                batch_size=batch_size,  # Explicit batch size
                normalize_embeddings=True  # Normalize for better similarity
            )
            all_embeddings.append(embeddings)
        
        # Combine all embeddings
        embeddings_matrix = np.vstack(all_embeddings).astype('float32')
        
        # Add to FAISS index
        self.vector_store.add(embeddings_matrix)
        
        logger.info(f"✅ Added {embeddings_matrix.shape[0]} embeddings to vector store")
    
    async def _build_bm25_index(self, chunks: List[str]):
        """Build BM25 sparse retrieval index"""
        logger.info("📝 Building BM25 index...")
        
        # Tokenize documents with legal-specific preprocessing
        tokenized_docs = []
        for chunk in chunks:
            tokens = self._legal_tokenize(chunk)
            tokenized_docs.append(tokens)
        
        # Create BM25 index with legal-specific term weighting
        self.bm25_retriever = BM25Okapi(tokenized_docs, k1=1.5, b=0.75)
        
        logger.info(f"✅ Built BM25 index with {len(tokenized_docs)} documents")
    
    def _legal_tokenize(self, text: str) -> List[str]:
        """Legal-specific tokenization with term weighting"""
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Preserve legal terms and phrases
        legal_phrases = [
            'force majeure', 'due process', 'good faith', 'best efforts',
            'intellectual property', 'trade secret', 'non-disclosure',
            'liquidated damages', 'specific performance', 'breach of contract'
        ]
        
        # Replace phrases with single tokens
        for phrase in legal_phrases:
            text = text.replace(phrase, phrase.replace(' ', '_'))
        
        # Basic tokenization
        tokens = re.findall(r'\b\w+\b', text)
        
        # Filter out very short tokens and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        tokens = [token for token in tokens if len(token) > 2 and token not in stop_words]
        
        return tokens
    
    async def _build_legal_knowledge_graph(self, documents: List[Dict[str, Any]]):
        """Build knowledge graph for legal entity relationships"""
        logger.info("🕸️ Building legal knowledge graph...")
        
        # Simple entity extraction and relationship mapping
        for doc in documents:
            doc_text = doc.get('text', '')
            doc_id = doc.get('id', 'unknown')
            
            # Extract legal entities (simplified)
            entities = self._extract_legal_entities(doc_text)
            
            self.legal_knowledge_base[doc_id] = {
                'entities': entities,
                'document_type': doc.get('type', 'general'),
                'relationships': self._extract_entity_relationships(entities, doc_text)
            }
        
        logger.info(f"✅ Built knowledge graph with {len(self.legal_knowledge_base)} documents")
    
    def _extract_legal_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal entities from text"""
        entities = []
        
        # Simple pattern-based entity extraction
        import re
        
        # Extract monetary amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        for match in re.finditer(money_pattern, text):
            entities.append({
                'type': 'monetary_amount',
                'value': match.group(),
                'position': match.span()
            })
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            entities.append({
                'type': 'date',
                'value': match.group(),
                'position': match.span()
            })
        
        # Extract percentages
        percent_pattern = r'\b\d+(?:\.\d+)?%\b'
        for match in re.finditer(percent_pattern, text):
            entities.append({
                'type': 'percentage',
                'value': match.group(),
                'position': match.span()
            })
        
        return entities
    
    def _extract_entity_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """Extract relationships between entities"""
        relationships = []
        
        # Simple co-occurrence based relationships
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # Check if entities are close to each other in text
                pos1 = entity1['position']
                pos2 = entity2['position']
                
                if abs(pos1[0] - pos2[0]) < 200:  # Within 200 characters
                    relationships.append({
                        'entity1': entity1,
                        'entity2': entity2,
                        'relationship_type': 'co_occurrence',
                        'confidence': 0.7
                    })
        
        return relationships
    
    async def retrieve_and_rerank(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Multi-stage retrieval with comprehensive reranking - OPTIMIZED"""
        logger.info(f"🔍 Multi-stage retrieval for query: {query[:50]}...")
        
        try:
            # OPTIMIZATION: Parallel retrieval for better performance
            dense_task = asyncio.create_task(self._dense_vector_search(query))
            sparse_task = asyncio.create_task(self._sparse_bm25_search(query))
            
            # Execute both retrievals concurrently
            dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
            
            # Stage 3: Combine and deduplicate results
            combined_results = self._combine_retrieval_results(dense_results, sparse_results)
            
            # OPTIMIZATION: Limit results early to reduce processing time
            if len(combined_results) > self.reranking_top_k:
                combined_results = combined_results[:self.reranking_top_k]
            
            # Stage 4: Streamlined reranking pipeline
            reranked_results = await self._optimized_reranking(query, combined_results, context)
            
            # Stage 5: Quick memory and feedback application
            final_results = self._quick_apply_memory_and_feedback(query, reranked_results)
            
            logger.info(f"✅ Retrieved and reranked {len(final_results)} results in optimized mode")
            
            return final_results[:self.final_top_k]
            
        except Exception as e:
            logger.error(f"Retrieval and reranking failed: {e}")
            return []
    
    async def _dense_vector_search(self, query: str) -> List[Dict[str, Any]]:
        """Dense vector search using embeddings"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Search in FAISS index
        distances, indices = self.vector_store.search(
            query_embedding.astype('float32'), 
            k=min(self.max_chunks_per_retrieval, self.vector_store.ntotal)
        )
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.document_chunks):
                results.append({
                    'text': self.document_chunks[idx],
                    'metadata': self.chunk_metadata[idx],
                    'dense_score': float(distance),
                    'retrieval_method': 'dense_vector',
                    'rank': i
                })
        
        return results
    
    async def _sparse_bm25_search(self, query: str) -> List[Dict[str, Any]]:
        """Sparse BM25 search"""
        if not self.bm25_retriever:
            return []
        
        # Tokenize query
        query_tokens = self._legal_tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25_retriever.get_scores(query_tokens)
        
        # Get top results
        top_indices = np.argsort(scores)[::-1][:self.max_chunks_per_retrieval]
        
        results = []
        for i, idx in enumerate(top_indices):
            if idx < len(self.document_chunks) and scores[idx] > 0:
                results.append({
                    'text': self.document_chunks[idx],
                    'metadata': self.chunk_metadata[idx],
                    'bm25_score': float(scores[idx]),
                    'retrieval_method': 'sparse_bm25',
                    'rank': i
                })
        
        return results
    
    def _combine_retrieval_results(self, dense_results: List[Dict], sparse_results: List[Dict]) -> List[Dict]:
        """Combine and deduplicate retrieval results"""
        combined = {}
        
        # Add dense results
        for result in dense_results:
            chunk_id = result['metadata'].get('chunk_id', 'unknown')
            if chunk_id not in combined:
                combined[chunk_id] = result
                combined[chunk_id]['combined_score'] = result.get('dense_score', 0) * 0.6
            else:
                combined[chunk_id]['dense_score'] = result.get('dense_score', 0)
                combined[chunk_id]['combined_score'] += result.get('dense_score', 0) * 0.6
        
        # Add sparse results
        for result in sparse_results:
            chunk_id = result['metadata'].get('chunk_id', 'unknown')
            if chunk_id not in combined:
                combined[chunk_id] = result
                combined[chunk_id]['combined_score'] = result.get('bm25_score', 0) * 0.4
            else:
                combined[chunk_id]['bm25_score'] = result.get('bm25_score', 0)
                combined[chunk_id]['combined_score'] += result.get('bm25_score', 0) * 0.4
        
        # Sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return results[:self.reranking_top_k]
    
    async def _comprehensive_reranking(self, query: str, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Comprehensive reranking pipeline"""
        if not results:
            return results
        
        # Cross-encoder reranking
        if self.cross_encoder:
            results = await self._cross_encoder_reranking(query, results)
        
        # Legal domain-specific reranking
        results = await self._legal_domain_reranking(query, results, context)
        
        # Multi-criteria reranking
        results = await self._multi_criteria_reranking(query, results, context)
        
        # Ensemble reranking
        results = await self._ensemble_reranking(query, results)
        
        return results
    
    async def _cross_encoder_reranking(self, query: str, results: List[Dict]) -> List[Dict]:
        """Cross-encoder reranking for improved relevance"""
        if not self.cross_encoder:
            return results
        
        try:
            # Prepare query-passage pairs
            pairs = [(query, result['text']) for result in results]
            
            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs)
            
            # Update results with cross-encoder scores
            for result, score in zip(results, scores):
                result['cross_encoder_score'] = float(score)
            
            # Sort by cross-encoder score
            results.sort(key=lambda x: x.get('cross_encoder_score', 0), reverse=True)
            
        except Exception as e:
            logger.warning(f"Cross-encoder reranking failed: {e}")
        
        return results
    
    async def _legal_domain_reranking(self, query: str, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Legal domain-specific reranking with contract clause similarity"""
        for result in results:
            metadata = result.get('metadata', {})
            
            # Legal importance boost
            legal_importance = metadata.get('legal_importance', 0.5)
            result['legal_importance_score'] = legal_importance
            
            # Section type relevance
            section_type = metadata.get('section_type', 'general')
            section_relevance = self._calculate_section_relevance(query, section_type)
            result['section_relevance_score'] = section_relevance
            
            # Contract clause similarity
            clause_similarity = self._calculate_clause_similarity(query, result['text'])
            result['clause_similarity_score'] = clause_similarity
            
            # Combine legal domain scores
            result['legal_domain_score'] = (
                legal_importance * 0.3 +
                section_relevance * 0.4 +
                clause_similarity * 0.3
            )
        
        return results
    
    def _calculate_section_relevance(self, query: str, section_type: str) -> float:
        """Calculate relevance based on section type"""
        query_lower = query.lower()
        
        relevance_map = {
            'financial': ['payment', 'cost', 'fee', 'money', 'price', 'compensation'],
            'liability': ['liability', 'responsible', 'damages', 'loss', 'indemnify'],
            'termination': ['terminate', 'end', 'cancel', 'expire', 'breach'],
            'confidentiality': ['confidential', 'secret', 'disclosure', 'privacy'],
            'intellectual_property': ['ip', 'copyright', 'patent', 'trademark', 'proprietary'],
            'dispute_resolution': ['dispute', 'arbitration', 'court', 'litigation', 'resolve']
        }
        
        if section_type in relevance_map:
            keywords = relevance_map[section_type]
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            return min(1.0, matches / len(keywords) * 2)  # Boost relevance
        
        return 0.5  # Default relevance
    
    def _calculate_clause_similarity(self, query: str, clause_text: str) -> float:
        """Calculate contract clause similarity scoring"""
        query_lower = query.lower()
        clause_lower = clause_text.lower()
        
        # Keyword overlap
        query_words = set(query_lower.split())
        clause_words = set(clause_lower.split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(clause_words))
        keyword_similarity = overlap / len(query_words)
        
        # Legal term matching boost
        legal_terms = [
            'shall', 'may', 'must', 'agree', 'covenant', 'warrant',
            'represent', 'indemnify', 'liable', 'breach', 'default'
        ]
        
        legal_term_matches = sum(1 for term in legal_terms if term in clause_lower)
        legal_boost = min(0.3, legal_term_matches * 0.1)
        
        return min(1.0, keyword_similarity + legal_boost)
    
    async def _multi_criteria_reranking(self, query: str, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Multi-criteria reranking combining relevance, recency, and legal precedent"""
        for result in results:
            metadata = result.get('metadata', {})
            
            # Recency score (newer documents get slight boost)
            timestamp = metadata.get('timestamp', datetime.now().isoformat())
            try:
                doc_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                days_old = (datetime.now() - doc_date.replace(tzinfo=None)).days
                recency_score = max(0.1, 1.0 - (days_old / 365))  # Decay over a year
            except:
                recency_score = 0.5
            
            result['recency_score'] = recency_score
            
            # Legal precedent importance (hierarchy level)
            hierarchy_level = metadata.get('hierarchy_level', 1)
            precedent_score = 1.0 / hierarchy_level  # Higher level = more important
            result['precedent_score'] = precedent_score
            
            # Document type importance
            doc_type_weights = {
                'contract': 0.9,
                'agreement': 0.9,
                'statute': 1.0,
                'regulation': 0.8,
                'case_law': 0.7,
                'general': 0.5
            }
            
            chunk_type = metadata.get('chunk_type', 'general')
            doc_type_score = doc_type_weights.get(chunk_type, 0.5)
            result['doc_type_score'] = doc_type_score
            
            # Multi-criteria combined score
            result['multi_criteria_score'] = (
                result.get('cross_encoder_score', 0.5) * 0.4 +
                result.get('legal_domain_score', 0.5) * 0.3 +
                recency_score * 0.1 +
                precedent_score * 0.1 +
                doc_type_score * 0.1
            )
        
        return results
    
    async def _ensemble_reranking(self, query: str, results: List[Dict]) -> List[Dict]:
        """Ensemble reranking using multiple models for optimal result ordering"""
        for result in results:
            # Combine all scoring methods
            scores = [
                result.get('combined_score', 0) * 0.2,
                result.get('cross_encoder_score', 0) * 0.3,
                result.get('legal_domain_score', 0) * 0.2,
                result.get('multi_criteria_score', 0) * 0.2,
                result.get('legal_importance_score', 0) * 0.1
            ]
            
            # Ensemble final score
            result['ensemble_score'] = sum(scores)
        
        # Final sort by ensemble score
        results.sort(key=lambda x: x.get('ensemble_score', 0), reverse=True)
        
        return results
    
    async def _optimized_reranking(self, query: str, results: List[Dict], context: Dict = None) -> List[Dict]:
        """Optimized reranking pipeline for better performance"""
        if not results:
            return results
        
        # OPTIMIZATION: Only use cross-encoder for top results
        top_results = results[:10]  # Limit to top 10 for cross-encoder
        
        # Cross-encoder reranking (only for top results)
        if self.cross_encoder and top_results:
            try:
                pairs = [(query, result['text'][:500]) for result in top_results]  # Limit text length
                scores = self.cross_encoder.predict(pairs)
                
                for result, score in zip(top_results, scores):
                    result['cross_encoder_score'] = float(score)
                
                # Sort by cross-encoder score
                top_results.sort(key=lambda x: x.get('cross_encoder_score', 0), reverse=True)
                
            except Exception as e:
                logger.warning(f"Cross-encoder reranking failed: {e}")
        
        # Quick legal domain scoring
        for result in results:
            metadata = result.get('metadata', {})
            legal_importance = metadata.get('legal_importance', 0.5)
            result['final_score'] = (
                result.get('combined_score', 0) * 0.6 +
                result.get('cross_encoder_score', 0.5) * 0.3 +
                legal_importance * 0.1
            )
        
        # Final sort
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results
    
    def _quick_apply_memory_and_feedback(self, query: str, results: List[Dict]) -> List[Dict]:
        """Quick memory and feedback application without async overhead"""
        # Store query in conversation memory (non-async)
        self.conversation_memory.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results_count': len(results)
        })
        
        # Keep memory manageable
        if len(self.conversation_memory) > 50:
            self.conversation_memory = self.conversation_memory[-25:]
        
        # Quick feedback application
        for result in results:
            chunk_id = result['metadata'].get('chunk_id', 'unknown')
            feedback_score = self.feedback_scores.get(chunk_id, 0.5)
            
            # Adjust final score based on feedback
            result['final_score'] = (
                result.get('final_score', 0) * 0.8 +
                feedback_score * 0.2
            )
        
        # Final sort
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results
    
    async def _apply_memory_and_feedback(self, query: str, results: List[Dict]) -> List[Dict]:
        """Apply conversation memory and feedback-based reranking"""
        # Store query in conversation memory
        self.conversation_memory.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results_count': len(results)
        })
        
        # Keep memory manageable
        if len(self.conversation_memory) > 100:
            self.conversation_memory = self.conversation_memory[-50:]
        
        # Apply feedback-based adjustments
        for result in results:
            chunk_id = result['metadata'].get('chunk_id', 'unknown')
            
            # Get historical feedback for this chunk
            feedback_score = self.feedback_scores.get(chunk_id, 0.5)
            result['feedback_score'] = feedback_score
            
            # Adjust final score based on feedback
            result['final_score'] = (
                result.get('ensemble_score', 0) * 0.8 +
                feedback_score * 0.2
            )
        
        # Final sort
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results
    
    async def update_feedback(self, chunk_id: str, feedback_score: float):
        """Update feedback score for a chunk based on user interaction"""
        if chunk_id in self.feedback_scores:
            # Exponential moving average
            self.feedback_scores[chunk_id] = (
                self.feedback_scores[chunk_id] * 0.7 + feedback_score * 0.3
            )
        else:
            self.feedback_scores[chunk_id] = feedback_score
        
        logger.info(f"Updated feedback for {chunk_id}: {self.feedback_scores[chunk_id]:.3f}")
    
    async def generate_hyde_query(self, original_query: str) -> str:
        """Generate HyDE (Hypothetical Document Embeddings) for query refinement"""
        # Simple HyDE implementation - generate hypothetical answer
        hyde_prompt = f"""
        Given this legal question: "{original_query}"
        
        Generate a hypothetical legal document excerpt that would perfectly answer this question.
        Focus on the specific legal concepts, terms, and structure that would be found in relevant legal documents.
        """
        
        # For now, return enhanced query (can be improved with LLM integration)
        enhanced_query = f"{original_query} legal document contract clause provision terms conditions"
        
        return enhanced_query
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        return {
            'vector_store_size': self.vector_store.ntotal if self.vector_store else 0,
            'bm25_corpus_size': len(self.document_chunks) if self.bm25_retriever else 0,
            'total_chunks': len(self.document_chunks),
            'knowledge_graph_entities': len(self.legal_knowledge_base),
            'conversation_memory_size': len(self.conversation_memory),
            'feedback_entries': len(self.feedback_scores),
            'models_loaded': {
                'embedding_model': self.embedding_model is not None,
                'cross_encoder': self.cross_encoder is not None,
                'vector_store': self.vector_store is not None,
                'bm25_retriever': self.bm25_retriever is not None
            }
        }

# Global instance
advanced_rag_service = AdvancedRAGService()