#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 백테스트 테스트
문제를 빠르게 진단하고 수정합니다.
"""

import sys
import os
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_strategy import (
    StrategyManager, create_default_strategies, TradingSignal, 
    SignalType, StrategyType, StrategyConfig
)
from technical_indicators import (
    calculate_sma, calculate_ema, calculate_rsi, 
    calculate_bollinger_bands, calculate_macd
)

def test_simple_strategy():
    """간단한 전략 테스트"""
    logger.info("=== 간단한 전략 테스트 ===")
    
    # 전략 매니저 생성
    strategy_manager = create_default_strategies()
    
    # 더 많은 샘플 데이터 생성 (365일)
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    
    # 실제 주가와 비슷한 패턴 생성
    base_price = 50000
    prices = []
    for i in range(len(dates)):
        # 상승 추세 + 변동성
        trend = i * 10  # 상승 추세
        noise = np.random.normal(0, 1000)  # 변동성
        price = base_price + trend + noise
        prices.append(max(price, 1000))  # 최소 가격 보장
    
    sample_data = pd.DataFrame({
        'open': prices,
        'high': [p + np.random.uniform(0, 500) for p in prices],
        'low': [p - np.random.uniform(0, 500) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 100000) for _ in prices]
    }, index=dates)
    
    logger.info(f"샘플 데이터 생성: {len(sample_data)}개")
    logger.info(f"가격 범위: {sample_data['close'].min():,.0f} ~ {sample_data['close'].max():,.0f}")
    
    # 각 전략에 데이터 추가
    total_signals = 0
    
    for name, strategy in strategy_manager.strategies.items():
        logger.info(f"\n{name} 전략 테스트:")
        
        # 데이터 초기화
        strategy.price_history = []
        
        # 데이터 추가
        for date, row in sample_data.iterrows():
            strategy.add_data(date, row)
        
        logger.info(f"  데이터 추가 완료: {len(strategy.price_history)}개")
        
        # 신호 생성 테스트 (마지막 30일 동안)
        signals_count = 0
        for i in range(max(0, len(sample_data) - 30), len(sample_data)):
            date = sample_data.index[i]
            row = sample_data.iloc[i]
            
            # 해당 날짜까지의 데이터로 신호 생성
            temp_strategy = type(strategy)(strategy.config)
            for j in range(i + 1):
                temp_strategy.add_data(sample_data.index[j], sample_data.iloc[j])
            
            signal = temp_strategy.generate_signal()
            if signal:
                signals_count += 1
                logger.info(f"  {date.strftime('%Y-%m-%d')}: {signal.signal_type} (신뢰도: {signal.confidence:.2f})")
        
        logger.info(f"  총 신호 수: {signals_count}개")
        total_signals += signals_count
    
    logger.info(f"\n=== 전체 결과 ===")
    logger.info(f"총 생성된 신호: {total_signals}개")
    
    return total_signals > 0

def test_improved_strategies():
    """개선된 전략 테스트"""
    logger.info("\n=== 개선된 전략 테스트 ===")
    
    # 더 관대한 파라미터로 전략 생성
    manager = StrategyManager()
    
    # 이동평균 크로스오버 - 매우 짧은 기간
    ma_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={'short_period': 1, 'long_period': 2, 'min_cross_threshold': 0.0001}
    )
    from trading_strategy import MovingAverageCrossoverStrategy
    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    manager.add_strategy('MA_Crossover_Improved', ma_strategy)
    
    # RSI - 매우 관대한 임계값
    rsi_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={'rsi_period': 3, 'oversold_threshold': 40, 'overbought_threshold': 60}
    )
    from trading_strategy import RSIStrategy
    rsi_strategy = RSIStrategy(rsi_config)
    manager.add_strategy('RSI_Improved', rsi_strategy)
    
    # 샘플 데이터 생성
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    prices = [50000 + i * 20 + np.random.normal(0, 500) for i in range(len(dates))]
    
    sample_data = pd.DataFrame({
        'open': prices,
        'high': [p + np.random.uniform(0, 200) for p in prices],
        'low': [p - np.random.uniform(0, 200) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 50000) for _ in prices]
    }, index=dates)
    
    # 전략 테스트
    for name, strategy in manager.strategies.items():
        logger.info(f"\n{name} 전략:")
        
        # 데이터 추가
        for date, row in sample_data.iterrows():
            strategy.add_data(date, row)
        
        # 신호 생성
        signal = strategy.generate_signal()
        if signal:
            logger.info(f"  ✅ 신호 생성: {signal.signal_type} (신뢰도: {signal.confidence:.2f})")
        else:
            logger.info(f"  ❌ 신호 없음")

def main():
    """메인 함수"""
    logger.info("빠른 백테스트 테스트 시작")
    
    # 1. 기본 전략 테스트
    success1 = test_simple_strategy()
    
    # 2. 개선된 전략 테스트
    test_improved_strategies()
    
    logger.info(f"\n=== 테스트 완료 ===")
    if success1:
        logger.info("✅ 기본 전략에서 신호가 생성됩니다!")
    else:
        logger.warning("⚠️ 기본 전략에서 신호가 생성되지 않습니다.")

if __name__ == "__main__":
    main() 