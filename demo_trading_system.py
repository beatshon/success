#!/usr/bin/env python3
"""
모의 거래 시스템
키움 API 연결 없이도 거래 로직을 테스트할 수 있는 시스템
"""
import time
import random
import json
from datetime import datetime, timedelta
import config

class MockTradingSystem:
    """모의 거래 시스템"""
    
    def __init__(self):
        self.account_balance = 10000000  # 1000만원 초기 자금
        self.positions = {}  # 보유 종목
        self.trade_history = []  # 거래 내역
        self.current_prices = {}  # 현재가 시뮬레이션
        
        # 모니터링 종목 초기화
        for stock in config.WATCH_STOCKS:
            self.current_prices[stock['code']] = {
                'price': random.randint(50000, 200000),
                'change': random.uniform(-5, 5),
                'volume': random.randint(1000, 10000)
            }
    
    def get_stock_price(self, stock_code):
        """주식 가격 조회 (모의)"""
        if stock_code in self.current_prices:
            # 가격 변동 시뮬레이션
            current = self.current_prices[stock_code]
            change_percent = random.uniform(-2, 2)
            current['price'] = int(current['price'] * (1 + change_percent / 100))
            current['change'] = change_percent
            return current
        return None
    
    def buy_stock(self, stock_code, quantity, price=None):
        """주식 매수 (모의)"""
        stock_info = self.get_stock_price(stock_code)
        if not stock_info:
            return False, "종목 정보를 찾을 수 없습니다."
        
        if price is None:
            price = stock_info['price']
        
        total_cost = price * quantity
        if total_cost > self.account_balance:
            return False, "잔액이 부족합니다."
        
        # 거래 실행
        self.account_balance -= total_cost
        
        if stock_code in self.positions:
            # 기존 보유 종목에 추가
            avg_price = (self.positions[stock_code]['avg_price'] * self.positions[stock_code]['quantity'] + total_cost) / (self.positions[stock_code]['quantity'] + quantity)
            self.positions[stock_code]['quantity'] += quantity
            self.positions[stock_code]['avg_price'] = avg_price
        else:
            # 새로운 종목 매수
            self.positions[stock_code] = {
                'quantity': quantity,
                'avg_price': price,
                'buy_date': datetime.now()
            }
        
        # 거래 내역 기록
        trade_record = {
            'timestamp': datetime.now(),
            'type': 'BUY',
            'stock_code': stock_code,
            'quantity': quantity,
            'price': price,
            'total': total_cost
        }
        self.trade_history.append(trade_record)
        
        return True, f"매수 성공: {stock_code} {quantity}주 @ {price:,}원"
    
    def sell_stock(self, stock_code, quantity, price=None):
        """주식 매도 (모의)"""
        if stock_code not in self.positions:
            return False, "보유하지 않은 종목입니다."
        
        if self.positions[stock_code]['quantity'] < quantity:
            return False, "보유 수량이 부족합니다."
        
        stock_info = self.get_stock_price(stock_code)
        if not stock_info:
            return False, "종목 정보를 찾을 수 없습니다."
        
        if price is None:
            price = stock_info['price']
        
        total_revenue = price * quantity
        
        # 거래 실행
        self.account_balance += total_revenue
        self.positions[stock_code]['quantity'] -= quantity
        
        if self.positions[stock_code]['quantity'] == 0:
            del self.positions[stock_code]
        
        # 거래 내역 기록
        trade_record = {
            'timestamp': datetime.now(),
            'type': 'SELL',
            'stock_code': stock_code,
            'quantity': quantity,
            'price': price,
            'total': total_revenue
        }
        self.trade_history.append(trade_record)
        
        return True, f"매도 성공: {stock_code} {quantity}주 @ {price:,}원"
    
    def get_account_info(self):
        """계좌 정보 조회"""
        total_value = self.account_balance
        
        for stock_code, position in self.positions.items():
            stock_info = self.get_stock_price(stock_code)
            if stock_info:
                current_value = stock_info['price'] * position['quantity']
                total_value += current_value
        
        return {
            'cash_balance': self.account_balance,
            'total_value': total_value,
            'positions': len(self.positions),
            'total_positions_value': total_value - self.account_balance
        }
    
    def get_positions(self):
        """보유 종목 조회"""
        positions_info = []
        
        for stock_code, position in self.positions.items():
            stock_info = self.get_stock_price(stock_code)
            if stock_info:
                current_value = stock_info['price'] * position['quantity']
                profit_loss = current_value - (position['avg_price'] * position['quantity'])
                profit_loss_percent = (profit_loss / (position['avg_price'] * position['quantity'])) * 100
                
                positions_info.append({
                    'stock_code': stock_code,
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': stock_info['price'],
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'buy_date': position['buy_date']
                })
        
        return positions_info
    
    def get_trade_history(self, limit=10):
        """거래 내역 조회"""
        return self.trade_history[-limit:] if self.trade_history else []

def test_mock_trading():
    """모의 거래 시스템 테스트"""
    print("🚀 모의 거래 시스템 테스트")
    print("=" * 50)
    
    # 모의 거래 시스템 초기화
    trading_system = MockTradingSystem()
    
    # 1. 계좌 정보 조회
    print("\n1️⃣ 계좌 정보 조회:")
    account_info = trading_system.get_account_info()
    print(f"💰 현금 잔고: {account_info['cash_balance']:,}원")
    print(f"💰 총 자산: {account_info['total_value']:,}원")
    print(f"📊 보유 종목 수: {account_info['positions']}개")
    
    # 2. 주식 가격 조회
    print("\n2️⃣ 주식 가격 조회:")
    for stock in config.WATCH_STOCKS[:3]:  # 처음 3개 종목만
        price_info = trading_system.get_stock_price(stock['code'])
        print(f"📈 {stock['name']}({stock['code']}): {price_info['price']:,}원 ({price_info['change']:+.2f}%)")
    
    # 3. 주식 매수 테스트
    print("\n3️⃣ 주식 매수 테스트:")
    test_stock = config.WATCH_STOCKS[0]
    success, message = trading_system.buy_stock(test_stock['code'], 10)
    print(f"매수 결과: {message}")
    
    # 4. 보유 종목 조회
    print("\n4️⃣ 보유 종목 조회:")
    positions = trading_system.get_positions()
    for pos in positions:
        print(f"📊 {test_stock['name']}: {pos['quantity']}주, 평균단가 {pos['avg_price']:,}원, "
              f"현재가 {pos['current_price']:,}원, 수익률 {pos['profit_loss_percent']:+.2f}%")
    
    # 5. 주식 매도 테스트
    print("\n5️⃣ 주식 매도 테스트:")
    success, message = trading_system.sell_stock(test_stock['code'], 5)
    print(f"매도 결과: {message}")
    
    # 6. 거래 내역 조회
    print("\n6️⃣ 거래 내역 조회:")
    history = trading_system.get_trade_history()
    for trade in history:
        print(f"📝 {trade['timestamp'].strftime('%H:%M:%S')} - {trade['type']}: "
              f"{trade['stock_code']} {trade['quantity']}주 @ {trade['price']:,}원")
    
    # 7. 최종 계좌 정보
    print("\n7️⃣ 최종 계좌 정보:")
    final_account = trading_system.get_account_info()
    print(f"💰 현금 잔고: {final_account['cash_balance']:,}원")
    print(f"💰 총 자산: {final_account['total_value']:,}원")
    print(f"📊 보유 종목 수: {final_account['positions']}개")
    
    print("\n" + "=" * 50)
    print("✅ 모의 거래 시스템 테스트 완료!")
    print("💡 이 시스템을 통해 거래 로직을 테스트할 수 있습니다.")

if __name__ == "__main__":
    test_mock_trading() 