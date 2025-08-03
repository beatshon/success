#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 수익 분석 및 수수료 영향 분석
승률과 수익률의 차이를 분석하고 실제 수익을 계산합니다.
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

def analyze_profit_without_commission():
    """수수료 없는 수익률 분석"""
    logger.info("=== 수수료 없는 수익률 분석 시작 ===")
    
    # 수수료 없는 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 수수료 제거
        commission_rate=0.0,      # 수수료 0%
        slippage_rate=0.0,        # 슬리피지 0%
        min_trade_amount=10000,
        
        # 포지션 관리
        max_positions=20,
        position_size_ratio=0.05,
        
        # 위험 관리
        stop_loss_rate=0.05,
        take_profit_rate=0.10,
        max_drawdown_limit=0.15
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    stock_codes = ['005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS']
    success = engine.load_data(stock_codes, data_source="yahoo")
    
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 수수료 없는 백테스트 결과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"실제 수익: {result.total_profit:,.0f}원")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        
        return result
    return None

def analyze_profit_with_commission():
    """수수료 있는 수익률 분석"""
    logger.info("\n=== 수수료 있는 수익률 분석 시작 ===")
    
    # 수수료 있는 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 실제 수수료 적용
        commission_rate=0.00015,  # 0.015% 수수료 (실제 거래소 수수료)
        slippage_rate=0.0001,     # 0.01% 슬리피지
        min_trade_amount=10000,
        
        # 포지션 관리
        max_positions=20,
        position_size_ratio=0.05,
        
        # 위험 관리
        stop_loss_rate=0.05,
        take_profit_rate=0.10,
        max_drawdown_limit=0.15
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    stock_codes = ['005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS']
    success = engine.load_data(stock_codes, data_source="yahoo")
    
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    # 백테스트 실행
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 수수료 있는 백테스트 결과 ===")
        logger.info(f"총 거래 수: {result.total_trades}회")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"실제 수익: {result.total_profit:,.0f}원")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        
        return result
    return None

def calculate_detailed_profit_analysis():
    """상세 수익 분석"""
    logger.info("\n=== 상세 수익 분석 시작 ===")
    
    # 다양한 수수료 설정으로 테스트
    commission_rates = [0.0, 0.0001, 0.00015, 0.0002, 0.0003]
    results = []
    
    for commission_rate in commission_rates:
        config = BacktestConfig(
            mode=BacktestMode.SINGLE_STOCK,
            start_date="2023-02-15",
            end_date="2023-12-28",
            initial_capital=10000000,
            
            commission_rate=commission_rate,
            slippage_rate=commission_rate * 0.5,  # 슬리피지는 수수료의 절반
            min_trade_amount=10000,
            
            max_positions=20,
            position_size_ratio=0.05,
            
            stop_loss_rate=0.05,
            take_profit_rate=0.10,
            max_drawdown_limit=0.15
        )
        
        engine = BacktestingEngine(config)
        strategy_manager = create_default_strategies()
        engine.add_strategy(strategy_manager)
        
        stock_codes = ['005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS']
        success = engine.load_data(stock_codes, data_source="yahoo")
        
        if success:
            result = engine.run_backtest()
            if result:
                results.append({
                    'commission_rate': commission_rate,
                    'total_trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'total_return': result.total_return,
                    'total_profit': result.total_profit,
                    'max_drawdown': result.max_drawdown
                })
    
    # 결과 출력
    logger.info("=== 수수료별 수익률 비교 ===")
    logger.info("수수료율 | 거래수 | 승률 | 수익률 | 실제수익 | 최대낙폭")
    logger.info("-" * 60)
    
    for result in results:
        logger.info(f"{result['commission_rate']*100:.3f}% | {result['total_trades']:4d} | {result['win_rate']:5.1f}% | {result['total_return']:6.2f}% | {result['total_profit']:8,.0f}원 | {result['max_drawdown']:6.2f}%")
    
    return results

def analyze_trade_details():
    """거래 상세 분석"""
    logger.info("\n=== 거래 상세 분석 시작 ===")
    
    # 중간 수수료로 상세 분석
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        commission_rate=0.00015,  # 0.015%
        slippage_rate=0.000075,   # 0.0075%
        min_trade_amount=10000,
        
        max_positions=20,
        position_size_ratio=0.05,
        
        stop_loss_rate=0.05,
        take_profit_rate=0.10,
        max_drawdown_limit=0.15
    )
    
    engine = BacktestingEngine(config)
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    stock_codes = ['005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS']
    success = engine.load_data(stock_codes, data_source="yahoo")
    
    if success:
        result = engine.run_backtest()
        
        if result and result.trades:
            # 거래 분석
            total_commission = sum(trade.commission for trade in result.trades)
            total_slippage = sum(trade.slippage for trade in result.trades)
            total_trading_cost = total_commission + total_slippage
            
            winning_trades = [t for t in result.trades if t.action == 'SELL' and hasattr(t, 'profit_rate') and t.profit_rate > 0]
            losing_trades = [t for t in result.trades if t.action == 'SELL' and hasattr(t, 'profit_rate') and t.profit_rate < 0]
            
            avg_win_profit = np.mean([t.profit_rate for t in winning_trades]) if winning_trades else 0
            avg_loss_profit = np.mean([t.profit_rate for t in losing_trades]) if losing_trades else 0
            
            logger.info("=== 거래 상세 분석 결과 ===")
            logger.info(f"총 거래 수: {result.total_trades}회")
            logger.info(f"총 수수료: {total_commission:,.0f}원")
            logger.info(f"총 슬리피지: {total_slippage:,.0f}원")
            logger.info(f"총 거래 비용: {total_trading_cost:,.0f}원")
            logger.info(f"거래 비용 비율: {total_trading_cost/10000000*100:.2f}%")
            logger.info(f"평균 수익 거래: {avg_win_profit*100:.2f}%")
            logger.info(f"평균 손실 거래: {avg_loss_profit*100:.2f}%")
            logger.info(f"수익/손실 비율: {abs(avg_win_profit/avg_loss_profit):.2f}:1" if avg_loss_profit != 0 else "수익/손실 비율: 계산 불가")
            
            # 수수료가 수익률에 미치는 영향
            gross_profit = result.total_profit + total_trading_cost
            logger.info(f"수수료 제외 수익: {gross_profit:,.0f}원")
            logger.info(f"수수료 제외 수익률: {gross_profit/10000000*100:.2f}%")
            logger.info(f"수수료 영향도: {total_trading_cost/gross_profit*100:.2f}%" if gross_profit > 0 else "수수료 영향도: 계산 불가")

def main():
    """메인 실행 함수"""
    logger.info("=== 실제 수익 분석 시스템 시작 ===")
    
    # 1. 수수료 없는 수익률 분석
    no_commission_result = analyze_profit_without_commission()
    
    # 2. 수수료 있는 수익률 분석
    commission_result = analyze_profit_with_commission()
    
    # 3. 수수료별 상세 비교
    detailed_results = calculate_detailed_profit_analysis()
    
    # 4. 거래 상세 분석
    analyze_trade_details()
    
    # 최종 분석 결과
    logger.info("\n=== 최종 분석 결과 ===")
    
    if no_commission_result and commission_result:
        commission_impact = no_commission_result.total_return - commission_result.total_return
        logger.info(f"수수료로 인한 수익률 감소: {commission_impact:.2f}%")
        logger.info(f"수수료로 인한 실제 손실: {no_commission_result.total_profit - commission_result.total_profit:,.0f}원")
    
    logger.info("\n=== 수수료 영향 분석 완료 ===")

if __name__ == "__main__":
    main() 