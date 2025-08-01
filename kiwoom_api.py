"""
키움증권 API 자동매매 시스템
키움 Open API+를 사용한 자동매매 프로그램
"""

import sys
import time
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum

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

class KiwoomAPI(QAxWidget):
    """
    키움증권 API 래퍼 클래스
    """
    
    def __init__(self):
        super().__init__()
        
        # API 컨트롤 생성
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 연결
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveRealData.connect(self._receive_real_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveMsg.connect(self._receive_msg)
        
        # 로그인 상태
        self.login_status = False
        self.login_error = None
        
        # TR 요청 번호
        self.tr_request_no = 0
        self.tr_data = {}
        self.tr_completed = {}
        
        # 데이터 저장소
        self.account_info = {}
        self.stock_info = {}
        self.order_info = {}
        self.position_info = {}
        self.deposit_info = {} # 예수금 정보를 저장할 딕셔너리
        
        # 주문 관리
        self.pending_orders = {}  # 대기 중인 주문들
        self.order_history = {}   # 주문 내역
        self.max_retry_count = 3  # 최대 재시도 횟수
        
        # 실시간 데이터 구독
        self.real_data_codes = set()
        
        # 콜백 함수들
        self.on_login_callback = None
        self.on_real_data_callback = None
        self.on_order_callback = None
        
        logger.info("키움 API 초기화 완료")
    
    def set_login_callback(self, callback):
        """로그인 완료 콜백 설정"""
        self.on_login_callback = callback
    
    def set_real_data_callback(self, callback):
        """실시간 데이터 콜백 설정"""
        self.on_real_data_callback = callback
    
    def set_order_callback(self, callback):
        """주문 완료 콜백 설정"""
        self.on_order_callback = callback
    
    def login(self, timeout=30):
        """로그인 요청"""
        logger.info("로그인 요청 중...")
        self.login_status = False
        self.login_error = None
        
        # 로그인 요청
        result = self.dynamicCall("CommConnect()")
        if result != 0:
            logger.error(f"로그인 요청 실패: {result}")
            return False
        
        # 로그인 완료까지 대기
        start_time = time.time()
        while not self.login_status and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not self.login_status:
            logger.error("로그인 타임아웃")
            return False
        
        if self.login_error:
            logger.error(f"로그인 실패: {self.login_error}")
            return False
        
        logger.info("로그인 완료")
        
        # 로그인 콜백 호출
        if self.on_login_callback:
            self.on_login_callback(self.login_status)
        
        return True
    
    def _event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            self.login_status = True
            self.login_error = None
            logger.info("로그인 성공")
        else:
            self.login_status = False
            self.login_error = err_code
            logger.error(f"로그인 실패: {err_code}")
    
    def _receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 처리"""
        logger.info(f"메시지 수신: {rqname} - {msg}")
    
    def get_account_info(self):
        """계좌 정보 조회"""
        try:
            account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
            accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')
            
            for account in accounts:
                if account:
                    self.account_info[account] = {
                        'account': account,
                        'user_id': self.dynamicCall("GetLoginInfo(QString)", "USER_ID"),
                        'user_name': self.dynamicCall("GetLoginInfo(QString)", "USER_NAME"),
                        'server_gubun': self.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
                    }
            
            logger.info(f"계좌 정보 조회 완료: {len(self.account_info)}개")
            return self.account_info
        except Exception as e:
            logger.error(f"계좌 정보 조회 오류: {e}")
            return {}
    
    def get_deposit_info(self, account):
        """예수금 조회 (기본 메서드 - 비밀번호 없음)"""
        return self.get_deposit_info_with_password(account, "")
    
    def get_deposit_info_with_password(self, account, password):
        """예수금 조회 (비밀번호 포함)"""
        try:
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            # TR 요청
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", password)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
            
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                    "예수금상세현황요청", "opw00001", 0, request_no)
            
            if result != 0:
                logger.error(f"예수금 조회 TR 요청 실패: {result}")
                return {}
            
            # TR 응답 대기
            start_time = time.time()
            while request_no not in self.tr_completed and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if request_no in self.tr_completed:
                self.tr_completed.pop(request_no)
                return self.deposit_info.get(account, {})
            else:
                logger.error("예수금 조회 TR 응답 타임아웃")
                return {}
                
        except Exception as e:
            logger.error(f"예수금 조회 오류: {e}")
            return {}
    
    def get_stock_basic_info(self, code):
        """주식 기본 정보 조회"""
        try:
            name = self.dynamicCall("GetMasterCodeName(QString)", code)
            return {
                'code': code,
                'name': name
            }
        except Exception as e:
            logger.error(f"종목 정보 조회 오류: {e}")
            return {'code': code, 'name': '알 수 없음'}
    
    def get_current_price(self, code):
        """현재가 조회"""
        try:
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            # TR 요청
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                    "주식기본정보", "opt10001", 0, request_no)
            
            if result != 0:
                logger.error(f"TR 요청 실패: {result}")
                return {}
            
            # TR 응답 대기
            start_time = time.time()
            while request_no not in self.tr_completed and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if request_no in self.tr_completed:
                self.tr_completed.pop(request_no)
                return self.stock_info.get(code, {})
            else:
                logger.error("TR 응답 타임아웃")
                return {}
                
        except Exception as e:
            logger.error(f"현재가 조회 오류: {e}")
            return {}
    
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next):
        """TR 데이터 수신 처리"""
        try:
            if rqname == "주식기본정보":
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                      trcode, rqname, 0, "종목코드").strip()
                name = self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                      trcode, rqname, 0, "종목명").strip()
                current_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                   trcode, rqname, 0, "현재가").strip())
                volume = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                            trcode, rqname, 0, "거래량").strip())
                
                self.stock_info[code] = {
                    'code': code,
                    'name': name,
                    'current_price': current_price,
                    'volume': volume,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"주식 정보 수신: {code} - {name} - {current_price:,}원")
            
            elif rqname == "예수금상세현황요청":
                # 예수금 정보 처리
                deposit = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                             trcode, rqname, 0, "예수금").strip())
                available_deposit = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                       trcode, rqname, 0, "출금가능금액").strip())
                orderable_amount = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                      trcode, rqname, 0, "주문가능금액").strip())
                
                # 계좌번호는 TR 요청 시 사용한 계좌번호를 사용
                account = self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                         trcode, rqname, 0, "계좌번호").strip()
                
                self.deposit_info[account] = {
                    'account': account,
                    'deposit': deposit,
                    'available_deposit': available_deposit,
                    'orderable_amount': orderable_amount,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"예수금 정보 수신: {account} - 예수금: {deposit:,}원, 출금가능: {available_deposit:,}원, 주문가능: {orderable_amount:,}원")
            
            # TR 완료 표시
            self.tr_completed[str(self.tr_request_no)] = True
            
        except Exception as e:
            logger.error(f"TR 데이터 처리 오류: {e}")
    
    def _receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신 처리"""
        try:
            if real_type == "주식체결":
                current_price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 10))
                volume = int(self.dynamicCall("GetCommRealData(QString, int)", code, 15))
                change = int(self.dynamicCall("GetCommRealData(QString, int)", code, 12))
                change_rate = float(self.dynamicCall("GetCommRealData(QString, int)", code, 13))
                
                if code in self.stock_info:
                    self.stock_info[code].update({
                        'current_price': current_price,
                        'volume': volume,
                        'change': change,
                        'change_rate': change_rate,
                        'timestamp': datetime.now()
                    })
                
                # 실시간 데이터 콜백 호출
                if self.on_real_data_callback:
                    self.on_real_data_callback(code, {
                        'current_price': current_price,
                        'volume': volume,
                        'change': change,
                        'change_rate': change_rate
                    })
                
                logger.debug(f"실시간 데이터: {code} - {current_price:,}원 ({change_rate:+.2f}%)")
                
        except Exception as e:
            logger.error(f"실시간 데이터 처리 오류: {e}")
    
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결잔고 데이터 수신 처리"""
        try:
            if gubun == "0":  # 주문체결통보
                order_no = self.dynamicCall("GetChejanData(int)", 9203).strip()
                code = self.dynamicCall("GetChejanData(int)", 9001).strip()
                order_type = self.dynamicCall("GetChejanData(int)", 913).strip()
                quantity = int(self.dynamicCall("GetChejanData(int)", 900).strip())
                price = int(self.dynamicCall("GetChejanData(int)", 901).strip())
                order_status = self.dynamicCall("GetChejanData(int)", 913).strip()
                
                # 체결 수량과 미체결 수량
                filled_quantity = int(self.dynamicCall("GetChejanData(int)", 911).strip())
                unfilled_quantity = int(self.dynamicCall("GetChejanData(int)", 912).strip())
                
                order_info = {
                    'order_no': order_no,
                    'code': code,
                    'order_type': order_type,
                    'quantity': quantity,
                    'price': price,
                    'filled_quantity': filled_quantity,
                    'unfilled_quantity': unfilled_quantity,
                    'status': order_status,
                    'timestamp': datetime.now()
                }
                
                # 주문 상태 업데이트
                self.order_info[order_no] = order_info
                
                # 대기 중인 주문에서 제거 (완료된 경우)
                if order_no in self.pending_orders:
                    if order_status in ["체결", "취소", "거부"]:
                        completed_order = self.pending_orders.pop(order_no)
                        self.order_history[order_no] = completed_order
                
                # 주문 콜백 호출
                if self.on_order_callback:
                    self.on_order_callback(order_info)
                
                logger.info(f"주문 체결: {code} - {order_type} - {filled_quantity}/{quantity}주 - {price:,}원 - {order_status}")
                
        except Exception as e:
            logger.error(f"체결잔고 데이터 처리 오류: {e}")
    
    def subscribe_real_data(self, code):
        """실시간 데이터 구독"""
        try:
            if code not in self.real_data_codes:
                result = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                                        "0101", code, "10;15;12;13", "1")
                if result == 0:
                    self.real_data_codes.add(code)
                    logger.info(f"실시간 데이터 구독: {code}")
                else:
                    logger.error(f"실시간 데이터 구독 실패: {code} - {result}")
        except Exception as e:
            logger.error(f"실시간 데이터 구독 오류: {e}")
    
    def unsubscribe_real_data(self, code):
        """실시간 데이터 구독 해제"""
        try:
            if code in self.real_data_codes:
                self.dynamicCall("SetRealRemove(QString, QString)", "0101", code)
                self.real_data_codes.remove(code)
                logger.info(f"실시간 데이터 구독 해제: {code}")
        except Exception as e:
            logger.error(f"실시간 데이터 구독 해제 오류: {e}")
    
    def validate_order(self, account, code, quantity, price, order_type):
        """주문 유효성 검증"""
        try:
            # 기본 검증
            if not account or not code or quantity <= 0 or price <= 0:
                logger.error("주문 파라미터 오류")
                return False, "주문 파라미터 오류"
            
            # 계좌 정보 확인
            if not self.account_info:
                logger.error("계좌 정보가 없습니다")
                return False, "계좌 정보 없음"
            
            # 예수금 확인 (매수인 경우)
            if order_type in ["신규매수", "매수정정"]:
                deposit = self.get_deposit_info(account)
                required_amount = quantity * price
                if deposit.get('예수금', 0) < required_amount:
                    logger.error(f"예수금 부족: 필요 {required_amount:,}원, 보유 {deposit.get('예수금', 0):,}원")
                    return False, "예수금 부족"
            
            # 보유 주식 확인 (매도인 경우)
            if order_type in ["신규매도", "매도정정"]:
                position = self.get_position_info(account)
                if code in position:
                    available_quantity = position[code].get('보유수량', 0)
                    if available_quantity < quantity:
                        logger.error(f"보유 주식 부족: 필요 {quantity}주, 보유 {available_quantity}주")
                        return False, "보유 주식 부족"
                else:
                    logger.error(f"보유하지 않은 종목: {code}")
                    return False, "보유하지 않은 종목"
            
            return True, "검증 통과"
            
        except Exception as e:
            logger.error(f"주문 검증 오류: {e}")
            return False, f"검증 오류: {e}"

    def order_stock(self, account, code, quantity, price, order_type="신규매수", retry_count=0):
        """주식 주문 (개선된 버전)"""
        try:
            # 주문 검증
            is_valid, message = self.validate_order(account, code, quantity, price, order_type)
            if not is_valid:
                logger.error(f"주문 검증 실패: {message}")
                return None
            
            # 주문 전송
            order_no = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString)",
                                       "주식주문", "0101", account, 1, code, quantity, price, order_type)
            
            if order_no > 0:
                # 대기 중인 주문에 추가
                pending_order = {
                    'order_no': order_no,
                    'account': account,
                    'code': code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'retry_count': retry_count,
                    'timestamp': datetime.now(),
                    'status': OrderStatus.PENDING.value
                }
                self.pending_orders[order_no] = pending_order
                
                logger.info(f"주문 전송 성공: {code} - {order_type} - {quantity}주 - {price:,}원 (주문번호: {order_no})")
                return order_no
            else:
                logger.error(f"주문 전송 실패: {order_no}")
                
                # 재시도 로직
                if retry_count < self.max_retry_count:
                    logger.info(f"주문 재시도 중... ({retry_count + 1}/{self.max_retry_count})")
                    time.sleep(1)  # 1초 대기
                    return self.order_stock(account, code, quantity, price, order_type, retry_count + 1)
                else:
                    logger.error(f"주문 최대 재시도 횟수 초과")
                    return None
                
        except Exception as e:
            logger.error(f"주문 전송 오류: {e}")
            return None

    def buy_stock(self, account, code, quantity, price):
        """매수 주문"""
        return self.order_stock(account, code, quantity, price, OrderType.BUY.value)
    
    def sell_stock(self, account, code, quantity, price):
        """매도 주문"""
        return self.order_stock(account, code, quantity, price, OrderType.SELL.value)
    
    def buy_market_order(self, account, code, quantity):
        """시장가 매수"""
        return self.order_stock(account, code, quantity, 0, OrderType.BUY.value)
    
    def sell_market_order(self, account, code, quantity):
        """시장가 매도"""
        return self.order_stock(account, code, quantity, 0, OrderType.SELL.value)

    def cancel_order(self, account, order_no, code, quantity):
        """주문 취소 (개선된 버전)"""
        try:
            # 취소할 주문이 대기 중인지 확인
            if order_no not in self.pending_orders:
                logger.error(f"취소할 주문을 찾을 수 없음: {order_no}")
                return None
            
            pending_order = self.pending_orders[order_no]
            
            # 주문 취소
            result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString)",
                                     "주문취소", "0101", account, 2, code, quantity, 0, "주문취소")
            
            if result > 0:
                logger.info(f"주문 취소 요청: {code} - {order_no}")
                return result
            else:
                logger.error(f"주문 취소 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"주문 취소 오류: {e}")
            return None

    def modify_order(self, account, order_no, code, quantity, price):
        """주문 정정"""
        try:
            # 정정할 주문이 대기 중인지 확인
            if order_no not in self.pending_orders:
                logger.error(f"정정할 주문을 찾을 수 없음: {order_no}")
                return None
            
            pending_order = self.pending_orders[order_no]
            original_type = pending_order['order_type']
            
            # 매수/매도에 따른 정정 타입 결정
            if "매수" in original_type:
                modify_type = OrderType.BUY_MODIFY.value
            else:
                modify_type = OrderType.SELL_MODIFY.value
            
            # 주문 정정
            result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString)",
                                     "주문정정", "0101", account, 3, code, quantity, price, modify_type)
            
            if result > 0:
                logger.info(f"주문 정정 요청: {code} - {order_no} - {quantity}주 - {price:,}원")
                return result
            else:
                logger.error(f"주문 정정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"주문 정정 오류: {e}")
            return None

    def get_pending_orders(self):
        """대기 중인 주문 조회"""
        return self.pending_orders.copy()
    
    def get_order_status(self, order_no):
        """특정 주문 상태 조회"""
        if order_no in self.pending_orders:
            return self.pending_orders[order_no]
        elif order_no in self.order_history:
            return self.order_history[order_no]
        else:
            return None

    def cancel_all_orders(self, account):
        """모든 대기 중인 주문 취소"""
        cancelled_count = 0
        for order_no, order_info in self.pending_orders.items():
            if order_info['account'] == account:
                result = self.cancel_order(account, order_no, order_info['code'], order_info['quantity'])
                if result:
                    cancelled_count += 1
        
        logger.info(f"전체 주문 취소 완료: {cancelled_count}건")
        return cancelled_count
    
    def get_position_info(self, account):
        """보유 종목 조회"""
        try:
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
            
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                    "보유종목조회", "opw00018", 0, request_no)
            
            if result != 0:
                logger.error(f"보유종목 조회 실패: {result}")
                return {}
            
            # TR 응답 대기
            start_time = time.time()
            while request_no not in self.tr_completed and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if request_no in self.tr_completed:
                self.tr_completed.pop(request_no)
                return self.position_info
            else:
                logger.error("보유종목 조회 타임아웃")
                return {}
                
        except Exception as e:
            logger.error(f"보유종목 조회 오류: {e}")
            return {}
    
    def get_order_history(self, account):
        """주문 내역 조회"""
        try:
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
            self.dynamicCall("SetInputValue(QString, QString)", "시작일자", 
                            (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"))
            self.dynamicCall("SetInputValue(QString, QString)", "종료일자", 
                            datetime.now().strftime("%Y%m%d"))
            
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                    "주문내역조회", "opt10075", 0, request_no)
            
            if result != 0:
                logger.error(f"주문내역 조회 실패: {result}")
                return {}
            
            # TR 응답 대기
            start_time = time.time()
            while request_no not in self.tr_completed and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if request_no in self.tr_completed:
                self.tr_completed.pop(request_no)
                return self.order_info
            else:
                logger.error("주문내역 조회 타임아웃")
                return {}
                
        except Exception as e:
            logger.error(f"주문내역 조회 오류: {e}")
            return {} 