#!/usr/bin/env python3
"""
GPT-5 NLU 서비스 테스트 스크립트
"""
import asyncio
import os
from backend.nlu_service import get_nlu_service

async def test_nlu_service():
    """NLU 서비스 기본 테스트"""
    
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("다음 명령으로 설정하세요:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print()
        print("🔧 대신 NLU 서비스 구조 테스트를 진행합니다...")
        test_nlu_structure()
        return
    
    nlu = get_nlu_service()
    
    test_cases = [
        "내일 우유 사는 거 기억해줘",
        "오후 3시에 팀 회의 잡아줘",
        "할일 목록 보여줘",
        "방금 말한 할일 취소해",
        "이번 주에 뭔 일정 있었지?",
        "긴급한 프로젝트 보고서 작성하기",
        "다음주 월요일 오전 10시 치과 예약"
    ]
    
    print("🤖 GPT-5 NLU 서비스 테스트 시작\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"📝 테스트 {i}: '{text}'")
        
        try:
            result = await nlu.analyze_intent(text)
            
            print(f"   Intent: {result.intent.name} (신뢰도: {result.confidence:.2f})")
            
            if result.entities:
                print("   Entities:")
                for key, value in result.entities.items():
                    if value:  # None이 아닌 값만 출력
                        print(f"     - {key}: {value}")
            
            # 응답 템플릿 테스트
            response = nlu.get_response_template(result.intent.name, result.entities)
            print(f"   응답: {response}")
            
        except Exception as e:
            print(f"   ❌ 에러: {e}")
        
        print("   " + "-"*50)

def test_nlu_structure():
    """API 키 없이 NLU 서비스 구조 테스트"""
    print("🔍 NLU 서비스 구조 테스트")
    
    try:
        # 임시 API 키로 서비스 객체 생성 테스트
        os.environ["OPENAI_API_KEY"] = "test-key"
        nlu = get_nlu_service()
        
        print("✅ NLU 서비스 객체 생성 성공")
        print(f"✅ 지원하는 Intent 수: {len(nlu.intents)}")
        
        # Intent 목록 출력
        print("📋 지원하는 Intent 목록:")
        for intent, desc in nlu.intents.items():
            print(f"   - {intent}: {desc}")
        
        # 시스템 프롬프트 생성 테스트
        prompt = nlu._create_system_prompt()
        print(f"✅ 시스템 프롬프트 생성 성공 (길이: {len(prompt)} chars)")
        
        # 응답 템플릿 테스트
        print("📝 응답 템플릿 테스트:")
        test_entities = {"item_name": "우유 사기"}
        for intent_name in ["create_memo", "create_todo", "create_event", "unknown"]:
            template = nlu.get_response_template(intent_name, test_entities)
            print(f"   - {intent_name}: {template}")
        
        # 시간 파싱 테스트
        print("⏰ 시간 파싱 테스트:")
        time_texts = ["내일 오후 3시", "다음주 월요일", "오늘 오전 10시"]
        for text in time_texts:
            parsed = nlu._parse_time_expression(text)
            print(f"   - '{text}' → {parsed}")
        
        print("\n🎉 모든 구조 테스트 통과!")
        
    except Exception as e:
        print(f"❌ 구조 테스트 실패: {e}")
    
    finally:
        # 테스트 API 키 제거
        if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"] == "test-key":
            del os.environ["OPENAI_API_KEY"]

if __name__ == "__main__":
    asyncio.run(test_nlu_service())