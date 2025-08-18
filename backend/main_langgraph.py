"""
MERE AI Agent - Main FastAPI Application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import tempfile
import os
import json
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime

from mere.services.stt_service import get_stt_service
from mere.services.nlu_service import get_nlu_service
from mere.services.enhanced_nlu_service import get_enhanced_nlu_service
from mere.services.tts_service import get_tts_service
from mere.core.business_services import get_intent_mapper
from mere.core.conversation_state import get_state_manager, ConversationState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MERE AI Agent",
    description="Voice-based personal assistant AI with LangGraph State Management",
    version="2.0.0"
)

# CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Connection Manager for WebSocket with LangGraph State
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_sessions: dict[str, dict] = {}  # Store user session data
        self.state_manager = get_state_manager()
        self.enhanced_nlu = get_enhanced_nlu_service()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Initialize conversation state
        conversation_id = self.state_manager.start_conversation(user_id)
        
        self.user_sessions[user_id] = {
            "connected_at": str(datetime.now()),
            "last_activity": str(datetime.now()),
            "message_count": 0,
            "conversation_id": conversation_id,
            "conversation_state": ConversationState.PARSING.value
        }
        logger.info(f"User {user_id} connected with conversation {conversation_id}")
        
        # Send connection acknowledgment with state info
        await self.send_message({
            "type": "connection_ack",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "server_time": str(datetime.now()),
            "message": "Successfully connected to MERE AI Agent",
            "features": ["langgraph_state_management", "context_awareness", "interruption_handling"]
        }, user_id)
    
    def disconnect(self, user_id: str):
        # End conversation state
        if user_id in self.user_sessions:
            conversation_id = self.user_sessions[user_id].get("conversation_id")
            if conversation_id:
                self.state_manager.end_conversation(conversation_id)
                logger.info(f"Ended conversation {conversation_id} for user {user_id}")
        
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"User {user_id} disconnected")
    
    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                # Update user activity
                if user_id in self.user_sessions:
                    self.user_sessions[user_id]["last_activity"] = str(datetime.now())
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_message(self, message: dict):
        """Send message to all connected users"""
        disconnected_users = []
        for user_id in self.active_connections:
            try:
                await self.send_message(message, user_id)
            except:
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def get_active_users(self) -> list[str]:
        return list(self.active_connections.keys())
    
    def get_user_session(self, user_id: str) -> dict:
        return self.user_sessions.get(user_id, {})

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "MERE AI Agent API Server", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mere-ai-agent"}

@app.get("/api/websocket/status")
async def websocket_status():
    """Get WebSocket connection status"""
    active_users = manager.get_active_users()
    return JSONResponse({
        "active_connections": len(active_users),
        "connected_users": active_users,
        "server_time": str(datetime.now())
    })

# STT API Endpoints
@app.post("/api/stt/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = "ko"
):
    """오디오 파일을 텍스트로 변환"""
    try:
        # 지원하는 오디오 포맷 확인
        stt_service = get_stt_service()
        supported_formats = stt_service.get_supported_formats()
        
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. Supported: {supported_formats}"
            )
        
        # 임시 파일에 저장
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # STT 처리
            text, confidence = await stt_service.transcribe_audio_file(
                temp_path, language=language
            )
            
            return JSONResponse({
                "success": True,
                "text": text,
                "confidence": confidence,
                "language": language,
                "filename": file.filename
            })
            
        finally:
            # 임시 파일 삭제
            Path(temp_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/stt/transcribe-bytes")
async def transcribe_audio_bytes(
    audio_data: bytes,
    sample_rate: int = 16000,
    language: Optional[str] = "ko"
):
    """바이트 데이터를 직접 텍스트로 변환"""
    try:
        stt_service = get_stt_service()
        
        text, confidence = await stt_service.transcribe_audio_data(
            audio_data, sample_rate=sample_rate, language=language
        )
        
        return JSONResponse({
            "success": True,
            "text": text,
            "confidence": confidence,
            "language": language,
            "sample_rate": sample_rate
        })
        
    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/api/stt/info")
async def get_stt_info():
    """STT 서비스 정보 조회"""
    stt_service = get_stt_service()
    return JSONResponse(stt_service.get_model_info())

# TTS API Endpoints
@app.post("/api/tts/synthesize")
async def synthesize_text_to_speech(
    text: str,
    format: str = "wav"
):
    """텍스트를 음성으로 변환"""
    try:
        tts_service = get_tts_service()
        
        # 오디오 데이터 생성
        audio_bytes = await tts_service.synthesize_text(text)
        
        if isinstance(audio_bytes, str):
            # 파일 경로인 경우 읽기
            with open(audio_bytes, 'rb') as f:
                audio_bytes = f.read()
            # 임시 파일 삭제
            Path(audio_bytes).unlink(missing_ok=True)
        
        # 오디오 데이터 응답
        from fastapi.responses import Response
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_output.{format}",
                "Content-Length": str(len(audio_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

@app.get("/api/tts/info")
async def get_tts_info():
    """TTS 서비스 정보 조회"""
    tts_service = get_tts_service()
    return JSONResponse(tts_service.get_voice_info())

@app.get("/api/tts/stream/{text}")
async def stream_tts(text: str):
    """스트리밍 TTS"""
    try:
        tts_service = get_tts_service()
        
        from fastapi.responses import StreamingResponse
        
        async def generate_audio_stream():
            async for chunk in tts_service.synthesize_streaming(text, chunk_size=1024):
                yield chunk
        
        return StreamingResponse(
            generate_audio_stream(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=tts_stream.wav"}
        )
        
    except Exception as e:
        logger.error(f"TTS streaming failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")

# Enhanced Voice Processing with LangGraph State Management
@app.post("/api/voice/process_stateful")
async def process_voice_command_stateful(
    file: UploadFile = File(...),
    user_id: str = "default_user",
    conversation_id: Optional[str] = None,
    language: Optional[str] = "ko"
):
    """음성 파일을 LangGraph 상태 관리로 처리"""
    try:
        # Services
        stt_service = get_stt_service()
        enhanced_nlu = get_enhanced_nlu_service()
        tts_service = get_tts_service()
        intent_mapper = get_intent_mapper()
        
        # STT 처리
        supported_formats = stt_service.get_supported_formats()
        file_ext = Path(file.filename or "").suffix.lower()
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. Supported: {supported_formats}"
            )
        
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # STT processing
            start_time = datetime.now()
            stt_result = await stt_service.transcribe_audio(tmp_path, language=language)
            text = stt_result.get("text", "").strip()
            
            if not text:
                return JSONResponse({
                    "success": False,
                    "error": "No speech detected",
                    "processing_time": (datetime.now() - start_time).total_seconds()
                })
            
            # Enhanced NLU with conversation context
            contextual_nlu = enhanced_nlu.process_with_context(
                text=text,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Get conversation state
            state_manager = get_state_manager()
            context = state_manager.get_conversation(contextual_nlu.conversation_id)
            
            # Business logic execution (if in execution state)
            business_result = None
            if context and context.current_state == ConversationState.EXECUTION:
                business_result = await intent_mapper.execute_intent(
                    intent=contextual_nlu.intent.name,
                    entities=contextual_nlu.entities,
                    user_id=user_id
                )
            
            # Generate response based on conversation state
            response_text = _generate_state_aware_response(context, contextual_nlu, business_result)
            
            # TTS synthesis
            tts_audio = await tts_service.synthesize_text(response_text)
            audio_base64 = base64.b64encode(tts_audio).decode('utf-8') if tts_audio else None
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return JSONResponse({
                "success": True,
                "conversation_id": contextual_nlu.conversation_id,
                "conversation_state": context.current_state.value if context else "unknown",
                "stt": {
                    "text": text,
                    "confidence": stt_result.get("confidence", 1.0)
                },
                "nlu": {
                    "intent": contextual_nlu.intent.name,
                    "confidence": contextual_nlu.confidence,
                    "entities": contextual_nlu.entities,
                    "context_entities": contextual_nlu.context_entities,
                    "requires_confirmation": contextual_nlu.requires_confirmation,
                    "previous_intent": contextual_nlu.previous_intent
                },
                "business": business_result,
                "response": {
                    "text": response_text,
                    "hasAudio": audio_base64 is not None,
                    "audioBase64": audio_base64
                },
                "processing_time": processing_time,
                "state_info": {
                    "current_state": context.current_state.value if context else "unknown",
                    "state_transitions": _get_possible_transitions(context)
                }
            })
            
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Enhanced voice processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

def _generate_state_aware_response(context, nlu_result, business_result):
    """Generate response based on conversation state"""
    if not context:
        return "처리 중 오류가 발생했습니다."
    
    state = context.current_state
    
    if state == ConversationState.CONFIRMATION:
        return f"'{context.intent}' 작업을 실행하시겠습니까? (예/아니요로 답해주세요)"
    
    elif state == ConversationState.VALIDATION:
        missing_entities = _get_missing_entities(context.intent, context.entities)
        if missing_entities:
            return f"추가 정보가 필요합니다: {', '.join(missing_entities)}"
    
    elif state == ConversationState.INTERRUPTED:
        return f"작업이 취소되었습니다. ({context.interruption_reason})"
    
    elif state == ConversationState.RESPONSE and business_result:
        if business_result.get("success"):
            return business_result.get("response", "작업이 완료되었습니다.")
        else:
            return f"작업 실행 중 오류가 발생했습니다: {business_result.get('error', '알 수 없는 오류')}"
    
    return "요청을 처리했습니다."

def _get_possible_transitions(context):
    """Get possible state transitions from current state"""
    if not context:
        return []
    
    transitions = {
        ConversationState.PARSING: ["validation", "interrupted", "end"],
        ConversationState.VALIDATION: ["confirmation", "execution", "interrupted"],
        ConversationState.CONFIRMATION: ["execution", "validation", "interrupted", "end"],
        ConversationState.EXECUTION: ["response"],
        ConversationState.RESPONSE: ["end"],
        ConversationState.INTERRUPTED: ["end"]
    }
    
    return transitions.get(context.current_state, [])

def _get_missing_entities(intent, entities):
    """Get list of missing required entities for intent"""
    # This would be expanded based on intent requirements
    required_entities = {
        "create_memo": ["content"],
        "create_todo": ["task"],
        "create_event": ["title", "datetime"],
        "delete_memo": ["memo_id"],
        "update_todo": ["todo_id", "status"]
    }
    
    required = required_entities.get(intent, [])
    missing = [req for req in required if req not in entities]
    return missing

# Legacy endpoint (keeping for backward compatibility)
@app.post("/api/voice/process")
async def process_voice_command(
    file: UploadFile = File(...),
    language: Optional[str] = "ko"
):
    """음성 파일을 받아서 STT + NLU 처리 (Legacy)"""
    try:
        # STT 처리
        stt_service = get_stt_service()
        nlu_service = get_nlu_service()
        
        # 지원 포맷 확인
        supported_formats = stt_service.get_supported_formats()
        file_ext = Path(file.filename or "").suffix.lower()
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )
        
        # 임시 파일에 저장
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # 1. STT 처리
            text, stt_confidence = await stt_service.transcribe_audio_file(
                temp_path, language=language
            )
            
            if not text:
                return JSONResponse({
                    "success": False,
                    "error": "No speech detected",
                    "stt_confidence": stt_confidence
                })
            
            # 2. NLU 처리
            nlu_result = await nlu_service.analyze_intent(text)
            
            # 3. 응답 템플릿 생성
            response_text = nlu_service.get_response_template(
                nlu_result.intent.name,
                nlu_result.entities
            )
            
            # 4. TTS 오디오 생성 (선택적)
            tts_service = get_tts_service()
            try:
                response_audio = await tts_service.synthesize_text(response_text)
                
                # 바이트 데이터를 Base64로 인코딩
                import base64
                if isinstance(response_audio, bytes):
                    audio_base64 = base64.b64encode(response_audio).decode('utf-8')
                else:
                    # 파일 경로인 경우
                    with open(response_audio, 'rb') as f:
                        audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    # 임시 파일 삭제
                    Path(response_audio).unlink(missing_ok=True)
                
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
                audio_base64 = None
            
            return JSONResponse({
                "success": True,
                "stt": {
                    "text": text,
                    "confidence": stt_confidence,
                    "language": language
                },
                "nlu": {
                    "intent": nlu_result.intent.name,
                    "confidence": nlu_result.confidence,
                    "entities": nlu_result.entities
                },
                "response": {
                    "text": response_text,
                    "audio_base64": audio_base64
                },
                "filename": file.filename
            })
            
        finally:
            # 임시 파일 삭제
            Path(temp_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Voice processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get('type', 'unknown')
            
            # Update session message count
            if user_id in manager.user_sessions:
                manager.user_sessions[user_id]["message_count"] += 1
            
            await handle_websocket_message(user_id, message_type, data)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Server error: {str(e)}",
            "timestamp": str(datetime.now())
        }, user_id)

async def handle_websocket_message(user_id: str, message_type: str, data: dict):
    """Handle different types of WebSocket messages"""
    
    if message_type == "voice_command":
        await handle_voice_command(user_id, data)
        
    elif message_type == "text_command":
        await handle_text_command(user_id, data)
        
    elif message_type == "ping":
        await manager.send_message({
            "type": "pong",
            "timestamp": str(datetime.now()),
            "server_status": "healthy"
        }, user_id)
        
    elif message_type == "status_request":
        session_info = manager.get_user_session(user_id)
        await manager.send_message({
            "type": "status_response",
            "user_id": user_id,
            "session": session_info,
            "server_time": str(datetime.now())
        }, user_id)
        
    else:
        await manager.send_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": str(datetime.now())
        }, user_id)

async def handle_voice_command(user_id: str, data: dict):
    """Process voice command received via WebSocket"""
    try:
        # Extract voice command data
        text = data.get('text', '')
        confidence = data.get('confidence', 0.0)
        audio_base64 = data.get('audio_base64')
        
        if not text and not audio_base64:
            await manager.send_message({
                "type": "error",
                "message": "Voice command requires either text or audio_base64",
                "timestamp": str(datetime.now())
            }, user_id)
            return
        
        # Send processing status
        await manager.send_message({
            "type": "processing_status",
            "stage": "nlu",
            "message": "Processing voice command...",
            "timestamp": str(datetime.now())
        }, user_id)
        
        # Process with NLU if we have text
        if text:
            nlu_service = get_nlu_service()
            nlu_result = await nlu_service.analyze_intent(text)
            
            # Execute business logic
            intent_mapper = get_intent_mapper()
            business_result = await intent_mapper.execute_intent(user_id, nlu_result)
            
            # Use business result message or fallback to template
            if business_result and business_result.get("success"):
                response_text = business_result.get("message", "처리가 완료되었습니다.")
            else:
                response_text = business_result.get("message", "처리 중 오류가 발생했습니다.")
            
            # Generate TTS audio
            tts_service = get_tts_service()
            try:
                response_audio = await tts_service.synthesize_text(response_text)
                
                # Convert to base64
                if isinstance(response_audio, bytes):
                    audio_base64 = base64.b64encode(response_audio).decode('utf-8')
                else:
                    with open(response_audio, 'rb') as f:
                        audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    Path(response_audio).unlink(missing_ok=True)
                    
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
                audio_base64 = None
            
            # Send AI response with business result
            await manager.send_message({
                "type": "ai_response",
                "stt": {
                    "text": text,
                    "confidence": confidence
                },
                "nlu": {
                    "intent": nlu_result.intent.name,
                    "confidence": nlu_result.confidence,
                    "entities": nlu_result.entities
                },
                "business": {
                    "success": business_result.get("success", False),
                    "action": business_result.get("action", "unknown"),
                    "data": business_result.get("data")
                },
                "response": {
                    "text": response_text,
                    "audio_base64": audio_base64
                },
                "timestamp": str(datetime.now())
            }, user_id)
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Voice command processing failed: {str(e)}",
            "timestamp": str(datetime.now())
        }, user_id)

async def handle_text_command(user_id: str, data: dict):
    """Process text command received via WebSocket"""
    try:
        text = data.get('text', '').strip()
        
        if not text:
            await manager.send_message({
                "type": "error",
                "message": "Text command cannot be empty",
                "timestamp": str(datetime.now())
            }, user_id)
            return
            
        # Send processing status
        await manager.send_message({
            "type": "processing_status",
            "stage": "nlu",
            "message": f"Processing: {text}",
            "timestamp": str(datetime.now())
        }, user_id)
        
        # Process with NLU
        nlu_service = get_nlu_service()
        nlu_result = await nlu_service.analyze_intent(text)
        
        # Execute business logic
        intent_mapper = get_intent_mapper()
        business_result = await intent_mapper.execute_intent(user_id, nlu_result)
        
        # Use business result message or fallback to template
        if business_result and business_result.get("success"):
            response_text = business_result.get("message", "처리가 완료되었습니다.")
        else:
            response_text = business_result.get("message", "처리 중 오류가 발생했습니다.")
        
        # Send response with business result
        await manager.send_message({
            "type": "text_response",
            "input": text,
            "nlu": {
                "intent": nlu_result.intent.name,
                "confidence": nlu_result.confidence,
                "entities": nlu_result.entities
            },
            "business": {
                "success": business_result.get("success", False),
                "action": business_result.get("action", "unknown"),
                "data": business_result.get("data")
            },
            "response": response_text,
            "timestamp": str(datetime.now())
        }, user_id)
        
    except Exception as e:
        logger.error(f"Text command processing failed: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Text command processing failed: {str(e)}",
            "timestamp": str(datetime.now())
        }, user_id)

# Health and Status Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check core services
        state_manager = get_state_manager()
        active_conversations = len(state_manager.get_active_conversations())
        
        return JSONResponse({
            "status": "healthy",
            "version": "2.0.0",
            "features": [
                "langgraph_state_management",
                "context_aware_nlu", 
                "conversation_tracking",
                "interruption_handling"
            ],
            "active_conversations": active_conversations,
            "timestamp": str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": str(datetime.now())
            }
        )

@app.get("/api/status/conversations")
async def get_conversation_status():
    """Get conversation status information"""
    try:
        state_manager = get_state_manager()
        conversations = state_manager.get_active_conversations()
        
        return JSONResponse({
            "active_conversations": len(conversations),
            "conversations": [
                {
                    "conversation_id": conv_id,
                    "user_id": context.user_id,
                    "current_state": context.current_state.value,
                    "intent": context.intent,
                    "confidence": context.confidence,
                    "duration": (datetime.now() - context.created_at).total_seconds()
                }
                for conv_id, context in conversations.items()
            ]
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)