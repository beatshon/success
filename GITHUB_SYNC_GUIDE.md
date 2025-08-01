# GitHub 자동 동기화 가이드

## 🔄 맥-윈도우 실시간 파일 동기화

GitHub를 통해 맥에서 작업한 파일이 실시간으로 Windows 서버에 반영되는 시스템입니다.

## 🚀 설정 방법

### 1단계: GitHub 저장소 생성

1. **GitHub에서 새 저장소 생성**
   - https://github.com/new 접속
   - 저장소 이름: `kiwoom_trading` (또는 원하는 이름)
   - Public 또는 Private 선택
   - README 파일 생성 체크 해제

2. **로컬 저장소 설정**
   ```bash
   # 현재 디렉토리에서
   git init
   git add .
   git commit -m "Initial commit"
   
   # GitHub 원격 저장소 연결
   git remote add origin https://github.com/사용자명/저장소명.git
   git branch -M main
   git push -u origin main
   ```

### 2단계: 맥에서 자동 동기화 시작

```bash
# 실시간 파일 감시 및 자동 푸시 시작
python watch_and_commit.py
```

**기능:**
- 파일 변경 감지 시 자동 커밋
- 30초 쿨다운으로 중복 커밋 방지
- GitHub에 자동 푸시
- 로그 파일에 동기화 기록

### 3단계: Windows에서 자동 풀

```cmd
# Windows에서 자동 풀 시작
windows_auto_pull.bat
```

**기능:**
- 30초마다 GitHub 변경사항 확인
- 새로운 변경사항 발견 시 자동 풀
- Windows 서버 자동 재시작 (선택사항)

## 📋 동기화 파일 목록

### ✅ 동기화되는 파일
- `*.py` - Python 스크립트
- `*.md` - 마크다운 문서
- `*.txt` - 텍스트 파일
- `*.json` - 설정 파일
- `*.bat` - Windows 배치 파일
- `*.sh` - 맥/리눅스 스크립트

### ❌ 동기화되지 않는 파일
- `__pycache__/` - Python 캐시
- `venv/` - 가상환경
- `logs/` - 로그 파일
- `.DS_Store` - 맥 시스템 파일
- `*.log` - 로그 파일
- `config/windows_server.conf` - 민감한 설정

## 🔧 사용 방법

### 맥에서 개발 시

1. **파일 편집**
   ```bash
   # 코드 편집
   vim mac_hybrid_controller.py
   ```

2. **자동 동기화 확인**
   ```bash
   # 실시간 감시 로그 확인
   tail -f logs/github_sync.log
   ```

3. **수동 동기화 (필요시)**
   ```bash
   # 수동으로 커밋 및 푸시
   ./auto_commit_and_push.sh
   ```

### Windows에서 확인

1. **변경사항 확인**
   ```cmd
   # Git 상태 확인
   git status
   ```

2. **수동 풀 (필요시)**
   ```cmd
   # 수동으로 변경사항 가져오기
   git pull origin main
   ```

## 📊 동기화 상태 확인

### 맥에서 확인
```bash
# GitHub 동기화 로그
tail -f logs/github_sync.log

# Git 상태
git status
git log --oneline -5
```

### Windows에서 확인
```cmd
# Git 상태
git status
git log --oneline -5

# 자동 풀 로그
type logs\windows_auto_pull.log
```

## ⚙️ 고급 설정

### 동기화 주기 조정

**맥 (watch_and_commit.py):**
```python
self.commit_cooldown = 30  # 30초 쿨다운
```

**Windows (windows_auto_pull.bat):**
```cmd
timeout /t 30 /nobreak >nul  # 30초마다 확인
```

### 동기화할 파일 확장자 추가

**watch_and_commit.py에서:**
```python
sync_extensions = ['.py', '.md', '.txt', '.json', '.bat', '.sh', '.yml', '.yaml']
```

### 자동 서버 재시작 설정

**windows_auto_pull.bat에서:**
```cmd
REM 서버 재시작 활성화
taskkill /f /im python.exe >nul 2>&1
start /b python windows_api_server.py --host 0.0.0.0 --port 8080
```

## 🛠️ 문제 해결

### 동기화 실패

1. **GitHub 인증 확인**
   ```bash
   # GitHub 토큰 또는 SSH 키 설정
   git config --global user.name "사용자명"
   git config --global user.email "이메일"
   ```

2. **네트워크 연결 확인**
   ```bash
   # GitHub 연결 테스트
   ping github.com
   ```

3. **충돌 해결**
   ```bash
   # 충돌 파일 확인
   git status
   
   # 충돌 해결 후
   git add .
   git commit -m "Resolve conflicts"
   git push origin main
   ```

### Windows 자동 풀 실패

1. **Git 설정 확인**
   ```cmd
   git config --list
   ```

2. **권한 확인**
   ```cmd
   # 관리자 권한으로 실행
   ```

3. **수동 풀 시도**
   ```cmd
   git fetch origin
   git pull origin main
   ```

## 📝 로그 파일

### 맥 로그
- `logs/github_sync.log`: GitHub 동기화 로그
- `logs/watch_and_sync.log`: 파일 감시 로그

### Windows 로그
- `logs/windows_auto_pull.log`: 자동 풀 로그
- `logs/windows_api_server.log`: API 서버 로그

## 🔒 보안 고려사항

1. **민감한 정보 제외**
   - API 키, 비밀번호 등은 `.gitignore`에 추가
   - `config/windows_server.conf`는 동기화 제외

2. **Private 저장소 사용**
   - 실제 운영 시 Private 저장소 권장
   - GitHub 토큰 사용

3. **백업 설정**
   - 중요한 설정 파일은 별도 백업
   - 로그 파일 정기 정리

## 📞 지원

문제 발생 시:
1. 로그 파일 확인
2. Git 상태 확인
3. 네트워크 연결 확인
4. GitHub 저장소 설정 확인

---

**✅ 이제 맥에서 작업한 파일이 실시간으로 Windows 서버에 반영됩니다!** 