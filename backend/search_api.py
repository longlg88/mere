"""
Search API Endpoints
Day 12: Semantic and Hybrid Search Implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime, timedelta

from embedding_service import embedding_service, semantic_search_service
from search_models import SearchDocument, SearchQuery, UsageAnalytics
from database import get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="검색 쿼리")
    search_type: str = Field(default="hybrid", description="검색 타입: semantic, keyword, hybrid")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="검색 필터")
    top_k: int = Field(default=10, ge=1, le=50, description="반환할 최대 결과 수")
    min_similarity: float = Field(default=0.1, ge=0.0, le=1.0, description="최소 유사도 임계값")


class SearchResult(BaseModel):
    id: str
    doc_type: str
    title: Optional[str]
    content: str
    category: Optional[str]
    created_at: datetime
    
    # Search scores
    similarity: Optional[float] = None
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    final_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SearchResult]
    total_count: int
    processing_time_ms: float
    query_id: str


class IndexDocumentRequest(BaseModel):
    doc_type: str = Field(..., description="문서 타입: memo, todo, event")
    source_id: str = Field(..., description="원본 데이터 ID")
    title: Optional[str] = None
    content: str = Field(..., description="문서 내용")
    category: Optional[str] = None
    priority: Optional[str] = None
    tags: List[str] = Field(default=[], description="태그 목록")
    source_created_at: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    period: str
    total_searches: int
    avg_response_time_ms: float
    popular_queries: List[Dict[str, Any]]
    intent_frequency: List[Dict[str, Any]]
    search_success_rate: float


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    session_id: str = Query(None, description="세션 ID"),
    user_id: str = Query(None, description="사용자 ID"),
    db: Session = Depends(get_db_session)
):
    """
    시맨틱 검색 수행
    임베딩 기반 의미 검색
    """
    start_time = time.time()
    
    try:
        # Get query embedding
        query_embedding = await embedding_service.get_embedding(request.query)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Perform vector similarity search using SQL function
        sql_query = text("""
            SELECT * FROM search_documents_by_similarity(
                :query_embedding::vector,
                :similarity_threshold,
                :max_results
            )
        """)
        
        result = db.execute(sql_query, {
            "query_embedding": query_embedding,
            "similarity_threshold": request.min_similarity,
            "max_results": request.top_k
        })
        
        rows = result.fetchall()
        
        # Convert to response format
        search_results = []
        for row in rows:
            search_results.append(SearchResult(
                id=str(row.id),
                doc_type=row.doc_type,
                title=row.title,
                content=row.content,
                category=row.category,
                created_at=row.created_at,
                similarity=float(row.similarity)
            ))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log search query
        query_log = SearchQuery(
            session_id=session_id,
            user_id=user_id,
            query_text=request.query,
            query_type="semantic",
            query_embedding=query_embedding,
            filters=request.filters,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
            results_count=len(search_results),
            processing_time_ms=processing_time
        )
        
        db.add(query_log)
        db.commit()
        
        return SearchResponse(
            query=request.query,
            search_type="semantic",
            results=search_results,
            total_count=len(search_results),
            processing_time_ms=processing_time,
            query_id=str(query_log.id)
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/keyword", response_model=SearchResponse)
async def keyword_search(
    request: SearchRequest,
    session_id: str = Query(None),
    user_id: str = Query(None),
    db: Session = Depends(get_db_session)
):
    """
    키워드 검색 수행
    PostgreSQL 전체 텍스트 검색 사용
    """
    start_time = time.time()
    
    try:
        # Build base query
        query = db.query(SearchDocument)
        
        # Full-text search using content and title
        search_condition = func.to_tsvector('korean', 
            func.coalesce(SearchDocument.title, '') + ' ' + SearchDocument.content
        ).op('@@')(func.plainto_tsquery('korean', request.query))
        query = query.filter(search_condition)
        
        # Apply filters
        if request.filters:
            if 'doc_type' in request.filters:
                query = query.filter(SearchDocument.doc_type.in_(request.filters['doc_type']))
            if 'category' in request.filters:
                query = query.filter(SearchDocument.category.in_(request.filters['category']))
            if 'date_from' in request.filters:
                query = query.filter(SearchDocument.created_at >= request.filters['date_from'])
            if 'date_to' in request.filters:
                query = query.filter(SearchDocument.created_at <= request.filters['date_to'])
        
        # Order by text search rank
        query = query.order_by(
            desc(func.ts_rank_cd(
                func.to_tsvector('korean', SearchDocument.search_text),
                func.plainto_tsquery('korean', request.query)
            ))
        )
        
        # Limit results
        documents = query.limit(request.top_k).all()
        
        # Convert to response format
        search_results = []
        for doc in documents:
            # Calculate keyword score
            keyword_score = float(db.execute(
                text("SELECT ts_rank_cd(to_tsvector('korean', :content), plainto_tsquery('korean', :query))"),
                {"content": doc.search_text, "query": request.query}
            ).scalar() or 0.0)
            
            search_results.append(SearchResult(
                id=str(doc.id),
                doc_type=doc.doc_type,
                title=doc.title,
                content=doc.content,
                category=doc.category,
                created_at=doc.created_at,
                keyword_score=keyword_score
            ))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log search query
        query_log = SearchQuery(
            session_id=session_id,
            user_id=user_id,
            query_text=request.query,
            query_type="keyword",
            filters=request.filters,
            top_k=request.top_k,
            results_count=len(search_results),
            processing_time_ms=processing_time
        )
        
        db.add(query_log)
        db.commit()
        
        return SearchResponse(
            query=request.query,
            search_type="keyword",
            results=search_results,
            total_count=len(search_results),
            processing_time_ms=processing_time,
            query_id=str(query_log.id)
        )
        
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="시맨틱 점수 가중치"),
    session_id: str = Query(None),
    user_id: str = Query(None),
    db: Session = Depends(get_db_session)
):
    """
    하이브리드 검색 수행
    키워드 + 시맨틱 검색 결합
    """
    start_time = time.time()
    
    try:
        # Get query embedding
        query_embedding = await embedding_service.get_embedding(request.query)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Use hybrid search SQL function
        sql_query = text("""
            SELECT * FROM hybrid_search(
                :query_text,
                :query_embedding::vector,
                :semantic_weight,
                :max_results
            )
        """)
        
        result = db.execute(sql_query, {
            "query_text": request.query,
            "query_embedding": query_embedding,
            "semantic_weight": semantic_weight,
            "max_results": request.top_k
        })
        
        rows = result.fetchall()
        
        # Convert to response format
        search_results = []
        for row in rows:
            search_results.append(SearchResult(
                id=str(row.id),
                doc_type=row.doc_type,
                title=row.title,
                content=row.content,
                semantic_score=float(row.semantic_score),
                keyword_score=float(row.keyword_score),
                final_score=float(row.final_score)
            ))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log search query
        query_log = SearchQuery(
            session_id=session_id,
            user_id=user_id,
            query_text=request.query,
            query_type="hybrid",
            query_embedding=query_embedding,
            filters=request.filters,
            top_k=request.top_k,
            results_count=len(search_results),
            processing_time_ms=processing_time
        )
        
        db.add(query_log)
        db.commit()
        
        return SearchResponse(
            query=request.query,
            search_type="hybrid",
            results=search_results,
            total_count=len(search_results),
            processing_time_ms=processing_time,
            query_id=str(query_log.id)
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/index")
async def index_document(
    request: IndexDocumentRequest,
    db: Session = Depends(get_db_session)
):
    """
    문서를 검색 인덱스에 추가
    """
    try:
        # Generate embedding for content
        full_text = f"{request.title or ''} {request.content} {' '.join(request.tags)}"
        embedding = await embedding_service.get_embedding(full_text)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Create or update search document
        search_text = f"{request.title or ''} {request.content} {' '.join(request.tags)} {request.category or ''}"
        
        # Check if document already exists
        existing_doc = db.query(SearchDocument).filter(
            and_(
                SearchDocument.doc_type == request.doc_type,
                SearchDocument.source_id == request.source_id
            )
        ).first()
        
        if existing_doc:
            # Update existing document
            existing_doc.title = request.title
            existing_doc.content = request.content
            existing_doc.embedding = embedding
            existing_doc.category = request.category
            existing_doc.priority = request.priority
            existing_doc.tags = request.tags
            existing_doc.search_text = search_text
            existing_doc.source_created_at = request.source_created_at
            existing_doc.updated_at = func.now()
        else:
            # Create new document
            doc = SearchDocument(
                doc_type=request.doc_type,
                source_id=request.source_id,
                title=request.title,
                content=request.content,
                embedding=embedding,
                category=request.category,
                priority=request.priority,
                tags=request.tags,
                search_text=search_text,
                source_created_at=request.source_created_at
            )
            db.add(doc)
        
        db.commit()
        
        return {"success": True, "message": "Document indexed successfully"}
        
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_search_analytics(
    period: str = Query("7d", description="분석 기간: 1d, 7d, 30d"),
    db: Session = Depends(get_db_session)
):
    """
    검색 분석 데이터 조회
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        # Total searches
        total_searches = db.query(SearchQuery).filter(
            SearchQuery.created_at >= start_date
        ).count()
        
        # Average response time
        avg_response_time = db.query(func.avg(SearchQuery.processing_time_ms)).filter(
            SearchQuery.created_at >= start_date
        ).scalar() or 0.0
        
        # Popular queries
        popular_queries = db.query(
            SearchQuery.query_text,
            func.count(SearchQuery.id).label('count')
        ).filter(
            SearchQuery.created_at >= start_date
        ).group_by(SearchQuery.query_text).order_by(desc('count')).limit(10).all()
        
        popular_queries_list = [
            {"query": q.query_text, "count": q.count}
            for q in popular_queries
        ]
        
        # Intent frequency from usage analytics
        intent_frequency = db.query(
            UsageAnalytics.intent,
            func.count(UsageAnalytics.id).label('count')
        ).filter(
            and_(
                UsageAnalytics.created_at >= start_date,
                UsageAnalytics.intent.isnot(None)
            )
        ).group_by(UsageAnalytics.intent).order_by(desc('count')).limit(10).all()
        
        intent_frequency_list = [
            {"intent": i.intent, "count": i.count}
            for i in intent_frequency
        ]
        
        # Success rate
        total_events = db.query(UsageAnalytics).filter(
            UsageAnalytics.created_at >= start_date
        ).count()
        
        success_events = db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.created_at >= start_date,
                UsageAnalytics.success == True
            )
        ).count()
        
        success_rate = (success_events / total_events * 100) if total_events > 0 else 0.0
        
        return AnalyticsResponse(
            period=period,
            total_searches=total_searches,
            avg_response_time_ms=float(avg_response_time),
            popular_queries=popular_queries_list,
            intent_frequency=intent_frequency_list,
            search_success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Analytics query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/stats")
async def get_search_stats(db: Session = Depends(get_db_session)):
    """
    검색 인덱스 통계 조회
    """
    try:
        total_docs = db.query(SearchDocument).count()
        
        # Count by document type
        doc_type_counts = db.query(
            SearchDocument.doc_type,
            func.count(SearchDocument.id).label('count')
        ).group_by(SearchDocument.doc_type).all()
        
        doc_type_stats = {doc_type: count for doc_type, count in doc_type_counts}
        
        # Embedding service stats
        embedding_stats = semantic_search_service.get_index_stats()
        
        return {
            "total_documents": total_docs,
            "documents_by_type": doc_type_stats,
            "embedding_stats": embedding_stats,
            "database_stats": {
                "tables_created": True,
                "indexes_created": True,
                "pgvector_enabled": True
            }
        }
        
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")