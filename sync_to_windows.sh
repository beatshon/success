#!/bin/bash

# 맥에서 윈도우 서버로 키움 트레이딩 시스템 동기화 스크립트

echo "🔄 키움 트레이딩 시스템 동기화 시작"
echo "=================================="

# 설정
WINDOWS_SERVER="your_windows_server_ip"  # 윈도우 서버 IP 주소
WINDOWS_USER="your_windows_username"     # 윈도우 사용자명
WINDOWS_PATH="/path/to/kiwoom_trading"   # 윈도우 서버의 프로젝트 경로

# 동기화할 파일 목록 (키움 시스템 안정화 파일들 추가)
FILES_TO_SYNC=(
    # 기존 뉴스 분석 파일들
    "news_collector.py"
    "stock_news_analyzer.py"
    "run_news_analysis.py"
    "config/news_config.json"
    "NEWS_ANALYSIS_README.md"
    "requirements.txt"
    
    # 새로 추가된 키움 시스템 안정화 파일들
    "kiwoom_mac_compatible.py"
    "windows_kiwoom_server.py"
    "integrated_auto_trader.py"
    "kiwoom_stabilization_plan.md"
    "naver_trend_enhancement_plan.md"
    "simple_naver_server.py"
    
    # 기존 키움 관련 파일들
    "kiwoom_api.py"
    "auto_trader.py"
    "trading_strategy.py"
    "error_handler.py"
    "system_monitor.py"
    
    # 네이버 트렌드 분석 파일들
    "naver_trend_analyzer.py"
    "naver_trend_server.py"
    "templates/naver_trend_dashboard.html"
    
    # 대시보드 파일들
    "integrated_dashboard.py"
    "hybrid_dashboard.py"
    "simulation_dashboard.py"
    "templates/integrated_dashboard.html"
    "templates/hybrid_dashboard.html"
    "templates/simulation_dashboard.html"
)

# 디렉토리 생성
echo "📁 윈도우 서버에 디렉토리 생성 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/config"
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/data/news_analysis"
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/logs"
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/templates"

# 파일 동기화
echo "📤 파일 동기화 중..."
for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$file" ]; then
        echo "  동기화: $file"
        scp "$file" "${WINDOWS_USER}@${WINDOWS_SERVER}:${WINDOWS_PATH}/$file"
    else
        echo "  ⚠️  파일 없음: $file"
    fi
done

# requirements.txt 업데이트 (키움 시스템용)
echo "📦 requirements.txt 업데이트 중..."
cat > requirements_kiwoom.txt << EOF
requests>=2.25.1
pandas>=1.3.0
numpy>=1.21.0
loguru>=0.6.0
flask>=2.0.0
flask-cors>=3.0.10
PyQt5>=5.15.0
aiohttp>=3.8.0
websockets>=10.0
EOF

scp requirements_kiwoom.txt "${WINDOWS_USER}@${WINDOWS_SERVER}:${WINDOWS_PATH}/requirements_kiwoom.txt"

# 윈도우 서버에서 패키지 설치
echo "🔧 윈도우 서버에서 패키지 설치 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && pip install -r requirements_kiwoom.txt"

# 실행 권한 설정
echo "🔐 실행 권한 설정 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && chmod +x *.py"

# 키움 API 서버 테스트
echo "🧪 키움 API 서버 테스트 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && python windows_kiwoom_server.py --test"

# 통합 자동매매 시스템 테스트
echo "🧪 통합 자동매매 시스템 테스트 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && python integrated_auto_trader.py --test"

echo "✅ 동기화 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 윈도우 서버에서 키움 API 설정 확인"
echo "2. config/kiwoom_config.json 파일 수정"
echo "3. python windows_kiwoom_server.py 실행 (키움 API 서버)"
echo "4. python integrated_auto_trader.py 실행 (자동매매 시스템)"
echo ""
echo "🔧 키움 시스템 안정화 체크리스트:"
echo "- [ ] 키움 Open API+ 설치 확인"
echo "- [ ] PyQt5 설치 확인"
echo "- [ ] 키움 계정 로그인 테스트"
echo "- [ ] 실시간 데이터 수신 테스트"
echo "- [ ] 주문 전송 테스트"
echo ""
echo "📞 문제 발생 시:"
echo "- 키움 API 서버 로그 확인: logs/kiwoom_server_YYYYMMDD.log"
echo "- 자동매매 시스템 로그 확인: logs/auto_trader_YYYYMMDD.log"
echo "- 설정 파일 확인: config/kiwoom_config.json"
echo ""
echo "🚀 월요일 모의투자 준비:"
echo "1. 윈도우 서버에서 키움 API 서버 시작"
echo "2. Mac에서 kiwoom_mac_compatible.py로 연결"
echo "3. integrated_auto_trader.py로 자동매매 시작" 