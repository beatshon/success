# 📰 뉴스 기반 주식 거래 시스템 완전 가이드

네이버 뉴스 API를 활용하여 뉴스를 수집하고 분석한 결과를 키움 API와 연동하여 자동 주식 거래를 수행하는 통합 시스템입니다.

## 🚀 시스템 개요

### 주요 기능
- **📰 실시간 뉴스 수집**: 네이버 뉴스 API를 통한 키워드 기반 뉴스 수집
- **📊 뉴스 분석**: 감정 분석, 종목 매칭, 투자 점수 계산
- **💰 자동 거래**: 키움 API 연동을 통한 자동 매수/매도
- **📈 실시간 모니터링**: 웹 대시보드를 통한 실시간 모니터링
- **⚠️ 위험 관리**: 리스크 평가 및 알림 시스템

### 시스템 구성
```
kiwoom_trading/
├── 📰 뉴스 수집 및 분석
│   ├── news_collector.py          # 네이버 뉴스 수집기
│   ├── stock_news_analyzer.py     # 뉴스 분석기
│   └── run_news_analysis.py       # 뉴스 분석 실행
├── 💰 거래 시스템
│   ├── news_trading_integration.py # 뉴스-거래 통합 시스템
│   └── kiwoom_api.py              # 키움 API 연동
├── 📊 모니터링
│   └── news_monitoring_dashboard.py # 웹 대시보드
├── ⚙️ 설정 및 실행
│   ├── start_news_trading_system.py # 통합 실행 스크립트
│   └── config/                     # 설정 파일들
└── 📁 데이터
    ├── data/news_analysis/         # 뉴스 분석 결과
    ├── data/trading_results/       # 거래 결과
    └── logs/                       # 로그 파일
```

## 🛠️ 설치 및 설정

### 1단계: 환경 설정

#### 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python3 -m venv news_env

# 가상환경 활성화 (Mac/Linux)
source news_env/bin/activate

# 가상환경 활성화 (Windows)
news_env\Scripts\activate
```

#### 필수 패키지 설치
```bash
# 기본 패키지
pip install loguru requests pandas numpy

# 웹 대시보드용 (선택사항)
pip install flask flask-socketio
```

### 2단계: 네이버 API 키 설정

#### API 키 발급
1. **네이버 개발자 센터** 방문: https://developers.naver.com/
2. **애플리케이션 등록**
   - 애플리케이션 이름: `주식뉴스분석시스템`
   - 사용 API: `검색` 선택
   - 웹 서비스 URL: `http://localhost`
3. **Client ID**와 **Client Secret** 발급

#### 설정 파일 수정
```bash
# config/news_config.json 파일 수정
{
  "naver_api": {
    "client_id": "실제_발급받은_클라이언트_ID",
    "client_secret": "실제_발급받은_클라이언트_시크릿"
  }
}
```

### 3단계: 키움 API 설정

#### 키움 Open API+ 설치
1. **키움 Open API+** 다운로드 및 설치
2. **모의투자** 또는 **실투자** 계정 설정
3. **자동 로그인** 설정

#### 키움 API 설정 확인
```bash
# 키움 API 연결 테스트
python test_kiwoom_connection.py
```

## 🎯 사용 방법

### 기본 실행

#### 시스템 상태 확인
```bash
python start_news_trading_system.py --status
```

#### 종합 테스트 실행
```bash
python start_news_trading_system.py --test
```

#### 전체 시스템 실행 (실제 거래)
```bash
python start_news_trading_system.py --full
```

#### 웹 대시보드 실행
```bash
python start_news_trading_system.py --monitor
```

### 단계별 실행

#### 1. 뉴스 분석만 실행
```bash
python run_news_analysis.py --test
```

#### 2. 거래 시스템만 실행
```bash
python news_trading_integration.py --test
```

#### 3. 웹 대시보드만 실행
```bash
python news_monitoring_dashboard.py --create-template
python news_monitoring_dashboard.py
```

## 📊 시스템 동작 과정

### 1. 뉴스 수집 단계
```
키워드 설정 → 네이버 API 호출 → 뉴스 데이터 수집 → 중복 제거 → 데이터 정리
```

### 2. 뉴스 분석 단계
```
뉴스 텍스트 분석 → 종목 매칭 → 감정 분석 → 투자 점수 계산 → 위험도 평가
```

### 3. 거래 신호 생성 단계
```
투자 점수 기반 신호 생성 → 신뢰도 계산 → 목표가/손절가 설정 → 거래 결정
```

### 4. 거래 실행 단계
```
키움 API 연결 → 계좌 정보 확인 → 주문 실행 → 결과 확인 → 로그 저장
```

## 📈 투자 점수 계산 방식

### 점수 구성 (총 100점)
- **뉴스 양 점수** (0-30점): 수집된 뉴스 개수
- **긍정/부정 비율 점수** (0-40점): 긍정 뉴스 비율
- **감정 점수** (0-30점): 평균 감정 점수

### 투자 추천 기준
- **강력 매수**: 80점 이상 + 낮은 위험도
- **매수**: 70점 이상 + 중간 위험도
- **신중 매수**: 60점 이상 + 높은 위험도
- **관망**: 40-60점
- **매도**: 40점 미만

## ⚙️ 고급 설정

### 거래 설정 수정
```json
{
  "trading": {
    "enabled": false,                    // 실제 거래 활성화
    "max_position_per_stock": 1000000,   // 종목당 최대 투자금
    "max_total_position": 5000000,       // 총 최대 투자금
    "min_confidence": 0.7,               // 최소 신뢰도
    "stop_loss_ratio": 0.05,             // 손절 비율 (5%)
    "take_profit_ratio": 0.15,           // 익절 비율 (15%)
    "max_holdings": 5                    // 최대 보유 종목 수
  }
}
```

### 키워드 추가/수정
```json
{
  "analysis": {
    "keywords": [
      "주식", "증시", "코스피", "코스닥", "투자",
      "삼성전자", "SK하이닉스", "네이버", "카카오",
      "LG화학", "현대자동차", "기아", "포스코"
    ]
  }
}
```

### 모니터링 설정
```json
{
  "scheduling": {
    "auto_run": false,                   // 자동 실행
    "run_times": ["09:00", "12:00", "15:00"], // 실행 시간
    "run_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  }
}
```

## 📊 출력 파일 및 결과

### 뉴스 분석 결과
- **CSV 파일**: `data/news_analysis/stock_analysis_YYYYMMDD.csv`
- **리포트**: `data/news_analysis/stock_analysis_report_YYYYMMDD.txt`

### 거래 결과
- **거래 신호**: `data/trading_results/trading_signals_YYYYMMDD_HHMMSS.csv`
- **거래 로그**: `logs/news_trading_YYYYMMDD.log`

### 웹 대시보드
- **URL**: http://localhost:5000
- **실시간 업데이트**: 5분마다 자동 새로고침

## ⚠️ 주의사항 및 위험 고지

### API 사용 제한
- **네이버 API**: 일일 25,000회 호출 제한
- **키움 API**: 계좌별 거래 제한 확인 필요

### 투자 위험 고지
- **참고 자료**: 이 시스템은 투자 참고 자료일 뿐입니다
- **투자 책임**: 실제 투자는 본인의 판단과 책임 하에 진행
- **시장 변동**: 뉴스 분석 결과가 주가에 직접 반영되지 않을 수 있음
- **손실 위험**: 주식 투자는 원금 손실 위험이 있습니다

### 시스템 사용 주의사항
- **테스트 모드**: 처음에는 반드시 테스트 모드로 실행
- **소액 투자**: 실제 거래 시 소액으로 시작
- **정기 모니터링**: 시스템 동작 상태 정기 확인
- **백업**: 중요한 설정 및 데이터 정기 백업

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 네이버 API 오류
```
❌ 네이버 API 키가 설정되지 않았습니다.
```
**해결**: `config/news_config.json`에서 API 키 확인

#### 2. 키움 API 연결 실패
```
❌ 키움 API 연결에 실패했습니다.
```
**해결**: 
1. 키움 Open API+ 설치 확인
2. 자동 로그인 설정 확인
3. 계좌 정보 확인

#### 3. 뉴스 수집 실패
```
❌ 뉴스 수집에 실패했습니다.
```
**해결**:
1. 인터넷 연결 확인
2. API 호출 제한 확인
3. 키워드 수 줄이기

#### 4. 웹 대시보드 오류
```
❌ Flask가 설치되지 않았습니다.
```
**해결**: `pip install flask flask-socketio`

### 로그 확인 방법
```bash
# 최신 로그 확인
tail -f logs/news_trading_$(date +%Y%m%d).log

# 오류 로그만 확인
grep "ERROR" logs/news_trading_$(date +%Y%m%d).log
```

## 📞 지원 및 문의

### 문서 및 가이드
- **네이버 API 문서**: https://developers.naver.com/docs/search/
- **키움 Open API+ 문서**: 키움 Open API+ 설치 시 제공
- **시스템 로그**: `logs/` 디렉토리

### 추가 기능 요청
- GitHub Issues를 통해 기능 요청
- 코드 기여 환영

### 기술 지원
- 로그 파일 확인 후 구체적인 오류 내용과 함께 문의
- 시스템 환경 정보 포함 (OS, Python 버전, 패키지 버전)

---

## 🎉 시작하기

### 빠른 시작 (5분)
1. **환경 설정**: `python3 -m venv news_env && source news_env/bin/activate`
2. **패키지 설치**: `pip install loguru requests pandas numpy`
3. **API 키 설정**: `NAVER_API_SETUP_GUIDE.md` 참고
4. **시스템 테스트**: `python start_news_trading_system.py --test`
5. **웹 대시보드**: `python start_news_trading_system.py --monitor`

### 다음 단계
- **실제 거래**: 테스트 완료 후 `--full` 옵션으로 실제 거래
- **고급 설정**: 거래 파라미터 및 키워드 최적화
- **모니터링**: 실시간 대시보드 및 알림 설정

**이 시스템을 통해 데이터 기반의 스마트한 주식 투자를 시작하세요!** 🚀 