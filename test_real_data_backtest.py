#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 데이터 백테스트 디버깅
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime
from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from trading_strategy import create_default_strategies

# 로그 레벨을 DEBUG로 설정
logger.remove()
logger.add(sys.stderr, level="DEBUG")

def test_real_data_backtest():
    """실제 데이터 백테스트 테스트"""
    logger.info("=== 실제 데이터 백테스트 디버깅 시작 ===")
    
    # 백테스트 설정
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 전략 매니저 추가
    strategy_manager = create_default_strategies()
    engine.add_strategy(strategy_manager)
    
    # 데이터 로드
    logger.info("데이터 로드 시작...")
    success = engine.load_data(['005930'], data_source="yahoo")
    
    if not success:
        logger.error("데이터 로드 실패")
        return False
    
    logger.info(f"데이터 로드 완료: {len(engine.data)}개 종목")
    
    # 첫 번째 종목 확인
    if engine.data:
        first_code = list(engine.data.keys())[0]
        df = engine.data[first_code]
        logger.info(f"첫 번째 종목: {first_code}")
        logger.info(f"데이터 수: {len(df)}개")
        logger.info(f"데이터 범위: {df.index[0]} ~ {df.index[-1]}")
        logger.info(f"컬럼: {list(df.columns)}")
        logger.info(f"첫 번째 행: {df.iloc[0].to_dict()}")
        logger.info(f"마지막 행: {df.iloc[-1].to_dict()}")
    
    # 백테스트 실행
    logger.info("백테스트 실행 시작...")
    result = engine.run_backtest()
    
    if result:
        logger.info("=== 백테스트 결과 ===")
        logger.info(f"총 거래: {result.total_trades}개")
        logger.info(f"승률: {result.win_rate:.2f}%")
        logger.info(f"총 수익률: {result.total_return:.2f}%")
        logger.info(f"최대 낙폭: {result.max_drawdown:.2f}%")
        
        # 전략별 성과
        for name, perf in result.strategy_performance.items():
            logger.info(f"{name}: {perf}")
        
        return result.total_trades > 0
    else:
        logger.error("백테스트 실행 실패")
        return False

def main():
    """메인 함수"""
    try:
        success = test_real_data_backtest()
        
        if success:
            logger.info("✅ 실제 데이터 백테스트가 성공적으로 완료되었습니다!")
        else:
            logger.error("❌ 실제 데이터 백테스트에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 