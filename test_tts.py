#!/usr/bin/env python3
"""
TTS 서비스 테스트 스크립트
"""
import asyncio
import os
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)

from backend.tts_service import get_tts_service, precache_common_responses

async def test_tts_service():
    """TTS 서비스 기능 테스트"""
    print("🎙️ Piper TTS 서비스 테스트 시작")
    print("=" * 50)
    
    # TTS 서비스 인스턴스 생성
    tts_service = get_tts_service()
    
    # 1. 서비스 정보 확인
    print("1. TTS 서비스 정보:")
    voice_info = tts_service.get_voice_info()
    for key, value in voice_info.items():
        print(f"   {key}: {value}")
    print()
    
    # 2. 기본 텍스트 합성 테스트
    test_texts = [
        "안녕하세요. 저장되었습니다.",
        "메모를 저장했습니다.",
        "일정을 등록했습니다.",
        "할일을 추가했습니다.",
        "죄송합니다. 명령을 이해하지 못했습니다."
    ]
    
    print("2. 기본 TTS 합성 테스트:")
    for i, text in enumerate(test_texts, 1):
        print(f"   테스트 {i}: '{text}'")
        
        try:
            # 임시 파일로 저장
            output_file = f"test_tts_{i}.wav"
            
            result = await tts_service.synthesize_text(text, output_file)
            
            if isinstance(result, str) and os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"   ✅ TTS 성공: {result} ({file_size} bytes)")
                
                # 테스트 후 파일 삭제
                os.unlink(result)
            else:
                print(f"   ✅ TTS 성공: 바이트 데이터 ({len(result) if result else 0} bytes)")
                
        except Exception as e:
            print(f"   ❌ TTS 실패: {e}")
    
    print()
    
    # 3. 바이트 데이터 반환 테스트
    print("3. 바이트 데이터 반환 테스트:")
    test_text = "테스트 음성입니다."
    
    try:
        audio_bytes = await tts_service.synthesize_text(test_text)
        
        if isinstance(audio_bytes, bytes):
            print(f"   ✅ 바이트 데이터 생성 성공: {len(audio_bytes)} bytes")
            
            # WAV 헤더 확인
            if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:20]:
                print(f"   ✅ 유효한 WAV 포맷 확인")
            else:
                print(f"   ⚠️  WAV 포맷이 아닐 수 있습니다")
        else:
            print(f"   ❌ 바이트 데이터가 아닙니다: {type(audio_bytes)}")
            
    except Exception as e:
        print(f"   ❌ 바이트 데이터 생성 실패: {e}")
    
    print()
    
    # 4. 스트리밍 TTS 테스트
    print("4. 스트리밍 TTS 테스트:")
    test_text = "스트리밍 음성 테스트입니다. 여러 청크로 나누어 전송됩니다."
    
    try:
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in tts_service.synthesize_streaming(test_text, chunk_size=512):
            chunk_count += 1
            total_bytes += len(chunk)
        
        print(f"   ✅ 스트리밍 성공: {chunk_count} chunks, {total_bytes} bytes")
        
    except Exception as e:
        print(f"   ❌ 스트리밍 실패: {e}")
    
    print()
    
    # 5. 일반 응답 프리캐싱 테스트
    print("5. 일반 응답 프리캐싱 테스트:")
    
    try:
        await precache_common_responses()
        print(f"   ✅ 프리캐싱 완료")
        
        # 캐시 디렉토리 확인
        import tempfile
        cache_dir = Path(tempfile.gettempdir()) / "tts_cache"
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.wav"))
            print(f"   📁 캐시 파일: {len(cache_files)}개")
            for cache_file in cache_files:
                file_size = cache_file.stat().st_size
                print(f"      - {cache_file.name}: {file_size} bytes")
        
    except Exception as e:
        print(f"   ❌ 프리캐싱 실패: {e}")
    
    print("\n🎯 TTS 서비스 테스트 완료")
    print("\n💡 실제 음성 확인을 위해서는:")
    print("   1. test_tts_single.py로 개별 파일 생성")
    print("   2. 생성된 .wav 파일을 음성 플레이어로 재생")

async def test_single_tts(text: str, output_file: str = "single_test.wav"):
    """단일 텍스트 TTS 테스트"""
    print(f"🎵 단일 TTS 테스트: '{text}'")
    print("-" * 40)
    
    tts_service = get_tts_service()
    
    try:
        result = await tts_service.synthesize_text(text, output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ TTS 파일 생성: {output_file} ({file_size} bytes)")
            print(f"💡 재생 명령: afplay {output_file}  # macOS")
        else:
            print(f"❌ 파일 생성 실패: {output_file}")
            
    except Exception as e:
        print(f"❌ TTS 생성 실패: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 명령행 인자가 있으면 단일 텍스트 테스트
        text = " ".join(sys.argv[1:])
        output_file = "custom_tts.wav"
        asyncio.run(test_single_tts(text, output_file))
    else:
        # 전체 테스트 실행
        asyncio.run(test_tts_service())