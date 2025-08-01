#!/usr/bin/env python3
"""
전략 클래스 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy
import numpy as np

class MockAPI:
    """테스트용 Mock API 클래스"""
    def order_stock(self, account, code, quantity, price, order_type):
        print(f"Mock 주문: {order_type} - {code} {quantity}주 @ {price:,}원")
        return "TEST_ORDER_001"

def test_moving_average_strategy():
    """이동평균 전략 테스트"""
    print("=== 이동평균 전략 테스트 ===")
    
    mock_api = MockAPI()
    strategy = MovingAverageStrategy(mock_api, "TEST_ACCOUNT", short_period=3, long_period=5)
    
    # 가격 데이터 시뮬레이션 (상승 추세)
    prices = [1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100]
    
    for i, price in enumerate(prices):
        print(f"가격: {price:,}원")
        
        # 매수 조건 확인
        if strategy.should_buy("005930", price):
            print("  -> 매수 신호!")
            strategy.execute_trade("005930", "매수", 10, price)
        
        # 매도 조건 확인
        elif strategy.should_sell("005930", price):
            print("  -> 매도 신호!")
            strategy.execute_trade("005930", "매도", 10, price)
        else:
            print("  -> 관망")

def test_rsi_strategy():
    """RSI 전략 테스트"""
    print("\n=== RSI 전략 테스트 ===")
    
    mock_api = MockAPI()
    strategy = RSIStrategy(mock_api, "TEST_ACCOUNT", period=5, oversold=30, overbought=70)
    
    # RSI 변동을 시뮬레이션하는 가격 데이터
    prices = [1000, 990, 980, 970, 960, 950, 940, 930, 920, 910, 900, 890, 880, 870, 860]
    
    for i, price in enumerate(prices):
        print(f"가격: {price:,}원")
        
        # 매수 조건 확인
        if strategy.should_buy("005930", price):
            print("  -> 매수 신호!")
            strategy.execute_trade("005930", "매수", 10, price)
        
        # 매도 조건 확인
        elif strategy.should_sell("005930", price):
            print("  -> 매도 신호!")
            strategy.execute_trade("005930", "매도", 10, price)
        else:
            print("  -> 관망")

def test_bollinger_bands_strategy():
    """볼린저 밴드 전략 테스트"""
    print("\n=== 볼린저 밴드 전략 테스트 ===")
    
    mock_api = MockAPI()
    strategy = BollingerBandsStrategy(mock_api, "TEST_ACCOUNT", period=5, std_dev=1.5)
    
    # 변동성이 있는 가격 데이터
    prices = [1000, 1010, 990, 1020, 980, 1030, 970, 1040, 960, 1050, 950, 1060, 940, 1070, 930]
    
    for i, price in enumerate(prices):
        print(f"가격: {price:,}원")
        
        # 매수 조건 확인
        if strategy.should_buy("005930", price):
            print("  -> 매수 신호!")
            strategy.execute_trade("005930", "매수", 10, price)
        
        # 매도 조건 확인
        elif strategy.should_sell("005930", price):
            print("  -> 매도 신호!")
            strategy.execute_trade("005930", "매도", 10, price)
        else:
            print("  -> 관망")

if __name__ == "__main__":
    print("키움 자동매매 전략 테스트 시작\n")
    
    try:
        test_moving_average_strategy()
        test_rsi_strategy()
        test_bollinger_bands_strategy()
        
        print("\n✅ 모든 전략 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 