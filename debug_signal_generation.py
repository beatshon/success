#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신호 생성 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 백테스팅 시스템 모듈들
from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies

def debug_signal_generation():
    """신호 생성 과정 디버깅"""
    logger.info("=== 신호 생성 디버깅 ===")
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 샘플 데이터 생성
    logger.info("샘플 데이터 생성...")
    engine._generate_sample_data()
    
    # 전략 매니저 초기화
    engine.strategy_manager = create_default_strategies()
    
    # 첫 번째 종목으로 테스트
    test_code = list(engine.data.keys())[0]
    logger.info(f"테스트 종목: {test_code}")
    
    # 데이터 확인
    df = engine.data[test_code]
    logger.info(f"데이터 수: {len(df)}개")
    logger.info(f"데이터 범위: {df.index[0]} ~ {df.index[-1]}")
    
    # 전략별 데이터 추가 과정 추적
    logger.info("\n=== 전략별 데이터 추가 과정 ===")
    
    for name, strategy in engine.strategy_manager.strategies.items():
        logger.info(f"\n{name} 전략:")
        logger.info(f"  전략 타입: {strategy.strategy_type.value}")
        logger.info(f"  활성화: {strategy.enabled}")
        
        # 전략에 가격 데이터 추가
        strategy.price_history = []
        
        for i, (date, row) in enumerate(df.iterrows()):
            strategy.add_price_data(row['close'], date)
            
            # 10일마다 상태 출력
            if i % 10 == 0:
                logger.info(f"    {i+1}일차: {date.strftime('%Y-%m-%d')} - {row['close']:,.0f}원")
        
        logger.info(f"  총 데이터 추가: {len(strategy.price_history)}개")
        
        # 전략별 최소 데이터 요구사항 확인
        if hasattr(strategy, 'long_period'):
            logger.info(f"  MA 전략 - 단기: {strategy.short_period}, 장기: {strategy.long_period}")
            if len(strategy.price_history) >= strategy.long_period:
                logger.info(f"  ✅ 충분한 데이터 (필요: {strategy.long_period}, 보유: {len(strategy.price_history)})")
            else:
                logger.warning(f"  ❌ 데이터 부족 (필요: {strategy.long_period}, 보유: {len(strategy.price_history)})")
        
        if hasattr(strategy, 'rsi_period'):
            logger.info(f"  RSI 전략 - 기간: {strategy.rsi_period}")
            if len(strategy.price_history) >= strategy.rsi_period:
                logger.info(f"  ✅ 충분한 데이터 (필요: {strategy.rsi_period}, 보유: {len(strategy.price_history)})")
            else:
                logger.warning(f"  ❌ 데이터 부족 (필요: {strategy.rsi_period}, 보유: {len(strategy.price_history)})")
    
    # 일별 신호 생성 테스트
    logger.info("\n=== 일별 신호 생성 테스트 ===")
    
    total_signals = 0
    
    for i, date in enumerate(df.index[:30]):  # 처음 30일만 테스트
        current_price = df.loc[date, 'close']
        
        logger.info(f"\n--- {i+1}일차: {date.strftime('%Y-%m-%d')} ---")
        logger.info(f"현재가: {current_price:,.0f}원")
        
        # 신호 생성
        signals = engine._generate_signals(date)
        
        if signals:
            total_signals += len(signals)
            logger.info(f"생성된 신호: {len(signals)}개")
            
            for j, signal in enumerate(signals):
                logger.info(f"  신호 {j+1}: {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
        else:
            logger.info("생성된 신호: 0개")
    
    # 전략별 개별 신호 생성 테스트
    logger.info("\n=== 전략별 개별 신호 생성 테스트 ===")
    
    for name, strategy in engine.strategy_manager.strategies.items():
        logger.info(f"\n{name} 전략 개별 테스트:")
        
        # 마지막 10일간 신호 생성 테스트
        for i in range(max(0, len(df) - 10), len(df)):
            date = df.index[i]
            price = df.loc[date, 'close']
            
            signal = strategy.generate_signal()
            if signal:
                logger.info(f"  {date.strftime('%Y-%m-%d')}: {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
                break
        else:
            logger.info(f"  마지막 10일간 신호 없음")
    
    # 최종 결과
    logger.info(f"\n=== 디버깅 결과 ===")
    logger.info(f"총 생성된 신호: {total_signals}개")
    
    if total_signals > 0:
        logger.info("✅ 신호 생성이 정상적으로 작동합니다!")
        return True
    else:
        logger.error("❌ 신호가 생성되지 않았습니다.")
        return False

def debug_strategy_parameters():
    """전략 파라미터 디버깅"""
    logger.info("\n=== 전략 파라미터 디버깅 ===")
    
    # 전략 매니저 생성
    manager = create_default_strategies()
    
    for name, strategy in manager.strategies.items():
        logger.info(f"\n{name} 전략:")
        logger.info(f"  전략 타입: {strategy.strategy_type.value}")
        logger.info(f"  활성화: {strategy.enabled}")
        logger.info(f"  가중치: {strategy.weight}")
        
        if hasattr(strategy, 'short_period'):
            logger.info(f"  단기 기간: {strategy.short_period}")
            logger.info(f"  장기 기간: {strategy.long_period}")
            logger.info(f"  최소 크로스 임계값: {strategy.min_cross_threshold}")
        
        if hasattr(strategy, 'rsi_period'):
            logger.info(f"  RSI 기간: {strategy.rsi_period}")
            logger.info(f"  과매도 임계값: {strategy.oversold_threshold}")
            logger.info(f"  과매수 임계값: {strategy.overbought_threshold}")

def main():
    """메인 디버깅 함수"""
    logger.info("신호 생성 디버깅 시작")
    
    try:
        # 1. 전략 파라미터 확인
        debug_strategy_parameters()
        
        # 2. 신호 생성 과정 디버깅
        success = debug_signal_generation()
        
        # 결과 요약
        logger.info(f"\n=== 디버깅 완료 ===")
        if success:
            logger.info("✅ 신호 생성이 정상적으로 작동합니다!")
        else:
            logger.error("❌ 신호 생성에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"디버깅 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 