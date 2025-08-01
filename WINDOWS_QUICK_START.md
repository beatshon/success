# Windows 서버 빠른 시작 가이드

## 🚀 3단계로 서버 시작하기

### 1단계: 초기 설정 (최초 1회만)

```
setup_windows.bat 더블클릭
```

**설정 내용:**
- Python 환경 확인
- 가상환경 생성
- 필요한 패키지 설치
- 기본 설정 파일 생성

### 2단계: 키움증권 설정

1. **Open API+ 설치**
   - https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
   - 다운로드 후 설치

2. **로그인 및 API 신청**
   - 키움증권 계정으로 로그인
   - Open API+ 사용 신청
   - 승인 대기 (1-2일)

### 3단계: 서버 시작

```
start_windows_server.bat 더블클릭
```

**서버 정보:**
- 호스트: 0.0.0.0 (모든 IP에서 접근 가능)
- 포트: 8080
- 상태 확인: http://localhost:8080/api/health

## 📋 실행 파일 목록

| 파일명 | 설명 | 사용 시기 |
|--------|------|-----------|
| `setup_windows.bat` | 초기 환경 설정 | 최초 1회만 |
| `start_windows_server.bat` | 서버 시작 (상세) | 매일 사용 |
| `start_server_simple.bat` | 서버 시작 (간단) | 빠른 시작 |
| `windows_server_service.py` | 백그라운드 서비스 | 자동 실행 |

## 🔧 문제 해결

### Python 설치 오류
```
❌ Python이 설치되지 않았습니다.
```
**해결:** https://www.python.org/downloads/ 에서 설치

### 포트 충돌 오류
```
⚠️ 포트 8080이 이미 사용 중입니다.
```
**해결:** 기존 프로세스 종료 또는 다른 포트 사용

### 키움 API 오류
```
키움 API 초기화 실패
```
**해결:** 키움증권 Open API+ 재설치 및 로그인

## 📊 서버 상태 확인

### 브라우저에서 확인
```
http://localhost:8080/api/health
```

### 명령줄에서 확인
```cmd
curl http://localhost:8080/api/health
```

### 정상 응답
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 🔄 맥과 연동

Windows 서버가 실행되면 맥에서:

```bash
# 연결 테스트
python watch_and_sync.py --test

# QA 프로세스 실행
python mac_hybrid_controller.py --action qa
```

## 📝 로그 확인

### 실시간 로그
```cmd
type logs\windows_api_server.log
```

### 로그 파일 위치
- `logs\windows_api_server.log`: 메인 로그
- `logs\windows_server_service.log`: 서비스 로그

## ⚠️ 주의사항

1. **키움 API 필수**: Windows 서버는 키움 API가 설치된 환경에서만 실행
2. **방화벽 설정**: 8080 포트 허용 필요
3. **네트워크 보안**: 실제 운영 시 HTTPS 사용 권장
4. **테스트 필수**: 충분한 시뮬레이션 후 실제 거래

## 📞 지원

문제 발생 시:
1. 로그 파일 확인
2. `WINDOWS_SETUP.md` 참조
3. 키움증권 고객센터: 1544-9000

---

**✅ 이제 Windows 서버가 준비되었습니다!** 