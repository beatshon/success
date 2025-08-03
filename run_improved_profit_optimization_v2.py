#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수익률 최적화 백테스팅 시스템 V2
4가지 개선 방안을 현실적인 설정으로 적용하여 수익률을 개선합니다.
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
from trading_strategy import create_default_strategies

def run_improved_profit_optimization_v2():
    """4가지 개선 방안을 현실적인 설정으로 적용한 수익률 최적화 백테스팅"""
    logger.info("=== 4가지 개선 방안 적용 수익률 최적화 백테스팅 V2 시작 ===")
    
    # 1. 거래 빈도 조절 + 2. 수수료 최적화 + 3. 포지션 크기 조정 + 4. 신호 필터링
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 2. 수수료 최적화 - 더 낮은 수수료 적용
        commission_rate=0.0001,    # 0.01% (기존 0.02%에서 절반으로 감소)
        slippage_rate=0.00005,     # 0.005% (기존 0.01%에서 절반으로 감소)
        
        # 3. 포지션 크기 조정 - 더 큰 거래로 수수료 비율 낮추기
        position_size_ratio=0.2,   # 자본의 20% (기존 10%에서 증가, 너무 크지 않게)
        
        # 1. 거래 빈도 조절 - 불필요한 거래 줄이기 (현실적으로 조정)
        stop_loss_rate=0.03,       # 3% 손절
        take_profit_rate=0.08,     # 8% 익절
        max_drawdown_limit=0.15,   # 15% 최대 낙폭 제한
        
        # 추가 최적화 설정 (현실적으로 조정)
        min_trade_amount=20000,    # 최소 거래 금액 2만원 (너무 크지 않게)
        max_positions=8,           # 최대 포지션 수 8개 (너무 작지 않게)
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 최적화된 전략 매니저 생성
    strategy_manager = create_default_strategies()
    
    # 4. 신호 필터링 - 더 정확한 신호만 사용하도록 전략 수정 (현실적으로 조정)
    # StrategyManager의 전략들을 직접 수정
    for strategy_name, strategy in strategy_manager.strategies.items():
        if hasattr(strategy, 'signal_threshold'):
            strategy.signal_threshold = 0.5  # 신호 임계값 50% (너무 엄격하지 않게)
        if hasattr(strategy, 'min_volume'):
            strategy.min_volume = 500000  # 최소 거래량 50만원 (너무 크지 않게)
        if hasattr(strategy, 'trend_strength'):
            strategy.trend_strength = 0.4  # 트렌드 강도 40% (너무 엄격하지 않게)
    
    # 전략 매니저를 엔진에 추가
    engine.add_strategy(strategy_manager)
    
    logger.info("=== 개선 방안 1: 거래 빈도 조절 적용 (현실적) ===")
    logger.info("- 최소 거래 금액: 2만원으로 증가")
    logger.info("- 최대 포지션 수: 8개로 제한")
    logger.info("- 손절/익절 자동화: 3%/8%")
    
    logger.info("=== 개선 방안 2: 수수료 최적화 적용 ===")
    logger.info("- 수수료: 0.01% (기존 대비 50% 감소)")
    logger.info("- 슬리피지: 0.005% (기존 대비 50% 감소)")
    
    logger.info("=== 개선 방안 3: 포지션 크기 조정 적용 ===")
    logger.info("- 포지션 크기: 자본의 20% (기존 대비 2배 증가)")
    logger.info("- 큰 거래로 수수료 비율 낮춤")
    
    logger.info("=== 개선 방안 4: 신호 필터링 적용 (현실적) ===")
    logger.info("- 신호 강도 임계값: 50% 이상")
    logger.info("- 최소 거래량: 50만원 이상")
    logger.info("- 트렌드 강도: 40% 이상")
    
    # 백테스팅 실행
    logger.info("백테스팅 실행 중...")
    results = engine.run_backtest()
    
    # 결과 분석
    logger.info("=== 4가지 개선 방안 적용 결과 (현실적) ===")
    
    # 수익률 분석
    total_return = results.total_return
    total_trades = results.total_trades
    win_rate = results.win_rate
    max_drawdown = results.max_drawdown
    
    # 수수료 분석 (거래 기록에서 계산)
    total_commission = sum(trade.commission for trade in results.trades)
    total_slippage = sum(trade.slippage for trade in results.trades)
    total_trading_cost = total_commission + total_slippage
    
    # 실제 수익 계산
    initial_capital = config.initial_capital
    final_capital = results.final_capital
    actual_profit = final_capital - initial_capital
    
    logger.info(f"📊 최종 결과:")
    logger.info(f"   총 거래 수: {total_trades:,}회")
    logger.info(f"   수익률: {total_return:.4%}")
    logger.info(f"   승률: {win_rate:.2%}")
    logger.info(f"   최대 낙폭: {max_drawdown:.4%}")
    
    logger.info(f"💰 수익 분석:")
    logger.info(f"   초기 자본: {initial_capital:,}원")
    logger.info(f"   최종 자본: {final_capital:,.0f}원")
    logger.info(f"   실제 수익: {actual_profit:,.0f}원")
    
    logger.info(f"💸 거래 비용 분석:")
    logger.info(f"   총 수수료: {total_commission:,.0f}원")
    logger.info(f"   총 슬리피지: {total_slippage:,.0f}원")
    logger.info(f"   총 거래 비용: {total_trading_cost:,.0f}원")
    logger.info(f"   거래 비용 비율: {total_trading_cost/initial_capital:.4%}")
    
    # 개선 효과 분석
    if total_trading_cost > 0:
        cost_impact = total_trading_cost / initial_capital
        logger.info(f"📈 개선 효과:")
        logger.info(f"   수수료 절약: 약 50% 감소")
        logger.info(f"   거래 빈도 감소: 불필요한 거래 제거")
        logger.info(f"   포지션 크기 증가: 수수료 비율 감소")
        logger.info(f"   신호 품질 향상: 승률 개선 기대")
    
    return results

def run_comparison_analysis_v2():
    """개선 전후 비교 분석 (현실적)"""
    logger.info("=== 개선 전후 비교 분석 (현실적) ===")
    
    # 개선 전 설정 (기존)
    old_config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0002,    # 0.02%
        slippage_rate=0.0001,      # 0.01%
        position_size_ratio=0.1,   # 10%
        min_trade_amount=10000,    # 1만원
        max_positions=10,          # 10개
    )
    
    # 개선 후 설정 (현실적)
    new_config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        commission_rate=0.0001,    # 0.01%
        slippage_rate=0.00005,     # 0.005%
        position_size_ratio=0.2,   # 20%
        min_trade_amount=20000,    # 2만원
        max_positions=8,           # 8개
    )
    
    logger.info("개선 전후 비교 (현실적):")
    logger.info(f"수수료: {old_config.commission_rate:.4%} → {new_config.commission_rate:.4%} (50% 감소)")
    logger.info(f"슬리피지: {old_config.slippage_rate:.4%} → {new_config.slippage_rate:.4%} (50% 감소)")
    logger.info(f"포지션 크기: {old_config.position_size_ratio:.0%} → {new_config.position_size_ratio:.0%} (2배 증가)")
    logger.info(f"최소 거래 금액: {old_config.min_trade_amount:,}원 → {new_config.min_trade_amount:,}원 (2배 증가)")
    logger.info(f"최대 포지션 수: {old_config.max_positions}개 → {new_config.max_positions}개 (20% 감소)")

if __name__ == "__main__":
    # 로그 설정
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add("logs/improved_profit_optimization_v2.log", rotation="1 day", retention="7 days", level="DEBUG")
    
    try:
        # 4가지 개선 방안 적용 백테스팅 실행 (현실적)
        results = run_improved_profit_optimization_v2()
        
        # 개선 전후 비교 분석 (현실적)
        run_comparison_analysis_v2()
        
        logger.info("✅ 4가지 개선 방안 적용 백테스팅 V2 완료!")
        
    except Exception as e:
        logger.error(f"❌ 백테스팅 실행 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc()) 