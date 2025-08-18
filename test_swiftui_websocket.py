#!/usr/bin/env python3
"""
iOS SwiftUI WebSocket Integration Simulation Test
이 스크립트는 iOS SwiftUI 앱이 백엔드와 통신하는 방식을 시뮬레이션합니다.
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwiftUISimulator:
    """iOS SwiftUI 앱의 WebSocket 통신을 시뮬레이션"""
    
    def __init__(self, user_id="swiftui-test-user"):
        self.user_id = user_id
        self.websocket = None
        self.message_log = []
        
    async def connect(self):
        """WebSocket 연결 (iOS WebSocketManager.connect() 시뮬레이션)"""
        try:
            uri = f"ws://localhost:8000/ws/{self.user_id}"
            print(f"🔗 Connecting to: {uri}")
            
            self.websocket = await websockets.connect(uri)
            
            # Connection ACK 대기
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'connection_ack':
                print(f"✅ Connected: {data.get('message')}")
                self.log_message(f"Connected: {data.get('message')}")
                return True
            else:
                print(f"❌ Unexpected response: {data}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from server")
    
    async def send_text_command(self, text):
        """텍스트 명령 전송 (iOS WebSocketManager.sendTextCommand() 시뮬레이션)"""
        message = {
            "type": "text_command",
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id
        }
        
        print(f"📤 Sending: {text}")
        await self.websocket.send(json.dumps(message))
        self.log_message(f"Sent: {text}")
        
        # 응답 대기
        return await self.wait_for_responses()
    
    async def send_voice_command(self, text, confidence=0.95):
        """음성 명령 전송 시뮬레이션"""
        message = {
            "type": "voice_command", 
            "text": text,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id
        }
        
        print(f"🎤 Sending voice: {text}")
        await self.websocket.send(json.dumps(message))
        self.log_message(f"Voice sent: {text}")
        
        return await self.wait_for_responses()
    
    async def wait_for_responses(self, timeout=10):
        """서버 응답 대기 (iOS에서 NotificationCenter로 처리하는 부분 시뮬레이션)"""
        responses = []
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                data = json.loads(response)
                responses.append(data)
                
                # iOS SwiftUI에서 처리하는 것처럼 메시지 타입별 처리
                await self.handle_message(data)
                
                # text_response나 ai_response가 오면 완료
                if data.get('type') in ['text_response', 'ai_response']:
                    break
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Error receiving: {e}")
                break
        
        return responses
    
    async def handle_message(self, data):
        """메시지 처리 (iOS NotificationCenter 핸들러 시뮬레이션)"""
        message_type = data.get('type')
        
        if message_type == 'processing_status':
            stage = data.get('stage', '')
            message = data.get('message', '')
            print(f"   ⚡ Processing: {message}")
            self.log_message(f"Processing [{stage}]: {message}")
            
        elif message_type == 'text_response':
            nlu = data.get('nlu', {})
            business = data.get('business', {})
            response = data.get('response', '')
            
            print(f"   🧠 Intent: {nlu.get('intent')} (confidence: {nlu.get('confidence', 0):.2f})")
            print(f"   💼 Business: {business.get('action')} (success: {business.get('success')})")
            print(f"   💬 Response: {response}")
            
            self.log_message(f"Final response: {response}")
            
            # iOS에서 TTS 재생 시뮬레이션
            if response:
                print(f"   🔊 [iOS] Playing TTS audio for: {response[:30]}...")
        
        elif message_type == 'ai_response':
            print(f"   🤖 AI Response received")
            self.log_message("AI Response received")
            
        elif message_type == 'error':
            error_msg = data.get('message', 'Unknown error')
            print(f"   ❌ Error: {error_msg}")
            self.log_message(f"Error: {error_msg}")
    
    def log_message(self, message):
        """메시지 로깅 (iOS MessageLog 시뮬레이션)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_log.append(f"[{timestamp}] {message}")
        
        # 최근 20개 메시지만 유지 (iOS 앱처럼)
        if len(self.message_log) > 20:
            self.message_log = self.message_log[-20:]
    
    def print_message_log(self):
        """메시지 로그 출력 (iOS UI 시뮬레이션)"""
        print("\n📱 iOS Message Log:")
        print("-" * 40)
        for msg in self.message_log[-10:]:  # 최근 10개만
            print(f"   {msg}")

async def test_ios_swiftui_scenarios():
    """iOS SwiftUI 앱 시나리오 테스트"""
    print("📱 iOS SwiftUI WebSocket Integration Test")
    print("=" * 50)
    
    simulator = SwiftUISimulator()
    
    try:
        # 연결
        if not await simulator.connect():
            print("❌ Connection failed, aborting tests")
            return
        
        # 시나리오 1: 기본 메모 생성 (iOS WebSocketTestView의 텍스트 테스트와 유사)
        print(f"\n🧪 Scenario 1: Create Memo")
        await simulator.send_text_command("내일 우유 사는 거 기억해줘")
        
        await asyncio.sleep(1)
        
        # 시나리오 2: 할일 생성
        print(f"\n🧪 Scenario 2: Create Todo")
        await simulator.send_text_command("장보기 할일로 추가해줘")
        
        await asyncio.sleep(1)
        
        # 시나리오 3: 메모 조회
        print(f"\n🧪 Scenario 3: Query Memos")
        await simulator.send_text_command("메모 뭐 있는지 보여줘")
        
        await asyncio.sleep(1)
        
        # 시나리오 4: 음성 명령 시뮬레이션 (iOS PTT 버튼 시뮬레이션)
        print(f"\n🧪 Scenario 4: Voice Command (PTT Simulation)")
        await simulator.send_voice_command("할일 목록 보여줘", confidence=0.92)
        
        await asyncio.sleep(1)
        
        # 시나리오 5: 인사
        print(f"\n🧪 Scenario 5: Greeting")
        await simulator.send_text_command("안녕하세요")
        
        # iOS 앱의 메시지 로그 시뮬레이션
        simulator.print_message_log()
        
        print(f"\n✅ All iOS SwiftUI scenarios completed successfully!")
        print(f"💡 The iOS app would now be ready for:")
        print(f"   - Audio recording with AVFoundation")
        print(f"   - Real-time WebSocket communication")
        print(f"   - TTS audio playback")
        print(f"   - SwiftUI conversation history")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await simulator.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ios_swiftui_scenarios())