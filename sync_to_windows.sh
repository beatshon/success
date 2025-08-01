#!/bin/bash

# 맥에서 Windows 서버로 파일 동기화 스크립트
# 실시간으로 변경된 파일을 Windows 서버에 반영

echo "🔄 Windows 서버 파일 동기화 시작"
echo "=================================="

# Windows 서버 설정
WINDOWS_HOST="192.168.1.100"  # Windows 서버 IP 주소
WINDOWS_USER="user"           # Windows 사용자명
WINDOWS_PATH="/path/to/kiwoom_trading"  # Windows 서버 경로

# 동기화할 파일 목록
FILES_TO_SYNC=(
    "windows_api_server.py"
    "kiwoom_api.py"
    "auto_trader.py"
    "trading_strategy.py"
    "requirements.txt"
    "config/hybrid_config.json"
)

# 동기화할 디렉토리 목록
DIRS_TO_SYNC=(
    "config"
    "logs"
)

# 파일 동기화 함수
sync_files() {
    echo "📁 파일 동기화 중..."
    
    for file in "${FILES_TO_SYNC[@]}"; do
        if [ -f "$file" ]; then
            echo "  📄 $file → Windows 서버"
            scp "$file" "$WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/$file"
            if [ $? -eq 0 ]; then
                echo "    ✅ 성공"
            else
                echo "    ❌ 실패"
            fi
        else
            echo "  ⚠️ 파일 없음: $file"
        fi
    done
}

# 디렉토리 동기화 함수
sync_directories() {
    echo "📂 디렉토리 동기화 중..."
    
    for dir in "${DIRS_TO_SYNC[@]}"; do
        if [ -d "$dir" ]; then
            echo "  📁 $dir → Windows 서버"
            scp -r "$dir" "$WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/"
            if [ $? -eq 0 ]; then
                echo "    ✅ 성공"
            else
                echo "    ❌ 실패"
            fi
        else
            echo "  ⚠️ 디렉토리 없음: $dir"
        fi
    done
}

# Windows 서버 연결 테스트
test_connection() {
    echo "🔍 Windows 서버 연결 테스트..."
    if ping -c 1 "$WINDOWS_HOST" > /dev/null 2>&1; then
        echo "  ✅ Windows 서버 연결 성공"
        return 0
    else
        echo "  ❌ Windows 서버 연결 실패"
        return 1
    fi
}

# Windows 서버 재시작
restart_windows_server() {
    echo "🔄 Windows 서버 재시작 요청..."
    
    # SSH를 통해 Windows 서버에서 Python 프로세스 재시작
    ssh "$WINDOWS_USER@$WINDOWS_HOST" << 'EOF'
        cd /path/to/kiwoom_trading
        
        # 기존 Python 프로세스 종료
        pkill -f "windows_api_server.py"
        sleep 2
        
        # 새로운 서버 시작
        nohup python windows_api_server.py --host 0.0.0.0 --port 8080 > logs/windows_api_server.log 2>&1 &
        
        echo "Windows API 서버 재시작 완료"
EOF
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Windows 서버 재시작 성공"
    else
        echo "  ❌ Windows 서버 재시작 실패"
    fi
}

# 메인 실행
main() {
    # 설정 확인
    if [ ! -f "config/windows_server.conf" ]; then
        echo "⚠️ Windows 서버 설정 파일이 없습니다."
        echo "config/windows_server.conf 파일을 생성하세요:"
        echo "WINDOWS_HOST=192.168.1.100"
        echo "WINDOWS_USER=user"
        echo "WINDOWS_PATH=/path/to/kiwoom_trading"
        exit 1
    fi
    
    # 설정 파일 로드
    source config/windows_server.conf
    
    # 연결 테스트
    if ! test_connection; then
        echo "❌ Windows 서버에 연결할 수 없습니다."
        echo "네트워크 연결과 설정을 확인하세요."
        exit 1
    fi
    
    # 파일 동기화
    sync_files
    sync_directories
    
    # 재시작 여부 확인
    read -p "Windows 서버를 재시작하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_windows_server
    fi
    
    echo "✅ 동기화 완료"
}

# 명령어 인수 처리
case "$1" in
    "files")
        sync_files
        ;;
    "dirs")
        sync_directories
        ;;
    "restart")
        restart_windows_server
        ;;
    "test")
        test_connection
        ;;
    *)
        main
        ;;
esac 