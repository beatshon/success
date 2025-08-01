# 🚀 실시간 데이터 처리 최적화 가이드

## 📋 개요

키움 API의 실시간 데이터 처리 시스템이 대폭 최적화되었습니다. 이제 더 빠르고 안정적인 실시간 데이터 처리가 가능합니다.

## ✨ 주요 최적화 사항

### 1. 데이터 캐싱 시스템
- **메모리 캐시**: 최신 데이터를 메모리에 캐싱하여 빠른 접근
- **TTL (Time To Live)**: 캐시 유효시간 설정으로 데이터 신선도 보장
- **자동 정리**: 만료된 캐시 자동 정리

### 2. 배치 처리 시스템
- **콜백 큐**: 실시간 콜백을 큐에 저장하여 배치 처리
- **배치 크기 조정**: 처리할 데이터 양을 조정 가능
- **배치 간격 조정**: 처리 주기를 조정 가능

### 3. 데이터 검증 및 통계
- **데이터 유효성 검증**: 잘못된 데이터 필터링
- **급격한 변화 감지**: 비정상적인 가격 변화 감지
- **성능 통계**: 처리 속도, 에러율 등 모니터링

### 4. 메모리 최적화
- **히스토리 제한**: 최근 N개 데이터만 보관
- **자동 정리**: 사용하지 않는 데이터 자동 정리
- **스레드 안전**: 멀티스레드 환경에서 안전한 데이터 접근

## 🚀 사용법

### 기본 설정

```python
from kiwoom_api import KiwoomAPI, RealDataType

# API 인스턴스 생성
kiwoom = KiwoomAPI()

# 로그인
if kiwoom.login():
    # 실시간 데이터 설정
    kiwoom.set_real_data_config(
        enable_caching=True,
        cache_ttl=1.0,
        batch_size=10,
        batch_interval=0.1
    )
```

### 1. 실시간 데이터 구독

```python
# 기본 구독
result = kiwoom.subscribe_real_data("005930")  # 삼성전자

# 상세 설정으로 구독
result = kiwoom.subscribe_real_data(
    code="005930",
    real_type="주식체결",
    fid_list="10;15;12;13;16;17;18;20"
)

if result:
    print("구독 성공")
else:
    print("구독 실패")
```

### 2. 실시간 데이터 콜백 처리

```python
def on_real_data(code, data):
    """실시간 데이터 콜백"""
    print(f"종목: {code}")
    print(f"현재가: {data['current_price']:,}원")
    print(f"거래량: {data['volume']:,}주")
    print(f"등락률: {data['change_rate']:+.2f}%")
    print(f"시가: {data['open_price']:,}원")
    print(f"고가: {data['high_price']:,}원")
    print(f"저가: {data['low_price']:,}원")

kiwoom.set_real_data_callback(on_real_data)
```

### 3. 캐시 데이터 조회

```python
# 특정 종목 캐시 조회
cache_data = kiwoom.get_real_data_cache("005930")
if cache_data:
    print(f"캐시된 현재가: {cache_data['current_price']:,}원")

# 전체 캐시 조회
all_cache = kiwoom.get_real_data_cache()
print(f"캐시된 종목 수: {len(all_cache)}")
```

### 4. 히스토리 데이터 조회

```python
# 최근 100개 데이터 조회
history = kiwoom.get_real_data_history("005930", limit=100)

for data in history[-5:]:  # 최근 5개만 출력
    print(f"{data['timestamp']}: {data['current_price']:,}원")

# 전체 히스토리 조회
full_history = kiwoom.get_real_data_history("005930", limit=0)
print(f"전체 히스토리: {len(full_history)}건")
```

### 5. 성능 통계 조회

```python
# 특정 종목 통계
stats = kiwoom.get_real_data_stats("005930")
print(f"업데이트 횟수: {stats['update_count']}")
print(f"에러 횟수: {stats['error_count']}")
print(f"평균 처리시간: {stats['avg_processing_time']:.4f}초")

# 전체 통계
all_stats = kiwoom.get_real_data_stats()
for code, stat in all_stats.items():
    print(f"{code}: {stat['update_count']}건 처리")
```

### 6. 설정 변경

```python
# 실시간 데이터 설정 변경
kiwoom.set_real_data_config(
    enable_caching=True,      # 캐싱 활성화
    cache_ttl=2.0,           # 캐시 유효시간 2초
    max_history_size=500,    # 히스토리 최대 500개
    enable_stats=True,       # 통계 활성화
    batch_processing=True,   # 배치 처리 활성화
    batch_size=20,          # 배치 크기 20
    batch_interval=0.05     # 배치 간격 0.05초
)
```

### 7. 데이터 정리

```python
# 특정 종목 캐시 정리
kiwoom.clear_real_data_cache("005930")

# 전체 캐시 정리
kiwoom.clear_real_data_cache()

# 구독 해제
kiwoom.unsubscribe_real_data("005930")
```

## 📊 실시간 데이터 타입

### RealDataType Enum
```python
class RealDataType(Enum):
    STOCK_TICK = "주식체결"      # 주식 체결 데이터
    STOCK_ORDER = "주식주문체결"  # 주식 주문 체결
    STOCK_TRADE = "주식체결통보"  # 주식 체결 통보
    INDEX = "지수"              # 지수 데이터
    FUTURES = "선물"            # 선물 데이터
    OPTION = "옵션"             # 옵션 데이터
```

## 🔧 설정 옵션

### real_data_config 설정
```python
{
    'enable_caching': True,        # 캐싱 활성화
    'cache_ttl': 1.0,             # 캐시 유효시간 (초)
    'max_history_size': 1000,     # 히스토리 최대 크기
    'enable_stats': True,         # 통계 활성화
    'batch_processing': True,     # 배치 처리 활성화
    'batch_size': 10,            # 배치 크기
    'batch_interval': 0.1        # 배치 간격 (초)
}
```

## 📈 성능 최적화 팁

### 1. 배치 크기 조정
```python
# 고성능 설정 (빠른 처리)
kiwoom.set_real_data_config(
    batch_size=50,
    batch_interval=0.02
)

# 안정성 설정 (안정적인 처리)
kiwoom.set_real_data_config(
    batch_size=5,
    batch_interval=0.2
)
```

### 2. 캐시 TTL 조정
```python
# 실시간성 중시
kiwoom.set_real_data_config(cache_ttl=0.5)

# 안정성 중시
kiwoom.set_real_data_config(cache_ttl=2.0)
```

### 3. 히스토리 크기 조정
```python
# 메모리 절약
kiwoom.set_real_data_config(max_history_size=100)

# 데이터 보존
kiwoom.set_real_data_config(max_history_size=5000)
```

## 🧪 테스트

```bash
# 실시간 데이터 최적화 테스트 실행
python test_real_data_optimization.py
```

테스트 파일에서는 다음 기능들을 검증합니다:
- 설정 테스트
- 구독/해제 테스트
- 캐시 기능 테스트
- 히스토리 기능 테스트
- 통계 기능 테스트
- 성능 테스트
- 배치 처리 테스트
- 스트레스 테스트

## 📝 로그 확인

실시간 데이터 관련 로그는 다음 파일에서 확인할 수 있습니다:
- `logs/real_data_test.log`: 테스트 로그
- `logs/github_sync.log`: 시스템 로그

## ⚠️ 주의사항

1. **메모리 사용량**: 많은 종목을 구독할 때 메모리 사용량을 모니터링하세요.

2. **배치 크기**: 너무 큰 배치 크기는 지연을, 너무 작은 배치 크기는 오버헤드를 발생시킬 수 있습니다.

3. **캐시 TTL**: 너무 짧은 TTL은 캐시 효과를, 너무 긴 TTL은 데이터 신선도를 떨어뜨릴 수 있습니다.

4. **에러 처리**: 콜백 함수에서 예외가 발생하면 전체 배치 처리가 중단될 수 있습니다.

## 🔄 다음 단계

실시간 데이터 처리 최적화가 완성되었으니, 다음 중 선택하여 진행하세요:

1. **C) 거래 전략 연동 인터페이스** - 자동매매 전략과 연동하는 시스템
2. **D) 전체적인 에러 처리 및 안정성 개선** - 시스템 안정성 강화

어떤 부분을 개선하고 싶으신가요? 