"""
자동매매 전략 클래스
다양한 매매 전략을 구현
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
from abc import ABC, abstractmethod

class TradingStrategy(ABC):
    """매매 전략 기본 클래스"""
    
    def __init__(self, api, account):
        self.api = api
        self.account = account
        self.position = {}  # 보유 종목
        self.trade_history = []  # 거래 내역
        
    @abstractmethod
    def should_buy(self, code, current_price, **kwargs):
        """매수 조건 확인"""
        pass
    
    @abstractmethod
    def should_sell(self, code, current_price, **kwargs):
        """매도 조건 확인"""
        pass
    
    def execute_trade(self, code, action, quantity, price):
        """거래 실행"""
        try:
            if action == "매수":
                order_no = self.api.order_stock(self.account, code, quantity, price, "신규매수")
                logger.info(f"매수 주문 실행: {code} - {quantity}주 - {price:,}원")
            elif action == "매도":
                order_no = self.api.order_stock(self.account, code, quantity, price, "신규매도")
                logger.info(f"매도 주문 실행: {code} - {quantity}주 - {price:,}원")
            
            # 거래 내역 기록
            self.trade_history.append({
                'timestamp': datetime.now(),
                'code': code,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_no': order_no
            })
            
            return order_no
        except Exception as e:
            logger.error(f"거래 실행 실패: {e}")
            return None

class MovingAverageStrategy(TradingStrategy):
    """이동평균 크로스오버 전략"""
    
    def __init__(self, api, account, short_period=5, long_period=20):
        super().__init__(api, account)
        self.short_period = short_period
        self.long_period = long_period
        self.price_history = {}  # 종목별 가격 이력
        
    def update_price_history(self, code, price):
        """가격 이력 업데이트"""
        if code not in self.price_history:
            self.price_history[code] = []
        
        self.price_history[code].append({
            'timestamp': datetime.now(),
            'price': price
        })
        
        # 최근 100개 데이터만 유지
        if len(self.price_history[code]) > 100:
            self.price_history[code] = self.price_history[code][-100:]
    
    def calculate_moving_averages(self, code):
        """이동평균 계산"""
        if code not in self.price_history or len(self.price_history[code]) < self.long_period:
            return None, None
        
        prices = [item['price'] for item in self.price_history[code]]
        
        short_ma = np.mean(prices[-self.short_period:])
        long_ma = np.mean(prices[-self.long_period:])
        
        return short_ma, long_ma
    
    def should_buy(self, code, current_price, **kwargs):
        """매수 조건: 단기 이평선이 장기 이평선을 상향 돌파"""
        self.update_price_history(code, current_price)
        short_ma, long_ma = self.calculate_moving_averages(code)
        
        if short_ma is None or long_ma is None:
            return False
        
        # 이전 값들 확인
        if len(self.price_history[code]) < self.long_period + 1:
            return False
        
        prev_prices = [item['price'] for item in self.price_history[code][-self.long_period-1:-1]]
        prev_short_ma = np.mean(prev_prices[-self.short_period:])
        prev_long_ma = np.mean(prev_prices[-self.long_period:])
        
        # 골든크로스 확인
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            logger.info(f"골든크로스 발생: {code} - 단기이평: {short_ma:.0f}, 장기이평: {long_ma:.0f}")
            return True
        
        return False
    
    def should_sell(self, code, current_price, **kwargs):
        """매도 조건: 단기 이평선이 장기 이평선을 하향 돌파"""
        self.update_price_history(code, current_price)
        short_ma, long_ma = self.calculate_moving_averages(code)
        
        if short_ma is None or long_ma is None:
            return False
        
        # 이전 값들 확인
        if len(self.price_history[code]) < self.long_period + 1:
            return False
        
        prev_prices = [item['price'] for item in self.price_history[code][-self.long_period-1:-1]]
        prev_short_ma = np.mean(prev_prices[-self.short_period:])
        prev_long_ma = np.mean(prev_prices[-self.long_period:])
        
        # 데드크로스 확인
        if prev_short_ma >= prev_long_ma and short_ma < long_ma:
            logger.info(f"데드크로스 발생: {code} - 단기이평: {short_ma:.0f}, 장기이평: {long_ma:.0f}")
            return True
        
        return False

class RSIStrategy(TradingStrategy):
    """RSI 전략"""
    
    def __init__(self, api, account, period=14, oversold=30, overbought=70):
        super().__init__(api, account)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.price_history = {}
        
    def calculate_rsi(self, code):
        """RSI 계산"""
        if code not in self.price_history or len(self.price_history[code]) < self.period + 1:
            return None
        
        prices = [item['price'] for item in self.price_history[code]]
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def update_price_history(self, code, price):
        """가격 이력 업데이트"""
        if code not in self.price_history:
            self.price_history[code] = []
        
        self.price_history[code].append({
            'timestamp': datetime.now(),
            'price': price
        })
        
        # 최근 100개 데이터만 유지
        if len(self.price_history[code]) > 100:
            self.price_history[code] = self.price_history[code][-100:]
    
    def should_buy(self, code, current_price, **kwargs):
        """매수 조건: RSI가 과매도 구간에서 반등"""
        self.update_price_history(code, current_price)
        rsi = self.calculate_rsi(code)
        
        if rsi is None:
            return False
        
        # 이전 RSI 값 확인
        if len(self.price_history[code]) < self.period + 2:
            return False
        
        prev_prices = [item['price'] for item in self.price_history[code][-self.period-2:-1]]
        prev_deltas = np.diff(prev_prices)
        prev_gains = np.where(prev_deltas > 0, prev_deltas, 0)
        prev_losses = np.where(prev_deltas < 0, -prev_deltas, 0)
        
        prev_avg_gain = np.mean(prev_gains[-self.period:])
        prev_avg_loss = np.mean(prev_losses[-self.period:])
        
        if prev_avg_loss == 0:
            prev_rsi = 100
        else:
            prev_rs = prev_avg_gain / prev_avg_loss
            prev_rsi = 100 - (100 / (1 + prev_rs))
        
        # RSI가 과매도 구간에서 반등하는 경우
        if prev_rsi < self.oversold and rsi > self.oversold:
            logger.info(f"RSI 매수 신호: {code} - RSI: {rsi:.1f}")
            return True
        
        return False
    
    def should_sell(self, code, current_price, **kwargs):
        """매도 조건: RSI가 과매수 구간에서 하락"""
        self.update_price_history(code, current_price)
        rsi = self.calculate_rsi(code)
        
        if rsi is None:
            return False
        
        # 이전 RSI 값 확인
        if len(self.price_history[code]) < self.period + 2:
            return False
        
        prev_prices = [item['price'] for item in self.price_history[code][-self.period-2:-1]]
        prev_deltas = np.diff(prev_prices)
        prev_gains = np.where(prev_deltas > 0, prev_deltas, 0)
        prev_losses = np.where(prev_deltas < 0, -prev_deltas, 0)
        
        prev_avg_gain = np.mean(prev_gains[-self.period:])
        prev_avg_loss = np.mean(prev_losses[-self.period:])
        
        if prev_avg_loss == 0:
            prev_rsi = 100
        else:
            prev_rs = prev_avg_gain / prev_avg_loss
            prev_rsi = 100 - (100 / (1 + prev_rs))
        
        # RSI가 과매수 구간에서 하락하는 경우
        if prev_rsi > self.overbought and rsi < self.overbought:
            logger.info(f"RSI 매도 신호: {code} - RSI: {rsi:.1f}")
            return True
        
        return False

class BollingerBandsStrategy(TradingStrategy):
    """볼린저 밴드 전략"""
    
    def __init__(self, api, account, period=20, std_dev=2):
        super().__init__(api, account)
        self.period = period
        self.std_dev = std_dev
        self.price_history = {}
        
    def calculate_bollinger_bands(self, code):
        """볼린저 밴드 계산"""
        if code not in self.price_history or len(self.price_history[code]) < self.period:
            return None, None, None
        
        prices = [item['price'] for item in self.price_history[code][-self.period:]]
        
        middle_band = np.mean(prices)
        std = np.std(prices)
        
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)
        
        return upper_band, middle_band, lower_band
    
    def update_price_history(self, code, price):
        """가격 이력 업데이트"""
        if code not in self.price_history:
            self.price_history[code] = []
        
        self.price_history[code].append({
            'timestamp': datetime.now(),
            'price': price
        })
        
        # 최근 100개 데이터만 유지
        if len(self.price_history[code]) > 100:
            self.price_history[code] = self.price_history[code][-100:]
    
    def should_buy(self, code, current_price, **kwargs):
        """매수 조건: 가격이 하단 밴드에 닿았을 때"""
        self.update_price_history(code, current_price)
        upper, middle, lower = self.calculate_bollinger_bands(code)
        
        if lower is None:
            return False
        
        # 가격이 하단 밴드 근처에 있을 때
        if current_price <= lower * 1.01:  # 1% 여유
            logger.info(f"볼린저 밴드 매수 신호: {code} - 현재가: {current_price:,}, 하단밴드: {lower:.0f}")
            return True
        
        return False
    
    def should_sell(self, code, current_price, **kwargs):
        """매도 조건: 가격이 상단 밴드에 닿았을 때"""
        self.update_price_history(code, current_price)
        upper, middle, lower = self.calculate_bollinger_bands(code)
        
        if upper is None:
            return False
        
        # 가격이 상단 밴드 근처에 있을 때
        if current_price >= upper * 0.99:  # 1% 여유
            logger.info(f"볼린저 밴드 매도 신호: {code} - 현재가: {current_price:,}, 상단밴드: {upper:.0f}")
            return True
        
        return False 