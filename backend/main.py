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

from stt_service import get_stt_service
from nlu_service import get_nlu_service
from tts_service import get_tts_service
from business_services import get_intent_mapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MERE AI Agent",
    description="Voice-based personal assistant AI",
    version="1.0.0"
)

# CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Connection Manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_sessions: dict[str, dict] = {}  # Store user session data
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {
            "connected_at": str(datetime.now()),
            "last_activity": str(datetime.now()),
            "message_count": 0
        }
        logger.info(f"User {user_id} connected")
        
        # Send connection acknowledgment
        await self.send_message({
            "type": "connection_ack",
            "user_id": user_id,
            "server_time": str(datetime.now()),
            "message": "Successfully connected to MERE AI Agent"
        }, user_id)
    
    def disconnect(self, user_id: str):
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

# NLU + STT 통합 엔드포인트
@app.post("/api/voice/process")
async def process_voice_command(
    file: UploadFile = File(...),
    language: Optional[str] = "ko"
):
    """음성 파일을 받아서 STT + NLU 처리"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)