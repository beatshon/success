# GitHub 기반 파일 동기화 가이드

## 개요
이 가이드는 맥과 윈도우 서버 간 GitHub를 통한 파일 동기화 방법을 제공합니다. GitHub를 사용하면 SSH보다 더 안전하고 효율적인 동기화가 가능합니다.

## GitHub 동기화의 장점

### ✅ 주요 장점:
- **버전 관리**: 모든 변경사항이 히스토리로 기록됨
- **백업 기능**: 자동으로 클라우드에 백업됨
- **협업 지원**: 여러 개발자가 동시에 작업 가능
- **브랜치 관리**: 안전한 실험과 롤백 가능
- **충돌 해결**: 자동 충돌 감지 및 해결 도구 제공
- **무료 저장소**: GitHub의 무료 저장소 활용

## 사전 준비사항

### 1. GitHub 계정 및 저장소 설정
```bash
# 1. GitHub에서 새 저장소 생성
# https://github.com/new

# 2. 저장소 이름: kiwoom_trading
# 3. Public 또는 Private 선택
# 4. README 파일 생성 체크
```

### 2. Git 설치 확인
```bash
# 맥에서
brew install git

# 윈도우에서
# https://git-scm.com/ 에서 다운로드
```

### 3. GitHub 인증 설정
```bash
# SSH 키 생성 (맥)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# SSH 키를 GitHub에 등록
# GitHub Settings > SSH and GPG keys > New SSH key
```

## 설정 파일 구성

### 1. GitHub 동기화 설정 파일 수정
`config/github_sync_config.json` 파일을 실제 정보로 수정:

```json
{
  "repo_url": "https://github.com/your-username/kiwoom_trading.git",
  "branch": "main",
  "auto_sync": true,
  "sync_interval": 300,
  "backup_enabled": true,
  "file_patterns": [
    "*.py", "*.bat", "*.sh", "*.md", "*.txt", "*.json",
    "config/*", "templates/*"
  ],
  "exclude_patterns": [
    "*.log", "logs/*", "venv/*", "__pycache__/*", "*.pyc",
    ".git/*", "backup_*/*"
  ],
  "git_config": {
    "user_name": "Your Name",
    "user_email": "your-email@example.com"
  }
}
```

## 동기화 방법

### 1. 맥에서 GitHub 동기화

#### 수동 동기화:
```bash
# 실행 권한 부여
chmod +x github_sync.sh

# GitHub로 푸시 (변경사항 업로드)
./github_sync.sh push

# GitHub에서 풀 (변경사항 다운로드)
./github_sync.sh pull

# 상태 확인
./github_sync.sh status

# 백업 브랜치 생성
./github_sync.sh backup
```

#### 자동 동기화:
```bash
# 자동 모니터링 시작 (파일 변경 시 자동 동기화)
python3 auto_github_sync.py start

# 수동 동기화
python3 auto_github_sync.py sync

# 상태 확인
python3 auto_github_sync.py status
```

### 2. 윈도우에서 GitHub 동기화

#### 수동 동기화:
```cmd
# GitHub로 푸시
github_sync.bat push

# GitHub에서 풀
github_sync.bat pull

# 상태 확인
github_sync.bat status

# 백업 브랜치 생성
github_sync.bat backup
```

#### Python 스크립트 사용:
```cmd
# GitHub로 푸시
python github_sync_manager.py push

# GitHub에서 풀
python github_sync_manager.py pull

# 상태 확인
python github_sync_manager.py status
```

## 워크플로우

### 1. 기본 워크플로우 (권장)

#### 맥에서 개발 시:
```bash
# 1. 개발 작업 수행
# 2. 변경사항 자동 감지 및 동기화
python3 auto_github_sync.py start

# 또는 수동 동기화
./github_sync.sh push
```

#### 윈도우에서 테스트 시:
```cmd
# 1. GitHub에서 최신 파일 가져오기
github_sync.bat pull

# 2. API 테스트 실행
run_windows_api_test.bat

# 3. API 서버 실행
start_windows_api_server.bat
```

### 2. 고급 워크플로우

#### 브랜치 기반 개발:
```bash
# 1. 개발 브랜치 생성
git checkout -b feature/new-feature

# 2. 개발 작업 수행
# 3. 변경사항 커밋
git add .
git commit -m "새 기능 추가"

# 4. GitHub에 푸시
git push origin feature/new-feature

# 5. Pull Request 생성 (GitHub 웹사이트)
# 6. 코드 리뷰 후 main 브랜치에 머지
```

## 자동화 옵션

### 1. 파일 변경 감지 자동 동기화
```bash
# 맥에서 자동 모니터링 시작
python3 auto_github_sync.py start

# 백그라운드에서 실행
nohup python3 auto_github_sync.py start > auto_sync.log 2>&1 &
```

### 2. 정기적 동기화 (cron 사용)
```bash
# 매일 오전 9시에 동기화
0 9 * * * /path/to/kiwoom_trading/github_sync.sh push

# 매시간 동기화
0 * * * * /path/to/kiwoom_trading/github_sync.sh pull
```

### 3. GitHub Actions 자동화
`.github/workflows/sync.yml` 파일 생성:

```yaml
name: Auto Sync

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python run_windows_api_test.py
```

## 문제 해결

### 1. Git 인증 문제
```bash
# SSH 키 확인
ssh -T git@github.com

# Personal Access Token 사용 (HTTPS)
git remote set-url origin https://username:token@github.com/username/repo.git
```

### 2. 충돌 해결
```bash
# 충돌 상태 확인
git status

# 충돌 파일 수정 후
git add .
git commit -m "충돌 해결"
git push origin main
```

### 3. 브랜치 관리
```bash
# 브랜치 목록 확인
git branch -a

# 브랜치 전환
git checkout branch-name

# 브랜치 삭제
git branch -d branch-name
```

### 4. 히스토리 관리
```bash
# 커밋 히스토리 확인
git log --oneline

# 특정 커밋으로 되돌리기
git reset --hard commit-hash

# 변경사항 취소
git checkout -- filename
```

## 보안 고려사항

### 1. 민감한 정보 관리
```bash
# .gitignore 파일에 추가
config/kiwoom_api_keys.py
*.key
*.pem
.env
```

### 2. 환경 변수 사용
```python
# 환경 변수로 API 키 관리
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('KIWOOM_API_KEY')
```

### 3. GitHub Secrets 사용
```yaml
# GitHub Actions에서 시크릿 사용
- name: Use secret
  env:
    API_KEY: ${{ secrets.KIWOOM_API_KEY }}
```

## 성능 최적화

### 1. 파일 필터링
```json
{
  "exclude_patterns": [
    "*.log", "logs/*", "venv/*", "__pycache__/*",
    "*.pyc", ".git/*", "backup_*/*", "temp/*"
  ]
}
```

### 2. 압축 사용
```bash
# Git 압축 활성화
git config --global core.compression 9
```

### 3. 병렬 처리
```python
# 여러 파일 동시 처리
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_file, file) for file in files]
```

## 모니터링 및 로깅

### 1. 동기화 로그 확인
```bash
# 로그 파일 위치
logs/github_sync.log
logs/auto_github_sync.log
```

### 2. 실시간 모니터링
```bash
# 로그 실시간 모니터링
tail -f logs/github_sync.log
```

### 3. GitHub 웹훅 설정
```python
# GitHub 웹훅으로 실시간 알림
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data['ref'] == 'refs/heads/main':
        # 메인 브랜치 업데이트 시 알림
        send_notification("GitHub 동기화 완료")
```

## 결론

GitHub를 통한 동기화는 SSH 기반 동기화보다 더 안전하고 효율적입니다.

### 권장 워크플로우:
1. **맥에서 개발**: `python3 auto_github_sync.py start`
2. **자동 동기화**: 파일 변경 시 자동으로 GitHub에 푸시
3. **윈도우에서 테스트**: `github_sync.bat pull`
4. **API 테스트**: `run_windows_api_test.bat`
5. **상태 모니터링**: `python github_sync_manager.py status`

### 주요 장점:
- ✅ **버전 관리**: 모든 변경사항 추적
- ✅ **자동 백업**: 클라우드에 안전한 백업
- ✅ **협업 지원**: 팀 작업 가능
- ✅ **충돌 해결**: 자동 충돌 감지
- ✅ **브랜치 관리**: 안전한 실험 환경
- ✅ **무료 저장소**: GitHub 무료 플랜 활용

이제 GitHub를 통해 맥과 윈도우 서버 간 안전하고 효율적인 파일 동기화를 할 수 있습니다! 