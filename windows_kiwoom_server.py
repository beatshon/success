#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 키움 API 서버
Mac 환경에서 접근할 수 있는 REST API 서버
"""

import sys
import time
import threading
import json
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# Flask 웹 서버
from flask import Flask, request, jsonify
from flask_cors import CORS

# 키움 API (Windows에서만 사용)
try:
    from PyQt5.QAxContainer import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    KIWOOM_AVAILABLE = True
except ImportError:
    KIWOOM_AVAILABLE = False
    logger.warning("PyQt5가 설치되지 않아 키움 API를 사용할 수 없습니다.")

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
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

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
    
    def to_dict(self):
        data = asdict(self)
        data['order_type'] = self.order_type.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class KiwoomWindowsAPI:
    """Windows 키움 API 래퍼"""
    
    def __init__(self):
        if not KIWOOM_AVAILABLE:
            raise ImportError("키움 API를 사용할 수 없습니다. PyQt5가 설치되어 있는지 확인하세요.")
        
        # QApplication 생성
        self.app = QApplication(sys.argv)
        
        # API 컨트롤 생성
        try:
            self.api = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        except Exception as e:
            handle_error(
                ErrorType.API,
                "키움 API 컨트롤 초기화 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
        
        # 이벤트 연결
        self.api.OnEventConnect.connect(self._event_connect)
        self.api.OnReceiveTrData.connect(self._receive_tr_data)
        self.api.OnReceiveRealData.connect(self._receive_real_data)
        self.api.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.api.OnReceiveMsg.connect(self._receive_msg)
        
        # 상태 변수
        self.is_connected = False
        self.is_logged_in = False
        self.login_error = None
        
        # 데이터 저장소
        self.account_info = {}
        self.stock_info = {}
        self.order_info = {}
        self.position_info = {}
        self.deposit_info = {}
        
        # 실시간 데이터
        self.real_data_cache = {}
        self.real_data_history = {}
        self.real_data_stats = {}
        
        # TR 요청 관리
        self.tr_request_no = 0
        self.tr_data = {}
        self.tr_completed = {}
        
        # 콜백 함수들
        self.login_callback = None
        self.real_data_callback = None
        self.order_callback = None
        
        logger.info("Windows 키움 API 초기화 완료")
    
    def login(self, user_id: str, password: str, account: str) -> bool:
        """로그인"""
        try:
            # 로그인 요청
            result = self.api.dynamicCall("CommConnect()")
            
            if result == 0:
                # 로그인 대기
                for _ in range(30):  # 30초 대기
                    if self.is_logged_in:
                        self.account_info = {
                            'user_id': user_id,
                            'account': account,
                            'login_time': datetime.now().isoformat()
                        }
                        logger.info("키움 API 로그인 성공")
                        return True
                    elif self.login_error:
                        logger.error(f"로그인 실패: {self.login_error}")
                        return False
                    time.sleep(1)
                
                logger.error("로그인 타임아웃")
                return False
            else:
                logger.error(f"로그인 요청 실패: {result}")
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
            account_list = self.api.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            accounts = account_list.split(';')
            
            self.account_info = {
                'accounts': accounts,
                'user_id': self.api.dynamicCall("GetLoginInfo(QString)", "USER_ID"),
                'user_name': self.api.dynamicCall("GetLoginInfo(QString)", "USER_NAME"),
                'server_gubun': self.api.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
            }
            
            return self.account_info
            
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
            # TR 요청 번호 생성
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            # 예수금 조회 TR 요청
            result = self.api.dynamicCall(
                "SetInputValue(QString, QString)",
                "계좌번호", account
            )
            
            result = self.api.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "예수금상세현황요청", "opw00001", 0, request_no
            )
            
            if result == 0:
                # TR 응답 대기
                for _ in range(10):
                    if request_no in self.tr_completed:
                        data = self.tr_data.get(request_no, {})
                        self.deposit_info = data
                        del self.tr_completed[request_no]
                        del self.tr_data[request_no]
                        return data
                    time.sleep(0.5)
                
                logger.error("예수금 조회 타임아웃")
                return {}
            else:
                logger.error(f"예수금 조회 요청 실패: {result}")
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
            # TR 요청 번호 생성
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            # 주식기본정보 TR 요청
            result = self.api.dynamicCall(
                "SetInputValue(QString, QString)",
                "종목코드", code
            )
            
            result = self.api.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "주식기본정보", "opt10001", 0, request_no
            )
            
            if result == 0:
                # TR 응답 대기
                for _ in range(10):
                    if request_no in self.tr_completed:
                        data = self.tr_data.get(request_no, {})
                        del self.tr_completed[request_no]
                        del self.tr_data[request_no]
                        
                        if data:
                            return float(data.get('현재가', 0))
                        return None
                    time.sleep(0.5)
                
                logger.error("현재가 조회 타임아웃")
                return None
            else:
                logger.error(f"현재가 조회 요청 실패: {result}")
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
            # 주문 요청
            result = self.api.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                "주식주문", "0101", account, 1, code, quantity, price, order_type, ""
            )
            
            if result == 0:
                logger.info(f"주문 요청 성공: {code} {order_type} {quantity}주")
                return {
                    'success': True,
                    'order_no': f"ORDER_{int(time.time())}",
                    'message': '주문 요청 성공'
                }
            else:
                logger.error(f"주문 요청 실패: {result}")
                return {
                    'success': False,
                    'error': f'주문 요청 실패: {result}'
                }
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"주문 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_position_info(self, account: str) -> Dict:
        """보유 종목 조회"""
        try:
            # TR 요청 번호 생성
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            # 보유종목 조회 TR 요청
            result = self.api.dynamicCall(
                "SetInputValue(QString, QString)",
                "계좌번호", account
            )
            
            result = self.api.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "보유종목조회", "opw00018", 0, request_no
            )
            
            if result == 0:
                # TR 응답 대기
                for _ in range(10):
                    if request_no in self.tr_completed:
                        data = self.tr_data.get(request_no, {})
                        self.position_info = data
                        del self.tr_completed[request_no]
                        del self.tr_data[request_no]
                        return data
                    time.sleep(0.5)
                
                logger.error("보유종목 조회 타임아웃")
                return {}
            else:
                logger.error(f"보유종목 조회 요청 실패: {result}")
                return {}
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                "보유종목 조회 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return {}
    
    def subscribe_real_data(self, code: str, real_type: str = "주식체결") -> bool:
        """실시간 데이터 구독"""
        try:
            # 실시간 데이터 요청
            result = self.api.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                "0101", code, "10;15;12;13;16;17;18;20", "1"
            )
            
            if result == 0:
                logger.info(f"실시간 데이터 구독 성공: {code}")
                return True
            else:
                logger.error(f"실시간 데이터 구독 실패: {result}")
                return False
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"실시간 데이터 구독 실패 ({code})",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
            return False
    
    def _event_connect(self, err_code):
        """로그인 이벤트"""
        if err_code == 0:
            self.is_connected = True
            self.is_logged_in = True
            logger.info("키움 API 로그인 성공")
            
            if self.login_callback:
                self.login_callback(True, None)
        else:
            self.login_error = f"로그인 실패: {err_code}"
            logger.error(self.login_error)
            
            if self.login_callback:
                self.login_callback(False, self.login_error)
    
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next):
        """TR 데이터 수신"""
        try:
            data = {}
            
            if rqname == "예수금상세현황요청":
                data = {
                    '예수금': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금"),
                    '출금가능금액': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "출금가능금액"),
                    '주문가능금액': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액")
                }
            elif rqname == "주식기본정보":
                data = {
                    '종목명': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목명"),
                    '현재가': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "현재가"),
                    '전일대비': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "전일대비"),
                    '등락율': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "등락율"),
                    '거래량': self.api.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "거래량")
                }
            
            # 데이터 정리
            for key, value in data.items():
                data[key] = value.strip()
            
            # TR 완료 표시
            self.tr_data[str(self.tr_request_no)] = data
            self.tr_completed[str(self.tr_request_no)] = True
            
        except Exception as e:
            handle_error(
                ErrorType.API,
                "TR 데이터 처리 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        try:
            if real_type == "주식체결":
                data = {
                    'code': code,
                    'price': int(self.api.dynamicCall("GetCommRealData(QString, int)", code, 10)),
                    'volume': int(self.api.dynamicCall("GetCommRealData(QString, int)", code, 15)),
                    'timestamp': datetime.now().isoformat()
                }
                
                # 캐시에 저장
                self.real_data_cache[code] = data
                
                # 히스토리에 추가
                if code not in self.real_data_history:
                    self.real_data_history[code] = []
                self.real_data_history[code].append(data)
                
                # 최대 100개까지만 유지
                if len(self.real_data_history[code]) > 100:
                    self.real_data_history[code] = self.real_data_history[code][-100:]
                
                if self.real_data_callback:
                    self.real_data_callback(code, real_type, data)
                    
        except Exception as e:
            handle_error(
                ErrorType.API,
                "실시간 데이터 처리 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신"""
        try:
            if gubun == "0":  # 주문 체결
                order_no = self.api.dynamicCall("GetChejanData(int)", 9203)
                code = self.api.dynamicCall("GetChejanData(int)", 9001)
                quantity = int(self.api.dynamicCall("GetChejanData(int)", 900))
                price = int(self.api.dynamicCall("GetChejanData(int)", 901))
                order_type = self.api.dynamicCall("GetChejanData(int)", 913)
                status = self.api.dynamicCall("GetChejanData(int)", 913)
                
                order_data = OrderData(
                    order_no=order_no.strip(),
                    code=code.strip(),
                    quantity=quantity,
                    price=price,
                    order_type=OrderType(order_type.strip()),
                    status=OrderStatus(status.strip()),
                    timestamp=datetime.now()
                )
                
                if self.order_callback:
                    self.order_callback(order_data)
                    
        except Exception as e:
            handle_error(
                ErrorType.API,
                "체결 데이터 처리 실패",
                exception=e,
                error_level=ErrorLevel.WARNING
            )
    
    def _receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        logger.info(f"키움 메시지: {msg}")

class KiwoomServer:
    """키움 API 서버"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 키움 API 인스턴스
        self.kiwoom_api = None
        
        # 라우트 설정
        self._setup_routes()
        
        logger.info(f"키움 API 서버 초기화 완료 (포트: {port})")
    
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'kiwoom_connected': self.kiwoom_api.is_connected if self.kiwoom_api else False
            })
        
        @self.app.route('/login', methods=['POST'])
        def login():
            """로그인"""
            try:
                data = request.get_json()
                user_id = data.get('user_id')
                password = data.get('password')
                account = data.get('account')
                
                if not all([user_id, password, account]):
                    return jsonify({
                        'success': False,
                        'error': '필수 정보가 누락되었습니다.'
                    }), 400
                
                if not self.kiwoom_api:
                    self.kiwoom_api = KiwoomWindowsAPI()
                
                success = self.kiwoom_api.login(user_id, password, account)
                
                if success:
                    account_info = self.kiwoom_api.get_account_info()
                    return jsonify({
                        'success': True,
                        'account_info': account_info
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '로그인에 실패했습니다.'
                    })
                    
            except Exception as e:
                logger.error(f"로그인 처리 실패: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/account-info', methods=['GET'])
        def get_account_info():
            """계좌 정보 조회"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                account_info = self.kiwoom_api.get_account_info()
                return jsonify(account_info)
                
            except Exception as e:
                logger.error(f"계좌 정보 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/deposit-info/<account>', methods=['GET'])
        def get_deposit_info(account):
            """예수금 정보 조회"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                deposit_info = self.kiwoom_api.get_deposit_info(account)
                return jsonify(deposit_info)
                
            except Exception as e:
                logger.error(f"예수금 정보 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/current-price/<code>', methods=['GET'])
        def get_current_price(code):
            """현재가 조회"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                price = self.kiwoom_api.get_current_price(code)
                if price is not None:
                    return jsonify({'price': price})
                else:
                    return jsonify({'error': '현재가 조회 실패'}), 404
                
            except Exception as e:
                logger.error(f"현재가 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/order', methods=['POST'])
        def order_stock():
            """주식 주문"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                data = request.get_json()
                account = data.get('account')
                code = data.get('code')
                quantity = data.get('quantity')
                price = data.get('price')
                order_type = data.get('order_type', '신규매수')
                
                if not all([account, code, quantity, price]):
                    return jsonify({
                        'success': False,
                        'error': '필수 정보가 누락되었습니다.'
                    }), 400
                
                result = self.kiwoom_api.order_stock(account, code, quantity, price, order_type)
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"주문 처리 실패: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/position-info/<account>', methods=['GET'])
        def get_position_info(account):
            """보유 종목 조회"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                position_info = self.kiwoom_api.get_position_info(account)
                return jsonify(position_info)
                
            except Exception as e:
                logger.error(f"보유 종목 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/order-history/<account>', methods=['GET'])
        def get_order_history(account):
            """주문 내역 조회"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                # 주문 내역 조회 구현 필요
                return jsonify([])
                
            except Exception as e:
                logger.error(f"주문 내역 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/subscribe-real-data', methods=['POST'])
        def subscribe_real_data():
            """실시간 데이터 구독"""
            try:
                if not self.kiwoom_api or not self.kiwoom_api.is_logged_in:
                    return jsonify({'error': '로그인이 필요합니다.'}), 401
                
                data = request.get_json()
                code = data.get('code')
                real_type = data.get('real_type', '주식체결')
                
                if not code:
                    return jsonify({
                        'success': False,
                        'error': '종목코드가 필요합니다.'
                    }), 400
                
                success = self.kiwoom_api.subscribe_real_data(code, real_type)
                return jsonify({
                    'success': success,
                    'error': None if success else '실시간 데이터 구독 실패'
                })
                
            except Exception as e:
                logger.error(f"실시간 데이터 구독 실패: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/real-data-cache', methods=['GET'])
        @self.app.route('/real-data-cache/<code>', methods=['GET'])
        def get_real_data_cache(code=None):
            """실시간 데이터 캐시 조회"""
            try:
                if not self.kiwoom_api:
                    return jsonify({})
                
                if code:
                    return jsonify(self.kiwoom_api.real_data_cache.get(code, {}))
                else:
                    return jsonify(self.kiwoom_api.real_data_cache)
                    
            except Exception as e:
                logger.error(f"실시간 데이터 캐시 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"키움 API 서버 시작: http://localhost:{self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            raise

def main():
    """메인 함수"""
    try:
        # 서버 생성 및 시작
        server = KiwoomServer(port=8080)
        server.start()
    except KeyboardInterrupt:
        logger.info("서버 종료")
    except Exception as e:
        logger.error(f"서버 실행 실패: {e}")

if __name__ == "__main__":
    main() 