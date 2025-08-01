"""
키움 API 에러 처리 및 안정성 모듈
키움 Open API+ 사용 시 발생할 수 있는 다양한 에러를 처리하고 시스템 안정성을 보장합니다.
"""

import sys
import time
import threading
import traceback
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from functools import wraps
from loguru import logger
import json
import os

class ErrorType(Enum):
    """에러 타입 정의"""
    API = "API_에러"
    NETWORK = "네트워크_에러"
    DATA = "데이터_에러"
    ORDER = "주문_에러"
    LOGIN = "로그인_에러"
    TIMEOUT = "타임아웃_에러"
    VALIDATION = "검증_에러"
    SYSTEM = "시스템_에러"
    UNKNOWN = "알수없는_에러"

class ErrorLevel(Enum):
    """에러 레벨 정의"""
    INFO = "정보"
    WARNING = "경고"
    ERROR = "에러"
    CRITICAL = "치명적"

class ErrorHandler:
    """에러 처리 및 모니터링 클래스"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.recovery_attempts = defaultdict(int)
        self.max_recovery_attempts = 3
        self.error_callbacks = {}
        self.alert_callbacks = {}
        
        # 에러 통계
        self.stats = {
            'total_errors': 0,
            'critical_errors': 0,
            'recovered_errors': 0,
            'last_error_time': None,
            'error_rate': 0.0
        }
        
        # 에러 패턴 분석
        self.error_patterns = defaultdict(list)
        
        # 로그 파일 설정
        self.setup_error_logging()
    
    def setup_error_logging(self):
        """에러 로깅 설정"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 에러 전용 로그 파일
        logger.add(
            f"{log_dir}/errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="ERROR",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # 크리티컬 에러 전용 로그 파일
        logger.add(
            f"{log_dir}/critical_errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="CRITICAL",
            rotation="1 day",
            retention="90 days",
            compression="zip"
        )

def handle_error(error_type, message, exception=None, error_level=ErrorLevel.ERROR, 
                context=None, retry_count=0, max_retries=3):
    """
    에러 처리 메인 함수
    
    Args:
        error_type (ErrorType): 에러 타입
        message (str): 에러 메시지
        exception (Exception): 발생한 예외 객체
        error_level (ErrorLevel): 에러 레벨
        context (dict): 추가 컨텍스트 정보
        retry_count (int): 현재 재시도 횟수
        max_retries (int): 최대 재시도 횟수
    """
    error_info = {
        'timestamp': datetime.now(),
        'error_type': error_type,
        'message': message,
        'error_level': error_level,
        'exception': str(exception) if exception else None,
        'traceback': traceback.format_exc() if exception else None,
        'context': context or {},
        'retry_count': retry_count,
        'max_retries': max_retries
    }
    
    # 에러 히스토리에 추가
    _error_handler.error_history.append(error_info)
    
    # 에러 카운트 증가
    _error_handler.error_counts[error_type.value] += 1
    _error_handler.stats['total_errors'] += 1
    
    if error_level == ErrorLevel.CRITICAL:
        _error_handler.stats['critical_errors'] += 1
    
    # 로그 기록
    log_message = f"[{error_type.value}] {message}"
    if exception:
        log_message += f" - Exception: {str(exception)}"
    
    if error_level == ErrorLevel.CRITICAL:
        logger.critical(log_message)
    elif error_level == ErrorLevel.ERROR:
        logger.error(log_message)
    elif error_level == ErrorLevel.WARNING:
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    # 에러 패턴 분석
    _analyze_error_pattern(error_info)
    
    # 에러 콜백 실행
    if error_type.value in _error_handler.error_callbacks:
        try:
            _error_handler.error_callbacks[error_type.value](error_info)
        except Exception as e:
            logger.error(f"에러 콜백 실행 실패: {e}")
    
    # 크리티컬 에러 알림
    if error_level == ErrorLevel.CRITICAL:
        _send_critical_alert(error_info)
    
    # 자동 복구 시도 (테스트 환경에서는 비활성화)
    if retry_count < max_retries and not os.environ.get('DISABLE_AUTO_RECOVERY'):
        return _attempt_auto_recovery(error_info)
    
    return False

def retry_operation(operation, max_retries=3, delay=1.0, backoff_factor=2.0,
                   error_types=None, on_retry=None, on_failure=None):
    """
    작업 재시도 데코레이터
    
    Args:
        operation: 재시도할 함수
        max_retries (int): 최대 재시도 횟수
        delay (float): 초기 지연 시간 (초)
        backoff_factor (float): 지연 시간 증가 배수
        error_types (list): 재시도할 에러 타입 리스트
        on_retry (callable): 재시도 시 실행할 콜백
        on_failure (callable): 최종 실패 시 실행할 콜백
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 에러 타입 체크
                    if error_types and not any(et in str(e) for et in error_types):
                        raise e
                    
                    if attempt < max_retries:
                        # 재시도 콜백 실행
                        if on_retry:
                            try:
                                on_retry(attempt, e, current_delay)
                            except Exception as callback_e:
                                logger.error(f"재시도 콜백 실행 실패: {callback_e}")
                        
                        # 지연 후 재시도
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # 최종 실패 콜백 실행
                        if on_failure:
                            try:
                                on_failure(e)
                            except Exception as callback_e:
                                logger.error(f"실패 콜백 실행 실패: {callback_e}")
                        
                        raise e
            
            return None
        return wrapper
    return decorator

def error_handler(error_type, error_level=ErrorLevel.ERROR, max_retries=3):
    """
    에러 처리 데코레이터
    
    Args:
        error_type (ErrorType): 에러 타입
        error_level (ErrorLevel): 에러 레벨
        max_retries (int): 최대 재시도 횟수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(
                    error_type=error_type,
                    message=f"함수 {func.__name__} 실행 중 에러 발생",
                    exception=e,
                    error_level=error_level,
                    context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                )
                raise
        return wrapper
    return decorator

def _analyze_error_pattern(error_info):
    """에러 패턴 분석"""
    pattern_key = f"{error_info['error_type'].value}_{error_info['error_level'].value}"
    _error_handler.error_patterns[pattern_key].append(error_info['timestamp'])
    
    # 최근 1시간 내 에러 패턴 분석
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_errors = [ts for ts in _error_handler.error_patterns[pattern_key] 
                    if ts > one_hour_ago]
    
    # 에러율 계산
    if len(recent_errors) > 10:  # 1시간 내 10회 이상 에러 발생 시
        _error_handler.stats['error_rate'] = len(recent_errors) / 60.0  # 분당 에러율
        
        if _error_handler.stats['error_rate'] > 0.5:  # 분당 0.5회 이상
            logger.warning(f"높은 에러율 감지: {pattern_key} - 분당 {_error_handler.stats['error_rate']:.2f}회")

def _attempt_auto_recovery(error_info):
    """자동 복구 시도"""
    error_type = error_info['error_type']
    recovery_key = f"{error_type.value}_{error_info['error_level'].value}"
    
    if _error_handler.recovery_attempts[recovery_key] < _error_handler.max_recovery_attempts:
        _error_handler.recovery_attempts[recovery_key] += 1
        
        logger.info(f"자동 복구 시도 {_error_handler.recovery_attempts[recovery_key]}/{_error_handler.max_recovery_attempts}")
        
        # 에러 타입별 복구 전략
        if error_type == ErrorType.NETWORK:
            return _recover_network_error(error_info)
        elif error_type == ErrorType.LOGIN:
            return _recover_login_error(error_info)
        elif error_type == ErrorType.API:
            return _recover_api_error(error_info)
        elif error_type == ErrorType.TIMEOUT:
            return _recover_timeout_error(error_info)
    
    return False

def _recover_network_error(error_info):
    """네트워크 에러 복구"""
    logger.info("네트워크 에러 복구 시도 중...")
    time.sleep(2)  # 잠시 대기
    return True

def _recover_login_error(error_info):
    """로그인 에러 복구"""
    logger.info("로그인 에러 복구 시도 중...")
    # 로그인 재시도 로직
    return True

def _recover_api_error(error_info):
    """API 에러 복구"""
    logger.info("API 에러 복구 시도 중...")
    time.sleep(1)
    return True

def _recover_timeout_error(error_info):
    """타임아웃 에러 복구"""
    logger.info("타임아웃 에러 복구 시도 중...")
    time.sleep(3)  # 더 긴 대기 시간
    return True

def _send_critical_alert(error_info):
    """크리티컬 에러 알림 전송"""
    alert_message = f"크리티컬 에러 발생!\n타입: {error_info['error_type'].value}\n메시지: {error_info['message']}\n시간: {error_info['timestamp']}"
    
    logger.critical(alert_message)
    
    # 알림 콜백 실행
    for callback in _error_handler.alert_callbacks.values():
        try:
            callback(alert_message, error_info)
        except Exception as e:
            logger.error(f"알림 콜백 실행 실패: {e}")

def get_error_stats():
    """에러 통계 반환"""
    return {
        'total_errors': _error_handler.stats['total_errors'],
        'critical_errors': _error_handler.stats['critical_errors'],
        'recovered_errors': _error_handler.stats['recovered_errors'],
        'error_rate': _error_handler.stats['error_rate'],
        'error_counts': dict(_error_handler.error_counts),
        'recovery_attempts': dict(_error_handler.recovery_attempts),
        'last_error_time': _error_handler.stats['last_error_time']
    }

def add_error_callback(error_type, callback):
    """에러 콜백 추가"""
    _error_handler.error_callbacks[error_type.value] = callback

def add_alert_callback(name, callback):
    """알림 콜백 추가"""
    _error_handler.alert_callbacks[name] = callback

def clear_error_history():
    """에러 히스토리 초기화"""
    _error_handler.error_history.clear()
    _error_handler.error_counts.clear()
    _error_handler.recovery_attempts.clear()
    _error_handler.stats = {
        'total_errors': 0,
        'critical_errors': 0,
        'recovered_errors': 0,
        'last_error_time': None,
        'error_rate': 0.0
    }

# 전역 에러 핸들러 인스턴스
_error_handler = ErrorHandler() 