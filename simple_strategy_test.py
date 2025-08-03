#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 전략 신호 생성 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 전략 모듈들
from trading_strategy import create_default_strategies, StrategyManager
from technical_indicators import calculate_sma, calculate_rsi

def create_test_data():
    """테스트용 가격 데이터 생성"""
    # 100일간의 가격 데이터 생성
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = []
    
    # 변동성이 있는 가격 패턴 생성
    base_price = 70000
    current_price = base_price
    
    for i in range(100):
        # 주말 제외
        if dates[i].weekday() >= 5:
            continue
            
        # 랜덤 워크 + 트렌드
        trend = 0.0001 * i
        noise = np.random.normal(0, 0.02)
        change = trend + noise
        current_price *= (1 + change)
        
        prices.append({
            'date': dates[i],
            'price': current_price
        })
    
    return pd.DataFrame(prices)

def test_individual_strategies():
    """개별 전략 테스트"""
    logger.info("=== 개별 전략 테스트 ===")
    
    # 테스트 데이터 생성
    df = create_test_data()
    logger.info(f"테스트 데이터 생성: {len(df)}개")
    
    # 전략 매니저 생성
    manager = create_default_strategies()
    
    # 각 전략별로 테스트
    for name, strategy in manager.strategies.items():
        logger.info(f"\n--- {name} 전략 테스트 ---")
        
        # 가격 데이터 추가
        strategy.price_history = []
        for _, row in df.iterrows():
            strategy.add_price_data(row['price'], row['date'])
        
        logger.info(f"데이터 추가 완료: {len(strategy.price_history)}개")
        
        # 신호 생성 테스트
        signal = strategy.generate_signal()
        if signal:
            logger.info(f"✅ 신호 생성: {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
        else:
            logger.info(f"❌ 신호 없음")
            
            # 디버깅 정보
            if hasattr(strategy, 'short_period'):
                logger.info(f"  MA 전략 - short_period: {strategy.short_period}, long_period: {strategy.long_period}")
                logger.info(f"  데이터 수: {len(strategy.price_history)}")
                
                if len(strategy.price_history) >= strategy.long_period:
                    prices = [data['price'] for data in strategy.price_history]
                    short_ma = calculate_sma(prices, strategy.short_period)
                    long_ma = calculate_sma(prices, strategy.long_period)
                    logger.info(f"  Short MA: {short_ma[-1]:.0f}, Long MA: {long_ma[-1]:.0f}")
            
            if hasattr(strategy, 'rsi_period'):
                logger.info(f"  RSI 전략 - rsi_period: {strategy.rsi_period}")
                logger.info(f"  데이터 수: {len(strategy.price_history)}")
                
                if len(strategy.price_history) >= strategy.rsi_period:
                    prices = [data['price'] for data in strategy.price_history]
                    rsi_values = calculate_rsi(prices, strategy.rsi_period)
                    if rsi_values:
                        logger.info(f"  RSI: {rsi_values[-1]:.2f}")

def test_strategy_manager():
    """전략 매니저 테스트"""
    logger.info("\n=== 전략 매니저 테스트 ===")
    
    # 테스트 데이터 생성
    df = create_test_data()
    
    # 전략 매니저 생성
    manager = create_default_strategies()
    
    # 가격 데이터 업데이트
    for _, row in df.iterrows():
        manager.update_price(row['price'], row['date'])
    
    logger.info(f"가격 데이터 업데이트 완료: {len(df)}개")
    
    # 신호 생성
    signals = manager.generate_signals()
    
    logger.info(f"생성된 신호 수: {len(signals)}")
    
    if signals:
        for i, signal in enumerate(signals[:3]):  # 처음 3개만 출력
            logger.info(f"신호 {i+1}: {signal.signal_type.value} - {signal.timestamp}")
        return True
    else:
        logger.warning("신호가 생성되지 않았습니다.")
        return False

def test_with_more_volatile_data():
    """더 변동성이 큰 데이터로 테스트"""
    logger.info("\n=== 변동성 높은 데이터 테스트 ===")
    
    # 더 변동성이 큰 데이터 생성
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    prices = []
    
    base_price = 70000
    current_price = base_price
    
    for i in range(200):
        if dates[i].weekday() >= 5:
            continue
            
        # 더 큰 변동성
        trend = 0.0001 * i
        noise = np.random.normal(0, 0.04)  # 4% 변동성
        change = trend + noise
        current_price *= (1 + change)
        
        prices.append({
            'date': dates[i],
            'price': current_price
        })
    
    df = pd.DataFrame(prices)
    logger.info(f"변동성 높은 데이터 생성: {len(df)}개")
    
    # 전략 매니저 테스트
    manager = create_default_strategies()
    
    for _, row in df.iterrows():
        manager.update_price(row['price'], row['date'])
    
    signals = manager.generate_signals()
    logger.info(f"변동성 높은 데이터에서 생성된 신호: {len(signals)}개")
    
    return len(signals) > 0

def main():
    """메인 함수"""
    logger.info("간단한 전략 신호 생성 테스트 시작")
    
    try:
        # 1. 개별 전략 테스트
        test_individual_strategies()
        
        # 2. 전략 매니저 테스트
        success1 = test_strategy_manager()
        
        # 3. 변동성 높은 데이터 테스트
        success2 = test_with_more_volatile_data()
        
        # 결과 요약
        logger.info(f"\n=== 테스트 결과 요약 ===")
        logger.info(f"전략 매니저 테스트: {'✅ 성공' if success1 else '❌ 실패'}")
        logger.info(f"변동성 높은 데이터 테스트: {'✅ 성공' if success2 else '❌ 실패'}")
        
        if success1 or success2:
            logger.info("🎉 전략 신호 생성이 정상적으로 작동합니다!")
        else:
            logger.error("⚠️ 전략 신호 생성에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 