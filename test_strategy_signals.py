#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전략별 신호 생성 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime
import pandas as pd
from trading_strategy import create_default_strategies
from real_stock_data_api import StockDataAPI, DataManager

# 로그 레벨을 DEBUG로 설정
logger.remove()
logger.add(sys.stderr, level="DEBUG")

def test_strategy_signals():
    """전략별 신호 생성 테스트"""
    logger.info("=== 전략별 신호 생성 테스트 시작 ===")
    
    # 데이터 로드
    api = StockDataAPI(data_source="yahoo")
    manager = DataManager(api)
    
    stock_data = manager.get_backtest_data(
        ['005930'], 
        "2023-01-01", 
        "2023-12-31",
        validate=True,
        clean=True
    )
    
    if not stock_data:
        logger.error("데이터 로드 실패")
        return False
    
    df = stock_data['005930'].data
    logger.info(f"데이터 로드 완료: {len(df)}개")
    
    # 전략 매니저 생성
    strategy_manager = create_default_strategies()
    
    # 각 전략별로 테스트
    for name, strategy in strategy_manager.strategies.items():
        logger.info(f"\n=== {name} 전략 테스트 ===")
        
        # 전략 초기화
        strategy.price_history = []
        
        # 데이터 추가 및 신호 생성 테스트
        signal_count = 0
        for i, (date, row) in enumerate(df.iterrows()):
            # 데이터 추가
            strategy.add_data(date, row)
            
            # 30개 이상의 데이터가 있으면 신호 생성 시도
            if len(strategy.price_history) >= 30:
                signal = strategy.generate_signal()
                if signal:
                    signal_count += 1
                    logger.info(f"신호 {signal_count}: {date.strftime('%Y-%m-%d')} - {signal.signal_type.value} @ {signal.price:,.0f}원 (신뢰도: {signal.confidence:.3f})")
                
                # 10개 신호가 생성되면 중단
                if signal_count >= 10:
                    break
        
        logger.info(f"{name} 전략: 총 {signal_count}개 신호 생성")
        
        if signal_count == 0:
            logger.warning(f"⚠️ {name} 전략에서 신호가 생성되지 않았습니다!")
            
            # 전략 파라미터 출력
            logger.info(f"전략 파라미터: {strategy.config.parameters}")
            
            # 마지막 10개 가격 데이터 출력
            if len(strategy.price_history) >= 10:
                logger.info("마지막 10개 가격 데이터:")
                for i, data in enumerate(strategy.price_history[-10:]):
                    logger.info(f"  {i+1}: {data['timestamp'].strftime('%Y-%m-%d')} - {data['price']:,.0f}원")
    
    return True

def main():
    """메인 함수"""
    try:
        success = test_strategy_signals()
        
        if success:
            logger.info("✅ 전략별 신호 생성 테스트가 완료되었습니다!")
        else:
            logger.error("❌ 전략별 신호 생성 테스트에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 