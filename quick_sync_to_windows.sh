#!/bin/bash

# 맥에서 윈도우 서버로 빠른 동기화 스크립트
# 주요 파일들만 빠르게 동기화

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}맥에서 윈도우 서버로 빠른 동기화 시작${NC}"

# 설정 파일 로드
if [ -f "config/windows_server.conf" ]; then
    source config/windows_server.conf
else
    echo -e "${RED}설정 파일을 찾을 수 없습니다: config/windows_server.conf${NC}"
    exit 1
fi

# 필수 변수 확인
if [ -z "$WINDOWS_HOST" ] || [ -z "$WINDOWS_USER" ] || [ -z "$WINDOWS_PATH" ]; then
    echo -e "${RED}설정 파일에 필수 정보가 누락되었습니다.${NC}"
    exit 1
fi

echo "윈도우 서버: $WINDOWS_HOST"
echo "사용자: $WINDOWS_USER"
echo "경로: $WINDOWS_PATH"
echo

# SSH 연결 테스트
echo "SSH 연결 테스트 중..."
if ssh -p $SSH_PORT -o ConnectTimeout=5 $WINDOWS_USER@$WINDOWS_HOST "echo '연결 성공'" 2>/dev/null; then
    echo -e "${GREEN}SSH 연결 성공${NC}"
else
    echo -e "${RED}SSH 연결 실패${NC}"
    exit 1
fi

# 주요 파일들만 빠르게 동기화
echo "주요 파일들 동기화 중..."

# Python 파일들
echo "1. Python 파일들..."
scp -P $SSH_PORT *.py $WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/

# 설정 파일들
echo "2. 설정 파일들..."
scp -P $SSH_PORT -r config/ $WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/

# 요구사항 파일들
echo "3. 요구사항 파일들..."
scp -P $SSH_PORT requirements*.txt $WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/

# 실행 스크립트들
echo "4. 실행 스크립트들..."
scp -P $SSH_PORT *.bat *.sh $WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/

# 템플릿 파일들
if [ -d "templates" ]; then
    echo "5. 템플릿 파일들..."
    scp -P $SSH_PORT -r templates/ $WINDOWS_USER@$WINDOWS_HOST:$WINDOWS_PATH/
fi

echo -e "${GREEN}빠른 동기화 완료!${NC}"
echo
echo "다음 단계:"
echo "1. 윈도우 서버에 접속"
echo "2. cd $WINDOWS_PATH"
echo "3. ./start_windows_api_server.bat"
echo "4. ./run_windows_api_test.bat" 