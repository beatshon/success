#!/bin/bash

# GitHub를 통한 맥-윈도우 자동 동기화 설정
# 맥에서 작업한 파일이 자동으로 Windows 서버에 반영

echo "🔄 GitHub 자동 동기화 시스템 설정"
echo "=================================="

# Git 상태 확인
if ! command -v git &> /dev/null; then
    echo "❌ Git이 설치되지 않았습니다."
    echo "Git을 설치하세요: https://git-scm.com/"
    exit 1
fi

echo "✅ Git 설치 확인 완료"

# 현재 Git 저장소 확인
if [ ! -d ".git" ]; then
    echo "❌ 현재 디렉토리가 Git 저장소가 아닙니다."
    echo "Git 저장소를 초기화하시겠습니까? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git init
        echo "✅ Git 저장소 초기화 완료"
    else
        echo "Git 저장소가 필요합니다."
        exit 1
    fi
fi

# .gitignore 파일 확인 및 생성
if [ ! -f ".gitignore" ]; then
    echo "📝 .gitignore 파일 생성 중..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Logs
logs/*.log
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Sensitive data
config/windows_server.conf
*.key
*.pem

# Temporary files
*.tmp
*.temp
EOF
    echo "✅ .gitignore 파일 생성 완료"
fi

# 자동 커밋 및 푸시 스크립트 생성
echo "📝 자동 동기화 스크립트 생성 중..."

cat > auto_commit_and_push.sh << 'EOF'
#!/bin/bash

# 자동 커밋 및 푸시 스크립트
# 파일 변경 시 자동으로 GitHub에 푸시

echo "🔄 자동 커밋 및 푸시 시작"
echo "=========================="

# 변경된 파일 확인
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 변경된 파일이 없습니다."
    exit 0
fi

# 변경된 파일 목록 표시
echo "📋 변경된 파일:"
git status --porcelain

# 커밋 메시지 생성
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
commit_message="Auto sync: $timestamp"

# 변경사항 스테이징
echo "📦 변경사항 스테이징 중..."
git add .

# 커밋
echo "💾 커밋 중..."
git commit -m "$commit_message"

# 푸시
echo "🚀 GitHub에 푸시 중..."
if git push origin main; then
    echo "✅ 푸시 완료"
else
    echo "❌ 푸시 실패"
    exit 1
fi

echo "✅ 자동 동기화 완료"
EOF

chmod +x auto_commit_and_push.sh
echo "✅ 자동 커밋 스크립트 생성 완료"

# 실시간 감시 스크립트 생성
cat > watch_and_commit.py << 'EOF'
#!/usr/bin/env python3
"""
실시간 파일 감시 및 자동 커밋
파일이 변경되면 자동으로 GitHub에 푸시
"""

import os
import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

# 로그 설정
logger.add("logs/github_sync.log", rotation="1 day", retention="7 days")

class GitSyncHandler(FileSystemEventHandler):
    """Git 동기화 이벤트 핸들러"""
    
    def __init__(self):
        self.last_commit_time = {}
        self.commit_cooldown = 30  # 30초 쿨다운
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        current_time = time.time()
        
        # 쿨다운 체크
        if file_path in self.last_commit_time:
            if current_time - self.last_commit_time[file_path] < self.commit_cooldown:
                return
        
        self.last_commit_time[file_path] = current_time
        
        # 동기화할 파일인지 확인
        if self.should_sync_file(file_path):
            logger.info(f"파일 변경 감지: {file_path}")
            self.auto_commit_and_push()
    
    def should_sync_file(self, file_path):
        """동기화할 파일인지 확인"""
        # .gitignore에 있는 파일 제외
        ignore_patterns = [
            '__pycache__', '.git', 'venv', 'logs', 
            '.DS_Store', '*.log', '*.tmp'
        ]
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return False
        
        # 특정 확장자만 동기화
        sync_extensions = ['.py', '.md', '.txt', '.json', '.bat', '.sh']
        _, ext = os.path.splitext(file_path)
        
        return ext in sync_extensions
    
    def auto_commit_and_push(self):
        """자동 커밋 및 푸시"""
        try:
            logger.info("자동 커밋 및 푸시 시작")
            
            # 변경사항 확인
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                logger.info("변경사항이 없습니다.")
                return
            
            # 변경사항 스테이징
            subprocess.run(['git', 'add', '.'], check=True)
            
            # 커밋
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto sync: {timestamp}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            # 푸시
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            logger.info("✅ 자동 동기화 완료")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 자동 동기화 실패: {e}")
        except Exception as e:
            logger.error(f"❌ 자동 동기화 오류: {e}")

def main():
    """메인 실행 함수"""
    logger.info("🔄 GitHub 자동 동기화 시스템 시작")
    
    # 감시할 디렉토리 설정
    watch_directories = ['.', 'config']
    
    # Observer 설정
    observer = Observer()
    event_handler = GitSyncHandler()
    
    # 디렉토리 감시 등록
    for directory in watch_directories:
        if os.path.exists(directory):
            observer.schedule(event_handler, directory, recursive=True)
            logger.info(f"📁 감시 시작: {directory}")
    
    # 감시 시작
    observer.start()
    logger.info("🚀 실시간 파일 감시 시작")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    
    observer.stop()
    observer.join()
    logger.info("🛑 GitHub 자동 동기화 시스템 종료")

if __name__ == "__main__":
    main()
EOF

echo "✅ 실시간 감시 스크립트 생성 완료"

# GitHub 원격 저장소 설정 가이드
echo ""
echo "📋 GitHub 원격 저장소 설정:"
echo "=========================="
echo ""
echo "1. GitHub에서 새 저장소 생성"
echo "2. 다음 명령어 실행:"
echo ""
echo "   git remote add origin https://github.com/사용자명/저장소명.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 자동 동기화 시작:"
echo "   python watch_and_commit.py"
echo ""
echo "4. Windows 서버에서 자동 풀:"
echo "   git pull origin main"
echo ""

# Windows용 자동 풀 스크립트 생성
cat > windows_auto_pull.bat << 'EOF'
@echo off
REM Windows 자동 풀 스크립트
REM GitHub에서 변경사항을 자동으로 가져옴

title Windows Auto Pull

echo.
echo ========================================
echo    Windows 자동 풀 시스템
echo ========================================
echo.

cd /d "%~dp0"

:loop
echo.
echo 🔄 GitHub에서 변경사항 확인 중...
echo.

git fetch origin
git status -uno

if git status -uno | findstr "behind" >nul; then
    echo.
    echo 📥 새로운 변경사항 발견!
    echo.
    
    git pull origin main
    
    if errorlevel 1 (
        echo ❌ 풀 실패
    ) else (
        echo ✅ 풀 완료
        echo.
        echo 🔄 Windows 서버 재시작 중...
        echo.
        
        REM 서버 재시작 (선택사항)
        REM taskkill /f /im python.exe >nul 2>&1
        REM start /b python windows_api_server.py --host 0.0.0.0 --port 8080
    )
else
    echo ✅ 최신 상태입니다.
fi

echo.
echo ⏰ 30초 후 다시 확인합니다...
timeout /t 30 /nobreak >nul

goto loop
EOF

echo "✅ Windows 자동 풀 스크립트 생성 완료"

echo ""
echo "🎉 GitHub 자동 동기화 시스템 설정 완료!"
echo "======================================"
echo ""
echo "📋 사용 방법:"
echo "1. GitHub 저장소 설정"
echo "2. 맥에서: python watch_and_commit.py"
echo "3. Windows에서: windows_auto_pull.bat"
echo ""
echo "📝 생성된 파일:"
echo "- auto_commit_and_push.sh: 수동 동기화"
echo "- watch_and_commit.py: 실시간 자동 동기화"
echo "- windows_auto_pull.bat: Windows 자동 풀"
echo "" 