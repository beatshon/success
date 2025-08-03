#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 성과 최적화 스크립트
더 정교한 파라미터 최적화와 포트폴리오 최적화를 수행합니다.
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
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies, StrategyConfig, StrategyType

def analyze_performance_issues():
    """성과 문제점 분석"""
    logger.info("=== 성과 문제점 분석 ===")
    
    # 현재 전략의 문제점 분석
    logger.info("1. 현재 전략 파라미터가 너무 짧음:")
    logger.info("   - MA: short=1, long=2 (너무 짧음)")
    logger.info("   - RSI: period=2 (너무 짧음)")
    logger.info("   - BB: period=5 (너무 짧음)")
    logger.info("   - MACD: fast=2, slow=3 (너무 짧음)")
    
    logger.info("\n2. 문제점:")
    logger.info("   - 노이즈에 민감함")
    logger.info("   - 허위 신호가 많음")
    logger.info("   - 실제 트렌드를 포착하지 못함")
    logger.info("   - 과도한 거래로 수수료 손실")
    
    logger.info("\n3. 개선 방향:")
    logger.info("   - 더 긴 기간의 파라미터 사용")
    logger.info("   - 신호 필터링 강화")
    logger.info("   - 포지션 사이징 최적화")
    logger.info("   - 리스크 관리 개선")

def create_stable_strategies():
    """안정적인 전략 생성"""
    logger.info("=== 안정적인 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandsStrategy, MACDStrategy
    
    strategy_manager = StrategyManager()
    
    # 1. 안정적인 이동평균 크로스오버
    ma_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 10,      # 10일 이동평균
            'long_period': 30,       # 30일 이동평균
            'min_cross_threshold': 0.01  # 1% 임계값
        }
    )
    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    strategy_manager.add_strategy('MA_Stable', ma_strategy)
    
    # 2. 안정적인 RSI
    rsi_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 14,        # 표준 14일
            'oversold_threshold': 30, # 과매도
            'overbought_threshold': 70, # 과매수
            'confirmation_period': 3   # 3일 확인
        }
    )
    rsi_strategy = RSIStrategy(rsi_config)
    strategy_manager.add_strategy('RSI_Stable', rsi_strategy)
    
    # 3. 안정적인 볼린저 밴드
    bb_config = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={
            'period': 20,            # 20일
            'std_dev': 2.0,          # 2 표준편차
            'min_touch_threshold': 0.01  # 1% 임계값
        }
    )
    bb_strategy = BollingerBandsStrategy(bb_config)
    strategy_manager.add_strategy('BB_Stable', bb_strategy)
    
    # 4. 안정적인 MACD
    macd_config = StrategyConfig(
        strategy_type=StrategyType.MACD_STRATEGY,
        parameters={
            'fast_period': 12,       # 12일
            'slow_period': 26,       # 26일
            'signal_period': 9       # 9일
        }
    )
    macd_strategy = MACDStrategy(macd_config)
    strategy_manager.add_strategy('MACD_Stable', macd_strategy)
    
    return strategy_manager

def test_stable_strategies():
    """안정적인 전략 테스트"""
    logger.info("=== 안정적인 전략 테스트 ===")
    
    # 안정적인 전략 생성
    stable_strategies = create_stable_strategies()
    
    # 백테스트 설정 (더 보수적)
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,      # 최소 거래 금액 증가
        max_positions=5,             # 최대 포지션 수 감소
        position_size_ratio=0.1,     # 포지션 크기 증가
        stop_loss_rate=0.05,         # 5% 손절
        take_profit_rate=0.15        # 15% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(stable_strategies)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 안정적인 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("안정적인 전략 테스트 실패")
        return None

def optimize_portfolio_weights():
    """포트폴리오 가중치 최적화"""
    logger.info("=== 포트폴리오 가중치 최적화 ===")
    
    # 여러 종목으로 포트폴리오 테스트
    test_stocks = ['005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS']
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,
        max_positions=10,
        position_size_ratio=0.05
    )
    
    engine = BacktestingEngine(config)
    
    # 안정적인 전략 사용
    stable_strategies = create_stable_strategies()
    engine.add_strategy(stable_strategies)
    
    # 데이터 로드
    success = engine.load_data(test_stocks, data_source="yahoo")
    if not success:
        logger.error("포트폴리오 데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 포트폴리오 최적화 결과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("포트폴리오 최적화 실패")
        return None

def create_hybrid_strategy():
    """하이브리드 전략 생성 (여러 전략 조합)"""
    logger.info("=== 하이브리드 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy
    
    strategy_manager = StrategyManager()
    
    # 1. 트렌드 추종 전략 (MA Crossover)
    trend_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 20,
            'long_period': 50,
            'min_cross_threshold': 0.02
        }
    )
    trend_strategy = MovingAverageCrossoverStrategy(trend_config)
    strategy_manager.add_strategy('Trend_Following', trend_strategy)
    
    # 2. 반전 전략 (RSI)
    reversal_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 14,
            'oversold_threshold': 25,
            'overbought_threshold': 75,
            'confirmation_period': 2
        }
    )
    reversal_strategy = RSIStrategy(reversal_config)
    strategy_manager.add_strategy('Reversal', reversal_strategy)
    
    return strategy_manager

def test_hybrid_strategy():
    """하이브리드 전략 테스트"""
    logger.info("=== 하이브리드 전략 테스트 ===")
    
    # 하이브리드 전략 생성
    hybrid_strategies = create_hybrid_strategy()
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,
        max_positions=3,
        position_size_ratio=0.15
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(hybrid_strategies)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 하이브리드 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("하이브리드 전략 테스트 실패")
        return None

def create_risk_managed_strategy():
    """리스크 관리가 강화된 전략"""
    logger.info("=== 리스크 관리 강화 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 보수적인 이동평균 크로스오버
    config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 50,      # 50일 이동평균
            'long_period': 200,      # 200일 이동평균
            'min_cross_threshold': 0.05  # 5% 임계값
        }
    )
    strategy = MovingAverageCrossoverStrategy(config)
    strategy_manager.add_strategy('Conservative_MA', strategy)
    
    return strategy_manager

def test_risk_managed_strategy():
    """리스크 관리 전략 테스트"""
    logger.info("=== 리스크 관리 전략 테스트 ===")
    
    # 리스크 관리 전략 생성
    risk_strategies = create_risk_managed_strategy()
    
    # 매우 보수적인 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=100000,     # 10만원 최소 거래
        max_positions=2,             # 최대 2개 포지션
        position_size_ratio=0.2,     # 20% 포지션 크기
        stop_loss_rate=0.03,         # 3% 손절
        take_profit_rate=0.10        # 10% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(risk_strategies)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 리스크 관리 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("리스크 관리 전략 테스트 실패")
        return None

def compare_all_strategies():
    """모든 전략 비교"""
    logger.info("=== 모든 전략 비교 ===")
    
    results = {}
    
    # 1. 현재 전략 (기본)
    logger.info("1. 현재 전략 테스트 중...")
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
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if success:
        result = engine.run_backtest()
        if result:
            results['현재 전략'] = result
    
    # 2. 안정적인 전략
    logger.info("2. 안정적인 전략 테스트 중...")
    stable_result = test_stable_strategies()
    if stable_result:
        results['안정적인 전략'] = stable_result
    
    # 3. 하이브리드 전략
    logger.info("3. 하이브리드 전략 테스트 중...")
    hybrid_result = test_hybrid_strategy()
    if hybrid_result:
        results['하이브리드 전략'] = hybrid_result
    
    # 4. 리스크 관리 전략
    logger.info("4. 리스크 관리 전략 테스트 중...")
    risk_result = test_risk_managed_strategy()
    if risk_result:
        results['리스크 관리 전략'] = risk_result
    
    # 결과 비교
    logger.info("\n=== 전략별 성과 비교 ===")
    for name, result in results.items():
        logger.info(f"\n{name}:")
        logger.info(f"  거래 수: {result.total_trades}회")
        logger.info(f"  승률: {result.win_rate:.2f}%")
        logger.info(f"  수익률: {result.total_return:.2f}%")
        logger.info(f"  샤프 비율: {result.sharpe_ratio:.2f}")
        logger.info(f"  최대 낙폭: {result.max_drawdown:.2f}%")
    
    # 최고 성과 전략 찾기
    best_strategy = None
    best_sharpe = -999
    
    for name, result in results.items():
        if result.sharpe_ratio > best_sharpe:
            best_sharpe = result.sharpe_ratio
            best_strategy = name
    
    logger.info(f"\n🎯 최고 성과 전략: {best_strategy}")
    logger.info(f"   샤프 비율: {best_sharpe:.2f}")
    
    return results, best_strategy

def main():
    """메인 함수"""
    logger.info("고급 성과 최적화 시작")
    
    # 1. 문제점 분석
    analyze_performance_issues()
    
    # 2. 모든 전략 비교
    results, best_strategy = compare_all_strategies()
    
    # 3. 최적화 권장사항
    logger.info("\n=== 최적화 권장사항 ===")
    logger.info("1. 파라미터 안정화:")
    logger.info("   - 더 긴 기간의 이동평균 사용 (10-30일)")
    logger.info("   - 표준 RSI 기간 사용 (14일)")
    logger.info("   - 더 높은 임계값 설정")
    
    logger.info("\n2. 거래 관리 개선:")
    logger.info("   - 최소 거래 금액 증가")
    logger.info("   - 포지션 크기 최적화")
    logger.info("   - 손절/익절 설정")
    
    logger.info("\n3. 포트폴리오 다각화:")
    logger.info("   - 여러 종목 분산 투자")
    logger.info("   - 섹터별 분산")
    logger.info("   - 리스크 관리 강화")
    
    logger.info(f"\n✅ 최적 전략: {best_strategy}")
    logger.info("고급 성과 최적화 완료")

if __name__ == "__main__":
    main() 