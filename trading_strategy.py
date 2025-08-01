#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래 전략 인터페이스 및 기본 전략 구현
키움 API와 연동하여 자동매매 전략을 실행합니다.
"""

import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger

class StrategyType(Enum):
    """전략 타입 정의"""
    MOVING_AVERAGE = "이동평균"
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER_BANDS = "볼린저밴드"
    MOMENTUM = "모멘텀"
    MEAN_REVERSION = "평균회귀"
    BREAKOUT = "브레이크아웃"
    CUSTOM = "커스텀"

class SignalType(Enum):
    """매매 신호 타입"""
    BUY = "매수"
    SELL = "매도"
    HOLD = "보유"
    CANCEL = "취소"

@dataclass
class TradingSignal:
    """매매 신호 데이터 클래스"""
    code: str
    signal_type: SignalType
    price: float
    quantity: int
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    timestamp: datetime
    strategy_name: str
    reason: str
    metadata: Dict = None

@dataclass
class Position:
    """포지션 정보"""
    code: str
    quantity: int
    avg_price: float
    current_price: float
    profit_loss: float
    profit_loss_rate: float
    timestamp: datetime

class StrategyBase(ABC):
    """거래 전략 기본 클래스"""
    
    def __init__(self, name: str, strategy_type: StrategyType):
        self.name = name
        self.strategy_type = strategy_type
        self.is_active = False
        self.positions = {}  # 현재 포지션
        self.signals = []    # 신호 히스토리
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'max_drawdown': 0.0
        }
        
    @abstractmethod
    def generate_signal(self, data: Dict) -> Optional[TradingSignal]:
        """매매 신호 생성 (추상 메서드)"""
        pass
    
    @abstractmethod
    def update_parameters(self, **kwargs):
        """전략 파라미터 업데이트 (추상 메서드)"""
        pass
    
    def activate(self):
        """전략 활성화"""
        self.is_active = True
        logger.info(f"전략 활성화: {self.name}")
    
    def deactivate(self):
        """전략 비활성화"""
        self.is_active = False
        logger.info(f"전략 비활성화: {self.name}")
    
    def add_signal(self, signal: TradingSignal):
        """신호 추가"""
        self.signals.append(signal)
        logger.info(f"신호 생성: {signal.code} - {signal.signal_type.value} - {signal.price:,}원")
    
    def update_position(self, code: str, quantity: int, price: float):
        """포지션 업데이트"""
        if code in self.positions:
            pos = self.positions[code]
            if quantity == 0:  # 포지션 종료
                del self.positions[code]
            else:  # 포지션 업데이트
                pos.quantity = quantity
                pos.current_price = price
                pos.profit_loss = (price - pos.avg_price) * quantity
                pos.profit_loss_rate = (price - pos.avg_price) / pos.avg_price
                pos.timestamp = datetime.now()
        else:
            if quantity > 0:  # 새 포지션
                self.positions[code] = Position(
                    code=code,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    profit_loss=0.0,
                    profit_loss_rate=0.0,
                    timestamp=datetime.now()
                )

class MovingAverageStrategy(StrategyBase):
    """이동평균 전략"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__("이동평균 전략", StrategyType.MOVING_AVERAGE)
        self.short_period = short_period
        self.long_period = long_period
        self.price_history = {}
    
    def generate_signal(self, data: Dict) -> Optional[TradingSignal]:
        """이동평균 기반 매매 신호 생성"""
        try:
            code = data.get('code')
            current_price = data.get('current_price', 0)
            
            if not code or current_price <= 0:
                return None
            
            # 가격 히스토리 업데이트
            if code not in self.price_history:
                self.price_history[code] = []
            
            self.price_history[code].append(current_price)
            
            # 최대 기간만큼만 보관
            max_period = max(self.short_period, self.long_period)
            if len(self.price_history[code]) > max_period:
                self.price_history[code] = self.price_history[code][-max_period:]
            
            # 충분한 데이터가 없으면 신호 생성 안함
            if len(self.price_history[code]) < self.long_period:
                return None
            
            # 이동평균 계산
            short_ma = np.mean(self.price_history[code][-self.short_period:])
            long_ma = np.mean(self.price_history[code][-self.long_period:])
            
            # 신호 생성
            signal_type = SignalType.HOLD
            confidence = 0.5
            reason = ""
            
            if short_ma > long_ma * 1.01:  # 단기 이평선이 장기 이평선보다 1% 이상 높을 때
                signal_type = SignalType.BUY
                confidence = min(0.8, (short_ma - long_ma) / long_ma * 10)
                reason = f"단기이평({short_ma:.0f}) > 장기이평({long_ma:.0f})"
            elif short_ma < long_ma * 0.99:  # 단기 이평선이 장기 이평선보다 1% 이상 낮을 때
                signal_type = SignalType.SELL
                confidence = min(0.8, (long_ma - short_ma) / long_ma * 10)
                reason = f"단기이평({short_ma:.0f}) < 장기이평({long_ma:.0f})"
            
            if signal_type != SignalType.HOLD:
                return TradingSignal(
                    code=code,
                    signal_type=signal_type,
                    price=current_price,
                    quantity=1,  # 기본 1주
                    confidence=confidence,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    reason=reason,
                    metadata={
                        'short_ma': short_ma,
                        'long_ma': long_ma,
                        'short_period': self.short_period,
                        'long_period': self.long_period
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"이동평균 신호 생성 오류: {e}")
            return None
    
    def update_parameters(self, short_period: int = None, long_period: int = None):
        """파라미터 업데이트"""
        if short_period is not None:
            self.short_period = short_period
        if long_period is not None:
            self.long_period = long_period
        logger.info(f"이동평균 전략 파라미터 업데이트: 단기={self.short_period}, 장기={self.long_period}")

class RSIStrategy(StrategyBase):
    """RSI 전략"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI 전략", StrategyType.RSI)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.price_history = {}
    
    def calculate_rsi(self, prices: List[float]) -> float:
        """RSI 계산"""
        if len(prices) < self.period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self, data: Dict) -> Optional[TradingSignal]:
        """RSI 기반 매매 신호 생성"""
        try:
            code = data.get('code')
            current_price = data.get('current_price', 0)
            
            if not code or current_price <= 0:
                return None
            
            # 가격 히스토리 업데이트
            if code not in self.price_history:
                self.price_history[code] = []
            
            self.price_history[code].append(current_price)
            
            # 충분한 데이터가 없으면 신호 생성 안함
            if len(self.price_history[code]) < self.period + 1:
                return None
            
            # RSI 계산
            rsi = self.calculate_rsi(self.price_history[code])
            
            # 신호 생성
            signal_type = SignalType.HOLD
            confidence = 0.5
            reason = ""
            
            if rsi < self.oversold:  # 과매도
                signal_type = SignalType.BUY
                confidence = min(0.8, (self.oversold - rsi) / self.oversold)
                reason = f"RSI 과매도({rsi:.1f})"
            elif rsi > self.overbought:  # 과매수
                signal_type = SignalType.SELL
                confidence = min(0.8, (rsi - self.overbought) / (100 - self.overbought))
                reason = f"RSI 과매수({rsi:.1f})"
            
            if signal_type != SignalType.HOLD:
                return TradingSignal(
                    code=code,
                    signal_type=signal_type,
                    price=current_price,
                    quantity=1,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    reason=reason,
                    metadata={'rsi': rsi, 'period': self.period}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"RSI 신호 생성 오류: {e}")
            return None
    
    def update_parameters(self, period: int = None, oversold: float = None, overbought: float = None):
        """파라미터 업데이트"""
        if period is not None:
            self.period = period
        if oversold is not None:
            self.oversold = oversold
        if overbought is not None:
            self.overbought = overbought
        logger.info(f"RSI 전략 파라미터 업데이트: 기간={self.period}, 과매도={self.oversold}, 과매수={self.overbought}")

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self, kiwoom_api):
        self.kiwoom = kiwoom_api
        self.strategies = {}
        self.is_running = False
        self.thread = None
        self.callback = None
        
        # 전략 실행 설정
        self.execution_config = {
            'auto_execute': True,      # 자동 실행
            'min_confidence': 0.6,     # 최소 신뢰도
            'max_position_size': 10,   # 최대 포지션 크기
            'stop_loss_rate': 0.05,    # 손절 비율 (5%)
            'take_profit_rate': 0.1,   # 익절 비율 (10%)
            'check_interval': 1.0      # 체크 간격 (초)
        }
    
    def add_strategy(self, strategy: StrategyBase):
        """전략 추가"""
        self.strategies[strategy.name] = strategy
        logger.info(f"전략 추가: {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """전략 제거"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.deactivate()
            del self.strategies[strategy_name]
            logger.info(f"전략 제거: {strategy_name}")
    
    def activate_strategy(self, strategy_name: str):
        """전략 활성화"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].activate()
    
    def deactivate_strategy(self, strategy_name: str):
        """전략 비활성화"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].deactivate()
    
    def start(self):
        """전략 실행 시작"""
        if self.is_running:
            logger.warning("전략 매니저가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_strategies, daemon=True)
        self.thread.start()
        logger.info("전략 매니저 시작")
    
    def stop(self):
        """전략 실행 중지"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("전략 매니저 중지")
    
    def _run_strategies(self):
        """전략 실행 루프"""
        while self.is_running:
            try:
                # 실시간 데이터 수집
                real_data_cache = self.kiwoom.get_real_data_cache()
                
                for code, cache_data in real_data_cache.items():
                    if not cache_data:
                        continue
                    
                    data = cache_data.get('data', {})
                    if not data:
                        continue
                    
                    # 각 전략에 대해 신호 생성
                    for strategy in self.strategies.values():
                        if not strategy.is_active:
                            continue
                        
                        signal = strategy.generate_signal(data)
                        if signal and signal.confidence >= self.execution_config['min_confidence']:
                            strategy.add_signal(signal)
                            
                            # 자동 실행이 활성화된 경우 주문 실행
                            if self.execution_config['auto_execute']:
                                self._execute_signal(signal)
                
                time.sleep(self.execution_config['check_interval'])
                
            except Exception as e:
                logger.error(f"전략 실행 오류: {e}")
                time.sleep(1)
    
    def _execute_signal(self, signal: TradingSignal):
        """신호 실행"""
        try:
            # 계좌 정보 조회
            account_info = self.kiwoom.get_account_info()
            if not account_info:
                logger.error("계좌 정보를 가져올 수 없습니다.")
                return
            
            account = list(account_info.keys())[0]
            
            if signal.signal_type == SignalType.BUY:
                # 매수 조건 확인
                if self._can_buy(account, signal):
                    order_no = self.kiwoom.buy_stock(
                        account=account,
                        code=signal.code,
                        quantity=signal.quantity,
                        price=int(signal.price)
                    )
                    if order_no:
                        logger.info(f"매수 주문 실행: {signal.code} - {signal.quantity}주 - {signal.price:,}원")
            
            elif signal.signal_type == SignalType.SELL:
                # 매도 조건 확인
                if self._can_sell(account, signal):
                    order_no = self.kiwoom.sell_stock(
                        account=account,
                        code=signal.code,
                        quantity=signal.quantity,
                        price=int(signal.price)
                    )
                    if order_no:
                        logger.info(f"매도 주문 실행: {signal.code} - {signal.quantity}주 - {signal.price:,}원")
            
            # 콜백 호출
            if self.callback:
                self.callback(signal)
                
        except Exception as e:
            logger.error(f"신호 실행 오류: {e}")
    
    def _can_buy(self, account: str, signal: TradingSignal) -> bool:
        """매수 가능 여부 확인"""
        try:
            # 예수금 확인
            deposit_info = self.kiwoom.get_deposit_info(account)
            if not deposit_info:
                return False
            
            required_amount = signal.price * signal.quantity
            available_amount = deposit_info.get('예수금', 0)
            
            if available_amount < required_amount:
                logger.warning(f"예수금 부족: 필요 {required_amount:,}원, 보유 {available_amount:,}원")
                return False
            
            # 포지션 크기 확인
            current_positions = len([s for s in self.strategies.values() if signal.code in s.positions])
            if current_positions >= self.execution_config['max_position_size']:
                logger.warning(f"최대 포지션 크기 초과: {current_positions}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매수 조건 확인 오류: {e}")
            return False
    
    def _can_sell(self, account: str, signal: TradingSignal) -> bool:
        """매도 가능 여부 확인"""
        try:
            # 보유 주식 확인
            position_info = self.kiwoom.get_position_info(account)
            if signal.code not in position_info:
                logger.warning(f"보유하지 않은 종목: {signal.code}")
                return False
            
            available_quantity = position_info[signal.code].get('보유수량', 0)
            if available_quantity < signal.quantity:
                logger.warning(f"보유 주식 부족: 필요 {signal.quantity}주, 보유 {available_quantity}주")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매도 조건 확인 오류: {e}")
            return False
    
    def set_callback(self, callback: Callable[[TradingSignal], None]):
        """신호 실행 콜백 설정"""
        self.callback = callback
    
    def get_strategy_performance(self) -> Dict:
        """전략 성능 조회"""
        performance = {}
        for name, strategy in self.strategies.items():
            performance[name] = {
                'type': strategy.strategy_type.value,
                'is_active': strategy.is_active,
                'total_signals': len(strategy.signals),
                'current_positions': len(strategy.positions),
                'performance': strategy.performance
            }
        return performance
    
    def update_execution_config(self, **kwargs):
        """실행 설정 업데이트"""
        for key, value in kwargs.items():
            if key in self.execution_config:
                self.execution_config[key] = value
                logger.info(f"실행 설정 변경: {key} = {value}")

# 기본 전략 팩토리
def create_strategy(strategy_type: StrategyType, **kwargs) -> StrategyBase:
    """전략 생성 팩토리 함수"""
    if strategy_type == StrategyType.MOVING_AVERAGE:
        return MovingAverageStrategy(**kwargs)
    elif strategy_type == StrategyType.RSI:
        return RSIStrategy(**kwargs)
    else:
        raise ValueError(f"지원하지 않는 전략 타입: {strategy_type}") 