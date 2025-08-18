# MERE AI Agent - 개발 가이드

## OpenAI API 연결 문제 해결

### Proxy 환경에서 OpenAI API 사용하기

**문제**: `Connection error` 또는 `APIConnectionError` 오류 발생

**해결방법**: 
1. **환경변수 설정**:
   ```bash
   export HTTP_PROXY="http://localhost:8080"
   export HTTPS_PROXY="http://localhost:8080"
   ```

2. **NLU 서비스에서 자동으로 프록시 감지**:
   - NLU 서비스가 환경변수의 프록시 설정을 자동 감지
   - httpx 클라이언트에 직접 프록시 설정 적용
   - 별도 설정 없이 바로 동작

3. **연결 테스트**:
   ```bash
   python debug_connection.py  # 상세 디버깅
   python test_nlu.py          # NLU 서비스 테스트
   ```

### GPT-5 API 사용 설정

**API 키 설정**:
```bash
export OPENAI_API_KEY="your-gpt-5-api-key"
```

**모델 사용**:
- 기본 모델: `gpt-5`
- 비용: $1.25/1M input tokens, $10.00/1M output tokens
- NLU 서비스에서 자동으로 GPT-5 사용하도록 설정됨

**중요한 차이점**:
- GPT-5는 `max_tokens` 대신 `max_completion_tokens` 사용
- GPT-5는 `temperature`를 기본값(1)만 지원 (커스텀 값 설정 불가)
- 자동으로 처리되므로 별도 설정 불필요

### 테스트 실행 순서

1. **API 키 설정**:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **API 키 검증 테스트**:
   ```bash
   python test_api_key.py
   ```

3. **NLU 서비스 테스트**:
   ```bash
   python test_nlu.py
   ```

### 일반적인 오류와 해결책

| 오류 | 원인 | 해결책 |
|------|------|--------|
| `Connection error` | 프록시/네트워크 문제 | HTTP_PROXY, HTTPS_PROXY 설정 |
| `invalid_api_key` | 잘못된 API 키 | 올바른 API 키 재설정 |
| `insufficient_quota` | 사용량 한도 초과 | OpenAI 계정 결제 정보 확인 |
| `model_not_found` | GPT-5 접근 권한 없음 | GPT-5 접근 권한 확인 또는 gpt-4o로 변경 |

### 개발 환경 설정 체크리스트

- [ ] Python 3.12 설치 확인
- [ ] 가상환경 활성화
- [ ] OpenAI 패키지 설치 (`pip install openai==1.47.0`)
- [ ] 프록시 환경변수 설정 (필요시)
- [ ] OPENAI_API_KEY 환경변수 설정
- [ ] Docker 컨테이너 실행 (PostgreSQL, Redis, MinIO)

### 성공 확인

NLU 테스트가 성공하면 다음과 같은 출력이 나타납니다:

```
🤖 GPT-5 NLU 서비스 테스트 시작

📝 테스트 1: '내일 우유 사는 거 기억해줘'
   Intent: create_memo (신뢰도: 0.95)
   Entities:
     - item_name: 우유 사기
     - date_time: 내일
   응답: '우유 사기' 메모를 저장했습니다.
```