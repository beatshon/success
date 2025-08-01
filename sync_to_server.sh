#!/bin/bash

# 윈도우 서버 동기화 스크립트
# 사용법: ./sync_to_server.sh

# 설정
LOCAL_DIR="/Users/jaceson/kiwoom_trading"
REMOTE_USER="Administrator"
REMOTE_HOST="your-windows-server-ip"
REMOTE_DIR="C:/kiwoom_trading"

# 제외할 파일들
EXCLUDE_FILES=(
    "venv/"
    "logs/"
    "__pycache__/"
    "*.pyc"
    ".git/"
    "*.log"
    "data/"
)

# rsync 옵션
RSYNC_OPTS="-avz --delete --exclude-from=-"

echo "🔄 윈도우 서버로 파일 동기화 시작..."

# 제외 파일 목록 생성
for file in "${EXCLUDE_FILES[@]}"; do
    echo "$file"
done | rsync $RSYNC_OPTS "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

if [ $? -eq 0 ]; then
    echo "✅ 동기화 완료!"
else
    echo "❌ 동기화 실패!"
    exit 1
fi 