"""
Advanced Search Features
Day 12: Natural Language Query Processing & Advanced Filtering
"""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import calendar

from embedding_service import embedding_service
from nlu_service import get_nlu_service

logger = logging.getLogger(__name__)

class QueryProcessor:
    """
    자연어 검색 쿼리 처리기
    사용자의 자연어 질의를 구조화된 검색 파라미터로 변환
    """
    
    def __init__(self):
        self.nlu_service = None
        self._init_patterns()
    
    def _init_patterns(self):
        """검색 패턴 초기화"""
        
        # 날짜 관련 패턴
        self.date_patterns = {
            "today": ["오늘", "today"],
            "yesterday": ["어제", "yesterday"],
            "tomorrow": ["내일", "tomorrow"],
            "this_week": ["이번 주", "이번주", "this week"],
            "last_week": ["지난 주", "지난주", "last week"],
            "this_month": ["이번 달", "이번달", "this month"],
            "last_month": ["지난 달", "지난달", "last month"]
        }
        
        # 우선순위 패턴
        self.priority_patterns = {
            "high": ["중요한", "urgent", "높은", "high", "긴급", "급한"],
            "medium": ["보통", "medium", "일반적인"],
            "low": ["낮은", "low", "나중에"]
        }
        
        # 카테고리 패턴
        self.category_patterns = {
            "work": ["업무", "일", "work", "프로젝트", "project", "회사"],
            "personal": ["개인", "personal", "private", "사적인"],
            "meeting": ["회의", "meeting", "미팅", "만남"],
            "todo": ["할일", "todo", "task", "작업"],
            "memo": ["메모", "memo", "note", "기록"],
            "event": ["일정", "event", "스케줄", "schedule"]
        }
        
        # 상태 패턴
        self.status_patterns = {
            "completed": ["완료된", "finished", "done", "completed"],
            "pending": ["대기중인", "pending", "미완료", "할일"],
            "in_progress": ["진행중인", "ongoing", "working on"]
        }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        자연어 쿼리를 구조화된 검색 파라미터로 변환
        
        Args:
            query: 자연어 검색 쿼리
            
        Returns:
            구조화된 검색 파라미터
        """
        try:
            # Initialize NLU service if needed
            if not self.nlu_service:
                self.nlu_service = get_nlu_service()
            
            # Extract components from query
            date_filters = self._extract_date_filters(query)
            category_filters = self._extract_category_filters(query)
            priority_filters = self._extract_priority_filters(query)
            status_filters = self._extract_status_filters(query)
            
            # Extract search intent and clean query
            search_intent = await self._analyze_search_intent(query)
            clean_query = self._clean_query_for_search(query)
            
            # Determine search type based on query characteristics
            search_type = self._determine_search_type(query, search_intent)
            
            return {
                "clean_query": clean_query,
                "original_query": query,
                "search_type": search_type,
                "search_intent": search_intent,
                "filters": {
                    "date_range": date_filters,
                    "categories": category_filters,
                    "priorities": priority_filters,
                    "statuses": status_filters
                },
                "ranking_factors": self._extract_ranking_factors(query)
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "clean_query": query,
                "original_query": query,
                "search_type": "hybrid",
                "search_intent": {"intent": "search_general", "confidence": 0.5},
                "filters": {},
                "ranking_factors": {}
            }
    
    def _extract_date_filters(self, query: str) -> Optional[Dict[str, datetime]]:
        """날짜 필터 추출"""
        query_lower = query.lower()
        now = datetime.now()
        
        # Check relative date patterns
        for date_type, patterns in self.date_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                if date_type == "today":
                    return {
                        "start": now.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": now.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif date_type == "yesterday":
                    yesterday = now - timedelta(days=1)
                    return {
                        "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif date_type == "tomorrow":
                    tomorrow = now + timedelta(days=1)
                    return {
                        "start": tomorrow.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif date_type == "this_week":
                    start_week = now - timedelta(days=now.weekday())
                    end_week = start_week + timedelta(days=6)
                    return {
                        "start": start_week.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": end_week.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif date_type == "last_week":
                    start_week = now - timedelta(days=now.weekday() + 7)
                    end_week = start_week + timedelta(days=6)
                    return {
                        "start": start_week.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": end_week.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif date_type == "this_month":
                    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    _, last_day = calendar.monthrange(now.year, now.month)
                    end_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
                    return {
                        "start": start_month,
                        "end": end_month
                    }
                elif date_type == "last_month":
                    if now.month == 1:
                        last_month_year = now.year - 1
                        last_month_month = 12
                    else:
                        last_month_year = now.year
                        last_month_month = now.month - 1
                    
                    start_month = datetime(last_month_year, last_month_month, 1)
                    _, last_day = calendar.monthrange(last_month_year, last_month_month)
                    end_month = datetime(last_month_year, last_month_month, last_day, 23, 59, 59, 999999)
                    return {
                        "start": start_month,
                        "end": end_month
                    }
        
        # Try to parse absolute dates
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})', query)
        if date_match:
            try:
                parsed_date = date_parser.parse(date_match.group(1))
                return {
                    "start": parsed_date.replace(hour=0, minute=0, second=0, microsecond=0),
                    "end": parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            except:
                pass
        
        return None
    
    def _extract_category_filters(self, query: str) -> List[str]:
        """카테고리 필터 추출"""
        query_lower = query.lower()
        categories = []
        
        for category, patterns in self.category_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                categories.append(category)
        
        return categories
    
    def _extract_priority_filters(self, query: str) -> List[str]:
        """우선순위 필터 추출"""
        query_lower = query.lower()
        priorities = []
        
        for priority, patterns in self.priority_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                priorities.append(priority)
        
        return priorities
    
    def _extract_status_filters(self, query: str) -> List[str]:
        """상태 필터 추출"""
        query_lower = query.lower()
        statuses = []
        
        for status, patterns in self.status_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                statuses.append(status)
        
        return statuses
    
    async def _analyze_search_intent(self, query: str) -> Dict[str, Any]:
        """검색 의도 분석"""
        try:
            if self.nlu_service:
                nlu_result = await self.nlu_service.analyze_intent(query)
                return {
                    "intent": nlu_result.intent.name,
                    "confidence": nlu_result.confidence,
                    "entities": nlu_result.entities
                }
        except Exception as e:
            logger.warning(f"NLU analysis failed: {e}")
        
        # Fallback to rule-based intent detection
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["찾아", "검색", "보여", "find", "search", "show"]):
            return {"intent": "search_general", "confidence": 0.7}
        elif any(word in query_lower for word in ["생성", "작성", "추가", "create", "add", "new"]):
            return {"intent": "create_item", "confidence": 0.7}
        elif any(word in query_lower for word in ["수정", "변경", "업데이트", "edit", "update", "modify"]):
            return {"intent": "update_item", "confidence": 0.7}
        elif any(word in query_lower for word in ["삭제", "제거", "delete", "remove"]):
            return {"intent": "delete_item", "confidence": 0.7}
        else:
            return {"intent": "search_general", "confidence": 0.5}
    
    def _clean_query_for_search(self, query: str) -> str:
        """검색을 위한 쿼리 정리"""
        # Remove date-related words
        for patterns in self.date_patterns.values():
            for pattern in patterns:
                query = re.sub(r'\b' + re.escape(pattern) + r'\b', '', query, flags=re.IGNORECASE)
        
        # Remove filter-related words
        filter_words = ["중요한", "완료된", "업무", "개인", "회의", "urgent", "important", "completed"]
        for word in filter_words:
            query = re.sub(r'\b' + re.escape(word) + r'\b', '', query, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _determine_search_type(self, query: str, search_intent: Dict[str, Any]) -> str:
        """검색 타입 결정"""
        # If high confidence intent for specific action, use semantic
        if search_intent.get("confidence", 0) > 0.8:
            return "semantic"
        
        # If query contains specific keywords, prefer keyword search
        if any(char in query for char in ['*', '"', '+', '-']):
            return "keyword"
        
        # For natural language queries, use hybrid
        if len(query.split()) > 3:
            return "hybrid"
        
        # Default to hybrid for best results
        return "hybrid"
    
    def _extract_ranking_factors(self, query: str) -> Dict[str, float]:
        """랭킹 요소 추출"""
        factors = {}
        
        # Recency boost for time-sensitive queries
        if any(word in query.lower() for word in ["최근", "recent", "새로운", "new", "latest"]):
            factors["recency_boost"] = 1.5
        
        # Relevance boost for specific domains
        if any(word in query.lower() for word in ["프로젝트", "project"]):
            factors["work_relevance"] = 1.2
        
        # Priority boost
        if any(word in query.lower() for word in ["중요", "urgent", "급한"]):
            factors["priority_boost"] = 1.3
        
        return factors


class RankingAlgorithm:
    """
    검색 결과 랭킹 알고리즘
    다양한 시그널을 조합하여 최적의 검색 결과 순서 결정
    """
    
    def __init__(self):
        self.default_weights = {
            "semantic_score": 0.4,
            "keyword_score": 0.3,
            "recency": 0.15,
            "priority": 0.1,
            "user_interaction": 0.05
        }
    
    def rank_results(self, results: List[Dict[str, Any]], 
                    ranking_factors: Dict[str, float] = None,
                    custom_weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        검색 결과 재랭킹
        
        Args:
            results: 검색 결과 리스트
            ranking_factors: 쿼리별 랭킹 요소
            custom_weights: 커스텀 가중치
            
        Returns:
            재랭킹된 검색 결과
        """
        if not results:
            return results
        
        weights = {**self.default_weights, **(custom_weights or {})}
        ranking_factors = ranking_factors or {}
        
        # Calculate composite scores
        for result in results:
            score = 0.0
            
            # Semantic similarity score
            semantic_score = result.get("semantic_score", 0.0)
            score += weights["semantic_score"] * semantic_score
            
            # Keyword relevance score
            keyword_score = result.get("keyword_score", 0.0)
            score += weights["keyword_score"] * keyword_score
            
            # Recency score
            recency_score = self._calculate_recency_score(result.get("created_at"))
            score += weights["recency"] * recency_score
            
            # Priority score
            priority_score = self._calculate_priority_score(result.get("priority"))
            score += weights["priority"] * priority_score
            
            # User interaction score (placeholder - would use actual click data)
            interaction_score = self._calculate_interaction_score(result.get("doc_id"))
            score += weights["user_interaction"] * interaction_score
            
            # Apply ranking factors
            for factor, boost in ranking_factors.items():
                if factor == "recency_boost":
                    score *= boost if recency_score > 0.5 else 1.0
                elif factor == "priority_boost":
                    score *= boost if priority_score > 0.5 else 1.0
                elif factor == "work_relevance":
                    if result.get("category") == "work":
                        score *= boost
            
            result["final_score"] = score
        
        # Sort by final score
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return results
    
    def _calculate_recency_score(self, created_at) -> float:
        """최신성 점수 계산"""
        if not created_at:
            return 0.0
        
        try:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            now = datetime.now()
            time_diff = now - created_at
            days_old = time_diff.total_seconds() / (24 * 3600)
            
            # Exponential decay: newer items get higher scores
            return max(0.0, 1.0 - (days_old / 30.0))  # 30일 기준
            
        except Exception:
            return 0.0
    
    def _calculate_priority_score(self, priority) -> float:
        """우선순위 점수 계산"""
        priority_map = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3,
            None: 0.5
        }
        return priority_map.get(priority, 0.5)
    
    def _calculate_interaction_score(self, doc_id) -> float:
        """사용자 상호작용 점수 계산 (실제 구현 시 클릭 데이터 사용)"""
        # Placeholder: 실제로는 데이터베이스에서 클릭/조회 데이터 가져옴
        return 0.5


class SmartSearchEngine:
    """
    지능형 검색 엔진
    자연어 쿼리 처리와 고급 랭킹을 결합한 종합 검색 시스템
    """
    
    def __init__(self):
        self.query_processor = QueryProcessor()
        self.ranking_algorithm = RankingAlgorithm()
    
    async def smart_search(self, query: str, top_k: int = 10, 
                          user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        지능형 검색 수행
        
        Args:
            query: 자연어 검색 쿼리
            top_k: 반환할 최대 결과 수
            user_context: 사용자 컨텍스트 정보
            
        Returns:
            검색 결과와 메타데이터
        """
        start_time = datetime.now()
        
        try:
            # Process natural language query
            processed_query = await self.query_processor.process_query(query)
            
            # Import here to avoid circular imports
            from search_api import semantic_search, keyword_search, hybrid_search
            from search_models import SearchRequest
            
            # Create search request
            search_request = SearchRequest(
                query=processed_query["clean_query"],
                search_type=processed_query["search_type"],
                filters=processed_query["filters"],
                top_k=top_k * 2  # Get more results for re-ranking
            )
            
            # Perform search based on determined type
            if processed_query["search_type"] == "semantic":
                # Note: This would need to be adapted for actual API call
                raw_results = []  # Placeholder
            elif processed_query["search_type"] == "keyword":
                raw_results = []  # Placeholder
            else:  # hybrid
                raw_results = []  # Placeholder
            
            # Re-rank results using advanced algorithm
            ranked_results = self.ranking_algorithm.rank_results(
                raw_results,
                processed_query["ranking_factors"],
                user_context.get("ranking_weights") if user_context else None
            )
            
            # Limit to requested number
            final_results = ranked_results[:top_k]
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "results": final_results,
                "query_analysis": processed_query,
                "total_found": len(raw_results),
                "returned_count": len(final_results),
                "processing_time_ms": processing_time,
                "search_metadata": {
                    "search_type_used": processed_query["search_type"],
                    "filters_applied": processed_query["filters"],
                    "ranking_factors": processed_query["ranking_factors"]
                }
            }
            
        except Exception as e:
            logger.error(f"Smart search failed: {e}")
            return {
                "results": [],
                "error": str(e),
                "query_analysis": {"clean_query": query, "original_query": query},
                "total_found": 0,
                "returned_count": 0,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }


# Global instance
smart_search_engine = SmartSearchEngine()