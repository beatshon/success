#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 백테스팅 시스템 디버깅
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies
from real_stock_data_api import DataManager, StockDataAPI

def debug_main_backtest_flow():
    """메인 백테스팅 시스템의 전체 흐름 디버깅"""
    logger.info("=== 메인 백테스팅 시스템 디버깅 시작 ===")
    
    # 1. 설정 초기화
    config = BacktestConfig(
        initial_capital=10000000,  # 1천만원
        commission_rate=0.0001,    # 0.01%
        slippage_rate=0.00005,     # 0.005%
        min_trade_amount=10000,    # 1만원
        max_positions=10,          # 최대 10개 포지션
        position_size_ratio=0.1,   # 10%
        stop_loss_rate=0.05,       # 5%
        take_profit_rate=0.1       # 10%
    )
    
    # 2. 백테스팅 엔진 초기화
    engine = BacktestingEngine(config)
    logger.info(f"백테스팅 엔진 초기화 완료: 초기 자본 {config.initial_capital:,}원")
    
    # 3. 전략 매니저 생성
    strategy_manager = create_default_strategies()
    logger.info(f"전략 매니저 생성 완료: {len(strategy_manager.strategies)}개 전략")
    
    # 4. 샘플 데이터 생성 (더 큰 데이터)
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    # 더 큰 변동성을 가진 샘플 데이터 생성
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    base_price = 50000
    returns = np.random.normal(0.001, 0.03, len(dates))  # 더 큰 변동성
    prices = [base_price]
    
    for i in range(1, len(dates)):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1000))  # 최소 가격 보장
    
    sample_data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    sample_data.set_index('Date', inplace=True)
    logger.info(f"샘플 데이터 생성 완료: {len(sample_data)}일, 가격 범위: {sample_data['Close'].min():,.0f}~{sample_data['Close'].max():,.0f}원")
    
    # 5. 데이터를 엔진에 로드
    engine.data = {'KTEST': sample_data}
    logger.info("데이터를 엔진에 로드 완료")
    
    # 6. 전략 매니저를 엔진에 추가
    engine.add_strategy(strategy_manager)
    logger.info("전략 매니저를 엔진에 추가 완료")
    
    # 7. 각 전략별로 데이터 추가 확인
    logger.info("\n=== 전략별 데이터 추가 확인 ===")
    for name, strategy in strategy_manager.strategies.items():
        strategy.price_history = []  # 초기화
        logger.info(f"\n{name} 전략:")
        logger.info(f"  - 전략 타입: {strategy.config.strategy_type}")
        logger.info(f"  - 파라미터: {strategy.config.parameters}")
        
        # 데이터 추가
        for date, row in sample_data.iterrows():
            strategy.add_data(date, row)
        
        logger.info(f"  - 추가된 데이터: {len(strategy.price_history)}개")
        if len(strategy.price_history) > 0:
            logger.info(f"  - 첫 번째 데이터: {strategy.price_history[0]}")
            logger.info(f"  - 마지막 데이터: {strategy.price_history[-1]}")
    
    # 8. 일별 신호 생성 테스트
    logger.info("\n=== 일별 신호 생성 테스트 ===")
    total_signals = 0
    
    for i, (date, row) in enumerate(sample_data.iterrows()):
        if i < 30:  # 처음 30일은 건너뛰기
            continue
            
        signals = engine._generate_signals(date)
        if signals:
            logger.info(f"{date.strftime('%Y-%m-%d')}: {len(signals)}개 신호 생성")
            for signal in signals:
                logger.info(f"  - {signal.strategy_name}: {signal.signal_type} (신뢰도: {signal.confidence:.3f})")
            total_signals += len(signals)
    
    logger.info(f"\n총 생성된 신호: {total_signals}개")
    
    # 9. 백테스트 실행
    if total_signals > 0:
        logger.info("\n=== 백테스트 실행 ===")
        try:
            result = engine.run_backtest()
            
            logger.info(f"백테스트 완료:")
            logger.info(f"  - 총 거래: {result.total_trades}개")
            logger.info(f"  - 승률: {result.win_rate:.2f}%")
            logger.info(f"  - 총 수익률: {result.total_return:.2f}%")
            logger.info(f"  - 최대 낙폭: {result.max_drawdown:.2f}%")
            
        except Exception as e:
            logger.error(f"백테스트 실행 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.warning("신호가 생성되지 않아 백테스트를 건너뜁니다.")
    
    return total_signals > 0

def main():
    """메인 함수"""
    logger.info("메인 백테스팅 시스템 디버깅 시작")
    try:
        success = debug_main_backtest_flow()
        logger.info(f"\n=== 디버깅 완료 ===")
        if success:
            logger.info("✅ 메인 백테스팅 시스템이 정상적으로 작동합니다!")
        else:
            logger.error("❌ 메인 백테스팅 시스템에 문제가 있습니다.")
    except Exception as e:
        logger.error(f"디버깅 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 