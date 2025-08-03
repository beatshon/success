#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 자동매매 시스템
키움 API와 트레이딩 전략을 통합하여 완전한 자동매매 시스템을 제공합니다.
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# 키움 API 및 전략 모듈들
from kiwoom_mac_compatible import KiwoomMacAPI
from trading_strategy import (
    StrategyManager, create_default_strategies, TradingSignal, 
    SignalType, StrategyType
)
from technical_indicators import calculate_sma, calculate_rsi
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation

class TradingMode(Enum):
    """거래 모드"""
    PAPER_TRADING = "페이퍼트레이딩"
    REAL_TRADING = "실제거래"
    SIMULATION = "시뮬레이션"

class RiskLevel(Enum):
    """위험 수준"""
    LOW = "낮음"
    MEDIUM = "보통"
    HIGH = "높음"
    VERY_HIGH = "매우높음"

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
    timestamp: datetime

@dataclass
class TradeConfig:
    """거래 설정"""
    # 기본 설정
    trading_mode: TradingMode = TradingMode.PAPER_TRADING
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # 자금 관리
    initial_capital: float = 10000000  # 1천만원
    max_position_size: float = 1000000  # 100만원
    daily_loss_limit: float = 500000   # 50만원
    max_positions: int = 5
    
    # 손절/익절
    stop_loss_percentage: float = 5.0
    take_profit_percentage: float = 10.0
    trailing_stop: bool = True
    trailing_stop_percentage: float = 3.0
    
    # 신호 필터링
    min_confidence: float = 0.6
    min_volume: int = 1000
    max_spread_percentage: float = 2.0
    
    # 시간 제한
    trading_start_time: str = "09:00"
    trading_end_time: str = "15:30"
    lunch_break_start: str = "11:30"
    lunch_break_end: str = "13:00"

class IntegratedAutoTrader:
    """통합 자동매매 시스템"""
    
    def __init__(self, config: TradeConfig):
        self.config = config
        self.kiwoom_api = None
        self.strategy_manager = None
        
        # 시스템 상태
        self.is_running = False
        self.is_connected = False
        self.is_logged_in = False
        
        # 거래 상태
        self.positions = {}  # 현재 포지션
        self.orders = {}     # 주문 정보
        self.trades = []     # 거래 이력
        self.daily_pnl = 0.0 # 일일 손익
        
        # 데이터 저장소
        self.price_data = {}  # 종목별 가격 데이터
        self.signal_history = []  # 신호 히스토리
        
        # 스레드
        self.trading_thread = None
        self.monitoring_thread = None
        
        # 콜백 함수들
        self.signal_callback = None
        self.trade_callback = None
        self.error_callback = None
        
        # 통계
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
        
        logger.info("통합 자동매매 시스템 초기화 완료")
    
    def initialize(self, server_url: str = "http://localhost:8080"):
        """시스템 초기화"""
        try:
            logger.info("자동매매 시스템 초기화 시작")
            
            # 키움 API 초기화
            self.kiwoom_api = KiwoomMacAPI(server_url)
            
            # 전략 매니저 초기화
            self.strategy_manager = create_default_strategies()
            
            # 콜백 설정
            self.kiwoom_api.set_login_callback(self._on_login)
            self.kiwoom_api.set_real_data_callback(self._on_real_data)
            self.kiwoom_api.set_order_callback(self._on_order)
            
            logger.info("자동매매 시스템 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            return False
    
    def connect(self, timeout: int = 30) -> bool:
        """키움 API 연결"""
        try:
            logger.info("키움 API 연결 시도")
            success = self.kiwoom_api.connect(timeout)
            
            if success:
                self.is_connected = True
                logger.info("키움 API 연결 성공")
            else:
                logger.error("키움 API 연결 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"연결 오류: {e}")
            return False
    
    def login(self, user_id: str, password: str, account: str, timeout: int = 60) -> bool:
        """키움 API 로그인"""
        try:
            logger.info("키움 API 로그인 시도")
            success = self.kiwoom_api.login(user_id, password, account, timeout)
            
            if success:
                self.is_logged_in = True
                logger.info("키움 API 로그인 성공")
                
                # 계좌 정보 조회
                self._load_account_info()
            else:
                logger.error("키움 API 로그인 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"로그인 오류: {e}")
            return False
    
    def start_trading(self):
        """자동매매 시작"""
        if self.is_running:
            logger.warning("자동매매가 이미 실행 중입니다.")
            return False
        
        if not self.is_connected or not self.is_logged_in:
            logger.error("키움 API에 연결되지 않았습니다.")
            return False
        
        try:
            logger.info("자동매매 시작")
            self.is_running = True
            
            # 거래 스레드 시작
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            
            # 모니터링 스레드 시작
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("자동매매 시작 완료")
            return True
            
        except Exception as e:
            logger.error(f"자동매매 시작 실패: {e}")
            self.is_running = False
            return False
    
    def stop_trading(self):
        """자동매매 중지"""
        if not self.is_running:
            logger.warning("자동매매가 실행 중이 아닙니다.")
            return
        
        try:
            logger.info("자동매매 중지")
            self.is_running = False
            
            # 스레드 종료 대기
            if self.trading_thread:
                self.trading_thread.join(timeout=5)
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            logger.info("자동매매 중지 완료")
            
        except Exception as e:
            logger.error(f"자동매매 중지 오류: {e}")
    
    def _trading_loop(self):
        """거래 루프"""
        logger.info("거래 루프 시작")
        
        while self.is_running:
            try:
                # 거래 시간 확인
                if not self._is_trading_time():
                    time.sleep(60)
                    continue
                
                # 일일 손실 한도 확인
                if self._check_daily_loss_limit():
                    logger.warning("일일 손실 한도 도달. 거래 중지.")
                    break
                
                # 실시간 데이터 수집
                real_data = self.kiwoom_api.get_real_data_cache()
                
                # 각 종목에 대해 신호 생성
                for code, data in real_data.items():
                    if not data or 'data' not in data:
                        continue
                    
                    price_data = data['data']
                    current_price = price_data.get('현재가', 0)
                    
                    if current_price <= 0:
                        continue
                    
                    # 가격 데이터 업데이트
                    self._update_price_data(code, current_price)
                    
                    # 전략 신호 생성
                    signals = self._generate_signals(code, current_price)
                    
                    # 신호 처리
                    for signal in signals:
                        if signal.confidence >= self.config.min_confidence:
                            self._process_signal(signal)
                
                time.sleep(1)  # 1초 대기
                
            except Exception as e:
                logger.error(f"거래 루프 오류: {e}")
                time.sleep(5)
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        logger.info("모니터링 루프 시작")
        
        while self.is_running:
            try:
                # 포지션 모니터링
                self._monitor_positions()
                
                # 손절/익절 체크
                self._check_stop_loss_take_profit()
                
                # 통계 업데이트
                self._update_statistics()
                
                time.sleep(5)  # 5초 대기
                
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(10)
    
    def _update_price_data(self, code: str, price: float):
        """가격 데이터 업데이트"""
        if code not in self.price_data:
            self.price_data[code] = []
        
        self.price_data[code].append({
            'price': price,
            'timestamp': datetime.now()
        })
        
        # 최대 1000개 데이터만 유지
        if len(self.price_data[code]) > 1000:
            self.price_data[code] = self.price_data[code][-1000:]
        
        # 전략 매니저에 가격 데이터 전달
        if self.strategy_manager:
            self.strategy_manager.update_price(price)
    
    def _generate_signals(self, code: str, current_price: float) -> List[TradingSignal]:
        """신호 생성"""
        signals = []
        
        try:
            # 전략 매니저에서 신호 생성
            if self.strategy_manager:
                strategy_signals = self.strategy_manager.generate_signals()
                
                for signal in strategy_signals:
                    # 종목 코드 추가
                    signal.code = code
                    signal.price = current_price
                    signals.append(signal)
            
            # 신호 히스토리에 추가
            self.signal_history.extend(signals)
            
        except Exception as e:
            logger.error(f"신호 생성 오류: {e}")
        
        return signals
    
    def _process_signal(self, signal: TradingSignal):
        """신호 처리"""
        try:
            logger.info(f"신호 처리: {signal.code} - {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
            
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                self._execute_buy_signal(signal)
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                self._execute_sell_signal(signal)
            
            # 콜백 호출
            if self.signal_callback:
                self.signal_callback(signal)
                
        except Exception as e:
            logger.error(f"신호 처리 오류: {e}")
    
    def _execute_buy_signal(self, signal: TradingSignal):
        """매수 신호 실행"""
        try:
            code = signal.code
            price = signal.price
            
            # 매수 조건 확인
            if not self._can_buy(code, price):
                logger.info(f"매수 조건 불충족: {code}")
                return
            
            # 주문 수량 계산
            quantity = self._calculate_buy_quantity(code, price)
            
            if quantity <= 0:
                logger.warning(f"매수 수량이 0입니다: {code}")
                return
            
            # 주문 실행
            if self.config.trading_mode == TradingMode.PAPER_TRADING:
                self._execute_paper_buy(code, price, quantity, signal)
            else:
                self._execute_real_buy(code, price, quantity, signal)
            
            logger.info(f"매수 주문 실행: {code} - {quantity}주 - {price:,}원")
            
        except Exception as e:
            logger.error(f"매수 신호 실행 오류: {e}")
    
    def _execute_sell_signal(self, signal: TradingSignal):
        """매도 신호 실행"""
        try:
            code = signal.code
            price = signal.price
            
            # 매도 조건 확인
            if not self._can_sell(code, price):
                logger.info(f"매도 조건 불충족: {code}")
                return
            
            # 보유 수량 확인
            if code not in self.positions:
                logger.warning(f"보유하지 않은 종목: {code}")
                return
            
            quantity = self.positions[code].quantity
            
            # 주문 실행
            if self.config.trading_mode == TradingMode.PAPER_TRADING:
                self._execute_paper_sell(code, price, quantity, signal)
            else:
                self._execute_real_sell(code, price, quantity, signal)
            
            logger.info(f"매도 주문 실행: {code} - {quantity}주 - {price:,}원")
            
        except Exception as e:
            logger.error(f"매도 신호 실행 오류: {e}")
    
    def _can_buy(self, code: str, price: float) -> bool:
        """매수 가능 여부 확인"""
        try:
            # 최대 포지션 수 확인
            if len(self.positions) >= self.config.max_positions:
                return False
            
            # 이미 보유 중인 종목인지 확인
            if code in self.positions:
                return False
            
            # 자금 확인
            available_capital = self._get_available_capital()
            required_amount = price * self._calculate_buy_quantity(code, price)
            
            if required_amount > available_capital:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매수 조건 확인 오류: {e}")
            return False
    
    def _can_sell(self, code: str, price: float) -> bool:
        """매도 가능 여부 확인"""
        try:
            # 보유 종목인지 확인
            if code not in self.positions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매도 조건 확인 오류: {e}")
            return False
    
    def _calculate_buy_quantity(self, code: str, price: float) -> int:
        """매수 수량 계산"""
        try:
            # 최대 포지션 크기 기반 계산
            max_quantity = int(self.config.max_position_size / price)
            
            # 최소 거래 단위 (1주)
            if max_quantity < 1:
                return 0
            
            return max_quantity
            
        except Exception as e:
            logger.error(f"매수 수량 계산 오류: {e}")
            return 0
    
    def _execute_paper_buy(self, code: str, price: float, quantity: int, signal: TradingSignal):
        """페이퍼 트레이딩 매수"""
        try:
            # 포지션 생성
            position = Position(
                code=code,
                name=f"{code}_종목",
                quantity=quantity,
                avg_price=price,
                current_price=price,
                profit_loss=0.0,
                profit_loss_rate=0.0,
                timestamp=datetime.now()
            )
            
            self.positions[code] = position
            
            # 거래 이력 추가
            trade = {
                'timestamp': datetime.now(),
                'code': code,
                'type': '매수',
                'quantity': quantity,
                'price': price,
                'amount': price * quantity,
                'signal': signal
            }
            self.trades.append(trade)
            
            logger.info(f"페이퍼 매수 완료: {code} - {quantity}주 - {price:,}원")
            
        except Exception as e:
            logger.error(f"페이퍼 매수 오류: {e}")
    
    def _execute_paper_sell(self, code: str, price: float, quantity: int, signal: TradingSignal):
        """페이퍼 트레이딩 매도"""
        try:
            if code not in self.positions:
                return
            
            position = self.positions[code]
            
            # 손익 계산
            profit_loss = (price - position.avg_price) * quantity
            profit_loss_rate = (price - position.avg_price) / position.avg_price * 100
            
            # 거래 이력 추가
            trade = {
                'timestamp': datetime.now(),
                'code': code,
                'type': '매도',
                'quantity': quantity,
                'price': price,
                'amount': price * quantity,
                'profit_loss': profit_loss,
                'profit_loss_rate': profit_loss_rate,
                'signal': signal
            }
            self.trades.append(trade)
            
            # 통계 업데이트
            self.stats['total_trades'] += 1
            if profit_loss > 0:
                self.stats['winning_trades'] += 1
            else:
                self.stats['losing_trades'] += 1
            
            self.stats['total_profit'] += profit_loss
            self.daily_pnl += profit_loss
            
            # 포지션 제거
            del self.positions[code]
            
            logger.info(f"페이퍼 매도 완료: {code} - {quantity}주 - {price:,}원 (손익: {profit_loss:,}원)")
            
        except Exception as e:
            logger.error(f"페이퍼 매도 오류: {e}")
    
    def _execute_real_buy(self, code: str, price: float, quantity: int, signal: TradingSignal):
        """실제 매수 주문"""
        try:
            # 계좌 정보 조회
            account_info = self.kiwoom_api.get_account_info()
            if not account_info:
                logger.error("계좌 정보를 가져올 수 없습니다.")
                return
            
            account = list(account_info.keys())[0]
            
            # 주문 실행
            order_result = self.kiwoom_api.order_stock(
                account=account,
                code=code,
                quantity=quantity,
                price=int(price),
                order_type="신규매수"
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"실제 매수 주문 성공: {code}")
            else:
                logger.error(f"실제 매수 주문 실패: {code}")
            
        except Exception as e:
            logger.error(f"실제 매수 주문 오류: {e}")
    
    def _execute_real_sell(self, code: str, price: float, quantity: int, signal: TradingSignal):
        """실제 매도 주문"""
        try:
            # 계좌 정보 조회
            account_info = self.kiwoom_api.get_account_info()
            if not account_info:
                logger.error("계좌 정보를 가져올 수 없습니다.")
                return
            
            account = list(account_info.keys())[0]
            
            # 주문 실행
            order_result = self.kiwoom_api.order_stock(
                account=account,
                code=code,
                quantity=quantity,
                price=int(price),
                order_type="신규매도"
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"실제 매도 주문 성공: {code}")
            else:
                logger.error(f"실제 매도 주문 실패: {code}")
            
        except Exception as e:
            logger.error(f"실제 매도 주문 오류: {e}")
    
    def _monitor_positions(self):
        """포지션 모니터링"""
        try:
            for code, position in self.positions.items():
                # 현재가 조회
                current_price = self.kiwoom_api.get_current_price(code)
                if current_price:
                    position.current_price = current_price
                    position.profit_loss = (current_price - position.avg_price) * position.quantity
                    position.profit_loss_rate = (current_price - position.avg_price) / position.avg_price * 100
                    position.timestamp = datetime.now()
        
        except Exception as e:
            logger.error(f"포지션 모니터링 오류: {e}")
    
    def _check_stop_loss_take_profit(self):
        """손절/익절 체크"""
        try:
            for code, position in list(self.positions.items()):
                current_price = position.current_price
                avg_price = position.avg_price
                
                # 손절 체크
                if current_price <= avg_price * (1 - self.config.stop_loss_percentage / 100):
                    logger.info(f"손절 실행: {code} - 현재가: {current_price:,}원")
                    self._execute_emergency_sell(code, "손절")
                
                # 익절 체크
                elif current_price >= avg_price * (1 + self.config.take_profit_percentage / 100):
                    logger.info(f"익절 실행: {code} - 현재가: {current_price:,}원")
                    self._execute_emergency_sell(code, "익절")
        
        except Exception as e:
            logger.error(f"손절/익절 체크 오류: {e}")
    
    def _execute_emergency_sell(self, code: str, reason: str):
        """긴급 매도 실행"""
        try:
            if code not in self.positions:
                return
            
            position = self.positions[code]
            
            # 매도 신호 생성
            signal = TradingSignal(
                strategy=StrategyType.COMBINED_STRATEGY,
                signal_type=SignalType.SELL,
                confidence=1.0,
                price=position.current_price,
                timestamp=datetime.now(),
                details={'reason': reason}
            )
            
            # 매도 실행
            if self.config.trading_mode == TradingMode.PAPER_TRADING:
                self._execute_paper_sell(code, position.current_price, position.quantity, signal)
            else:
                self._execute_real_sell(code, position.current_price, position.quantity, signal)
        
        except Exception as e:
            logger.error(f"긴급 매도 실행 오류: {e}")
    
    def _check_daily_loss_limit(self) -> bool:
        """일일 손실 한도 체크"""
        return self.daily_pnl <= -self.config.daily_loss_limit
    
    def _is_trading_time(self) -> bool:
        """거래 시간 확인"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 점심시간 체크
        if self.config.lunch_break_start <= current_time <= self.config.lunch_break_end:
            return False
        
        # 거래시간 체크
        return self.config.trading_start_time <= current_time <= self.config.trading_end_time
    
    def _get_available_capital(self) -> float:
        """사용 가능한 자금 조회"""
        try:
            if self.config.trading_mode == TradingMode.PAPER_TRADING:
                # 페이퍼 트레이딩: 초기 자금에서 사용된 자금 차감
                used_capital = sum(pos.avg_price * pos.quantity for pos in self.positions.values())
                return self.config.initial_capital - used_capital
            else:
                # 실제 거래: 예수금 조회
                account_info = self.kiwoom_api.get_account_info()
                if account_info:
                    account = list(account_info.keys())[0]
                    deposit_info = self.kiwoom_api.get_deposit_info(account)
                    return deposit_info.get('available_amount', 0)
                return 0
        
        except Exception as e:
            logger.error(f"사용 가능한 자금 조회 오류: {e}")
            return 0
    
    def _load_account_info(self):
        """계좌 정보 로드"""
        try:
            account_info = self.kiwoom_api.get_account_info()
            if account_info:
                logger.info(f"계좌 정보 로드 완료: {len(account_info)}개 계좌")
            
            # 포지션 정보 로드
            if account_info:
                account = list(account_info.keys())[0]
                position_info = self.kiwoom_api.get_position_info(account)
                if position_info:
                    logger.info(f"포지션 정보 로드 완료: {len(position_info.get('positions', []))}개 포지션")
        
        except Exception as e:
            logger.error(f"계좌 정보 로드 오류: {e}")
    
    def _update_statistics(self):
        """통계 업데이트"""
        try:
            # 승률 계산
            if self.stats['total_trades'] > 0:
                win_rate = (self.stats['winning_trades'] / self.stats['total_trades']) * 100
                self.stats['win_rate'] = win_rate
            
            # 최대 낙폭 계산
            if self.trades:
                cumulative_pnl = 0
                max_pnl = 0
                max_drawdown = 0
                
                for trade in self.trades:
                    if trade['type'] == '매도':
                        cumulative_pnl += trade.get('profit_loss', 0)
                        max_pnl = max(max_pnl, cumulative_pnl)
                        drawdown = max_pnl - cumulative_pnl
                        max_drawdown = max(max_drawdown, drawdown)
                
                self.stats['max_drawdown'] = max_drawdown
        
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")
    
    def _on_login(self, result: Dict):
        """로그인 콜백"""
        logger.info(f"로그인 결과: {result}")
    
    def _on_real_data(self, data: Dict):
        """실시간 데이터 콜백"""
        # 실시간 데이터 처리
        pass
    
    def _on_order(self, data: Dict):
        """주문 콜백"""
        logger.info(f"주문 결과: {data}")
        
        # 콜백 호출
        if self.trade_callback:
            self.trade_callback(data)
    
    def set_signal_callback(self, callback: Callable):
        """신호 콜백 설정"""
        self.signal_callback = callback
    
    def set_trade_callback(self, callback: Callable):
        """거래 콜백 설정"""
        self.trade_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """에러 콜백 설정"""
        self.error_callback = callback
    
    def get_status(self) -> Dict:
        """시스템 상태 조회"""
        return {
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'is_logged_in': self.is_logged_in,
            'trading_mode': self.config.trading_mode.value,
            'positions_count': len(self.positions),
            'total_trades': self.stats['total_trades'],
            'total_profit': self.stats['total_profit'],
            'daily_pnl': self.daily_pnl,
            'available_capital': self._get_available_capital()
        }
    
    def get_positions(self) -> Dict[str, Position]:
        """포지션 정보 조회"""
        return self.positions
    
    def get_trades(self) -> List[Dict]:
        """거래 이력 조회"""
        return self.trades
    
    def get_statistics(self) -> Dict:
        """통계 정보 조회"""
        return self.stats
    
    def get_strategy_performance(self) -> Dict:
        """전략 성과 조회"""
        if self.strategy_manager:
            return self.strategy_manager.get_performance_summary()
        return {}

def main():
    """메인 함수"""
    logger.info("통합 자동매매 시스템 시작")
    
    # 설정 생성
    config = TradeConfig(
        trading_mode=TradingMode.PAPER_TRADING,
        risk_level=RiskLevel.MEDIUM,
        initial_capital=10000000,
        max_position_size=1000000,
        daily_loss_limit=500000
    )
    
    # 자동매매 시스템 생성
    trader = IntegratedAutoTrader(config)
    
    try:
        # 시스템 초기화
        if not trader.initialize():
            logger.error("시스템 초기화 실패")
            return False
        
        # 키움 API 연결
        if not trader.connect():
            logger.error("키움 API 연결 실패")
            return False
        
        # 로그인 (설정 파일에서 정보 읽기)
        try:
            with open("config/kiwoom_config.json", "r", encoding="utf-8") as f:
                kiwoom_config = json.load(f)
                login_info = kiwoom_config.get("login", {})
                
                if not trader.login(
                    login_info.get("user_id", ""),
                    login_info.get("password", ""),
                    login_info.get("account", "")
                ):
                    logger.error("키움 API 로그인 실패")
                    return False
        except FileNotFoundError:
            logger.warning("키움 설정 파일을 찾을 수 없습니다. 페이퍼 트레이딩 모드로 실행합니다.")
        
        # 자동매매 시작
        if not trader.start_trading():
            logger.error("자동매매 시작 실패")
            return False
        
        # 무한 루프 (Ctrl+C로 종료)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        
        # 자동매매 중지
        trader.stop_trading()
        
        # 최종 통계 출력
        stats = trader.get_statistics()
        logger.info(f"최종 통계: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"자동매매 시스템 오류: {e}")
        return False

if __name__ == "__main__":
    main() 