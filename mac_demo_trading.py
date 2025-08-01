#!/usr/bin/env python3
"""
맥용 데모 거래 스크립트
실제 예수금 정보를 사용한 시뮬레이션 거래
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta
from loguru import logger

# 로그 설정
logger.add("logs/mac_demo_trading.log", rotation="1 day", retention="7 days")

class MacDemoTrader:
    """맥용 데모 거래 클래스"""
    
    def __init__(self):
        # 시뮬레이션된 계좌 정보
        self.account = "1234567890"
        self.deposit_info = {
            'account': self.account,
            'deposit': 10000000,  # 1천만원
            'available_deposit': 9500000,  # 950만원
            'orderable_amount': 9000000,  # 900만원
            'timestamp': datetime.now()
        }
        
        self.positions = {}  # 보유 종목
        self.trade_history = []
        
        # 시뮬레이션된 종목 데이터
        self.demo_stocks = {
            '005930': {'name': '삼성전자', 'price': 70000},
            '000660': {'name': 'SK하이닉스', 'price': 120000},
            '035420': {'name': 'NAVER', 'price': 200000},
            '051910': {'name': 'LG화학', 'price': 500000},
            '006400': {'name': '삼성SDI', 'price': 400000}
        }
        
        # 거래 설정
        self.trade_amount = min(100000, self.deposit_info['orderable_amount'] // 10)
        
        logger.info(f"맥용 데모 거래 시스템 초기화 완료")
        logger.info(f"계좌: {self.account}")
        logger.info(f"예수금: {self.deposit_info['deposit']:,}원")
        logger.info(f"주문가능: {self.deposit_info['orderable_amount']:,}원")
        logger.info(f"거래금액: {self.trade_amount:,}원")
    
    def update_deposit_info(self):
        """예수금 정보 업데이트 (시뮬레이션)"""
        # 시뮬레이션된 예수금 변동
        change_rate = random.uniform(-0.01, 0.01)  # -1% ~ +1%
        self.deposit_info['deposit'] = int(self.deposit_info['deposit'] * (1 + change_rate))
        self.deposit_info['orderable_amount'] = int(self.deposit_info['orderable_amount'] * (1 + change_rate))
        self.deposit_info['timestamp'] = datetime.now()
        
        logger.info(f"예수금 업데이트: {self.deposit_info['deposit']:,}원")
    
    def simulate_price_change(self):
        """가격 변동 시뮬레이션"""
        for code in self.demo_stocks:
            # -3% ~ +3% 랜덤 변동
            change_rate = random.uniform(-0.03, 0.03)
            self.demo_stocks[code]['price'] = int(self.demo_stocks[code]['price'] * (1 + change_rate))
    
    def get_current_price(self, code):
        """현재가 조회"""
        return self.demo_stocks.get(code, {}).get('price', 0)
    
    def place_order(self, code, action, quantity, price):
        """주문 실행 (시뮬레이션)"""
        stock_name = self.demo_stocks.get(code, {}).get('name', '알수없음')
        total_amount = quantity * price
        
        if action == "매수":
            if total_amount > self.deposit_info['orderable_amount']:
                logger.warning(f"예수금 부족: 필요 {total_amount:,}원, 보유 {self.deposit_info['orderable_amount']:,}원")
                return None
            
            self.deposit_info['orderable_amount'] -= total_amount
            if code in self.positions:
                self.positions[code]['quantity'] += quantity
                self.positions[code]['avg_price'] = (
                    (self.positions[code]['avg_price'] * self.positions[code]['quantity'] + total_amount) /
                    (self.positions[code]['quantity'] + quantity)
                )
            else:
                self.positions[code] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'name': stock_name
                }
            
            logger.info(f"매수 완료: {stock_name}({code}) {quantity}주 @ {price:,}원")
            
        elif action == "매도":
            if code not in self.positions or self.positions[code]['quantity'] < quantity:
                logger.warning(f"보유 주식 부족: {code}")
                return None
            
            self.deposit_info['orderable_amount'] += total_amount
            self.positions[code]['quantity'] -= quantity
            
            if self.positions[code]['quantity'] == 0:
                del self.positions[code]
            
            logger.info(f"매도 완료: {stock_name}({code}) {quantity}주 @ {price:,}원")
        
        # 거래 내역 기록
        self.trade_history.append({
            'timestamp': datetime.now(),
            'code': code,
            'name': stock_name,
            'action': action,
            'quantity': quantity,
            'price': price,
            'total_amount': total_amount
        })
        
        return f"MAC_ORDER_{len(self.trade_history):03d}"

class MacDemoStrategy:
    """맥용 데모 전략 클래스"""
    
    def __init__(self, trader):
        self.trader = trader
        self.price_history = {}
    
    def update_price_history(self, code, price):
        """가격 이력 업데이트"""
        if code not in self.price_history:
            self.price_history[code] = []
        
        self.price_history[code].append({
            'timestamp': datetime.now(),
            'price': price
        })
        
        # 최근 10개 데이터만 유지
        if len(self.price_history[code]) > 10:
            self.price_history[code] = self.price_history[code][-10:]
    
    def should_buy(self, code, current_price):
        """매수 조건 확인"""
        self.update_price_history(code, current_price)
        
        if len(self.price_history[code]) < 5:
            return False
        
        # 간단한 매수 조건: 가격이 하락했을 때
        recent_prices = [item['price'] for item in self.price_history[code][-5:]]
        if current_price < min(recent_prices[:-1]):
            return True
        
        return False
    
    def should_sell(self, code, current_price):
        """매도 조건 확인"""
        self.update_price_history(code, current_price)
        
        if len(self.price_history[code]) < 5:
            return False
        
        # 간단한 매도 조건: 가격이 상승했을 때
        recent_prices = [item['price'] for item in self.price_history[code][-5:]]
        if current_price > max(recent_prices[:-1]):
            return True
        
        return False

def print_status(trader, strategy):
    """현재 상태 출력"""
    print("\n" + "=" * 60)
    print(f"📊 맥용 데모 거래 상태 - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    print(f"💰 예수금: {trader.deposit_info['deposit']:,}원")
    print(f"💳 주문가능: {trader.deposit_info['orderable_amount']:,}원")
    print(f"📈 보유 종목: {len(trader.positions)}개")
    
    if trader.positions:
        print("\n보유 종목:")
        for code, position in trader.positions.items():
            current_price = trader.get_current_price(code)
            profit_loss = (current_price - position['avg_price']) * position['quantity']
            profit_rate = (current_price / position['avg_price'] - 1) * 100
            
            print(f"  {position['name']}({code}): {position['quantity']}주")
            print(f"    평균단가: {position['avg_price']:,}원")
            print(f"    현재가: {current_price:,}원")
            print(f"    손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
    
    print(f"\n📝 총 거래 횟수: {len(trader.trade_history)}회")

def run_mac_demo():
    """맥용 데모 거래 실행"""
    print("🚀 맥용 데모 거래 시스템 시작")
    print("=" * 60)
    print("이 데모는 시뮬레이션된 데이터를 사용합니다.")
    print("실제 거래는 Windows 서버에서 키움 API를 통해 실행됩니다.")
    print("Ctrl+C로 중단할 수 있습니다.")
    print("=" * 60)
    
    trader = MacDemoTrader()
    strategy = MacDemoStrategy(trader)
    
    try:
        cycle = 0
        while True:
            cycle += 1
            print(f"\n🔄 거래 사이클 {cycle}")
            
            # 예수금 정보 업데이트
            trader.update_deposit_info()
            
            # 가격 변동 시뮬레이션
            trader.simulate_price_change()
            
            # 각 종목에 대해 매매 조건 확인
            for code in trader.demo_stocks:
                current_price = trader.get_current_price(code)
                stock_name = trader.demo_stocks[code]['name']
                
                print(f"  {stock_name}({code}): {current_price:,}원")
                
                # 매수 조건 확인
                if strategy.should_buy(code, current_price):
                    quantity = 10  # 10주씩 매수
                    order = trader.place_order(code, "매수", quantity, current_price)
                    if order:
                        print(f"    -> 매수 신호! {quantity}주 매수")
                
                # 매도 조건 확인
                elif strategy.should_sell(code, current_price):
                    if code in trader.positions:
                        quantity = min(10, trader.positions[code]['quantity'])  # 최대 10주 매도
                        order = trader.place_order(code, "매도", quantity, current_price)
                        if order:
                            print(f"    -> 매도 신호! {quantity}주 매도")
            
            # 상태 출력
            print_status(trader, strategy)
            
            # 3초 대기
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 맥용 데모 거래 중단")
        print("\n📊 최종 결과:")
        print_status(trader, strategy)
        
        # 거래 내역 출력
        if trader.trade_history:
            print(f"\n📝 최근 거래 내역 (최근 10건):")
            for trade in trader.trade_history[-10:]:
                print(f"  {trade['timestamp'].strftime('%H:%M:%S')} - "
                      f"{trade['action']} {trade['name']}({trade['code']}) "
                      f"{trade['quantity']}주 @ {trade['price']:,}원")

if __name__ == "__main__":
    run_mac_demo() 