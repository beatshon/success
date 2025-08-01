#!/bin/bash

echo "========================================"
echo "맥용 예수금 조회 시뮬레이션 테스트"
echo "========================================"
echo

echo "현재 시간: $(date)"
echo

# Python 환경 확인
echo "🔍 Python 환경 확인 중..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3이 설치되지 않았습니다."
    exit 1
fi

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "🔄 가상환경 활성화 중..."
    source venv/bin/activate
fi

# 필요한 패키지 설치 확인
echo "📦 패키지 설치 확인 중..."
pip install -r requirements.txt

# 로그 디렉토리 생성
mkdir -p logs

echo
echo "🚀 맥용 예수금 조회 시뮬레이션 테스트 시작..."
echo
echo "⚠️ 주의사항:"
echo "이 테스트는 시뮬레이션된 데이터를 사용합니다."
echo "실제 키움 API는 Windows에서만 작동합니다."
echo

# 맥용 테스트 실행
python3 mac_deposit_test.py

if [ $? -eq 0 ]; then
    echo
    echo "✅ 맥용 예수금 조회 시뮬레이션 테스트가 성공적으로 완료되었습니다!"
    echo
    echo "이제 Windows 서버에서 실제 키움 API를 테스트할 수 있습니다."
    echo
else
    echo
    echo "❌ 맥용 예수금 조회 시뮬레이션 테스트 중 오류가 발생했습니다."
    echo
    echo "문제 해결 방법:"
    echo "1. Python3이 설치되어 있는지 확인"
    echo "2. 필요한 패키지가 설치되어 있는지 확인"
    echo "3. 로그 파일을 확인하여 상세 오류 내용 확인"
    echo
fi

echo "테스트 결과를 확인하려면 logs 폴더를 열어주세요."
echo
echo "아무 키나 누르면 종료됩니다..."
read -n 1 