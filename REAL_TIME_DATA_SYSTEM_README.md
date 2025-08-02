# 실시간 데이터 수집 시스템

키움 API 기반 고도화된 실시간 주식 데이터 수집 및 분석 시스템입니다.

## 🚀 주요 기능

### 📊 실시간 데이터 수집
- **멀티스레딩 기반** 고성능 데이터 수집
- **자동 재연결** 및 **에러 복구** 기능
- **데이터 캐싱** 및 **큐 관리** 시스템
- **실시간 종목 구독/해제** 기능

### 📈 데이터 분석
- **시장 추세 분석** (상승/하락/보합 종목 비율)
- **급등/급락 종목 감지**
- **종목 간 상관관계 분석**
- **거래량 및 변동성 분석**

### 🖥️ 웹 대시보드
- **실시간 차트** 및 **통계 표시**
- **반응형 웹 인터페이스**
- **데이터 내보내기** 기능
- **시스템 모니터링** 대시보드

### 🔧 API 서버
- **RESTful API** 제공
- **JSON 기반** 데이터 교환
- **CORS 지원** 크로스 도메인 접근
- **실시간 상태 모니터링**

## 📋 시스템 요구사항

### 필수 소프트웨어
- Python 3.8 이상
- 키움 Open API+ (설치 및 로그인 필요)
- Windows OS (키움 API 제약)

### Python 패키지
```
flask>=2.0.0
flask-cors>=3.0.0
pandas>=1.3.0
numpy>=1.21.0
loguru>=0.6.0
requests>=2.25.0
PyQt5>=5.15.0
```

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd kiwoom_trading
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv real_time_env
source real_time_env/bin/activate  # Windows: real_time_env\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 키움 API 설정
1. 키움 Open API+ 설치 및 로그인
2. `config/kiwoom_config.py` 파일에서 API 설정 확인
3. 키움 API 키 설정 (필요시)

## 🚀 사용법

### 1. 시스템 시작

#### 자동 시작 (권장)
```bash
python start_real_time_data_system.py
```

#### 수동 시작
```bash
# 1. 데이터 수집기만 실행
python real_time_data_collector.py

# 2. API 서버만 실행
python real_time_data_server.py
```

#### 커스텀 설정으로 시작
```bash
# 특정 포트로 시작
python start_real_time_data_system.py --port 8084

# 특정 종목만 구독
python start_real_time_data_system.py --stocks 005930 000660 035420
```

### 2. 웹 대시보드 접속
브라우저에서 다음 URL로 접속:
```
http://localhost:8083
```

### 3. API 사용
```bash
# 시스템 상태 조회
curl http://localhost:8083/api/status

# 데이터 수집 시작
curl -X POST http://localhost:8083/api/start

# 실시간 데이터 조회
curl http://localhost:8083/api/data

# 종목 구독
curl -X POST http://localhost:8083/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"codes": ["005930", "000660"]}'
```

## 📚 API 문서

### 기본 엔드포인트

#### GET /api/status
시스템 상태 조회
```json
{
  "server_running": true,
  "collector_running": true,
  "collector_stats": {
    "data_received": 1250,
    "data_processed": 1250,
    "errors": 0,
    "subscribed_count": 20,
    "queue_size": 0
  },
  "timestamp": "2025-08-02T16:30:00"
}
```

#### POST /api/start
데이터 수집 시작
```json
{
  "status": "started",
  "message": "데이터 수집이 시작되었습니다"
}
```

#### POST /api/stop
데이터 수집 중지
```json
{
  "status": "stopped",
  "message": "데이터 수집이 중지되었습니다"
}
```

#### GET /api/data
모든 실시간 데이터 조회
```json
{
  "data": [
    {
      "code": "005930",
      "name": "삼성전자",
      "current_price": 75000,
      "change_rate": 2.5,
      "volume": 15000000,
      "amount": 1125000000000,
      "open_price": 73500,
      "high_price": 75500,
      "low_price": 73000,
      "prev_close": 73200,
      "timestamp": "2025-08-02T16:30:00",
      "data_type": "stock_tick"
    }
  ],
  "count": 20,
  "timestamp": "2025-08-02T16:30:00"
}
```

#### GET /api/data/{code}
특정 종목 데이터 조회
```json
{
  "code": "005930",
  "name": "삼성전자",
  "current_price": 75000,
  "change_rate": 2.5,
  "volume": 15000000,
  "amount": 1125000000000,
  "open_price": 73500,
  "high_price": 75500,
  "low_price": 73000,
  "prev_close": 73200,
  "timestamp": "2025-08-02T16:30:00",
  "data_type": "stock_tick"
}
```

#### POST /api/subscribe
종목 구독
```json
{
  "codes": ["005930", "000660", "035420"]
}
```

#### POST /api/unsubscribe
종목 구독 해제
```json
{
  "codes": ["005930"]
}
```

### 분석 엔드포인트

#### GET /api/analysis/market-trend
시장 추세 분석
```json
{
  "analysis": {
    "up_count": 12,
    "down_count": 6,
    "flat_count": 2,
    "avg_change_rate": 1.25,
    "total_volume": 150000000,
    "avg_volume": 7500000,
    "market_sentiment": "bullish"
  },
  "timestamp": "2025-08-02T16:30:00"
}
```

#### GET /api/analysis/hot-stocks?min_change_rate=3.0
급등/급락 종목 조회
```json
{
  "hot_stocks": [
    {
      "code": "005930",
      "name": "삼성전자",
      "change_rate": 5.2,
      "current_price": 75000,
      "volume": 15000000,
      "type": "up"
    }
  ],
  "count": 3,
  "min_change_rate": 3.0,
  "timestamp": "2025-08-02T16:30:00"
}
```

#### GET /api/analysis/correlation?codes=005930,000660,035420
종목 간 상관관계 분석
```json
{
  "correlation": {
    "005930": {
      "005930": 1.0,
      "000660": 0.85,
      "035420": 0.32
    }
  },
  "codes": ["005930", "000660", "035420"],
  "timestamp": "2025-08-02T16:30:00"
}
```

### 유틸리티 엔드포인트

#### GET /api/export?format=csv
데이터 내보내기
```json
{
  "status": "exported",
  "filename": "real_time_data_20250802_163000.csv",
  "format": "csv",
  "timestamp": "2025-08-02T16:30:00"
}
```

#### GET /api/stats
상세 통계 조회
```json
{
  "collector_stats": {
    "data_received": 1250,
    "data_processed": 1250,
    "errors": 0,
    "start_time": "2025-08-02T16:00:00",
    "last_update": "2025-08-02T16:30:00",
    "subscribed_count": 20,
    "queue_size": 0,
    "cache_stats": {
      "size": 20,
      "max_size": 1000,
      "hit_rate": 0,
      "ttl": 300
    },
    "running": true
  },
  "server_stats": {
    "server_running": true,
    "uptime": "0:30:00",
    "timestamp": "2025-08-02T16:30:00"
  }
}
```

## 🧪 테스트

### 전체 시스템 테스트
```bash
python test_real_time_data.py
```

### 개별 기능 테스트
```bash
# API 연결 테스트
python test_real_time_data.py --test connection

# 데이터 수집 테스트
python test_real_time_data.py --test collection

# 시장 분석 테스트
python test_real_time_data.py --test analysis

# 성능 모니터링 테스트
python test_real_time_data.py --test performance
```

### 커스텀 URL 테스트
```bash
python test_real_time_data.py --url http://localhost:8084
```

## 🔧 설정

### 데이터 수집 설정
`real_time_data_collector.py`의 `DataCollectionConfig` 클래스에서 설정 가능:

```python
config = DataCollectionConfig(
    update_interval=1.0,        # 업데이트 간격 (초)
    max_queue_size=10000,       # 최대 큐 크기
    cache_duration=300,         # 캐시 유지 시간 (초)
    retry_attempts=3,           # 재시도 횟수
    retry_delay=1.0,            # 재시도 간격 (초)
    enable_compression=True,    # 압축 사용
    enable_caching=True,        # 캐싱 사용
    enable_monitoring=True      # 모니터링 사용
)
```

### 서버 설정
`real_time_data_server.py`에서 포트 및 기타 설정 변경 가능:

```python
server = RealTimeDataServer(port=8083)
```

## 📊 성능 최적화

### 1. 메모리 사용량 최적화
- 캐시 크기 조정 (`max_size` 파라미터)
- 큐 크기 제한 (`max_queue_size` 파라미터)
- TTL 설정으로 오래된 데이터 자동 삭제

### 2. CPU 사용량 최적화
- 업데이트 간격 조정 (`update_interval` 파라미터)
- 불필요한 분석 기능 비활성화
- 멀티스레딩 활용

### 3. 네트워크 최적화
- 데이터 압축 사용 (`enable_compression=True`)
- 배치 처리로 API 호출 최소화
- 연결 풀링 활용

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. 키움 API 연결 실패
```
❌ 키움 API 컨트롤 초기화 실패
```
**해결방법:**
- 키움 Open API+ 재설치
- 키움 증권 로그인 확인
- 관리자 권한으로 실행

#### 2. 포트 충돌
```
❌ Address already in use
```
**해결방법:**
```bash
# 다른 포트 사용
python start_real_time_data_system.py --port 8084

# 또는 기존 프로세스 종료
netstat -ano | findstr :8083
taskkill /PID <process_id>
```

#### 3. 데이터 수집 안됨
```
❌ 데이터가 없습니다
```
**해결방법:**
- 키움 API 로그인 상태 확인
- 종목 구독 상태 확인
- 거래 시간 확인 (장 시간: 09:00-15:30)

#### 4. 메모리 부족
```
❌ MemoryError
```
**해결방법:**
- 캐시 크기 줄이기
- 큐 크기 줄이기
- 구독 종목 수 줄이기

### 로그 확인
```bash
# 실시간 로그 확인
tail -f logs/real_time_data.log

# 에러 로그만 확인
grep "ERROR" logs/real_time_data.log
```

### 디버그 모드
```python
# 디버그 로그 활성화
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 모니터링

### 시스템 상태 모니터링
- 웹 대시보드에서 실시간 상태 확인
- API `/api/stats` 엔드포인트로 상세 통계 조회
- 로그 파일에서 에러 및 성능 지표 확인

### 성능 지표
- **데이터 수신률**: 초당 수신 데이터 수
- **처리 지연시간**: 데이터 수신부터 처리까지 시간
- **에러율**: 전체 요청 대비 에러 비율
- **메모리 사용량**: 캐시 및 큐 사용량

### 알림 설정
```python
# 커스텀 알림 콜백 등록
def alert_callback(data, processed_data):
    if processed_data.get('price_alert', {}).get('alerts'):
        # 이메일, 슬랙 등으로 알림 전송
        pass

collector.add_callback('data_processed', alert_callback)
```

## 🔒 보안

### API 보안
- CORS 설정으로 허용된 도메인만 접근
- 요청 제한 (Rate Limiting) 구현 권장
- API 키 인증 추가 권장

### 데이터 보안
- 민감한 데이터 암호화
- 로그 파일 접근 제한
- 네트워크 보안 설정

## 🤝 기여

### 개발 환경 설정
1. 저장소 포크
2. 개발 브랜치 생성
3. 코드 수정 및 테스트
4. Pull Request 생성

### 코드 스타일
- PEP 8 준수
- Type hints 사용
- Docstring 작성
- 에러 처리 구현

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

### 이슈 리포트
GitHub Issues를 통해 버그 리포트 및 기능 요청을 해주세요.

### 문의사항
- 이메일: [your-email@example.com]
- GitHub: [your-github-profile]

---

**⚠️ 주의사항:**
- 이 시스템은 교육 및 연구 목적으로 제작되었습니다.
- 실제 투자에 사용하기 전에 충분한 테스트가 필요합니다.
- 키움 API 사용 시 키움증권의 이용약관을 준수해주세요. 