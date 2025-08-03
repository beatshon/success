#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
커스텀 트레이딩 전략
사용자 정의 진입/청산 조건을 구현합니다.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_strategy import TradingStrategy, TradingSignal, SignalType, StrategyType, StrategyConfig
from technical_indicators import calculate_sma, calculate_rsi

class CustomStrategy(TradingStrategy):
    """
    사용자 정의 트레이딩 전략
    진입: MA5 > MA20 + RSI < 35 + 거래량 급증
    청산: (목표 수익률 +5% or 손절 -2%) + 트레일링 스탑
    """
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                strategy_type=StrategyType.COMBINED_STRATEGY,
                parameters={
                    'ma_short': 5,
                    'ma_long': 20,
                    'rsi_period': 14,
                    'rsi_oversold': 35,
                    'volume_spike_ratio': 2.0,  # 평균 거래량의 2배
                    'take_profit': 0.05,  # 5% 익절
                    'stop_loss': -0.02,   # 2% 손절
                    'trailing_stop': 0.015,  # 1.5% 트레일링 스탑
                    'max_position_ratio': 0.20,  # 종목당 최대 20% 비중
                },
                enabled=True,
                weight=1.0
            )
        super().__init__(config)
        
        # 포지션 관리
        self.positions = {}
        self.entry_prices = {}
        self.highest_prices = {}  # 트레일링 스탑용
        
    def generate_signal(self, data: pd.DataFrame, code: str = None) -> Optional[TradingSignal]:
        """사용자 정의 전략에 따른 신호 생성"""
        if len(data) < self.parameters['ma_long']:
            return None
            
        try:
            # 현재 가격과 거래량
            current_price = data['close'].iloc[-1]
            current_volume = data['volume'].iloc[-1]
            
            # 이동평균 계산
            ma5 = calculate_sma(data['close'], self.parameters['ma_short'])
            ma20 = calculate_sma(data['close'], self.parameters['ma_long'])
            
            # RSI 계산
            rsi = calculate_rsi(data['close'], self.parameters['rsi_period'])
            
            # 평균 거래량 계산 (최근 20일)
            avg_volume = data['volume'].iloc[-20:].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # 현재 값
            current_ma5 = ma5.iloc[-1]
            current_ma20 = ma20.iloc[-1]
            current_rsi = rsi.iloc[-1]
            
            # 디버깅 로그
            logger.debug(f"{code} - MA5: {current_ma5:.2f}, MA20: {current_ma20:.2f}, RSI: {current_rsi:.2f}, Volume Ratio: {volume_ratio:.2f}")
            
            # 포지션 확인
            has_position = code in self.positions and self.positions[code] > 0
            
            # 진입 신호: MA5 > MA20 + RSI < 35 + 거래량 급증
            if not has_position:
                if (current_ma5 > current_ma20 and 
                    current_rsi < self.parameters['rsi_oversold'] and
                    volume_ratio >= self.parameters['volume_spike_ratio']):
                    
                    logger.info(f"🎯 {code} 매수 신호 발생! MA5({current_ma5:.2f}) > MA20({current_ma20:.2f}), RSI({current_rsi:.2f}) < 35, Volume Spike({volume_ratio:.2f}x)")
                    
                    return TradingSignal(
                        strategy=self.strategy_type,
                        signal_type=SignalType.BUY,
                        confidence=0.8,
                        price=current_price,
                        timestamp=data.index[-1],
                        code=code,
                        strategy_name="CustomStrategy",
                        details={
                            'ma5': current_ma5,
                            'ma20': current_ma20,
                            'rsi': current_rsi,
                            'volume_ratio': volume_ratio,
                            'reason': 'MA5>MA20 + RSI<35 + Volume Spike'
                        },
                        stop_loss=current_price * (1 + self.parameters['stop_loss']),
                        take_profit=current_price * (1 + self.parameters['take_profit'])
                    )
            
            # 청산 신호: (목표 수익률 +5% or 손절 -2%) + 트레일링 스탑
            elif has_position and code in self.entry_prices:
                entry_price = self.entry_prices[code]
                profit_rate = (current_price - entry_price) / entry_price
                
                # 최고가 업데이트 (트레일링 스탑용)
                if code not in self.highest_prices:
                    self.highest_prices[code] = current_price
                else:
                    self.highest_prices[code] = max(self.highest_prices[code], current_price)
                
                highest_price = self.highest_prices[code]
                drawdown_from_high = (current_price - highest_price) / highest_price
                
                # 청산 조건 확인
                sell_reason = None
                
                # 1. 목표 수익률 달성 (+5%)
                if profit_rate >= self.parameters['take_profit']:
                    sell_reason = f"목표 수익률 달성 ({profit_rate:.2%})"
                
                # 2. 손절 (-2%)
                elif profit_rate <= self.parameters['stop_loss']:
                    sell_reason = f"손절 ({profit_rate:.2%})"
                
                # 3. 트레일링 스탑 (고점 대비 -1.5%)
                elif drawdown_from_high <= -self.parameters['trailing_stop']:
                    sell_reason = f"트레일링 스탑 (고점 대비 {drawdown_from_high:.2%})"
                
                if sell_reason:
                    logger.info(f"🎯 {code} 매도 신호 발생! {sell_reason}")
                    
                    return TradingSignal(
                        strategy=self.strategy_type,
                        signal_type=SignalType.SELL,
                        confidence=0.9,
                        price=current_price,
                        timestamp=data.index[-1],
                        code=code,
                        strategy_name="CustomStrategy",
                        details={
                            'entry_price': entry_price,
                            'current_price': current_price,
                            'profit_rate': profit_rate,
                            'highest_price': highest_price,
                            'drawdown_from_high': drawdown_from_high,
                            'reason': sell_reason
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"신호 생성 중 오류: {e}")
            return None
    
    def update_position(self, code: str, quantity: int, price: float, action: str):
        """포지션 업데이트"""
        if action == 'BUY':
            self.positions[code] = self.positions.get(code, 0) + quantity
            self.entry_prices[code] = price
            self.highest_prices[code] = price
        elif action == 'SELL':
            self.positions[code] = max(0, self.positions.get(code, 0) - quantity)
            if self.positions[code] == 0:
                # 포지션 청산 시 관련 정보 삭제
                self.entry_prices.pop(code, None)
                self.highest_prices.pop(code, None)
    
    def get_position_size_recommendation(self, code: str, current_capital: float, 
                                       portfolio_value: float) -> float:
        """포지션 크기 추천 (종목당 최대 20% 비중)"""
        max_position_value = portfolio_value * self.parameters['max_position_ratio']
        recommended_size = min(current_capital * 0.95, max_position_value)  # 현금의 95% 또는 포트폴리오의 20%
        return recommended_size

def create_custom_strategy() -> CustomStrategy:
    """커스텀 전략 생성"""
    return CustomStrategy()

if __name__ == "__main__":
    # 로그 설정
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 전략 테스트
    strategy = create_custom_strategy()
    logger.info("커스텀 트레이딩 전략 생성 완료")
    logger.info(f"진입 조건: MA5 > MA20 + RSI < 35 + 거래량 급증")
    logger.info(f"청산 조건: 익절 +5% / 손절 -2% / 트레일링 스탑 -1.5%")
    logger.info(f"리스크 관리: 종목당 최대 20% 비중")