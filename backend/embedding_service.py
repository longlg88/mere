"""
Embedding Service for Semantic Search
Day 12: Search & Analytics Implementation
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import openai
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    텍스트 임베딩 생성 서비스
    OpenAI Embeddings API와 로컬 SentenceTransformers 지원
    """
    
    def __init__(self, model_name: str = "sentence-transformers/distiluse-base-multilingual-cased"):
        self.model_name = model_name
        self.local_model: Optional[SentenceTransformer] = None
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            logger.info("✅ OpenAI Embeddings API initialized")
        
        # Initialize local model as fallback
        self._load_local_model()
    
    def _load_local_model(self):
        """로컬 SentenceTransformer 모델 로드"""
        try:
            self.local_model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Local embedding model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")
            self.local_model = None
    
    async def get_embedding(self, text: str, use_openai: bool = True) -> Optional[List[float]]:
        """
        단일 텍스트에 대한 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            use_openai: OpenAI API 사용 여부 (기본값: True)
            
        Returns:
            임베딩 벡터 또는 None
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        
        # Try OpenAI first if available and requested
        if use_openai and self.openai_client:
            try:
                return await self._get_openai_embedding(text)
            except Exception as e:
                logger.warning(f"OpenAI embedding failed, falling back to local: {e}")
        
        # Fallback to local model
        if self.local_model:
            try:
                return await self._get_local_embedding(text)
            except Exception as e:
                logger.error(f"Local embedding failed: {e}")
                return None
        
        logger.error("No embedding model available")
        return None
    
    async def get_embeddings_batch(self, texts: List[str], use_openai: bool = True) -> List[Optional[List[float]]]:
        """
        배치 텍스트에 대한 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            use_openai: OpenAI API 사용 여부
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # Filter empty texts
        non_empty_texts = [text.strip() for text in texts if text and text.strip()]
        
        if not non_empty_texts:
            return [None] * len(texts)
        
        # Try OpenAI batch processing first
        if use_openai and self.openai_client:
            try:
                return await self._get_openai_embeddings_batch(non_empty_texts)
            except Exception as e:
                logger.warning(f"OpenAI batch embedding failed, falling back to local: {e}")
        
        # Fallback to local batch processing
        if self.local_model:
            try:
                return await self._get_local_embeddings_batch(non_empty_texts)
            except Exception as e:
                logger.error(f"Local batch embedding failed: {e}")
                return [None] * len(texts)
        
        logger.error("No embedding model available")
        return [None] * len(texts)
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """OpenAI API를 사용한 임베딩 생성"""
        response = await asyncio.to_thread(
            self.openai_client.embeddings.create,
            model="text-embedding-3-small",  # Cost-effective model
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    async def _get_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """OpenAI API를 사용한 배치 임베딩 생성"""
        # OpenAI supports up to 2048 inputs per request
        batch_size = 100  # Conservative batch size
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model="text-embedding-3-small",
                input=batch,
                encoding_format="float"
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _get_local_embedding(self, text: str) -> List[float]:
        """로컬 모델을 사용한 임베딩 생성"""
        embedding = await asyncio.to_thread(
            self.local_model.encode,
            text,
            convert_to_numpy=True
        )
        return embedding.tolist()
    
    async def _get_local_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """로컬 모델을 사용한 배치 임베딩 생성"""
        embeddings = await asyncio.to_thread(
            self.local_model.encode,
            texts,
            convert_to_numpy=True,
            batch_size=32
        )
        return embeddings.tolist()
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        두 임베딩 간의 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩 벡터
            embedding2: 두 번째 임베딩 벡터
            
        Returns:
            코사인 유사도 (-1 ~ 1)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def get_embedding_dimension(self) -> int:
        """임베딩 벡터의 차원 수 반환"""
        if self.openai_client:
            return 1536  # text-embedding-3-small dimension
        elif self.local_model:
            return self.local_model.get_sentence_embedding_dimension()
        else:
            return 512  # Default fallback dimension


class SemanticSearchService:
    """
    시맨틱 검색 서비스
    임베딩을 사용한 의미 기반 검색 구현
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.document_embeddings: Dict[str, List[float]] = {}  # doc_id -> embedding
        self.documents: Dict[str, Dict[str, Any]] = {}  # doc_id -> document data
    
    async def index_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        문서를 인덱싱하여 검색 가능하게 만듦
        
        Args:
            doc_id: 문서 고유 ID
            content: 문서 내용
            metadata: 추가 메타데이터
            
        Returns:
            인덱싱 성공 여부
        """
        try:
            # Generate embedding for content
            embedding = await self.embedding_service.get_embedding(content)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for document {doc_id}")
                return False
            
            # Store embedding and document
            self.document_embeddings[doc_id] = embedding
            self.documents[doc_id] = {
                "content": content,
                "metadata": metadata or {},
                "indexed_at": asyncio.get_event_loop().time()
            }
            
            logger.info(f"✅ Document indexed: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index document {doc_id}: {e}")
            return False
    
    async def search(self, query: str, top_k: int = 10, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """
        시맨틱 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            min_similarity: 최소 유사도 임계값
            
        Returns:
            검색 결과 리스트 (유사도 순 정렬)
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Calculate similarities with all documents
            similarities = []
            
            for doc_id, doc_embedding in self.document_embeddings.items():
                similarity = self.embedding_service.cosine_similarity(query_embedding, doc_embedding)
                
                if similarity >= min_similarity:
                    similarities.append({
                        "doc_id": doc_id,
                        "similarity": similarity,
                        "content": self.documents[doc_id]["content"],
                        "metadata": self.documents[doc_id]["metadata"]
                    })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top-k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []
    
    async def hybrid_search(self, query: str, keyword_results: List[Dict[str, Any]], 
                          semantic_weight: float = 0.7, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (키워드 + 시맨틱)
        
        Args:
            query: 검색 쿼리
            keyword_results: 키워드 검색 결과
            semantic_weight: 시맨틱 점수 가중치 (0.0 ~ 1.0)
            top_k: 반환할 최대 결과 수
            
        Returns:
            하이브리드 검색 결과
        """
        try:
            # Get semantic search results
            semantic_results = await self.search(query, top_k=top_k * 2)  # Get more for mixing
            
            # Create combined scoring
            combined_scores = {}
            keyword_weight = 1.0 - semantic_weight
            
            # Process keyword results
            for i, result in enumerate(keyword_results):
                doc_id = result.get("doc_id") or result.get("id")
                if doc_id:
                    # Keyword score based on rank (higher rank = higher score)
                    keyword_score = (len(keyword_results) - i) / len(keyword_results)
                    combined_scores[doc_id] = {
                        "keyword_score": keyword_score,
                        "semantic_score": 0.0,
                        "data": result
                    }
            
            # Process semantic results
            for result in semantic_results:
                doc_id = result["doc_id"]
                semantic_score = result["similarity"]
                
                if doc_id in combined_scores:
                    combined_scores[doc_id]["semantic_score"] = semantic_score
                else:
                    combined_scores[doc_id] = {
                        "keyword_score": 0.0,
                        "semantic_score": semantic_score,
                        "data": result
                    }
            
            # Calculate final scores and sort
            final_results = []
            
            for doc_id, scores in combined_scores.items():
                final_score = (
                    keyword_weight * scores["keyword_score"] + 
                    semantic_weight * scores["semantic_score"]
                )
                
                result = scores["data"].copy()
                result["final_score"] = final_score
                result["keyword_score"] = scores["keyword_score"]
                result["semantic_score"] = scores["semantic_score"]
                
                final_results.append(result)
            
            # Sort by final score
            final_results.sort(key=lambda x: x["final_score"], reverse=True)
            
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return keyword_results[:top_k]  # Fallback to keyword results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """인덱스 통계 반환"""
        return {
            "total_documents": len(self.documents),
            "total_embeddings": len(self.document_embeddings),
            "embedding_dimension": self.embedding_service.get_embedding_dimension(),
            "model_name": self.embedding_service.model_name
        }


# Global instances
embedding_service = EmbeddingService()
semantic_search_service = SemanticSearchService(embedding_service)