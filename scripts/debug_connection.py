#!/usr/bin/env python3
"""
OpenAI 연결 디버깅 스크립트
"""
import os
import sys
from openai import OpenAI

def debug_connection():
    """연결 상태 상세 디버깅"""
    
    print("🔍 OpenAI API 연결 디버깅")
    print("=" * 50)
    
    # 1. 환경변수 확인
    print("1. 환경변수 확인:")
    api_key = os.getenv("OPENAI_API_KEY")
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    
    print(f"   OPENAI_API_KEY: {'✅ 설정됨' if api_key else '❌ 없음'}")
    if api_key:
        print(f"   키 형식: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    
    print(f"   HTTP_PROXY: {http_proxy or '❌ 설정안됨'}")
    print(f"   HTTPS_PROXY: {https_proxy or '❌ 설정안됨'}")
    print()
    
    if not api_key:
        print("❌ API 키가 설정되지 않았습니다!")
        return
    
    # 2. 기본 연결 테스트
    print("2. 기본 연결 테스트:")
    try:
        # 기본 OpenAI 클라이언트 사용 (환경변수 프록시 자동 인식)
        if http_proxy or https_proxy:
            print(f"   🔧 환경변수 프록시 감지됨: {https_proxy or http_proxy}")
            print("   📡 OpenAI 클라이언트가 자동으로 프록시 사용")
        
        client = OpenAI(api_key=api_key)
        
        print("   ✅ OpenAI 클라이언트 생성 성공")
    except Exception as e:
        print(f"   ❌ 클라이언트 생성 실패: {e}")
        return
    
    # 3. 모델 목록 조회 (가장 기본적인 API 호출)
    print("3. 모델 목록 조회:")
    try:
        models = client.models.list()
        print("   ✅ API 연결 성공!")
        
        # GPT-5 사용 가능 여부 확인
        available_models = [model.id for model in models]
        if "gpt-5" in available_models:
            print("   ✅ GPT-5 사용 가능")
        elif "gpt-4o" in available_models:
            print("   ⚠️  GPT-5 없음, GPT-4o 사용 가능")
        elif "gpt-4" in available_models:
            print("   ⚠️  GPT-4만 사용 가능")
        else:
            print("   ❓ 사용 가능한 GPT 모델을 확인하세요")
            
    except Exception as e:
        print(f"   ❌ API 연결 실패: {e}")
        print(f"   오류 타입: {type(e).__name__}")
        return
    
    # 4. 간단한 채팅 테스트
    print("4. 간단한 채팅 테스트:")
    try:
        response = client.chat.completions.create(
            model="gpt-5",  # GPT-5 테스트
            messages=[{"role": "user", "content": "Hello"}],
            max_completion_tokens=5  # GPT-5는 max_completion_tokens 사용
        )
        print(f"   ✅ 채팅 API 성공: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"   ❌ 채팅 API 실패: {e}")
        if "model_not_found" in str(e):
            print("   💡 gpt-4o-mini 모델에 접근할 수 없습니다.")
        elif "insufficient_quota" in str(e):
            print("   💡 사용량 한도 초과 또는 결제 정보 필요")
        elif "invalid_request_error" in str(e):
            print("   💡 요청 형식에 문제가 있습니다.")

if __name__ == "__main__":
    debug_connection()