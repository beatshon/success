#!/bin/bash

# 맥에서 윈도우 서버로 파일 재동기화 스크립트
# 맥에서 작업한 최신 파일들을 윈도우 서버로 가져와서 동기화

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_sync() {
    echo -e "${CYAN}[SYNC]${NC} $1"
}

# 설정 파일 로드
if [ -f "config/windows_server.conf" ]; then
    source config/windows_server.conf
else
    log_error "설정 파일을 찾을 수 없습니다: config/windows_server.conf"
    exit 1
fi

# 필수 변수 확인
if [ -z "$WINDOWS_HOST" ] || [ -z "$WINDOWS_USER" ] || [ -z "$WINDOWS_PATH" ]; then
    log_error "설정 파일에 필수 정보가 누락되었습니다."
    echo "다음 정보를 확인해주세요:"
    echo "- WINDOWS_HOST: 윈도우 서버 IP 주소"
    echo "- WINDOWS_USER: 윈도우 사용자명"
    echo "- WINDOWS_PATH: 윈도우 서버의 프로젝트 경로"
    exit 1
fi

log_step "맥에서 윈도우 서버로 파일 재동기화 시작"
echo "========================================"
log_info "윈도우 서버 정보:"
echo "  호스트: $WINDOWS_HOST"
echo "  사용자: $WINDOWS_USER"
echo "  경로: $WINDOWS_PATH"
echo "  SSH 포트: $SSH_PORT"
echo

# SSH 연결 테스트
log_step "SSH 연결 테스트 중..."
if ssh -p $SSH_PORT -o ConnectTimeout=10 -o BatchMode=yes $WINDOWS_USER@$WINDOWS_HOST "echo 'SSH 연결 성공'" 2>/dev/null; then
    log_success "SSH 연결 성공"
else
    log_error "SSH 연결 실패"
    echo "다음을 확인해주세요:"
    echo "1. 윈도우 서버가 실행 중인지"
    echo "2. SSH 서비스가 활성화되어 있는지"
    echo "3. 방화벽에서 SSH 포트($SSH_PORT)가 열려있는지"
    echo "4. SSH 키가 설정되어 있는지"
    exit 1
fi

# 윈도우 서버에서 현재 상태 확인
log_step "윈도우 서버 현재 상태 확인..."
ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST << 'EOF'
    cd "$WINDOWS_PATH"
    echo "현재 디렉토리: $(pwd)"
    echo "파일 개수: $(find . -type f | wc -l)"
    echo "최근 수정된 파일들:"
    find . -type f -mtime -1 -name "*.py" | head -5
    echo "디스크 사용량:"
    du -sh .
EOF

# 백업 디렉토리 생성
BACKUP_DIR="backup_local_files/$(date +%Y%m%d_%H%M%S)_resync"
log_info "로컬 백업 디렉토리 생성: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 동기화할 파일 목록 정의 (맥에서 작업한 주요 파일들)
SYNC_FILES=(
    # 핵심 API 및 테스트 파일들
    "windows_api_test.py"
    "start_windows_api_server.py"
    "integrated_trading_system.py"
    "real_time_data_server.py"
    "news_collector.py"
    "advanced_deep_learning_model.py"
    "kiwoom_api.py"
    "kiwoom_client_64bit.py"
    "kiwoom_32bit_bridge.py"
    
    # 설정 파일들
    "config/"
    "requirements.txt"
    "requirements_windows.txt"
    "requirements_advanced.txt"
    
    # 템플릿 파일들
    "templates/"
    
    # 실행 스크립트들
    "run_windows_api_test.bat"
    "start_windows_api_server.bat"
    "sync_to_windows_server.sh"
    
    # 가이드 문서들
    "MAC_TO_WINDOWS_API_TEST_GUIDE.md"
    "KIWOOM_API_SETUP_GUIDE.md"
    "DEPLOYMENT_GUIDE.md"
    
    # 기타 중요한 파일들
    "integrated_advanced_system.py"
    "simple_advanced_system.py"
    "advanced_analytics_system.py"
    "advanced_investment_signals.py"
    "portfolio_optimizer.py"
    "trading_strategy.py"
    "technical_indicators.py"
    "risk_manager.py"
    "notification_system.py"
)

# 파일 동기화 함수
sync_file() {
    local file="$1"
    
    if [ -e "$file" ]; then
        log_sync "동기화 중: $file"
        
        # 로컬 백업
        if [ -d "$file" ]; then
            cp -r "$file" "$BACKUP_DIR/"
        else
            cp "$file" "$BACKUP_DIR/"
        fi
        
        # 윈도우 서버로 전송
        if scp -P $SSH_PORT -r "$file" "$WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/"; then
            log_success "동기화 완료: $file"
            return 0
        else
            log_error "동기화 실패: $file"
            return 1
        fi
    else
        log_warning "파일을 찾을 수 없음: $file"
        return 0
    fi
}

# 메인 동기화 프로세스
log_step "파일 동기화 시작..."
echo "========================================"

SYNC_COUNT=0
FAILED_COUNT=0

for file in "${SYNC_FILES[@]}"; do
    if sync_file "$file"; then
        ((SYNC_COUNT++))
    else
        ((FAILED_COUNT++))
    fi
done

# 윈도우 서버에서 추가 설정
log_step "윈도우 서버에서 추가 설정 수행..."
ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST << 'EOF'
    cd "$WINDOWS_PATH"
    
    # 필요한 디렉토리 생성
    mkdir -p logs
    mkdir -p config
    mkdir -p templates
    mkdir -p backup_local_files
    mkdir -p investment_data
    mkdir -p trading_data
    
    # 파일 권한 설정
    chmod +x *.bat 2>/dev/null || true
    chmod +x *.sh 2>/dev/null || true
    
    # Python 환경 업데이트
    if [ -d "venv" ]; then
        echo "가상환경 활성화 및 패키지 업데이트 중..."
        source venv/Scripts/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements_windows.txt
        echo "패키지 업데이트 완료"
    else
        echo "가상환경이 없습니다. 새로 생성하시겠습니까?"
    fi
    
    # 파일 개수 및 크기 확인
    echo "동기화 후 상태:"
    echo "파일 개수: $(find . -type f | wc -l)"
    echo "디스크 사용량: $(du -sh .)"
    echo "최근 수정된 파일들:"
    find . -type f -mtime -1 | head -5
EOF

# 동기화 결과 요약
log_step "동기화 완료!"
echo "========================================"
log_success "동기화 작업이 완료되었습니다."

echo
log_info "동기화 결과:"
echo "  ✅ 성공: $SYNC_COUNT개 파일"
if [ $FAILED_COUNT -gt 0 ]; then
    echo "  ❌ 실패: $FAILED_COUNT개 파일"
fi

echo
log_info "다음 단계:"
echo "1. 윈도우 서버에 접속"
echo "2. 프로젝트 디렉토리로 이동: cd $WINDOWS_PATH"
echo "3. API 서버 실행: ./start_windows_api_server.bat"
echo "4. API 테스트 실행: ./run_windows_api_test.bat"

echo
log_info "원격 실행 명령어:"
echo "# API 서버 실행:"
echo "ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST 'cd $WINDOWS_PATH && ./start_windows_api_server.bat'"
echo
echo "# API 테스트 실행:"
echo "ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST 'cd $WINDOWS_PATH && ./run_windows_api_test.bat'"

# 백업 정보 표시
echo
log_info "로컬 백업 위치: $BACKUP_DIR"
echo "백업된 파일들:"
ls -la "$BACKUP_DIR" | head -10

# 동기화 로그 저장
SYNC_LOG="logs/sync_log_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p logs
{
    echo "동기화 로그 - $(date)"
    echo "========================================"
    echo "윈도우 서버: $WINDOWS_HOST"
    echo "사용자: $WINDOWS_USER"
    echo "경로: $WINDOWS_PATH"
    echo "성공: $SYNC_COUNT개 파일"
    echo "실패: $FAILED_COUNT개 파일"
    echo "백업 위치: $BACKUP_DIR"
} > "$SYNC_LOG"

log_success "동기화 로그 저장: $SYNC_LOG"
echo
log_success "재동기화 작업 완료!" 