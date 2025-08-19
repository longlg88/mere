-- Day 12 Search & Analytics 테이블 생성
-- PostgreSQL with pgvector extension

-- Search Documents table - 검색할 문서들을 저장
CREATE TABLE IF NOT EXISTS search_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type VARCHAR(50) NOT NULL, -- memo, todo, event, etc
    source_id VARCHAR(255) NOT NULL, -- 원본 데이터의 ID
    title VARCHAR(500),
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small 차원
    category VARCHAR(100),
    priority INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search Queries table - 검색 쿼리 로그
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- users 테이블 참조 (nullable for anonymous)
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    query_embedding vector(1536),
    search_type VARCHAR(20) DEFAULT 'semantic', -- semantic, keyword, hybrid
    filters JSONB DEFAULT '{}'::jsonb,
    result_count INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage Analytics table - 사용 분석 데이터
CREATE TABLE IF NOT EXISTS usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- users 테이블 참조 (nullable)
    session_id VARCHAR(255),
    event_type VARCHAR(50) NOT NULL, -- search, index, click, etc
    event_data JSONB DEFAULT '{}'::jsonb,
    intent VARCHAR(100), -- 추출된 의도
    confidence DECIMAL(3,2),
    success BOOLEAN DEFAULT true,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_search_documents_doc_type ON search_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_search_documents_source_id ON search_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_search_documents_category ON search_documents(category);
CREATE INDEX IF NOT EXISTS idx_search_documents_created_at ON search_documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_documents_tags ON search_documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_search_documents_metadata ON search_documents USING GIN(metadata);

-- Vector similarity search index (HNSW for better performance than IVFFlat for small datasets)
CREATE INDEX IF NOT EXISTS idx_search_documents_embedding ON search_documents 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_session_id ON search_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_search_type ON search_queries(search_type);
CREATE INDEX IF NOT EXISTS idx_search_queries_created_at ON search_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_queries_success ON search_queries(success);
CREATE INDEX IF NOT EXISTS idx_search_queries_filters ON search_queries USING GIN(filters);

-- Query embedding similarity index
CREATE INDEX IF NOT EXISTS idx_search_queries_embedding ON search_queries 
USING hnsw (query_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_session_id ON usage_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_event_type ON usage_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_intent ON usage_analytics(intent);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_created_at ON usage_analytics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_success ON usage_analytics(success);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_event_data ON usage_analytics USING GIN(event_data);

-- Sample search documents for testing
INSERT INTO search_documents (doc_type, source_id, title, content, category, priority, tags) VALUES
('memo', 'test_memo_1', '프로젝트 회의 메모', '다음 주 월요일 오전 10시에 프로젝트 킥오프 미팅이 있습니다. 주요 안건은 일정 및 역할 분담입니다.', 'work', 3, ARRAY['회의', '프로젝트', '일정']),
('todo', 'test_todo_1', '월간 보고서 작성', '이번 달 프로젝트 진행 상황을 정리하여 월간 보고서를 작성해야 합니다.', 'work', 3, ARRAY['보고서', '작업']),
('memo', 'test_memo_2', '개발 환경 설정', 'Docker 컨테이너를 사용하여 개발 환경을 구성하고 PostgreSQL과 Redis를 설정했습니다.', 'development', 2, ARRAY['개발', 'Docker', 'DB']),
('event', 'test_event_1', '팀 빌딩 이벤트', '팀원들과의 유대감 강화를 위한 팀 빌딩 이벤트를 계획 중입니다.', 'team', 1, ARRAY['팀빌딩', '이벤트']),
('todo', 'test_todo_2', 'AI 검색 기능 구현', '시맨틱 검색과 자연어 처리를 활용한 지능형 검색 시스템을 개발합니다.', 'development', 3, ARRAY['AI', '검색', '개발'])
ON CONFLICT (source_id) DO NOTHING;

COMMIT;