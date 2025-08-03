# 맥-윈도우 서버 파일 동기화 가이드

## 개요
이 가이드는 맥에서 작업한 파일들을 윈도우 서버로 동기화하는 다양한 방법을 제공합니다.

## 동기화 방법

### 1. 맥에서 윈도우로 동기화 (권장)

#### 방법 A: 전체 동기화 (완전한 동기화)
```bash
# 실행 권한 부여 (맥에서)
chmod +x sync_from_mac.sh

# 전체 동기화 실행
./sync_from_mac.sh
```

**특징:**
- 모든 중요 파일들을 동기화
- 백업 생성
- 상세한 로그 기록
- Python 환경 자동 업데이트

#### 방법 B: 빠른 동기화 (주요 파일만)
```bash
# 실행 권한 부여 (맥에서)
chmod +x quick_sync_to_windows.sh

# 빠른 동기화 실행
./quick_sync_to_windows.sh
```

**특징:**
- 주요 파일들만 빠르게 동기화
- 시간 절약
- 간단한 로그

### 2. 윈도우에서 맥으로 가져오기

윈도우 서버에서 실행:
```cmd
# 윈도우 서버에서 맥 파일 가져오기
pull_from_mac.bat
```

**특징:**
- 윈도우에서 맥으로 파일 가져오기
- 자동 백업 생성
- Python 환경 업데이트

### 3. 동기화 상태 확인

#### 맥에서 확인
```bash
# 동기화 상태 확인
python check_sync_status.py
```

#### 윈도우에서 확인
```cmd
# 동기화 상태 확인
python check_sync_status.py
```

## 동기화되는 파일들

### 핵심 파일들
- `windows_api_test.py` - API 테스트 스크립트
- `start_windows_api_server.py` - API 서버 스크립트
- `integrated_trading_system.py` - 통합 거래 시스템
- `kiwoom_api.py` - 키움 API
- `kiwoom_client_64bit.py` - 64비트 키움 클라이언트
- `kiwoom_32bit_bridge.py` - 32비트 브리지

### 설정 파일들
- `config/` - 모든 설정 파일들
- `requirements.txt` - 기본 패키지 요구사항
- `requirements_windows.txt` - 윈도우용 패키지 요구사항
- `requirements_advanced.txt` - 고급 패키지 요구사항

### 실행 스크립트들
- `run_windows_api_test.bat` - API 테스트 실행
- `start_windows_api_server.bat` - API 서버 실행
- `sync_to_windows_server.sh` - 동기화 스크립트
- `pull_from_mac.bat` - 맥에서 파일 가져오기

### 템플릿 및 문서
- `templates/` - 웹 템플릿 파일들
- `*.md` - 모든 마크다운 문서들

## 설정 파일

### 윈도우 서버 설정 (`config/windows_server.conf`)
```bash
# 윈도우 서버 IP 주소
WINDOWS_HOST="192.168.1.100"

# 윈도우 사용자명
WINDOWS_USER="Administrator"

# 윈도우 서버의 프로젝트 경로
WINDOWS_PATH="C:/Users/Administrator/Desktop/kiwoom_trading"

# SSH 포트
SSH_PORT="22"

# API 서버 포트
API_PORT="8080"
```

## 동기화 후 작업

### 1. 윈도우 서버에서 API 서버 실행
```cmd
# API 서버 실행
start_windows_api_server.bat
```

### 2. API 테스트 실행
```cmd
# API 테스트 실행
run_windows_api_test.bat
```

### 3. 원격으로 실행 (맥에서)
```bash
# API 서버 원격 실행
ssh -p 22 Administrator@192.168.1.100 "cd C:/Users/Administrator/Desktop/kiwoom_trading && ./start_windows_api_server.bat"

# API 테스트 원격 실행
ssh -p 22 Administrator@192.168.1.100 "cd C:/Users/Administrator/Desktop/kiwoom_trading && ./run_windows_api_test.bat"
```

## 문제 해결

### 1. SSH 연결 실패
```bash
# SSH 연결 테스트
ssh -p 22 Administrator@192.168.1.100 "echo '연결 성공'"

# 문제 해결:
# 1. 윈도우 서버가 실행 중인지 확인
# 2. SSH 서비스가 활성화되어 있는지 확인
# 3. 방화벽에서 SSH 포트(22)가 열려있는지 확인
# 4. SSH 키가 설정되어 있는지 확인
```

### 2. 파일 권한 문제
```bash
# 맥에서 실행 권한 부여
chmod +x *.sh

# 윈도우에서 실행 권한 확인
icacls *.bat
```

### 3. Python 환경 문제
```cmd
# 윈도우에서 가상환경 생성
python -m venv venv
venv\Scripts\activate
pip install -r requirements_windows.txt
```

### 4. 포트 충돌 문제
```cmd
# 포트 사용 확인
netstat -an | findstr :8080

# 프로세스 종료
taskkill /f /im python.exe
```

## 자동화 옵션

### 1. 파일 변경 감지 자동 동기화
```bash
# 파일 변경 시 자동 동기화 (개발 중)
watch_and_sync.py
```

### 2. 정기적 동기화 (cron 사용)
```bash
# 매일 오전 9시에 동기화
0 9 * * * /path/to/kiwoom_trading/quick_sync_to_windows.sh
```

### 3. Git 기반 동기화
```bash
# Git을 통한 동기화 (고급 사용자)
git push origin main
# 윈도우에서: git pull origin main
```

## 성능 최적화

### 1. 네트워크 최적화
```bash
# SSH 압축 사용
ssh -C -p 22 Administrator@192.168.1.100

# 병렬 전송 (rsync 사용)
rsync -avz -e "ssh -p 22" ./ Administrator@192.168.1.100:C:/Users/Administrator/Desktop/kiwoom_trading/
```

### 2. 선택적 동기화
```bash
# 특정 파일만 동기화
scp -P 22 specific_file.py Administrator@192.168.1.100:C:/Users/Administrator/Desktop/kiwoom_trading/
```

## 모니터링 및 로깅

### 1. 동기화 로그 확인
```bash
# 로그 파일 위치
logs/sync_log_YYYYMMDD_HHMMSS.txt
logs/sync_status.json
```

### 2. 실시간 모니터링
```bash
# 로그 실시간 모니터링
tail -f logs/sync_log_*.txt
```

### 3. 성능 메트릭
```python
# 동기화 시간 측정
import time
start_time = time.time()
# 동기화 실행
end_time = time.time()
print(f"동기화 시간: {end_time - start_time:.2f}초")
```

## 보안 고려사항

### 1. SSH 키 인증
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

### 3. 파일 암호화 (선택사항)
```python
# 중요 파일 암호화
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher_suite = Fernet(key)
```

## 결론

이 가이드를 따라하면 맥에서 작업한 파일들을 윈도우 서버로 안전하고 효율적으로 동기화할 수 있습니다.

### 권장 워크플로우:
1. 맥에서 개발 작업
2. `./quick_sync_to_windows.sh` 실행 (빠른 동기화)
3. 윈도우 서버에서 API 테스트
4. 문제 발생 시 `./sync_from_mac.sh` 실행 (전체 동기화)
5. `python check_sync_status.py`로 상태 확인

### 주요 장점:
- ✅ 자동화된 파일 동기화
- ✅ 백업 및 복구 기능
- ✅ 상세한 로깅 및 모니터링
- ✅ 다양한 동기화 옵션
- ✅ 보안 고려사항 포함
- ✅ 문제 해결 가이드 제공 