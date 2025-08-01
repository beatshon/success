"""
자동매매 실행 엔진
실시간으로 시장을 모니터링하고 매매 전략을 실행
"""

import sys
import time
import schedule
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from loguru import logger
import pandas as pd

from kiwoom_api import KiwoomAPI
from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy

class AutoTrader:
    """자동매매 실행 클래스"""
    
    def __init__(self, strategy_type="moving_average", **strategy_params):
        self.app = QApplication(sys.argv)
        self.api = KiwoomAPI()
        
        # 로그인
        self.api.login()
        
        # 계좌 정보 조회
        self.accounts = self.api.get_account_info()
        if not self.accounts:
            logger.error("계좌 정보를 찾을 수 없습니다.")
            return
        
        # 첫 번째 계좌 사용
        self.account = list(self.accounts.keys())[0]
        logger.info(f"사용 계좌: {self.account}")
        
        # 전략 선택
        if strategy_type == "moving_average":
            self.strategy = MovingAverageStrategy(self.api, self.account, **strategy_params)
        elif strategy_type == "rsi":
            self.strategy = RSIStrategy(self.api, self.account, **strategy_params)
        elif strategy_type == "bollinger":
            self.strategy = BollingerBandsStrategy(self.api, self.account, **strategy_params)
        else:
            raise ValueError(f"지원하지 않는 전략: {strategy_type}")
        
        # 모니터링할 종목 리스트
        self.watch_list = []
        
        # 거래 설정
        self.trade_amount = 100000  # 10만원
        self.max_positions = 5  # 최대 보유 종목 수
        
        # 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_trading_cycle)
        
        logger.info(f"자동매매 시스템 초기화 완료 - 전략: {strategy_type}")
    
    def add_watch_stock(self, code, name=""):
        """모니터링 종목 추가"""
        if code not in [item['code'] for item in self.watch_list]:
            self.watch_list.append({
                'code': code,
                'name': name or self.api.get_stock_basic_info(code)['name']
            })
            logger.info(f"모니터링 종목 추가: {code} - {name}")
    
    def remove_watch_stock(self, code):
        """모니터링 종목 제거"""
        self.watch_list = [item for item in self.watch_list if item['code'] != code]
        logger.info(f"모니터링 종목 제거: {code}")
    
    def get_current_positions(self):
        """현재 보유 종목 조회"""
        # 실제 구현에서는 API를 통해 보유 종목을 조회해야 함
        # 여기서는 간단한 예시로 구현
        return self.strategy.position
    
    def calculate_order_quantity(self, price):
        """주문 수량 계산"""
        quantity = self.trade_amount // price
        return max(1, quantity)  # 최소 1주
    
    def run_trading_cycle(self):
        """매매 사이클 실행"""
        try:
            logger.info("매매 사이클 시작")
            
            # 현재 보유 종목 확인
            positions = self.get_current_positions()
            
            # 모니터링 종목들의 현재가 조회
            for stock in self.watch_list:
                code = stock['code']
                current_price = self.api.get_current_price(code)
                
                if not current_price:
                    continue
                
                price = current_price.get('current_price', 0)
                if price == 0:
                    continue
                
                # 매수 조건 확인
                if (code not in positions and 
                    len(positions) < self.max_positions and
                    self.strategy.should_buy(code, price)):
                    
                    quantity = self.calculate_order_quantity(price)
                    self.strategy.execute_trade(code, "매수", quantity, price)
                    
                    # 보유 종목에 추가
                    positions[code] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'buy_time': datetime.now()
                    }
                
                # 매도 조건 확인
                elif (code in positions and 
                      self.strategy.should_sell(code, price)):
                    
                    quantity = positions[code]['quantity']
                    self.strategy.execute_trade(code, "매도", quantity, price)
                    
                    # 보유 종목에서 제거
                    del positions[code]
            
            logger.info("매매 사이클 완료")
            
        except Exception as e:
            logger.error(f"매매 사이클 실행 중 오류: {e}")
    
    def start_trading(self, interval_seconds=60):
        """자동매매 시작"""
        logger.info(f"자동매매 시작 - 주기: {interval_seconds}초")
        
        # 타이머 시작
        self.timer.start(interval_seconds * 1000)
        
        # GUI 이벤트 루프 시작
        sys.exit(self.app.exec_())
    
    def stop_trading(self):
        """자동매매 중지"""
        logger.info("자동매매 중지")
        self.timer.stop()
    
    def get_trade_summary(self):
        """거래 요약 정보"""
        total_trades = len(self.strategy.trade_history)
        buy_trades = len([t for t in self.strategy.trade_history if t['action'] == '매수'])
        sell_trades = len([t for t in self.strategy.trade_history if t['action'] == '매도'])
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'current_positions': len(self.get_current_positions()),
            'watch_list_count': len(self.watch_list)
        }

def main():
    """메인 실행 함수"""
    # 로그 설정
    logger.add("logs/auto_trader_{time}.log", rotation="1 day", retention="7 days")
    
    # 자동매매 시스템 생성 (이동평균 전략)
    trader = AutoTrader(
        strategy_type="moving_average",
        short_period=5,
        long_period=20
    )
    
    # 모니터링 종목 추가 (예시)
    sample_stocks = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "051910",  # LG화학
        "006400"   # 삼성SDI
    ]
    
    for code in sample_stocks:
        trader.add_watch_stock(code)
    
    # 자동매매 시작 (1분마다 실행)
    trader.start_trading(interval_seconds=60)

if __name__ == "__main__":
    main() 