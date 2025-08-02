#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 자동매매 시스템
Mac 환경에서 네이버 트렌드 분석과 키움 API를 연동한 자동매매 시스템
"""

import sys
import time
import threading
import queue
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# Mac 호환 키움 API
from kiwoom_mac_compatible import KiwoomMacAPI, OrderType, OrderStatus

# 네이버 트렌드 분석
from naver_trend_analyzer import NaverTrendAnalyzer

# 에러 처리
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
    kiwoom_server_url: str = "http://localhost:8080"  # 키움 서버 URL

@dataclass
class Position:
    """포지션 정보"""
    code: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    profit_loss: float
    profit_loss_rate: float
    entry_time: datetime
    stop_loss_price: float
    take_profit_price: float

@dataclass
class TradingSignal:
    """거래 신호"""
    code: str
    name: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    price: float
    reason: str
    timestamp: datetime

class IntegratedAutoTrader:
    """통합 자동매매 시스템"""
    
    def __init__(self, config: TradeConfig):
        self.config = config
        
        # 키움 API 초기화
        self.kiwoom_api = KiwoomMacAPI(config.kiwoom_server_url)
        
        # 네이버 트렌드 분석기 초기화
        self.trend_analyzer = NaverTrendAnalyzer()
        
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
            'max_drawdown': 0.0,
            'current_drawdown': 0.0
        }
        
        # 스레드 및 큐
        self.signal_queue = queue.Queue()
        self.trading_thread = None
        self.monitoring_thread = None
        self.analysis_thread = None
        
        # 콜백 함수
        self.on_trade_executed = None
        self.on_position_updated = None
        self.on_error_occurred = None
        
        # 거래 대상 종목
        self.target_stocks = [
            '005930',  # 삼성전자
            '000660',  # SK하이닉스
            '035420',  # NAVER
            '035720',  # 카카오
            '051910',  # LG화학
            '006400',  # 삼성SDI
            '207940',  # 삼성바이오로직스
            '068270',  # 셀트리온
            '323410',  # 카카오뱅크
            '035760'   # CJ대한통운
        ]
        
        logger.info("통합 자동매매 시스템 초기화 완료")
    
    def connect_kiwoom(self, user_id: str, password: str, account: str) -> bool:
        """키움 API 연결 및 로그인"""
        try:
            # 서버 연결
            if not self.kiwoom_api.connect():
                logger.error("키움 서버 연결 실패")
                return False
            
            # 로그인
            if not self.kiwoom_api.login(user_id, password, account):
                logger.error("키움 API 로그인 실패")
                return False
            
            self.is_connected = True
            self.account = account
            
            # 계좌 정보 조회
            account_info = self.kiwoom_api.get_account_info()
            logger.info(f"계좌 정보: {account_info}")
            
            # 예수금 정보 조회
            deposit_info = self.kiwoom_api.get_deposit_info(account)
            if deposit_info:
                self.deposit = float(deposit_info.get('주문가능금액', 0))
                logger.info(f"예수금: {self.deposit:,}원")
            
            # 보유 종목 조회
            self._update_positions()
            
            logger.info("키움 API 연결 및 로그인 성공")
            return True
            
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
        
        # 스레드 시작
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        
        self.trading_thread.start()
        self.monitoring_thread.start()
        self.analysis_thread.start()
        
        logger.info("자동매매 시작")
        return True
    
    def stop_trading(self):
        """자동매매 중지"""
        self.is_running = False
        
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        
        logger.info("자동매매 중지")
    
    def _trading_loop(self):
        """거래 루프"""
        while self.is_running:
            try:
                # 거래 시간 확인
                if not self._is_trading_time():
                    time.sleep(60)
                    continue
                
                # 일일 손실 한도 확인
                if not self._check_daily_loss_limit():
                    logger.warning("일일 손실 한도 초과로 거래 중지")
                    time.sleep(300)  # 5분 대기
                    continue
                
                # 신호 처리
                try:
                    signal = self.signal_queue.get_nowait()
                    self._process_signal(signal)
                except queue.Empty:
                    pass
                
                time.sleep(1)  # 1초 대기
                
            except Exception as e:
                handle_error(
                    ErrorType.TRADING,
                    "거래 루프 에러",
                    exception=e,
                    error_level=ErrorLevel.CRITICAL
                )
                time.sleep(5)
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.is_running:
            try:
                # 포지션 모니터링
                self._monitor_positions()
                
                # 손절매/익절매 확인
                self._check_stop_loss_take_profit()
                
                # 주문 상태 확인
                self._check_order_status()
                
                time.sleep(5)  # 5초 대기
                
            except Exception as e:
                handle_error(
                    ErrorType.MONITORING,
                    "모니터링 루프 에러",
                    exception=e,
                    error_level=ErrorLevel.WARNING
                )
                time.sleep(10)
    
    def _analysis_loop(self):
        """분석 루프"""
        while self.is_running:
            try:
                # 거래 시간 확인
                if not self._is_trading_time():
                    time.sleep(300)  # 5분 대기
                    continue
                
                # 각 종목별 분석
                for stock_code in self.target_stocks:
                    try:
                        # 네이버 트렌드 분석
                        signal = self._analyze_stock(stock_code)
                        
                        if signal and signal.confidence >= self.config.min_confidence:
                            self.signal_queue.put(signal)
                            logger.info(f"신호 생성: {stock_code} {signal.signal_type} (신뢰도: {signal.confidence:.2f})")
                    
                    except Exception as e:
                        handle_error(
                            ErrorType.ANALYSIS,
                            f"종목 분석 실패 ({stock_code})",
                            exception=e,
                            error_level=ErrorLevel.WARNING
                        )
                
                time.sleep(60)  # 1분 대기
                
            except Exception as e:
                handle_error(
                    ErrorType.ANALYSIS,
                    "분석 루프 에러",
                    exception=e,
                    error_level=ErrorLevel.WARNING
                )
                time.sleep(60)
    
    def _analyze_stock(self, stock_code: str) -> Optional[TradingSignal]:
        """종목 분석"""
        try:
            # 현재가 조회
            current_price = self.kiwoom_api.get_current_price(stock_code)
            if not current_price:
                return None
            
            # 네이버 트렌드 분석
            trend_data = self.trend_analyzer.get_investment_signals(stock_code)
            
            if not trend_data:
                return None
            
            # 신호 생성
            signal_type = trend_data.get('overall_signal', 'HOLD')
            confidence = trend_data.get('confidence', 0.0)
            
            # 종목명 조회
            stock_name = self._get_stock_name(stock_code)
            
            signal = TradingSignal(
                code=stock_code,
                name=stock_name,
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                reason=trend_data.get('reason', ''),
                timestamp=datetime.now()
            )
            
            return signal
            
        except Exception as e:
            handle_error(
                ErrorType.ANALYSIS,
                f"종목 분석 실패 ({stock_code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return None
    
    def _process_signal(self, signal: TradingSignal):
        """신호 처리"""
        try:
            if signal.signal_type == 'BUY':
                self._execute_buy_signal(signal)
            elif signal.signal_type == 'SELL':
                self._execute_sell_signal(signal)
            else:
                logger.debug(f"보유 신호: {signal.code}")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"신호 처리 실패 ({signal.code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
    
    def _execute_buy_signal(self, signal: TradingSignal):
        """매수 신호 실행"""
        try:
            # 이미 보유 중인지 확인
            if signal.code in self.positions:
                logger.debug(f"이미 보유 중: {signal.code}")
                return
            
            # 주문 수량 계산
            quantity = self._calculate_position_size(signal.price)
            if quantity <= 0:
                logger.warning(f"주문 수량이 0입니다: {signal.code}")
                return
            
            # 주문 실행
            if self.config.mode == TradeMode.PAPER_TRADING:
                success = self._paper_trading_buy(signal.code, quantity, signal.price)
            else:
                result = self.kiwoom_api.order_stock(
                    self.account, signal.code, quantity, signal.price, "신규매수"
                )
                success = result.get('success', False)
            
            if success:
                # 포지션 추가
                position = Position(
                    code=signal.code,
                    name=signal.name,
                    quantity=quantity,
                    avg_price=signal.price,
                    current_price=signal.price,
                    profit_loss=0.0,
                    profit_loss_rate=0.0,
                    entry_time=datetime.now(),
                    stop_loss_price=signal.price * (1 - self.config.stop_loss_rate),
                    take_profit_price=signal.price * (1 + self.config.take_profit_rate)
                )
                
                self.positions[signal.code] = position
                self.daily_stats['total_trades'] += 1
                
                logger.info(f"매수 성공: {signal.code} {quantity}주 @ {signal.price:,}원")
                
                if self.on_trade_executed:
                    self.on_trade_executed(signal, position)
            else:
                logger.error(f"매수 실패: {signal.code}")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"매수 신호 실행 실패 ({signal.code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
    
    def _execute_sell_signal(self, signal: TradingSignal):
        """매도 신호 실행"""
        try:
            # 보유 중인지 확인
            if signal.code not in self.positions:
                logger.debug(f"보유하지 않음: {signal.code}")
                return
            
            position = self.positions[signal.code]
            
            # 주문 실행
            if self.config.mode == TradeMode.PAPER_TRADING:
                success = self._paper_trading_sell(signal.code, position.quantity, signal.price)
            else:
                result = self.kiwoom_api.order_stock(
                    self.account, signal.code, position.quantity, signal.price, "신규매도"
                )
                success = result.get('success', False)
            
            if success:
                # 수익/손실 계산
                profit_loss = (signal.price - position.avg_price) * position.quantity
                profit_loss_rate = (signal.price - position.avg_price) / position.avg_price
                
                # 성과 업데이트
                self._update_performance(profit_loss)
                
                # 포지션 제거
                del self.positions[signal.code]
                self.daily_stats['total_trades'] += 1
                
                logger.info(f"매도 성공: {signal.code} {position.quantity}주 @ {signal.price:,}원 (손익: {profit_loss:+,}원)")
                
                if self.on_trade_executed:
                    self.on_trade_executed(signal, position)
            else:
                logger.error(f"매도 실패: {signal.code}")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"매도 신호 실행 실패 ({signal.code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
    
    def _paper_trading_buy(self, code: str, quantity: int, price: float) -> bool:
        """페이퍼 트레이딩 매수"""
        try:
            total_cost = quantity * price
            if total_cost > self.deposit:
                logger.warning(f"예수금 부족: {code}")
                return False
            
            self.deposit -= total_cost
            logger.info(f"페이퍼 매수: {code} {quantity}주 @ {price:,}원 (잔고: {self.deposit:,}원)")
            return True
            
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"페이퍼 매수 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return False
    
    def _paper_trading_sell(self, code: str, quantity: int, price: float) -> bool:
        """페이퍼 트레이딩 매도"""
        try:
            total_revenue = quantity * price
            self.deposit += total_revenue
            logger.info(f"페이퍼 매도: {code} {quantity}주 @ {price:,}원 (잔고: {self.deposit:,}원)")
            return True
            
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"페이퍼 매도 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return False
    
    def _calculate_position_size(self, price: float) -> int:
        """주문 수량 계산"""
        try:
            max_amount = self.deposit * self.config.max_position_size
            quantity = int(max_amount / price)
            return max(quantity, 1)  # 최소 1주
            
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                "주문 수량 계산 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return 0
    
    def _monitor_positions(self):
        """포지션 모니터링"""
        try:
            # 현재가 업데이트
            self._update_position_prices()
            
            # 포지션 정보 업데이트
            for code, position in self.positions.items():
                old_pl = position.profit_loss
                position.profit_loss = (position.current_price - position.avg_price) * position.quantity
                position.profit_loss_rate = (position.current_price - position.avg_price) / position.avg_price
                
                # 콜백 호출
                if self.on_position_updated and old_pl != position.profit_loss:
                    self.on_position_updated(position)
                    
        except Exception as e:
            handle_error(
                ErrorType.MONITORING,
                "포지션 모니터링 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _check_stop_loss_take_profit(self):
        """손절매/익절매 확인"""
        try:
            for code, position in list(self.positions.items()):
                # 손절매 확인
                if position.current_price <= position.stop_loss_price:
                    logger.warning(f"손절매 실행: {code} @ {position.current_price:,}원")
                    self._execute_stop_loss(position)
                
                # 익절매 확인
                elif position.current_price >= position.take_profit_price:
                    logger.info(f"익절매 실행: {code} @ {position.current_price:,}원")
                    self._execute_take_profit(position)
                    
        except Exception as e:
            handle_error(
                ErrorType.MONITORING,
                "손절매/익절매 확인 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _execute_stop_loss(self, position: Position):
        """손절매 실행"""
        try:
            if self.config.mode == TradeMode.PAPER_TRADING:
                success = self._paper_trading_sell(position.code, position.quantity, position.current_price)
            else:
                result = self.kiwoom_api.order_stock(
                    self.account, position.code, position.quantity, position.current_price, "신규매도"
                )
                success = result.get('success', False)
            
            if success:
                profit_loss = (position.current_price - position.avg_price) * position.quantity
                self._update_performance(profit_loss)
                del self.positions[position.code]
                self.daily_stats['total_trades'] += 1
                
                logger.info(f"손절매 완료: {position.code} (손실: {profit_loss:+,}원)")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"손절매 실행 실패 ({position.code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
    
    def _execute_take_profit(self, position: Position):
        """익절매 실행"""
        try:
            if self.config.mode == TradeMode.PAPER_TRADING:
                success = self._paper_trading_sell(position.code, position.quantity, position.current_price)
            else:
                result = self.kiwoom_api.order_stock(
                    self.account, position.code, position.quantity, position.current_price, "신규매도"
                )
                success = result.get('success', False)
            
            if success:
                profit_loss = (position.current_price - position.avg_price) * position.quantity
                self._update_performance(profit_loss)
                del self.positions[position.code]
                self.daily_stats['total_trades'] += 1
                
                logger.info(f"익절매 완료: {position.code} (수익: {profit_loss:+,}원)")
                
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                f"익절매 실행 실패 ({position.code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
    
    def _update_position_prices(self):
        """포지션 가격 업데이트"""
        try:
            for code in self.positions:
                current_price = self.kiwoom_api.get_current_price(code)
                if current_price:
                    self.positions[code].current_price = current_price
                    
        except Exception as e:
            handle_error(
                ErrorType.MONITORING,
                "포지션 가격 업데이트 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _update_positions(self):
        """보유 종목 업데이트"""
        try:
            position_info = self.kiwoom_api.get_position_info(self.account)
            if position_info:
                # 보유 종목 정보 파싱 및 업데이트
                # 실제 구현에서는 position_info의 구조에 따라 파싱 필요
                pass
                
        except Exception as e:
            handle_error(
                ErrorType.MONITORING,
                "보유 종목 업데이트 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _check_order_status(self):
        """주문 상태 확인"""
        try:
            # 주문 상태 확인 로직
            # 실제 구현에서는 키움 API를 통해 주문 상태 조회
            pass
            
        except Exception as e:
            handle_error(
                ErrorType.MONITORING,
                "주문 상태 확인 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _is_trading_time(self) -> bool:
        """거래 시간 확인"""
        now = datetime.now()
        start_hour, end_hour = self.config.trading_hours
        
        # 주말 제외
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 거래 시간 확인
        return start_hour <= now.hour < end_hour
    
    def _check_daily_loss_limit(self) -> bool:
        """일일 손실 한도 확인"""
        try:
            total_pl = self.daily_stats['total_profit'] + self.daily_stats['total_loss']
            loss_rate = abs(min(total_pl, 0)) / self.deposit if self.deposit > 0 else 0
            
            return loss_rate <= self.config.max_daily_loss
            
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                "일일 손실 한도 확인 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return True
    
    def _update_performance(self, profit_loss: float):
        """성과 업데이트"""
        try:
            if profit_loss > 0:
                self.daily_stats['winning_trades'] += 1
                self.daily_stats['total_profit'] += profit_loss
            else:
                self.daily_stats['losing_trades'] += 1
                self.daily_stats['total_loss'] += profit_loss
            
            # 최대 낙폭 계산
            total_pl = self.daily_stats['total_profit'] + self.daily_stats['total_loss']
            if total_pl < self.daily_stats['max_drawdown']:
                self.daily_stats['max_drawdown'] = total_pl
            
            self.daily_stats['current_drawdown'] = total_pl
            
        except Exception as e:
            handle_error(
                ErrorType.TRADING,
                "성과 업데이트 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _get_stock_name(self, code: str) -> str:
        """종목명 조회"""
        stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI',
            '207940': '삼성바이오로직스',
            '068270': '셀트리온',
            '323410': '카카오뱅크',
            '035760': 'CJ대한통운'
        }
        return stock_names.get(code, f'종목({code})')
    
    def get_performance_summary(self) -> Dict:
        """성과 요약"""
        try:
            total_trades = self.daily_stats['total_trades']
            win_rate = (self.daily_stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0
            
            total_pl = self.daily_stats['total_profit'] + self.daily_stats['total_loss']
            total_return = (total_pl / self.deposit * 100) if self.deposit > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': self.daily_stats['winning_trades'],
                'losing_trades': self.daily_stats['losing_trades'],
                'win_rate': round(win_rate, 2),
                'total_profit': self.daily_stats['total_profit'],
                'total_loss': self.daily_stats['total_loss'],
                'total_pl': total_pl,
                'total_return': round(total_return, 2),
                'max_drawdown': self.daily_stats['max_drawdown'],
                'current_drawdown': self.daily_stats['current_drawdown'],
                'deposit': self.deposit,
                'positions_count': len(self.positions)
            }
            
        except Exception as e:
            handle_error(
                ErrorType.ANALYSIS,
                "성과 요약 생성 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def set_callbacks(self, on_trade_executed=None, on_position_updated=None, on_error_occurred=None):
        """콜백 함수 설정"""
        self.on_trade_executed = on_trade_executed
        self.on_position_updated = on_position_updated
        self.on_error_occurred = on_error_occurred

def main():
    """메인 함수"""
    try:
        # 설정
        config = TradeConfig(
            mode=TradeMode.PAPER_TRADING,  # 페이퍼 트레이딩 모드
            max_position_size=0.1,         # 최대 10%
            stop_loss_rate=0.05,           # 5% 손절매
            take_profit_rate=0.15,         # 15% 익절매
            max_daily_loss=0.03,           # 일일 최대 3% 손실
            min_confidence=0.7,            # 최소 70% 신뢰도
            trading_hours=(9, 15),         # 9시~15시
            max_orders_per_day=10,         # 일일 최대 10주문
            kiwoom_server_url="http://localhost:8080"
        )
        
        # 자동매매 시스템 생성
        trader = IntegratedAutoTrader(config)
        
        # 콜백 함수 설정
        def on_trade_executed(signal, position):
            logger.info(f"거래 실행: {signal.code} {signal.signal_type}")
        
        def on_position_updated(position):
            logger.info(f"포지션 업데이트: {position.code} (손익: {position.profit_loss:+,}원)")
        
        def on_error_occurred(error_type, message, exception):
            logger.error(f"에러 발생: {error_type} - {message}")
        
        trader.set_callbacks(on_trade_executed, on_position_updated, on_error_occurred)
        
        # 키움 API 연결 (실제 계정 정보 필요)
        # if trader.connect_kiwoom("user_id", "password", "account"):
        #     # 자동매매 시작
        #     if trader.start_trading():
        #         logger.info("자동매매 시작됨")
        #         
        #         # 무한 루프
        #         try:
        #             while True:
        #                 time.sleep(60)
        #                 
        #                 # 성과 출력
        #                 summary = trader.get_performance_summary()
        #                 if summary:
        #                     logger.info(f"성과: {summary}")
        #                     
        #         except KeyboardInterrupt:
        #             trader.stop_trading()
        #             logger.info("자동매매 종료")
        #     else:
        #         logger.error("자동매매 시작 실패")
        # else:
        #     logger.error("키움 API 연결 실패")
        
        # 테스트용 (연결 없이)
        logger.info("테스트 모드로 실행")
        trader.is_connected = True
        trader.account = "TEST_ACCOUNT"
        trader.deposit = 10000000  # 1천만원
        
        if trader.start_trading():
            logger.info("테스트 자동매매 시작됨")
            
            try:
                while True:
                    time.sleep(60)
                    
                    # 성과 출력
                    summary = trader.get_performance_summary()
                    if summary:
                        logger.info(f"성과: {summary}")
                        
            except KeyboardInterrupt:
                trader.stop_trading()
                logger.info("테스트 자동매매 종료")
        else:
            logger.error("테스트 자동매매 시작 실패")
        
    except Exception as e:
        logger.error(f"자동매매 시스템 실행 실패: {e}")

if __name__ == "__main__":
    main() 