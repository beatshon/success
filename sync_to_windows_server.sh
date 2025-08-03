#!/bin/bash

# 맥에서 윈도우 서버로 파일 전송 스크립트
# 윈도우 서버에서 API 테스트를 위해 필요한 파일들을 전송

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

log_info "윈도우 서버 정보:"
echo "  호스트: $WINDOWS_HOST"
echo "  사용자: $WINDOWS_USER"
echo "  경로: $WINDOWS_PATH"
echo "  SSH 포트: $SSH_PORT"
echo

# SSH 연결 테스트
log_info "SSH 연결 테스트 중..."
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

# 전송할 파일 목록 정의
FILES_TO_SYNC=(
    "windows_api_test.py"
    "run_windows_api_test.bat"
    "config/"
    "requirements.txt"
    "requirements_windows.txt"
    "kiwoom_api.py"
    "integrated_trading_system.py"
    "real_time_data_server.py"
    "news_collector.py"
    "advanced_deep_learning_model.py"
    "templates/"
    "logs/"
)

# 백업 디렉토리 생성
BACKUP_DIR="backup_local_files/$(date +%Y%m%d_%H%M%S)"
log_info "로컬 백업 디렉토리 생성: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 파일 전송 함수
sync_files() {
    local file="$1"
    
    if [ -e "$file" ]; then
        log_info "전송 중: $file"
        
        # 로컬 백업
        if [ -d "$file" ]; then
            cp -r "$file" "$BACKUP_DIR/"
        else
            cp "$file" "$BACKUP_DIR/"
        fi
        
        # 윈도우 서버로 전송
        if scp -P $SSH_PORT -r "$file" "$WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/"; then
            log_success "전송 완료: $file"
        else
            log_error "전송 실패: $file"
            return 1
        fi
    else
        log_warning "파일을 찾을 수 없음: $file"
    fi
}

# 메인 전송 프로세스
log_info "파일 전송 시작..."
echo "========================================"

for file in "${FILES_TO_SYNC[@]}"; do
    sync_files "$file"
done

# 윈도우 서버에서 필요한 디렉토리 생성
log_info "윈도우 서버에서 필요한 디렉토리 생성..."
ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST << 'EOF'
    cd "$WINDOWS_PATH"
    mkdir -p logs
    mkdir -p config
    mkdir -p templates
    mkdir -p backup_local_files
    echo "디렉토리 생성 완료"
EOF

# 윈도우 서버에서 Python 환경 설정
log_info "윈도우 서버에서 Python 환경 설정..."
ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST << 'EOF'
    cd "$WINDOWS_PATH"
    
    # Python 버전 확인
    python --version
    
    # 가상환경 생성 (없는 경우)
    if [ ! -d "venv" ]; then
        echo "가상환경 생성 중..."
        python -m venv venv
    fi
    
    # 가상환경 활성화 및 패키지 설치
    echo "패키지 설치 중..."
    source venv/Scripts/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements_windows.txt
    
    echo "Python 환경 설정 완료"
EOF

# 전송 완료 후 테스트 실행 준비
log_info "전송 완료!"
echo "========================================"
log_success "모든 파일이 윈도우 서버로 전송되었습니다."

echo
log_info "다음 단계:"
echo "1. 윈도우 서버에 접속"
echo "2. 프로젝트 디렉토리로 이동: cd $WINDOWS_PATH"
echo "3. API 테스트 실행: ./run_windows_api_test.bat"
echo
echo "또는 원격으로 테스트를 실행하려면:"
echo "ssh -p $SSH_PORT $WINDOWS_USER@$WINDOWS_HOST 'cd $WINDOWS_PATH && ./run_windows_api_test.bat'"

# 백업 정보 표시
echo
log_info "로컬 백업 위치: $BACKUP_DIR"
echo "백업된 파일들:"
ls -la "$BACKUP_DIR"

echo
log_success "전송 작업 완료!" 