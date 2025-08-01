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
                
                order_info = {
                    'order_no': order_no,
                    'code': code,
                    'order_type': order_type,
                    'quantity': quantity,
                    'price': price,
                    'status': order_status,
                    'timestamp': datetime.now()
                }
                
                self.order_info[order_no] = order_info
                
                # 주문 콜백 호출
                if self.on_order_callback:
                    self.on_order_callback(order_info)
                
                logger.info(f"주문 체결: {code} - {order_type} - {quantity}주 - {price:,}원 - {order_status}")
                
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
    
    def order_stock(self, account, code, quantity, price, order_type="신규매수"):
        """주식 주문"""
        try:
            order_no = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString)",
                                       "주식주문", "0101", account, 1, code, quantity, price, order_type)
            
            if order_no > 0:
                logger.info(f"주문 전송: {code} - {order_type} - {quantity}주 - {price:,}원 (주문번호: {order_no})")
                return order_no
            else:
                logger.error(f"주문 전송 실패: {order_no}")
                return None
                
        except Exception as e:
            logger.error(f"주문 전송 오류: {e}")
            return None
    
    def cancel_order(self, account, order_no, code, quantity):
        """주문 취소"""
        try:
            result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString)",
                                     "주문취소", "0101", account, 2, code, quantity, 0, "주문취소")
            
            if result > 0:
                logger.info(f"주문 취소: {code} - {order_no}")
                return result
            else:
                logger.error(f"주문 취소 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"주문 취소 오류: {e}")
            return None
    
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