# Google Calendar API Setup Guide

## 단계별 설정 가이드

### 1. Google Cloud Console 프로젝트 생성
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성
   - 프로젝트 이름: `MERE AI Agent`
   - 프로젝트 ID: `mere-ai-agent-calendar`

### 2. Google Calendar API 활성화
1. API 및 서비스 → 라이브러리
2. "Google Calendar API" 검색
3. Google Calendar API 선택 → "사용 설정" 클릭

### 3. OAuth 2.0 클라이언트 ID 생성

**현재 구현 분석**:
- `InstalledAppFlow.from_client_secrets_file()` 사용
- `flow.run_local_server(port=0)` - 로컬 서버 임시 실행
- 브라우저 자동 열기로 사용자 인증
- 개발/테스트 환경에서 동작하는 방식

**올바른 설정**:
1. API 및 서비스 → 사용자 인증 정보
2. "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: **"데스크톱 애플리케이션"**
4. 이름: "MERE AI Agent Calendar Client"

**선택 이유**:
- `InstalledAppFlow`는 데스크톱 애플리케이션용 OAuth 플로우
- `run_local_server()`가 임시 로컬 서버를 실행하여 인증 코드 수신
- 개발 환경에서 브라우저 기반 인증에 적합
- 서버 애플리케이션이지만 설치형 앱처럼 동작

### 4. OAuth 동의 화면 구성
1. OAuth 동의 화면 → 외부 사용자
2. 앱 정보:
   - 앱 이름: `MERE AI Agent`
   - 사용자 지원 이메일: [your-email]
   - 승인된 도메인: `localhost`
3. 범위 추가:
   - `https://www.googleapis.com/auth/calendar`

### 5. 클라이언트 시크릿 다운로드
1. 생성된 OAuth 클라이언트에서 JSON 다운로드
2. 파일명을 `credentials.json`으로 변경
3. `/Users/eden.jang/Work/eden/mere/backend/credentials.json`에 저장

### 6. 테스트 사용자 추가 (필수)
1. OAuth 동의 화면 → 테스트 사용자
2. **"+ 사용자 추가"** 클릭
3. **본인 Gmail 계정 입력** (예: your-email@gmail.com)
4. **저장** 클릭

**중요**: 이 단계를 건너뛰면 "403 오류: access_denied" 발생
- 앱이 테스트 모드일 때는 승인된 테스터만 접근 가능
- 개발자 본인도 테스트 사용자 목록에 추가해야 함

## 보안 주의사항
- `credentials.json` 파일을 절대 git에 커밋하지 마세요
- `.gitignore`에 `credentials.json` 추가 필수
- 프로덕션 환경에서는 환경 변수 사용 권장