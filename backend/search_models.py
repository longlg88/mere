"""
Search & Analytics Database Models
Day 12: Semantic Search with pgvector support
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from typing import List, Dict, Any, Optional
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class SearchDocument(Base):
    """
    검색 가능한 문서 저장 테이블
    임베딩 벡터와 메타데이터 포함
    """
    __tablename__ = "search_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_type = Column(String(50), nullable=False)  # memo, todo, event, conversation
    source_id = Column(String(255), nullable=False)  # 원본 데이터 ID
    title = Column(String(500))
    content = Column(Text, nullable=False)
    
    # Vector embedding for semantic search
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    
    # Metadata for filtering and ranking
    category = Column(String(100))
    priority = Column(Integer, default=1)  # Changed to INTEGER to match table
    tags = Column(ARRAY(String), default=[])
    extra_data = Column('metadata', JSON, default={})  # Map to metadata column in DB
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())  # Added indexed_at
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_search_documents_doc_type', 'doc_type'),
        Index('idx_search_documents_category', 'category'),
        Index('idx_search_documents_created_at', 'created_at'),
    )


class SearchQuery(Base):
    """
    검색 쿼리 로그 및 분석 테이블
    """
    __tablename__ = "search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))  # Changed to UUID to match table
    session_id = Column(String(255))
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536))
    search_type = Column(String(20), default='semantic')  # Renamed from query_type
    filters = Column(JSON, default={})  # 검색 필터 (날짜, 카테고리 등)
    result_count = Column(Integer, default=0)  # Renamed from results_count
    processing_time_ms = Column(Integer)  # Changed to INTEGER
    success = Column(Boolean, default=True)  # Added success column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_search_queries_created_at', 'created_at'),
        Index('idx_search_queries_search_type', 'search_type'),  # Fixed index name
        Index('idx_search_queries_user_id', 'user_id'),
    )


class UsageAnalytics(Base):
    """
    사용 패턴 분석 테이블
    """
    __tablename__ = "usage_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))  # Changed to UUID to match table
    session_id = Column(String(255))
    event_type = Column(String(50), nullable=False)  # intent_processed, search_performed, action_completed
    event_data = Column(JSON, default={})  # 이벤트 관련 데이터
    intent = Column(String(100))
    confidence = Column(Float)  # Renamed from intent_confidence
    success = Column(Boolean, default=True)
    processing_time_ms = Column(Integer)  # Changed to INTEGER
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Renamed from timestamp
    
    __table_args__ = (
        Index('idx_usage_analytics_created_at', 'created_at'),  # Fixed index name
        Index('idx_usage_analytics_event_type', 'event_type'),
        Index('idx_usage_analytics_intent', 'intent'),
        Index('idx_usage_analytics_user_id', 'user_id'),
        Index('idx_usage_analytics_success', 'success'),
    )


class IntentFrequency(Base):
    """
    Intent 사용 빈도 집계 테이블
    """
    __tablename__ = "intent_frequency"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Intent details
    intent = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # 일자별 집계
    
    # Frequency metrics
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_ms = Column(Float)
    avg_confidence = Column(Float)
    
    # Time distribution
    hour_distribution = Column(JSON)  # {hour: count} for 24 hours
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_intent_frequency_intent_date', 'intent', 'date'),
        Index('idx_intent_frequency_date', 'date'),
    )


class SearchPerformance(Base):
    """
    검색 성능 메트릭 테이블
    """
    __tablename__ = "search_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False)
    hour = Column(Integer)  # 시간별 집계용
    
    # Search metrics
    total_searches = Column(Integer, default=0)
    semantic_searches = Column(Integer, default=0)
    keyword_searches = Column(Integer, default=0)
    hybrid_searches = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time_ms = Column(Float)
    avg_results_count = Column(Float)
    avg_user_satisfaction = Column(Float)
    
    # Effectiveness metrics
    searches_with_clicks = Column(Integer, default=0)  # 클릭이 발생한 검색
    avg_click_position = Column(Float)  # 평균 클릭 위치
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_search_performance_date', 'date'),
        Index('idx_search_performance_date_hour', 'date', 'hour'),
    )


# Database initialization SQL for pgvector extension
PGVECTOR_INIT_SQL = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create vector similarity search functions
CREATE OR REPLACE FUNCTION search_documents_by_similarity(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.1,
    max_results int DEFAULT 10
)
RETURNS TABLE(
    id uuid,
    doc_type varchar,
    title varchar,
    content text,
    similarity float,
    category varchar,
    created_at timestamptz
)
LANGUAGE sql STABLE AS $$
    SELECT 
        sd.id,
        sd.doc_type,
        sd.title,
        sd.content,
        1 - (sd.embedding <=> query_embedding) as similarity,
        sd.category,
        sd.created_at
    FROM search_documents sd
    WHERE sd.is_active = true
        AND 1 - (sd.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY sd.embedding <=> query_embedding
    LIMIT max_results;
$$;

-- Create hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text text,
    query_embedding vector(1536),
    semantic_weight float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE(
    id uuid,
    doc_type varchar,
    title varchar,
    content text,
    semantic_score float,
    keyword_score float,
    final_score float
)
LANGUAGE sql STABLE AS $$
    WITH semantic_results AS (
        SELECT 
            sd.id,
            sd.doc_type,
            sd.title,
            sd.content,
            1 - (sd.embedding <=> query_embedding) as semantic_score
        FROM search_documents sd
        WHERE sd.is_active = true
    ),
    keyword_results AS (
        SELECT 
            sd.id,
            sd.doc_type,
            sd.title,
            sd.content,
            ts_rank_cd(to_tsvector('korean', sd.search_text), plainto_tsquery('korean', query_text)) as keyword_score
        FROM search_documents sd
        WHERE sd.is_active = true
            AND to_tsvector('korean', sd.search_text) @@ plainto_tsquery('korean', query_text)
    )
    SELECT 
        COALESCE(s.id, k.id) as id,
        COALESCE(s.doc_type, k.doc_type) as doc_type,
        COALESCE(s.title, k.title) as title,
        COALESCE(s.content, k.content) as content,
        COALESCE(s.semantic_score, 0.0) as semantic_score,
        COALESCE(k.keyword_score, 0.0) as keyword_score,
        (semantic_weight * COALESCE(s.semantic_score, 0.0) + 
         (1 - semantic_weight) * COALESCE(k.keyword_score, 0.0)) as final_score
    FROM semantic_results s
    FULL OUTER JOIN keyword_results k ON s.id = k.id
    WHERE (s.semantic_score > 0.1 OR k.keyword_score > 0.0)
    ORDER BY final_score DESC
    LIMIT max_results;
$$;

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_search_documents_embedding_cosine 
ON search_documents USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_search_documents_fts 
ON search_documents USING gin (to_tsvector('korean', search_text));
"""