#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 전략
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 전략 모듈들
from typing import Optional
from trading_strategy import (
    TradingStrategy, StrategyConfig, StrategyType, 
    TradingSignal, SignalType, StrategyManager
)

class SimpleTestStrategy(TradingStrategy):
    """매우 간단한 테스트 전략 - 매 5일마다 신호 생성"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.signal_counter = 0
    
    def generate_signal(self) -> Optional[TradingSignal]:
        """매우 간단한 신호 생성 - 매 5일마다 매수/매도 신호"""
        if len(self.price_history) < 5:
            return None
        
        self.signal_counter += 1
        
        # 매 5일마다 신호 생성
        if self.signal_counter % 5 == 0:
            current_price = self.price_history[-1]['price']
            current_time = self.price_history[-1]['timestamp']
            
            # 홀수번째는 매수, 짝수번째는 매도
            if (self.signal_counter // 5) % 2 == 1:
                signal_type = SignalType.BUY
                confidence = 0.8
            else:
                signal_type = SignalType.SELL
                confidence = 0.8
            
            return TradingSignal(
                strategy=self.strategy_type,
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                timestamp=current_time,
                details={'signal_counter': self.signal_counter}
            )
        
        return None

def create_test_strategies() -> StrategyManager:
    """테스트용 전략들 생성"""
    manager = StrategyManager()
    
    # 간단한 테스트 전략
    test_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={},
        enabled=True,
        weight=1.0
    )
    test_strategy = SimpleTestStrategy(test_config)
    manager.add_strategy('Simple_Test', test_strategy)
    
    return manager

def test_simple_strategy():
    """간단한 전략 테스트"""
    logger.info("=== 간단한 전략 테스트 ===")
    
    # 전략 매니저 생성
    manager = create_test_strategies()
    
    # 샘플 가격 데이터 생성
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    prices = []
    
    base_price = 70000
    current_price = base_price
    
    for i in range(50):
        if dates[i].weekday() >= 5:  # 주말 제외
            continue
            
        # 랜덤 워크
        change = np.random.normal(0, 0.02)
        current_price *= (1 + change)
        
        prices.append({
            'date': dates[i],
            'price': current_price
        })
    
    df = pd.DataFrame(prices)
    logger.info(f"테스트 데이터 생성: {len(df)}개")
    
    # 전략에 가격 데이터 추가
    strategy = manager.strategies['Simple_Test']
    
    for _, row in df.iterrows():
        strategy.add_price_data(row['price'], row['date'])
    
    logger.info(f"전략에 데이터 추가 완료: {len(strategy.price_history)}개")
    
    # 신호 생성 테스트
    total_signals = 0
    
    for i, (_, row) in enumerate(df.iterrows()):
        signal = strategy.generate_signal()
        if signal:
            total_signals += 1
            logger.info(f"신호 {total_signals}: {row['date'].strftime('%Y-%m-%d')} - {signal.signal_type.value} @ {signal.price:,.0f}원")
    
    logger.info(f"\n총 생성된 신호: {total_signals}개")
    
    if total_signals > 0:
        logger.info("✅ 간단한 전략이 정상적으로 신호를 생성합니다!")
        return True
    else:
        logger.error("❌ 간단한 전략에서도 신호가 생성되지 않았습니다.")
        return False

def main():
    """메인 함수"""
    logger.info("간단한 전략 테스트 시작")
    
    try:
        success = test_simple_strategy()
        
        if success:
            logger.info("🎉 전략 신호 생성이 정상적으로 작동합니다!")
        else:
            logger.error("⚠️ 전략 신호 생성에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 