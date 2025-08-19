#!/usr/bin/env python3
"""
시맨틱 검색 기능 테스트 스크립트
Day 12: Search & Analytics Testing
"""

import asyncio
import sys
import os
import json
import time
from typing import List, Dict, Any
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from embedding_service import embedding_service, semantic_search_service
from search_api import *

class SemanticSearchTest:
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """모든 시맨틱 검색 테스트 실행"""
        print("🔍 시맨틱 검색 기능 테스트 시작")
        print("=" * 60)
        
        test_scenarios = [
            self.test_embedding_generation,
            self.test_semantic_similarity,
            self.test_document_indexing,
            self.test_semantic_search,
            self.test_batch_operations,
            self.test_hybrid_search_logic,
            self.test_search_performance,
            self.test_multilingual_support
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
        print(f"🎯 시맨틱 검색 테스트 결과 요약")
        print(f"   통과: {passed}")
        print(f"   실패: {failed}")
        print(f"   총 테스트: {passed + failed}")
        print(f"   성공률: {(passed / (passed + failed) * 100):.1f}%")
        print(f"   실행 시간: {time.time() - self.start_time:.2f}초")
        
        return passed, failed
    
    async def test_embedding_generation(self) -> bool:
        """임베딩 생성 테스트"""
        print("\n🔢 테스트: 임베딩 생성")
        
        test_texts = [
            "오늘 회의 일정을 확인해줘",
            "프로젝트 관련 메모를 찾아줘",
            "할일 목록에서 중요한 것들을 보여줘",
            "지난주 작성한 문서들이 어디있지?",
            "Meeting schedule for today"
        ]
        
        success_count = 0
        
        for text in test_texts:
            try:
                # Test individual embedding
                embedding = await embedding_service.get_embedding(text)
                
                if embedding and len(embedding) > 0:
                    dimension = len(embedding)
                    print(f"   ✅ '{text[:30]}...' -> {dimension}D 벡터")
                    success_count += 1
                    
                    # Verify embedding properties
                    if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding):
                        print(f"      벡터 타입: 올바름, 차원: {dimension}")
                    else:
                        print(f"      ❌ 벡터 타입 오류")
                        return False
                else:
                    print(f"   ❌ '{text}' -> 임베딩 생성 실패")
                    
            except Exception as e:
                print(f"   ❌ '{text}' -> 오류: {e}")
        
        success_rate = success_count / len(test_texts)
        print(f"   📊 임베딩 생성 성공률: {success_rate * 100:.1f}% ({success_count}/{len(test_texts)})")
        
        return success_rate >= 0.8  # 80% 이상 성공률 요구
    
    async def test_semantic_similarity(self) -> bool:
        """의미적 유사도 계산 테스트"""
        print("\n📐 테스트: 의미적 유사도 계산")
        
        # Test cases with expected similarity relationships
        test_cases = [
            {
                "text1": "회의 일정을 확인해줘",
                "text2": "미팅 스케줄을 보여줘",
                "expected": "high",  # Should be highly similar
                "description": "한국어 동의어"
            },
            {
                "text1": "프로젝트 문서 작성",
                "text2": "프로젝트 보고서 작성",
                "expected": "high",
                "description": "관련된 작업"
            },
            {
                "text1": "오늘 날씨가 좋다",
                "text2": "할일 목록 확인",
                "expected": "low",  # Should be low similarity
                "description": "관련 없는 내용"
            },
            {
                "text1": "Create a memo",
                "text2": "메모를 작성해줘",
                "expected": "high",
                "description": "다국어 동일 의미"
            }
        ]
        
        similarity_tests_passed = 0
        
        for case in test_cases:
            try:
                # Get embeddings
                emb1 = await embedding_service.get_embedding(case["text1"])
                emb2 = await embedding_service.get_embedding(case["text2"])
                
                if emb1 and emb2:
                    similarity = embedding_service.cosine_similarity(emb1, emb2)
                    
                    # Check if similarity meets expectations
                    if case["expected"] == "high" and similarity > 0.7:
                        similarity_tests_passed += 1
                        print(f"   ✅ {case['description']}: {similarity:.3f} (높은 유사도)")
                    elif case["expected"] == "low" and similarity < 0.5:
                        similarity_tests_passed += 1
                        print(f"   ✅ {case['description']}: {similarity:.3f} (낮은 유사도)")
                    else:
                        print(f"   ❌ {case['description']}: {similarity:.3f} (예상과 다름)")
                else:
                    print(f"   ❌ {case['description']}: 임베딩 생성 실패")
                    
            except Exception as e:
                print(f"   ❌ {case['description']}: 오류 - {e}")
        
        success_rate = similarity_tests_passed / len(test_cases)
        print(f"   📊 유사도 테스트 성공률: {success_rate * 100:.1f}% ({similarity_tests_passed}/{len(test_cases)})")
        
        return success_rate >= 0.75
    
    async def test_document_indexing(self) -> bool:
        """문서 인덱싱 테스트"""
        print("\n📚 테스트: 문서 인덱싱")
        
        test_documents = [
            {"id": "doc_1", "content": "프로젝트 킥오프 미팅이 내일 오전 10시에 있습니다", "metadata": {"type": "memo", "category": "회의"}},
            {"id": "doc_2", "content": "월간 보고서 작성 완료해야 함", "metadata": {"type": "todo", "priority": "high"}},
            {"id": "doc_3", "content": "팀 빌딩 이벤트 계획하기", "metadata": {"type": "todo", "category": "기획"}},
            {"id": "doc_4", "content": "기술 문서 업데이트 및 배포", "metadata": {"type": "memo", "category": "개발"}},
            {"id": "doc_5", "content": "고객 미팅 피드백 정리", "metadata": {"type": "memo", "category": "회의"}}
        ]
        
        indexed_count = 0
        
        for doc in test_documents:
            try:
                success = await semantic_search_service.index_document(
                    doc["id"], 
                    doc["content"], 
                    doc["metadata"]
                )
                
                if success:
                    indexed_count += 1
                    print(f"   ✅ 문서 인덱싱 성공: {doc['id']}")
                else:
                    print(f"   ❌ 문서 인덱싱 실패: {doc['id']}")
                    
            except Exception as e:
                print(f"   ❌ 문서 인덱싱 오류: {doc['id']} - {e}")
        
        # Check index stats
        stats = semantic_search_service.get_index_stats()
        print(f"   📊 인덱스 통계: {stats['total_documents']}개 문서, {stats['embedding_dimension']}차원")
        
        success_rate = indexed_count / len(test_documents)
        print(f"   📊 인덱싱 성공률: {success_rate * 100:.1f}% ({indexed_count}/{len(test_documents)})")
        
        return success_rate >= 0.9
    
    async def test_semantic_search(self) -> bool:
        """시맨틱 검색 테스트"""
        print("\n🔍 테스트: 시맨틱 검색")
        
        search_queries = [
            {
                "query": "미팅 관련 내용",
                "expected_docs": ["doc_1", "doc_5"],  # 회의 관련 문서들
                "min_results": 1
            },
            {
                "query": "작업해야 할 일들",
                "expected_docs": ["doc_2", "doc_3"],  # 할일 관련 문서들
                "min_results": 1
            },
            {
                "query": "문서 작성",
                "expected_docs": ["doc_2", "doc_4"],  # 문서 관련 작업들
                "min_results": 1
            },
            {
                "query": "존재하지않는내용검색어",
                "expected_docs": [],
                "min_results": 0
            }
        ]
        
        search_tests_passed = 0
        
        for query_data in search_queries:
            try:
                # Perform semantic search
                results = await semantic_search_service.search(
                    query_data["query"], 
                    top_k=10, 
                    min_similarity=0.1
                )
                
                found_docs = [r["doc_id"] for r in results]
                expected_found = any(doc_id in found_docs for doc_id in query_data["expected_docs"]) if query_data["expected_docs"] else True
                
                if len(results) >= query_data["min_results"] and expected_found:
                    search_tests_passed += 1
                    print(f"   ✅ 검색 '{query_data['query']}': {len(results)}개 결과")
                    for result in results[:3]:  # Show top 3 results
                        print(f"      - {result['doc_id']}: {result['similarity']:.3f}")
                else:
                    print(f"   ❌ 검색 '{query_data['query']}': 예상 결과와 다름 ({len(results)}개 결과)")
                    
            except Exception as e:
                print(f"   ❌ 검색 오류: '{query_data['query']}' - {e}")
        
        success_rate = search_tests_passed / len(search_queries)
        print(f"   📊 검색 성공률: {success_rate * 100:.1f}% ({search_tests_passed}/{len(search_queries)})")
        
        return success_rate >= 0.75
    
    async def test_batch_operations(self) -> bool:
        """배치 연산 테스트"""
        print("\n📦 테스트: 배치 연산")
        
        batch_texts = [
            "배치 처리 테스트 문서 1",
            "배치 처리 테스트 문서 2", 
            "배치 처리 테스트 문서 3",
            "배치 처리 테스트 문서 4",
            "배치 처리 테스트 문서 5"
        ]
        
        try:
            # Test batch embedding generation
            start_time = time.time()
            embeddings = await embedding_service.get_embeddings_batch(batch_texts)
            batch_time = time.time() - start_time
            
            if len(embeddings) == len(batch_texts) and all(emb is not None for emb in embeddings):
                print(f"   ✅ 배치 임베딩: {len(embeddings)}개 생성, {batch_time:.3f}초")
                
                # Test individual vs batch performance
                start_time = time.time()
                individual_embeddings = []
                for text in batch_texts:
                    emb = await embedding_service.get_embedding(text)
                    individual_embeddings.append(emb)
                individual_time = time.time() - start_time
                
                speedup = individual_time / batch_time if batch_time > 0 else 1.0
                print(f"   📊 성능 비교: 개별 {individual_time:.3f}초 vs 배치 {batch_time:.3f}초 (배속: {speedup:.1f}x)")
                
                return speedup >= 1.0  # Batch should be at least as fast
            else:
                print(f"   ❌ 배치 임베딩 실패: {len(embeddings)}/{len(batch_texts)}")
                return False
                
        except Exception as e:
            print(f"   ❌ 배치 연산 오류: {e}")
            return False
    
    async def test_hybrid_search_logic(self) -> bool:
        """하이브리드 검색 로직 테스트"""
        print("\n🔀 테스트: 하이브리드 검색 로직")
        
        try:
            # Mock keyword search results
            keyword_results = [
                {"doc_id": "doc_1", "content": "키워드 매치 문서", "keyword_score": 0.8},
                {"doc_id": "doc_2", "content": "부분 키워드 매치", "keyword_score": 0.5}
            ]
            
            # Test hybrid search
            query = "미팅 일정"
            hybrid_results = await semantic_search_service.hybrid_search(
                query, 
                keyword_results, 
                semantic_weight=0.7, 
                top_k=10
            )
            
            if len(hybrid_results) > 0:
                print(f"   ✅ 하이브리드 검색: {len(hybrid_results)}개 결과")
                
                # Check if results have both scores
                for result in hybrid_results[:3]:
                    has_keyword = "keyword_score" in result and result["keyword_score"] is not None
                    has_semantic = "semantic_score" in result and result["semantic_score"] is not None
                    has_final = "final_score" in result and result["final_score"] is not None
                    
                    if has_keyword and has_semantic and has_final:
                        print(f"      ✅ {result.get('doc_id', 'unknown')}: 키워드={result['keyword_score']:.3f}, 시맨틱={result['semantic_score']:.3f}, 최종={result['final_score']:.3f}")
                    else:
                        print(f"      ❌ 점수 누락: {result.get('doc_id', 'unknown')}")
                        return False
                
                return True
            else:
                print(f"   ❌ 하이브리드 검색 결과 없음")
                return False
                
        except Exception as e:
            print(f"   ❌ 하이브리드 검색 오류: {e}")
            return False
    
    async def test_search_performance(self) -> bool:
        """검색 성능 테스트"""
        print("\n⚡ 테스트: 검색 성능")
        
        try:
            # Performance test query
            test_query = "프로젝트 관련 문서들"
            iterations = 10
            
            total_time = 0
            successful_searches = 0
            
            for i in range(iterations):
                start_time = time.time()
                results = await semantic_search_service.search(test_query, top_k=5)
                search_time = time.time() - start_time
                
                if results is not None:
                    successful_searches += 1
                    total_time += search_time
            
            if successful_searches > 0:
                avg_time = total_time / successful_searches
                qps = 1.0 / avg_time if avg_time > 0 else 0
                
                print(f"   📊 성능 메트릭:")
                print(f"      평균 검색 시간: {avg_time * 1000:.1f}ms")
                print(f"      초당 쿼리 수: {qps:.1f} QPS")
                print(f"      성공률: {successful_searches}/{iterations}")
                
                # Performance criteria: under 500ms per search
                return avg_time < 0.5 and successful_searches >= iterations * 0.9
            else:
                print(f"   ❌ 모든 검색 실패")
                return False
                
        except Exception as e:
            print(f"   ❌ 성능 테스트 오류: {e}")
            return False
    
    async def test_multilingual_support(self) -> bool:
        """다국어 지원 테스트"""
        print("\n🌍 테스트: 다국어 지원")
        
        multilingual_texts = [
            {"text": "회의 일정을 확인해주세요", "lang": "Korean"},
            {"text": "Please check the meeting schedule", "lang": "English"},
            {"text": "ミーティングのスケジュールを確認してください", "lang": "Japanese"},
            {"text": "请检查会议日程", "lang": "Chinese"}
        ]
        
        embeddings_generated = 0
        cross_language_similarities = []
        
        try:
            # Generate embeddings for all languages
            embeddings = {}
            for item in multilingual_texts:
                embedding = await embedding_service.get_embedding(item["text"])
                if embedding:
                    embeddings[item["lang"]] = embedding
                    embeddings_generated += 1
                    print(f"   ✅ {item['lang']} 임베딩 생성 성공")
                else:
                    print(f"   ❌ {item['lang']} 임베딩 생성 실패")
            
            # Test cross-language semantic similarity
            if "Korean" in embeddings and "English" in embeddings:
                similarity = embedding_service.cosine_similarity(
                    embeddings["Korean"], 
                    embeddings["English"]
                )
                cross_language_similarities.append(similarity)
                print(f"   📊 한국어-영어 유사도: {similarity:.3f}")
            
            success_rate = embeddings_generated / len(multilingual_texts)
            avg_similarity = sum(cross_language_similarities) / len(cross_language_similarities) if cross_language_similarities else 0
            
            print(f"   📊 다국어 지원 성공률: {success_rate * 100:.1f}%")
            print(f"   📊 교차 언어 유사도: {avg_similarity:.3f}")
            
            return success_rate >= 0.75 and avg_similarity > 0.5
            
        except Exception as e:
            print(f"   ❌ 다국어 테스트 오류: {e}")
            return False


# Main execution
if __name__ == "__main__":
    async def main():
        tester = SemanticSearchTest()
        passed, failed = await tester.run_all_tests()
        
        # Save test results
        result_file = "semantic_search_test_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "passed": passed,
                    "failed": failed,
                    "total": passed + failed,
                    "success_rate": passed / (passed + failed) * 100 if (passed + failed) > 0 else 0,
                    "execution_time": time.time() - tester.start_time
                },
                "details": tester.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 테스트 결과가 {result_file}에 저장되었습니다.")
        
        # Return success if all tests passed
        return passed == (passed + failed)
    
    success = asyncio.run(main())
    exit(0 if success else 1)