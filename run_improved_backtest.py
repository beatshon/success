#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 백테스팅 실행 스크립트
수정된 전략과 설정으로 백테스팅을 실행합니다.
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

def run_improved_backtest():
    """개선된 백테스팅 실행"""
    logger.info("=== 개선된 백테스팅 시작 ===")
    
    # 백테스트 설정 - 더 관대한 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000,  # 1천만원
        
        # 거래 설정 - 더 관대하게
        commission_rate=0.0001,    # 0.01% 수수료
        slippage_rate=0.00005,     # 0.005% 슬리피지
        min_trade_amount=5000,     # 5천원 최소 거래
        
        # 포지션 관리 - 더 관대하게
        max_positions=15,          # 최대 15개 포지션
        position_size_ratio=0.05,  # 전체 자금의 5%씩
        
        # 위험 관리 - 더 관대하게
        stop_loss_rate=0.08,       # 8% 손절
        take_profit_rate=0.15,     # 15% 익절
        max_drawdown_limit=0.25    # 25% 최대 낙폭
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    logger.info("데이터 로드 시작...")
    success = engine.load_data(['005930.KS'], data_source="yahoo")
    
    if not success:
        logger.error("데이터 로드 실패")
        return None
    
    logger.info(f"데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 백테스트 실행
    logger.info("백테스트 실행 시작...")
    try:
        result = engine.run_backtest()
        
        if result:
            logger.info("=== 백테스트 결과 ===")
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

def run_portfolio_backtest():
    """포트폴리오 백테스트 실행"""
    logger.info("\n=== 포트폴리오 백테스트 시작 ===")
    
    # 포트폴리오 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.PORTFOLIO,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000,
        commission_rate=0.0001,
        slippage_rate=0.00005,
        min_trade_amount=5000,
        max_positions=10,
        position_size_ratio=0.1
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드 (여러 종목)
    logger.info("포트폴리오 데이터 로드 시작...")
    success = engine.load_data(['005930.KS', '000660.KS', '035420.KS'], data_source="yahoo")
    
    if not success:
        logger.error("포트폴리오 데이터 로드 실패")
        return None
    
    logger.info(f"포트폴리오 데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 포트폴리오 백테스트 실행
    logger.info("포트폴리오 백테스트 실행 시작...")
    try:
        result = engine.run_backtest()
        
        if result:
            logger.info("=== 포트폴리오 백테스트 결과 ===")
            logger.info(f"총 거래 수: {result.total_trades}회")
            logger.info(f"승률: {result.win_rate:.2f}%")
            logger.info(f"총 수익률: {result.total_return:.2f}%")
            logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
            logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
            
            return result
        else:
            logger.error("포트폴리오 백테스트 실행 실패")
            return None
            
    except Exception as e:
        logger.error(f"포트폴리오 백테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """메인 함수"""
    logger.info("개선된 백테스팅 시스템 시작")
    
    # 1. 단일 종목 백테스트
    single_result = run_improved_backtest()
    
    # 2. 포트폴리오 백테스트
    portfolio_result = run_portfolio_backtest()
    
    # 결과 요약
    logger.info("\n=== 최종 결과 요약 ===")
    
    if single_result:
        logger.info("✅ 단일 종목 백테스트 성공")
        logger.info(f"   거래 수: {single_result.total_trades}회")
        logger.info(f"   수익률: {single_result.total_return:.2f}%")
    else:
        logger.error("❌ 단일 종목 백테스트 실패")
    
    if portfolio_result:
        logger.info("✅ 포트폴리오 백테스트 성공")
        logger.info(f"   거래 수: {portfolio_result.total_trades}회")
        logger.info(f"   수익률: {portfolio_result.total_return:.2f}%")
    else:
        logger.error("❌ 포트폴리오 백테스트 실패")
    
    logger.info("백테스팅 완료")

if __name__ == "__main__":
    main() 