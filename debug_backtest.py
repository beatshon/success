#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백테스팅 시스템 디버그 스크립트
문제점을 찾아서 수정합니다.
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
from real_stock_data_api import StockDataAPI

def test_data_loading():
    """데이터 로딩 테스트"""
    logger.info("=== 데이터 로딩 테스트 ===")
    
    # API 초기화
    api = StockDataAPI(data_source="yahoo")
    
    # 테스트 종목
    test_codes = ["005930.KS", "000660.KS", "035420.KS"]
    
    for code in test_codes:
        logger.info(f"종목 {code} 데이터 로드 중...")
        try:
            data = api.get_stock_data(code, "2023-01-01", "2023-12-31")
            if data is not None and not data.empty:
                logger.info(f"✅ {code}: {len(data)}개 데이터 로드 성공")
                logger.info(f"   컬럼: {list(data.columns)}")
                logger.info(f"   첫 번째 데이터: {data.iloc[0]}")
                logger.info(f"   마지막 데이터: {data.iloc[-1]}")
            else:
                logger.warning(f"❌ {code}: 데이터 없음")
        except Exception as e:
            logger.error(f"❌ {code}: 오류 발생 - {e}")

def test_strategy_signals():
    """전략 신호 생성 테스트"""
    logger.info("\n=== 전략 신호 생성 테스트 ===")
    
    # 전략 매니저 생성
    strategy_manager = create_default_strategies()
    
    # 샘플 데이터 생성
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    prices = [100 + i * 0.1 + np.random.normal(0, 1) for i in range(len(dates))]
    
    sample_data = pd.DataFrame({
        'open': prices,
        'high': [p + np.random.uniform(0, 2) for p in prices],
        'low': [p - np.random.uniform(0, 2) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 10000) for _ in prices]
    }, index=dates)
    
    logger.info(f"샘플 데이터 생성: {len(sample_data)}개")
    
    # 전략에 데이터 추가
    for name, strategy in strategy_manager.strategies.items():
        logger.info(f"\n{name} 전략 테스트:")
        
        # 데이터 추가
        for date, row in sample_data.iterrows():
            strategy.add_data(date, row)
        
        logger.info(f"  데이터 추가 완료: {len(strategy.price_history)}개")
        
        # 신호 생성 테스트
        signal = strategy.generate_signal()
        if signal:
            logger.info(f"  ✅ 신호 생성: {signal.signal_type} (신뢰도: {signal.confidence:.2f})")
        else:
            logger.info(f"  ❌ 신호 없음")

def test_backtest_engine():
    """백테스트 엔진 테스트"""
    logger.info("\n=== 백테스트 엔진 테스트 ===")
    
    from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
    
    # 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000
    )
    
    # 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    logger.info("데이터 로드 중...")
    success = engine.load_data(codes=["005930.KS"], data_source="yahoo")
    
    if success:
        logger.info("✅ 데이터 로드 성공")
        
        # 백테스트 실행
        logger.info("백테스트 실행 중...")
        try:
            result = engine.run_backtest()
            if result:
                logger.info("✅ 백테스트 성공")
                logger.info(f"총 거래 수: {result.total_trades}")
                logger.info(f"최종 자본: {result.final_capital:,.0f}원")
                logger.info(f"총 수익률: {result.total_return:.2f}%")
            else:
                logger.error("❌ 백테스트 실패")
        except Exception as e:
            logger.error(f"❌ 백테스트 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.error("❌ 데이터 로드 실패")

def main():
    """메인 함수"""
    logger.info("백테스팅 시스템 디버그 시작")
    
    # 1. 데이터 로딩 테스트
    test_data_loading()
    
    # 2. 전략 신호 생성 테스트
    test_strategy_signals()
    
    # 3. 백테스트 엔진 테스트
    test_backtest_engine()
    
    logger.info("디버그 완료")

if __name__ == "__main__":
    main() 