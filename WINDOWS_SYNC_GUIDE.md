# Windows 서버 동기화 설정 가이드

맥에서 진행한 코드 작업을 윈도우 서버에 자동으로 동기화하는 시스템을 설정하는 방법입니다.

## 📋 목차

1. [개요](#개요)
2. [설정 파일](#설정-파일)
3. [동기화 방법](#동기화-방법)
4. [서비스 설치](#서비스-설치)
5. [모니터링](#모니터링)
6. [문제 해결](#문제-해결)

## 🎯 개요

이 시스템은 다음과 같은 방법으로 맥과 윈도우 서버 간 동기화를 제공합니다:

- **GitHub 기반 동기화**: 맥에서 코드를 GitHub에 푸시하면 윈도우 서버가 자동으로 풀
- **파일 감시 동기화**: 실시간으로 파일 변경을 감지하여 동기화
- **Windows 서비스**: 백그라운드에서 자동으로 동기화 수행

## ⚙️ 설정 파일

### config/windows_server.conf

```bash
# Windows 서버 연결 설정
WINDOWS_HOST="192.168.1.100"
WINDOWS_USER="Administrator"
WINDOWS_PATH="C:/Users/Administrator/Desktop/kiwoom_trading"

# 동기화 설정
SYNC_INTERVAL="30"
AUTO_RESTART="true"
LOG_LEVEL="INFO"

# GitHub 설정
GITHUB_REPO="your-username/kiwoom_trading"
GITHUB_BRANCH="main"
```

## 🔄 동기화 방법

### 1. 수동 동기화

```bash
# 동기화 관리자 실행
python windows_sync_manager.py

# 또는 명령어로 실행
python windows_sync_manager.py sync    # 파일 동기화
python windows_sync_manager.py restart # 서비스 재시작
python windows_sync_manager.py git     # GitHub 업데이트
python windows_sync_manager.py auto    # 자동 동기화
```

### 2. 배치 파일 실행

```bash
# 동기화 관리자 시작
start_windows_sync.bat

# 자동 풀 스크립트
windows_auto_pull.bat
```

### 3. Windows 서비스

```bash
# 서비스 설치
install_sync_service.bat

# 서비스 관리
net start KiwoomSyncService    # 시작
net stop KiwoomSyncService     # 중지
sc query KiwoomSyncService     # 상태 확인
```

## 🔧 서비스 설치

### 1. 관리자 권한으로 실행

```bash
# 관리자 권한으로 명령 프롬프트 실행
install_sync_service.bat
```

### 2. 수동 설치

```bash
# 필요한 패키지 설치
pip install pywin32 watchdog

# 서비스 설치
python windows_sync_service.py install

# 서비스 시작
python windows_sync_service.py start
```

## 📊 모니터링

### 로그 파일

- `logs/sync_manager.log`: 동기화 관리자 로그
- `logs/sync_service.log`: Windows 서비스 로그
- `logs/windows_api_server.log`: API 서버 로그

### 실시간 모니터링

```bash
# 로그 실시간 확인
Get-Content logs/sync_manager.log -Wait

# 서비스 상태 확인
sc query KiwoomSyncService
```

## 🛠️ 문제 해결

### 일반적인 문제

#### 1. Python 경로 문제

```bash
# Python 경로 확인
python --version
where python

# PATH에 Python 추가
set PATH=%PATH%;C:\Python39\
```

#### 2. 권한 문제

```bash
# 관리자 권한으로 실행
# 또는 서비스 계정 권한 설정
```

#### 3. 네트워크 연결 문제

```bash
# Windows 서버 IP 확인
ipconfig

# 네트워크 연결 테스트
ping 192.168.1.100
```

#### 4. Git 설정 문제

```bash
# Git 설정 확인
git config --list

# 원격 저장소 확인
git remote -v

# 인증 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 디버깅

#### 1. 상세 로그 활성화

```python
# config/windows_server.conf
LOG_LEVEL="DEBUG"
```

#### 2. 수동 테스트

```bash
# 각 단계별 수동 테스트
python windows_sync_manager.py sync
python windows_sync_manager.py git
python windows_sync_manager.py restart
```

#### 3. 서비스 로그 확인

```bash
# 이벤트 뷰어에서 확인
eventvwr.msc
```

## 📝 사용 예시

### 맥에서 코드 수정 후

1. **코드 수정**
2. **Git 커밋 및 푸시**
   ```bash
   git add .
   git commit -m "Update trading strategy"
   git push origin main
   ```

### 윈도우 서버에서

1. **자동 동기화 확인**
   - 서비스가 자동으로 GitHub에서 변경사항을 감지
   - 30초마다 확인하여 새로운 변경사항이 있으면 자동 풀

2. **수동 동기화**
   ```bash
   python windows_sync_manager.py
   ```

3. **서비스 재시작**
   - 변경사항이 있을 때 자동으로 서비스 재시작
   - 또는 수동으로 재시작

## 🔒 보안 고려사항

1. **네트워크 보안**
   - 방화벽 설정으로 필요한 포트만 열기
   - SSH 키 기반 인증 사용

2. **파일 권한**
   - 서비스 계정에 필요한 최소 권한만 부여
   - 중요 파일은 읽기 전용으로 설정

3. **로그 관리**
   - 로그 파일 크기 제한
   - 정기적인 로그 정리

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. 로그 파일 확인
2. 네트워크 연결 상태
3. 서비스 상태
4. Python 환경 설정

추가 지원이 필요하면 프로젝트 이슈를 생성하거나 개발팀에 문의하세요. 