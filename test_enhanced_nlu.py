#!/usr/bin/env python3
"""
Enhanced NLU 서비스 테스트 - 확장된 Intent와 Entity 테스트
"""
import asyncio
import os
from backend.nlu_service import get_nlu_service

# 테스트 케이스들
test_cases = [
    # 메모 관련
    {
        "text": "다음 주 토요일 여행 가는 거 기록해줘",
        "expected_intent": "create_memo",
        "expected_entities": ["item_name", "date_time"]
    },
    {
        "text": "쇼핑 관련해서 뭐 적었더라?",
        "expected_intent": "search_by_category",
        "expected_entities": ["category"]
    },
    {
        "text": "어제 적은 메모 수정해줘",
        "expected_intent": "update_memo",
        "expected_entities": ["date_time"]
    },
    
    # 할일 관리
    {
        "text": "내일까지 긴급하게 보고서 작성해야 해",
        "expected_intent": "create_todo",
        "expected_entities": ["item_name", "date_time", "priority"]
    },
    {
        "text": "프로젝트 관련 할일 다 했어",
        "expected_intent": "complete_todo",
        "expected_entities": ["category"]
    },
    {
        "text": "오늘 해야 할 일들 보여줘",
        "expected_intent": "query_todo",
        "expected_entities": ["date_time"]
    },
    
    # 일정 관리
    {
        "text": "다음 주 월요일 오후 3시에 김대리와 회의 잡아줘",
        "expected_intent": "create_event",
        "expected_entities": ["date_time", "person", "item_name"]
    },
    {
        "text": "강남역에서 2시간 짜리 미팅 예약해줘",
        "expected_intent": "create_event",
        "expected_entities": ["location", "duration", "item_name"]
    },
    {
        "text": "내일 약속 취소해줘",
        "expected_intent": "cancel_event",
        "expected_entities": ["date_time"]
    },
    
    # 검색 및 분석
    {
        "text": "이번 주에 뭘 했는지 확인해줘",
        "expected_intent": "search_by_date",
        "expected_entities": ["date_time"]
    },
    {
        "text": "업무 관련해서 자주 하는 일이 뭐야?",
        "expected_intent": "analyze_pattern",
        "expected_entities": ["category"]
    },
    
    # 알림 관리
    {
        "text": "내일 아침에 운동 가는 거 알려줘",
        "expected_intent": "set_reminder",
        "expected_entities": ["date_time", "item_name", "reminder_time"]
    },
    {
        "text": "10분 후에 다시 알려줘",
        "expected_intent": "snooze_reminder",
        "expected_entities": ["reminder_time"]
    },
    
    # 감정 및 소통
    {
        "text": "안녕하세요",
        "expected_intent": "greeting",
        "expected_entities": []
    },
    {
        "text": "고마워요",
        "expected_intent": "thanks",
        "expected_entities": []
    },
    {
        "text": "도와주세요",
        "expected_intent": "help",
        "expected_entities": []
    },
    
    # 복잡한 케이스
    {
        "text": "매주 화요일마다 헬스장에서 1시간씩 운동하는 걸로 일정 잡아줘",
        "expected_intent": "create_event",
        "expected_entities": ["repeat_pattern", "location", "duration", "item_name"]
    },
    {
        "text": "중요한 프레젠테이션 준비하는 거 완료 처리하고 다음 할일로 넘어가줘",
        "expected_intent": "complete_todo",
        "expected_entities": ["priority", "item_name"]
    }
]

async def test_enhanced_nlu():
    """확장된 NLU 서비스 테스트"""
    print("🧠 Enhanced NLU 서비스 테스트 시작")
    print("=" * 60)
    
    nlu_service = get_nlu_service()
    
    total_tests = len(test_cases)
    passed_tests = 0
    failed_tests = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 테스트 {i}/{total_tests}: '{test_case['text']}'")
        print("-" * 50)
        
        try:
            result = await nlu_service.analyze_intent(test_case['text'])
            
            # Intent 검증
            intent_correct = result.intent.name == test_case['expected_intent']
            
            # Entity 검증 (예상된 entity가 있는지 확인)
            entities_found = list(result.entities.keys()) if result.entities else []
            expected_entities = test_case['expected_entities']
            
            # 적어도 하나의 예상 entity가 있는지 확인
            entity_match = True
            if expected_entities:
                entity_match = any(entity in entities_found for entity in expected_entities)
            
            # 결과 출력
            print(f"   🎯 Intent: {result.intent.name} (신뢰도: {result.confidence:.2f})")
            print(f"   📊 예상: {test_case['expected_intent']} - {'✅' if intent_correct else '❌'}")
            
            if result.entities:
                print(f"   🔍 추출된 Entities:")
                for key, value in result.entities.items():
                    print(f"      - {key}: {value}")
            else:
                print(f"   🔍 추출된 Entities: 없음")
            
            if expected_entities:
                print(f"   📋 예상 Entities: {expected_entities} - {'✅' if entity_match else '❌'}")
            
            # 응답 생성 테스트
            response = nlu_service.get_response_template(result.intent.name, result.entities)
            print(f"   💬 응답: '{response}'")
            
            # 전체 평가
            test_passed = intent_correct and entity_match
            
            if test_passed:
                passed_tests += 1
                print(f"   ✅ 테스트 통과")
            else:
                failed_tests.append({
                    'text': test_case['text'],
                    'expected': test_case['expected_intent'],
                    'actual': result.intent.name,
                    'confidence': result.confidence
                })
                print(f"   ❌ 테스트 실패")
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
            failed_tests.append({
                'text': test_case['text'],
                'error': str(e)
            })
    
    # 결과 요약
    print(f"\n" + "=" * 60)
    print(f"🎯 테스트 결과 요약")
    print(f"   총 테스트: {total_tests}")
    print(f"   통과: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   실패: {len(failed_tests)} ({len(failed_tests)/total_tests*100:.1f}%)")
    
    if failed_tests:
        print(f"\n❌ 실패한 테스트들:")
        for i, fail in enumerate(failed_tests, 1):
            print(f"   {i}. '{fail['text']}'")
            if 'error' in fail:
                print(f"      오류: {fail['error']}")
            else:
                print(f"      예상: {fail['expected']}, 실제: {fail['actual']} (신뢰도: {fail['confidence']:.2f})")
    
    if passed_tests == total_tests:
        print(f"\n🎉 모든 테스트 통과! Enhanced NLU 시스템이 완벽하게 작동합니다!")
    elif passed_tests / total_tests >= 0.8:
        print(f"\n✅ 대부분의 테스트 통과! NLU 시스템이 잘 작동합니다.")
    else:
        print(f"\n⚠️  일부 테스트 실패. 추가 튜닝이 필요할 수 있습니다.")

async def test_specific_case(text: str):
    """특정 문장만 테스트"""
    print(f"🔍 단일 테스트: '{text}'")
    print("-" * 40)
    
    nlu_service = get_nlu_service()
    
    try:
        result = await nlu_service.analyze_intent(text)
        
        print(f"Intent: {result.intent.name} (신뢰도: {result.confidence:.2f})")
        
        if result.entities:
            print(f"Entities:")
            for key, value in result.entities.items():
                print(f"  - {key}: {value}")
        else:
            print("Entities: 없음")
        
        response = nlu_service.get_response_template(result.intent.name, result.entities)
        print(f"응답: '{response}'")
        
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 명령행 인자가 있으면 특정 문장 테스트
        test_text = " ".join(sys.argv[1:])
        asyncio.run(test_specific_case(test_text))
    else:
        # 전체 테스트 실행
        asyncio.run(test_enhanced_nlu())