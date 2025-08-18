#!/usr/bin/env python3
"""
STT API 엔드포인트 테스트 스크립트
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

def create_test_wav(filename: str = "test_audio.wav", duration: int = 2):
    """테스트용 WAV 파일 생성"""
    sample_rate = 16000
    num_samples = sample_rate * duration
    
    # WAV 헤더
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
    
    # 간단한 사인파 생성 (440Hz A음)
    import math
    audio_data = bytearray()
    for i in range(num_samples):
        # 사인파 + 약간의 노이즈
        sample = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        audio_data.extend(sample.to_bytes(2, 'little', signed=True))
    
    full_data = header + audio_data
    
    with open(filename, 'wb') as f:
        f.write(full_data)
    
    return filename

async def test_health_check():
    """기본 헬스체크 테스트"""
    print("🏥 Health Check 테스트")
    print("-" * 30)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Status: {response.status}")
                    print(f"   📝 Response: {data}")
                else:
                    print(f"   ❌ Status: {response.status}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
    
    return True

async def test_stt_info():
    """STT 정보 조회 테스트"""
    print("\n📊 STT Info 테스트")
    print("-" * 30)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/api/stt/info") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ STT 서비스 정보:")
                    for key, value in data.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"   ❌ Status: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return False
    
    return True

async def test_stt_transcribe():
    """STT 파일 업로드 테스트"""
    print("\n🎤 STT Transcribe 테스트")
    print("-" * 30)
    
    # 테스트 오디오 파일 생성
    test_file = "test_audio.wav"
    create_test_wav(test_file)
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(test_file, 'rb') as f:
                # Multipart 폼 데이터 생성
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file, content_type='audio/wav')
                data.add_field('language', 'ko')
                
                async with session.post(f"{BASE_URL}/api/stt/transcribe", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Status: {response.status}")
                        print(f"   📝 Transcription:")
                        print(f"      Text: '{result.get('text')}'")
                        print(f"      Confidence: {result.get('confidence')}")
                        print(f"      Language: {result.get('language')}")
                    else:
                        print(f"   ❌ Status: {response.status}")
                        text = await response.text()
                        print(f"   Error: {text}")
                        return False
                        
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    finally:
        # 테스트 파일 삭제
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    return True

async def test_voice_process():
    """통합 음성 처리 테스트"""
    print("\n🗣️  Voice Process 테스트")
    print("-" * 30)
    
    # 테스트 오디오 파일 생성
    test_file = "test_voice.wav"
    create_test_wav(test_file, duration=3)
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file, content_type='audio/wav')
                data.add_field('language', 'ko')
                
                async with session.post(f"{BASE_URL}/api/voice/process", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Status: {response.status}")
                        print(f"   🎯 Full Pipeline Result:")
                        
                        # STT 결과
                        stt_data = result.get('stt', {})
                        print(f"      STT:")
                        print(f"        Text: '{stt_data.get('text')}'")
                        print(f"        Confidence: {stt_data.get('confidence')}")
                        
                        # NLU 결과
                        nlu_data = result.get('nlu', {})
                        print(f"      NLU:")
                        print(f"        Intent: {nlu_data.get('intent')}")
                        print(f"        Confidence: {nlu_data.get('confidence')}")
                        print(f"        Entities: {nlu_data.get('entities')}")
                        
                        # 최종 응답
                        print(f"      Response: '{result.get('response')}'")
                        
                    else:
                        print(f"   ❌ Status: {response.status}")
                        text = await response.text()
                        print(f"   Error: {text}")
                        return False
                        
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    finally:
        # 테스트 파일 삭제
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    return True

async def test_api_with_real_file(file_path: str):
    """실제 오디오 파일로 API 테스트"""
    if not os.path.exists(file_path):
        print(f"❌ 파일이 존재하지 않습니다: {file_path}")
        return False
        
    print(f"\n🎵 실제 파일 테스트: {file_path}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=os.path.basename(file_path))
                data.add_field('language', 'ko')
                
                async with session.post(f"{BASE_URL}/api/voice/process", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ 성공적으로 처리됨!")
                        
                        stt_data = result.get('stt', {})
                        nlu_data = result.get('nlu', {})
                        
                        print(f"   🎤 STT: '{stt_data.get('text')}'")
                        print(f"   🧠 Intent: {nlu_data.get('intent')} ({nlu_data.get('confidence'):.2f})")
                        print(f"   📝 Response: '{result.get('response')}'")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 실패: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
            return False
    
    return True

async def main():
    """메인 테스트 실행"""
    print("🚀 MERE AI Agent API 테스트 시작")
    print("=" * 50)
    
    # 0. 서버 연결 확인
    if not await test_health_check():
        print("\n❌ 서버에 연결할 수 없습니다!")
        print("💡 서버가 실행 중인지 확인하세요: python -m backend.main")
        return
    
    # 1. STT 정보 조회
    if not await test_stt_info():
        print("\n❌ STT 서비스 정보 조회 실패")
        return
    
    # 2. STT 파일 업로드 테스트
    if not await test_stt_transcribe():
        print("\n❌ STT 파일 처리 테스트 실패")
        return
    
    # 3. 통합 음성 처리 테스트
    if not await test_voice_process():
        print("\n❌ 통합 음성 처리 테스트 실패")
        return
    
    print("\n🎉 모든 테스트 통과!")
    print("\n💡 실제 음성 파일 테스트:")
    print("   python test_api_endpoints.py [audio_file_path]")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 2:
        # 실제 파일로 테스트
        asyncio.run(test_api_with_real_file(sys.argv[1]))
    else:
        # 기본 테스트 실행
        asyncio.run(main())