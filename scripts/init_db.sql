-- MERE AI Agent Database Initialization
-- PostgreSQL with pgvector extension

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

-- Memos table
CREATE TABLE memos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_embedding vector(384), -- for sentence-transformers all-MiniLM-L6-v2
    tags TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Todos table  
CREATE TABLE todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    priority INTEGER DEFAULT 1,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Events/Calendar table
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    calendar_provider VARCHAR(50), -- google, outlook, apple
    external_id VARCHAR(255), -- ID from external calendar
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table for context management
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(20) NOT NULL, -- user_input, ai_response, system
    content TEXT NOT NULL,
    audio_file_path VARCHAR(500), -- path to stored audio file
    intent VARCHAR(100),
    entities JSONB DEFAULT '{}'::jsonb,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

CREATE INDEX idx_memos_user_id ON memos(user_id);
CREATE INDEX idx_memos_created_at ON memos(created_at DESC);
CREATE INDEX idx_memos_tags ON memos USING GIN(tags);
CREATE INDEX idx_memos_content_embedding ON memos USING ivfflat (content_embedding vector_cosine_ops);

CREATE INDEX idx_todos_user_id ON todos(user_id);
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_due_date ON todos(due_date);
CREATE INDEX idx_todos_priority ON todos(priority DESC);

CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_calendar_provider ON events(calendar_provider);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_intent ON conversations(intent);

-- Sample data for testing
INSERT INTO users (username, email) VALUES 
('testuser', 'test@example.com'),
('demo', 'demo@mere.ai');

-- Sample memos
INSERT INTO memos (user_id, content, tags) VALUES
((SELECT id FROM users WHERE username = 'testuser'), '우유 사야함', ARRAY['shopping', 'food']),
((SELECT id FROM users WHERE username = 'testuser'), '프레젠테이션 준비하기', ARRAY['work', 'presentation']),
((SELECT id FROM users WHERE username = 'testuser'), '친구와 저녁 약속', ARRAY['personal', 'social']);

-- Sample todos
INSERT INTO todos (user_id, title, description, priority, due_date) VALUES
((SELECT id FROM users WHERE username = 'testuser'), '장보기', '우유, 빵, 계란 사기', 2, NOW() + INTERVAL '1 day'),
((SELECT id FROM users WHERE username = 'testuser'), '보고서 작성', 'Q4 실적 보고서 완성', 3, NOW() + INTERVAL '3 days'),
((SELECT id FROM users WHERE username = 'testuser'), '병원 예약', '정기 검진 예약 잡기', 1, NOW() + INTERVAL '1 week');

-- Sample events
INSERT INTO events (user_id, title, description, start_time, end_time, location) VALUES
((SELECT id FROM users WHERE username = 'testuser'), '팀 회의', '주간 팀 미팅', 
 NOW() + INTERVAL '1 day' + INTERVAL '9 hours', 
 NOW() + INTERVAL '1 day' + INTERVAL '10 hours', 
 '회의실 A'),
((SELECT id FROM users WHERE username = 'testuser'), '프레젠테이션', '신제품 발표', 
 NOW() + INTERVAL '3 days' + INTERVAL '14 hours', 
 NOW() + INTERVAL '3 days' + INTERVAL '16 hours', 
 '대회의실');