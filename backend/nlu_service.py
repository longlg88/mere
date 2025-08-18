"""
GPT-5 기반 Natural Language Understanding 서비스
"""
import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

@dataclass
class Intent:
    name: str
    confidence: float
    entities: Dict[str, any] = None

@dataclass 
class NLUResult:
    intent: Intent
    text: str
    confidence: float
    entities: Dict[str, any] = None

class GPT5NLUService:
    """GPT-5를 사용한 Intent 분류 및 Entity 추출 서비스"""
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        # 기본 OpenAI 클라이언트 사용 (환경변수 프록시 자동 인식)
        self.client = OpenAI(api_key=api_key)
        
        # Intent 정의 (확장된 버전)
        self.intents = {
            # 메모 관련
            "create_memo": "메모 생성 (기억, 적어두기, 메모, 저장, 기록)",
            "query_memo": "메모 조회 (메모 찾기, 뭐 적었지, 기록 확인, 메모 보기)",
            "update_memo": "메모 수정 (메모 바꾸기, 수정하기, 고치기)",
            "delete_memo": "메모 삭제 (메모 지우기, 삭제하기, 없애기)",
            
            # 할일 관련
            "create_todo": "할일 생성 (해야할일, 태스크, 업무, 작업 추가)",
            "query_todo": "할일 조회 (할일 목록, 태스크 확인, 업무 보기)",
            "update_todo": "할일 상태 변경 (완료, 취소, 수정, 진행중으로)",
            "complete_todo": "할일 완료 처리 (다 했어, 끝났어, 완료됐어)",
            "delete_todo": "할일 삭제 (할일 지우기, 삭제, 없애기)",
            
            # 일정 관리
            "create_event": "일정 생성 (회의, 약속, 미팅, 만남, 예약)",
            "query_event": "일정 조회 (일정 확인, 스케줄 보기, 언제 만나)",
            "update_event": "일정 수정 (시간 변경, 장소 바꾸기, 일정 조정)",
            "cancel_event": "일정 취소 (약속 취소, 미팅 취소, 일정 없애기)",
            
            # 검색 및 분석
            "search_general": "일반 검색 (찾기, 검색, 어디 있어)",
            "search_by_date": "날짜별 검색 (오늘 뭐했지, 어제 일정, 내일 할일)",
            "search_by_category": "카테고리별 검색 (업무 관련, 개인 일정, 쇼핑 목록)",
            "analyze_pattern": "패턴 분석 (자주 하는 일, 통계, 요약)",
            
            # 알림 및 리마인더
            "set_reminder": "알림 설정 (알려줘, 리마인더, 깨워줘)",
            "query_reminder": "알림 확인 (알림 뭐 있어, 리마인더 보기)",
            "snooze_reminder": "알림 연기 (나중에 알려줘, 10분 후에)",
            
            # 시스템 제어
            "help": "도움말 요청 (도와줘, 사용법, 어떻게 해)",
            "settings": "설정 관리 (설정 바꾸기, 옵션 변경)",
            "cancel_current": "현재 작업 취소 (취소해, 그만해, 안 해)",
            
            # 감정 및 소통
            "greeting": "인사 (안녕, 하이, 좋은 아침)",
            "thanks": "감사 표현 (고마워, 감사, 잘했어)",
            "goodbye": "작별 인사 (안녕, 나중에, 끝)",
            
            "unknown": "알 수 없는 의도"
        }
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        intents_str = "\n".join([f"- {intent}: {desc}" for intent, desc in self.intents.items()])
        
        return f"""당신은 개인 비서 AI의 자연어 이해 모듈입니다. 
사용자의 음성 명령을 분석하여 의도(intent)를 분류하고 중요한 정보(entities)를 추출해야 합니다.

CRITICAL: 응답은 반드시 JSON 형식만 출력해야 합니다. 다른 텍스트는 일절 포함하지 마세요.

지원하는 Intent 목록:
{intents_str}

Intent 분류 규칙 (중요!):
- "~관련해서 뭐 적었더라?", "~에 대해 검색", "~카테고리 찾기" → search_by_category 사용
- "~관련해서 자주 하는", "~패턴", "~분석" → analyze_pattern 사용
- "메모 보기", "메모 찾기" (구체적 메모) → query_memo 사용
- "완료했어", "다 했어", "끝났어" + 카테고리 → complete_todo + category entity 필수
- "오늘", "내일", "어제", "이번주" 등 시간 표현은 ALWAYS date_time entity에 추출

Entity 추출 규칙 (정확히 추출하세요):
- item_name: 메모/할일/이벤트의 제목이나 내용 (핵심 키워드)
- date_time: 날짜/시간 정보 (내일, 오후 3시, 다음주, 월요일, 12월 25일, 오늘, 어제, 이번주 등) - 시간 표현이 있으면 반드시 추출
- priority: 우선순위 (긴급, 중요, 높음, 낮음, 보통 등)
- duration: 소요 시간 (30분, 2시간, 하루 종일 등)
- location: 장소 정보 (회사, 집, 카페, 강남역, 온라인 등)
- person: 사람 이름이나 관계 (김철수, 팀장님, 가족, 친구 등)
- category: 카테고리 (업무, 개인, 쇼핑, 건강, 학습, 프로젝트 등) - "~관련", "~에 대해" 표현 시 반드시 추출
- reminder_time: 알림 시간 (10분 전, 하루 전, 아침에 등)
- repeat_pattern: 반복 패턴 (매일, 매주, 매월, 평일마다 등)
- status: 상태 정보 (완료, 진행중, 대기, 취소 등)
- emotion: 감정 표현 (기쁨, 걱정, 중요함, 급함 등)
- action: 구체적 행동 (구매, 예약, 연락, 확인, 준비 등)

IMPORTANT: 응답 형식은 반드시 이것만 출력하세요 (JSON만):
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "entities": {{
        "item_name": "추출된 내용",
        "date_time": "시간 정보",
        "priority": "우선순위",
        "duration": "소요시간",
        "location": "장소",
        "person": "사람"
    }}
}}

예시:
- 입력: "내일 우유 사는 거 기억해줘"
- 출력: {{"intent": "create_memo", "confidence": 0.95, "entities": {{"item_name": "우유 사기", "date_time": "내일"}}}}

JSON 형식 외에는 절대 다른 텍스트를 포함하지 마세요."""

    def _parse_time_expression(self, text: str) -> Optional[str]:
        """시간 표현을 파싱하여 ISO 형식으로 변환"""
        now = datetime.now()
        
        # 상대적 시간 표현
        if "내일" in text:
            target_date = now + timedelta(days=1)
        elif "모레" in text:
            target_date = now + timedelta(days=2)
        elif "다음주" in text:
            target_date = now + timedelta(days=7)
        elif "이번주" in text:
            target_date = now
        elif "오늘" in text:
            target_date = now
        else:
            target_date = now
        
        # 시간 패턴 매칭
        time_patterns = [
            r"(\d{1,2})시",
            r"오전\s*(\d{1,2})시",
            r"오후\s*(\d{1,2})시",
            r"(\d{1,2}):\d{2}",
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                if "오후" in text and hour != 12:
                    hour += 12
                target_date = target_date.replace(hour=hour, minute=0, second=0)
                break
        
        return target_date.isoformat()

    async def analyze_intent(self, text: str, user_context: Dict = None) -> NLUResult:
        """사용자 입력을 분석하여 의도와 엔티티 추출"""
        try:
            messages = [
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": f"분석할 텍스트: '{text}'"}
            ]
            
            # 컨텍스트가 있으면 추가
            if user_context:
                context_msg = f"사용자 컨텍스트: {json.dumps(user_context, ensure_ascii=False)}"
                messages.append({"role": "system", "content": context_msg})
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Docker 환경 호환성을 위해 gpt-4o-mini 사용
                messages=messages,
                temperature=0.1,  # 일관성을 위해 낮은 온도 설정
                max_tokens=800  # Docker 환경 호환 매개변수명
            )
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
            
            # 응답 내용 디버깅
            print(f"🔍 Raw GPT Response: '{content}'")
            print(f"🔍 Response length: {len(content) if content else 0}")
            logger.info(f"GPT Response: {content}")
            
            if not content:
                print("❌ GPT-5 응답이 비어있습니다!")
                return NLUResult(
                    intent=Intent("unknown", 0.3),
                    text=text,
                    confidence=0.3
                )
            
            # JSON 파싱
            try:
                # JSON이 아닌 텍스트가 포함된 경우 정리
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].strip()
                
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # JSON이 아닌 경우 더 자세한 로깅
                logger.warning(f"Failed to parse JSON: '{content}' Error: {e}")
                print(f"❌ JSON 파싱 실패. 실제 응답: '{content}'")
                return NLUResult(
                    intent=Intent("unknown", 0.5),
                    text=text,
                    confidence=0.5
                )
            
            # 시간 정보 정규화
            entities = result.get("entities", {})
            if entities.get("date_time"):
                parsed_time = self._parse_time_expression(text)
                if parsed_time:
                    entities["parsed_datetime"] = parsed_time
            
            return NLUResult(
                intent=Intent(
                    name=result["intent"],
                    confidence=result["confidence"],
                    entities=entities
                ),
                text=text,
                confidence=result["confidence"],
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"NLU analysis failed: {e}")
            return NLUResult(
                intent=Intent("unknown", 0.3),
                text=text,
                confidence=0.3
            )

    def get_response_template(self, intent_name: str, entities: Dict = None) -> str:
        """Intent와 entities에 따른 응답 템플릿 생성 (확장된 버전)"""
        if entities is None:
            entities = {}
            
        templates = {
            # 메모 관련
            "create_memo": self._format_memo_response(entities, "메모를 저장했습니다."),
            "query_memo": "메모를 검색하고 있습니다.",
            "update_memo": "메모를 수정했습니다.",
            "delete_memo": "메모를 삭제했습니다.",
            
            # 할일 관련  
            "create_todo": self._format_todo_response(entities, "할일을 추가했습니다."),
            "query_todo": "할일 목록을 확인하고 있습니다.",
            "update_todo": "할일 상태를 업데이트했습니다.",
            "complete_todo": "할일을 완료 처리했습니다!",
            "delete_todo": "할일을 삭제했습니다.",
            
            # 일정 관리
            "create_event": self._format_event_response(entities, "일정을 등록했습니다."),
            "query_event": "일정을 조회하고 있습니다.",
            "update_event": "일정을 수정했습니다.",
            "cancel_event": "일정을 취소했습니다.",
            
            # 검색 및 분석
            "search_general": "검색하고 있습니다.",
            "search_by_date": f"{entities.get('date_time', '해당 날짜')}의 기록을 찾고 있습니다.",
            "search_by_category": f"{entities.get('category', '해당 카테고리')} 관련 항목을 찾고 있습니다.",
            "analyze_pattern": "패턴을 분석하고 있습니다.",
            
            # 알림 및 리마인더
            "set_reminder": f"알림을 설정했습니다.",
            "query_reminder": "설정된 알림을 확인하고 있습니다.",
            "snooze_reminder": "알림을 연기했습니다.",
            
            # 시스템 제어
            "help": "무엇을 도와드릴까요? 메모 저장, 할일 관리, 일정 등록 등을 할 수 있습니다.",
            "settings": "설정을 변경하고 있습니다.",
            "cancel_current": "현재 작업을 취소했습니다.",
            
            # 감정 및 소통
            "greeting": "안녕하세요! 오늘 무엇을 도와드릴까요?",
            "thanks": "천만에요! 언제든 말씀해주세요.",
            "goodbye": "안녕히 가세요! 좋은 하루 되세요.",
            
            "unknown": "죄송합니다. 명령을 이해하지 못했습니다. 다시 말씀해주세요."
        }
        
        return templates.get(intent_name, templates["unknown"])
    
    def _format_memo_response(self, entities: Dict, base_message: str) -> str:
        """메모 관련 응답 포맷팅"""
        item_name = entities.get("item_name", "내용")
        date_time = entities.get("date_time")
        category = entities.get("category")
        
        response = f"'{item_name}' {base_message}"
        
        if date_time:
            response += f" ({date_time})"
        if category:
            response += f" [{category}]"
            
        return response
    
    def _format_todo_response(self, entities: Dict, base_message: str) -> str:
        """할일 관련 응답 포맷팅"""
        item_name = entities.get("item_name", "작업")
        priority = entities.get("priority")
        date_time = entities.get("date_time")
        
        response = f"'{item_name}' {base_message}"
        
        if priority:
            response += f" (우선순위: {priority})"
        if date_time:
            response += f" 마감: {date_time}"
            
        return response
    
    def _format_event_response(self, entities: Dict, base_message: str) -> str:
        """일정 관련 응답 포맷팅"""
        item_name = entities.get("item_name", "일정")
        date_time = entities.get("date_time")
        location = entities.get("location")
        person = entities.get("person")
        duration = entities.get("duration")
        
        response = f"'{item_name}' {base_message}"
        
        if date_time:
            response += f" - {date_time}"
        if location:
            response += f" @ {location}"
        if person:
            response += f" (참석자: {person})"
        if duration:
            response += f" ({duration})"
            
        return response

# 전역 NLU 서비스 인스턴스
nlu_service = None

def get_nlu_service() -> GPT5NLUService:
    """NLU 서비스 싱글톤 인스턴스 반환"""
    global nlu_service
    if nlu_service is None:
        nlu_service = GPT5NLUService()
    return nlu_service