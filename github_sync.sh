#!/bin/bash

# GitHub 동기화 실행 스크립트 (맥용)
# 맥과 윈도우 서버 간 GitHub를 통한 파일 동기화

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "========================================"
echo "GitHub 동기화 실행 스크립트 (맥용)"
echo "========================================"
echo

# 현재 디렉토리 확인
log_info "현재 작업 디렉토리: $(pwd)"
echo

# Git 설치 확인
log_info "Git 설치 확인 중..."
if command -v git &> /dev/null; then
    git_version=$(git --version)
    log_success "Git 설치 확인됨: $git_version"
else
    log_error "Git이 설치되지 않았습니다."
    echo "Git을 설치해주세요:"
    echo "  brew install git"
    echo "  또는 https://git-scm.com/ 에서 다운로드"
    exit 1
fi
echo

# Python 환경 확인
log_info "Python 환경 확인 중..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    log_success "Python 설치 확인됨: $python_version"
else
    log_error "Python이 설치되지 않았습니다."
    echo "Python을 설치해주세요:"
    echo "  brew install python"
    exit 1
fi
echo

# 가상환경 활성화 (있는 경우)
if [ -f "venv/bin/activate" ]; then
    log_info "가상환경 활성화 중..."
    source venv/bin/activate
    log_success "가상환경 활성화 완료"
    echo
fi

# logs 디렉토리 생성
if [ ! -d "logs" ]; then
    log_info "logs 디렉토리 생성 중..."
    mkdir -p logs
fi

# GitHub 동기화 실행
log_info "GitHub 동기화 시작..."
echo "========================================"

case "$1" in
    "push")
        log_info "GitHub로 푸시 중..."
        python3 github_sync_manager.py push
        ;;
    "pull")
        log_info "GitHub에서 풀 중..."
        python3 github_sync_manager.py pull
        ;;
    "status")
        log_info "Git 상태 확인 중..."
        python3 github_sync_manager.py status
        ;;
    "backup")
        log_info "백업 브랜치 생성 중..."
        python3 github_sync_manager.py backup
        ;;
    "setup")
        log_info "GitHub 저장소 초기 설정 중..."
        setup_github_repo
        ;;
    *)
        echo "사용법:"
        echo "  ./github_sync.sh push   - GitHub로 푸시"
        echo "  ./github_sync.sh pull   - GitHub에서 풀"
        echo "  ./github_sync.sh status - 상태 확인"
        echo "  ./github_sync.sh backup - 백업 브랜치 생성"
        echo "  ./github_sync.sh setup  - GitHub 저장소 초기 설정"
        echo
        log_info "기본 동기화 (풀 후 푸시)..."
        python3 github_sync_manager.py pull
        python3 github_sync_manager.py push
        ;;
esac

echo
echo "========================================"
log_success "GitHub 동기화 완료!"
echo

# 동기화 후 상태 확인
log_info "동기화 후 상태 확인..."
git status --short

echo
log_info "다음 단계:"
echo "1. 윈도우 서버에서: github_sync.bat pull"
echo "2. API 테스트 실행: run_windows_api_test.bat"
echo "3. API 서버 실행: start_windows_api_server.bat" 