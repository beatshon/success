#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 거래 실행 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime
from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode

def test_simple_trade():
    """간단한 거래 테스트"""
    logger.info("=== 간단한 거래 테스트 ===")
    
    # 매우 관대한 설정으로 백테스트
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000000,
        max_positions=10,
        position_size_ratio=0.1,  # 10%만 사용
        min_trade_amount=1000,    # 매우 작은 최소 거래 금액
        commission_rate=0.0001,   # 낮은 수수료
        slippage_rate=0.00005     # 낮은 슬리피지
    )
    
    # 백테스팅 엔진 생성
    engine = BacktestingEngine(config)
    
    # 샘플 데이터 생성
    engine._generate_sample_data()
    
    # 첫 번째 종목 선택
    test_code = list(engine.data.keys())[0]
    df = engine.data[test_code]
    
    logger.info(f"테스트 종목: {test_code}")
    logger.info(f"데이터 수: {len(df)}개")
    
    # 첫 번째 거래일 데이터
    first_date = df.index[0]
    first_price = df.loc[first_date, 'close']
    
    logger.info(f"첫 번째 거래일: {first_date.strftime('%Y-%m-%d')}")
    logger.info(f"가격: {first_price:,.0f}원")
    
    # 수동으로 매수 거래 실행
    logger.info("\n=== 수동 매수 거래 테스트 ===")
    
    # 주문 수량 계산
    available_capital = engine.current_capital * config.position_size_ratio
    quantity = int(available_capital / first_price)
    
    logger.info(f"초기 자본: {engine.current_capital:,.0f}원")
    logger.info(f"사용 가능 자본: {available_capital:,.0f}원")
    logger.info(f"계산된 주문 수량: {quantity}주")
    
    if quantity > 0:
        # 수수료 계산
        commission = first_price * quantity * config.commission_rate
        slippage = first_price * quantity * config.slippage_rate
        total_cost = first_price * quantity + commission + slippage
        
        logger.info(f"주문 금액: {first_price * quantity:,.0f}원")
        logger.info(f"수수료: {commission:,.0f}원")
        logger.info(f"슬리피지: {slippage:,.0f}원")
        logger.info(f"총 비용: {total_cost:,.0f}원")
        
        if total_cost <= engine.current_capital:
            logger.info("✅ 거래 조건 만족 - 매수 실행")
            
            # 매수 실행
            from trading_strategy import TradingSignal, SignalType, StrategyType
            
            # 가짜 신호 생성
            fake_signal = TradingSignal(
                strategy=StrategyType.MOVING_AVERAGE_CROSSOVER,
                signal_type=SignalType.BUY,
                confidence=0.8,
                price=first_price,
                timestamp=first_date
            )
            
            engine._execute_buy(test_code, first_price, first_date, fake_signal)
            
            logger.info(f"매수 후 자본: {engine.current_capital:,.0f}원")
            logger.info(f"보유 포지션: {len(engine.positions)}개")
            logger.info(f"총 거래 수: {len(engine.trades)}개")
            
            if len(engine.trades) > 0:
                logger.info("🎉 거래 실행 성공!")
                return True
            else:
                logger.error("❌ 거래가 기록되지 않았습니다.")
                return False
        else:
            logger.error(f"❌ 자본금 부족: 필요 {total_cost:,.0f}원, 보유 {engine.current_capital:,.0f}원")
            return False
    else:
        logger.error(f"❌ 주문 수량이 0: {available_capital:,.0f} / {first_price:,.0f} = {available_capital/first_price:.2f}")
        return False

def test_force_trade():
    """강제 거래 테스트"""
    logger.info("\n=== 강제 거래 테스트 ===")
    
    # 매우 작은 자본으로 테스트
    config = BacktestConfig(
        mode=BacktestMode.SINGLE_STOCK,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=1000000,  # 100만원
        max_positions=5,
        position_size_ratio=0.5,  # 50% 사용
        min_trade_amount=1000,
        commission_rate=0.0001,
        slippage_rate=0.00005
    )
    
    engine = BacktestingEngine(config)
    engine._generate_sample_data()
    
    test_code = list(engine.data.keys())[0]
    df = engine.data[test_code]
    
    # 낮은 가격의 데이터 찾기
    low_price_date = None
    low_price = float('inf')
    
    for date in df.index[:30]:  # 처음 30일 중에서
        price = df.loc[date, 'close']
        if price < low_price:
            low_price = price
            low_price_date = date
    
    logger.info(f"최저가 날짜: {low_price_date.strftime('%Y-%m-%d')}")
    logger.info(f"최저가: {low_price:,.0f}원")
    
    # 강제 매수
    from trading_strategy import TradingSignal, SignalType, StrategyType
    
    fake_signal = TradingSignal(
        strategy=StrategyType.MOVING_AVERAGE_CROSSOVER,
        signal_type=SignalType.BUY,
        confidence=0.8,
        price=low_price,
        timestamp=low_price_date
    )
    
    logger.info(f"강제 매수 실행: {test_code} @ {low_price:,.0f}원")
    engine._execute_buy(test_code, low_price, low_price_date, fake_signal)
    
    logger.info(f"거래 후 자본: {engine.current_capital:,.0f}원")
    logger.info(f"보유 포지션: {len(engine.positions)}개")
    logger.info(f"총 거래 수: {len(engine.trades)}개")
    
    if len(engine.trades) > 0:
        logger.info("🎉 강제 거래 성공!")
        return True
    else:
        logger.error("❌ 강제 거래 실패")
        return False

def main():
    """메인 함수"""
    logger.info("간단한 거래 실행 테스트 시작")
    
    try:
        # 1. 일반 거래 테스트
        success1 = test_simple_trade()
        
        # 2. 강제 거래 테스트
        success2 = test_force_trade()
        
        # 결과 요약
        logger.info(f"\n=== 테스트 결과 ===")
        logger.info(f"일반 거래 테스트: {'✅ 성공' if success1 else '❌ 실패'}")
        logger.info(f"강제 거래 테스트: {'✅ 성공' if success2 else '❌ 실패'}")
        
        if success1 or success2:
            logger.info("🎉 거래 실행이 정상적으로 작동합니다!")
        else:
            logger.error("⚠️ 거래 실행에 문제가 있습니다.")
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 