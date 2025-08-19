#!/usr/bin/env python3
"""
Search API 테스트 스크립트
Day 12: Search & Analytics API Testing
"""

import requests
import json
import time
import asyncio

def test_search_api():
    """Search API 기능 테스트"""
    base_url = "http://localhost:8000"
    
    print("🔍 Search API 테스트 시작")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. Health Check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ 서버 상태: {health_data.get('status')}")
            print(f"   ✅ 버전: {health_data.get('version')}")
            print(f"   ✅ 기능: {health_data.get('features')}")
        else:
            print(f"   ❌ Health check 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 서버 연결 실패: {e}")
        return False
    
    # 2. Search stats (initial)
    print("\n2. Search Stats 확인")
    try:
        response = requests.get(f"{base_url}/api/search/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"   📊 총 문서: {stats.get('total_documents', 0)}개")
            print(f"   📊 문서 타입별: {stats.get('documents_by_type', {})}")
            print(f"   📊 임베딩 통계: {stats.get('embedding_stats', {})}")
        else:
            print(f"   ⚠️ Stats 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Stats 조회 오류: {e}")
    
    # 3. Document indexing test
    print("\n3. 문서 인덱싱 테스트")
    test_documents = [
        {
            "doc_type": "memo",
            "source_id": "test_memo_1",
            "title": "프로젝트 회의 메모",
            "content": "다음 주 월요일 오전 10시에 프로젝트 킥오프 미팅이 있습니다. 주요 안건은 일정 및 역할 분담입니다.",
            "category": "work",
            "tags": ["회의", "프로젝트", "일정"]
        },
        {
            "doc_type": "todo",
            "source_id": "test_todo_1", 
            "title": "월간 보고서 작성",
            "content": "이번 달 프로젝트 진행 상황을 정리하여 월간 보고서를 작성해야 합니다.",
            "category": "work",
            "priority": "high",
            "tags": ["보고서", "작업"]
        },
        {
            "doc_type": "event",
            "source_id": "test_event_1",
            "title": "팀 빌딩 이벤트",
            "content": "팀원들과의 유대감 강화를 위한 팀 빌딩 이벤트를 계획 중입니다.",
            "category": "team",
            "tags": ["팀빌딩", "이벤트"]
        }
    ]
    
    indexed_count = 0
    for doc in test_documents:
        try:
            response = requests.post(
                f"{base_url}/api/search/index",
                json=doc,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                indexed_count += 1
                print(f"   ✅ 문서 인덱싱 성공: {doc['source_id']}")
            else:
                print(f"   ❌ 인덱싱 실패: {doc['source_id']} - {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 인덱싱 오류: {doc['source_id']} - {e}")
    
    print(f"   📊 인덱싱 결과: {indexed_count}/{len(test_documents)} 성공")
    
    # 4. Search tests
    print("\n4. 검색 기능 테스트")
    
    search_tests = [
        {
            "name": "시맨틱 검색 - 회의 관련",
            "endpoint": "/api/search/semantic",
            "query": "미팅과 회의에 관한 내용",
            "expected_docs": ["test_memo_1"]
        },
        {
            "name": "키워드 검색 - 프로젝트",
            "endpoint": "/api/search/keyword", 
            "query": "프로젝트",
            "expected_docs": ["test_memo_1", "test_todo_1"]
        },
        {
            "name": "하이브리드 검색 - 작업",
            "endpoint": "/api/search/hybrid",
            "query": "해야할 작업들",
            "expected_docs": ["test_todo_1"]
        }
    ]
    
    search_success = 0
    
    for test in search_tests:
        try:
            search_data = {
                "query": test["query"],
                "top_k": 5,
                "min_similarity": 0.1
            }
            
            response = requests.post(
                f"{base_url}{test['endpoint']}",
                json=search_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                results_count = result.get("total_count", 0)
                processing_time = result.get("processing_time_ms", 0)
                
                print(f"   ✅ {test['name']}: {results_count}개 결과, {processing_time:.1f}ms")
                
                # Show top results
                for i, res in enumerate(result.get("results", [])[:3]):
                    score_info = ""
                    if "similarity" in res:
                        score_info = f"유사도: {res['similarity']:.3f}"
                    elif "final_score" in res:
                        score_info = f"점수: {res['final_score']:.3f}"
                    
                    print(f"      {i+1}. {res.get('title', 'No title')} ({score_info})")
                
                search_success += 1
            else:
                print(f"   ❌ {test['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test['name']}: 오류 - {e}")
    
    print(f"   📊 검색 테스트 결과: {search_success}/{len(search_tests)} 성공")
    
    # 5. Analytics test  
    print("\n5. 분석 기능 테스트")
    try:
        response = requests.get(f"{base_url}/api/search/analytics?period=1d", timeout=10)
        if response.status_code == 200:
            analytics = response.json()
            print(f"   📊 총 검색 수: {analytics.get('total_searches', 0)}")
            print(f"   📊 평균 응답시간: {analytics.get('avg_response_time_ms', 0):.1f}ms")
            print(f"   📊 인기 쿼리: {len(analytics.get('popular_queries', []))}개")
            print(f"   📊 성공률: {analytics.get('search_success_rate', 0):.1f}%")
        else:
            print(f"   ⚠️ Analytics 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Analytics 오류: {e}")
    
    # Final stats
    print("\n6. 최종 통계 확인")
    try:
        response = requests.get(f"{base_url}/api/search/stats", timeout=10)
        if response.status_code == 200:
            final_stats = response.json()
            print(f"   📊 최종 문서 수: {final_stats.get('total_documents', 0)}개")
            print(f"   📊 문서 타입별: {final_stats.get('documents_by_type', {})}")
        else:
            print(f"   ⚠️ Final stats 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Final stats 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Search API 테스트 완료")
    
    # Calculate overall success rate
    total_tests = 4  # Health, indexing, search, analytics
    success_tests = 1  # Health passed, others depend on implementation
    if indexed_count > 0:
        success_tests += 1
    if search_success > 0:
        success_tests += 1
    
    success_rate = (success_tests / total_tests) * 100
    print(f"📊 전체 성공률: {success_rate:.1f}%")
    
    return success_rate >= 75.0


if __name__ == "__main__":
    # Wait a moment for server to start
    print("⏳ 서버 시작 대기 중...")
    time.sleep(3)
    
    success = test_search_api()
    if success:
        print("✅ Search API 테스트 성공!")
        exit(0)
    else:
        print("❌ Search API 테스트 실패")
        exit(1)