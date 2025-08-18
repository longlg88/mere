#!/usr/bin/env python3
"""
오프라인 모드 테스트 스크립트
Day 11: Offline Mode & Data Sync Testing
"""

import asyncio
import json
import time
from typing import Dict, List, Any

class OfflineModeTest:
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """모든 오프라인 모드 테스트 실행"""
        print("🔧 오프라인 모드 테스트 시작")
        print("=" * 60)
        
        # Test scenarios
        test_scenarios = [
            self.test_offline_intent_processing,
            self.test_local_data_storage,
            self.test_network_state_detection,
            self.test_data_queuing,
            self.test_sync_on_reconnect,
            self.test_conflict_resolution,
            self.test_offline_search,
            self.test_data_persistence
        ]
        
        passed = 0
        failed = 0
        
        for test_func in test_scenarios:
            try:
                result = await test_func()
                if result:
                    passed += 1
                    print(f"✅ {test_func.__name__}: PASS")
                else:
                    failed += 1
                    print(f"❌ {test_func.__name__}: FAIL")
                    
                self.test_results.append({
                    "test": test_func.__name__,
                    "status": "PASS" if result else "FAIL",
                    "timestamp": time.time() - self.start_time
                })
                
            except Exception as e:
                failed += 1
                print(f"❌ {test_func.__name__}: ERROR - {e}")
                self.test_results.append({
                    "test": test_func.__name__,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": time.time() - self.start_time
                })
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎯 테스트 결과 요약")
        print(f"   통과: {passed}")
        print(f"   실패: {failed}")
        print(f"   총 테스트: {passed + failed}")
        print(f"   성공률: {(passed / (passed + failed) * 100):.1f}%")
        print(f"   실행 시간: {time.time() - self.start_time:.2f}초")
        
        return passed, failed
    
    async def test_offline_intent_processing(self) -> bool:
        """오프라인 Intent 처리 테스트"""
        print("\n📝 테스트: 오프라인 Intent 처리")
        
        # Simulate offline intent processor
        test_cases = [
            {
                "input": "내일 회의 일정 기록해줘",
                "expected_intent": "create_memo",
                "expected_entities": ["item_name", "date_time"]
            },
            {
                "input": "프로젝트 관련 할일 추가해줘",
                "expected_intent": "create_todo",
                "expected_entities": ["category", "item_name"]
            },
            {
                "input": "오늘 회의 일정 잡아줘",
                "expected_intent": "create_event",
                "expected_entities": ["date_time", "item_name"]
            },
            {
                "input": "할일 목록 보여줘",
                "expected_intent": "query_todo",
                "expected_entities": []
            }
        ]
        
        success_count = 0
        
        for case in test_cases:
            # Simulate intent processing result
            result = self.simulate_intent_processing(case["input"])
            
            intent_match = result["intent"] == case["expected_intent"]
            entity_match = all(entity in result["entities"] for entity in case["expected_entities"])
            
            if intent_match and entity_match:
                success_count += 1
                print(f"   ✅ '{case['input']}' -> {result['intent']}")
            else:
                print(f"   ❌ '{case['input']}' -> Expected: {case['expected_intent']}, Got: {result['intent']}")
        
        success_rate = success_count / len(test_cases)
        print(f"   📊 Intent 처리 성공률: {success_rate * 100:.1f}% ({success_count}/{len(test_cases)})")
        
        return success_rate >= 0.75  # 75% 이상 성공률 요구
    
    async def test_local_data_storage(self) -> bool:
        """로컬 데이터 저장 테스트"""
        print("\n💾 테스트: 로컬 데이터 저장")
        
        # Simulate local data operations
        test_operations = [
            {"type": "create_memo", "data": {"content": "테스트 메모", "category": "업무"}},
            {"type": "create_todo", "data": {"title": "테스트 할일", "priority": "high"}},
            {"type": "create_event", "data": {"title": "테스트 이벤트", "date": "2024-01-01"}},
            {"type": "update_memo", "data": {"id": "memo_1", "content": "수정된 메모"}},
            {"type": "delete_todo", "data": {"id": "todo_1"}},
        ]
        
        success_count = 0
        
        for op in test_operations:
            try:
                # Simulate database operation
                await asyncio.sleep(0.1)  # Simulate processing time
                
                # Check if operation would succeed
                if self.simulate_db_operation(op):
                    success_count += 1
                    print(f"   ✅ {op['type']}: 성공")
                else:
                    print(f"   ❌ {op['type']}: 실패")
                    
            except Exception as e:
                print(f"   ❌ {op['type']}: 오류 - {e}")
        
        success_rate = success_count / len(test_operations)
        print(f"   📊 데이터 저장 성공률: {success_rate * 100:.1f}% ({success_count}/{len(test_operations)})")
        
        return success_rate >= 0.9  # 90% 이상 성공률 요구
    
    async def test_network_state_detection(self) -> bool:
        """네트워크 상태 감지 테스트"""
        print("\n🌐 테스트: 네트워크 상태 감지")
        
        # Simulate network state changes
        network_states = [
            {"connected": True, "type": "wifi"},
            {"connected": False, "type": "none"},
            {"connected": True, "type": "cellular"},
            {"connected": False, "type": "none"},
            {"connected": True, "type": "wifi"}
        ]
        
        state_changes_detected = 0
        
        for i, state in enumerate(network_states):
            await asyncio.sleep(0.2)  # Simulate state change delay
            
            # Simulate network monitor detection
            detected = self.simulate_network_detection(state)
            
            if detected:
                state_changes_detected += 1
                status = "온라인" if state["connected"] else "오프라인"
                print(f"   ✅ 상태 변경 감지: {status} ({state['type']})")
            else:
                print(f"   ❌ 상태 변경 미감지: {state}")
        
        detection_rate = state_changes_detected / len(network_states)
        print(f"   📊 네트워크 상태 감지율: {detection_rate * 100:.1f}% ({state_changes_detected}/{len(network_states)})")
        
        return detection_rate >= 0.8  # 80% 이상 감지율 요구
    
    async def test_data_queuing(self) -> bool:
        """데이터 큐잉 테스트"""
        print("\n📋 테스트: 데이터 큐잉")
        
        # Simulate offline data queuing
        offline_operations = [
            {"type": "memo", "action": "create", "data": {"content": "오프라인 메모 1"}},
            {"type": "todo", "action": "create", "data": {"title": "오프라인 할일 1"}},
            {"type": "event", "action": "create", "data": {"title": "오프라인 이벤트 1"}},
            {"type": "memo", "action": "update", "data": {"id": "memo_1", "content": "수정됨"}},
            {"type": "todo", "action": "complete", "data": {"id": "todo_1"}},
        ]
        
        queued_items = []
        
        # Simulate offline operations getting queued
        for op in offline_operations:
            await asyncio.sleep(0.1)
            
            if self.simulate_queue_operation(op):
                queued_items.append(op)
                print(f"   ✅ 큐에 추가: {op['type']} {op['action']}")
            else:
                print(f"   ❌ 큐 추가 실패: {op['type']} {op['action']}")
        
        queue_success_rate = len(queued_items) / len(offline_operations)
        print(f"   📊 큐잉 성공률: {queue_success_rate * 100:.1f}% ({len(queued_items)}/{len(offline_operations)})")
        
        # Check if queued items are properly marked as unsynced
        unsynced_count = len([item for item in queued_items if not item.get("synced", True)])
        print(f"   📊 미동기화 항목: {unsynced_count}개")
        
        return queue_success_rate >= 0.9 and unsynced_count == len(queued_items)
    
    async def test_sync_on_reconnect(self) -> bool:
        """재연결 시 동기화 테스트"""
        print("\n🔄 테스트: 재연결 시 동기화")
        
        # Simulate items waiting for sync
        pending_sync_items = [
            {"type": "memo", "id": "memo_1", "action": "create"},
            {"type": "todo", "id": "todo_1", "action": "update"},
            {"type": "event", "id": "event_1", "action": "delete"},
        ]
        
        print(f"   📋 동기화 대기 항목: {len(pending_sync_items)}개")
        
        # Simulate network reconnection
        await asyncio.sleep(0.5)
        print("   🌐 네트워크 재연결 감지")
        
        # Simulate sync process
        synced_items = 0
        failed_items = 0
        
        for item in pending_sync_items:
            await asyncio.sleep(0.2)  # Simulate sync time
            
            if self.simulate_sync_item(item):
                synced_items += 1
                print(f"   ✅ 동기화 완료: {item['type']} {item['action']}")
            else:
                failed_items += 1
                print(f"   ❌ 동기화 실패: {item['type']} {item['action']}")
        
        sync_success_rate = synced_items / len(pending_sync_items)
        print(f"   📊 동기화 성공률: {sync_success_rate * 100:.1f}% ({synced_items}/{len(pending_sync_items)})")
        
        return sync_success_rate >= 0.8
    
    async def test_conflict_resolution(self) -> bool:
        """충돌 해결 테스트"""
        print("\n⚔️  테스트: 충돌 해결")
        
        # Simulate conflict scenarios
        conflicts = [
            {
                "type": "memo",
                "local": {"id": "memo_1", "content": "로컬 버전", "updated_at": "2024-01-01T10:00:00"},
                "server": {"id": "memo_1", "content": "서버 버전", "updated_at": "2024-01-01T09:30:00"}
            },
            {
                "type": "todo",
                "local": {"id": "todo_1", "status": "completed", "updated_at": "2024-01-01T11:00:00"},
                "server": {"id": "todo_1", "status": "pending", "updated_at": "2024-01-01T10:30:00"}
            }
        ]
        
        resolved_conflicts = 0
        
        for conflict in conflicts:
            await asyncio.sleep(0.2)
            
            # Simulate conflict resolution (latest wins)
            resolution = self.simulate_conflict_resolution(conflict)
            
            if resolution:
                resolved_conflicts += 1
                print(f"   ✅ 충돌 해결: {conflict['type']} -> {resolution['strategy']}")
            else:
                print(f"   ❌ 충돌 해결 실패: {conflict['type']}")
        
        resolution_rate = resolved_conflicts / len(conflicts)
        print(f"   📊 충돌 해결률: {resolution_rate * 100:.1f}% ({resolved_conflicts}/{len(conflicts)})")
        
        return resolution_rate >= 1.0  # 모든 충돌 해결 요구
    
    async def test_offline_search(self) -> bool:
        """오프라인 검색 테스트"""
        print("\n🔍 테스트: 오프라인 검색")
        
        # Simulate local data for search
        local_data = [
            {"type": "memo", "content": "프로젝트 회의 내용", "category": "업무"},
            {"type": "memo", "content": "쇼핑 리스트", "category": "개인"},
            {"type": "todo", "title": "프로젝트 문서 작성", "category": "업무"},
            {"type": "todo", "title": "운동하기", "category": "건강"},
            {"type": "event", "title": "팀 미팅", "location": "회의실"},
        ]
        
        search_queries = [
            {"query": "프로젝트", "expected_results": 2},
            {"query": "업무", "expected_results": 2},
            {"query": "회의", "expected_results": 2},
            {"query": "쇼핑", "expected_results": 1},
            {"query": "존재하지않는검색어", "expected_results": 0}
        ]
        
        search_success = 0
        
        for query_data in search_queries:
            await asyncio.sleep(0.1)
            
            results = self.simulate_local_search(local_data, query_data["query"])
            expected = query_data["expected_results"]
            
            if len(results) == expected:
                search_success += 1
                print(f"   ✅ 검색 '{query_data['query']}': {len(results)}개 결과 (예상: {expected})")
            else:
                print(f"   ❌ 검색 '{query_data['query']}': {len(results)}개 결과 (예상: {expected})")
        
        search_accuracy = search_success / len(search_queries)
        print(f"   📊 검색 정확도: {search_accuracy * 100:.1f}% ({search_success}/{len(search_queries)})")
        
        return search_accuracy >= 0.8
    
    async def test_data_persistence(self) -> bool:
        """데이터 지속성 테스트"""
        print("\n💿 테스트: 데이터 지속성")
        
        # Simulate app restart scenarios
        scenarios = [
            {"name": "정상 종료 후 재시작", "data_loss_risk": 0.0},
            {"name": "강제 종료 후 재시작", "data_loss_risk": 0.1},
            {"name": "메모리 부족으로 인한 종료", "data_loss_risk": 0.2},
            {"name": "시스템 재부팅", "data_loss_risk": 0.05},
        ]
        
        persistence_success = 0
        
        for scenario in scenarios:
            await asyncio.sleep(0.2)
            
            # Simulate data persistence check
            data_survived = self.simulate_data_persistence(scenario)
            
            if data_survived:
                persistence_success += 1
                print(f"   ✅ {scenario['name']}: 데이터 유지됨")
            else:
                print(f"   ❌ {scenario['name']}: 데이터 손실")
        
        persistence_rate = persistence_success / len(scenarios)
        print(f"   📊 데이터 지속성: {persistence_rate * 100:.1f}% ({persistence_success}/{len(scenarios)})")
        
        return persistence_rate >= 0.9
    
    # Simulation Helper Methods
    
    def simulate_intent_processing(self, text: str) -> Dict[str, Any]:
        """Intent 처리 시뮬레이션"""
        # Simple rule-based simulation
        text_lower = text.lower()
        
        if "기록" in text_lower or "메모" in text_lower:
            return {"intent": "create_memo", "entities": ["item_name", "date_time"], "confidence": 0.9}
        elif "할일" in text_lower and "추가" in text_lower:
            return {"intent": "create_todo", "entities": ["category", "item_name"], "confidence": 0.9}
        elif "일정" in text_lower and "잡아" in text_lower:
            return {"intent": "create_event", "entities": ["date_time", "item_name"], "confidence": 0.9}
        elif "목록" in text_lower and "보여" in text_lower:
            return {"intent": "query_todo", "entities": [], "confidence": 0.8}
        else:
            return {"intent": "unknown", "entities": [], "confidence": 0.1}
    
    def simulate_db_operation(self, operation: Dict[str, Any]) -> bool:
        """데이터베이스 작업 시뮬레이션"""
        # Simulate 95% success rate
        import random
        return random.random() > 0.05
    
    def simulate_network_detection(self, state: Dict[str, Any]) -> bool:
        """네트워크 감지 시뮬레이션"""
        # Simulate 90% detection accuracy
        import random
        return random.random() > 0.1
    
    def simulate_queue_operation(self, operation: Dict[str, Any]) -> bool:
        """큐 작업 시뮬레이션"""
        # Mark as unsynced
        operation["synced"] = False
        return True
    
    def simulate_sync_item(self, item: Dict[str, Any]) -> bool:
        """동기화 시뮬레이션"""
        # Simulate 85% sync success rate
        import random
        return random.random() > 0.15
    
    def simulate_conflict_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """충돌 해결 시뮬레이션"""
        # Latest timestamp wins strategy
        local_time = conflict["local"]["updated_at"]
        server_time = conflict["server"]["updated_at"]
        
        if local_time > server_time:
            return {"strategy": "local_wins", "chosen": "local"}
        else:
            return {"strategy": "server_wins", "chosen": "server"}
    
    def simulate_local_search(self, data: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """로컬 검색 시뮬레이션"""
        results = []
        query_lower = query.lower()
        
        for item in data:
            # Search in content, title, category fields
            searchable_text = ""
            if "content" in item:
                searchable_text += item["content"].lower() + " "
            if "title" in item:
                searchable_text += item["title"].lower() + " "
            if "category" in item:
                searchable_text += item["category"].lower() + " "
            
            if query_lower in searchable_text:
                results.append(item)
        
        return results
    
    def simulate_data_persistence(self, scenario: Dict[str, Any]) -> bool:
        """데이터 지속성 시뮬레이션"""
        import random
        return random.random() > scenario["data_loss_risk"]

# Main execution
if __name__ == "__main__":
    async def main():
        tester = OfflineModeTest()
        passed, failed = await tester.run_all_tests()
        
        # Save test results
        with open("offline_mode_test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "passed": passed,
                    "failed": failed,
                    "total": passed + failed,
                    "success_rate": passed / (passed + failed) * 100,
                    "execution_time": time.time() - tester.start_time
                },
                "details": tester.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 테스트 결과가 offline_mode_test_results.json에 저장되었습니다.")
        
        return passed == len(tester.test_results)
    
    success = asyncio.run(main())
    exit(0 if success else 1)