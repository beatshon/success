# 🎯 거래 전략 연동 인터페이스 가이드

## 📋 개요

키움 API와 연동된 자동매매 전략 인터페이스가 구축되었습니다. 다양한 거래 전략을 쉽게 구현하고 관리할 수 있습니다.

## ✨ 주요 기능

### 1. 전략 패턴 기반 설계
- **StrategyBase**: 모든 전략의 기본 클래스
- **전략 팩토리**: 쉽게 전략 생성
- **확장 가능**: 새로운 전략 쉽게 추가

### 2. 전략 관리 시스템
- **StrategyManager**: 전략 통합 관리
- **활성화/비활성화**: 전략별 개별 제어
- **성능 모니터링**: 전략별 성과 추적

### 3. 실시간 신호 생성
- **자동 신호 생성**: 실시간 데이터 기반
- **신뢰도 평가**: 신호의 신뢰도 계산
- **자동 실행**: 설정에 따른 자동 주문

### 4. 포지션 관리
- **포지션 추적**: 실시간 포지션 모니터링
- **손익 계산**: 실시간 손익 분석
- **리스크 관리**: 손절/익절 설정

## 🚀 사용법

### 기본 설정

```python
from kiwoom_api import KiwoomAPI
from trading_strategy import (
    StrategyManager, StrategyType, SignalType,
    MovingAverageStrategy, RSIStrategy, create_strategy
)

# 키움 API 설정
kiwoom = KiwoomAPI()
if kiwoom.login():
    # 전략 매니저 생성
    strategy_manager = StrategyManager(kiwoom)
```

### 1. 전략 생성

```python
# 팩토리 함수로 전략 생성
ma_strategy = create_strategy(
    StrategyType.MOVING_AVERAGE,
    short_period=5,
    long_period=20
)

rsi_strategy = create_strategy(
    StrategyType.RSI,
    period=14,
    oversold=30,
    overbought=70
)

# 직접 생성
custom_ma = MovingAverageStrategy(short_period=3, long_period=10)
custom_ma.name = "커스텀 이동평균"
```

### 2. 전략 관리

```python
# 전략 추가
strategy_manager.add_strategy(ma_strategy)
strategy_manager.add_strategy(rsi_strategy)

# 전략 활성화/비활성화
strategy_manager.activate_strategy("이동평균 전략")
strategy_manager.deactivate_strategy("RSI 전략")

# 전략 제거
strategy_manager.remove_strategy("RSI 전략")
```

### 3. 실행 설정

```python
# 전략 실행 설정
strategy_manager.update_execution_config(
    auto_execute=True,        # 자동 실행
    min_confidence=0.6,       # 최소 신뢰도
    max_position_size=10,     # 최대 포지션 크기
    stop_loss_rate=0.05,      # 손절 비율 (5%)
    take_profit_rate=0.1,     # 익절 비율 (10%)
    check_interval=1.0        # 체크 간격 (초)
)
```

### 4. 전략 실행

```python
# 실시간 데이터 구독
kiwoom.subscribe_real_data("005930")  # 삼성전자

# 전략 매니저 시작
strategy_manager.start()

# 전략 매니저 중지
strategy_manager.stop()
```

### 5. 신호 콜백 처리

```python
def on_signal_executed(signal):
    """신호 실행 콜백"""
    print(f"신호 실행: {signal.code} - {signal.signal_type.value}")
    print(f"가격: {signal.price:,}원")
    print(f"수량: {signal.quantity}주")
    print(f"신뢰도: {signal.confidence:.2f}")
    print(f"이유: {signal.reason}")

strategy_manager.set_callback(on_signal_executed)
```

### 6. 성능 모니터링

```python
# 전략 성능 조회
performance = strategy_manager.get_strategy_performance()

for name, perf in performance.items():
    print(f"전략: {name}")
    print(f"  타입: {perf['type']}")
    print(f"  활성화: {perf['is_active']}")
    print(f"  총 신호: {perf['total_signals']}")
    print(f"  현재 포지션: {perf['current_positions']}")
    print(f"  성과: {perf['performance']}")
```

## 📊 전략 타입

### StrategyType Enum
```python
class StrategyType(Enum):
    MOVING_AVERAGE = "이동평균"      # 이동평균 크로스오버
    RSI = "RSI"                    # RSI 과매수/과매도
    MACD = "MACD"                  # MACD 신호
    BOLLINGER_BANDS = "볼린저밴드"  # 볼린저 밴드
    MOMENTUM = "모멘텀"            # 모멘텀 전략
    MEAN_REVERSION = "평균회귀"     # 평균회귀 전략
    BREAKOUT = "브레이크아웃"       # 브레이크아웃 전략
    CUSTOM = "커스텀"              # 사용자 정의
```

### SignalType Enum
```python
class SignalType(Enum):
    BUY = "매수"      # 매수 신호
    SELL = "매도"     # 매도 신호
    HOLD = "보유"     # 보유 신호
    CANCEL = "취소"   # 취소 신호
```

## 🔧 기본 전략 상세

### 1. 이동평균 전략 (MovingAverageStrategy)

```python
# 기본 설정
ma_strategy = MovingAverageStrategy(
    short_period=5,    # 단기 이동평균 기간
    long_period=20     # 장기 이동평균 기간
)

# 매수 조건: 단기 이평선 > 장기 이평선 * 1.01
# 매도 조건: 단기 이평선 < 장기 이평선 * 0.99

# 파라미터 업데이트
ma_strategy.update_parameters(
    short_period=3,
    long_period=10
)
```

### 2. RSI 전략 (RSIStrategy)

```python
# 기본 설정
rsi_strategy = RSIStrategy(
    period=14,        # RSI 계산 기간
    oversold=30,      # 과매도 기준
    overbought=70     # 과매수 기준
)

# 매수 조건: RSI < oversold (과매도)
# 매도 조건: RSI > overbought (과매수)

# 파라미터 업데이트
rsi_strategy.update_parameters(
    period=10,
    oversold=25,
    overbought=75
)
```

## 📈 커스텀 전략 구현

### 새로운 전략 추가

```python
from trading_strategy import StrategyBase, StrategyType, SignalType, TradingSignal

class MyCustomStrategy(StrategyBase):
    """커스텀 전략 예제"""
    
    def __init__(self, param1=10, param2=20):
        super().__init__("커스텀 전략", StrategyType.CUSTOM)
        self.param1 = param1
        self.param2 = param2
        self.price_history = {}
    
    def generate_signal(self, data: Dict) -> Optional[TradingSignal]:
        """매매 신호 생성"""
        try:
            code = data.get('code')
            current_price = data.get('current_price', 0)
            
            if not code or current_price <= 0:
                return None
            
            # 가격 히스토리 업데이트
            if code not in self.price_history:
                self.price_history[code] = []
            
            self.price_history[code].append(current_price)
            
            # 전략 로직 구현
            if len(self.price_history[code]) >= self.param1:
                # 예시: 최근 N일간 상승률이 X% 이상이면 매수
                recent_prices = self.price_history[code][-self.param1:]
                price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if price_change > 0.05:  # 5% 이상 상승
                    return TradingSignal(
                        code=code,
                        signal_type=SignalType.BUY,
                        price=current_price,
                        quantity=1,
                        confidence=0.7,
                        timestamp=datetime.now(),
                        strategy_name=self.name,
                        reason=f"상승률 {price_change:.2%}",
                        metadata={'price_change': price_change}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"커스텀 전략 신호 생성 오류: {e}")
            return None
    
    def update_parameters(self, param1=None, param2=None):
        """파라미터 업데이트"""
        if param1 is not None:
            self.param1 = param1
        if param2 is not None:
            self.param2 = param2
        logger.info(f"커스텀 전략 파라미터 업데이트: param1={self.param1}, param2={self.param2}")

# 사용 예시
custom_strategy = MyCustomStrategy(param1=10, param2=20)
strategy_manager.add_strategy(custom_strategy)
```

## 🧪 테스트

```bash
# 거래 전략 인터페이스 테스트 실행
python test_trading_strategy.py
```

테스트 파일에서는 다음 기능들을 검증합니다:
- 전략 생성 및 관리
- 전략 활성화/비활성화
- 실시간 데이터 구독
- 전략 실행 및 신호 생성
- 성능 모니터링
- 백테스트

## 📝 로그 확인

거래 전략 관련 로그는 다음 파일에서 확인할 수 있습니다:
- `logs/trading_strategy_test.log`: 테스트 로그
- `logs/github_sync.log`: 시스템 로그

## ⚠️ 주의사항

1. **실제 거래**: 이 시스템은 실제 거래를 수행합니다. 테스트 시에는 자동 실행을 비활성화하세요.

2. **리스크 관리**: 적절한 손절/익절 설정을 통해 리스크를 관리하세요.

3. **전략 검증**: 새로운 전략은 충분한 백테스트 후 사용하세요.

4. **자금 관리**: 최대 포지션 크기와 예수금을 고려하여 설정하세요.

5. **시장 상황**: 모든 전략은 특정 시장 상황에 최적화되어 있습니다.

## 🔄 다음 단계

거래 전략 연동 인터페이스가 완성되었으니, 다음 중 선택하여 진행하세요:

1. **D) 전체적인 에러 처리 및 안정성 개선** - 시스템 안정성 강화
2. **추가 전략 구현** - MACD, 볼린저 밴드 등 추가 전략
3. **백테스팅 시스템** - 전략 성과 분석 시스템

어떤 부분을 개선하고 싶으신가요? 