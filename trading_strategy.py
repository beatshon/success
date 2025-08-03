#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
트레이딩 전략 구현
이동평균 크로스오버, RSI, 볼린저 밴드 등 기본 전략들
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np
from scipy import stats

# 기술적 지표 계산
from technical_indicators import (
    calculate_sma, calculate_ema, calculate_rsi, 
    calculate_bollinger_bands, calculate_macd,
    calculate_stochastic, calculate_atr
)

class SignalType(Enum):
    """신호 타입"""
    BUY = "매수"
    SELL = "매도"
    HOLD = "보유"
    STRONG_BUY = "강력매수"
    STRONG_SELL = "강력매도"

class StrategyType(Enum):
    """전략 타입"""
    MOVING_AVERAGE_CROSSOVER = "이동평균크로스오버"
    RSI_STRATEGY = "RSI전략"
    BOLLINGER_BANDS = "볼린저밴드"
    MACD_STRATEGY = "MACD전략"
    STOCHASTIC_STRATEGY = "스토캐스틱전략"
    COMBINED_STRATEGY = "복합전략"

@dataclass
class TradingSignal:
    """트레이딩 신호"""
    strategy: StrategyType
    signal_type: SignalType
    confidence: float  # 0.0 ~ 1.0
    price: float
    timestamp: datetime
    code: str = None
    strategy_name: str = None
    details: Dict = None
    stop_loss: float = None
    take_profit: float = None

@dataclass
class StrategyConfig:
    """전략 설정"""
    strategy_type: StrategyType
    parameters: Dict
    enabled: bool = True
    weight: float = 1.0  # 복합 전략에서의 가중치

class TradingStrategy:
    """트레이딩 전략 기본 클래스"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.strategy_type = config.strategy_type
        self.parameters = config.parameters
        self.enabled = config.enabled
        self.weight = config.weight
        
        # 데이터 저장소
        self.price_history = []
        self.signal_history = []
        self.performance_history = []
        
        # 성과 통계
        self.total_signals = 0
        self.successful_signals = 0
        self.total_profit = 0.0
        
    def add_price_data(self, price: float, timestamp: datetime = None):
        """가격 데이터 추가"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.price_history.append({
            'price': price,
            'timestamp': timestamp
        })
        
        # 최대 1000개 데이터만 유지
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
    
    def add_data(self, date: datetime, row: pd.Series):
        """데이터 추가 (DataFrame 행 형태)"""
        # 대소문자 구분 없이 가격 데이터 접근
        if 'Close' in row:
            price = row['Close']
        elif 'close' in row:
            price = row['close']
        else:
            logger.error(f"가격 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {list(row.index)}")
            return
        
        self.add_price_data(price, date)
    
    def generate_signal(self) -> Optional[TradingSignal]:
        """신호 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다")
    
    def update_performance(self, signal: TradingSignal, actual_profit: float):
        """성과 업데이트"""
        self.total_signals += 1
        if actual_profit > 0:
            self.successful_signals += 1
        
        self.total_profit += actual_profit
        
        self.performance_history.append({
            'signal': signal,
            'profit': actual_profit,
            'timestamp': datetime.now()
        })
    
    def get_performance_stats(self) -> Dict:
        """성과 통계 반환"""
        if self.total_signals == 0:
            return {
                'total_signals': 0,
                'success_rate': 0.0,
                'total_profit': 0.0,
                'avg_profit': 0.0
            }
        
        success_rate = (self.successful_signals / self.total_signals) * 100
        avg_profit = self.total_profit / self.total_signals
        
        return {
            'total_signals': self.total_signals,
            'success_rate': success_rate,
            'total_profit': self.total_profit,
            'avg_profit': avg_profit
        }

class MovingAverageCrossoverStrategy(TradingStrategy):
    """이동평균 크로스오버 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.short_period = self.parameters.get('short_period', 5)
        self.long_period = self.parameters.get('long_period', 20)
        self.min_cross_threshold = self.parameters.get('min_cross_threshold', 0.01)
        
    def generate_signal(self) -> Optional[TradingSignal]:
        """이동평균 크로스오버 신호 생성"""
        if len(self.price_history) < self.long_period:
            return None
        
        prices = [data['price'] for data in self.price_history]
        
        # 이동평균 계산
        short_ma = calculate_sma(prices, self.short_period)
        long_ma = calculate_sma(prices, self.long_period)
        
        if len(short_ma) < 2 or len(long_ma) < 2:
            return None
        
        current_short = short_ma[-1]
        current_long = long_ma[-1]
        prev_short = short_ma[-2]
        prev_long = long_ma[-2]
        
        current_price = prices[-1]
        
        # 골든 크로스 (단기선이 장기선을 상향 돌파)
        if (prev_short <= prev_long and current_short > current_long and 
            abs(current_short - current_long) / current_long > self.min_cross_threshold):
            
            confidence = min(0.9, abs(current_short - current_long) / current_long * 10)
            return TradingSignal(
                strategy=self.strategy_type,
                signal_type=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                details={
                    'short_ma': current_short,
                    'long_ma': current_long,
                    'crossover_type': 'golden_cross'
                }
            )
        
        # 데드 크로스 (단기선이 장기선을 하향 돌파)
        elif (prev_short >= prev_long and current_short < current_long and 
              abs(current_short - current_long) / current_long > self.min_cross_threshold):
            
            confidence = min(0.9, abs(current_short - current_long) / current_long * 10)
            return TradingSignal(
                strategy=self.strategy_type,
                signal_type=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                details={
                    'short_ma': current_short,
                    'long_ma': current_long,
                    'crossover_type': 'dead_cross'
                }
            )
        
        return None

class RSIStrategy(TradingStrategy):
    """RSI 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.oversold_threshold = self.parameters.get('oversold_threshold', 30)
        self.overbought_threshold = self.parameters.get('overbought_threshold', 70)
        self.confirmation_period = self.parameters.get('confirmation_period', 2)
        
    def generate_signal(self) -> Optional[TradingSignal]:
        """RSI 신호 생성"""
        if len(self.price_history) < self.rsi_period + self.confirmation_period:
            return None
        
        prices = [data['price'] for data in self.price_history]
        rsi_values = calculate_rsi(prices, self.rsi_period)
        
        if len(rsi_values) < self.confirmation_period:
            return None
        
        current_rsi = rsi_values[-1]
        current_price = prices[-1]
        
        # 과매도 구간에서 반등 신호
        if current_rsi < self.oversold_threshold:
            # 최근 RSI가 상승 추세인지 확인
            recent_rsi = rsi_values[-self.confirmation_period:]
            if all(recent_rsi[i] >= recent_rsi[i-1] for i in range(1, len(recent_rsi))):
                confidence = min(0.9, (self.oversold_threshold - current_rsi) / self.oversold_threshold)
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=SignalType.BUY,
                    confidence=confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'rsi': current_rsi,
                        'signal_type': 'oversold_bounce'
                    }
                )
        
        # 과매수 구간에서 하락 신호
        elif current_rsi > self.overbought_threshold:
            # 최근 RSI가 하락 추세인지 확인
            recent_rsi = rsi_values[-self.confirmation_period:]
            if all(recent_rsi[i] <= recent_rsi[i-1] for i in range(1, len(recent_rsi))):
                confidence = min(0.9, (current_rsi - self.overbought_threshold) / (100 - self.overbought_threshold))
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=SignalType.SELL,
                    confidence=confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'rsi': current_rsi,
                        'signal_type': 'overbought_drop'
                    }
                )
        
        return None

class BollingerBandsStrategy(TradingStrategy):
    """볼린저 밴드 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = self.parameters.get('period', 20)
        self.std_dev = self.parameters.get('std_dev', 2.0)
        self.min_touch_threshold = self.parameters.get('min_touch_threshold', 0.02)
        
    def generate_signal(self) -> Optional[TradingSignal]:
        """볼린저 밴드 신호 생성"""
        if len(self.price_history) < self.period:
            return None
        
        prices = [data['price'] for data in self.price_history]
        bb_data = calculate_bollinger_bands(prices, self.period, self.std_dev)
        
        if not bb_data or len(bb_data['upper']) < 2:
            return None
        
        current_price = prices[-1]
        current_upper = bb_data['upper'][-1]
        current_lower = bb_data['lower'][-1]
        current_middle = bb_data['middle'][-1]
        
        # 하단 밴드 터치 후 반등
        if current_price <= current_lower * (1 + self.min_touch_threshold):
            # 이전 가격이 하단 밴드 아래에 있었는지 확인
            prev_price = prices[-2]
            prev_lower = bb_data['lower'][-2]
            
            if prev_price <= prev_lower:
                confidence = min(0.9, (current_lower - current_price) / current_lower)
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=SignalType.BUY,
                    confidence=confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'upper_band': current_upper,
                        'lower_band': current_lower,
                        'middle_band': current_middle,
                        'signal_type': 'lower_band_bounce'
                    }
                )
        
        # 상단 밴드 터치 후 하락
        elif current_price >= current_upper * (1 - self.min_touch_threshold):
            # 이전 가격이 상단 밴드 위에 있었는지 확인
            prev_price = prices[-2]
            prev_upper = bb_data['upper'][-2]
            
            if prev_price >= prev_upper:
                confidence = min(0.9, (current_price - current_upper) / current_upper)
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=SignalType.SELL,
                    confidence=confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'upper_band': current_upper,
                        'lower_band': current_lower,
                        'middle_band': current_middle,
                        'signal_type': 'upper_band_drop'
                    }
                )
        
        return None

class MACDStrategy(TradingStrategy):
    """MACD 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.fast_period = self.parameters.get('fast_period', 12)
        self.slow_period = self.parameters.get('slow_period', 26)
        self.signal_period = self.parameters.get('signal_period', 9)
        self.min_cross_threshold = self.parameters.get('min_cross_threshold', 0.001)
        
    def generate_signal(self) -> Optional[TradingSignal]:
        """MACD 신호 생성"""
        if len(self.price_history) < self.slow_period + self.signal_period:
            return None
        
        prices = [data['price'] for data in self.price_history]
        macd_data = calculate_macd(prices, self.fast_period, self.slow_period, self.signal_period)
        
        if not macd_data or len(macd_data['macd']) < 2:
            return None
        
        current_macd = macd_data['macd'][-1]
        current_signal = macd_data['signal'][-1]
        prev_macd = macd_data['macd'][-2]
        prev_signal = macd_data['signal'][-2]
        
        current_price = prices[-1]
        
        # MACD가 시그널선을 상향 돌파
        if (prev_macd <= prev_signal and current_macd > current_signal and 
            abs(current_macd - current_signal) > self.min_cross_threshold):
            
            confidence = min(0.9, abs(current_macd - current_signal) * 100)
            return TradingSignal(
                strategy=self.strategy_type,
                signal_type=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                details={
                    'macd': current_macd,
                    'signal': current_signal,
                    'crossover_type': 'bullish'
                }
            )
        
        # MACD가 시그널선을 하향 돌파
        elif (prev_macd >= prev_signal and current_macd < current_signal and 
              abs(current_macd - current_signal) > self.min_cross_threshold):
            
            confidence = min(0.9, abs(current_macd - current_signal) * 100)
            return TradingSignal(
                strategy=self.strategy_type,
                signal_type=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                details={
                    'macd': current_macd,
                    'signal': current_signal,
                    'crossover_type': 'bearish'
                }
            )
        
        return None

class CombinedStrategy(TradingStrategy):
    """복합 전략 (여러 전략의 신호를 조합)"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.strategies = []
        self.min_confidence_threshold = self.parameters.get('min_confidence_threshold', 0.6)
        self.min_strategy_agreement = self.parameters.get('min_strategy_agreement', 2)
        
    def add_strategy(self, strategy: TradingStrategy):
        """전략 추가"""
        self.strategies.append(strategy)
    
    def generate_signal(self) -> Optional[TradingSignal]:
        """복합 신호 생성"""
        if not self.strategies:
            return None
        
        signals = []
        buy_signals = []
        sell_signals = []
        
        # 각 전략에서 신호 수집
        for strategy in self.strategies:
            if strategy.enabled:
                signal = strategy.generate_signal()
                if signal:
                    signals.append(signal)
                    if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                        buy_signals.append(signal)
                    elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                        sell_signals.append(signal)
        
        if not signals:
            return None
        
        current_price = self.price_history[-1]['price'] if self.price_history else 0
        
        # 매수 신호가 더 많고 강한 경우
        if len(buy_signals) >= self.min_strategy_agreement and len(buy_signals) > len(sell_signals):
            avg_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals)
            if avg_confidence >= self.min_confidence_threshold:
                signal_type = SignalType.STRONG_BUY if avg_confidence > 0.8 else SignalType.BUY
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=signal_type,
                    confidence=avg_confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'buy_signals': len(buy_signals),
                        'sell_signals': len(sell_signals),
                        'total_strategies': len(self.strategies),
                        'strategy_agreement': len(buy_signals)
                    }
                )
        
        # 매도 신호가 더 많고 강한 경우
        elif len(sell_signals) >= self.min_strategy_agreement and len(sell_signals) > len(buy_signals):
            avg_confidence = sum(s.confidence for s in sell_signals) / len(sell_signals)
            if avg_confidence >= self.min_confidence_threshold:
                signal_type = SignalType.STRONG_SELL if avg_confidence > 0.8 else SignalType.SELL
                return TradingSignal(
                    strategy=self.strategy_type,
                    signal_type=signal_type,
                    confidence=avg_confidence,
                    price=current_price,
                    timestamp=datetime.now(),
                    details={
                        'buy_signals': len(buy_signals),
                        'sell_signals': len(sell_signals),
                        'total_strategies': len(self.strategies),
                        'strategy_agreement': len(sell_signals)
                    }
                )
        
        return None

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        self.combined_strategy = None
        self.signal_history = []
        
    def add_strategy(self, name: str, strategy: TradingStrategy):
        """전략 추가"""
        self.strategies[name] = strategy
        
        # 복합 전략에 추가
        if self.combined_strategy is None:
            config = StrategyConfig(
                strategy_type=StrategyType.COMBINED_STRATEGY,
                parameters={'min_confidence_threshold': 0.6, 'min_strategy_agreement': 2}
            )
            self.combined_strategy = CombinedStrategy(config)
        
        self.combined_strategy.add_strategy(strategy)
    
    def update_price(self, price: float, timestamp: datetime = None):
        """가격 데이터 업데이트"""
        for strategy in self.strategies.values():
            strategy.add_price_data(price, timestamp)
    
    def generate_signals(self) -> List[TradingSignal]:
        """모든 전략에서 신호 생성"""
        signals = []
        
        # 개별 전략 신호
        for name, strategy in self.strategies.items():
            if strategy.enabled:
                signal = strategy.generate_signal()
                if signal:
                    signals.append(signal)
                    logger.info(f"[{name}] {signal.signal_type.value} 신호 생성 (신뢰도: {signal.confidence:.2f})")
        
        # 복합 전략 신호
        if self.combined_strategy:
            combined_signal = self.combined_strategy.generate_signal()
            if combined_signal:
                signals.append(combined_signal)
                logger.info(f"[복합전략] {combined_signal.signal_type.value} 신호 생성 (신뢰도: {combined_signal.confidence:.2f})")
        
        # 신호 히스토리에 추가
        self.signal_history.extend(signals)
        
        return signals
    
    def get_performance_summary(self) -> Dict:
        """전략별 성과 요약"""
        summary = {}
        
        for name, strategy in self.strategies.items():
            summary[name] = strategy.get_performance_stats()
        
        if self.combined_strategy:
            summary['combined'] = self.combined_strategy.get_performance_stats()
        
        return summary

def create_default_strategies() -> StrategyManager:
    """기본 전략들 생성 - 실제 데이터에 맞게 매우 관대한 설정"""
    manager = StrategyManager()

    # 이동평균 크로스오버 전략 - 매우 짧은 기간
    ma_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={'short_period': 1, 'long_period': 2, 'min_cross_threshold': 0.00001}  # 더 관대한 설정
    )
    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    manager.add_strategy('MA_Crossover', ma_strategy)

    # RSI 전략 - 매우 관대한 임계값
    rsi_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 2, 
            'oversold_threshold': 30, 
            'overbought_threshold': 70,
            'confirmation_period': 1
        }  # 더 관대한 설정
    )
    rsi_strategy = RSIStrategy(rsi_config)
    manager.add_strategy('RSI', rsi_strategy)

    # 볼린저 밴드 전략 - 매우 낮은 임계값
    bb_config = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={'period': 5, 'std_dev': 0.5, 'min_touch_threshold': 0.0001}  # 더 관대한 설정
    )
    bb_strategy = BollingerBandsStrategy(bb_config)
    manager.add_strategy('Bollinger_Bands', bb_strategy)

    # MACD 전략 - 매우 짧은 기간
    macd_config = StrategyConfig(
        strategy_type=StrategyType.MACD_STRATEGY,
        parameters={'fast_period': 2, 'slow_period': 3, 'signal_period': 2}  # 더 관대한 설정
    )
    macd_strategy = MACDStrategy(macd_config)
    manager.add_strategy('MACD', macd_strategy)

    return manager

if __name__ == "__main__":
    # 테스트 코드
    logger.info("트레이딩 전략 테스트 시작")
    
    # 전략 매니저 생성
    manager = create_default_strategies()
    
    # 샘플 가격 데이터 생성
    sample_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                    111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    
    # 가격 데이터 업데이트
    for i, price in enumerate(sample_prices):
        manager.update_price(price, datetime.now() - timedelta(minutes=len(sample_prices)-i))
        time.sleep(0.1)
    
    # 신호 생성
    signals = manager.generate_signals()
    
    logger.info(f"생성된 신호 수: {len(signals)}")
    for signal in signals:
        logger.info(f"신호: {signal.signal_type.value}, 신뢰도: {signal.confidence:.2f}")
    
    # 성과 요약
    performance = manager.get_performance_summary()
    logger.info("성과 요약:")
    for name, stats in performance.items():
        logger.info(f"{name}: {stats}") 