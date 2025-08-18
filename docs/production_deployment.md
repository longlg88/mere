# Production Deployment Guide

## Google Calendar API Production 설정

### 1. Environment Variables 관리

#### Development vs Production
- **Development**: `credentials.json` 파일 사용 (InstalledAppFlow)
- **Production**: 환경변수 사용 (Web Application Flow)

#### 필수 환경변수
```bash
# Google Calendar API
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxx
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
SECRET_KEY=your-secret-key
```

### 2. Google Cloud Console 설정 변경

#### Production용 OAuth 설정
1. **애플리케이션 유형**: "웹 애플리케이션"으로 변경
2. **승인된 리디렉션 URI**:
   ```
   https://yourdomain.com/auth/google/callback
   https://api.yourdomain.com/auth/google/callback
   ```
3. **OAuth 동의 화면**: 프로덕션 상태로 승인 요청

### 3. 보안 관리 방법

#### Option 1: Kubernetes Secrets (Recommended)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mere-ai-secrets
type: Opaque
data:
  google-client-id: <base64-encoded-client-id>
  google-client-secret: <base64-encoded-client-secret>
  database-url: <base64-encoded-db-url>
```

#### Option 2: AWS Secrets Manager
```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e
```

#### Option 3: HashiCorp Vault
```python
import hvac

client = hvac.Client(url='https://vault.yourdomain.com')
client.token = os.getenv('VAULT_TOKEN')

secret = client.secrets.kv.v2.read_secret_version(
    path='mere-ai/google-credentials'
)
```

### 4. Multi-User OAuth Flow

#### 사용자별 인증 과정
1. **사용자 인증 시작**: `/auth/google/authorize/{user_id}`
2. **Google OAuth**: 사용자가 브라우저에서 인증
3. **콜백 처리**: `/auth/google/callback`
4. **토큰 저장**: 데이터베이스에 사용자별 토큰 저장
5. **API 호출**: 저장된 토큰으로 Calendar API 호출

#### 토큰 관리
```sql
CREATE TABLE user_calendar_auth (
    user_id VARCHAR(255) PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    scopes TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### 5. Production Deployment

#### Docker Compose (Production)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile.production
    environment:
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - DATABASE_URL=${DATABASE_URL}
    secrets:
      - google_client_secret
      - database_password

secrets:
  google_client_secret:
    external: true
  database_password:
    external: true
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mere-ai-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: mere-ai:latest
        env:
        - name: GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: mere-ai-secrets
              key: google-client-id
        - name: GOOGLE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: mere-ai-secrets
              key: google-client-secret
```

### 6. 보안 Best Practices

#### 환경변수 보안
- ❌ **절대 금지**: 소스 코드에 하드코딩
- ❌ **절대 금지**: Docker 이미지에 포함
- ❌ **절대 금지**: 로그에 출력
- ✅ **권장**: Secrets Manager 사용
- ✅ **권장**: 환경변수는 런타임에만 주입
- ✅ **권장**: 정기적 토큰 로테이션

#### 토큰 관리
- **Refresh Token**: 안전한 저장소에 암호화 저장
- **Access Token**: 메모리에만 보관, 만료 시 자동 갱신
- **Revocation**: 사용자가 언제든 접근 취소 가능

### 7. 모니터링 및 로깅

#### 로그 레벨 설정
```python
# Production에서는 DEBUG 로그 비활성화
logging.basicConfig(level=logging.INFO)

# 민감한 정보는 로그에서 제외
logger.info(f"OAuth successful for user {user_id[:8]}***")
```

#### 메트릭 수집
- OAuth 인증 성공/실패율
- API 호출 빈도 및 성공률
- 토큰 갱신 빈도
- 에러 발생률

### 8. 재해 복구

#### 백업 전략
- **사용자 토큰**: 정기적 데이터베이스 백업
- **설정**: Infrastructure as Code 관리
- **시크릿**: 복수 리전에 복제

#### 장애 시나리오
- Google API 서비스 중단: 캐싱된 데이터로 제한된 기능 제공
- 데이터베이스 장애: 읽기 전용 복제본 활용
- 인증 서비스 장애: 기존 토큰으로 계속 서비스