"""
키움 API 시스템 모니터링 및 성능 추적 모듈
API 호출, 데이터 처리, 주문 실행 등의 성능을 모니터링하고 통계를 수집합니다.
"""

import time
import threading
import psutil
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from loguru import logger
import json
import statistics

@dataclass
class APICallRecord:
    """API 호출 기록"""
    timestamp: datetime
    function_name: str
    duration: float
    success: bool
    error_message: Optional[str] = None
    parameters: Optional[Dict] = None
    result_size: Optional[int] = None

@dataclass
class DataProcessRecord:
    """데이터 처리 기록"""
    timestamp: datetime
    data_type: str
    record_count: int
    processing_time: float
    memory_usage: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class OrderExecutionRecord:
    """주문 실행 기록"""
    timestamp: datetime
    order_type: str
    symbol: str
    quantity: int
    price: float
    execution_time: float
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None

class SystemMonitor:
    """시스템 모니터링 및 성능 추적 클래스"""
    
    def __init__(self, max_records=10000):
        self.max_records = max_records
        
        # API 호출 기록
        self.api_calls = deque(maxlen=max_records)
        self.api_stats = defaultdict(lambda: {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'last_call': None
        })
        
        # 데이터 처리 기록
        self.data_processing = deque(maxlen=max_records)
        self.data_stats = defaultdict(lambda: {
            'total_records': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'total_memory_usage': 0.0,
            'avg_memory_usage': 0.0,
            'success_count': 0,
            'failure_count': 0
        })
        
        # 주문 실행 기록
        self.order_executions = deque(maxlen=max_records)
        self.order_stats = defaultdict(lambda: {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0,
            'total_volume': 0,
            'total_value': 0.0
        })
        
        # 시스템 리소스 모니터링
        self.system_stats = {
            'cpu_usage': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'disk_usage': deque(maxlen=1000),
            'network_io': deque(maxlen=1000)
        }
        
        # 성능 임계값
        self.thresholds = {
            'api_call_timeout': 30.0,  # 30초
            'data_processing_timeout': 60.0,  # 60초
            'order_execution_timeout': 10.0,  # 10초
            'memory_usage_threshold': 80.0,  # 80%
            'cpu_usage_threshold': 90.0,  # 90%
            'error_rate_threshold': 0.1  # 10%
        }
        
        # 모니터링 활성화 상태
        self.monitoring_active = True
        
        # 백그라운드 모니터링 스레드
        self.monitor_thread = None
        
        # 테스트 환경에서는 백그라운드 모니터링 비활성화
        if not os.environ.get('DISABLE_BACKGROUND_MONITORING'):
            self.start_background_monitoring()
    
    def start_background_monitoring(self):
        """백그라운드 모니터링 시작"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
            self.monitor_thread.start()
            logger.info("시스템 모니터링 백그라운드 스레드 시작")
    
    def _background_monitor(self):
        """백그라운드 모니터링 루프"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_performance_thresholds()
                self._cleanup_old_records()
                time.sleep(5)  # 5초마다 체크
            except Exception as e:
                logger.error(f"백그라운드 모니터링 에러: {e}")
                time.sleep(10)
    
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_stats['cpu_usage'].append({
                'timestamp': datetime.now(),
                'value': cpu_percent
            })
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            self.system_stats['memory_usage'].append({
                'timestamp': datetime.now(),
                'value': memory.percent,
                'used': memory.used,
                'available': memory.available,
                'total': memory.total
            })
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            self.system_stats['disk_usage'].append({
                'timestamp': datetime.now(),
                'value': (disk.used / disk.total) * 100,
                'used': disk.used,
                'free': disk.free,
                'total': disk.total
            })
            
            # 네트워크 I/O
            network = psutil.net_io_counters()
            self.system_stats['network_io'].append({
                'timestamp': datetime.now(),
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            })
            
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")
    
    def _check_performance_thresholds(self):
        """성능 임계값 체크"""
        try:
            # CPU 사용률 체크
            if self.system_stats['cpu_usage']:
                latest_cpu = self.system_stats['cpu_usage'][-1]['value']
                if latest_cpu > self.thresholds['cpu_usage_threshold']:
                    logger.warning(f"높은 CPU 사용률 감지: {latest_cpu:.1f}%")
            
            # 메모리 사용률 체크
            if self.system_stats['memory_usage']:
                latest_memory = self.system_stats['memory_usage'][-1]['value']
                if latest_memory > self.thresholds['memory_usage_threshold']:
                    logger.warning(f"높은 메모리 사용률 감지: {latest_memory:.1f}%")
            
            # API 호출 성능 체크
            for func_name, stats in self.api_stats.items():
                if stats['total_calls'] > 0:
                    error_rate = stats['failed_calls'] / stats['total_calls']
                    if error_rate > self.thresholds['error_rate_threshold']:
                        logger.warning(f"높은 API 에러율 감지: {func_name} - {error_rate:.2%}")
                    
                    if stats['avg_duration'] > self.thresholds['api_call_timeout']:
                        logger.warning(f"느린 API 호출 감지: {func_name} - 평균 {stats['avg_duration']:.2f}초")
            
        except Exception as e:
            logger.error(f"성능 임계값 체크 실패: {e}")
    
    def _cleanup_old_records(self):
        """오래된 기록 정리"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # 24시간 이전 기록 삭제
        
        # API 호출 기록 정리
        self.api_calls = deque(
            [record for record in self.api_calls if record.timestamp > cutoff_time],
            maxlen=self.max_records
        )
        
        # 데이터 처리 기록 정리
        self.data_processing = deque(
            [record for record in self.data_processing if record.timestamp > cutoff_time],
            maxlen=self.max_records
        )
        
        # 주문 실행 기록 정리
        self.order_executions = deque(
            [record for record in self.order_executions if record.timestamp > cutoff_time],
            maxlen=self.max_records
        )

def record_api_call(function_name: str, duration: float, success: bool, 
                   error_message: Optional[str] = None, parameters: Optional[Dict] = None,
                   result_size: Optional[int] = None):
    """
    API 호출 기록
    
    Args:
        function_name (str): 호출된 함수명
        duration (float): 실행 시간 (초)
        success (bool): 성공 여부
        error_message (str, optional): 에러 메시지
        parameters (dict, optional): 함수 파라미터
        result_size (int, optional): 결과 크기
    """
    record = APICallRecord(
        timestamp=datetime.now(),
        function_name=function_name,
        duration=duration,
        success=success,
        error_message=error_message,
        parameters=parameters,
        result_size=result_size
    )
    
    _system_monitor.api_calls.append(record)
    
    # 통계 업데이트
    stats = _system_monitor.api_stats[function_name]
    stats['total_calls'] += 1
    stats['total_duration'] += duration
    stats['avg_duration'] = stats['total_duration'] / stats['total_calls']
    stats['min_duration'] = min(stats['min_duration'], duration)
    stats['max_duration'] = max(stats['max_duration'], duration)
    stats['last_call'] = record.timestamp
    
    if success:
        stats['successful_calls'] += 1
    else:
        stats['failed_calls'] += 1

def record_data_processed(data_type: str, record_count: int, processing_time: float,
                         memory_usage: float, success: bool, error_message: Optional[str] = None):
    """
    데이터 처리 기록
    
    Args:
        data_type (str): 데이터 타입
        record_count (int): 처리된 레코드 수
        processing_time (float): 처리 시간 (초)
        memory_usage (float): 메모리 사용량 (MB)
        success (bool): 성공 여부
        error_message (str, optional): 에러 메시지
    """
    record = DataProcessRecord(
        timestamp=datetime.now(),
        data_type=data_type,
        record_count=record_count,
        processing_time=processing_time,
        memory_usage=memory_usage,
        success=success,
        error_message=error_message
    )
    
    _system_monitor.data_processing.append(record)
    
    # 통계 업데이트
    stats = _system_monitor.data_stats[data_type]
    stats['total_records'] += record_count
    stats['total_processing_time'] += processing_time
    stats['avg_processing_time'] = stats['total_processing_time'] / len([r for r in _system_monitor.data_processing if r.data_type == data_type])
    stats['total_memory_usage'] += memory_usage
    stats['avg_memory_usage'] = stats['total_memory_usage'] / len([r for r in _system_monitor.data_processing if r.data_type == data_type])
    
    if success:
        stats['success_count'] += 1
    else:
        stats['failure_count'] += 1

def record_order_execution(order_type: str, symbol: str, quantity: int, price: float,
                          execution_time: float, success: bool, order_id: Optional[str] = None,
                          error_message: Optional[str] = None):
    """
    주문 실행 기록
    
    Args:
        order_type (str): 주문 타입
        symbol (str): 종목 코드
        quantity (int): 수량
        price (float): 가격
        execution_time (float): 실행 시간 (초)
        success (bool): 성공 여부
        order_id (str, optional): 주문 ID
        error_message (str, optional): 에러 메시지
    """
    record = OrderExecutionRecord(
        timestamp=datetime.now(),
        order_type=order_type,
        symbol=symbol,
        quantity=quantity,
        price=price,
        execution_time=execution_time,
        success=success,
        order_id=order_id,
        error_message=error_message
    )
    
    _system_monitor.order_executions.append(record)
    
    # 통계 업데이트
    stats = _system_monitor.order_stats[order_type]
    stats['total_orders'] += 1
    stats['total_execution_time'] += execution_time
    stats['avg_execution_time'] = stats['total_execution_time'] / stats['total_orders']
    stats['total_volume'] += quantity
    stats['total_value'] += quantity * price
    
    if success:
        stats['successful_orders'] += 1
    else:
        stats['failed_orders'] += 1

def system_monitor(func):
    """시스템 모니터링 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            duration = time.time() - start_time
            record_api_call(
                function_name=func.__name__,
                duration=duration,
                success=success,
                error_message=error_message,
                parameters={'args': str(args), 'kwargs': str(kwargs)}
            )
    
    return wrapper

def get_performance_stats():
    """성능 통계 반환"""
    return {
        'api_stats': dict(_system_monitor.api_stats),
        'data_stats': dict(_system_monitor.data_stats),
        'order_stats': dict(_system_monitor.order_stats),
        'system_stats': {
            'cpu_usage': list(_system_monitor.system_stats['cpu_usage'])[-10:] if _system_monitor.system_stats['cpu_usage'] else [],
            'memory_usage': list(_system_monitor.system_stats['memory_usage'])[-10:] if _system_monitor.system_stats['memory_usage'] else [],
            'disk_usage': list(_system_monitor.system_stats['disk_usage'])[-10:] if _system_monitor.system_stats['disk_usage'] else [],
            'network_io': list(_system_monitor.system_stats['network_io'])[-10:] if _system_monitor.system_stats['network_io'] else []
        },
        'thresholds': _system_monitor.thresholds
    }

def get_recent_api_calls(limit: int = 100):
    """최근 API 호출 기록 반환"""
    return list(_system_monitor.api_calls)[-limit:]

def get_recent_data_processing(limit: int = 100):
    """최근 데이터 처리 기록 반환"""
    return list(_system_monitor.data_processing)[-limit:]

def get_recent_order_executions(limit: int = 100):
    """최근 주문 실행 기록 반환"""
    return list(_system_monitor.order_executions)[-limit:]

def update_thresholds(**kwargs):
    """임계값 업데이트"""
    _system_monitor.thresholds.update(kwargs)
    logger.info(f"성능 임계값 업데이트: {kwargs}")

def export_monitoring_data(filepath: str):
    """모니터링 데이터 내보내기"""
    try:
        data = {
            'api_calls': [asdict(record) for record in _system_monitor.api_calls],
            'data_processing': [asdict(record) for record in _system_monitor.data_processing],
            'order_executions': [asdict(record) for record in _system_monitor.order_executions],
            'system_stats': {
                'cpu_usage': list(_system_monitor.system_stats['cpu_usage']),
                'memory_usage': list(_system_monitor.system_stats['memory_usage']),
                'disk_usage': list(_system_monitor.system_stats['disk_usage']),
                'network_io': list(_system_monitor.system_stats['network_io'])
            },
            'performance_stats': get_performance_stats(),
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"모니터링 데이터 내보내기 완료: {filepath}")
        
    except Exception as e:
        logger.error(f"모니터링 데이터 내보내기 실패: {e}")

def clear_monitoring_data():
    """모니터링 데이터 초기화"""
    _system_monitor.api_calls.clear()
    _system_monitor.data_processing.clear()
    _system_monitor.order_executions.clear()
    _system_monitor.api_stats.clear()
    _system_monitor.data_stats.clear()
    _system_monitor.order_stats.clear()
    
    for stat_type in _system_monitor.system_stats.values():
        stat_type.clear()
    
    logger.info("모니터링 데이터 초기화 완료")

# 전역 시스템 모니터 인스턴스
_system_monitor = SystemMonitor() 