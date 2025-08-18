#!/usr/bin/env python3
"""
iOS 앱과 백엔드 통합 테스트 스크립트
실제 iOS 시뮬레이터나 디바이스에서 테스트하기 전에 백엔드 준비 상태 확인
"""
import asyncio
import aiohttp
import json
import tempfile
import os
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 기본 URL
BASE_URL = "http://localhost:8000"

def create_test_audio_m4a(filename: str = "test_ios.m4a", duration: int = 2):
    """iOS에서 사용하는 M4A 포맷 테스트 파일 생성"""
    # M4A는 복잡한 포맷이므로 WAV로 대체하여 테스트
    sample_rate = 16000
    num_samples = sample_rate * duration
    
    # WAV 헤더 (M4A 대신 WAV 사용)
    header = b'RIFF'
    header += (36 + num_samples * 2).to_bytes(4, 'little')
    header += b'WAVE'
    header += b'fmt '
    header += (16).to_bytes(4, 'little')
    header += (1).to_bytes(2, 'little')   # PCM
    header += (1).to_bytes(2, 'little')   # Mono
    header += sample_rate.to_bytes(4, 'little')
    header += (sample_rate * 2).to_bytes(4, 'little')
    header += (2).to_bytes(2, 'little')
    header += (16).to_bytes(2, 'little')
    header += b'data'
    header += (num_samples * 2).to_bytes(4, 'little')
    
    # 톤 생성 (440Hz A음)
    import math
    audio_data = bytearray()
    for i in range(num_samples):
        sample = int(8000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        audio_data.extend(sample.to_bytes(2, 'little', signed=True))
    
    full_data = header + audio_data
    
    # .wav 확장자로 저장 (백엔드에서 .wav도 지원함)
    wav_filename = filename.replace('.m4a', '.wav')
    with open(wav_filename, 'wb') as f:
        f.write(full_data)
    
    return wav_filename

async def test_backend_health():
    """백엔드 헬스체크"""
    print("🏥 백엔드 헬스체크")
    print("-" * 30)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 백엔드 상태: {data.get('status')}")
                    return True
                else:
                    print(f"   ❌ 백엔드 응답 오류: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 백엔드 연결 실패: {e}")
            return False

async def test_ios_audio_upload():
    """iOS 앱에서 업로드하는 것과 같은 방식으로 테스트"""
    print("\n📱 iOS 스타일 오디오 업로드 테스트")
    print("-" * 40)
    
    # iOS에서 생성하는 것과 유사한 오디오 파일 생성
    test_file = create_test_audio_m4a("ios_recording.m4a")
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(test_file, 'rb') as f:
                # iOS에서 전송하는 것과 같은 multipart 폼 생성
                data = aiohttp.FormData()
                data.add_field('file', f, filename='recording.wav', content_type='audio/wav')
                data.add_field('language', 'ko')
                
                print(f"   📤 파일 업로드: {test_file}")
                
                async with session.post(f"{BASE_URL}/api/voice/process", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print(f"   ✅ 처리 성공!")
                        print(f"   🎤 STT: '{result.get('stt', {}).get('text', '')}'")
                        print(f"   🧠 NLU: {result.get('nlu', {}).get('intent', '')} ({result.get('nlu', {}).get('confidence', 0):.2f})")
                        print(f"   💬 응답: '{result.get('response', '')}'")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 업로드 실패: {response.status}")
                        print(f"   Error: {error_text}")
                        return False
                        
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False
    finally:
        # 테스트 파일 삭제
        if os.path.exists(test_file):
            os.unlink(test_file)

async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    print("\n🔌 WebSocket 연결 테스트")
    print("-" * 30)
    
    try:
        import websockets
        
        uri = f"ws://localhost:8000/ws/ios-test-user"
        print(f"   🔗 연결 시도: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket 연결 성공!")
            
            # 테스트 메시지 전송
            test_message = {
                "type": "voice_command",
                "text": "안녕하세요",
                "confidence": 0.95,
                "user_id": "ios-test-user"
            }
            
            await websocket.send(json.dumps(test_message))
            print("   📤 메시지 전송 완료")
            
            # 응답 대기 (짧은 시간)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"   📥 서버 응답: {response}")
            except asyncio.TimeoutError:
                print("   ⏱️  서버 응답 타임아웃 (정상)")
            
            return True
            
    except ImportError:
        print("   ⚠️  websockets 패키지 없음 - pip install websockets")
        return False
    except Exception as e:
        print(f"   ❌ WebSocket 연결 실패: {e}")
        return False

async def test_stt_only():
    """STT만 별도 테스트"""
    print("\n🎙️  STT 전용 테스트")
    print("-" * 25)
    
    test_file = create_test_audio_m4a("stt_test.m4a")
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='stt_test.wav', content_type='audio/wav')
                data.add_field('language', 'ko')
                
                async with session.post(f"{BASE_URL}/api/stt/transcribe", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ STT 결과: '{result.get('text', '')}'")
                        print(f"   📊 신뢰도: {result.get('confidence', 0):.2f}")
                        return True
                    else:
                        print(f"   ❌ STT 실패: {response.status}")
                        return False
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)

async def main():
    """메인 통합 테스트"""
    print("🚀 iOS-백엔드 통합 테스트 시작")
    print("=" * 50)
    
    test_results = []
    
    # 1. 백엔드 헬스체크
    health_ok = await test_backend_health()
    test_results.append(("Backend Health", health_ok))
    
    if not health_ok:
        print("\n❌ 백엔드가 실행되지 않았습니다!")
        print("💡 서버를 먼저 실행하세요: python -m backend.main")
        return
    
    # 2. STT 전용 테스트
    stt_ok = await test_stt_only()
    test_results.append(("STT Service", stt_ok))
    
    # 3. iOS 스타일 전체 파이프라인 테스트
    ios_ok = await test_ios_audio_upload()
    test_results.append(("iOS Voice Pipeline", ios_ok))
    
    # 4. WebSocket 연결 테스트
    ws_ok = await test_websocket_connection()
    test_results.append(("WebSocket Connection", ws_ok))
    
    # 결과 요약
    print("\n📊 테스트 결과 요약")
    print("=" * 30)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print(f"\n🎉 모든 테스트 통과! iOS 앱 개발 준비 완료")
        print(f"\n💡 다음 단계:")
        print(f"   1. Xcode에서 MEREApp 프로젝트 생성")
        print(f"   2. 제공된 Swift 파일들을 프로젝트에 추가")
        print(f"   3. iOS 시뮬레이터에서 앱 실행 및 테스트")
    else:
        print(f"\n⚠️  일부 테스트 실패 - 문제를 해결하고 다시 시도하세요")

if __name__ == "__main__":
    asyncio.run(main())