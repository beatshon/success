# Windows 서버 실행 가이드

## 🖥️ Windows 환경에서 API 서버 실행하기

### 📋 사전 요구사항

1. **Python 설치**
   - Python 3.7 이상 설치
   - [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드
   - 설치 시 "Add Python to PATH" 옵션 체크

2. **키움증권 Open API+ 설치**
   - [키움증권 Open API+](https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView) 다운로드
   - 설치 후 키움증권 계정으로 로그인
   - Open API+ 사용 신청 및 승인

3. **네트워크 설정**
   - Windows 방화벽에서 8080 포트 허용
   - 맥에서 접근할 수 있도록 네트워크 설정

## 🚀 실행 방법

### 방법 1: 원클릭 실행 (가장 쉬움)

1. **초기 설정 (최초 1회만)**
   ```
   setup_windows.bat 더블클릭
   ```

2. **서버 시작**
   ```
   start_windows_server.bat 더블클릭
   ```

### 방법 2: 간단 버전 실행

```
start_server_simple.bat 더블클릭
```

### 방법 3: 상세 버전 실행

1. **프로젝트 폴더로 이동**
   ```cmd
   cd C:\path\to\kiwoom_trading
   ```

2. **배치 파일 실행**
   ```cmd
   start_windows_server.bat
   ```

3. **서버 시작 확인**
   ```
   ========================================
   Windows API 서버 시작
   ========================================
   
   현재 디렉토리: C:\path\to\kiwoom_trading
   
   ✅ Python 설치 확인 완료
   
   📦 가상환경 활성화...
   ✅ 가상환경 활성화 완료
   
   🔍 필요한 패키지 설치 확인...
   ✅ 패키지 설치 확인 완료
   
   🚀 Windows API 서버 시작...
   호스트: 0.0.0.0
   포트: 8080
   
   서버를 중지하려면 Ctrl+C를 누르세요.
   ```

### 방법 2: 명령줄 직접 실행

1. **명령 프롬프트 또는 PowerShell 실행**

2. **프로젝트 폴더로 이동**
   ```cmd
   cd C:\path\to\kiwoom_trading
   ```

3. **가상환경 활성화 (있는 경우)**
   ```cmd
   venv\Scripts\activate
   ```

4. **필요한 패키지 설치**
   ```cmd
   pip install flask flask-cors loguru requests watchdog
   ```

5. **서버 시작**
   ```cmd
   python windows_api_server.py --host 0.0.0.0 --port 8080
   ```

### 방법 3: 서비스 모드 실행

1. **서비스 스크립트 실행**
   ```cmd
   python windows_server_service.py --start
   ```

2. **서비스 상태 확인**
   ```cmd
   python windows_server_service.py --status
   ```

3. **서비스 중지**
   ```cmd
   python windows_server_service.py --stop
   ```

## 🔧 설정 및 구성

### 1. 방화벽 설정

Windows 방화벽에서 8080 포트를 허용해야 합니다:

1. **Windows 방화벽 고급 설정** 열기
2. **인바운드 규칙** → **새 규칙**
3. **포트** 선택 → **TCP** → **특정 로컬 포트: 8080**
4. **연결 허용** 선택
5. **도메인, 개인, 공용** 모두 체크
6. **이름: Windows API Server** 입력

### 2. 네트워크 설정

맥에서 접근할 수 있도록 네트워크 설정:

1. **Windows IP 주소 확인**
   ```cmd
   ipconfig
   ```

2. **맥에서 연결 테스트**
   ```bash
   ping [Windows_IP_주소]
   ```

### 3. 키움 API 설정

1. **키움증권 로그인**
   - 키움증권 Open API+ 실행
   - 계정 정보로 로그인

2. **API 사용 신청**
   - Open API+ 사용 신청
   - 승인 대기 (보통 1-2일 소요)

## 📊 서버 상태 확인

### 1. 로컬에서 확인

브라우저에서 다음 URL 접속:
```
http://localhost:8080/api/health
```

정상 응답:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### 2. 맥에서 확인

```bash
# Windows 서버 연결 테스트
python watch_and_sync.py --test

# 또는 직접 curl 사용
curl http://[Windows_IP]:8080/api/health
```

### 3. 로그 확인

```cmd
# 실시간 로그 확인
tail -f logs\windows_api_server.log

# 또는 Windows에서
type logs\windows_api_server.log
```

## 🛠️ 문제 해결

### 1. 포트 충돌 오류

```
Error: [Errno 10048] Only one usage of each socket address is normally permitted
```

**해결 방법:**
```cmd
# 8080 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8080

# 프로세스 종료
taskkill /PID [프로세스ID] /F
```

### 2. 키움 API 연결 실패

```
키움 API 초기화 실패
```

**해결 방법:**
1. 키움증권 Open API+ 재설치
2. 키움증권 계정으로 로그인 확인
3. API 사용 신청 상태 확인

### 3. 방화벽 차단

```
Connection refused
```

**해결 방법:**
1. Windows 방화벽에서 8080 포트 허용
2. 안티바이러스 프로그램에서 예외 추가
3. 네트워크 설정 확인

### 4. Python 패키지 오류

```
ModuleNotFoundError: No module named 'flask'
```

**해결 방법:**
```cmd
# 패키지 재설치
pip install --upgrade flask flask-cors loguru requests watchdog

# 또는 가상환경 재생성
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🔄 자동 시작 설정

### 1. 시작 프로그램 등록

1. **Windows + R** → `shell:startup` 입력
2. **시작 폴더**에 배치 파일 바로가기 생성
3. 배치 파일 내용에 `cd /d C:\path\to\kiwoom_trading` 추가

### 2. Windows 서비스 등록

```cmd
# 관리자 권한으로 명령 프롬프트 실행
sc create "KiwoomAPIServer" binPath= "C:\path\to\python.exe C:\path\to\kiwoom_trading\windows_server_service.py"
sc start "KiwoomAPIServer"
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. **로그 파일 확인**: `logs\windows_api_server.log`
2. **네트워크 연결 확인**: `ping [Windows_IP]`
3. **포트 사용 확인**: `netstat -ano | findstr :8080`
4. **키움 API 상태 확인**: 키움증권 Open API+ 로그인

---

**⚠️ 주의사항:**
- Windows 서버는 키움 API가 설치된 Windows 환경에서만 실행 가능
- 실제 거래 시에는 충분한 테스트 후 사용
- 네트워크 보안 설정 확인 필수 