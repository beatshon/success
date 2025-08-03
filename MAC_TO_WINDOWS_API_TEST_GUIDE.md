# 맥에서 윈도우 서버 API 테스트 가이드

## 개요
이 가이드는 맥에서 작업한 파일을 윈도우 서버에서 API 테스트를 하기 위한 단계별 가이드입니다.

## 사전 준비사항

### 1. 윈도우 서버 설정
- 윈도우 서버에 Python 3.8+ 설치
- SSH 서비스 활성화
- 방화벽에서 SSH 포트(22) 및 API 포트(8080) 개방

### 2. 맥 클라이언트 설정
- SSH 클라이언트 설치 (기본 포함)
- SCP 명령어 사용 가능

## 단계별 실행 가이드

### 1단계: 윈도우 서버 정보 설정

`config/windows_server.conf` 파일을 실제 서버 정보로 수정:

```bash
# 윈도우 서버 IP 주소 (실제 서버 IP로 변경)
WINDOWS_HOST="192.168.1.100"

# 윈도우 사용자명 (실제 사용자명으로 변경)
WINDOWS_USER="Administrator"

# 윈도우 서버의 프로젝트 경로 (실제 경로로 변경)
WINDOWS_PATH="C:/Users/Administrator/Desktop/kiwoom_trading"

# SSH 포트 (기본값: 22)
SSH_PORT="22"

# API 서버 포트 (기본값: 8080)
API_PORT="8080"
```

### 2단계: 맥에서 윈도우 서버로 파일 전송

```bash
# 전송 스크립트 실행 권한 부여
chmod +x sync_to_windows_server.sh

# 파일 전송 실행
./sync_to_windows_server.sh
```

**전송되는 파일들:**
- `windows_api_test.py` - API 테스트 스크립트
- `run_windows_api_test.bat` - 윈도우용 테스트 실행 배치 파일
- `start_windows_api_server.py` - API 서버 스크립트
- `start_windows_api_server.bat` - API 서버 실행 배치 파일
- `config/` - 설정 파일들
- `requirements_windows.txt` - 윈도우용 패키지 요구사항
- 기타 필요한 Python 파일들

### 3단계: 윈도우 서버에서 API 서버 실행

윈도우 서버에 접속하여 다음 명령어 실행:

```cmd
# 프로젝트 디렉토리로 이동
cd C:\Users\Administrator\Desktop\kiwoom_trading

# API 서버 실행
start_windows_api_server.bat
```

또는 맥에서 원격으로 실행:

```bash
ssh -p 22 Administrator@192.168.1.100 "cd C:/Users/Administrator/Desktop/kiwoom_trading && start_windows_api_server.bat"
```

### 4단계: API 테스트 실행

윈도우 서버에서:

```cmd
# API 테스트 실행
run_windows_api_test.bat
```

또는 맥에서 원격으로 실행:

```bash
ssh -p 22 Administrator@192.168.1.100 "cd C:/Users/Administrator/Desktop/kiwoom_trading && run_windows_api_test.bat"
```

## API 엔드포인트 목록

### 기본 엔드포인트
- `GET /` - 서버 정보
- `GET /status` - 서버 상태
- `GET /api/test/connection` - 연결 테스트

### 거래 시스템 API
- `GET /api/account/info` - 계좌 정보 조회
- `GET /api/stock/price?code=005930` - 주식 시세 조회
- `GET /api/order/available` - 주문 가능 금액 조회

### 시스템 상태 API
- `GET /api/realtime/status` - 실시간 데이터 서버 상태
- `GET /api/news/status` - 뉴스 분석 서버 상태
- `GET /api/ml/status` - 딥러닝 시스템 상태

## 테스트 결과 확인

### 로그 파일 위치
- **로그 파일**: `logs/windows_api_test.log`
- **결과 파일**: `logs/windows_api_test_results_YYYYMMDD_HHMMSS.json`

### 결과 파일 구조
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "tests": [
    {
      "category": "kiwoom_connection",
      "result": true
    },
    {
      "category": "trading_system",
      "results": [
        {
          "test": "계좌 정보 조회",
          "status": "success",
          "response_code": 200
        }
      ]
    }
  ]
}
```

## 문제 해결

### 1. SSH 연결 실패
```bash
# SSH 연결 테스트
ssh -p 22 Administrator@192.168.1.100 "echo '연결 성공'"

# 문제 해결 방법:
# 1. 윈도우 서버가 실행 중인지 확인
# 2. SSH 서비스가 활성화되어 있는지 확인
# 3. 방화벽에서 SSH 포트(22)가 열려있는지 확인
# 4. SSH 키가 설정되어 있는지 확인
```

### 2. Python 환경 문제
```cmd
# Python 버전 확인
python --version

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements_windows.txt
```

### 3. 포트 충돌 문제
```cmd
# 포트 사용 확인
netstat -an | findstr :8080

# 프로세스 종료
taskkill /f /im python.exe
```

### 4. 권한 문제
```cmd
# 관리자 권한으로 실행
# 또는 파일 권한 확인
icacls "C:\Users\Administrator\Desktop\kiwoom_trading"
```

## 고급 설정

### 1. 자동 동기화 설정
```bash
# 파일 변경 감지 및 자동 전송
watch_and_sync.py
```

### 2. 백업 설정
```bash
# 자동 백업 스크립트
auto_backup.sh
```

### 3. 모니터링 설정
```bash
# 시스템 모니터링
system_monitor.py
```

## 보안 고려사항

### 1. SSH 키 인증 설정
```bash
# SSH 키 생성
ssh-keygen -t rsa -b 4096

# 공개키를 윈도우 서버에 복사
ssh-copy-id -p 22 Administrator@192.168.1.100
```

### 2. 방화벽 설정
```cmd
# 윈도우 방화벽에서 필요한 포트만 개방
netsh advfirewall firewall add rule name="SSH" dir=in action=allow protocol=TCP localport=22
netsh advfirewall firewall add rule name="API" dir=in action=allow protocol=TCP localport=8080
```

### 3. API 키 보안
```python
# 환경 변수로 API 키 관리
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('KIWOOM_API_KEY')
```

## 성능 최적화

### 1. 네트워크 최적화
```bash
# SSH 압축 사용
ssh -C -p 22 Administrator@192.168.1.100
```

### 2. 파일 전송 최적화
```bash
# rsync 사용 (가능한 경우)
rsync -avz -e "ssh -p 22" ./ Administrator@192.168.1.100:C:/Users/Administrator/Desktop/kiwoom_trading/
```

### 3. 병렬 처리
```python
# 멀티스레딩으로 API 테스트
import threading
import concurrent.futures
```

## 모니터링 및 로깅

### 1. 실시간 로그 모니터링
```bash
# 로그 파일 실시간 모니터링
tail -f logs/windows_api_test.log
```

### 2. 성능 메트릭 수집
```python
# API 응답 시간 측정
import time
start_time = time.time()
response = requests.get(url)
response_time = time.time() - start_time
```

### 3. 알림 설정
```python
# 이메일 알림
import smtplib
from email.mime.text import MIMEText
```

## 결론

이 가이드를 따라하면 맥에서 작업한 파일을 윈도우 서버에서 안전하고 효율적으로 API 테스트를 할 수 있습니다. 

### 주요 장점:
1. **자동화된 파일 전송**: 스크립트를 통한 자동 동기화
2. **포괄적인 테스트**: 모든 API 엔드포인트 테스트
3. **상세한 로깅**: 문제 발생 시 빠른 진단 가능
4. **보안 고려**: SSH 키 인증 및 방화벽 설정
5. **성능 최적화**: 네트워크 및 파일 전송 최적화

### 다음 단계:
1. 실제 서버 정보로 설정 파일 업데이트
2. SSH 키 인증 설정
3. API 서버 실행 및 테스트
4. 결과 분석 및 최적화

문제가 발생하면 로그 파일을 확인하고 위의 문제 해결 섹션을 참조하세요. 