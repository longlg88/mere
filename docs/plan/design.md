# MERE AI Agent System Design Document

## Overview

MERE(Memory Engagement & Reminder Expert)는 Phase 2 고도화 AI Agent 기반 음성 비서로, 실시간 스트리밍 STT/TTS, Rasa NLU를 통한 정교한 자연어 이해, LangGraph 상태 머신을 통한 복합 업무 처리, 그리고 Langfuse 기반 지속 개선 시스템을 갖춘 완전 오픈소스 솔루션입니다.

### Design Goals
- **P50 <2s, P90 <2.5s** 실시간 응답
- **95% Intent 인식률, 90% Entity 추출 정확도**
- **완전 오픈소스** 스택으로 비용 0원
- **지속 개선** 가능한 AI Agent 시스템

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "iOS Client"
        A[PTT Button] --> B[Microphone Stream]
        B --> C[SwiftWhisper STT]
        C --> D[WebSocket Client]
        D --> E[Real-time UI]
        F[Piper Audio Player] --> G[Speaker]
        H[CoreData Cache] --> I[Offline Sync]
    end
    
    subgraph "AI Agent Backend"
        J[WebSocket Gateway] --> K[Rasa NLU Engine]
        K --> L[LangGraph State Machine]
        L --> M[Business Logic Layer]
        M --> N[External Integrations]
        O[Ollama LLM] --> L
        P[Piper TTS Server] --> Q[Audio Streaming]
    end
    
    subgraph "Data Layer"
        R[(PostgreSQL + pgvector)]
        S[(Redis Cache + Sessions)]
        T[(MinIO Object Storage)]
    end
    
    subgraph "Observability"
        U[Langfuse Tracing]
        V[DeepEval Quality]
        W[Performance Monitoring]
    end
    
    D <--> J
    Q --> F
    L --> R
    L --> S
    N --> T
    J --> U
    K --> U
    L --> U
    U --> V
    V --> W
```

---

## Component Design

### 1. iOS Client Architecture

#### 1.1 Voice Input Pipeline
```swift
// Voice input flow design
PTTButton -> AudioSession -> SwiftWhisper -> TextProcessor -> WebSocketClient

Components:
- PTTViewController: 음성 입력 UI 관리
- AudioSessionManager: 마이크 세션 및 권한 관리  
- SwiftWhisperSTT: 실시간 스트리밍 STT 처리
- TextProcessor: STT 결과 전처리 및 신뢰도 검증
- WebSocketManager: 서버와 실시간 양방향 통신
```

#### 1.2 Real-time UI System
```swift
// UI update flow design
STTPartialResult -> UIUpdateQueue -> MainThread -> ViewUpdates

Components:
- ConversationViewController: 메인 대화 인터페이스
- VoiceVisualizerView: 음성 인식 진행률 시각화
- ResponseStreamingView: TTS 응답 실시간 표시
- StatusIndicatorView: AI Agent 상태 표시 (listening/thinking/speaking)
- OfflineIndicatorView: 네트워크 상태 및 오프라인 모드 표시
```

#### 1.3 Audio Output Pipeline
```swift
// Audio output flow design
ServerAudioStream -> PiperAudioPlayer -> AudioQueue -> Speaker

Components:
- PiperAudioPlayer: 스트리밍 TTS 오디오 재생
- AudioQueueManager: 오디오 버퍼링 및 품질 관리
- SpeechFeedbackController: 음성/텍스트 피드백 조율
```

#### 1.4 Local Storage & Sync
```swift
// Data persistence design
CoreDataStack -> OfflineRepository -> SyncManager -> BackendAPI

Models:
- MemoEntity: 메모 로컬 저장
- TodoEntity: 할일 로컬 저장  
- EventEntity: 일정 로컬 캐시
- ConversationEntity: 대화 기록
- SyncStatusEntity: 동기화 상태 추적
```

### 2. AI Agent Backend Architecture

#### 2.1 WebSocket Gateway
```python
# WebSocket connection management
class WebSocketGateway:
    - connection_manager: 클라이언트 연결 관리
    - message_router: 메시지 타입별 라우팅
    - session_manager: 사용자 세션 관리
    - rate_limiter: 요청 속도 제한
    
# Message protocol design
{
    "type": "voice_input",
    "session_id": "uuid",
    "audio_data": "base64_encoded",
    "partial": true/false,
    "timestamp": "iso_datetime"
}
```

#### 2.2 Rasa NLU Engine
```yaml
# Rasa pipeline configuration
pipeline:
  - name: "ConveRTTokenizer"
    model_url: "korean_tokenizer_model"
  - name: "ConveRTFeaturizer"
  - name: "DIETClassifier"
    epochs: 100
    constrain_similarities: true
  - name: "EntitySynonymMapper"
  - name: "ResponseSelector"
    epochs: 100

# Intent examples
intents:
  - remember_memo
  - create_todo
  - schedule_event
  - search_items
  - modify_schedule
  - cancel_action
  - confirm_action
  
# Entity definitions
entities:
  - item_name
  - date_time
  - priority_level
  - category
  - person_name
  - location
```

#### 2.3 LangGraph State Machine
```python
# State machine design
from langgraph import StateGraph, END

class MereAgentState(TypedDict):
    user_input: str
    intent: str
    entities: Dict
    context: Dict
    action_history: List
    current_step: str
    confidence: float
    
# State transitions
def create_agent_graph():
    workflow = StateGraph(MereAgentState)
    
    # Nodes
    workflow.add_node("parse_input", parse_user_input)
    workflow.add_node("validate_intent", validate_intent_confidence)
    workflow.add_node("execute_action", execute_business_logic)
    workflow.add_node("confirm_action", request_user_confirmation)
    workflow.add_node("rollback_action", rollback_previous_action)
    workflow.add_node("generate_response", generate_response_text)
    
    # Edges
    workflow.add_edge("parse_input", "validate_intent")
    workflow.add_conditional_edges(
        "validate_intent",
        should_confirm,
        {
            "confirm": "confirm_action",
            "execute": "execute_action", 
            "clarify": "generate_response"
        }
    )
    
    return workflow.compile(checkpointer=MemorySaver())
```

#### 2.4 Business Logic Layer
```python
# Business logic components
class BusinessLogicManager:
    - memo_service: MemoService
    - todo_service: TodoService  
    - calendar_service: CalendarService
    - search_service: SearchService
    
class MemoService:
    async def create_memo(self, content: str, metadata: Dict) -> Memo
    async def search_memos(self, query: str, filters: Dict) -> List[Memo]
    async def update_memo(self, memo_id: str, updates: Dict) -> Memo
    
class TodoService:
    async def create_todo(self, title: str, metadata: Dict) -> Todo
    async def update_todo_status(self, todo_id: str, status: str) -> Todo
    async def get_todos_by_priority(self, priority: str) -> List[Todo]
    
class CalendarService:
    async def create_event(self, event_data: Dict) -> Event
    async def check_conflicts(self, start: datetime, end: datetime) -> List[Event]
    async def modify_event(self, event_id: str, changes: Dict) -> Event
```

### 3. Data Layer Design

#### 3.1 PostgreSQL Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Seoul',
    preferences JSONB DEFAULT '{}'
);

-- Memos table  
CREATE TABLE memos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,
    embedding VECTOR(768) -- for semantic search
);

-- Todos table
CREATE TABLE todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, done, cancelled
    priority INTEGER DEFAULT 0, -- 0=low, 1=medium, 2=high, 3=urgent
    due_date TIMESTAMP,
    category VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL
);

-- Events table (Google Calendar cache)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    gc_event_id VARCHAR(255), -- Google Calendar event ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]',
    recurring_rule VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table (for context & improvement)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    input_text TEXT NOT NULL,
    intent VARCHAR(100),
    entities JSONB DEFAULT '{}',
    confidence FLOAT,
    response_text TEXT,
    action_taken VARCHAR(100),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_memos_user_created ON memos(user_id, created_at DESC);
CREATE INDEX idx_memos_embedding ON memos USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_todos_user_status ON todos(user_id, status);
CREATE INDEX idx_events_user_time ON events(user_id, start_time);
CREATE INDEX idx_conversations_session ON conversations(session_id, created_at);
```

#### 3.2 Redis Data Structures
```python
# Redis key patterns and data structures

# User sessions
USER_SESSION = "session:{user_id}:{session_id}"
# Value: JSON with current context, state, and temporary data
{
    "current_state": "waiting_for_confirmation",
    "context": {...},
    "temp_data": {...},
    "expires_at": "timestamp"
}

# Rate limiting
RATE_LIMIT = "rate_limit:{user_id}:{minute}"
# Value: Counter with TTL

# Audio processing queue
AUDIO_QUEUE = "audio_processing"
# List of audio processing jobs

# TTS cache
TTS_CACHE = "tts:{text_hash}"
# Value: Audio file path or base64 data with TTL

# Conversation context
CONVERSATION_CONTEXT = "context:{user_id}"
# Value: Recent conversation history for context awareness
```

### 4. AI Pipeline Design

#### 4.1 STT Processing Pipeline
```python
class STTProcessingPipeline:
    def __init__(self):
        self.whisper_model = WhisperModel("large-v2", device="cpu")
        self.vad_detector = VADDetector()
        self.noise_reducer = NoiseReducer()
    
    async def process_audio_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """Real-time streaming STT processing"""
        buffer = AudioBuffer()
        
        async for audio_chunk in audio_stream:
            # Add to buffer
            buffer.add_chunk(audio_chunk)
            
            # Voice activity detection
            if self.vad_detector.has_speech(buffer.get_recent()):
                # Process partial transcription
                partial_text = await self.transcribe_partial(buffer.get_window())
                yield partial_text
            
        # Final transcription
        final_text = await self.transcribe_final(buffer.get_all())
        yield final_text
    
    async def transcribe_partial(self, audio_data: bytes) -> str:
        """Partial transcription for real-time feedback"""
        # Implement SwiftWhisper streaming
        pass
    
    async def transcribe_final(self, audio_data: bytes) -> str:
        """Final high-quality transcription"""
        # Implement full Whisper processing
        pass
```

#### 4.2 NLU Processing Pipeline
```python
class NLUProcessingPipeline:
    def __init__(self):
        self.rasa_agent = RasaAgent("models/nlu_model")
        self.ollama_client = OllamaClient("llama3:8b")
        self.confidence_threshold = 0.8
    
    async def process_text(self, text: str, context: Dict) -> NLUResult:
        """Process text through Rasa NLU with LLM fallback"""
        
        # Primary: Rasa NLU processing
        rasa_result = await self.rasa_agent.parse(text)
        
        if rasa_result.intent.confidence >= self.confidence_threshold:
            return NLUResult(
                intent=rasa_result.intent.name,
                entities=rasa_result.entities,
                confidence=rasa_result.intent.confidence,
                source="rasa"
            )
        
        # Fallback: Ollama LLM processing
        llm_result = await self.llm_fallback(text, context)
        return llm_result
    
    async def llm_fallback(self, text: str, context: Dict) -> NLUResult:
        """LLM-based intent parsing as fallback"""
        prompt = f"""
        사용자 입력: "{text}"
        대화 컨텍스트: {context}
        
        다음 중 하나의 intent로 분류하고 entities를 추출하세요:
        - remember_memo: 메모 저장
        - create_todo: 할일 생성
        - schedule_event: 일정 생성
        - search_items: 검색
        - modify_schedule: 일정 수정
        - cancel_action: 취소
        
        JSON 형식으로 응답:
        {{"intent": "...", "entities": {{}}, "confidence": 0.0-1.0}}
        """
        
        response = await self.ollama_client.generate(prompt)
        return self.parse_llm_response(response)
```

#### 4.3 LangGraph State Management
```python
class StateManager:
    def __init__(self):
        self.checkpoints = {}
        self.state_transitions = {
            "initial": ["parsing", "error"],
            "parsing": ["validation", "clarification", "error"],
            "validation": ["execution", "confirmation", "clarification"],
            "confirmation": ["execution", "cancellation"],
            "execution": ["success", "error", "partial_success"],
            "success": ["complete"],
            "error": ["retry", "escalation", "complete"],
            "cancellation": ["complete"]
        }
    
    async def transition_state(self, current_state: str, action: str, context: Dict) -> str:
        """Manage state transitions with validation"""
        if action not in self.state_transitions.get(current_state, []):
            raise InvalidStateTransition(f"Cannot transition from {current_state} to {action}")
        
        # Create checkpoint before transition
        checkpoint_id = self.create_checkpoint(current_state, context)
        
        try:
            new_state = await self.execute_transition(current_state, action, context)
            return new_state
        except Exception as e:
            # Rollback to checkpoint
            await self.rollback_to_checkpoint(checkpoint_id)
            raise e
    
    def create_checkpoint(self, state: str, context: Dict) -> str:
        """Create state checkpoint for rollback"""
        checkpoint_id = str(uuid.uuid4())
        self.checkpoints[checkpoint_id] = {
            "state": state,
            "context": copy.deepcopy(context),
            "timestamp": datetime.now()
        }
        return checkpoint_id
```

#### 4.4 TTS Generation Pipeline
```python
class TTSProcessingPipeline:
    def __init__(self):
        self.piper_client = PiperClient("jenny_korean")
        self.audio_optimizer = AudioOptimizer()
        self.streaming_buffer = StreamingBuffer()
    
    async def generate_speech_stream(self, text: str) -> AsyncIterator[bytes]:
        """Generate streaming TTS audio"""
        
        # Split text into sentences for streaming
        sentences = self.sentence_splitter.split(text)
        
        for sentence in sentences:
            # Generate audio for sentence
            audio_chunk = await self.piper_client.synthesize(sentence)
            
            # Optimize audio quality
            optimized_chunk = self.audio_optimizer.process(audio_chunk)
            
            # Add to streaming buffer
            self.streaming_buffer.add(optimized_chunk)
            
            # Yield when buffer has enough data
            while self.streaming_buffer.has_data():
                yield self.streaming_buffer.get_chunk()
        
        # Yield remaining data
        while self.streaming_buffer.has_data():
            yield self.streaming_buffer.get_chunk()
    
    async def cache_common_responses(self):
        """Pre-generate common responses for faster playback"""
        common_phrases = [
            "저장되었습니다.",
            "일정이 추가되었습니다.", 
            "다시 말씀해 주세요.",
            "확인되었습니다."
        ]
        
        for phrase in common_phrases:
            audio = await self.piper_client.synthesize(phrase)
            await self.cache_audio(phrase, audio)
```

---

## API Design

### 1. WebSocket API

#### 1.1 Connection & Authentication
```python
# WebSocket connection endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket connection for real-time communication"""
    
# Authentication message
{
    "type": "auth",
    "device_id": "unique_device_identifier",
    "token": "optional_auth_token"
}
```

#### 1.2 Message Types
```python
# Voice input message
{
    "type": "voice_input",
    "session_id": "uuid",
    "audio_data": "base64_encoded_audio",
    "is_final": false,
    "timestamp": "2024-01-01T12:00:00Z"
}

# Text input message (for testing/fallback)
{
    "type": "text_input", 
    "session_id": "uuid",
    "text": "내일 아침 우유 사는 거 기억시켜줘",
    "timestamp": "2024-01-01T12:00:00Z"
}

# Server response message
{
    "type": "response",
    "session_id": "uuid",
    "text_response": "저장되었습니다. 내일 아침 우유 사는 것을 기억하겠습니다.",
    "audio_url": "optional_tts_audio_url",
    "action_taken": "memo_created",
    "success": true,
    "timestamp": "2024-01-01T12:00:00Z"
}

# State update message
{
    "type": "state_update",
    "session_id": "uuid", 
    "state": "processing",
    "progress": 0.5,
    "message": "음성을 분석하고 있습니다..."
}

# Error message
{
    "type": "error",
    "session_id": "uuid",
    "error_code": "STT_FAILED",
    "error_message": "음성 인식에 실패했습니다.",
    "retry_possible": true
}
```

### 2. REST API (Backup & Management)

#### 2.1 Data Management Endpoints
```python
# Memos
GET /api/v1/memos?page=1&limit=20&search=query&category=work
POST /api/v1/memos
PUT /api/v1/memos/{memo_id}
DELETE /api/v1/memos/{memo_id}

# Todos  
GET /api/v1/todos?status=open&priority=high
POST /api/v1/todos
PUT /api/v1/todos/{todo_id}
PATCH /api/v1/todos/{todo_id}/status

# Events
GET /api/v1/events?start_date=2024-01-01&end_date=2024-01-31
POST /api/v1/events
PUT /api/v1/events/{event_id}
DELETE /api/v1/events/{event_id}
```

#### 2.2 Search & Analytics Endpoints
```python
# Semantic search
POST /api/v1/search
{
    "query": "지난주 쇼핑 관련 메모",
    "types": ["memos", "todos"],
    "limit": 10
}

# Analytics
GET /api/v1/analytics/usage?start_date=2024-01-01&end_date=2024-01-31
GET /api/v1/analytics/performance

# Health check
GET /api/v1/health
{
    "status": "healthy",
    "services": {
        "database": "up",
        "rasa": "up", 
        "ollama": "up",
        "piper": "up"
    }
}
```

---

## Performance Optimization Design

### 1. Latency Optimization Strategy

#### 1.1 Streaming Processing Pipeline
```python
# Parallel processing design
async def process_voice_input(audio_stream):
    # Start STT immediately
    stt_task = asyncio.create_task(
        stt_processor.process_stream(audio_stream)
    )
    
    # Prepare NLU pipeline  
    nlu_task = asyncio.create_task(
        nlu_processor.warm_up()
    )
    
    # Wait for STT completion
    transcribed_text = await stt_task
    
    # Process NLU (already warmed up)
    nlu_result = await nlu_processor.process(transcribed_text)
    
    # Start TTS generation while processing business logic
    tts_task = asyncio.create_task(
        tts_processor.generate_response(response_text)
    )
    
    business_task = asyncio.create_task(
        business_logic.execute(nlu_result)
    )
    
    # Return as soon as TTS starts
    await tts_task
```

#### 1.2 Caching Strategy
```python
# Multi-level caching design
class CachingStrategy:
    def __init__(self):
        self.l1_cache = {}  # In-memory for frequent requests
        self.l2_cache = RedisClient()  # Redis for session data
        self.l3_cache = DatabaseCache()  # DB for persistent data
    
    async def get_response(self, query_hash: str):
        # L1: Memory cache (fastest)
        if query_hash in self.l1_cache:
            return self.l1_cache[query_hash]
        
        # L2: Redis cache (fast)
        cached = await self.l2_cache.get(f"response:{query_hash}")
        if cached:
            self.l1_cache[query_hash] = cached  # Promote to L1
            return cached
        
        # L3: Database cache (slower)
        return await self.l3_cache.get(query_hash)
```

### 2. Accuracy Optimization

#### 2.1 Confidence-Based Routing
```python
class ConfidenceBasedRouter:
    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.9,      # Execute immediately
            "medium": 0.7,    # Ask for confirmation  
            "low": 0.5        # Request clarification
        }
    
    async def route_intent(self, nlu_result: NLUResult) -> str:
        confidence = nlu_result.confidence
        
        if confidence >= self.confidence_thresholds["high"]:
            return "execute_immediately"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "request_confirmation"
        elif confidence >= self.confidence_thresholds["low"]:
            return "request_clarification"
        else:
            return "fallback_to_llm"
```

#### 2.2 Context-Aware Processing
```python
class ContextManager:
    def __init__(self):
        self.conversation_history = {}
        self.user_preferences = {}
        self.temporal_context = {}
    
    def enhance_nlu_result(self, nlu_result: NLUResult, user_id: str) -> NLUResult:
        """Enhance NLU result with contextual information"""
        
        # Add conversation context
        recent_intents = self.get_recent_intents(user_id)
        nlu_result.context["recent_intents"] = recent_intents
        
        # Add user preferences
        preferences = self.get_user_preferences(user_id)
        nlu_result.context["preferences"] = preferences
        
        # Add temporal context
        current_time = datetime.now()
        nlu_result.context["current_time"] = current_time
        nlu_result.context["day_of_week"] = current_time.weekday()
        
        return nlu_result
```

---

## Observability & Monitoring Design

### 1. Langfuse Integration

#### 1.1 Tracing Configuration
```python
from langfuse import Langfuse

class LangfuseTracer:
    def __init__(self):
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host="http://localhost:3000"  # Self-hosted
        )
    
    def trace_conversation(self, session_id: str):
        """Create conversation-level trace"""
        return self.langfuse.trace(
            id=session_id,
            name="voice_conversation",
            user_id=session_id.split("-")[0]
        )
    
    def trace_step(self, trace, step_name: str, input_data: Dict, output_data: Dict, duration_ms: int):
        """Trace individual processing steps"""
        return trace.span(
            name=step_name,
            input=input_data,
            output=output_data,
            metadata={
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            }
        )
```

#### 1.2 Metrics Collection
```python
class MetricsCollector:
    def __init__(self):
        self.langfuse = LangfuseTracer()
        self.metrics_buffer = []
    
    async def collect_pipeline_metrics(self, session_id: str, pipeline_data: Dict):
        """Collect comprehensive pipeline metrics"""
        
        trace = self.langfuse.trace_conversation(session_id)
        
        # STT metrics
        trace.span(
            name="stt_processing",
            input={"audio_duration": pipeline_data["audio_duration"]},
            output={"transcribed_text": pipeline_data["transcribed_text"]},
            metadata={
                "confidence": pipeline_data["stt_confidence"],
                "processing_time_ms": pipeline_data["stt_duration"]
            }
        )
        
        # NLU metrics
        trace.span(
            name="nlu_processing", 
            input={"text": pipeline_data["transcribed_text"]},
            output={
                "intent": pipeline_data["intent"],
                "entities": pipeline_data["entities"]
            },
            metadata={
                "confidence": pipeline_data["nlu_confidence"],
                "processing_time_ms": pipeline_data["nlu_duration"],
                "fallback_used": pipeline_data["fallback_used"]
            }
        )
        
        # Business logic metrics
        trace.span(
            name="business_logic",
            input={"action": pipeline_data["action"]},
            output={"result": pipeline_data["result"]},
            metadata={
                "success": pipeline_data["success"],
                "processing_time_ms": pipeline_data["business_duration"]
            }
        )
        
        # TTS metrics
        trace.span(
            name="tts_processing",
            input={"response_text": pipeline_data["response_text"]},
            output={"audio_generated": True},
            metadata={
                "audio_duration": pipeline_data["tts_audio_duration"],
                "processing_time_ms": pipeline_data["tts_duration"]
            }
        )
```

### 2. Quality Evaluation System

#### 2.1 DeepEval Integration
```python
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

class QualityEvaluator:
    def __init__(self):
        self.answer_relevancy = AnswerRelevancyMetric()
        self.faithfulness = FaithfulnessMetric()
    
    async def evaluate_response_quality(self, input_text: str, response_text: str, context: str):
        """Evaluate response quality using DeepEval"""
        
        test_case = {
            "input": input_text,
            "actual_output": response_text,
            "retrieval_context": context
        }
        
        # Evaluate answer relevancy
        relevancy_score = await self.answer_relevancy.a_measure(test_case)
        
        # Evaluate faithfulness
        faithfulness_score = await self.faithfulness.a_measure(test_case)
        
        return {
            "relevancy_score": relevancy_score,
            "faithfulness_score": faithfulness_score,
            "overall_quality": (relevancy_score + faithfulness_score) / 2
        }
```

#### 2.2 A/B Testing Framework
```python
class ABTestingFramework:
    def __init__(self):
        self.experiments = {}
        self.user_assignments = {}
    
    def create_experiment(self, experiment_name: str, variants: List[str], traffic_split: Dict[str, float]):
        """Create new A/B test experiment"""
        self.experiments[experiment_name] = {
            "variants": variants,
            "traffic_split": traffic_split,
            "metrics": {},
            "start_time": datetime.now()
        }
    
    def assign_user_to_variant(self, user_id: str, experiment_name: str) -> str:
        """Assign user to experiment variant"""
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        
        if experiment_name not in self.user_assignments[user_id]:
            # Deterministic assignment based on user_id hash
            user_hash = hash(f"{user_id}_{experiment_name}") % 100
            cumulative = 0
            
            for variant, percentage in self.experiments[experiment_name]["traffic_split"].items():
                cumulative += percentage * 100
                if user_hash < cumulative:
                    self.user_assignments[user_id][experiment_name] = variant
                    break
        
        return self.user_assignments[user_id][experiment_name]
    
    def record_metric(self, user_id: str, experiment_name: str, metric_name: str, value: float):
        """Record metric for A/B test analysis"""
        variant = self.user_assignments.get(user_id, {}).get(experiment_name)
        if variant:
            if variant not in self.experiments[experiment_name]["metrics"]:
                self.experiments[experiment_name]["metrics"][variant] = {}
            
            if metric_name not in self.experiments[experiment_name]["metrics"][variant]:
                self.experiments[experiment_name]["metrics"][variant][metric_name] = []
            
            self.experiments[experiment_name]["metrics"][variant][metric_name].append(value)
```

---

## Security & Privacy Design

### 1. Data Privacy Protection

#### 1.1 On-Device Processing Priority
```python
class PrivacyProtectionManager:
    def __init__(self):
        self.sensitive_patterns = [
            r'\d{3}-\d{4}-\d{4}',  # Phone numbers
            r'\d{6}-\d{7}',        # Korean ID numbers
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
        ]
    
    def should_process_locally(self, text: str) -> bool:
        """Determine if text should be processed locally for privacy"""
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def sanitize_for_logging(self, text: str) -> str:
        """Sanitize sensitive information from logs"""
        sanitized = text
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        return sanitized
```

#### 1.2 Data Encryption
```python
class DataEncryption:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)
    
    def encrypt_user_data(self, data: str) -> str:
        """Encrypt sensitive user data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_user_data(self, encrypted_data: str) -> str:
        """Decrypt user data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
```

### 2. Audio Data Management

#### 2.1 Audio Storage Policy
```python
class AudioDataManager:
    def __init__(self):
        self.retention_policy = {
            "debug_audio": timedelta(days=7),    # For debugging
            "training_audio": timedelta(days=30), # For model improvement
            "user_audio": timedelta(days=0)      # Delete immediately after processing
        }
    
    async def store_audio_temporarily(self, audio_data: bytes, purpose: str) -> str:
        """Store audio with automatic deletion policy"""
        file_id = str(uuid.uuid4())
        retention_period = self.retention_policy.get(purpose, timedelta(days=0))
        
        if retention_period.days == 0:
            # Process immediately and don't store
            return await self.process_and_delete(audio_data)
        
        # Store with TTL
        await self.storage.store_with_ttl(file_id, audio_data, retention_period)
        return file_id
    
    async def cleanup_expired_audio(self):
        """Cleanup expired audio files"""
        expired_files = await self.storage.get_expired_files()
        for file_id in expired_files:
            await self.storage.delete(file_id)
            logger.info(f"Deleted expired audio file: {file_id}")
```

---

## Error Handling & Resilience Design

### 1. Circuit Breaker Pattern

#### 1.1 Service Health Monitoring
```python
class ServiceHealthMonitor:
    def __init__(self):
        self.circuit_breakers = {
            "rasa_nlu": CircuitBreaker(failure_threshold=5, timeout=30),
            "ollama_llm": CircuitBreaker(failure_threshold=3, timeout=60),
            "piper_tts": CircuitBreaker(failure_threshold=5, timeout=30),
            "google_calendar": CircuitBreaker(failure_threshold=10, timeout=120)
        }
    
    async def call_service(self, service_name: str, func: Callable, *args, **kwargs):
        """Call service through circuit breaker"""
        circuit_breaker = self.circuit_breakers[service_name]
        
        try:
            return await circuit_breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            # Service is down, use fallback
            return await self.get_fallback(service_name, *args, **kwargs)
    
    async def get_fallback(self, service_name: str, *args, **kwargs):
        """Provide fallback functionality when service is down"""
        fallback_handlers = {
            "rasa_nlu": self.regex_intent_fallback,
            "ollama_llm": self.simple_response_fallback,  
            "piper_tts": self.text_only_fallback,
            "google_calendar": self.local_calendar_fallback
        }
        
        handler = fallback_handlers.get(service_name)
        if handler:
            return await handler(*args, **kwargs)
        
        raise ServiceUnavailableError(f"Service {service_name} is unavailable and no fallback exists")
```

### 2. Graceful Degradation

#### 2.1 Fallback Processing Chain
```python
class FallbackProcessingChain:
    def __init__(self):
        self.processors = [
            ("rasa_nlu", self.process_with_rasa),
            ("ollama_llm", self.process_with_ollama),
            ("regex_rules", self.process_with_regex),
            ("default_response", self.process_with_default)
        ]
    
    async def process_input(self, text: str, context: Dict) -> ProcessingResult:
        """Try processors in order until one succeeds"""
        last_error = None
        
        for processor_name, processor_func in self.processors:
            try:
                result = await processor_func(text, context)
                if result.confidence > 0.3:  # Minimum acceptable confidence
                    logger.info(f"Successfully processed with {processor_name}")
                    return result
            except Exception as e:
                logger.warning(f"Processor {processor_name} failed: {e}")
                last_error = e
                continue
        
        # All processors failed
        logger.error(f"All processors failed. Last error: {last_error}")
        return ProcessingResult(
            intent="error",
            confidence=0.0,
            response="죄송합니다. 요청을 처리할 수 없습니다. 다시 시도해 주세요."
        )
```

---

## Deployment & Infrastructure Design

### 1. Container Architecture

#### 1.1 Docker Compose Configuration
```yaml
version: '3.8'

services:
  # Main API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mere_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # Rasa NLU Service
  rasa-nlu:
    image: rasa/rasa:3.6.0
    ports:
      - "5005:5005"
    volumes:
      - ./rasa-models:/app/models
      - ./rasa-config:/app
    command: run --enable-api --cors "*"

  # Ollama LLM Service  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_MODELS=llama3:8b,mistral:7b

  # Piper TTS Service
  piper-tts:
    build: ./piper-tts
    ports:
      - "5002:5002"
    volumes:
      - ./piper-models:/app/models

  # PostgreSQL Database
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=mere_db
      - POSTGRES_USER=mere_user
      - POSTGRES_PASSWORD=mere_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  # MinIO Object Storage
  minio:
    image: minio/minio
    ports:
      - "9000:9000" 
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"

  # Langfuse Observability
  langfuse-server:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://langfuse:password@postgres:5432/langfuse
      - NEXTAUTH_SECRET=your-secret-key
      - SALT=your-salt
    depends_on:
      - postgres

volumes:
  postgres-data:
  redis-data:
  minio-data:
  ollama-data:
```

### 2. Scaling Strategy

#### 2.1 Horizontal Scaling Design
```python
class LoadBalancer:
    def __init__(self):
        self.service_instances = {
            "rasa_nlu": ["rasa-1:5005", "rasa-2:5005"],
            "ollama_llm": ["ollama-1:11434", "ollama-2:11434"],
            "piper_tts": ["piper-1:5002", "piper-2:5002"]
        }
        self.health_checker = HealthChecker()
    
    async def get_available_instance(self, service_name: str) -> str:
        """Get available service instance using round-robin with health checks"""
        instances = self.service_instances[service_name]
        
        for instance in instances:
            if await self.health_checker.is_healthy(instance):
                return instance
        
        raise NoHealthyInstanceError(f"No healthy instances available for {service_name}")
```

---

## Development & Testing Strategy

### 1. Testing Architecture

#### 1.1 Test Pyramid Structure
```python
# Unit Tests
class TestNLUProcessor:
    async def test_intent_classification_accuracy(self):
        """Test intent classification with known inputs"""
        processor = NLUProcessor()
        
        test_cases = [
            ("내일 회의 잡아줘", "schedule_event"),
            ("쇼핑 리스트 기억해줘", "remember_memo"),
            ("할일 완료했어", "complete_todo")
        ]
        
        for input_text, expected_intent in test_cases:
            result = await processor.process(input_text, {})
            assert result.intent == expected_intent

# Integration Tests
class TestVoicePipeline:
    async def test_end_to_end_voice_processing(self):
        """Test complete voice processing pipeline"""
        pipeline = VoiceProcessingPipeline()
        
        # Mock audio input
        audio_data = self.load_test_audio("sample_voice_input.wav")
        
        # Process through pipeline
        result = await pipeline.process_audio(audio_data)
        
        assert result.success == True
        assert result.response_text is not None
        assert result.processing_time < 2000  # Under 2 seconds

# End-to-End Tests  
class TestUserScenarios:
    async def test_memo_creation_scenario(self):
        """Test complete memo creation user scenario"""
        # Simulate user saying: "내일 아침 우유 사는 거 기억시켜줘"
        audio_file = "test_audio/memo_creation.wav"
        
        # Send to WebSocket API
        result = await self.websocket_client.send_audio(audio_file)
        
        # Verify response
        assert "저장되었습니다" in result.response_text
        
        # Verify data persistence
        memos = await self.db_client.get_user_memos(self.test_user_id)
        assert any("우유" in memo.content for memo in memos)
```

### 2. Continuous Integration

#### 2.1 CI/CD Pipeline Configuration
```yaml
# .github/workflows/ci.yml
name: MERE AI Agent CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
        
      - name: Run DeepEval quality tests
        run: deepeval test run tests/quality/
      
      - name: Performance benchmarks
        run: python benchmarks/performance_test.py

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security scan
        run: |
          pip install bandit safety
          bandit -r src/
          safety check
  
  deploy:
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          docker-compose -f docker-compose.staging.yml up -d
          
      - name: Run smoke tests
        run: pytest tests/smoke/ -v
        
      - name: Deploy to production
        if: success()
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```

---

## Conclusion

이 설계 문서는 MERE AI Agent Phase 2 직접 구현을 위한 포괄적인 시스템 설계를 제시합니다. 핵심 특징:

### ✅ 설계 달성 목표
- **P50 <2초 응답시간** - 스트리밍 파이프라인과 병렬 처리
- **95% Intent 인식률** - Rasa + LLM 폴백 시스템  
- **완전 오픈소스** - 모든 컴포넌트 비용 0원
- **Production-Ready** - 확장성, 관찰성, 보안 고려

### 🛠️ 다음 단계
1. **Week 1**: 핵심 AI 파이프라인 구현 (STT→NLU→LangGraph→TTS)
2. **Week 2**: 비즈니스 로직 및 데이터 통합
3. **Week 3**: 관찰성 시스템 및 품질 평가 구축

이 설계를 바탕으로 고도화된 AI Agent를 3주 내에 구현할 수 있습니다.