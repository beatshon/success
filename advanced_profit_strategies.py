#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수익률 향상을 위한 고급 전략 개발
포트폴리오 최적화, 동적 자산 배분, 고급 필터링 등을 구현합니다.
"""

import sys
import os
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies, StrategyConfig, StrategyType

def create_momentum_strategy():
    """모멘텀 기반 전략 생성"""
    logger.info("=== 모멘텀 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 단기 모멘텀 전략 (5일 vs 10일)
    short_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 5,
            'long_period': 10,
            'min_cross_threshold': 0.005  # 0.5% 임계값
        }
    )
    short_strategy = MovingAverageCrossoverStrategy(short_momentum)
    strategy_manager.add_strategy('Short_Momentum', short_strategy)
    
    # 중기 모멘텀 전략 (10일 vs 20일)
    medium_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 10,
            'long_period': 20,
            'min_cross_threshold': 0.01  # 1% 임계값
        }
    )
    medium_strategy = MovingAverageCrossoverStrategy(medium_momentum)
    strategy_manager.add_strategy('Medium_Momentum', medium_strategy)
    
    return strategy_manager

def create_volatility_breakout_strategy():
    """변동성 돌파 전략 생성"""
    logger.info("=== 변동성 돌파 전략 생성 ===")
    
    from trading_strategy import StrategyManager, BollingerBandsStrategy
    
    strategy_manager = StrategyManager()
    
    # 변동성 돌파 전략 (낮은 기간, 높은 표준편차)
    volatility_breakout = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={
            'period': 10,            # 10일
            'std_dev': 2.5,          # 2.5 표준편차
            'min_touch_threshold': 0.005  # 0.5% 임계값
        }
    )
    breakout_strategy = BollingerBandsStrategy(volatility_breakout)
    strategy_manager.add_strategy('Volatility_Breakout', breakout_strategy)
    
    return strategy_manager

def create_trend_following_strategy():
    """트렌드 추종 전략 생성"""
    logger.info("=== 트렌드 추종 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 강한 트렌드 추종 전략
    strong_trend = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 20,
            'long_period': 60,
            'min_cross_threshold': 0.02  # 2% 임계값
        }
    )
    trend_strategy = MovingAverageCrossoverStrategy(strong_trend)
    strategy_manager.add_strategy('Strong_Trend', trend_strategy)
    
    return strategy_manager

def test_momentum_strategy():
    """모멘텀 전략 테스트"""
    logger.info("=== 모멘텀 전략 테스트 ===")
    
    momentum_strategies = create_momentum_strategy()
    
    # 모멘텀 전략에 최적화된 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=30000,      # 3만원
        max_positions=8,             # 8개 포지션
        position_size_ratio=0.08,    # 8% 포지션 크기
        stop_loss_rate=0.03,         # 3% 손절
        take_profit_rate=0.08        # 8% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(momentum_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 모멘텀 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("모멘텀 전략 테스트 실패")
        return None

def test_volatility_breakout_strategy():
    """변동성 돌파 전략 테스트"""
    logger.info("=== 변동성 돌파 전략 테스트 ===")
    
    breakout_strategies = create_volatility_breakout_strategy()
    
    # 변동성 돌파에 최적화된 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=20000,      # 2만원
        max_positions=10,            # 10개 포지션
        position_size_ratio=0.06,    # 6% 포지션 크기
        stop_loss_rate=0.04,         # 4% 손절
        take_profit_rate=0.12        # 12% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(breakout_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 변동성 돌파 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("변동성 돌파 전략 테스트 실패")
        return None

def test_trend_following_strategy():
    """트렌드 추종 전략 테스트"""
    logger.info("=== 트렌드 추종 전략 테스트 ===")
    
    trend_strategies = create_trend_following_strategy()
    
    # 트렌드 추종에 최적화된 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,      # 5만원
        max_positions=4,             # 4개 포지션
        position_size_ratio=0.15,    # 15% 포지션 크기
        stop_loss_rate=0.05,         # 5% 손절
        take_profit_rate=0.15        # 15% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(trend_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 트렌드 추종 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("트렌드 추종 전략 테스트 실패")
        return None

def test_portfolio_optimization():
    """포트폴리오 최적화 테스트"""
    logger.info("=== 포트폴리오 최적화 테스트 ===")
    
    # 다양한 종목으로 포트폴리오 구성
    portfolio_stocks = [
        '005930.KS',  # 삼성전자
        '000660.KS',  # SK하이닉스
        '035420.KS',  # NAVER
        '051910.KS',  # LG화학
        '006400.KS',  # 삼성SDI
        '035720.KS',  # 카카오
        '207940.KS',  # 삼성바이오로직스
        '068270.KS'   # 셀트리온
    ]
    
    # 모멘텀 전략 사용
    momentum_strategies = create_momentum_strategy()
    
    # 포트폴리오 최적화 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=20000,
        max_positions=15,
        position_size_ratio=0.04
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(momentum_strategies)
    
    success = engine.load_data(portfolio_stocks, data_source="yahoo")
    if not success:
        logger.error("포트폴리오 데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 포트폴리오 최적화 성과 ===")
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

def create_hybrid_high_profit_strategy():
    """고수익 하이브리드 전략 생성"""
    logger.info("=== 고수익 하이브리드 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandsStrategy
    
    strategy_manager = StrategyManager()
    
    # 1. 단기 모멘텀 (빠른 진입)
    short_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 3,
            'long_period': 8,
            'min_cross_threshold': 0.003
        }
    )
    short_strategy = MovingAverageCrossoverStrategy(short_momentum)
    strategy_manager.add_strategy('Fast_Momentum', short_strategy)
    
    # 2. RSI 과매수/과매도 (반전 기회 포착)
    rsi_reversal = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 7,
            'oversold_threshold': 25,
            'overbought_threshold': 75,
            'confirmation_period': 1
        }
    )
    rsi_strategy = RSIStrategy(rsi_reversal)
    strategy_manager.add_strategy('RSI_Reversal', rsi_strategy)
    
    # 3. 볼린저 밴드 돌파 (변동성 활용)
    bb_breakout = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={
            'period': 8,
            'std_dev': 2.0,
            'min_touch_threshold': 0.003
        }
    )
    bb_strategy = BollingerBandsStrategy(bb_breakout)
    strategy_manager.add_strategy('BB_Breakout', bb_strategy)
    
    return strategy_manager

def test_hybrid_high_profit_strategy():
    """고수익 하이브리드 전략 테스트"""
    logger.info("=== 고수익 하이브리드 전략 테스트 ===")
    
    hybrid_strategies = create_hybrid_high_profit_strategy()
    
    # 고수익을 위한 공격적 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=15000,      # 1.5만원
        max_positions=12,            # 12개 포지션
        position_size_ratio=0.05,    # 5% 포지션 크기
        stop_loss_rate=0.02,         # 2% 손절
        take_profit_rate=0.06        # 6% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(hybrid_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 고수익 하이브리드 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("고수익 하이브리드 전략 테스트 실패")
        return None

def compare_all_high_profit_strategies():
    """모든 고수익 전략 비교"""
    logger.info("=== 모든 고수익 전략 비교 ===")
    
    results = {}
    
    # 1. 모멘텀 전략
    logger.info("1. 모멘텀 전략 테스트 중...")
    momentum_result = test_momentum_strategy()
    if momentum_result:
        results['모멘텀 전략'] = momentum_result
    
    # 2. 변동성 돌파 전략
    logger.info("2. 변동성 돌파 전략 테스트 중...")
    breakout_result = test_volatility_breakout_strategy()
    if breakout_result:
        results['변동성 돌파 전략'] = breakout_result
    
    # 3. 트렌드 추종 전략
    logger.info("3. 트렌드 추종 전략 테스트 중...")
    trend_result = test_trend_following_strategy()
    if trend_result:
        results['트렌드 추종 전략'] = trend_result
    
    # 4. 고수익 하이브리드 전략
    logger.info("4. 고수익 하이브리드 전략 테스트 중...")
    hybrid_result = test_hybrid_high_profit_strategy()
    if hybrid_result:
        results['고수익 하이브리드 전략'] = hybrid_result
    
    # 5. 포트폴리오 최적화
    logger.info("5. 포트폴리오 최적화 테스트 중...")
    portfolio_result = test_portfolio_optimization()
    if portfolio_result:
        results['포트폴리오 최적화'] = portfolio_result
    
    # 결과 비교
    logger.info("\n=== 고수익 전략별 성과 비교 ===")
    for name, result in results.items():
        logger.info(f"\n{name}:")
        logger.info(f"  거래 수: {result.total_trades}회")
        logger.info(f"  승률: {result.win_rate:.2f}%")
        logger.info(f"  수익률: {result.total_return:.2f}%")
        logger.info(f"  샤프 비율: {result.sharpe_ratio:.2f}")
        logger.info(f"  최대 낙폭: {result.max_drawdown:.2f}%")
    
    # 최고 수익률 전략 찾기
    best_strategy = None
    best_return = -999
    
    for name, result in results.items():
        if result.total_return > best_return:
            best_return = result.total_return
            best_strategy = name
    
    logger.info(f"\n🏆 최고 수익률 전략: {best_strategy}")
    logger.info(f"   수익률: {best_return:.2f}%")
    
    return results, best_strategy

def generate_profit_optimization_report():
    """수익률 최적화 리포트 생성"""
    logger.info("=== 수익률 최적화 리포트 생성 ===")
    
    logger.info("\n📈 수익률 향상 전략:")
    logger.info("1. 모멘텀 전략:")
    logger.info("   - 단기/중기 모멘텀 조합")
    logger.info("   - 빠른 진입/청산")
    logger.info("   - 작은 손절, 빠른 익절")
    
    logger.info("\n2. 변동성 돌파 전략:")
    logger.info("   - 볼린저 밴드 돌파 활용")
    logger.info("   - 변동성 확대 시점 포착")
    logger.info("   - 높은 익절 목표")
    
    logger.info("\n3. 트렌드 추종 전략:")
    logger.info("   - 강한 트렌드에서만 거래")
    logger.info("   - 큰 포지션 크기")
    logger.info("   - 트렌드 지속 시 수익 극대화")
    
    logger.info("\n4. 포트폴리오 최적화:")
    logger.info("   - 다중 종목 분산 투자")
    logger.info("   - 섹터별 분산")
    logger.info("   - 리스크 분산 효과")
    
    logger.info("\n5. 하이브리드 전략:")
    logger.info("   - 여러 전략 조합")
    logger.info("   - 다양한 시장 상황 대응")
    logger.info("   - 수익 기회 극대화")

def main():
    """메인 함수"""
    logger.info("수익률 향상 고급 전략 개발 시작")
    
    # 1. 모든 고수익 전략 비교
    results, best_strategy = compare_all_high_profit_strategies()
    
    # 2. 수익률 최적화 리포트 생성
    generate_profit_optimization_report()
    
    logger.info(f"\n✅ 최고 수익률 전략: {best_strategy}")
    logger.info("수익률 향상 고급 전략 개발 완료")

def create_ultra_aggressive_strategy():
    """극도로 공격적인 전략 생성"""
    logger.info("=== 극도로 공격적인 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandsStrategy
    
    strategy_manager = StrategyManager()
    
    # 극단적으로 빠른 모멘텀 (2일 vs 5일)
    ultra_fast_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 2,
            'long_period': 5,
            'min_cross_threshold': 0.001  # 0.1% 임계값
        }
    )
    ultra_fast_strategy = MovingAverageCrossoverStrategy(ultra_fast_momentum)
    strategy_manager.add_strategy('Ultra_Fast_Momentum', ultra_fast_strategy)
    
    # 극단적으로 빠른 RSI (3일)
    ultra_fast_rsi = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 3,
            'oversold_threshold': 15,
            'overbought_threshold': 85,
            'confirmation_period': 1
        }
    )
    ultra_rsi_strategy = RSIStrategy(ultra_fast_rsi)
    strategy_manager.add_strategy('Ultra_Fast_RSI', ultra_rsi_strategy)
    
    # 극단적으로 공격적인 볼린저 밴드 (3일)
    ultra_aggressive_bb = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={
            'period': 3,
            'std_dev': 4.0,
            'min_touch_threshold': 0.001
        }
    )
    ultra_bb_strategy = BollingerBandsStrategy(ultra_aggressive_bb)
    strategy_manager.add_strategy('Ultra_Aggressive_BB', ultra_bb_strategy)
    
    return strategy_manager

def create_micro_trading_strategy():
    """마이크로 트레이딩 전략 생성"""
    logger.info("=== 마이크로 트레이딩 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 마이크로 모멘텀 (1일 vs 3일)
    micro_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 1,
            'long_period': 3,
            'min_cross_threshold': 0.0005  # 0.05% 임계값
        }
    )
    micro_strategy = MovingAverageCrossoverStrategy(micro_momentum)
    strategy_manager.add_strategy('Micro_Momentum', micro_strategy)
    
    return strategy_manager

def create_scalping_strategy():
    """스캘핑 전략 생성"""
    logger.info("=== 스캘핑 전략 생성 ===")
    
    from trading_strategy import StrategyManager, RSIStrategy, BollingerBandsStrategy
    
    strategy_manager = StrategyManager()
    
    # 스캘핑 RSI (2일)
    scalping_rsi = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 2,
            'oversold_threshold': 10,
            'overbought_threshold': 90,
            'confirmation_period': 1
        }
    )
    scalping_rsi_strategy = RSIStrategy(scalping_rsi)
    strategy_manager.add_strategy('Scalping_RSI', scalping_rsi_strategy)
    
    # 스캘핑 볼린저 밴드 (2일)
    scalping_bb = StrategyConfig(
        strategy_type=StrategyType.BOLLINGER_BANDS,
        parameters={
            'period': 2,
            'std_dev': 5.0,
            'min_touch_threshold': 0.0005
        }
    )
    scalping_bb_strategy = BollingerBandsStrategy(scalping_bb)
    strategy_manager.add_strategy('Scalping_BB', scalping_bb_strategy)
    
    return strategy_manager

def test_ultra_aggressive_strategy():
    """극도로 공격적인 전략 테스트"""
    logger.info("=== 극도로 공격적인 전략 테스트 ===")
    
    ultra_strategies = create_ultra_aggressive_strategy()
    
    # 극도로 공격적인 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=5000,       # 5천원
        max_positions=30,            # 30개 포지션
        position_size_ratio=0.02,    # 2% 포지션 크기
        stop_loss_rate=0.005,        # 0.5% 손절
        take_profit_rate=0.015       # 1.5% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(ultra_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 극도로 공격적인 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("극도로 공격적인 전략 테스트 실패")
        return None

def test_micro_trading_strategy():
    """마이크로 트레이딩 전략 테스트"""
    logger.info("=== 마이크로 트레이딩 전략 테스트 ===")
    
    micro_strategies = create_micro_trading_strategy()
    
    # 마이크로 트레이딩 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=3000,       # 3천원
        max_positions=50,            # 50개 포지션
        position_size_ratio=0.01,    # 1% 포지션 크기
        stop_loss_rate=0.003,        # 0.3% 손절
        take_profit_rate=0.008       # 0.8% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(micro_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 마이크로 트레이딩 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("마이크로 트레이딩 전략 테스트 실패")
        return None

def test_scalping_strategy():
    """스캘핑 전략 테스트"""
    logger.info("=== 스캘핑 전략 테스트 ===")
    
    scalping_strategies = create_scalping_strategy()
    
    # 스캘핑 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=2000,       # 2천원
        max_positions=100,           # 100개 포지션
        position_size_ratio=0.005,   # 0.5% 포지션 크기
        stop_loss_rate=0.002,        # 0.2% 손절
        take_profit_rate=0.005       # 0.5% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(scalping_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 스캘핑 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("스캘핑 전략 테스트 실패")
        return None

def test_mega_portfolio_optimization():
    """메가 포트폴리오 최적화 테스트"""
    logger.info("=== 메가 포트폴리오 최적화 테스트 ===")
    
    # 매우 다양한 종목으로 포트폴리오 구성
    mega_portfolio_stocks = [
        '005930.KS',  # 삼성전자
        '000660.KS',  # SK하이닉스
        '035420.KS',  # NAVER
        '051910.KS',  # LG화학
        '006400.KS',  # 삼성SDI
        '035720.KS',  # 카카오
        '207940.KS',  # 삼성바이오로직스
        '068270.KS',  # 셀트리온
        '323410.KS',  # 카카오뱅크
        '051900.KS',  # LG생활건강
        '006980.KS',  # 우성사료
        '017670.KS',  # SK텔레콤
        '035720.KS',  # 카카오
        '051910.KS',  # LG화학
        '006400.KS',  # 삼성SDI
        '035720.KS',  # 카카오
        '207940.KS',  # 삼성바이오로직스
        '068270.KS',  # 셀트리온
        '323410.KS',  # 카카오뱅크
        '051900.KS'   # LG생활건강
    ]
    
    # 극도로 공격적인 전략 사용
    ultra_strategies = create_ultra_aggressive_strategy()
    
    # 메가 포트폴리오 최적화 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=1000,
        max_positions=100,
        position_size_ratio=0.005,
        stop_loss_rate=0.002,
        take_profit_rate=0.005
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(ultra_strategies)
    
    success = engine.load_data(mega_portfolio_stocks, data_source="yahoo")
    if not success:
        logger.error("메가 포트폴리오 데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 메가 포트폴리오 최적화 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("메가 포트폴리오 최적화 실패")
        return None

def create_market_adaptive_strategy():
    """시장 상황 적응형 전략 생성"""
    logger.info("=== 시장 상황 적응형 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy, RSIStrategy
    
    strategy_manager = StrategyManager()
    
    # 시장 상황에 따른 적응형 모멘텀
    adaptive_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 10,
            'long_period': 30,
            'min_cross_threshold': 0.01,  # 1% 임계값
            'market_adaptive': True,
            'volatility_threshold': 0.02
        }
    )
    adaptive_strategy = MovingAverageCrossoverStrategy(adaptive_momentum)
    strategy_manager.add_strategy('Market_Adaptive', adaptive_strategy)
    
    # 보수적 RSI 전략
    conservative_rsi = StrategyConfig(
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters={
            'rsi_period': 14,
            'oversold_threshold': 35,
            'overbought_threshold': 65,
            'confirmation_period': 2
        }
    )
    rsi_strategy = RSIStrategy(conservative_rsi)
    strategy_manager.add_strategy('Conservative_RSI', rsi_strategy)
    
    return strategy_manager

def create_realistic_profit_strategy():
    """현실적인 수익 전략 생성"""
    logger.info("=== 현실적인 수익 전략 생성 ===")
    
    from trading_strategy import StrategyManager, MovingAverageCrossoverStrategy
    
    strategy_manager = StrategyManager()
    
    # 현실적인 모멘텀 전략
    realistic_momentum = StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={
            'short_period': 15,
            'long_period': 45,
            'min_cross_threshold': 0.015,  # 1.5% 임계값
            'position_sizing': 'kelly_criterion'
        }
    )
    realistic_strategy = MovingAverageCrossoverStrategy(realistic_momentum)
    strategy_manager.add_strategy('Realistic_Momentum', realistic_strategy)
    
    return strategy_manager

def test_market_adaptive_strategy():
    """시장 상황 적응형 전략 테스트"""
    logger.info("=== 시장 상황 적응형 전략 테스트 ===")
    
    adaptive_strategies = create_market_adaptive_strategy()
    
    # 현실적인 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=100000,     # 10만원
        max_positions=3,             # 3개 포지션
        position_size_ratio=0.25,    # 25% 포지션 크기
        stop_loss_rate=0.08,         # 8% 손절
        take_profit_rate=0.20        # 20% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(adaptive_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 시장 상황 적응형 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("시장 상황 적응형 전략 테스트 실패")
        return None

def test_realistic_profit_strategy():
    """현실적인 수익 전략 테스트"""
    logger.info("=== 현실적인 수익 전략 테스트 ===")
    
    realistic_strategies = create_realistic_profit_strategy()
    
    # 현실적인 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=200000,     # 20만원
        max_positions=2,             # 2개 포지션
        position_size_ratio=0.35,    # 35% 포지션 크기
        stop_loss_rate=0.10,         # 10% 손절
        take_profit_rate=0.25        # 25% 익절
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(realistic_strategies)
    
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 현실적인 수익 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("현실적인 수익 전략 테스트 실패")
        return None

def test_optimized_portfolio_strategy():
    """최적화된 포트폴리오 전략 테스트"""
    logger.info("=== 최적화된 포트폴리오 전략 테스트 ===")
    
    # 선별된 우량 종목들
    optimized_stocks = [
        '005930.KS',  # 삼성전자
        '000660.KS',  # SK하이닉스
        '035420.KS',  # NAVER
        '051910.KS',  # LG화학
        '006400.KS'   # 삼성SDI
    ]
    
    # 현실적인 전략 사용
    realistic_strategies = create_realistic_profit_strategy()
    
    # 최적화된 포트폴리오 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=50000,
        max_positions=8,
        position_size_ratio=0.15,
        stop_loss_rate=0.08,
        take_profit_rate=0.20
    )
    
    engine = BacktestingEngine(config)
    engine.add_strategy(realistic_strategies)
    
    success = engine.load_data(optimized_stocks, data_source="yahoo")
    if not success:
        logger.error("최적화된 포트폴리오 데이터 로드 실패")
        return None
    
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 최적화된 포트폴리오 전략 성과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"연간 수익률: {result.annual_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
        
        return result
    else:
        logger.error("최적화된 포트폴리오 전략 실패")
        return None

def compare_all_enhanced_strategies():
    """모든 향상된 전략 비교"""
    logger.info("=== 모든 향상된 전략 비교 ===")
    
    results = {}
    
    # 1. 모멘텀 전략
    logger.info("1. 모멘텀 전략 테스트 중...")
    momentum_result = test_momentum_strategy()
    if momentum_result:
        results['모멘텀 전략'] = momentum_result
    
    # 2. 변동성 돌파 전략
    logger.info("2. 변동성 돌파 전략 테스트 중...")
    breakout_result = test_volatility_breakout_strategy()
    if breakout_result:
        results['변동성 돌파 전략'] = breakout_result
    
    # 3. 트렌드 추종 전략
    logger.info("3. 트렌드 추종 전략 테스트 중...")
    trend_result = test_trend_following_strategy()
    if trend_result:
        results['트렌드 추종 전략'] = trend_result
    
    # 4. 고수익 하이브리드 전략
    logger.info("4. 고수익 하이브리드 전략 테스트 중...")
    hybrid_result = test_hybrid_high_profit_strategy()
    if hybrid_result:
        results['고수익 하이브리드 전략'] = hybrid_result
    
    # 5. 포트폴리오 최적화
    logger.info("5. 포트폴리오 최적화 테스트 중...")
    portfolio_result = test_portfolio_optimization()
    if portfolio_result:
        results['포트폴리오 최적화'] = portfolio_result
    
    # 6. 시장 상황 적응형 전략
    logger.info("6. 시장 상황 적응형 전략 테스트 중...")
    adaptive_result = test_market_adaptive_strategy()
    if adaptive_result:
        results['시장 상황 적응형 전략'] = adaptive_result
    
    # 7. 현실적인 수익 전략
    logger.info("7. 현실적인 수익 전략 테스트 중...")
    realistic_result = test_realistic_profit_strategy()
    if realistic_result:
        results['현실적인 수익 전략'] = realistic_result
    
    # 8. 최적화된 포트폴리오 전략
    logger.info("8. 최적화된 포트폴리오 전략 테스트 중...")
    optimized_result = test_optimized_portfolio_strategy()
    if optimized_result:
        results['최적화된 포트폴리오 전략'] = optimized_result
    
    # 결과 비교
    logger.info("\n=== 향상된 전략별 성과 비교 ===")
    for name, result in results.items():
        logger.info(f"\n{name}:")
        logger.info(f"  거래 수: {result.total_trades}회")
        logger.info(f"  승률: {result.win_rate:.2f}%")
        logger.info(f"  수익률: {result.total_return:.2f}%")
        logger.info(f"  샤프 비율: {result.sharpe_ratio:.2f}")
        logger.info(f"  최대 낙폭: {result.max_drawdown:.2f}%")
    
    # 최고 수익률 전략 찾기
    best_strategy = None
    best_return = -999
    
    for name, result in results.items():
        if result.total_return > best_return:
            best_return = result.total_return
            best_strategy = name
    
    logger.info(f"\n🏆 최고 수익률 전략: {best_strategy}")
    logger.info(f"   수익률: {best_return:.2f}%")
    
    return results, best_strategy

def generate_enhanced_profit_report():
    """향상된 수익률 최적화 리포트 생성"""
    logger.info("=== 향상된 수익률 최적화 리포트 생성 ===")
    
    logger.info("\n📈 고급 수익률 향상 전략:")
    logger.info("1. 모멘텀 전략:")
    logger.info("   - 단기/중기 모멘텀 조합")
    logger.info("   - 빠른 진입/청산")
    logger.info("   - 작은 손절, 빠른 익절")
    
    logger.info("\n2. 변동성 돌파 전략:")
    logger.info("   - 볼린저 밴드 돌파 활용")
    logger.info("   - 변동성 확대 시점 포착")
    logger.info("   - 높은 익절 목표")
    
    logger.info("\n3. 트렌드 추종 전략:")
    logger.info("   - 강한 트렌드에서만 거래")
    logger.info("   - 큰 포지션 크기")
    logger.info("   - 트렌드 지속 시 수익 극대화")
    
    logger.info("\n4. 포트폴리오 최적화:")
    logger.info("   - 다중 종목 분산 투자")
    logger.info("   - 섹터별 분산")
    logger.info("   - 리스크 분산 효과")
    
    logger.info("\n5. 하이브리드 전략:")
    logger.info("   - 여러 전략 조합")
    logger.info("   - 다양한 시장 상황 대응")
    logger.info("   - 수익 기회 극대화")
    
    logger.info("\n6. 시장 상황 적응형 전략:")
    logger.info("   - 시장 상황에 따른 파라미터 조정")
    logger.info("   - 변동성 기반 포지션 크기 조절")
    logger.info("   - 리스크 관리 최적화")
    
    logger.info("\n7. 현실적인 수익 전략:")
    logger.info("   - 현실적인 거래 금액과 포지션 크기")
    logger.info("   - 적절한 손절/익절 비율")
    logger.info("   - 장기적 관점의 투자")
    
    logger.info("\n8. 최적화된 포트폴리오:")
    logger.info("   - 선별된 우량 종목들")
    logger.info("   - 균형잡힌 포지션 크기")
    logger.info("   - 안정적인 수익 추구")

def main():
    """메인 함수"""
    logger.info("향상된 수익률 최적화 전략 개발 시작")
    
    # 1. 모든 향상된 전략 비교
    results, best_strategy = compare_all_enhanced_strategies()
    
    # 2. 향상된 수익률 최적화 리포트 생성
    generate_enhanced_profit_report()
    
    logger.info(f"\n✅ 최고 수익률 전략: {best_strategy}")
    logger.info("향상된 수익률 최적화 전략 개발 완료")

if __name__ == "__main__":
    main() 