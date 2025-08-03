#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
커스텀 전략 백테스팅 시스템
사용자 정의 진입/청산 조건을 백테스트합니다.
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
from custom_trading_strategy import create_custom_strategy
from trading_strategy import StrategyManager

def run_custom_strategy_backtest():
    """커스텀 전략 백테스팅 실행"""
    logger.info("=== 커스텀 전략 백테스팅 시작 ===")
    logger.info("진입: MA5 > MA20 + RSI < 35 + 거래량 급증")
    logger.info("청산: (목표 수익률 +5% or 손절 -2%) + 트레일링 스탑")
    logger.info("리스크 관리: 포트폴리오에서 종목당 최대 20% 비중")
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,  # 1천만원
        
        # 수수료 설정 (개선된 설정)
        commission_rate=0.0001,    # 0.01%
        slippage_rate=0.00005,     # 0.005%
        
        # 포지션 관리
        position_size_ratio=0.20,  # 종목당 최대 20%
        
        # 리스크 관리 (커스텀 전략에서 관리)
        stop_loss_rate=0.02,       # 2% 손절
        take_profit_rate=0.05,     # 5% 익절
        max_drawdown_limit=0.20,   # 20% 최대 낙폭
        
        # 거래 설정
        min_trade_amount=10000,    # 최소 거래 금액 1만원
        max_positions=5,           # 최대 5개 종목 (각 20% = 100%)
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 커스텀 전략 생성
    custom_strategy = create_custom_strategy()
    
    # 전략 매니저 생성 및 커스텀 전략 추가
    strategy_manager = StrategyManager()
    strategy_manager.add_strategy("CustomStrategy", custom_strategy)
    
    # 전략 매니저를 엔진에 추가
    engine.add_strategy(strategy_manager)
    
    # 백테스팅 실행
    logger.info("백테스팅 실행 중...")
    results = engine.run_backtest()
    
    # 결과 분석
    analyze_results(results, config)
    
    return results

def run_portfolio_custom_backtest():
    """포트폴리오 모드로 커스텀 전략 백테스팅"""
    logger.info("=== 포트폴리오 커스텀 전략 백테스팅 시작 ===")
    
    # 포트폴리오 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 수수료 설정
        commission_rate=0.0001,
        slippage_rate=0.00005,
        
        # 포지션 관리
        position_size_ratio=0.20,  # 종목당 최대 20%
        
        # 리스크 관리
        stop_loss_rate=0.02,
        take_profit_rate=0.05,
        max_drawdown_limit=0.20,
        
        # 거래 설정
        min_trade_amount=10000,
        max_positions=5,
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 커스텀 전략 생성
    custom_strategy = create_custom_strategy()
    
    # 전략 매니저 생성 및 커스텀 전략 추가
    strategy_manager = StrategyManager()
    strategy_manager.add_strategy("CustomStrategy", custom_strategy)
    
    # 전략 매니저를 엔진에 추가
    engine.add_strategy(strategy_manager)
    
    # 포트폴리오 백테스팅 실행
    results = engine.run_backtest()
    
    # 결과 분석
    if results:
        analyze_results(results, config)
    
    return results

def analyze_results(results, config):
    """백테스트 결과 분석"""
    if not results:
        logger.error("백테스트 결과가 없습니다.")
        return
        
    logger.info("=== 커스텀 전략 백테스트 결과 ===")
    
    # 수익률 분석
    total_return = results.total_return
    total_trades = results.total_trades
    win_rate = results.win_rate
    max_drawdown = results.max_drawdown
    
    # 수수료 분석
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
    
    # 거래 상세 분석
    if results.trades:
        winning_trades = [t for t in results.trades if t.action == 'SELL' and 
                         hasattr(t, 'profit') and t.profit > 0]
        losing_trades = [t for t in results.trades if t.action == 'SELL' and 
                        hasattr(t, 'profit') and t.profit <= 0]
        
        if winning_trades:
            avg_win = sum(t.profit for t in winning_trades) / len(winning_trades)
            logger.info(f"   평균 수익 거래: {avg_win:,.0f}원")
        
        if losing_trades:
            avg_loss = sum(t.profit for t in losing_trades) / len(losing_trades)
            logger.info(f"   평균 손실 거래: {avg_loss:,.0f}원")

if __name__ == "__main__":
    # 로그 설정
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add("logs/custom_strategy_backtest.log", rotation="1 day", retention="7 days", level="DEBUG")
    
    try:
        logger.info("🚀 커스텀 전략 백테스팅 시작!")
        
        # 단일 종목 백테스팅
        single_results = run_custom_strategy_backtest()
        
        # 포트폴리오 백테스팅
        portfolio_results = run_portfolio_custom_backtest()
        
        # 최종 요약
        logger.info("=== 커스텀 전략 백테스트 최종 요약 ===")
        
        if single_results:
            logger.info(f"✅ 단일 종목 백테스트:")
            logger.info(f"   거래 수: {single_results.total_trades:,}회")
            logger.info(f"   수익률: {single_results.total_return:.4%}")
            logger.info(f"   승률: {single_results.win_rate:.2%}")
        
        if portfolio_results:
            logger.info(f"✅ 포트폴리오 백테스트:")
            logger.info(f"   거래 수: {portfolio_results.total_trades:,}회")
            logger.info(f"   수익률: {portfolio_results.total_return:.4%}")
            logger.info(f"   승률: {portfolio_results.win_rate:.2%}")
        
        logger.info("🎉 커스텀 전략 백테스팅 완료!")
        
    except Exception as e:
        logger.error(f"❌ 백테스팅 실행 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())