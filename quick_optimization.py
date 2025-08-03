#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 성과 최적화 스크립트
핵심 문제점만 해결하는 간단한 최적화를 수행합니다.
"""

import sys
import os
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies, StrategyConfig, StrategyType

def analyze_current_issues():
    """현재 문제점 분석"""
    logger.info("=== 현재 문제점 분석 ===")
    
    # 현재 전략의 문제점
    logger.info("1. 파라미터가 너무 짧음:")
    logger.info("   - MA: short=1, long=2 (노이즈에 민감)")
    logger.info("   - RSI: period=2 (너무 짧음)")
    logger.info("   - BB: period=5 (너무 짧음)")
    logger.info("   - MACD: fast=2, slow=3 (너무 짧음)")
    
    logger.info("\n2. 거래 설정 문제:")
    logger.info("   - 최소 거래 금액이 너무 낮음 (1,000원)")
    logger.info("   - 포지션 크기가 너무 작음 (2%)")
    logger.info("   - 과도한 거래로 수수료 손실")
    
    logger.info("\n3. 개선 방향:")
    logger.info("   - 더 긴 기간의 파라미터 사용")
    logger.info("   - 최소 거래 금액 증가")
    logger.info("   - 포지션 크기 최적화")

def create_improved_strategies():
    """개선된 전략 생성"""
    logger.info("=== 개선된 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy
    
    strategy_manager = StrategyManager()
    
    # 1. 개선된 이동평균 크로스오버 (더 긴 기간)
    ma_config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 5,       # 5일 이동평균
            'long_period': 20,       # 20일 이동평균
            'min_cross_threshold': 0.01  # 1% 임계값
        }
    )
    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    strategy_manager.add_strategy('MA_Improved', ma_strategy)
    
    # 2. 개선된 RSI (표준 기간)
    rsi_config = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 14,        # 표준 14일
            'oversold_threshold': 30, # 과매도
            'overbought_threshold': 70, # 과매수
            'confirmation_period': 2   # 2일 확인
        }
    )
    rsi_strategy = RSIStrategy(rsi_config)
    strategy_manager.add_strategy('RSI_Improved', rsi_strategy)
    
    return strategy_manager

def test_improved_strategies():
    """개선된 전략 테스트"""
    logger.info("=== 개선된 전략 테스트 ===")
    
    # 개선된 전략 생성
    improved_strategies = create_improved_strategies()
    
    # 개선된 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,      # 5만원으로 증가
        max_positions=5,             # 최대 포지션 수 감소
        position_size_ratio=0.1,     # 10%로 증가
        stop_loss_rate=0.05,         # 5% 손절
        take_profit_rate=0.15        # 15% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(improved_strategies)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 개선된 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("개선된 전략 테스트 실패")
        return None

def test_conservative_strategy():
    """보수적인 전략 테스트"""
    logger.info("=== 보수적인 전략 테스트 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 매우 보수적인 이동평균 크로스오버
    config = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 20,      # 20일 이동평균
            'long_period': 50,       # 50일 이동평균
            'min_cross_threshold': 0.02  # 2% 임계값
        }
    )
    strategy = MovingAverageCrossoverStrategy(config)
    strategy_manager.add_strategy('Conservative_MA', strategy)
    
    # 보수적인 백테스트 설정
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
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 보수적인 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("보수적인 전략 테스트 실패")
        return None

def compare_strategies():
    """전략 비교"""
    logger.info("=== 전략 비교 ===")
    
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
    
    # 2. 개선된 전략
    logger.info("2. 개선된 전략 테스트 중...")
    improved_result = test_improved_strategies()
    if improved_result:
        results['개선된 전략'] = improved_result
    
    # 3. 보수적인 전략
    logger.info("3. 보수적인 전략 테스트 중...")
    conservative_result = test_conservative_strategy()
    if conservative_result:
        results['보수적인 전략'] = conservative_result
    
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

def generate_optimization_report():
    """최적화 리포트 생성"""
    logger.info("=== 최적화 리포트 생성 ===")
    
    logger.info("\n📊 최적화 권장사항:")
    logger.info("1. 파라미터 개선:")
    logger.info("   - MA: short=5-20일, long=20-50일")
    logger.info("   - RSI: period=14일 (표준)")
    logger.info("   - 더 높은 임계값 설정")
    
    logger.info("\n2. 거래 관리 개선:")
    logger.info("   - 최소 거래 금액: 5만원 이상")
    logger.info("   - 포지션 크기: 10-20%")
    logger.info("   - 손절: 3-5%, 익절: 10-15%")
    
    logger.info("\n3. 리스크 관리:")
    logger.info("   - 최대 포지션 수: 2-5개")
    logger.info("   - 포트폴리오 다각화")
    logger.info("   - 정기적인 성과 모니터링")

def main():
    """메인 함수"""
    logger.info("빠른 성과 최적화 시작")
    
    # 1. 문제점 분석
    analyze_current_issues()
    
    # 2. 전략 비교
    results, best_strategy = compare_strategies()
    
    # 3. 최적화 리포트 생성
    generate_optimization_report()
    
    logger.info(f"\n✅ 최적 전략: {best_strategy}")
    logger.info("빠른 성과 최적화 완료")

if __name__ == "__main__":
    main() 