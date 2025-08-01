#!/bin/bash

# 맥에서 윈도우 서버로 뉴스 분석 시스템 동기화 스크립트

echo "🔄 뉴스 분석 시스템 동기화 시작"
echo "=================================="

# 설정
WINDOWS_SERVER="your_windows_server_ip"  # 윈도우 서버 IP 주소
WINDOWS_USER="your_windows_username"     # 윈도우 사용자명
WINDOWS_PATH="/path/to/kiwoom_trading"   # 윈도우 서버의 프로젝트 경로

# 동기화할 파일 목록
FILES_TO_SYNC=(
    "news_collector.py"
    "stock_news_analyzer.py"
    "run_news_analysis.py"
    "config/news_config.json"
    "NEWS_ANALYSIS_README.md"
    "requirements.txt"
)

# 디렉토리 생성
echo "📁 윈도우 서버에 디렉토리 생성 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/config"
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/data/news_analysis"
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "mkdir -p ${WINDOWS_PATH}/logs"

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

# requirements.txt 업데이트
echo "📦 requirements.txt 업데이트 중..."
cat > requirements_news.txt << EOF
requests>=2.25.1
pandas>=1.3.0
numpy>=1.21.0
loguru>=0.6.0
EOF

scp requirements_news.txt "${WINDOWS_USER}@${WINDOWS_SERVER}:${WINDOWS_PATH}/requirements_news.txt"

# 윈도우 서버에서 패키지 설치
echo "🔧 윈도우 서버에서 패키지 설치 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && pip install -r requirements_news.txt"

# 실행 권한 설정
echo "🔐 실행 권한 설정 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && chmod +x *.py"

# 테스트 실행
echo "🧪 윈도우 서버에서 테스트 실행 중..."
ssh ${WINDOWS_USER}@${WINDOWS_SERVER} "cd ${WINDOWS_PATH} && python run_news_analysis.py --test"

echo "✅ 동기화 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 윈도우 서버에서 config/news_config.json 파일 수정"
echo "2. 네이버 API 키 설정"
echo "3. python run_news_analysis.py 실행"
echo ""
echo "📞 문제 발생 시:"
echo "- 윈도우 서버 로그 확인: logs/news_analysis_YYYYMMDD.log"
echo "- 설정 파일 확인: config/news_config.json" 