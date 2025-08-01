# 🔧 키움 API 주문 시스템 가이드

## 📋 개요

키움 API의 주문 시스템이 대폭 개선되었습니다. 이제 더 안전하고 안정적인 주문 기능을 제공합니다.

## ✨ 주요 개선사항

### 1. 주문 타입 및 상태 관리
- **OrderType Enum**: 주문 타입을 명확하게 정의
- **OrderStatus Enum**: 주문 상태를 체계적으로 관리
- **주문 추적**: 대기 중인 주문과 완료된 주문을 분리 관리

### 2. 주문 검증 시스템
- 예수금 부족 검증
- 보유 주식 부족 검증
- 주문 파라미터 유효성 검증
- 계좌 정보 확인

### 3. 재시도 메커니즘
- 주문 실패 시 자동 재시도 (최대 3회)
- 재시도 간격 조정 가능

### 4. 편의 기능
- 매수/매도 전용 메서드
- 시장가 주문 지원
- 주문 정정 기능
- 전체 주문 취소 기능

## 🚀 사용법

### 기본 설정

```python
from kiwoom_api import KiwoomAPI, OrderType, OrderStatus

# API 인스턴스 생성
kiwoom = KiwoomAPI()

# 로그인
if kiwoom.login():
    account_info = kiwoom.get_account_info()
    account = list(account_info.keys())[0]  # 첫 번째 계좌 사용
```

### 1. 주문 검증

```python
# 주문 전 검증
is_valid, message = kiwoom.validate_order(
    account="계좌번호",
    code="종목코드", 
    quantity=1,
    price=50000,
    order_type=OrderType.BUY.value
)

if is_valid:
    print("주문 가능")
else:
    print(f"주문 불가: {message}")
```

### 2. 매수 주문

```python
# 지정가 매수
order_no = kiwoom.buy_stock(
    account="계좌번호",
    code="005930",  # 삼성전자
    quantity=1,     # 1주
    price=50000     # 50,000원
)

# 시장가 매수
order_no = kiwoom.buy_market_order(
    account="계좌번호",
    code="005930",
    quantity=1
)
```

### 3. 매도 주문

```python
# 지정가 매도
order_no = kiwoom.sell_stock(
    account="계좌번호",
    code="005930",
    quantity=1,
    price=55000
)

# 시장가 매도
order_no = kiwoom.sell_market_order(
    account="계좌번호",
    code="005930",
    quantity=1
)
```

### 4. 주문 관리

```python
# 주문 상태 조회
order_status = kiwoom.get_order_status(order_no)

# 대기 중인 주문 조회
pending_orders = kiwoom.get_pending_orders()

# 주문 정정
modify_result = kiwoom.modify_order(
    account="계좌번호",
    order_no=order_no,
    code="005930",
    quantity=1,
    price=49000
)

# 주문 취소
cancel_result = kiwoom.cancel_order(
    account="계좌번호",
    order_no=order_no,
    code="005930",
    quantity=1
)

# 전체 주문 취소
cancelled_count = kiwoom.cancel_all_orders(account)
```

### 5. 콜백 설정

```python
def on_order(order_info):
    """주문 상태 변경 시 호출되는 콜백"""
    print(f"주문 상태: {order_info['status']}")
    print(f"체결 수량: {order_info['filled_quantity']}/{order_info['quantity']}")

kiwoom.set_order_callback(on_order)
```

## 📊 주문 타입 정의

### OrderType Enum
```python
class OrderType(Enum):
    BUY = "신규매수"           # 매수
    SELL = "신규매도"          # 매도
    BUY_CANCEL = "매수취소"    # 매수 취소
    SELL_CANCEL = "매도취소"   # 매도 취소
    BUY_MODIFY = "매수정정"    # 매수 정정
    SELL_MODIFY = "매도정정"   # 매도 정정
```

### OrderStatus Enum
```python
class OrderStatus(Enum):
    PENDING = "접수"           # 주문 접수
    CONFIRMED = "확인"         # 주문 확인
    PARTIAL_FILLED = "부분체결" # 부분 체결
    FILLED = "체결"            # 완전 체결
    CANCELLED = "취소"         # 주문 취소
    REJECTED = "거부"          # 주문 거부
```

## 🔍 주문 검증 항목

### 1. 기본 검증
- 계좌번호 유효성
- 종목코드 유효성
- 주문 수량 > 0
- 주문 가격 > 0

### 2. 매수 주문 검증
- 예수금 충분성 확인
- 필요 금액 = 주문 수량 × 주문 가격

### 3. 매도 주문 검증
- 보유 주식 확인
- 매도 가능 수량 확인

## ⚠️ 주의사항

1. **실제 거래**: 이 시스템은 실제 거래를 수행합니다. 테스트 시에는 소액으로 진행하세요.

2. **예수금 확인**: 매수 전 반드시 예수금을 확인하세요.

3. **주문 상태 모니터링**: 주문 후 상태를 지속적으로 모니터링하세요.

4. **에러 처리**: 주문 실패 시 적절한 에러 처리를 구현하세요.

## 🧪 테스트

```bash
# 주문 시스템 테스트 실행
python test_order_system.py
```

테스트 파일에서는 다음 기능들을 검증합니다:
- 주문 검증
- 매수/매도 주문
- 주문 정정/취소
- 시장가 주문
- 전체 주문 취소

## 📝 로그 확인

주문 관련 로그는 다음 파일에서 확인할 수 있습니다:
- `logs/order_test.log`: 테스트 로그
- `logs/github_sync.log`: 시스템 로그

## 🔄 다음 단계

주문 시스템이 완성되었으니, 다음 중 선택하여 진행하세요:

1. **B) 실시간 데이터 처리 최적화**
2. **C) 거래 전략 연동 인터페이스**
3. **D) 전체적인 에러 처리 및 안정성 개선**

어떤 부분을 개선하고 싶으신가요? 