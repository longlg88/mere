#!/usr/bin/env python3
"""
API 엔드포인트 직접 테스트 (DB 없이)
Day 12: API Endpoint Testing without Database
"""

import requests
import json
import time

def test_api_endpoints():
    """API 엔드포인트 직접 테스트"""
    base_url = "http://localhost:8000"
    
    print("🔌 API 엔드포인트 테스트 (DB 없이)")
    print("=" * 50)
    
    # 1. Health check
    print("\n1. Health Check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 상태: {data.get('status')}")
            print(f"   ✅ 버전: {data.get('version')}")
            print(f"   ✅ 기능: {data.get('features')}")
        else:
            print(f"   ❌ Health check 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        return False
    
    # 2. OpenAPI docs 확인
    print("\n2. API 문서 확인")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Swagger UI 접근 가능")
        else:
            print(f"   ⚠️ Swagger UI 접근 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Swagger UI 확인 실패: {e}")
    
    # 3. API 스키마 확인
    print("\n3. API 스키마 확인")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get('paths', {})
            search_endpoints = [path for path in paths.keys() if '/search/' in path]
            print(f"   ✅ API 스키마 로드 성공")
            print(f"   📊 검색 엔드포인트: {len(search_endpoints)}개")
            for endpoint in search_endpoints[:5]:  # Show first 5
                print(f"      - {endpoint}")
        else:
            print(f"   ⚠️ API 스키마 로드 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ API 스키마 확인 실패: {e}")
    
    # 4. 에러 응답 테스트 (DB 없이도 응답이 와야 함)
    print("\n4. 에러 응답 테스트")
    
    # Invalid search request
    try:
        invalid_data = {"query": ""}  # Empty query should fail
        response = requests.post(
            f"{base_url}/api/search/semantic",
            json=invalid_data,
            timeout=10
        )
        
        if response.status_code == 422:  # Validation error
            print(f"   ✅ 빈 쿼리 검증 오류: {response.status_code} (예상됨)")
        elif response.status_code == 500:  # DB connection error
            print(f"   ⚠️ DB 연결 오류: {response.status_code} (예상됨)")
        else:
            print(f"   🤔 예상치 못한 응답: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 에러 테스트 실패: {e}")
    
    # 5. WebSocket 엔드포인트 확인
    print("\n5. WebSocket 엔드포인트 확인")
    try:
        # WebSocket은 HTTP로 접근하면 upgrade 요구 응답을 줌
        response = requests.get(f"{base_url}/ws/test_user", timeout=5)
        if response.status_code == 426:  # Upgrade Required
            print(f"   ✅ WebSocket 엔드포인트 활성화됨 (HTTP 426 응답)")
        else:
            print(f"   🤔 WebSocket 응답: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ WebSocket 확인 실패: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API 엔드포인트 테스트 완료")
    print(f"💡 DB 연결 없이도 서버가 정상 동작 중")
    print(f"🔗 Swagger UI: {base_url}/docs")
    print(f"📊 API 스키마: {base_url}/openapi.json")
    
    return True


def test_openai_api_key():
    """OpenAI API 키 테스트"""
    print("\n🔑 OpenAI API 키 테스트")
    
    try:
        import openai
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv(Path(__file__).parent / "backend" / ".env")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print(f"   ✅ API 키 로드됨: {'*' * 20}{api_key[-10:]}")
            
            # Test API call
            client = openai.OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="테스트 임베딩",
                encoding_format="float"
            )
            
            if response.data:
                embedding_size = len(response.data[0].embedding)
                print(f"   ✅ API 호출 성공: {embedding_size}차원 임베딩")
                return True
            else:
                print(f"   ❌ API 응답 없음")
                return False
        else:
            print(f"   ⚠️ API 키 없음")
            return False
            
    except Exception as e:
        print(f"   ❌ API 키 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    print("⏳ 서버 확인 중...")
    time.sleep(1)
    
    # Test API endpoints
    api_success = test_api_endpoints()
    
    # Test OpenAI API key
    openai_success = test_openai_api_key()
    
    print(f"\n📊 종합 결과:")
    print(f"   API 서버: {'✅ 동작' if api_success else '❌ 실패'}")
    print(f"   OpenAI API: {'✅ 동작' if openai_success else '❌ 실패'}")
    
    if api_success:
        print(f"\n✅ API 서버가 정상 동작 중입니다!")
        print(f"💡 Search API는 DB 연결 후 완전 동작 가능")
        exit(0)
    else:
        print(f"\n❌ API 서버 테스트 실패")
        exit(1)