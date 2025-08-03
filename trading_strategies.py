#!/usr/bin/env python3
"""
거래 전략 구현
다양한 자동매매 전략을 구현합니다.
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import config
from loguru import logger

class BaseStrategy:
    """기본 전략 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.is_active = False
        self.positions = {}
        self.trade_history = []
        
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """매매 신호 계산 (하위 클래스에서 구현)"""
        raise NotImplementedError
        
    def should_buy(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        raise NotImplementedError
        
    def should_sell(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매도 조건 확인"""
        raise NotImplementedError
        
    def get_position_size(self, stock_code: str, current_price: float, available_cash: float) -> int:
        """포지션 크기 계산"""
        raise NotImplementedError

class MovingAverageStrategy(BaseStrategy):
    """이동평균 크로스오버 전략"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__(
            name="이동평균 크로스오버",
            description=f"단기({short_period}일) 이동평균과 장기({long_period}일) 이동평균의 크로스오버를 이용한 전략"
        )
        self.short_period = short_period
        self.long_period = long_period
        
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """매매 신호 계산"""
        if len(data) < self.long_period:
            return {}
            
        # 이동평균 계산
        data['MA_short'] = data['close'].rolling(window=self.short_period).mean()
        data['MA_long'] = data['close'].rolling(window=self.long_period).mean()
        
        signals = {}
        
        # 크로스오버 확인
        if len(data) >= 2:
            prev_short = data['MA_short'].iloc[-2]
            prev_long = data['MA_long'].iloc[-2]
            curr_short = data['MA_short'].iloc[-1]
            curr_long = data['MA_long'].iloc[-1]
            
            # 골든 크로스 (단기선이 장기선을 상향 돌파)
            if prev_short <= prev_long and curr_short > curr_long:
                signals['action'] = 'BUY'
                signals['reason'] = f'골든 크로스 (단기: {curr_short:.0f}, 장기: {curr_long:.0f})'
                
            # 데드 크로스 (단기선이 장기선을 하향 돌파)
            elif prev_short >= prev_long and curr_short < curr_long:
                signals['action'] = 'SELL'
                signals['reason'] = f'데드 크로스 (단기: {curr_short:.0f}, 장기: {curr_long:.0f})'
                
        return signals
        
    def should_buy(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'BUY'
        
    def should_sell(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매도 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'SELL'
        
    def get_position_size(self, stock_code: str, current_price: float, available_cash: float) -> int:
        """포지션 크기 계산 (가용 자금의 20% 사용)"""
        target_amount = available_cash * 0.2
        return int(target_amount / current_price)

class RSIStrategy(BaseStrategy):
    """RSI 과매수/과매도 전략"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(
            name="RSI 전략",
            description=f"RSI({period}일) 과매수({overbought})/과매도({oversold}) 구간을 이용한 전략"
        )
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def calculate_rsi(self, data: pd.DataFrame) -> float:
        """RSI 계산"""
        if len(data) < self.period + 1:
            return 50.0
            
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
        
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """매매 신호 계산"""
        rsi = self.calculate_rsi(data)
        
        signals = {}
        
        if rsi <= self.oversold:
            signals['action'] = 'BUY'
            signals['reason'] = f'RSI 과매도 ({rsi:.1f})'
        elif rsi >= self.overbought:
            signals['action'] = 'SELL'
            signals['reason'] = f'RSI 과매수 ({rsi:.1f})'
            
        return signals
        
    def should_buy(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'BUY'
        
    def should_sell(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매도 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'SELL'
        
    def get_position_size(self, stock_code: str, current_price: float, available_cash: float) -> int:
        """포지션 크기 계산 (가용 자금의 15% 사용)"""
        target_amount = available_cash * 0.15
        return int(target_amount / current_price)

class BollingerBandsStrategy(BaseStrategy):
    """볼린저 밴드 전략"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(
            name="볼린저 밴드 전략",
            description=f"볼린저 밴드({period}일, {std_dev}σ)를 이용한 전략"
        )
        self.period = period
        self.std_dev = std_dev
        
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Tuple[float, float, float]:
        """볼린저 밴드 계산"""
        if len(data) < self.period:
            return 0.0, 0.0, 0.0
            
        sma = data['close'].rolling(window=self.period).mean()
        std = data['close'].rolling(window=self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        return upper_band.iloc[-1], sma.iloc[-1], lower_band.iloc[-1]
        
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """매매 신호 계산"""
        if len(data) < self.period:
            return {}
            
        current_price = data['close'].iloc[-1]
        upper, middle, lower = self.calculate_bollinger_bands(data)
        
        signals = {}
        
        if current_price <= lower:
            signals['action'] = 'BUY'
            signals['reason'] = f'볼린저 밴드 하단 터치 (가격: {current_price:.0f}, 하단: {lower:.0f})'
        elif current_price >= upper:
            signals['action'] = 'SELL'
            signals['reason'] = f'볼린저 밴드 상단 터치 (가격: {current_price:.0f}, 상단: {upper:.0f})'
            
        return signals
        
    def should_buy(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'BUY'
        
    def should_sell(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매도 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'SELL'
        
    def get_position_size(self, stock_code: str, current_price: float, available_cash: float) -> int:
        """포지션 크기 계산 (가용 자금의 25% 사용)"""
        target_amount = available_cash * 0.25
        return int(target_amount / current_price)

class MomentumStrategy(BaseStrategy):
    """모멘텀 전략"""
    
    def __init__(self, period: int = 10, threshold: float = 0.05):
        super().__init__(
            name="모멘텀 전략",
            description=f"모멘텀({period}일) 변화율 {threshold*100}% 이상을 이용한 전략"
        )
        self.period = period
        self.threshold = threshold
        
    def calculate_momentum(self, data: pd.DataFrame) -> float:
        """모멘텀 계산"""
        if len(data) < self.period + 1:
            return 0.0
            
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-self.period-1]
        
        return (current_price - past_price) / past_price
        
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """매매 신호 계산"""
        momentum = self.calculate_momentum(data)
        
        signals = {}
        
        if momentum >= self.threshold:
            signals['action'] = 'BUY'
            signals['reason'] = f'상승 모멘텀 ({momentum*100:.1f}%)'
        elif momentum <= -self.threshold:
            signals['action'] = 'SELL'
            signals['reason'] = f'하락 모멘텀 ({momentum*100:.1f}%)'
            
        return signals
        
    def should_buy(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'BUY'
        
    def should_sell(self, stock_code: str, current_price: float, data: pd.DataFrame) -> bool:
        """매도 조건 확인"""
        signals = self.calculate_signals(data)
        return signals.get('action') == 'SELL'
        
    def get_position_size(self, stock_code: str, current_price: float, available_cash: float) -> int:
        """포지션 크기 계산 (가용 자금의 30% 사용)"""
        target_amount = available_cash * 0.30
        return int(target_amount / current_price)

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        self.active_strategies = {}
        
    def add_strategy(self, strategy: BaseStrategy):
        """전략 추가"""
        self.strategies[strategy.name] = strategy
        logger.info(f"전략 추가: {strategy.name}")
        
    def activate_strategy(self, strategy_name: str):
        """전략 활성화"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].is_active = True
            self.active_strategies[strategy_name] = self.strategies[strategy_name]
            logger.info(f"전략 활성화: {strategy_name}")
        else:
            logger.error(f"전략을 찾을 수 없음: {strategy_name}")
            
    def deactivate_strategy(self, strategy_name: str):
        """전략 비활성화"""
        if strategy_name in self.active_strategies:
            self.active_strategies[strategy_name].is_active = False
            del self.active_strategies[strategy_name]
            logger.info(f"전략 비활성화: {strategy_name}")
            
    def get_all_signals(self, stock_code: str, current_price: float, data: pd.DataFrame) -> List[Dict]:
        """모든 활성 전략의 신호 수집"""
        signals = []
        
        for strategy_name, strategy in self.active_strategies.items():
            if strategy.is_active:
                signal = strategy.calculate_signals(data)
                if signal:
                    signal['strategy'] = strategy_name
                    signal['stock_code'] = stock_code
                    signal['current_price'] = current_price
                    signal['timestamp'] = datetime.now()
                    signals.append(signal)
                    
        return signals
        
    def get_consensus_signal(self, stock_code: str, current_price: float, data: pd.DataFrame) -> Optional[Dict]:
        """전략들의 합의 신호 생성"""
        signals = self.get_all_signals(stock_code, current_price, data)
        
        if not signals:
            return None
            
        # 매수/매도 신호 개수 계산
        buy_signals = [s for s in signals if s['action'] == 'BUY']
        sell_signals = [s for s in signals if s['action'] == 'SELL']
        
        total_strategies = len(self.active_strategies)
        
        # 50% 이상의 전략이 같은 신호를 보내면 합의 신호 생성
        if len(buy_signals) >= total_strategies * 0.5:
            return {
                'action': 'BUY',
                'reason': f'매수 합의 신호 ({len(buy_signals)}/{total_strategies} 전략)',
                'stock_code': stock_code,
                'current_price': current_price,
                'timestamp': datetime.now()
            }
        elif len(sell_signals) >= total_strategies * 0.5:
            return {
                'action': 'SELL',
                'reason': f'매도 합의 신호 ({len(sell_signals)}/{total_strategies} 전략)',
                'stock_code': stock_code,
                'current_price': current_price,
                'timestamp': datetime.now()
            }
            
        return None

def create_sample_strategies() -> StrategyManager:
    """샘플 전략들 생성"""
    manager = StrategyManager()
    
    # 이동평균 전략
    ma_strategy = MovingAverageStrategy(short_period=5, long_period=20)
    manager.add_strategy(ma_strategy)
    
    # RSI 전략
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    manager.add_strategy(rsi_strategy)
    
    # 볼린저 밴드 전략
    bb_strategy = BollingerBandsStrategy(period=20, std_dev=2.0)
    manager.add_strategy(bb_strategy)
    
    # 모멘텀 전략
    momentum_strategy = MomentumStrategy(period=10, threshold=0.05)
    manager.add_strategy(momentum_strategy)
    
    return manager

if __name__ == "__main__":
    # 샘플 전략 테스트
    manager = create_sample_strategies()
    
    # 모든 전략 활성화
    for strategy_name in manager.strategies.keys():
        manager.activate_strategy(strategy_name)
    
    print("📊 거래 전략 구현 완료!")
    print(f"총 {len(manager.strategies)}개 전략 생성됨:")
    
    for name, strategy in manager.strategies.items():
        print(f"  - {name}: {strategy.description}") 