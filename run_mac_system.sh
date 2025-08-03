#!/bin/bash
# 맥 전용 실행 스크립트

echo "🍎 맥 전용 투자 시스템 시작"
echo "================================"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "가상환경이 없습니다. 새로 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask flask-cors requests pandas numpy loguru
fi

# 서버 시작
echo "실시간 데이터 서버 시작 중..."
python mac_real_time_server.py
