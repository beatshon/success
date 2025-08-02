#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 자동매매 시스템
키움 API와 연동하여 실제 주식 거래를 자동으로 실행합니다.
"""

import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger

# 기존 모듈 import
from kiwoom_api import KiwoomAPI, OrderType, OrderStatus
from trading_strategy import StrategyBase, TradingSignal, SignalType
from hybrid_trading_system import HybridTradingSystem
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation

class TradeMode(Enum):
    """거래 모드"""
    PAPER_TRADING = "페이퍼 트레이딩"  # 모의 거래
    REAL_TRADING = "실제 거래"        # 실제 거래
    SIMULATION = "시뮬레이션"         # 시뮬레이션

@dataclass
class TradeConfig:
    """거래 설정"""
    mode: TradeMode = TradeMode.PAPER_TRADING
    max_position_size: float = 0.1  # 전체 자금의 최대 10%
    stop_loss_rate: float = 0.05    # 5% 손절매
    take_profit_rate: float = 0.15  # 15% 익절매
    max_daily_loss: float = 0.03    # 일일 최대 손실 3%
    min_confidence: float = 0.7     # 최소 신뢰도 70%
    trading_hours: tuple = (9, 15)  # 거래 시간 (9시~15시)
    max_orders_per_day: int = 10    # 일일 최대 주문 수

@dataclass
class Position:
    """포지션 정보"""
    code: str
    quantity: int
    avg_price: float
    current_price: float
    profit_loss: float
    profit_loss_rate: float
    entry_time: datetime
    stop_loss_price: float
    take_profit_price: float

class AutoTrader:
    """실시간 자동매매 시스템"""
    
    def __init__(self, config: TradeConfig):
        self.config = config
        self.kiwoom_api = None
        self.hybrid_system = HybridTradingSystem()
        
        # 거래 상태
        self.is_running = False
        self.is_connected = False
        self.account = None
        self.deposit = 0
        
        # 포지션 관리
        self.positions: Dict[str, Position] = {}
        self.pending_orders = {}
        self.order_history = []
        
        # 성과 추적
        self.daily_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_drawdown': 0.0
        }
        
        # 스레드 및 큐
        self.signal_queue = queue.Queue()
        self.trading_thread = None
        self.monitoring_thread = None
        
        # 콜백 함수
        self.on_trade_executed = None
        self.on_position_updated = None
        self.on_error_occurred = None
        
        logger.info("자동매매 시스템 초기화 완료")
    
    def connect_kiwoom(self, account: str = None) -> bool:
        """키움 API 연결"""
        try:
            self.kiwoom_api = KiwoomAPI()
            
            # 로그인
            if self.kiwoom_api.login():
                self.is_connected = True
                logger.info("키움 API 연결 성공")
                
                # 계좌 정보 설정
                if account:
                    self.account = account
                else:
                    accounts = self.kiwoom_api.get_account_info()
                    if accounts:
                        self.account = list(accounts.keys())[0]
                
                # 예수금 조회
                if self.account:
                    self.deposit = self.kiwoom_api.get_deposit_info(self.account)
                    logger.info(f"계좌: {self.account}, 예수금: {self.deposit:,}원")
                
                return True
            else:
                logger.error("키움 API 로그인 실패")
                return False
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                "키움 API 연결 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            return False
    
    def start_trading(self):
        """자동매매 시작"""
        if not self.is_connected:
            logger.error("키움 API가 연결되지 않았습니다.")
            return False
        
        if self.is_running:
            logger.warning("자동매매가 이미 실행 중입니다.")
            return True
        
        self.is_running = True
        
        # 거래 스레드 시작
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        
        # 모니터링 스레드 시작
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("자동매매 시작")
        return True
    
    def stop_trading(self):
        """자동매매 중지"""
        self.is_running = False
        
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("자동매매 중지")
    
    def _trading_loop(self):
        """거래 실행 루프"""
        while self.is_running:
            try:
                # 거래 시간 확인
                if not self._is_trading_time():
                    time.sleep(60)
                    continue
                
                # 하이브리드 분석 실행
                signals = self.hybrid_system.analyze_all_stocks()
                
                # 신호 처리
                for signal in signals:
                    if signal.combined_score >= self.config.min_confidence:
                        self._process_signal(signal)
                
                # 포지션 모니터링
                self._monitor_positions()
                
                # 일일 손실 한도 확인
                if self._check_daily_loss_limit():
                    logger.warning("일일 손실 한도 도달. 거래 중지")
                    break
                
                time.sleep(300)  # 5분 대기
                
            except Exception as e:
                handle_error(
                    ErrorType.TRADING,
                    "거래 루프 오류",
                    exception=e,
                    error_level=ErrorLevel.HIGH
                )
                time.sleep(60)
    
    def _monitoring_loop(self):
        """포지션 모니터링 루프"""
        while self.is_running:
            try:
                # 실시간 가격 업데이트
                self._update_position_prices()
                
                # 손절매/익절매 체크
                self._check_stop_loss_take_profit()
                
                # 주문 상태 확인
                self._check_order_status()
                
                time.sleep(10)  # 10초 대기
                
            except Exception as e:
                handle_error(
                    ErrorType.MONITORING,
                    "모니터링 루프 오류",
                    exception=e,
                    error_level=ErrorLevel.MEDIUM
                )
                time.sleep(30)
    
    def _process_signal(self, signal):
        """매매 신호 처리"""
        try:
            if signal.final_signal == "매수" and signal.combined_score >= self.config.min_confidence:
                self._execute_buy_signal(signal)
            elif signal.final_signal == "매도":
                self._execute_sell_signal(signal)
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"신호 처리 오류: {signal.stock_code}",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def _execute_buy_signal(self, signal):
        """매수 신호 실행"""
        try:
            # 현재 가격 조회
            current_price = self.kiwoom_api.get_current_price(signal.stock_code)
            if not current_price:
                return
            
            # 포지션 사이징 계산
            quantity = self._calculate_position_size(current_price)
            if quantity <= 0:
                return
            
            # 주문 실행
            if self.config.mode == TradeMode.REAL_TRADING:
                order_result = self.kiwoom_api.buy_stock(
                    self.account, 
                    signal.stock_code, 
                    quantity, 
                    current_price
                )
            else:
                # 페이퍼 트레이딩
                order_result = self._paper_trading_buy(signal.stock_code, quantity, current_price)
            
            if order_result:
                # 포지션 정보 생성
                position = Position(
                    code=signal.stock_code,
                    quantity=quantity,
                    avg_price=current_price,
                    current_price=current_price,
                    profit_loss=0.0,
                    profit_loss_rate=0.0,
                    entry_time=datetime.now(),
                    stop_loss_price=current_price * (1 - self.config.stop_loss_rate),
                    take_profit_price=current_price * (1 + self.config.take_profit_rate)
                )
                
                self.positions[signal.stock_code] = position
                
                logger.info(f"매수 주문 실행: {signal.stock_code}, 수량: {quantity}, 가격: {current_price:,}원")
                
                # 콜백 실행
                if self.on_trade_executed:
                    self.on_trade_executed(signal, position)
                    
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"매수 주문 실행 오류: {signal.stock_code}",
                exception=e,
                error_level=ErrorLevel.HIGH
            )
    
    def _execute_sell_signal(self, signal):
        """매도 신호 실행"""
        try:
            if signal.stock_code not in self.positions:
                return
            
            position = self.positions[signal.stock_code]
            current_price = self.kiwoom_api.get_current_price(signal.stock_code)
            
            if not current_price:
                return
            
            # 주문 실행
            if self.config.mode == TradeMode.REAL_TRADING:
                order_result = self.kiwoom_api.sell_stock(
                    self.account,
                    signal.stock_code,
                    position.quantity,
                    current_price
                )
            else:
                # 페이퍼 트레이딩
                order_result = self._paper_trading_sell(signal.stock_code, position.quantity, current_price)
            
            if order_result:
                # 수익/손실 계산
                profit_loss = (current_price - position.avg_price) * position.quantity
                
                # 포지션 제거
                del self.positions[signal.stock_code]
                
                # 성과 업데이트
                self._update_performance(profit_loss)
                
                logger.info(f"매도 주문 실행: {signal.stock_code}, 수익: {profit_loss:,}원")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"매도 주문 실행 오류: {signal.stock_code}",
                exception=e,
                error_level=ErrorLevel.HIGH
            )
    
    def _paper_trading_buy(self, code: str, quantity: int, price: float) -> bool:
        """페이퍼 트레이딩 매수"""
        cost = quantity * price
        if cost > self.deposit:
            return False
        
        self.deposit -= cost
        return True
    
    def _paper_trading_sell(self, code: str, quantity: int, price: float) -> bool:
        """페이퍼 트레이딩 매도"""
        revenue = quantity * price
        self.deposit += revenue
        return True
    
    def _calculate_position_size(self, price: float) -> int:
        """포지션 사이징 계산"""
        max_amount = self.deposit * self.config.max_position_size
        quantity = int(max_amount / price)
        return max(1, quantity)  # 최소 1주
    
    def _monitor_positions(self):
        """포지션 모니터링"""
        for code, position in self.positions.items():
            current_price = self.kiwoom_api.get_current_price(code)
            if current_price:
                position.current_price = current_price
                position.profit_loss = (current_price - position.avg_price) * position.quantity
                position.profit_loss_rate = (current_price - position.avg_price) / position.avg_price
                
                # 콜백 실행
                if self.on_position_updated:
                    self.on_position_updated(position)
    
    def _check_stop_loss_take_profit(self):
        """손절매/익절매 체크"""
        for code, position in list(self.positions.items()):
            current_price = position.current_price
            
            # 손절매 체크
            if current_price <= position.stop_loss_price:
                logger.warning(f"손절매 실행: {code}, 가격: {current_price:,}원")
                self._execute_sell_signal(type('Signal', (), {
                    'stock_code': code,
                    'final_signal': '매도',
                    'combined_score': 1.0
                })())
            
            # 익절매 체크
            elif current_price >= position.take_profit_price:
                logger.info(f"익절매 실행: {code}, 가격: {current_price:,}원")
                self._execute_sell_signal(type('Signal', (), {
                    'stock_code': code,
                    'final_signal': '매도',
                    'combined_score': 1.0
                })())
    
    def _update_position_prices(self):
        """포지션 가격 업데이트"""
        for code in self.positions:
            current_price = self.kiwoom_api.get_current_price(code)
            if current_price:
                self.positions[code].current_price = current_price
    
    def _check_order_status(self):
        """주문 상태 확인"""
        if self.config.mode == TradeMode.REAL_TRADING:
            pending_orders = self.kiwoom_api.get_pending_orders()
            for order_no, order_info in pending_orders.items():
                status = self.kiwoom_api.get_order_status(order_no)
                if status == OrderStatus.FILLED:
                    logger.info(f"주문 체결: {order_no}")
                elif status == OrderStatus.REJECTED:
                    logger.error(f"주문 거부: {order_no}")
    
    def _is_trading_time(self) -> bool:
        """거래 시간 확인"""
        now = datetime.now()
        start_hour, end_hour = self.config.trading_hours
        
        # 주말 체크
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 거래 시간 체크
        return start_hour <= now.hour < end_hour
    
    def _check_daily_loss_limit(self) -> bool:
        """일일 손실 한도 체크"""
        daily_loss = self.daily_stats['total_loss']
        max_daily_loss = self.deposit * self.config.max_daily_loss
        
        return daily_loss >= max_daily_loss
    
    def _update_performance(self, profit_loss: float):
        """성과 업데이트"""
        self.daily_stats['total_trades'] += 1
        
        if profit_loss > 0:
            self.daily_stats['winning_trades'] += 1
            self.daily_stats['total_profit'] += profit_loss
        else:
            self.daily_stats['losing_trades'] += 1
            self.daily_stats['total_loss'] += abs(profit_loss)
    
    def get_performance_summary(self) -> Dict:
        """성과 요약 반환"""
        total_trades = self.daily_stats['total_trades']
        win_rate = (self.daily_stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': self.daily_stats['winning_trades'],
            'losing_trades': self.daily_stats['losing_trades'],
            'win_rate': round(win_rate, 2),
            'total_profit': self.daily_stats['total_profit'],
            'total_loss': self.daily_stats['total_loss'],
            'net_profit': self.daily_stats['total_profit'] - self.daily_stats['total_loss'],
            'max_drawdown': self.daily_stats['max_drawdown'],
            'current_positions': len(self.positions),
            'available_deposit': self.deposit
        }
    
    def set_callbacks(self, on_trade_executed=None, on_position_updated=None, on_error_occurred=None):
        """콜백 함수 설정"""
        self.on_trade_executed = on_trade_executed
        self.on_position_updated = on_position_updated
        self.on_error_occurred = on_error_occurred

def main():
    """메인 함수"""
    # 거래 설정
    config = TradeConfig(
        mode=TradeMode.PAPER_TRADING,  # 페이퍼 트레이딩으로 시작
        max_position_size=0.1,
        stop_loss_rate=0.05,
        take_profit_rate=0.15,
        max_daily_loss=0.03,
        min_confidence=0.7
    )
    
    # 자동매매 시스템 생성
    trader = AutoTrader(config)
    
    # 콜백 함수 설정
    def on_trade_executed(signal, position):
        logger.info(f"거래 실행: {signal.stock_code}, 신뢰도: {signal.combined_score:.2f}")
    
    def on_position_updated(position):
        logger.info(f"포지션 업데이트: {position.code}, 수익률: {position.profit_loss_rate:.2%}")
    
    trader.set_callbacks(
        on_trade_executed=on_trade_executed,
        on_position_updated=on_position_updated
    )
    
    # 키움 API 연결
    if trader.connect_kiwoom():
        # 자동매매 시작
        trader.start_trading()
        
        try:
            while True:
                time.sleep(60)
                # 성과 출력
                performance = trader.get_performance_summary()
                logger.info(f"성과: {performance}")
        except KeyboardInterrupt:
            logger.info("프로그램 종료")
            trader.stop_trading()
    else:
        logger.error("키움 API 연결 실패")

if __name__ == "__main__":
    main() 