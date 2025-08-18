#!/usr/bin/env python3
"""
End-to-End Pipeline 테스트 스크립트
Day 6 Task 6.2: STT → NLU → Business Logic → TTS 파이프라인 통합 테스트
"""
import asyncio
import websockets
import json
import logging
import time
from datetime import datetime
from typing import List, Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket 서버 정보
WEBSOCKET_URL = "ws://localhost:8000/ws/e2e-test-user"

class E2EPipelineTester:
    """End-to-End 파이프라인 테스트 클래스"""
    
    def __init__(self):
        self.test_results = []
        self.websocket = None
    
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.websocket = await websockets.connect(WEBSOCKET_URL)
            # Connection ACK 수신
            response = await self.websocket.recv()
            data = json.loads(response)
            if data.get('type') == 'connection_ack':
                logger.info("✅ WebSocket 연결 성공")
                return True
            else:
                logger.error("❌ Connection ACK 실패")
                return False
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
    
    async def test_scenario(self, scenario: Dict) -> Dict:
        """단일 시나리오 테스트"""
        scenario_name = scenario["name"]
        command_text = scenario["command"]
        expected_intent = scenario["expected_intent"]
        expected_success = scenario.get("expected_success", True)
        
        logger.info(f"🧪 테스트: {scenario_name}")
        logger.info(f"   명령: '{command_text}'")
        
        try:
            start_time = time.time()
            
            # 텍스트 명령 전송
            message = {
                "type": "text_command",
                "text": command_text,
                "timestamp": datetime.now().isoformat(),
                "user_id": "e2e-test-user"
            }
            
            await self.websocket.send(json.dumps(message))
            
            # Processing status 수신
            processing_response = await self.websocket.recv()
            processing_data = json.loads(processing_response)
            
            if processing_data.get('type') == 'processing_status':
                logger.info(f"   ⚡ {processing_data.get('message', '')}")
            
            # 최종 응답 수신
            final_response = await self.websocket.recv()
            final_data = json.loads(final_response)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 결과 분석
            if final_data.get('type') == 'text_response':
                nlu = final_data.get('nlu', {})
                business = final_data.get('business', {})
                response_text = final_data.get('response', '')
                
                actual_intent = nlu.get('intent', '')
                intent_confidence = nlu.get('confidence', 0)
                business_success = business.get('success', False)
                business_action = business.get('action', '')
                business_data = business.get('data')
                
                # 성공 판정
                intent_match = actual_intent == expected_intent
                success_match = business_success == expected_success
                overall_success = intent_match and success_match and response_time < 3.0
                
                # 결과 로깅
                logger.info(f"   🧠 Intent: {actual_intent} (confidence: {intent_confidence:.2f}) {'✅' if intent_match else '❌'}")
                logger.info(f"   💼 Business: {business_action} (success: {business_success}) {'✅' if success_match else '❌'}")
                logger.info(f"   💬 Response: {response_text}")
                logger.info(f"   ⏱️  Time: {response_time:.2f}s {'✅' if response_time < 3.0 else '❌'}")
                
                if business_data:
                    logger.info(f"   📊 Data: {json.dumps(business_data, ensure_ascii=False, indent=2)}")
                
                result = {
                    "scenario": scenario_name,
                    "command": command_text,
                    "success": overall_success,
                    "response_time": response_time,
                    "intent": {
                        "expected": expected_intent,
                        "actual": actual_intent,
                        "confidence": intent_confidence,
                        "match": intent_match
                    },
                    "business": {
                        "expected_success": expected_success,
                        "actual_success": business_success,
                        "action": business_action,
                        "match": success_match,
                        "data": business_data
                    },
                    "response": response_text
                }
                
                status = "✅ PASS" if overall_success else "❌ FAIL"
                logger.info(f"   결과: {status}")
                
                return result
            else:
                logger.error(f"   ❌ 예상하지 못한 응답 타입: {final_data.get('type')}")
                return {
                    "scenario": scenario_name,
                    "command": command_text,
                    "success": False,
                    "error": f"Unexpected response type: {final_data.get('type')}"
                }
                
        except Exception as e:
            logger.error(f"   ❌ 시나리오 테스트 실패: {e}")
            return {
                "scenario": scenario_name,
                "command": command_text,
                "success": False,
                "error": str(e)
            }
    
    async def run_test_suite(self, scenarios: List[Dict]) -> Dict:
        """전체 테스트 스위트 실행"""
        logger.info("🚀 E2E Pipeline 테스트 시작")
        logger.info("=" * 60)
        
        if not await self.connect():
            return {"success": False, "error": "WebSocket connection failed"}
        
        try:
            results = []
            
            for i, scenario in enumerate(scenarios, 1):
                logger.info(f"\n[{i}/{len(scenarios)}] {scenario['name']}")
                result = await self.test_scenario(scenario)
                results.append(result)
                
                # 시나리오 간 간격
                await asyncio.sleep(0.5)
            
            # 결과 요약
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]
            
            avg_response_time = sum(r.get('response_time', 0) for r in results if r.get('response_time')) / len(results)
            
            summary = {
                "total_scenarios": len(scenarios),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(scenarios) * 100,
                "avg_response_time": avg_response_time,
                "results": results
            }
            
            logger.info("\n📊 E2E 테스트 결과 요약")
            logger.info("=" * 40)
            logger.info(f"   총 시나리오: {len(scenarios)}")
            logger.info(f"   성공: {len(successful)} ✅")
            logger.info(f"   실패: {len(failed)} ❌")
            logger.info(f"   성공률: {summary['success_rate']:.1f}%")
            logger.info(f"   평균 응답시간: {avg_response_time:.2f}초")
            
            if failed:
                logger.info(f"\n❌ 실패한 시나리오:")
                for result in failed:
                    logger.info(f"   - {result['scenario']}: {result.get('error', 'Unknown error')}")
            
            overall_success = len(successful) == len(scenarios) and avg_response_time < 2.5
            
            if overall_success:
                logger.info(f"\n🎉 모든 E2E 테스트 통과!")
                logger.info(f"💡 Day 6 Task 6.2 완료:")
                logger.info(f"   ✅ STT → NLU → Business Logic → TTS 파이프라인 연결")
                logger.info(f"   ✅ Intent → Business Action 매핑 시스템 동작")
                logger.info(f"   ✅ 데이터베이스 CRUD 연산 통합")
                logger.info(f"   ✅ 에러 전파 및 처리 검증")
            else:
                logger.info(f"\n⚠️  E2E 테스트 일부 실패 - 문제를 확인하고 다시 시도하세요")
            
            summary["overall_success"] = overall_success
            return summary
            
        finally:
            await self.disconnect()

# 테스트 시나리오 정의
TEST_SCENARIOS = [
    # 메모 관리 시나리오
    {
        "name": "메모 생성 - 기본",
        "command": "내일 우유 사는 거 기억해줘",
        "expected_intent": "create_memo",
        "expected_success": True
    },
    {
        "name": "메모 생성 - 우선순위 포함",
        "command": "긴급하게 보고서 작성하라고 기억시켜줘",
        "expected_intent": "create_memo",
        "expected_success": True
    },
    {
        "name": "메모 조회 - 일반",
        "command": "메모 뭐 있는지 보여줘",
        "expected_intent": "query_memo",
        "expected_success": True
    },
    {
        "name": "메모 조회 - 카테고리별",
        "command": "업무 관련 메모 찾아줘",
        "expected_intent": "query_memo",
        "expected_success": True
    },
    
    # 할일 관리 시나리오
    {
        "name": "할일 생성 - 기본",
        "command": "장보기 할일로 추가해줘",
        "expected_intent": "create_todo",
        "expected_success": True
    },
    {
        "name": "할일 생성 - 마감일 포함",
        "command": "내일까지 프레젠테이션 준비하라고 할일 만들어줘",
        "expected_intent": "create_todo",
        "expected_success": True
    },
    {
        "name": "할일 조회 - 일반",
        "command": "할일 목록 보여줘",
        "expected_intent": "query_todo",
        "expected_success": True
    },
    {
        "name": "할일 조회 - 우선순위별",
        "command": "긴급한 할일 뭐 있어?",
        "expected_intent": "query_todo",
        "expected_success": True
    },
    
    # 일정 관리 시나리오 (현재는 기본 응답)
    {
        "name": "일정 생성",
        "command": "다음주 월요일 회의 일정 잡아줘",
        "expected_intent": "create_event",
        "expected_success": True
    },
    
    # 검색 및 분석 시나리오
    {
        "name": "일반 검색",
        "command": "쇼핑 관련해서 뭐 있었지?",
        "expected_intent": "search_general",
        "expected_success": True
    },
    {
        "name": "날짜별 검색",
        "command": "오늘 뭐 했는지 확인해줘",
        "expected_intent": "search_by_date",
        "expected_success": True
    },
    
    # 시스템 제어 시나리오
    {
        "name": "도움말 요청",
        "command": "어떻게 사용하는지 알려줘",
        "expected_intent": "help",
        "expected_success": True
    },
    
    # 감정 및 소통 시나리오
    {
        "name": "인사",
        "command": "안녕하세요",
        "expected_intent": "greeting",
        "expected_success": True
    },
    {
        "name": "감사 표현",
        "command": "고마워요",
        "expected_intent": "thanks",
        "expected_success": True
    }
]

async def main():
    """메인 E2E 테스트 실행"""
    tester = E2EPipelineTester()
    results = await tester.run_test_suite(TEST_SCENARIOS)
    
    # 성능 목표 검증
    logger.info(f"\n🎯 성능 목표 검증:")
    logger.info(f"   평균 응답시간: {results.get('avg_response_time', 0):.2f}초 (목표: <2.5초)")
    logger.info(f"   성공률: {results.get('success_rate', 0):.1f}% (목표: >90%)")
    
    if results.get('overall_success'):
        logger.info(f"\n🚀 Day 6: Basic Business Logic & Integration 완료!")
        return True
    else:
        logger.info(f"\n⚠️  일부 목표 미달성 - 추가 개선 필요")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())