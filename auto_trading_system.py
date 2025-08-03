#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 매매 시스템
조건 충족 시 자동으로 매수/매도 실행
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import sqlite3
from loguru import logger

# 프로젝트 모듈 import
from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer, IntegratedSignal
from enhanced_risk_management import EnhancedRiskManager
from day_trading_config import DayTradingConfig, DayTradingRiskLevel, MarketCondition
from error_handler import ErrorType, ErrorLevel, handle_error

class OrderType(Enum):
    """주문 타입"""
    BUY = "buy"
    SELL = "sell"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class TradingSignal:
    """매매 신호"""
    stock_code: str
    stock_name: str
    signal_type: OrderType
    price: float
    quantity: int
    confidence_score: float
    reasoning: List[str]
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_level: str = "medium"

@dataclass
class Order:
    """주문 정보"""
    order_id: str
    stock_code: str
    order_type: OrderType
    price: float
    quantity: int
    status: OrderStatus
    timestamp: datetime
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    commission: float = 0.0
    slippage: float = 0.0

@dataclass
class Position:
    """포지션 정보"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    last_update: datetime

class AutoTradingSystem:
    """자동 매매 시스템"""
    
    def __init__(self, config: DayTradingConfig = None):
        """초기화"""
        try:
            logger.info("자동 매매 시스템 초기화 시작")
            
            # 설정
            self.config = config or DayTradingConfig()
            
            # 분석기 초기화
            self.analyzer = IntegratedTrendStockAnalyzer()
            self.risk_manager = EnhancedRiskManager()
            
            # 상태 관리
            self.is_running = False
            self.is_trading_enabled = False
            self.positions: Dict[str, Position] = {}
            self.orders: List[Order] = []
            self.daily_pnl = 0.0
            self.daily_trades = 0
            
            # 모니터링 설정
            self.monitoring_interval = 30  # 30초마다 체크
            self.price_check_interval = 5  # 5초마다 가격 체크
            
            # 데이터베이스 초기화
            self._init_database()
            
            # 스레드 관리
            self.monitoring_thread = None
            self.price_monitoring_thread = None
            
            logger.info("자동 매매 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"자동 매매 시스템 초기화 실패: {e}")
            handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"자동 매매 시스템 오류: {e}")
            raise
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            self.db_conn = sqlite3.connect('auto_trading.db', check_same_thread=False)
            self.db_conn.row_factory = sqlite3.Row
            
            # 테이블 생성
            cursor = self.db_conn.cursor()
            
            # 주문 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    stock_code TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    executed_price REAL,
                    executed_quantity INTEGER,
                    commission REAL DEFAULT 0.0,
                    slippage REAL DEFAULT 0.0
                )
            ''')
            
            # 포지션 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    last_update TEXT NOT NULL
                )
            ''')
            
            # 거래 이력 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    pnl REAL DEFAULT 0.0
                )
            ''')
            
            self.db_conn.commit()
            logger.info("데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def start_auto_trading(self):
        """자동 매매 시작"""
        try:
            if self.is_running:
                logger.warning("자동 매매가 이미 실행 중입니다.")
                return
            
            logger.info("자동 매매 시작")
            self.is_running = True
            self.is_trading_enabled = True
            
            # 모니터링 스레드 시작
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            self.monitoring_thread.start()
            
            # 가격 모니터링 스레드 시작
            self.price_monitoring_thread = threading.Thread(target=self._price_monitoring_worker, daemon=True)
            self.price_monitoring_thread.start()
            
            logger.info("자동 매매 모니터링 시작됨")
            
        except Exception as e:
            logger.error(f"자동 매매 시작 실패: {e}")
            handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"자동 매매 시작 오류: {e}")
    
    def stop_auto_trading(self):
        """자동 매매 중지"""
        try:
            logger.info("자동 매매 중지 요청")
            self.is_running = False
            self.is_trading_enabled = False
            
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            if self.price_monitoring_thread:
                self.price_monitoring_thread.join(timeout=5)
            
            logger.info("자동 매매 중지 완료")
            
        except Exception as e:
            logger.error(f"자동 매매 중지 실패: {e}")
    
    def _monitoring_worker(self):
        """모니터링 워커 스레드"""
        while self.is_running:
            try:
                if self.is_trading_enabled:
                    # 새로운 매매 신호 확인
                    self._check_trading_signals()
                    
                    # 일일 한도 체크
                    self._check_daily_limits()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"모니터링 워커 오류: {e}")
                time.sleep(10)  # 오류 시 10초 대기
    
    def _price_monitoring_worker(self):
        """가격 모니터링 워커 스레드"""
        while self.is_running:
            try:
                if self.is_trading_enabled:
                    # 포지션 손절/익절 체크
                    self._check_stop_loss_take_profit()
                
                time.sleep(self.price_check_interval)
                
            except Exception as e:
                logger.error(f"가격 모니터링 워커 오류: {e}")
                time.sleep(5)  # 오류 시 5초 대기
    
    def _check_trading_signals(self):
        """매매 신호 확인"""
        try:
            # 통합 신호 가져오기
            signals = self.analyzer.get_all_signals()
            
            for stock_code, signal in signals.items():
                # 이미 포지션이 있는지 확인
                if stock_code in self.positions:
                    continue
                
                # 매수 신호 확인
                if signal.signal_strength.value in ['strong_buy', 'buy']:
                    if self._should_execute_buy_signal(signal):
                        self._execute_buy_order(signal)
                
                # 매도 신호 확인 (숏 포지션)
                elif signal.signal_strength.value in ['strong_sell', 'sell']:
                    if self._should_execute_sell_signal(signal):
                        self._execute_sell_order(signal)
            
        except Exception as e:
            logger.error(f"매매 신호 확인 오류: {e}")
    
    def _should_execute_buy_signal(self, signal: IntegratedSignal) -> bool:
        """매수 신호 실행 여부 확인"""
        try:
            # 신뢰도 체크
            if signal.confidence_score < 0.6:
                return False
            
            # 일일 거래 한도 체크
            if self.daily_trades >= self.config.max_daily_trades:
                logger.info(f"일일 거래 한도 도달: {self.daily_trades}")
                return False
            
            # 손실 한도 체크
            if self.daily_pnl < -(self.config.max_daily_loss * 10000000):  # 1000만원 기준
                logger.info(f"일일 손실 한도 도달: {self.daily_pnl}")
                return False
            
            # 최소 거래 간격 체크
            if self._is_recent_trade(signal.stock_code):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매수 신호 확인 오류: {e}")
            return False
    
    def _should_execute_sell_signal(self, signal: IntegratedSignal) -> bool:
        """매도 신호 실행 여부 확인"""
        try:
            # 신뢰도 체크
            if signal.confidence_score < 0.6:
                return False
            
            # 일일 거래 한도 체크
            if self.daily_trades >= self.config.max_daily_trades:
                return False
            
            # 손실 한도 체크
            if self.daily_pnl < -(self.config.max_daily_loss * 10000000):
                return False
            
            # 최소 거래 간격 체크
            if self._is_recent_trade(signal.stock_code):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"매도 신호 확인 오류: {e}")
            return False
    
    def _is_recent_trade(self, stock_code: str) -> bool:
        """최근 거래 여부 확인"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM trade_history 
                WHERE stock_code = ? AND timestamp > ?
            ''', (stock_code, (datetime.now() - timedelta(minutes=self.config.min_trade_interval)).isoformat()))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"최근 거래 확인 오류: {e}")
            return False
    
    def _execute_buy_order(self, signal: IntegratedSignal):
        """매수 주문 실행"""
        try:
            logger.info(f"매수 주문 실행: {signal.stock_name} ({signal.stock_code})")
            
            # 주문 정보 생성
            order_id = f"BUY_{signal.stock_code}_{int(time.time())}"
            quantity = self._calculate_position_size(signal)
            
            order = Order(
                order_id=order_id,
                stock_code=signal.stock_code,
                order_type=OrderType.BUY,
                price=signal.price_target or 0,
                quantity=quantity,
                status=OrderStatus.PENDING,
                timestamp=datetime.now()
            )
            
            # 실제 주문 실행 (키움 API 연동)
            success = self._execute_real_order(order)
            
            if success:
                # 주문 성공 시 포지션 생성
                self._create_position(signal, order)
                self.daily_trades += 1
                
                logger.info(f"매수 주문 성공: {signal.stock_name} {quantity}주")
            else:
                logger.error(f"매수 주문 실패: {signal.stock_name}")
            
        except Exception as e:
            logger.error(f"매수 주문 실행 오류: {e}")
    
    def _execute_sell_order(self, signal: IntegratedSignal):
        """매도 주문 실행"""
        try:
            logger.info(f"매도 주문 실행: {signal.stock_name} ({signal.stock_code})")
            
            # 주문 정보 생성
            order_id = f"SELL_{signal.stock_code}_{int(time.time())}"
            quantity = self._calculate_position_size(signal)
            
            order = Order(
                order_id=order_id,
                stock_code=signal.stock_code,
                order_type=OrderType.SELL,
                price=signal.price_target or 0,
                quantity=quantity,
                status=OrderStatus.PENDING,
                timestamp=datetime.now()
            )
            
            # 실제 주문 실행 (키움 API 연동)
            success = self._execute_real_order(order)
            
            if success:
                self.daily_trades += 1
                logger.info(f"매도 주문 성공: {signal.stock_name} {quantity}주")
            else:
                logger.error(f"매도 주문 실패: {signal.stock_name}")
            
        except Exception as e:
            logger.error(f"매도 주문 실행 오류: {e}")
    
    def _execute_real_order(self, order: Order) -> bool:
        """실제 주문 실행 (키움 API 연동)"""
        try:
            # TODO: 키움 API 연동 구현
            # 현재는 시뮬레이션 모드
            
            # 주문 정보 저장
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.order_id, order.stock_code, order.order_type.value,
                order.price, order.quantity, order.status.value,
                order.timestamp.isoformat(), order.executed_price,
                order.executed_quantity, order.commission, order.slippage
            ))
            
            # 거래 이력 저장
            cursor.execute('''
                INSERT INTO trade_history (stock_code, order_type, price, quantity, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                order.stock_code, order.order_type.value, order.price,
                order.quantity, order.timestamp.isoformat()
            ))
            
            self.db_conn.commit()
            
            # 시뮬레이션: 주문 성공으로 가정
            order.status = OrderStatus.EXECUTED
            order.executed_price = order.price
            order.executed_quantity = order.quantity
            
            return True
            
        except Exception as e:
            logger.error(f"실제 주문 실행 오류: {e}")
            return False
    
    def _calculate_position_size(self, signal: IntegratedSignal) -> int:
        """포지션 크기 계산 (1종목당 자본의 5~10% 제한)"""
        try:
            # 기본 자본 (1000만원)
            available_capital = 10000000
            
            # 위험도별 최대 포지션 크기 (5~10% 제한)
            risk_level = DayTradingRiskLevel.MODERATE  # 기본값
            if signal.risk_level == 'low':
                risk_level = DayTradingRiskLevel.CONSERVATIVE
            elif signal.risk_level == 'high':
                risk_level = DayTradingRiskLevel.AGGRESSIVE
            
            max_position_ratio = self.config.risk_levels[risk_level]["max_position_size"]
            max_position_value = available_capital * max_position_ratio
            
            # 주식 가격으로 나누어 주식 수 계산
            stock_price = signal.price_target or 80000  # 기본값
            quantity = int(max_position_value / stock_price)
            
            # 최소 1주, 최대 수량 제한
            quantity = max(1, quantity)
            
            # 실제 투자 금액 계산
            actual_investment = quantity * stock_price
            investment_ratio = actual_investment / available_capital
            
            logger.info(f"포지션 크기 계산: {signal.stock_name}")
            logger.info(f"  - 위험도: {risk_level.value}")
            logger.info(f"  - 최대 투자 비율: {max_position_ratio * 100:.1f}%")
            logger.info(f"  - 실제 투자 비율: {investment_ratio * 100:.1f}%")
            logger.info(f"  - 투자 금액: {actual_investment:,.0f}원")
            logger.info(f"  - 주식 수량: {quantity}주")
            
            return quantity
            
        except Exception as e:
            logger.error(f"포지션 크기 계산 오류: {e}")
            return 1
    
    def _create_position(self, signal: IntegratedSignal, order: Order):
        """포지션 생성"""
        try:
            position = Position(
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                quantity=order.quantity,
                avg_price=order.executed_price or order.price,
                current_price=order.executed_price or order.price,
                unrealized_pnl=0.0,
                stop_loss=signal.stop_loss or 0,
                take_profit=signal.take_profit or 0,
                entry_time=datetime.now(),
                last_update=datetime.now()
            )
            
            self.positions[signal.stock_code] = position
            
            # 데이터베이스에 저장
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.stock_code, position.stock_name, position.quantity,
                position.avg_price, position.current_price, position.unrealized_pnl,
                position.stop_loss, position.take_profit,
                position.entry_time.isoformat(), position.last_update.isoformat()
            ))
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"포지션 생성 오류: {e}")
    
    def _check_stop_loss_take_profit(self):
        """손절/익절 체크"""
        try:
            for stock_code, position in self.positions.items():
                # 현재가 업데이트 (실제로는 키움 API에서 가져옴)
                current_price = self._get_current_price(stock_code)
                position.current_price = current_price
                position.last_update = datetime.now()
                
                # 미실현 손익 계산
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                
                # 손절 체크
                if current_price <= position.stop_loss:
                    logger.info(f"손절 실행: {position.stock_name} ({stock_code})")
                    self._execute_stop_loss(position)
                
                # 익절 체크
                elif current_price >= position.take_profit:
                    logger.info(f"익절 실행: {position.stock_name} ({stock_code})")
                    self._execute_take_profit(position)
                
                # 데이터베이스 업데이트
                self._update_position_db(position)
            
        except Exception as e:
            logger.error(f"손절/익절 체크 오류: {e}")
    
    def _get_current_price(self, stock_code: str) -> float:
        """현재가 조회 (키움 API 연동)"""
        try:
            # TODO: 키움 API에서 실제 현재가 조회
            # 현재는 시뮬레이션용 가격 반환
            
            # 기본 가격 + 랜덤 변동
            import random
            base_prices = {
                '005930': 80000,  # 삼성전자
                '000660': 170000, # SK하이닉스
                '035420': 220000  # 네이버
            }
            
            base_price = base_prices.get(stock_code, 50000)
            variation = random.uniform(-0.02, 0.02)  # ±2% 변동
            return base_price * (1 + variation)
            
        except Exception as e:
            logger.error(f"현재가 조회 오류: {e}")
            return 0.0
    
    def _execute_stop_loss(self, position: Position):
        """손절 실행"""
        try:
            order_id = f"STOP_LOSS_{position.stock_code}_{int(time.time())}"
            
            order = Order(
                order_id=order_id,
                stock_code=position.stock_code,
                order_type=OrderType.STOP_LOSS,
                price=position.current_price,
                quantity=position.quantity,
                status=OrderStatus.PENDING,
                timestamp=datetime.now()
            )
            
            success = self._execute_real_order(order)
            
            if success:
                # 포지션 정리
                pnl = position.unrealized_pnl
                self.daily_pnl += pnl
                
                del self.positions[position.stock_code]
                
                # 데이터베이스에서 포지션 삭제
                cursor = self.db_conn.cursor()
                cursor.execute('DELETE FROM positions WHERE stock_code = ?', (position.stock_code,))
                self.db_conn.commit()
                
                logger.info(f"손절 완료: {position.stock_name} PnL: {pnl:,.0f}원")
            
        except Exception as e:
            logger.error(f"손절 실행 오류: {e}")
    
    def _execute_take_profit(self, position: Position):
        """익절 실행"""
        try:
            order_id = f"TAKE_PROFIT_{position.stock_code}_{int(time.time())}"
            
            order = Order(
                order_id=order_id,
                stock_code=position.stock_code,
                order_type=OrderType.TAKE_PROFIT,
                price=position.current_price,
                quantity=position.quantity,
                status=OrderStatus.PENDING,
                timestamp=datetime.now()
            )
            
            success = self._execute_real_order(order)
            
            if success:
                # 포지션 정리
                pnl = position.unrealized_pnl
                self.daily_pnl += pnl
                
                del self.positions[position.stock_code]
                
                # 데이터베이스에서 포지션 삭제
                cursor = self.db_conn.cursor()
                cursor.execute('DELETE FROM positions WHERE stock_code = ?', (position.stock_code,))
                self.db_conn.commit()
                
                logger.info(f"익절 완료: {position.stock_name} PnL: {pnl:,.0f}원")
            
        except Exception as e:
            logger.error(f"익절 실행 오류: {e}")
    
    def _update_position_db(self, position: Position):
        """포지션 데이터베이스 업데이트"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                UPDATE positions 
                SET current_price = ?, unrealized_pnl = ?, last_update = ?
                WHERE stock_code = ?
            ''', (
                position.current_price, position.unrealized_pnl,
                position.last_update.isoformat(), position.stock_code
            ))
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"포지션 DB 업데이트 오류: {e}")
    
    def _check_daily_limits(self):
        """일일 한도 체크"""
        try:
            # 일일 손실 한도 체크
            if self.daily_pnl < -(self.config.max_daily_loss * 10000000):
                logger.warning("일일 손실 한도 도달. 자동 매매 중지")
                self.is_trading_enabled = False
            
            # 일일 거래 한도 체크
            if self.daily_trades >= self.config.max_daily_trades:
                logger.warning("일일 거래 한도 도달. 자동 매매 중지")
                self.is_trading_enabled = False
            
        except Exception as e:
            logger.error(f"일일 한도 체크 오류: {e}")
    
    def get_trading_status(self) -> Dict:
        """매매 상태 조회"""
        try:
            return {
                'is_running': self.is_running,
                'is_trading_enabled': self.is_trading_enabled,
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'positions_count': len(self.positions),
                'orders_count': len(self.orders),
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"매매 상태 조회 오류: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """포지션 목록 조회"""
        try:
            return [asdict(position) for position in self.positions.values()]
        except Exception as e:
            logger.error(f"포지션 목록 조회 오류: {e}")
            return []
    
    def get_order_history(self) -> List[Dict]:
        """주문 이력 조회"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                SELECT * FROM trade_history 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"주문 이력 조회 오류: {e}")
            return []

def main():
    """메인 함수"""
    try:
        # 자동 매매 시스템 초기화
        trading_system = AutoTradingSystem()
        
        # 자동 매매 시작
        trading_system.start_auto_trading()
        
        # 무한 루프로 실행
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        finally:
            trading_system.stop_auto_trading()
        
    except Exception as e:
        logger.error(f"자동 매매 시스템 실행 실패: {e}")
        handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"자동 매매 시스템 오류: {e}")

if __name__ == "__main__":
    main() 