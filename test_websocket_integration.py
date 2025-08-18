#!/usr/bin/env python3
"""
WebSocket Integration 테스트 스크립트
Day 5 Task 5.1 & 5.2: WebSocket 통신 테스트
"""
import asyncio
import websockets
import json
import aiohttp
from datetime import datetime

# WebSocket 서버 정보
WEBSOCKET_URL = "ws://localhost:8000/ws/test-user"
HTTP_BASE_URL = "http://localhost:8000"

async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    print("🔌 WebSocket 연결 테스트")
    print("-" * 30)
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("   ✅ WebSocket 연결 성공")
            
            # Connection acknowledgment 수신 대기
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   📨 Connection ACK: {data.get('message', '')}")
            
            if data.get('type') == 'connection_ack':
                print("   ✅ Connection acknowledgment 수신 성공")
                return True
            else:
                print("   ❌ 예상하지 못한 응답 타입")
                return False
                
    except Exception as e:
        print(f"   ❌ WebSocket 연결 실패: {e}")
        return False

async def test_ping_pong():
    """Ping-Pong 테스트"""
    print("\n🏓 Ping-Pong 테스트")
    print("-" * 20)
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Connection ACK 수신
            await websocket.recv()
            
            # Ping 메시지 전송
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "user_id": "test-user"
            }
            
            print(f"   📤 Ping 전송: {ping_message['timestamp']}")
            await websocket.send(json.dumps(ping_message))
            
            # Pong 응답 수신
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'pong':
                print(f"   📨 Pong 수신: {data.get('timestamp', '')}")
                print("   ✅ Ping-Pong 테스트 성공")
                return True
            else:
                print(f"   ❌ 예상하지 못한 응답: {data}")
                return False
                
    except Exception as e:
        print(f"   ❌ Ping-Pong 테스트 실패: {e}")
        return False

async def test_text_command():
    """텍스트 명령 테스트"""
    print("\n💬 텍스트 명령 테스트")
    print("-" * 20)
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Connection ACK 수신
            await websocket.recv()
            
            # 텍스트 명령 전송
            text_command = {
                "type": "text_command",
                "text": "내일 우유 사는 거 기억해줘",
                "timestamp": datetime.now().isoformat(),
                "user_id": "test-user"
            }
            
            print(f"   📤 텍스트 명령: '{text_command['text']}'")
            await websocket.send(json.dumps(text_command))
            
            # Processing status 수신
            processing_response = await websocket.recv()
            processing_data = json.loads(processing_response)
            
            if processing_data.get('type') == 'processing_status':
                print(f"   ⚡ 처리 중: {processing_data.get('message', '')}")
            
            # 최종 응답 수신
            final_response = await websocket.recv()
            final_data = json.loads(final_response)
            
            if final_data.get('type') == 'text_response':
                print(f"   📨 응답: {final_data.get('response', '')}")
                
                # NLU 결과 출력
                nlu = final_data.get('nlu', {})
                print(f"   🧠 Intent: {nlu.get('intent', '')} (confidence: {nlu.get('confidence', 0):.2f})")
                print("   ✅ 텍스트 명령 테스트 성공")
                return True
            else:
                print(f"   ❌ 예상하지 못한 응답 타입: {final_data.get('type')}")
                return False
                
    except Exception as e:
        print(f"   ❌ 텍스트 명령 테스트 실패: {e}")
        return False

async def test_voice_command():
    """음성 명령 테스트 (텍스트 기반)"""
    print("\n🎤 음성 명령 테스트")
    print("-" * 20)
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Connection ACK 수신
            await websocket.recv()
            
            # 음성 명령 전송 (텍스트 포함)
            voice_command = {
                "type": "voice_command",
                "text": "오늘 할일 목록 보여줘",
                "confidence": 0.95,
                "timestamp": datetime.now().isoformat(),
                "user_id": "test-user"
            }
            
            print(f"   📤 음성 명령: '{voice_command['text']}'")
            print(f"   🎯 신뢰도: {voice_command['confidence']}")
            await websocket.send(json.dumps(voice_command))
            
            # Processing status 수신
            processing_response = await websocket.recv()
            processing_data = json.loads(processing_response)
            
            if processing_data.get('type') == 'processing_status':
                print(f"   ⚡ 처리 중: {processing_data.get('message', '')}")
            
            # AI 응답 수신
            ai_response = await websocket.recv()
            ai_data = json.loads(ai_response)
            
            if ai_data.get('type') == 'ai_response':
                # STT 결과
                stt = ai_data.get('stt', {})
                print(f"   🎤 STT: '{stt.get('text', '')}' (confidence: {stt.get('confidence', 0):.2f})")
                
                # NLU 결과
                nlu = ai_data.get('nlu', {})
                print(f"   🧠 NLU: {nlu.get('intent', '')} (confidence: {nlu.get('confidence', 0):.2f})")
                
                # 응답 결과
                response = ai_data.get('response', {})
                print(f"   💬 응답: {response.get('text', '')}")
                
                # TTS 오디오 확인
                if response.get('audio_base64'):
                    print(f"   🎵 TTS Audio: {len(response.get('audio_base64', ''))} chars (Base64)")
                else:
                    print("   ⚠️  TTS 오디오 없음")
                
                print("   ✅ 음성 명령 테스트 성공")
                return True
            else:
                print(f"   ❌ 예상하지 못한 응답 타입: {ai_data.get('type')}")
                return False
                
    except Exception as e:
        print(f"   ❌ 음성 명령 테스트 실패: {e}")
        return False

async def test_status_request():
    """서버 상태 요청 테스트"""
    print("\n📊 서버 상태 요청 테스트")
    print("-" * 25)
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Connection ACK 수신
            await websocket.recv()
            
            # 상태 요청
            status_request = {
                "type": "status_request",
                "timestamp": datetime.now().isoformat(),
                "user_id": "test-user"
            }
            
            print("   📤 서버 상태 요청")
            await websocket.send(json.dumps(status_request))
            
            # 상태 응답 수신
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'status_response':
                session = data.get('session', {})
                print(f"   📨 세션 정보:")
                print(f"      연결 시간: {session.get('connected_at', '')}")
                print(f"      마지막 활동: {session.get('last_activity', '')}")
                print(f"      메시지 수: {session.get('message_count', 0)}")
                print(f"   🕐 서버 시간: {data.get('server_time', '')}")
                print("   ✅ 상태 요청 테스트 성공")
                return True
            else:
                print(f"   ❌ 예상하지 못한 응답 타입: {data.get('type')}")
                return False
                
    except Exception as e:
        print(f"   ❌ 상태 요청 테스트 실패: {e}")
        return False

async def test_websocket_status_api():
    """WebSocket 상태 API 테스트"""
    print("\n🌐 WebSocket 상태 API 테스트")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{HTTP_BASE_URL}/api/websocket/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   📊 활성 연결: {data.get('active_connections', 0)}")
                    print(f"   👥 연결된 사용자: {data.get('connected_users', [])}")
                    print(f"   🕐 서버 시간: {data.get('server_time', '')}")
                    print("   ✅ WebSocket 상태 API 테스트 성공")
                    return True
                else:
                    print(f"   ❌ HTTP 오류: {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ API 테스트 실패: {e}")
        return False

async def main():
    """메인 WebSocket 통합 테스트"""
    print("🚀 WebSocket Integration 테스트 시작")
    print("=" * 50)
    
    test_results = []
    
    # 1. WebSocket 연결 테스트
    connection_ok = await test_websocket_connection()
    test_results.append(("WebSocket Connection", connection_ok))
    
    if not connection_ok:
        print("\n❌ WebSocket 연결 실패 - 후속 테스트 건너뛰기")
        return
    
    # 2. Ping-Pong 테스트
    ping_ok = await test_ping_pong()
    test_results.append(("Ping-Pong", ping_ok))
    
    # 3. 텍스트 명령 테스트
    text_ok = await test_text_command()
    test_results.append(("Text Command", text_ok))
    
    # 4. 음성 명령 테스트
    voice_ok = await test_voice_command()
    test_results.append(("Voice Command", voice_ok))
    
    # 5. 상태 요청 테스트
    status_ok = await test_status_request()
    test_results.append(("Status Request", status_ok))
    
    # 6. WebSocket 상태 API 테스트
    api_ok = await test_websocket_status_api()
    test_results.append(("WebSocket Status API", api_ok))
    
    # 결과 요약
    print("\n📊 테스트 결과 요약")
    print("=" * 30)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print(f"\n🎉 모든 WebSocket 통합 테스트 통과!")
        print(f"\n💡 Day 5 Task 5.1 & 5.2 완료:")
        print(f"   ✅ 백엔드 WebSocket 서버 메시지 프로토콜 구현")
        print(f"   ✅ iOS WebSocket 클라이언트 통합 준비 완료")
        print(f"   ✅ 실시간 양방향 통신 검증")
    else:
        print(f"\n⚠️  일부 테스트 실패 - 문제를 확인하고 다시 시도하세요")

if __name__ == "__main__":
    asyncio.run(main())