#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac 환경 호환 키움 API 래퍼
ActiveX 의존성을 제거하고 REST API 기반으로 작동
"""

import sys
import time
import threading
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# 에러 처리 모듈
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation

class OrderType(Enum):
    """주문 타입 정의"""
    BUY = "신규매수"
    SELL = "신규매도"
    BUY_CANCEL = "매수취소"
    SELL_CANCEL = "매도취소"
    BUY_MODIFY = "매수정정"
    SELL_MODIFY = "매도정정"

class OrderStatus(Enum):
    """주문 상태 정의"""
    PENDING = "접수"
    CONFIRMED = "확인"
    PARTIAL_FILLED = "부분체결"
    FILLED = "체결"
    CANCELLED = "취소"
    REJECTED = "거부"

class RealDataType(Enum):
    """실시간 데이터 타입 정의"""
    STOCK_TICK = "주식체결"
    STOCK_ORDER = "주식주문체결"
    STOCK_TRADE = "주식체결통보"
    INDEX = "지수"

@dataclass
class StockData:
    """주식 데이터"""
    code: str
    name: str
    price: float
    change: float
    change_rate: float
    volume: int
    timestamp: datetime

@dataclass
class OrderData:
    """주문 데이터"""
    order_no: str
    code: str
    quantity: int
    price: float
    order_type: OrderType
    status: OrderStatus
    timestamp: datetime

class KiwoomMacAPI:
    """
    Mac 환경 호환 키움 API 클래스
    Windows 서버와 WebSocket 통신하여 데이터 수신
    """
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url
        self.is_connected = False
        self.is_logged_in = False
        
        # 콜백 함수들
        self.login_callback = None
        self.real_data_callback = None
        self.order_callback = None
        
        # 데이터 저장소
        self.account_info = {}
        self.stock_info = {}
        self.order_info = {}
        self.position_info = {}
        self.deposit_info = {}
        
        # 실시간 데이터 캐시
        self.real_data_cache = {}
        self.real_data_history = {}
        self.real_data_stats = {}
        
        # 연결 상태 모니터링
        self.connection_thread = None
        self.is_monitoring = False
        
        # 에러 통계
        self.error_stats = {
            'connection_errors': 0,
            'api_errors': 0,
            'timeout_errors': 0,
            'last_error': None
        }
        
        logger.info("Mac 호환 키움 API 초기화 완료")
    
    def connect(self, timeout: int = 30) -> bool:
        """서버 연결"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=timeout)
            if response.status_code == 200:
                self.is_connected = True
                logger.info("키움 API 서버 연결 성공")
                self._start_connection_monitoring()
                return True
            else:
                logger.error(f"서버 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            handle_error(
                ErrorType.API,
                "서버 연결 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            return False
    
    def login(self, user_id: str, password: str, account: str, timeout: int = 30) -> bool:
        """로그인"""
        try:
            login_data = {
                'user_id': user_id,
                'password': password,
                'account': account
            }
            
            response = requests.post(
                f"{self.server_url}/login",
                json=login_data,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.is_logged_in = True
                    self.account_info = result.get('account_info', {})
                    logger.info("키움 API 로그인 성공")
                    
                    if self.login_callback:
                        self.login_callback(True, None)
                    
                    return True
                else:
                    error_msg = result.get('error', '로그인 실패')
                    logger.error(f"로그인 실패: {error_msg}")
                    
                    if self.login_callback:
                        self.login_callback(False, error_msg)
                    
                    return False
            else:
                logger.error(f"로그인 요청 실패: {response.status_code}")
                return False
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                "로그인 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            return False
    
    def get_account_info(self) -> Dict:
        """계좌 정보 조회"""
        try:
            response = requests.get(f"{self.server_url}/account-info", timeout=10)
            if response.status_code == 200:
                self.account_info = response.json()
                return self.account_info
            else:
                logger.error(f"계좌 정보 조회 실패: {response.status_code}")
                return {}
        except Exception as e:
            handle_error(
                ErrorType.API,
                "계좌 정보 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def get_deposit_info(self, account: str) -> Dict:
        """예수금 정보 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/deposit-info/{account}",
                timeout=10
            )
            if response.status_code == 200:
                self.deposit_info = response.json()
                return self.deposit_info
            else:
                logger.error(f"예수금 정보 조회 실패: {response.status_code}")
                return {}
        except Exception as e:
            handle_error(
                ErrorType.API,
                "예수금 정보 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def get_current_price(self, code: str) -> Optional[float]:
        """현재가 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/current-price/{code}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('price')
            else:
                logger.error(f"현재가 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"현재가 조회 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return None
    
    def order_stock(self, account: str, code: str, quantity: int, 
                   price: float, order_type: str = "신규매수") -> Dict:
        """주식 주문"""
        try:
            order_data = {
                'account': account,
                'code': code,
                'quantity': quantity,
                'price': price,
                'order_type': order_type
            }
            
            response = requests.post(
                f"{self.server_url}/order",
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"주문 성공: {code} {order_type} {quantity}주")
                    return result
                else:
                    logger.error(f"주문 실패: {result.get('error')}")
                    return result
            else:
                logger.error(f"주문 요청 실패: {response.status_code}")
                return {'success': False, 'error': '주문 요청 실패'}
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"주문 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            return {'success': False, 'error': str(e)}
    
    def get_position_info(self, account: str) -> Dict:
        """보유 종목 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/position-info/{account}",
                timeout=10
            )
            if response.status_code == 200:
                self.position_info = response.json()
                return self.position_info
            else:
                logger.error(f"보유 종목 조회 실패: {response.status_code}")
                return {}
        except Exception as e:
            handle_error(
                ErrorType.API,
                "보유 종목 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def get_order_history(self, account: str) -> List[Dict]:
        """주문 내역 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/order-history/{account}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"주문 내역 조회 실패: {response.status_code}")
                return []
        except Exception as e:
            handle_error(
                ErrorType.API,
                "주문 내역 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return []
    
    def subscribe_real_data(self, code: str, real_type: str = "주식체결") -> bool:
        """실시간 데이터 구독"""
        try:
            subscribe_data = {
                'code': code,
                'real_type': real_type
            }
            
            response = requests.post(
                f"{self.server_url}/subscribe-real-data",
                json=subscribe_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"실시간 데이터 구독 성공: {code}")
                    return True
                else:
                    logger.error(f"실시간 데이터 구독 실패: {result.get('error')}")
                    return False
            else:
                logger.error(f"실시간 데이터 구독 요청 실패: {response.status_code}")
                return False
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"실시간 데이터 구독 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return False
    
    def get_real_data_cache(self, code: str = None) -> Dict:
        """실시간 데이터 캐시 조회"""
        try:
            if code:
                response = requests.get(
                    f"{self.server_url}/real-data-cache/{code}",
                    timeout=5
                )
            else:
                response = requests.get(
                    f"{self.server_url}/real-data-cache",
                    timeout=5
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            handle_error(
                ErrorType.API,
                "실시간 데이터 캐시 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def _start_connection_monitoring(self):
        """연결 상태 모니터링 시작"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.connection_thread = threading.Thread(
                target=self._monitor_connection,
                daemon=True
            )
            self.connection_thread.start()
    
    def _monitor_connection(self):
        """연결 상태 모니터링"""
        while self.is_monitoring:
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code != 200:
                    self.is_connected = False
                    logger.warning("서버 연결 끊김 감지")
                    
                    # 재연결 시도
                    if self.connect():
                        logger.info("서버 재연결 성공")
                    else:
                        logger.error("서버 재연결 실패")
                
                time.sleep(10)  # 10초마다 체크
                
            except Exception as e:
                self.is_connected = False
                logger.error(f"연결 모니터링 에러: {e}")
                time.sleep(10)
    
    def set_login_callback(self, callback: Callable):
        """로그인 콜백 설정"""
        self.login_callback = callback
    
    def set_real_data_callback(self, callback: Callable):
        """실시간 데이터 콜백 설정"""
        self.real_data_callback = callback
    
    def set_order_callback(self, callback: Callable):
        """주문 콜백 설정"""
        self.order_callback = callback
    
    def disconnect(self):
        """연결 해제"""
        self.is_monitoring = False
        self.is_connected = False
        self.is_logged_in = False
        logger.info("키움 API 연결 해제")
    
    def get_error_stats(self) -> Dict:
        """에러 통계 조회"""
        return self.error_stats.copy()

# 사용 예시
if __name__ == "__main__":
    # API 인스턴스 생성
    api = KiwoomMacAPI("http://localhost:8080")
    
    # 연결 테스트
    if api.connect():
        print("서버 연결 성공")
        
        # 로그인 테스트 (실제 계정 정보 필요)
        # if api.login("user_id", "password", "account"):
        #     print("로그인 성공")
        #     
        #     # 계좌 정보 조회
        #     account_info = api.get_account_info()
        #     print(f"계좌 정보: {account_info}")
        # else:
        #     print("로그인 실패")
    else:
        print("서버 연결 실패") 