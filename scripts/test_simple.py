#!/usr/bin/env python3
"""
간단한 OpenAI 연결 테스트
"""
import os
from openai import OpenAI

# 테스트용 더미 API 키
os.environ["OPENAI_API_KEY"] = "test-key-123"

try:
    client = OpenAI(api_key="test-key-123")
    print("✅ OpenAI 클라이언트 생성 성공")
    print(f"✅ API Key 설정됨: {client.api_key[:10]}...")
    
    # 실제 요청은 하지 않고 클라이언트만 테스트
    print("✅ NLU 서비스 구조 테스트 준비 완료")
    
except Exception as e:
    print(f"❌ OpenAI 클라이언트 생성 실패: {e}")
    print("패키지 재설치가 필요할 수 있습니다.")