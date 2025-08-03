#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성과 최적화 스크립트
현재 전략들의 성과를 분석하고 파라미터를 최적화합니다.
"""

import sys
import os
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies, StrategyConfig, StrategyType

def analyze_current_performance():
    """현재 성과 분석"""
    logger.info("=== 현재 성과 분석 시작 ===")
    
    # 기본 백테스트 실행
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=1000,
        max_positions=20,
        position_size_ratio=0.02
    )
    
    engine = BacktestingEngine(config)
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 현재 성과 분석 결과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        logger.info(f"소르티노 비율: {result.sortino_ratio:.2f}")
        
        # 전략별 성과 분석
        logger.info("\n=== 전략별 성과 분석 ===")
        for name, perf in result.strategy_performance.items():
            logger.info(f"{name}:")
            logger.info(f"  총 신호 수: {perf.get('total_signals', 0)}")
            logger.info(f"  성공률: {perf.get('success_rate', 0):.2f}%")
            logger.info(f"  총 수익: {perf.get('total_profit', 0):,.0f}원")
            logger.info(f"  평균 수익: {perf.get('avg_profit', 0):,.0f}원")
        
        return result
    else:
        logger.error("백테스트 실행 실패")
        return None

def optimize_ma_crossover():
    """이동평균 크로스오버 전략 최적화"""
    logger.info("=== MA Crossover 전략 최적화 시작 ===")
    
    # 테스트할 파라미터 조합
    short_periods = [1, 2, 3, 5, 7, 10]
    long_periods = [5, 7, 10, 15, 20, 25]
    thresholds = [0.00001, 0.0001, 0.001, 0.01]
    
    best_result = None
    best_params = None
    best_sharpe = -999
    
    total_combinations = len(short_periods) * len(long_periods) * len(thresholds)
    logger.info(f"총 {total_combinations}개 조합 테스트 예정")
    
    for i, (short, long, threshold) in enumerate(product(short_periods, long_periods, thresholds)):
        if short >= long:  # short < long 조건 확인
            continue
            
        logger.info(f"테스트 {i+1}: short={short}, long={long}, threshold={threshold}")
        
        # 전략 생성
        config = StrategyConfig(
            strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
            parameters={'short_period': short, 'long_period': long, 'min_cross_threshold': threshold}
        )
        
        # 백테스트 실행
        backtest_result = run_optimization_backtest(config)
        
        if backtest_result and backtest_result.sharpe_ratio > best_sharpe:
            best_sharpe = backtest_result.sharpe_ratio
            best_result = backtest_result
            best_params = {'short_period': short, 'long_period': long, 'min_cross_threshold': threshold}
            
            logger.info(f"새로운 최고 성과 발견!")
            logger.info(f"샤프 비율: {best_sharpe:.3f}")
            logger.info(f"수익률: {best_result.total_return:.2f}%")
            logger.info(f"승률: {best_result.win_rate:.2f}%")
    
    logger.info("=== MA Crossover 최적화 완료 ===")
    logger.info(f"최적 파라미터: {best_params}")
    logger.info(f"최고 샤프 비율: {best_sharpe:.3f}")
    
    return best_params, best_result

def optimize_rsi_strategy():
    """RSI 전략 최적화"""
    logger.info("=== RSI 전략 최적화 시작 ===")
    
    # 테스트할 파라미터 조합
    rsi_periods = [2, 3, 5, 7, 10, 14]
    oversold_levels = [20, 25, 30, 35, 40]
    overbought_levels = [60, 65, 70, 75, 80]
    confirmation_periods = [1, 2, 3]
    
    best_result = None
    best_params = None
    best_sharpe = -999
    
    total_combinations = len(rsi_periods) * len(oversold_levels) * len(overbought_levels) * len(confirmation_periods)
    logger.info(f"총 {total_combinations}개 조합 테스트 예정")
    
    for i, (period, oversold, overbought, confirm) in enumerate(product(rsi_periods, oversold_levels, overbought_levels, confirmation_periods)):
        if oversold >= overbought:  # oversold < overbought 조건 확인
            continue
            
        logger.info(f"테스트 {i+1}: period={period}, oversold={oversold}, overbought={overbought}, confirm={confirm}")
        
        # 전략 생성
        config = StrategyConfig(
            strategy_type=StrategyType.RSI_STRATEGY,
            parameters={
                'rsi_period': period,
                'oversold_threshold': oversold,
                'overbought_threshold': overbought,
                'confirmation_period': confirm
            }
        )
        
        # 백테스트 실행
        backtest_result = run_optimization_backtest(config)
        
        if backtest_result and backtest_result.sharpe_ratio > best_sharpe:
            best_sharpe = backtest_result.sharpe_ratio
            best_result = backtest_result
            best_params = {
                'rsi_period': period,
                'oversold_threshold': oversold,
                'overbought_threshold': overbought,
                'confirmation_period': confirm
            }
            
            logger.info(f"새로운 최고 성과 발견!")
            logger.info(f"샤프 비율: {best_sharpe:.3f}")
            logger.info(f"수익률: {best_result.total_return:.2f}%")
            logger.info(f"승률: {best_result.win_rate:.2f}%")
    
    logger.info("=== RSI 최적화 완료 ===")
    logger.info(f"최적 파라미터: {best_params}")
    logger.info(f"최고 샤프 비율: {best_sharpe:.3f}")
    
    return best_params, best_result

def run_optimization_backtest(strategy_config):
    """최적화용 백테스트 실행"""
    try:
        config = BacktestConfig(
            mode=BacktestMode.SINGLE_STOCK,
            start_date="2023-02-15",
            end_date="2023-12-28",
            initial_capital=10000000,
            commission_rate=0.0001,
            slippage_rate=0.00005,
            min_trade_amount=1000,
            max_positions=20,
            position_size_ratio=0.02
        )
        
        engine = BacktestingEngine(config)
        
        # 단일 전략으로 테스트
        from trading_strategy import StrategyManager
        strategy_manager = StrategyManager()
        
        # 전략 타입에 따라 전략 생성
        if strategy_config.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
            from trading_strategy import MovingAverageCrossoverStrategy
            strategy = MovingAverageCrossoverStrategy(strategy_config)
            strategy_manager.add_strategy('MA_Crossover', strategy)
        elif strategy_config.strategy_type == StrategyType.RSI_STRATEGY:
            from trading_strategy import RSIStrategy
            strategy = RSIStrategy(strategy_config)
            strategy_manager.add_strategy('RSI', strategy)
        
        engine.add_strategy(strategy_manager)
        
        # 데이터 로드
        success = engine.load_data(['005930.KS'], data_source="yahoo")
        if not success:
            return None
        
        # 백테스트 실행
        result = engine.run_backtest()
        return result
        
    except Exception as e:
        logger.error(f"최적화 백테스트 오류: {e}")
        return None

def create_optimized_strategies():
    """최적화된 전략들 생성"""
    logger.info("=== 최적화된 전략 생성 ===")
    
    # 최적화된 파라미터 (실제 최적화 결과로 대체 예정)
    optimized_ma_params = {'short_period': 3, 'long_period': 10, 'min_cross_threshold': 0.001}
    optimized_rsi_params = {
        'rsi_period': 5, 
        'oversold_threshold': 30, 
        'overbought_threshold': 70,
        'confirmation_period': 2
    }
    
    # 최적화된 전략 생성
    ma_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters=optimized_ma_params
    )
    
    rsi_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters=optimized_rsi_params
    )
    
    # 전략 매니저에 추가
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy
    
    strategy_manager = StrategyManager()
    
    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    rsi_strategy = RSIStrategy(rsi_config)
    
    strategy_manager.add_strategy('MA_Crossover_Optimized', ma_strategy)
    strategy_manager.add_strategy('RSI_Optimized', rsi_strategy)
    
    return strategy_manager

def test_optimized_strategies():
    """최적화된 전략 테스트"""
    logger.info("=== 최적화된 전략 테스트 ===")
    
    # 최적화된 전략 생성
    optimized_strategies = create_optimized_strategies()
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=1000,
        max_positions=20,
        position_size_ratio=0.02
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(optimized_strategies)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 최적화된 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("최적화된 전략 테스트 실패")
        return None

def main():
    """메인 함수"""
    logger.info("성과 최적화 작업 시작")
    
    # 1. 현재 성과 분석
    current_result = analyze_current_performance()
    
    if not current_result:
        logger.error("현재 성과 분석 실패")
        return
    
    # 2. 전략별 최적화 (시간이 오래 걸리므로 선택적으로 실행)
    logger.info("\n전략 최적화를 시작하시겠습니까? (시간이 오래 걸립니다)")
    
    # 3. 최적화된 전략 테스트
    optimized_result = test_optimized_strategies()
    
    if optimized_result:
        logger.info("\n=== 최적화 결과 비교 ===")
        logger.info("현재 전략:")
        logger.info(f"  수익률: {current_result.total_return:.2f}%")
        logger.info(f"  승률: {current_result.win_rate:.2f}%")
        logger.info(f"  샤프 비율: {current_result.sharpe_ratio:.2f}")
        
        logger.info("최적화된 전략:")
        logger.info(f"  수익률: {optimized_result.total_return:.2f}%")
        logger.info(f"  승률: {optimized_result.win_rate:.2f}%")
        logger.info(f"  샤프 비율: {optimized_result.sharpe_ratio:.2f}")
        
        # 개선도 계산
        improvement_return = optimized_result.total_return - current_result.total_return
        improvement_sharpe = optimized_result.sharpe_ratio - current_result.sharpe_ratio
        
        logger.info(f"\n개선도:")
        logger.info(f"  수익률 개선: {improvement_return:+.2f}%")
        logger.info(f"  샤프 비율 개선: {improvement_sharpe:+.3f}")
    
    logger.info("성과 최적화 작업 완료")

if __name__ == "__main__":
    main() 