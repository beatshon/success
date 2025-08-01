# 📰 뉴스 수집 및 종목 매칭 분석 시스템

네이버 뉴스 API를 이용해서 뉴스를 수집하고 당일 투자종목을 매칭하는 시스템입니다.

## 🚀 주요 기능

### 📰 뉴스 수집
- **네이버 뉴스 API**를 통한 실시간 뉴스 수집
- **키워드 기반** 뉴스 검색 및 필터링
- **중복 제거** 및 데이터 정리

### 📊 종목 매칭
- **자동 종목 매칭**: 뉴스 내용에서 관련 종목 자동 추출
- **키워드 매핑**: 종목명과 관련 키워드 매칭
- **다중 종목 지원**: 하나의 뉴스가 여러 종목과 연관될 수 있음

### 📈 투자 분석
- **감정 분석**: 뉴스의 긍정/부정/중립 감정 분석
- **투자 점수**: 종목별 종합 투자 점수 계산
- **위험도 평가**: 리스크 키워드 기반 위험도 평가
- **투자 추천**: 점수와 위험도를 종합한 투자 추천

## 📋 시스템 구성

### 핵심 모듈
- `news_collector.py`: 네이버 뉴스 수집기
- `stock_news_analyzer.py`: 뉴스 분석 및 종목 매칭
- `run_news_analysis.py`: 통합 실행 스크립트

### 설정 파일
- `config/news_config.json`: 시스템 설정
- `config/naver_api_keys.py`: 네이버 API 키 (별도 생성)

### 출력 파일
- `data/news_analysis/`: 분석 결과 저장 디렉토리
- `logs/`: 로그 파일 저장 디렉토리

## 🛠️ 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install requests pandas numpy loguru
```

### 2. 네이버 API 키 발급
1. **네이버 개발자 센터** 방문: https://developers.naver.com/
2. **애플리케이션 등록**
3. **검색 API** 서비스 추가
4. **Client ID**와 **Client Secret** 발급

### 3. 설정 파일 수정
```bash
# config/news_config.json 파일 수정
{
  "naver_api": {
    "client_id": "실제_네이버_클라이언트_ID",
    "client_secret": "실제_네이버_클라이언트_시크릿"
  }
}
```

## 🎯 사용 방법

### 기본 실행
```bash
# 전체 분석 실행
python run_news_analysis.py

# 특정 키워드로 분석
python run_news_analysis.py --keywords 삼성전자 SK하이닉스 네이버

# 테스트 모드 실행
python run_news_analysis.py --test
```

### 단계별 실행
```python
from news_collector import NaverNewsCollector
from stock_news_analyzer import StockNewsAnalyzer

# 1. 뉴스 수집
collector = NaverNewsCollector("your_client_id", "your_client_secret")
news_items = collector.collect_daily_news()

# 2. 뉴스 분석
analyzer = StockNewsAnalyzer()
stock_analysis = analyzer.analyze_stock_news(news_items)

# 3. 결과 확인
top_stocks = analyzer.get_top_stocks(stock_analysis, 5)
for stock in top_stocks:
    print(f"{stock.stock_name}: {stock.investment_score:.1f}점")
```

## 📊 분석 결과

### 투자 점수 계산
- **뉴스 양 점수** (0-30점): 수집된 뉴스 개수
- **긍정/부정 비율 점수** (0-40점): 긍정 뉴스 비율
- **감정 점수** (0-30점): 평균 감정 점수

### 위험도 평가
- **Low**: 위험 키워드 비율 < 10%
- **Medium**: 위험 키워드 비율 10-30%
- **High**: 위험 키워드 비율 > 30%

### 투자 추천
- **강력 매수**: 높은 점수 + 낮은 위험도
- **매수**: 높은 점수 + 중간 위험도
- **신중 매수**: 높은 점수 + 높은 위험도
- **관망**: 중간 점수
- **매도**: 낮은 점수

## 📁 출력 파일

### CSV 파일
- `news_YYYYMMDD.csv`: 수집된 뉴스 데이터
- `stock_analysis_YYYYMMDD.csv`: 종목별 분석 결과

### 리포트 파일
- `stock_analysis_report_YYYYMMDD.txt`: 상세 분석 리포트

### 로그 파일
- `logs/news_analysis_YYYYMMDD.log`: 실행 로그

## 🔧 고급 설정

### 키워드 추가
```json
{
  "keywords": [
    "기존_키워드",
    "새로운_키워드"
  ]
}
```

### 종목 매핑 추가
```python
# news_collector.py의 _load_stock_keywords 메서드 수정
stock_keywords = {
    "종목코드": ["종목명", "관련키워드1", "관련키워드2"]
}
```

### 감정 분석 키워드 수정
```python
# stock_news_analyzer.py의 키워드 리스트 수정
positive_keywords = ["긍정키워드1", "긍정키워드2"]
negative_keywords = ["부정키워드1", "부정키워드2"]
```

## ⚠️ 주의사항

### API 사용 제한
- **네이버 API**: 일일 25,000회 호출 제한
- **키워드 수**: 너무 많은 키워드 사용 시 제한 도달 가능
- **호출 간격**: 0.1초 간격으로 제한하여 안정성 확보

### 데이터 품질
- **뉴스 중복**: 제목 기준으로 중복 제거
- **HTML 태그**: 자동으로 제거하여 텍스트 정리
- **키워드 매칭**: 대소문자 구분 없이 매칭

### 투자 위험 고지
- **참고 자료**: 이 시스템은 투자 참고 자료일 뿐입니다
- **투자 책임**: 실제 투자는 본인의 판단과 책임 하에 진행
- **시장 변동**: 뉴스 분석 결과가 주가에 직접 반영되지 않을 수 있음

## 🆘 문제 해결

### API 오류
```
❌ 네이버 API 키가 설정되지 않았습니다.
```
**해결**: `config/news_config.json`에서 API 키 설정

### 뉴스 수집 실패
```
❌ 뉴스 수집에 실패했습니다.
```
**해결**: 
1. 인터넷 연결 확인
2. API 키 유효성 확인
3. API 호출 제한 확인

### 분석 오류
```
❌ 뉴스 분석에 실패했습니다.
```
**해결**:
1. 수집된 뉴스 데이터 확인
2. 종목 매핑 데이터 확인
3. 로그 파일 확인

## 📞 지원

### 추가 기능 요청
- GitHub Issues를 통해 기능 요청
- 코드 기여 환영

### 기술 지원
- 로그 파일 확인: `logs/news_analysis_YYYYMMDD.log`
- 설정 파일 확인: `config/news_config.json`
- 네이버 API 문서: https://developers.naver.com/docs/search/

---

**이 시스템을 통해 뉴스 기반의 데이터 주도 투자 분석을 수행할 수 있습니다!** 🚀 