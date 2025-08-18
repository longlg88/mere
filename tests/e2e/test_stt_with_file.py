#!/usr/bin/env python3
"""
실제 오디오 파일로 STT 테스트
사용법: python test_stt_with_file.py [audio_file_path]
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

from backend.stt_service import get_stt_service

async def test_with_audio_file(file_path: str):
    """실제 오디오 파일로 STT 테스트"""
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    file_ext = Path(file_path).suffix.lower()
    
    print(f"🎤 오디오 파일 STT 테스트")
    print(f"📁 파일: {file_path}")
    print(f"📄 확장자: {file_ext}")
    print("=" * 50)
    
    # STT 서비스 초기화
    stt_service = get_stt_service(model_size="base")
    
    # 지원 포맷 확인
    supported_formats = stt_service.get_supported_formats()
    if file_ext not in supported_formats:
        print(f"⚠️  지원하지 않는 포맷: {file_ext}")
        print(f"   지원 포맷: {', '.join(supported_formats)}")
        print("   계속 진행합니다...")
    
    try:
        print("🔄 STT 처리 중...")
        
        # 한국어로 음성 인식
        text_ko, confidence_ko = await stt_service.transcribe_audio_file(
            file_path, 
            language="ko"
        )
        
        print(f"🇰🇷 한국어 결과:")
        print(f"   텍스트: '{text_ko}'")
        print(f"   신뢰도: {confidence_ko:.3f}")
        print()
        
        # 영어로도 테스트
        text_en, confidence_en = await stt_service.transcribe_audio_file(
            file_path, 
            language="en"
        )
        
        print(f"🇺🇸 영어 결과:")
        print(f"   텍스트: '{text_en}'")
        print(f"   신뢰도: {confidence_en:.3f}")
        print()
        
        # 자동 언어 감지
        text_auto, confidence_auto = await stt_service.transcribe_audio_file(
            file_path, 
            language=None  # 자동 감지
        )
        
        print(f"🌍 자동 감지 결과:")
        print(f"   텍스트: '{text_auto}'")
        print(f"   신뢰도: {confidence_auto:.3f}")
        
    except Exception as e:
        print(f"❌ STT 처리 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("사용법: python test_stt_with_file.py [audio_file_path]")
        print()
        print("예시:")
        print("  python test_stt_with_file.py sample.wav")
        print("  python test_stt_with_file.py recording.m4a")
        print()
        print("지원 포맷: .wav, .mp3, .m4a, .flac, .ogg")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    asyncio.run(test_with_audio_file(audio_file))

if __name__ == "__main__":
    main()