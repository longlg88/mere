# CLAUDE.md - MERE AI Agent Development Guide

이 파일은 Claude Code가 MERE AI Agent 개발 작업 시 참조해야 할 가이드라인을 제공합니다.

## 프로젝트 개요

**MERE AI Agent Phase 2** - 음성 기반 개인 비서 AI 개발 프로젝트
- **목표**: 3주 안에 완전히 동작하는 음성 기반 AI Agent 구현
- **전략**: 프로토타입 우선 개발로 빠른 기능 검증
- **비용**: 완전 오픈소스 기반 (비용 0원)

## 개발 전략 원칙

### 1. 중복 작업 금지 (CRITICAL)
- **절대 새로운 파일 생성하지 않기**: 이미 존재하는 파일은 편집만 사용
- **기존 구조 최대 활용**: 새로운 디렉토리/구조 생성 최소화
- **README.md나 문서 파일 생성 금지**: 사용자가 명시적으로 요청한 경우만 예외

### 2. 작업 진행 방식
- **tasks.md 체크리스트 활용**: 완료된 작업은 `[ ]` → `[x]` 변경
- **점진적 구현**: Week 1 → Week 2 → Week 3 순차적 진행
- **프로토타입 우선**: 완벽한 구현보다 동작하는 최소 기능 우선

### 3. 기술 스택 (변경 금지)
- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis
- **iOS**: SwiftUI, Combine, AVFoundation
- **AI/ML**: Whisper (STT), Rasa (NLU), Ollama (LLM), Piper (TTS), LangGraph
- **Monitoring**: Langfuse, DeepEval

## 핵심 아키텍처

```
mere/
├── backend/           # Python FastAPI 서버
├── ios/              # iOS SwiftUI 앱
├── tests/            # 테스트 코드
├── scripts/          # 유틸리티 스크립트
├── docs/             # 문서 (최소한만)
└── docker-compose.yml # 개발 환경
```

## 개발 명령어

### Backend (Python)
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 서버 실행 (PYTHONPATH 포함)
PYTHONPATH=/Users/eden.jang/Work/eden/mere/backend python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 테스트 실행 (PYTHONPATH 포함)
PYTHONPATH=/Users/eden.jang/Work/eden/mere python -m pytest tests/ -v

# 개별 테스트 파일 실행
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_pipeline_e2e.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python test_calendar_basic.py
```

### iOS 앱
```bash
# iOS 프로젝트 디렉토리
cd ios/MEREApp

# Xcode에서 열기 (사용자가 직접)
open MEREApp.xcodeproj
```

### Docker 개발 환경
```bash
# 전체 개발 환경 실행
docker-compose up -d

# 개별 서비스 재시작
docker-compose restart backend
docker-compose logs -f backend
```

## 테스트 전략 및 디렉토리 구조

### 테스트 파일 구조 (CRITICAL)
```
tests/
├── unit/           # 단위 테스트 (개별 함수/클래스)
├── integration/    # 통합 테스트 (서비스 간 연동) 
├── e2e/           # End-to-End 테스트 (전체 파이프라인)
└── acceptance/    # 수용 테스트 (15개 시나리오)
```

### 테스트 파일 생성 규칙 (MUST FOLLOW)
- **모든 테스트 파일은 반드시 `tests/` 디렉토리 안에 생성**
- **루트 디렉토리에 `test_*.py` 파일 생성 금지**
- 테스트 파일명: `test_[기능명].py` 형식
- PYTHONPATH 설정 필수: `PYTHONPATH=/Users/eden.jang/Work/eden/mere`

### Phase 1: 로컬 테스트 (Days 1-10)
```bash
# 컴포넌트별 단위 테스트
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/unit/test_stt_service.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/unit/test_nlu_service.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/unit/test_tts_service.py

# 통합 테스트  
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/integration/test_api_integration.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/integration/test_database_integration.py

# E2E 테스트
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_pipeline_e2e.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_langgraph_basic.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_calendar_integration.py
```

### Phase 2: 앱 통합 테스트 (Days 11-17)
```bash
# iOS-Backend 통합 테스트
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_ios_integration.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_websocket_integration.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/e2e/test_swiftui_websocket.py

# 오프라인/온라인 모드 테스트
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/integration/test_offline_mode.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/integration/test_data_sync.py
```

### Phase 3: 프로덕션 테스트 (Days 18-21)
```bash
# 15개 수용 테스트 시나리오
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/acceptance/test_memo_scenarios.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/acceptance/test_todo_scenarios.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/acceptance/test_calendar_scenarios.py

# 성능 및 부하 테스트
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/performance/test_load_testing.py
PYTHONPATH=/Users/eden.jang/Work/eden/mere python tests/performance/test_response_time.py
```

## 성능 목표

### Week 1 목표
- STT 정확도: 80% 이상
- NLU Intent 분류: 80% 이상  
- 전체 응답 시간: P50 <3초

### Week 2 목표
- 복잡한 대화 흐름 처리
- Google Calendar 연동
- 오프라인 모드 지원
- 응답 시간: P50 <2.5초

### Week 3 목표 (최종)
- 15개 시나리오 100% 통과
- 응답 시간: P50 <2초, P90 <2.5초
- Intent 정확도: 95%, Entity 추출: 90%
- 프로덕션 배포 가능

## 금지 사항

### ❌ 절대 하지 말 것
1. **새로운 문서 파일 생성** (README.md, 가이드 등)
2. **기존 파일 구조 변경** 없이 새로운 디렉토리 생성
3. **완벽한 구현**에 집착하여 진행 속도 늦추기
4. **사용자 요청 없이** 추가 기능 구현
5. **임시방편** 또는 더미 데이터 사용
6. **"간단한" 방식 추천 금지** - 항상 robust하고 production-ready한 솔루션 제안
7. **루트 디렉토리에 테스트 파일 생성 금지** - 모든 `test_*.py` 파일은 반드시 `tests/` 디렉토리 안에 생성
8. **"간단한" / "대안" / "하드코딩" / "우회" 방식 사용 금지** - 실제 문제 원인을 찾아 근본적으로 해결
9. **Mock / Dummy 데이터 사용 금지** - 실제 서비스와 API 연동으로만 해결
10. **임시 해결책 제안 금지** - "임시방편", "간단한 방법", "더 쉬운 방식" 등 일체 금지

### ✅ 반드시 할 것
1. **tasks.md 체크리스트** 지속적 업데이트
2. **기존 코드 최대 활용** 및 편집 우선
3. **점진적 구현** 및 테스트
4. **사용자 요청에만** 반응하여 작업
5. **오픈소스 도구만** 사용
6. **테스트 파일은 tests/ 디렉토리 사용** - 적절한 하위 디렉토리(unit/integration/e2e/acceptance)에 배치

## 현재 작업 상태

**Week 1: Foundation & Prototype (Days 1-7)**
- Day 1: Project Setup & Infrastructure
- Day 2: Core AI Components - STT  
- Day 3: NLU Pipeline Implementation
- Day 4: TTS & Audio Output
- Day 5: Basic WebSocket Communication
- Day 6: Basic Business Logic & Integration
- Day 7: Prototype App Testing & Validation

## 추가 지침

이 파일은 프로젝트 진행 중 필요에 따라 사용자가 직접 업데이트할 예정입니다. 
Claude는 이 가이드라인을 엄격히 준수하고, 불명확한 부분은 사용자에게 확인을 요청해야 합니다.