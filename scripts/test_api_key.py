#!/usr/bin/env python3
"""
OpenAI API 키 검증 테스트
"""
import os
from openai import OpenAI

def test_api_key():
    """API 키 유효성 간단 테스트"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # 간단한 테스트 요청
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API 키 검증 성공!")
        print(f"✅ 응답: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API 키 검증 실패: {e}")
        if "invalid_api_key" in str(e):
            print("💡 API 키가 유효하지 않습니다. 올바른 키를 확인해주세요.")
        elif "insufficient_quota" in str(e):
            print("💡 사용량 한도를 초과했습니다. 결제 정보를 확인해주세요.")
        elif "model_not_found" in str(e):
            print("💡 모델을 찾을 수 없습니다. gpt-4o-mini가 지원되는지 확인해주세요.")
        return False

if __name__ == "__main__":
    test_api_key()