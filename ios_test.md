# iOS 실기기 테스트 가이드

MERE AI Agent iOS 앱을 실제 iPhone에서 테스트하는 방법을 안내합니다.

## 1. 개발자 계정 설정

### Apple Developer Program 가입 (필요한 경우)
```bash
# 무료 개발자 계정으로도 7일간 테스트 가능
# 연간 $99 유료 계정 시 1년간 배포 가능
```

## 2. Xcode 프로젝트 설정

### Bundle Identifier 변경
```bash
# Xcode에서 프로젝트 열기
cd ios/MEREApp
open MEREApp.xcodeproj

# 또는 터미널에서
xed ios/MEREApp/MEREApp.xcodeproj
```

**Xcode에서 설정:**
1. 프로젝트 네비게이터에서 `MEREApp` 선택
2. `TARGETS` → `MEREApp` 선택  
3. `General` 탭에서:
   - **Bundle Identifier**: `com.yourname.MEREApp` (고유한 이름으로 변경)
   - **Team**: 본인의 Apple ID 선택

### 서명 설정
1. `Signing & Capabilities` 탭에서:
   - ✅ **Automatically manage signing** 체크
   - **Team**: 본인의 Apple ID/Developer Team 선택
   - **Provisioning Profile**: Automatic 선택

## 3. 디바이스 연결 및 신뢰

### iPhone 연결
```bash
# USB 케이블로 iPhone을 Mac에 연결
# iPhone에서 "이 컴퓨터를 신뢰하시겠습니까?" → 신뢰
```

### 개발자 모드 활성화 (iOS 16+)
1. iPhone에서 `설정` → `개인정보 보호 및 보안`
2. `개발자 모드` 활성화
3. 재부팅 후 개발자 모드 확인

## 4. 백엔드 서버 설정

### 로컬 IP 주소 확인
```bash
# Mac의 로컬 IP 주소 확인
ifconfig | grep "inet " | grep -v 127.0.0.1
# 예: 192.168.1.100
```

### AIService 서버 주소 변경
```swift
// ios/MEREApp/AIService.swift에서 수정
init(baseURL: String = "http://192.168.1.100:8000") {  // 실제 IP로 변경
    // ...
}
```

### 백엔드 서버 실행
```bash
# 터미널에서 백엔드 실행
cd /Users/eden.jang/Work/eden/mere
docker-compose up -d

# 또는 직접 실행
PYTHONPATH=/Users/eden.jang/Work/eden/mere/backend python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 5. 앱 빌드 및 설치

### Xcode에서 빌드
1. 상단 디바이스 선택에서 연결된 iPhone 선택
2. `Product` → `Run` (⌘+R) 또는 재생 버튼 클릭
3. 빌드 완료까지 대기

### 디바이스에서 앱 신뢰
1. iPhone에서 `설정` → `일반` → `VPN 및 기기 관리`
2. `개발자 앱` 섹션에서 본인의 Apple ID 선택
3. `MEREApp` 신뢰

## 6. 네트워크 설정 확인

### 같은 WiFi 네트워크 연결
```bash
# Mac과 iPhone이 같은 WiFi에 연결되어 있는지 확인
# iPhone: 설정 → WiFi에서 네트워크 이름 확인
# Mac: WiFi 아이콘 클릭하여 네트워크 이름 확인
```

### 방화벽 설정 (필요한 경우)
```bash
# Mac 방화벽에서 8000 포트 허용
# 시스템 환경설정 → 보안 및 개인 정보 보호 → 방화벽 → 방화벽 옵션
# Python 또는 해당 앱에 대해 들어오는 연결 허용
```

## 7. 테스트 및 문제 해결

### 기본 테스트
1. 앱 실행 후 WebSocket 연결 상태 확인
2. PTT 버튼으로 음성 입력 테스트
3. 백엔드 로그 확인:
```bash
docker-compose logs -f backend
```

### 일반적인 문제 해결

**연결 안됨:**
```bash
# 서버 상태 확인
curl http://192.168.1.100:8000/health

# 포트 확인
lsof -i :8000
```

**앱 크래시:**
- Xcode 콘솔에서 오류 메시지 확인
- 디바이스 로그 확인: `Window` → `Devices and Simulators`

**마이크 권한:**
- iPhone 설정 → 개인정보 보호 → 마이크 → MEREApp 허용

## 8. 빠른 설정 스크립트

```bash
# 1. IP 주소 자동 설정 스크립트 생성
echo '#!/bin/bash
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk "{print \$2}")
echo "Local IP: $LOCAL_IP"
echo "Update AIService.swift baseURL to: http://$LOCAL_IP:8000"
echo "Starting backend server..."
docker-compose up -d
echo "Server running at http://$LOCAL_IP:8000"' > setup_device_test.sh

chmod +x setup_device_test.sh
./setup_device_test.sh
```

## 9. 테스트할 기능들 (Day 11 완료분)

### 기본 음성 기능
- [x] PTT 버튼으로 음성 입력
- [x] STT 변환 및 텍스트 표시
- [x] NLU Intent 분류 (25개 Intent)
- [x] TTS 음성 응답 재생

### 오프라인 모드 기능
- [x] 네트워크 차단 후 로컬 데이터 저장
- [x] 오프라인 Intent 처리
- [x] 네트워크 복구 시 자동 동기화
- [x] CoreData 로컬 스토리지

### 데이터 관리
- [x] 메모 생성/조회/수정/삭제
- [x] 할일 생성/완료/수정/삭제
- [x] 일정 생성/조회/수정/취소
- [x] 데이터 동기화 상태 확인

### WebSocket 통신
- [x] 실시간 서버 통신
- [x] 자동 재연결
- [x] 연결 상태 표시
- [x] 에러 핸들링

## 10. 실제 테스트 시나리오

### 음성 명령 예시
```
"내일 아침 우유 사는 거 기억시켜줘"
"프로젝트 회의 메모 작성해줘"
"오늘 할일 목록 보여줘"
"다음주 화요일 2시에 미팅 잡아줘"
```

### 오프라인 테스트
1. WiFi 끄기
2. 음성 명령 입력
3. 로컬 저장 확인
4. WiFi 켜기
5. 자동 동기화 확인

이제 실제 iPhone에서 MERE AI Agent의 모든 기능을 테스트해볼 수 있습니다!