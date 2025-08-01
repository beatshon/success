#!/bin/bash

# 하이브리드 자동매매 시스템 시작 스크립트
# 맥에서 시뮬레이션하고 Windows 서버에 반영하여 QA 후 제어

echo "🚀 하이브리드 자동매매 시스템 시작"
echo "=================================="

# Python 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "📦 가상환경 활성화..."
    source venv/bin/activate
fi

# 로그 디렉토리 생성
echo "📁 로그 디렉토리 생성..."
mkdir -p logs

# 설정 디렉토리 생성
echo "⚙️ 설정 디렉토리 생성..."
mkdir -p config

# 필요한 패키지 설치 확인
echo "🔍 패키지 설치 확인..."
python -c "import requests, loguru" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 필요한 패키지 설치 중..."
    pip install requests loguru flask flask-cors
fi

# 하이브리드 시스템 상태 확인
echo "🔍 하이브리드 시스템 상태 확인..."
python mac_hybrid_controller.py --action status

echo ""
echo "사용 가능한 명령어:"
echo "  python mac_hybrid_controller.py --action qa                    # QA 프로세스 실행"
echo "  python mac_hybrid_controller.py --action simulation            # 맥 시뮬레이션만 실행"
echo "  python mac_hybrid_controller.py --action sync                  # Windows 동기화만 실행"
echo "  python mac_hybrid_controller.py --action start-windows         # Windows 실제 거래 시작"
echo "  python mac_hybrid_controller.py --action stop-windows          # Windows 실제 거래 중지"
echo "  python mac_hybrid_controller.py --action status                # 상태 확인"
echo ""
echo "전략 설정 예시:"
echo "  python mac_hybrid_controller.py --action qa --strategy moving_average"
echo "  python mac_hybrid_controller.py --action qa --strategy rsi"
echo "  python mac_hybrid_controller.py --action qa --strategy bollinger"
echo ""

# QA 프로세스 자동 실행 여부 확인
read -p "QA 프로세스를 자동으로 실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 QA 프로세스 시작..."
    python mac_hybrid_controller.py --action qa
else
    echo "✅ 하이브리드 시스템 준비 완료"
    echo "위의 명령어를 사용하여 원하는 작업을 실행하세요."
fi 