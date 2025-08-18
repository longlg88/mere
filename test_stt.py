#!/usr/bin/env python3
"""
STT 서비스 테스트 스크립트
"""
import asyncio
import os
import tempfile
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

from backend.stt_service import WhisperSTTService, get_stt_service

async def test_stt_service():
    """STT 서비스 기능 테스트"""
    print("🎤 Whisper STT 서비스 테스트 시작")
    print("=" * 50)
    
    # STT 서비스 인스턴스 생성
    stt_service = get_stt_service(model_size="base")
    
    # 1. 모델 정보 확인
    print("1. 모델 정보:")
    model_info = stt_service.get_model_info()
    for key, value in model_info.items():
        print(f"   {key}: {value}")
    print()
    
    # 2. 지원 포맷 확인
    print("2. 지원하는 오디오 포맷:")
    formats = stt_service.get_supported_formats()
    print(f"   {', '.join(formats)}")
    print()
    
    # 3. 테스트용 간단한 오디오 생성 (빈 오디오)
    print("3. 테스트 오디오 처리:")
    
    # 임시 WAV 파일 생성 (실제로는 실제 오디오 파일을 사용해야 함)
    test_audio_path = "/tmp/test_empty.wav"
    
    # 빈 WAV 파일 헤더 생성 (44바이트 헤더 + 1초 무음)
    sample_rate = 16000
    duration = 1  # 1초
    wav_header = create_wav_header(sample_rate, duration)
    
    with open(test_audio_path, "wb") as f:
        f.write(wav_header)
    
    try:
        # STT 처리 테스트
        print(f"   테스트 파일: {test_audio_path}")
        
        text, confidence = await stt_service.transcribe_audio_file(
            test_audio_path, 
            language="ko"
        )
        
        print(f"   ✅ STT 결과: '{text}' (신뢰도: {confidence:.2f})")
        
        # 4. 바이트 데이터 직접 처리 테스트
        print("4. 바이트 데이터 처리 테스트:")
        
        with open(test_audio_path, "rb") as f:
            audio_data = f.read()
        
        text2, confidence2 = await stt_service.transcribe_audio_data(
            audio_data, 
            sample_rate=16000, 
            language="ko"
        )
        
        print(f"   ✅ 바이트 처리 결과: '{text2}' (신뢰도: {confidence2:.2f})")
        
    except Exception as e:
        print(f"   ❌ STT 처리 실패: {e}")
        print("   💡 실제 오디오 파일로 테스트하면 더 정확한 결과를 얻을 수 있습니다.")
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)
    
    print("\n🎯 STT 서비스 테스트 완료")
    print("\n💡 실제 테스트를 위해서는:")
    print("   1. 실제 음성 파일(.wav, .mp3 등)을 준비하세요")
    print("   2. test_stt_with_file.py [파일경로] 를 실행하세요")

def create_wav_header(sample_rate: int, duration: int) -> bytes:
    """간단한 WAV 파일 헤더 생성 (무음)"""
    num_samples = sample_rate * duration
    byte_rate = sample_rate * 2  # 16-bit mono
    
    header = b'RIFF'
    header += (36 + num_samples * 2).to_bytes(4, 'little')  # 파일 크기
    header += b'WAVE'
    header += b'fmt '
    header += (16).to_bytes(4, 'little')  # fmt 청크 크기
    header += (1).to_bytes(2, 'little')   # 오디오 포맷 (PCM)
    header += (1).to_bytes(2, 'little')   # 채널 수 (mono)
    header += sample_rate.to_bytes(4, 'little')  # 샘플링 레이트
    header += byte_rate.to_bytes(4, 'little')    # 바이트 레이트
    header += (2).to_bytes(2, 'little')   # 블록 정렬
    header += (16).to_bytes(2, 'little')  # 비트 레이트
    header += b'data'
    header += (num_samples * 2).to_bytes(4, 'little')  # 데이터 크기
    
    # 무음 데이터 추가 (0으로 채움)
    header += b'\x00' * (num_samples * 2)
    
    return header

if __name__ == "__main__":
    asyncio.run(test_stt_service())