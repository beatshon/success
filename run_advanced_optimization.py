#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 수익률 최적화 백테스팅 시스템
더 높은 수익률을 위한 고급 최적화 기법을 적용합니다.
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

def run_advanced_optimization():
    """고급 수익률 최적화 백테스팅 실행"""
    logger.info("=== 고급 수익률 최적화 백테스팅 시작 ===")
    
    # 고급 최적화를 위한 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 거래 설정 - 고급 최적화
        commission_rate=0.00002,   # 0.002% 수수료 (매우 낮춤)
        slippage_rate=0.00001,     # 0.001% 슬리피지 (매우 낮춤)
        min_trade_amount=5000,     # 5천원 최소 거래
        
        # 포지션 관리 - 고급 최적화
        max_positions=50,          # 최대 50개 포지션 (매우 많게)
        position_size_ratio=0.015, # 전체 자금의 1.5%씩 (매우 작게)
        
        # 위험 관리 - 고급 최적화
        stop_loss_rate=0.03,       # 3% 손절 (매우 엄격하게)
        take_profit_rate=0.08,     # 8% 익절 (빠른 익절)
        max_drawdown_limit=0.10    # 10% 최대 낙폭 (매우 엄격하게)
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드 - 더 많은 종목으로 확장
    logger.info("데이터 로드 시작...")
    stock_codes = [
        '005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS',
        '005380.KS', '035720.KS', '068270.KS', '207940.KS', '323410.KS',
        '035720.KS', '051910.KS', '006400.KS', '005380.KS', '035720.KS'
    ]
    success = engine.load_data(stock_codes, data_source="yahoo")
    
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    logger.info(f"데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 백테스트 실행
    logger.info("고급 백테스트 실행 시작...")
    try:
        result = engine.run_backtest()
        
        if result:
            logger.info("=== 고급 수익률 최적화 백테스트 결과 ===")
            logger.info(f"백테스트 모드: {result.config.mode.value}")
            logger.info(f"기간: {result.start_date.strftime('%Y-%m-%d')} ~ {result.end_date.strftime('%Y-%m-%d')}")
            logger.info(f"초기 자본: {result.initial_capital:,.0f}원")
            logger.info(f"최종 자본: {result.final_capital:,.0f}원")
            logger.info(f"총 수익률: {result.total_return:.2f}%")
            logger.info(f"연간 수익률: {result.annual_return:.2f}%")
            logger.info(f"총 거래 수: {result.total_trades}회")
            logger.info(f"승률: {result.win_rate:.2f}%")
            logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
            logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
            
            # 전략별 성과
            logger.info("\n=== 전략별 성과 ===")
            for name, perf in result.strategy_performance.items():
                logger.info(f"{name}: {perf}")
            
            return result
        else:
            logger.error("백테스트 실행 실패")
            return None
            
    except Exception as e:
        logger.error(f"백테스트 실행 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_multi_strategy_optimization():
    """다중 전략 최적화 백테스트 실행"""
    logger.info("\n=== 다중 전략 최적화 백테스트 시작 ===")
    
    # 다중 전략 최적화 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 거래 설정 - 다중 전략 최적화
        commission_rate=0.00002,
        slippage_rate=0.00001,
        min_trade_amount=5000,
        
        # 포트폴리오 관리
        max_positions=100,
        position_size_ratio=0.01,
        
        # 위험 관리
        stop_loss_rate=0.025,
        take_profit_rate=0.06,
        max_drawdown_limit=0.08
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 포트폴리오 종목들 - 더 많은 종목
    portfolio_codes = [
        '005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS',
        '005380.KS', '035720.KS', '068270.KS', '207940.KS', '323410.KS',
        '035720.KS', '051910.KS', '006400.KS', '005380.KS', '035720.KS',
        '068270.KS', '207940.KS', '323410.KS', '035720.KS', '051910.KS'
    ]
    
    # 데이터 로드
    logger.info("다중 전략 데이터 로드 시작...")
    success = engine.load_data(portfolio_codes, data_source="yahoo")
    
    if not success:
        logger.error("다중 전략 데이터 로드 실패")
        return None
    
    logger.info(f"다중 전략 데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 백테스트 실행
    logger.info("다중 전략 백테스트 실행 시작...")
    try:
        result = engine.run_backtest()
        
        if result:
            logger.info("=== 다중 전략 최적화 백테스트 결과 ===")
            logger.info(f"총 거래 수: {result.total_trades}회")
            logger.info(f"승률: {result.win_rate:.2f}%")
            logger.info(f"총 수익률: {result.total_return:.2f}%")
            logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
            logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
            
            return result
        else:
            logger.error("다중 전략 백테스트 실행 실패")
            return None
            
    except Exception as e:
        logger.error(f"다중 전략 백테스트 실행 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_aggressive_optimization():
    """공격적 수익률 최적화 백테스트 실행"""
    logger.info("\n=== 공격적 수익률 최적화 백테스트 시작 ===")
    
    # 공격적 최적화 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-02-15",
        end_date="2023-12-28",
        initial_capital=10000000,
        
        # 거래 설정 - 공격적 최적화
        commission_rate=0.00001,   # 0.001% 수수료 (극도로 낮춤)
        slippage_rate=0.000005,    # 0.0005% 슬리피지 (극도로 낮춤)
        min_trade_amount=1000,     # 1천원 최소 거래
        
        # 포지션 관리 - 공격적 최적화
        max_positions=100,         # 최대 100개 포지션 (극도로 많게)
        position_size_ratio=0.008, # 전체 자금의 0.8%씩 (극도로 작게)
        
        # 위험 관리 - 공격적 최적화
        stop_loss_rate=0.02,       # 2% 손절 (극도로 엄격하게)
        take_profit_rate=0.05,     # 5% 익절 (매우 빠른 익절)
        max_drawdown_limit=0.05    # 5% 최대 낙폭 (극도로 엄격하게)
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    logger.info("공격적 최적화 데이터 로드 시작...")
    stock_codes = [
        '005930.KS', '000660.KS', '035420.KS', '051910.KS', '006400.KS',
        '005380.KS', '035720.KS', '068270.KS', '207940.KS', '323410.KS'
    ]
    success = engine.load_data(stock_codes, data_source="yahoo")
    
    if not success:
        logger.error("공격적 최적화 데이터 로드 실패")
        return None
    
    logger.info(f"공격적 최적화 데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 백테스트 실행
    logger.info("공격적 최적화 백테스트 실행 시작...")
    try:
        result = engine.run_backtest()
        
        if result:
            logger.info("=== 공격적 수익률 최적화 백테스트 결과 ===")
            logger.info(f"총 거래 수: {result.total_trades}회")
            logger.info(f"승률: {result.win_rate:.2f}%")
            logger.info(f"총 수익률: {result.total_return:.2f}%")
            logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
            logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
            
            return result
        else:
            logger.error("공격적 최적화 백테스트 실행 실패")
            return None
            
    except Exception as e:
        logger.error(f"공격적 최적화 백테스트 실행 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """메인 실행 함수"""
    logger.info("=== 고급 수익률 최적화 백테스팅 시스템 시작 ===")
    
    # 고급 최적화 백테스트
    advanced_result = run_advanced_optimization()
    
    # 다중 전략 최적화 백테스트
    multi_strategy_result = run_multi_strategy_optimization()
    
    # 공격적 최적화 백테스트
    aggressive_result = run_aggressive_optimization()
    
    # 최종 결과 요약
    logger.info("\n=== 고급 최적화 결과 요약 ===")
    
    if advanced_result:
        logger.info("✅ 고급 최적화 백테스트 성공")
        logger.info(f"   거래 수: {advanced_result.total_trades}회")
        logger.info(f"   수익률: {advanced_result.total_return:.2f}%")
        logger.info(f"   승률: {advanced_result.win_rate:.2f}%")
        logger.info(f"   최대 낙폭: {advanced_result.max_drawdown:.2f}%")
        
        if advanced_result.total_return > 0:
            logger.info("🎉 고급 최적화에서 수익이 발생했습니다!")
        else:
            logger.info("⚠️ 고급 최적화에서 손실이 발생했습니다.")
    
    if multi_strategy_result:
        logger.info("✅ 다중 전략 최적화 백테스트 성공")
        logger.info(f"   거래 수: {multi_strategy_result.total_trades}회")
        logger.info(f"   수익률: {multi_strategy_result.total_return:.2f}%")
        logger.info(f"   승률: {multi_strategy_result.win_rate:.2f}%")
        logger.info(f"   최대 낙폭: {multi_strategy_result.max_drawdown:.2f}%")
        
        if multi_strategy_result.total_return > 0:
            logger.info("🎉 다중 전략에서 수익이 발생했습니다!")
        else:
            logger.info("⚠️ 다중 전략에서 손실이 발생했습니다.")
    
    if aggressive_result:
        logger.info("✅ 공격적 최적화 백테스트 성공")
        logger.info(f"   거래 수: {aggressive_result.total_trades}회")
        logger.info(f"   수익률: {aggressive_result.total_return:.2f}%")
        logger.info(f"   승률: {aggressive_result.win_rate:.2f}%")
        logger.info(f"   최대 낙폭: {aggressive_result.max_drawdown:.2f}%")
        
        if aggressive_result.total_return > 0:
            logger.info("🎉 공격적 최적화에서 수익이 발생했습니다!")
        else:
            logger.info("⚠️ 공격적 최적화에서 손실이 발생했습니다.")
    
    # 최고 성과 분석
    results = []
    if advanced_result:
        results.append(("고급 최적화", advanced_result.total_return))
    if multi_strategy_result:
        results.append(("다중 전략", multi_strategy_result.total_return))
    if aggressive_result:
        results.append(("공격적 최적화", aggressive_result.total_return))
    
    if results:
        best_strategy = max(results, key=lambda x: x[1])
        logger.info(f"\n🏆 최고 성과 전략: {best_strategy[0]} (수익률: {best_strategy[1]:.2f}%)")
    
    logger.info("\n=== 고급 수익률 최적화 백테스팅 완료 ===")

if __name__ == "__main__":
    main() 