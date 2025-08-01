"""
키움증권 API 자동매매 시스템
키움 Open API+를 사용한 자동매매 프로그램
"""

import sys
import time
import threading
from collections import defaultdict, deque
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum

# 에러 처리 및 모니터링 모듈 import
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation, error_handler
from system_monitor import system_monitor, record_api_call, record_data_processed, record_order_execution

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
    FUTURES = "선물"
    OPTION = "옵션"

class KiwoomAPI(QAxWidget):
    """
    키움증권 API 래퍼 클래스 (안정성 강화 버전)
    """
    
    def __init__(self):
        super().__init__()
        
        # API 컨트롤 생성
        try:
            self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        except Exception as e:
            handle_error(
                ErrorType.API,
                "키움 API 컨트롤 초기화 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
        
        # 이벤트 연결
        try:
            self.OnEventConnect.connect(self._event_connect)
            self.OnReceiveTrData.connect(self._receive_tr_data)
            self.OnReceiveRealData.connect(self._receive_real_data)
            self.OnReceiveChejanData.connect(self._receive_chejan_data)
            self.OnReceiveMsg.connect(self._receive_msg)
        except Exception as e:
            handle_error(
                ErrorType.API,
                "키움 API 이벤트 연결 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
        
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
        
        # 실시간 데이터 관리 (최적화)
        self.real_data_codes = set()  # 구독 중인 종목 코드
        self.real_data_cache = {}     # 실시간 데이터 캐시
        self.real_data_history = defaultdict(lambda: deque(maxlen=1000))  # 최근 1000개 데이터 보관
        self.real_data_stats = defaultdict(lambda: {
            'last_update': None,
            'update_count': 0,
            'error_count': 0,
            'avg_processing_time': 0.0
        })
        
        # 성능 최적화
        self.data_lock = threading.Lock()  # 데이터 동기화용 락
        self.callback_queue = deque(maxlen=1000)  # 콜백 큐
        self.processing_thread = None
        self.is_processing = False
        
        # 실시간 데이터 설정
        self.real_data_config = {
            'enable_caching': True,
            'cache_ttl': 1.0,  # 캐시 유효시간 (초)
            'max_history_size': 1000,
            'enable_stats': True,
            'batch_processing': True,
            'batch_size': 10,
            'batch_interval': 0.1  # 배치 처리 간격 (초)
        }
        
        # 콜백 함수들
        self.on_login_callback = None
        self.on_real_data_callback = None
        self.on_order_callback = None
        
        # 배치 처리 타이머
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_batch_callbacks)
        self.batch_timer.start(int(self.real_data_config['batch_interval'] * 1000))
        
        # 안정성 설정
        self.stability_config = {
            'enable_health_check': True,
            'health_check_interval': 30.0,  # 30초마다 헬스 체크
            'max_consecutive_errors': 5,
            'auto_recovery_enabled': True,
            'connection_timeout': 10.0,
            'operation_timeout': 30.0
        }
        
        # 헬스 체크 타이머
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._perform_health_check)
        if self.stability_config['enable_health_check']:
            self.health_timer.start(int(self.stability_config['health_check_interval'] * 1000))
        
        # 에러 통계
        self.error_stats = {
            'consecutive_errors': 0,
            'total_errors': 0,
            'last_error_time': None,
            'recovery_attempts': 0
        }
        
        logger.info("키움 API 초기화 완료 (안정성 강화 적용)")

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
        """로그인 요청 (안정성 강화)"""
        start_time = time.time()
        
        try:
            logger.info("로그인 요청 중...")
            self.login_status = False
            self.login_error = None
            
            # 로그인 요청
            result = self.dynamicCall("CommConnect()")
            if result != 0:
                error_msg = f"로그인 요청 실패: {result}"
                handle_error(
                    ErrorType.API,
                    error_msg,
                    context={'result': result},
                    error_level=ErrorLevel.ERROR
                )
                return False
            
            # 로그인 완료까지 대기
            while not self.login_status and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if not self.login_status:
                error_msg = "로그인 타임아웃"
                handle_error(
                    ErrorType.TIMEOUT,
                    error_msg,
                    context={'timeout': timeout},
                    error_level=ErrorLevel.ERROR
                )
                return False
            
            if self.login_error:
                error_msg = f"로그인 실패: {self.login_error}"
                handle_error(
                    ErrorType.API,
                    error_msg,
                    context={'login_error': self.login_error},
                    error_level=ErrorLevel.ERROR
                )
                return False
            
            # 성공 기록
            response_time = time.time() - start_time
            record_api_call(response_time, True)
            
            logger.info("로그인 완료")
            
            # 로그인 콜백 호출
            if self.on_login_callback:
                self.on_login_callback(self.login_status)
            
            return True
            
        except Exception as e:
            response_time = time.time() - start_time
            record_api_call(response_time, False)
            
            handle_error(
                ErrorType.API,
                f"로그인 중 예외 발생: {e}",
                exception=e,
                context={'timeout': timeout},
                error_level=ErrorLevel.ERROR
            )
            return False

    def _event_connect(self, err_code):
        """로그인 이벤트 처리 (안정성 강화)"""
        try:
            if err_code == 0:
                self.login_status = True
                self.login_error = None
                logger.info("로그인 성공")
                
                # 에러 통계 리셋
                self.error_stats['consecutive_errors'] = 0
                self.error_stats['recovery_attempts'] = 0
                
            else:
                self.login_status = False
                self.login_error = f"로그인 실패 (에러코드: {err_code})"
                
                handle_error(
                    ErrorType.API,
                    f"로그인 실패: 에러코드 {err_code}",
                    context={'err_code': err_code},
                    error_level=ErrorLevel.ERROR
                )
                
                # 에러 통계 업데이트
                self.error_stats['consecutive_errors'] += 1
                self.error_stats['total_errors'] += 1
                self.error_stats['last_error_time'] = datetime.now()
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"로그인 이벤트 처리 오류: {e}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )

    def _receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 처리 (안정성 강화)"""
        try:
            if msg:
                logger.info(f"TR 메시지: {msg}")
                
                # 에러 메시지 감지
                if "에러" in msg or "오류" in msg or "실패" in msg:
                    handle_error(
                        ErrorType.API,
                        f"TR 에러 메시지: {msg}",
                        context={'screen_no': screen_no, 'rqname': rqname, 'trcode': trcode},
                        error_level=ErrorLevel.WARNING
                    )
                    
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"메시지 수신 처리 오류: {e}",
                exception=e,
                error_level=ErrorLevel.WARNING
            )

    def get_account_info(self):
        """계좌 정보 조회 (안정성 강화)"""
        return retry_operation(
            self._get_account_info_internal,
            error_type=ErrorType.API,
            context={'operation': 'get_account_info'}
        )
    
    def _get_account_info_internal(self):
        """계좌 정보 조회 내부 구현"""
        try:
            account_count = self.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
            account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
            
            if account_count and account_list:
                accounts = account_list.split(';')
                for account in accounts:
                    if account.strip():
                        self.account_info[account] = {
                            'account': account,
                            'timestamp': datetime.now()
                        }
            
            return self.account_info
            
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"계좌 정보 조회 오류: {e}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            return {}

    def get_deposit_info(self, account):
        """예수금 정보 조회 (안정성 강화)"""
        return retry_operation(
            self._get_deposit_info_internal,
            account,
            error_type=ErrorType.API,
            context={'operation': 'get_deposit_info', 'account': account}
        )
    
    def _get_deposit_info_internal(self, account):
        """예수금 정보 조회 내부 구현"""
        try:
            self.tr_request_no += 1
            request_no = str(self.tr_request_no)
            
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
            
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                    "예수금상세현황요청", "opw00001", 0, request_no)
            
            if result != 0:
                handle_error(
                    ErrorType.API,
                    f"예수금 조회 실패: {result}",
                    context={'result': result, 'account': account},
                    error_level=ErrorLevel.ERROR
                )
                return {}
            
            # TR 응답 대기
            start_time = time.time()
            while request_no not in self.tr_completed and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if request_no in self.tr_completed:
                self.tr_completed.pop(request_no)
                return self.deposit_info.get(account, {})
            else:
                handle_error(
                    ErrorType.TIMEOUT,
                    "예수금 조회 타임아웃",
                    context={'account': account, 'request_no': request_no},
                    error_level=ErrorLevel.WARNING
                )
                return {}
                
        except Exception as e:
            handle_error(
                ErrorType.API,
                f"예수금 조회 오류: {e}",
                exception=e,
                context={'account': account},
                error_level=ErrorLevel.ERROR
            )
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
        """실시간 데이터 수신 처리 (안정성 강화)"""
        start_time = time.time()
        
        try:
            with self.data_lock:
                if real_type == "주식체결":
                    self._process_stock_tick_data(code, start_time)
                elif real_type == "주식주문체결":
                    self._process_stock_order_data(code, start_time)
                elif real_type == "지수":
                    self._process_index_data(code, start_time)
                else:
                    logger.debug(f"미지원 실시간 데이터 타입: {real_type} - {code}")
                    
        except Exception as e:
            handle_error(
                ErrorType.DATA,
                f"실시간 데이터 처리 오류: {code} - {real_type} - {e}",
                exception=e,
                context={'code': code, 'real_type': real_type},
                error_level=ErrorLevel.ERROR
            )
            self.real_data_stats[code]['error_count'] += 1

    def _process_stock_tick_data(self, code, start_time):
        """주식 체결 데이터 처리 (안정성 강화)"""
        try:
            # 실시간 데이터 추출
            current_price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 10))
            volume = int(self.dynamicCall("GetCommRealData(QString, int)", code, 15))
            change = int(self.dynamicCall("GetCommRealData(QString, int)", code, 12))
            change_rate = float(self.dynamicCall("GetCommRealData(QString, int)", code, 13))
            
            # 추가 데이터 추출
            open_price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 16))
            high_price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 17))
            low_price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 18))
            total_volume = int(self.dynamicCall("GetCommRealData(QString, int)", code, 20))
            
            # 데이터 검증
            if not self._validate_real_data(code, current_price, volume):
                return
            
            # 타임스탬프 생성
            timestamp = datetime.now()
            
            # 데이터 구조화
            tick_data = {
                'code': code,
                'current_price': current_price,
                'volume': volume,
                'change': change,
                'change_rate': change_rate,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'total_volume': total_volume,
                'timestamp': timestamp,
                'real_type': RealDataType.STOCK_TICK.value
            }
            
            # 캐시 업데이트
            if self.real_data_config['enable_caching']:
                self.real_data_cache[code] = {
                    'data': tick_data,
                    'timestamp': timestamp
                }
            
            # 히스토리 업데이트
            self.real_data_history[code].append(tick_data)
            
            # 통계 업데이트
            self._update_real_data_stats(code, start_time)
            
            # 콜백 큐에 추가
            if self.on_real_data_callback:
                self.callback_queue.append({
                    'type': 'real_data',
                    'code': code,
                    'data': tick_data,
                    'timestamp': timestamp
                })
            
            # 성능 기록
            processing_time = time.time() - start_time
            record_data_processed(1)
            
            # 로깅 (디버그 레벨로 변경하여 성능 향상)
            logger.debug(f"실시간 체결: {code} - {current_price:,}원 ({change_rate:+.2f}%) - {volume:,}주")
            
        except Exception as e:
            handle_error(
                ErrorType.DATA,
                f"주식 체결 데이터 처리 오류: {code} - {e}",
                exception=e,
                context={'code': code},
                error_level=ErrorLevel.ERROR
            )
            self.real_data_stats[code]['error_count'] += 1

    def _process_stock_order_data(self, code, start_time):
        """주식 주문 체결 데이터 처리"""
        try:
            # 주문 체결 데이터 추출
            order_no = self.dynamicCall("GetCommRealData(QString, int)", code, 9203).strip()
            order_type = self.dynamicCall("GetCommRealData(QString, int)", code, 913).strip()
            quantity = int(self.dynamicCall("GetCommRealData(QString, int)", code, 900).strip())
            price = int(self.dynamicCall("GetCommRealData(QString, int)", code, 901).strip())
            
            order_data = {
                'code': code,
                'order_no': order_no,
                'order_type': order_type,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now(),
                'real_type': RealDataType.STOCK_ORDER.value
            }
            
            # 콜백 큐에 추가
            if self.on_order_callback:
                self.callback_queue.append({
                    'type': 'order_data',
                    'code': code,
                    'data': order_data,
                    'timestamp': datetime.now()
                })
            
        except Exception as e:
            logger.error(f"주식 주문 데이터 처리 오류: {code} - {e}")

    def _process_index_data(self, code, start_time):
        """지수 데이터 처리"""
        try:
            index_value = float(self.dynamicCall("GetCommRealData(QString, int)", code, 10))
            change = float(self.dynamicCall("GetCommRealData(QString, int)", code, 12))
            change_rate = float(self.dynamicCall("GetCommRealData(QString, int)", code, 13))
            
            index_data = {
                'code': code,
                'index_value': index_value,
                'change': change,
                'change_rate': change_rate,
                'timestamp': datetime.now(),
                'real_type': RealDataType.INDEX.value
            }
            
            # 캐시 업데이트
            if self.real_data_config['enable_caching']:
                self.real_data_cache[code] = {
                    'data': index_data,
                    'timestamp': datetime.now()
                }
            
        except Exception as e:
            logger.error(f"지수 데이터 처리 오류: {code} - {e}")

    def _validate_real_data(self, code, price, volume):
        """실시간 데이터 유효성 검증"""
        try:
            # 기본 검증
            if price <= 0 or volume < 0:
                logger.warning(f"유효하지 않은 데이터: {code} - 가격: {price}, 거래량: {volume}")
                return False
            
            # 이전 데이터와 비교하여 급격한 변화 감지
            if code in self.real_data_cache:
                prev_data = self.real_data_cache[code]['data']
                prev_price = prev_data.get('current_price', 0)
                
                if prev_price > 0:
                    price_change_rate = abs(price - prev_price) / prev_price
                    if price_change_rate > 0.3:  # 30% 이상 급격한 변화
                        logger.warning(f"급격한 가격 변화 감지: {code} - {prev_price:,} → {price:,} ({price_change_rate:.2%})")
            
            return True
            
        except Exception as e:
            logger.error(f"데이터 검증 오류: {code} - {e}")
            return False

    def _update_real_data_stats(self, code, start_time):
        """실시간 데이터 통계 업데이트"""
        try:
            processing_time = time.time() - start_time
            stats = self.real_data_stats[code]
            
            # 평균 처리 시간 계산
            if stats['update_count'] == 0:
                stats['avg_processing_time'] = processing_time
            else:
                stats['avg_processing_time'] = (
                    stats['avg_processing_time'] * stats['update_count'] + processing_time
                ) / (stats['update_count'] + 1)
            
            stats['update_count'] += 1
            stats['last_update'] = datetime.now()
            
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {code} - {e}")

    def _process_batch_callbacks(self):
        """배치 콜백 처리"""
        if not self.callback_queue:
            return
        
        try:
            # 배치 크기만큼 콜백 처리
            batch_size = min(self.real_data_config['batch_size'], len(self.callback_queue))
            processed_count = 0
            
            while self.callback_queue and processed_count < batch_size:
                callback_data = self.callback_queue.popleft()
                processed_count += 1
                
                try:
                    if callback_data['type'] == 'real_data':
                        if self.on_real_data_callback:
                            self.on_real_data_callback(
                                callback_data['code'], 
                                callback_data['data']
                            )
                    elif callback_data['type'] == 'order_data':
                        if self.on_order_callback:
                            self.on_order_callback(callback_data['data'])
                            
                except Exception as e:
                    logger.error(f"콜백 처리 오류: {e}")
            
            if processed_count > 0:
                logger.debug(f"배치 콜백 처리 완료: {processed_count}건")
                
        except Exception as e:
            logger.error(f"배치 콜백 처리 오류: {e}")

    def subscribe_real_data(self, code, real_type="주식체결", fid_list="10;15;12;13;16;17;18;20"):
        """실시간 데이터 구독 (개선된 버전)"""
        try:
            if code not in self.real_data_codes:
                result = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                                        "0101", code, fid_list, "1")
                if result == 0:
                    self.real_data_codes.add(code)
                    
                    # 초기화
                    if code not in self.real_data_cache:
                        self.real_data_cache[code] = {}
                    if code not in self.real_data_stats:
                        self.real_data_stats[code] = {
                            'last_update': None,
                            'update_count': 0,
                            'error_count': 0,
                            'avg_processing_time': 0.0
                        }
                    
                    logger.info(f"실시간 데이터 구독 성공: {code} - {real_type}")
                    return True
                else:
                    logger.error(f"실시간 데이터 구독 실패: {code} - {result}")
                    return False
            else:
                logger.debug(f"이미 구독 중인 종목: {code}")
                return True
                
        except Exception as e:
            logger.error(f"실시간 데이터 구독 오류: {code} - {e}")
            return False

    def unsubscribe_real_data(self, code):
        """실시간 데이터 구독 해제 (개선된 버전)"""
        try:
            if code in self.real_data_codes:
                self.dynamicCall("SetRealRemove(QString, QString)", "0101", code)
                self.real_data_codes.remove(code)
                
                # 캐시 및 히스토리 정리
                if code in self.real_data_cache:
                    del self.real_data_cache[code]
                if code in self.real_data_history:
                    del self.real_data_history[code]
                if code in self.real_data_stats:
                    del self.real_data_stats[code]
                
                logger.info(f"실시간 데이터 구독 해제: {code}")
                return True
            else:
                logger.debug(f"구독하지 않은 종목: {code}")
                return False
                
        except Exception as e:
            logger.error(f"실시간 데이터 구독 해제 오류: {code} - {e}")
            return False

    def get_real_data_cache(self, code=None):
        """실시간 데이터 캐시 조회"""
        try:
            with self.data_lock:
                if code:
                    if code in self.real_data_cache:
                        cache_data = self.real_data_cache[code]
                        # 캐시 유효성 확인
                        if (datetime.now() - cache_data['timestamp']).total_seconds() > self.real_data_config['cache_ttl']:
                            logger.warning(f"캐시 만료: {code}")
                            return None
                        return cache_data['data']
                    return None
                else:
                    return self.real_data_cache.copy()
                    
        except Exception as e:
            logger.error(f"캐시 조회 오류: {e}")
            return None

    def get_real_data_history(self, code, limit=100):
        """실시간 데이터 히스토리 조회"""
        try:
            with self.data_lock:
                if code in self.real_data_history:
                    history = list(self.real_data_history[code])
                    return history[-limit:] if limit > 0 else history
                return []
                
        except Exception as e:
            logger.error(f"히스토리 조회 오류: {code} - {e}")
            return []

    def get_real_data_stats(self, code=None):
        """실시간 데이터 통계 조회"""
        try:
            with self.data_lock:
                if code:
                    return self.real_data_stats.get(code, {})
                else:
                    return dict(self.real_data_stats)
                    
        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return {}

    def clear_real_data_cache(self, code=None):
        """실시간 데이터 캐시 정리"""
        try:
            with self.data_lock:
                if code:
                    if code in self.real_data_cache:
                        del self.real_data_cache[code]
                        logger.info(f"캐시 정리: {code}")
                else:
                    self.real_data_cache.clear()
                    logger.info("전체 캐시 정리")
                    
        except Exception as e:
            logger.error(f"캐시 정리 오류: {e}")

    def set_real_data_config(self, **kwargs):
        """실시간 데이터 설정 변경"""
        try:
            for key, value in kwargs.items():
                if key in self.real_data_config:
                    self.real_data_config[key] = value
                    logger.info(f"실시간 데이터 설정 변경: {key} = {value}")
                else:
                    logger.warning(f"알 수 없는 설정: {key}")
                    
        except Exception as e:
            logger.error(f"설정 변경 오류: {e}")

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
        """주식 주문 (안정성 강화)"""
        start_time = time.time()
        
        try:
            # 주문 검증
            is_valid, message = self.validate_order(account, code, quantity, price, order_type)
            if not is_valid:
                handle_error(
                    ErrorType.VALIDATION,
                    f"주문 검증 실패: {message}",
                    context={'account': account, 'code': code, 'quantity': quantity, 'price': price, 'order_type': order_type},
                    error_level=ErrorLevel.WARNING
                )
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
                
                # 성공 기록
                execution_time = time.time() - start_time
                record_order_execution(
                    order_type=order_type,
                    symbol=code,
                    quantity=quantity,
                    price=price,
                    execution_time=execution_time,
                    success=True,
                    order_id=str(order_no)
                )
                
                logger.info(f"주문 전송 성공: {code} - {order_type} - {quantity}주 - {price:,}원 (주문번호: {order_no})")
                return order_no
            else:
                # 실패 기록
                execution_time = time.time() - start_time
                record_order_execution(
                    order_type=order_type,
                    symbol=code,
                    quantity=quantity,
                    price=price,
                    execution_time=execution_time,
                    success=False,
                    error_message=f"주문 전송 실패: {order_no}"
                )
                
                handle_error(
                    ErrorType.API,
                    f"주문 전송 실패: {order_no}",
                    context={'account': account, 'code': code, 'quantity': quantity, 'price': price, 'order_type': order_type},
                    error_level=ErrorLevel.ERROR
                )
                
                # 재시도 로직
                if retry_count < self.max_retry_count:
                    logger.info(f"주문 재시도 중... ({retry_count + 1}/{self.max_retry_count})")
                    time.sleep(1)  # 1초 대기
                    return self.order_stock(account, code, quantity, price, order_type, retry_count + 1)
                else:
                    handle_error(
                        ErrorType.API,
                        "주문 최대 재시도 횟수 초과",
                        context={'account': account, 'code': code, 'retry_count': retry_count},
                        error_level=ErrorLevel.ERROR
                    )
                    return None
                
        except Exception as e:
            # 실패 기록
            execution_time = time.time() - start_time
            record_order_execution(
                order_type=order_type,
                symbol=code,
                quantity=quantity,
                price=price,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            
            handle_error(
                ErrorType.API,
                f"주문 전송 오류: {e}",
                exception=e,
                context={'account': account, 'code': code, 'quantity': quantity, 'price': price, 'order_type': order_type},
                error_level=ErrorLevel.ERROR
            )
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

    def _perform_health_check(self):
        """헬스 체크 수행"""
        try:
            # 로그인 상태 확인
            if not self.login_status:
                handle_error(
                    ErrorType.SYSTEM,
                    "로그인 상태 비정상",
                    error_level=ErrorLevel.WARNING
                )
                return False
            
            # API 연결 상태 확인
            try:
                # 간단한 API 호출로 연결 상태 확인
                test_result = self.dynamicCall("GetLoginInfo(QString)", "USER_ID")
                if not test_result:
                    handle_error(
                        ErrorType.SYSTEM,
                        "API 연결 상태 비정상",
                        error_level=ErrorLevel.WARNING
                    )
                    return False
            except Exception as e:
                handle_error(
                    ErrorType.SYSTEM,
                    f"API 연결 확인 실패: {e}",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return False
            
            # 에러 통계 확인
            if self.error_stats['consecutive_errors'] >= self.stability_config['max_consecutive_errors']:
                handle_error(
                    ErrorType.SYSTEM,
                    f"연속 에러 발생: {self.error_stats['consecutive_errors']}회",
                    context=self.error_stats,
                    error_level=ErrorLevel.WARNING
                )
                
                # 자동 복구 시도
                if self.stability_config['auto_recovery_enabled']:
                    self._attempt_recovery()
            
            logger.debug("헬스 체크 완료 - 정상")
            return True
            
        except Exception as e:
            handle_error(
                ErrorType.SYSTEM,
                f"헬스 체크 오류: {e}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            return False
    
    def _attempt_recovery(self):
        """복구 시도"""
        try:
            logger.info("시스템 복구 시도 중...")
            
            # 에러 통계 리셋
            self.error_stats['consecutive_errors'] = 0
            self.error_stats['recovery_attempts'] += 1
            
            # 캐시 정리
            self.clear_real_data_cache()
            
            # 재연결 시도
            if not self.login_status:
                logger.info("재로그인 시도 중...")
                self.login()
            
            logger.info("시스템 복구 완료")
            
        except Exception as e:
            handle_error(
                ErrorType.SYSTEM,
                f"복구 시도 실패: {e}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )

    def get_error_stats(self):
        """에러 통계 조회"""
        return self.error_stats.copy()
    
    def get_stability_config(self):
        """안정성 설정 조회"""
        return self.stability_config.copy()
    
    def update_stability_config(self, **kwargs):
        """안정성 설정 업데이트"""
        for key, value in kwargs.items():
            if key in self.stability_config:
                self.stability_config[key] = value
                logger.info(f"안정성 설정 변경: {key} = {value}") 