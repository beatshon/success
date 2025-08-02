#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 실시간 데이터 수집 시스템
키움 API 기반 실시간 데이터 수집 및 처리 시스템
"""

import sys
import time
import threading
import queue
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from loguru import logger

# 프로젝트 모듈 import
from kiwoom_api import KiwoomAPI, RealDataType
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation
from system_monitor import system_monitor, record_api_call, record_data_processed
from config import KIWOOM_CONFIG

@dataclass
class RealTimeData:
    """실시간 데이터 구조체"""
    code: str
    name: str
    current_price: float
    change_rate: float
    volume: int
    amount: int
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    timestamp: datetime
    data_type: str
    additional_data: Dict = None

@dataclass
class DataCollectionConfig:
    """데이터 수집 설정"""
    update_interval: float = 1.0  # 초
    max_queue_size: int = 10000
    cache_duration: int = 300  # 초
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_compression: bool = True
    enable_caching: bool = True
    enable_monitoring: bool = True

class DataProcessor:
    """실시간 데이터 처리기"""
    
    def __init__(self):
        self.processors = {
            'price_alert': self._process_price_alert,
            'volume_analysis': self._process_volume_analysis,
            'trend_analysis': self._process_trend_analysis,
            'volatility_calculation': self._process_volatility_calculation
        }
        
    def process_data(self, data: RealTimeData, processors: List[str] = None) -> Dict:
        """데이터 처리"""
        if processors is None:
            processors = list(self.processors.keys())
            
        results = {}
        for processor_name in processors:
            if processor_name in self.processors:
                try:
                    results[processor_name] = self.processors[processor_name](data)
                except Exception as e:
                    handle_error(
                        ErrorType.DATA_PROCESSING,
                        f"데이터 처리 오류: {processor_name}",
                        exception=e,
                        error_level=ErrorLevel.WARNING
                    )
                    results[processor_name] = None
                    
        return results
    
    def _process_price_alert(self, data: RealTimeData) -> Dict:
        """가격 알림 처리"""
        alerts = []
        
        # 급등/급락 감지
        if abs(data.change_rate) > 5.0:
            alerts.append({
                'type': 'price_volatility',
                'message': f"{data.name} 급격한 가격 변동: {data.change_rate:+.2f}%",
                'severity': 'high' if abs(data.change_rate) > 10.0 else 'medium'
            })
            
        return {'alerts': alerts}
    
    def _process_volume_analysis(self, data: RealTimeData) -> Dict:
        """거래량 분석"""
        # 거래량 급증 감지 (임시 기준)
        volume_ratio = data.volume / max(data.amount / data.current_price, 1)
        
        return {
            'volume_ratio': volume_ratio,
            'volume_signal': 'high' if volume_ratio > 2.0 else 'normal'
        }
    
    def _process_trend_analysis(self, data: RealTimeData) -> Dict:
        """추세 분석"""
        # 간단한 추세 분석 (실제로는 이전 데이터와 비교 필요)
        trend = 'up' if data.change_rate > 0 else 'down'
        
        return {
            'trend': trend,
            'strength': abs(data.change_rate) / 10.0  # 0-1 범위
        }
    
    def _process_volatility_calculation(self, data: RealTimeData) -> Dict:
        """변동성 계산"""
        # 일일 변동성 (고가-저가)
        daily_volatility = (data.high_price - data.low_price) / data.prev_close * 100
        
        return {
            'daily_volatility': daily_volatility,
            'volatility_level': 'high' if daily_volatility > 5.0 else 'normal'
        }

class DataCache:
    """데이터 캐시 관리"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[RealTimeData]:
        """캐시에서 데이터 조회"""
        with self.lock:
            if key in self.cache:
                # TTL 확인
                if time.time() - self.timestamps[key] < self.ttl:
                    return self.cache[key]
                else:
                    # 만료된 데이터 삭제
                    del self.cache[key]
                    del self.timestamps[key]
            return None
    
    def set(self, key: str, data: RealTimeData):
        """캐시에 데이터 저장"""
        with self.lock:
            # 캐시 크기 제한 확인
            if len(self.cache) >= self.max_size:
                # 가장 오래된 데이터 삭제
                oldest_key = min(self.timestamps.keys(), key=self.timestamps.get)
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = data
            self.timestamps[key] = time.time()
    
    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> Dict:
        """캐시 통계"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': 0,  # TODO: 히트율 계산 구현
                'ttl': self.ttl
            }

class RealTimeDataCollector:
    """고도화된 실시간 데이터 수집기"""
    
    def __init__(self, config: DataCollectionConfig = None):
        self.config = config or DataCollectionConfig()
        
        # API 초기화
        self.api = None
        self.api_lock = threading.Lock()
        
        # 데이터 큐 및 캐시
        self.data_queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.cache = DataCache(max_size=1000, ttl=self.config.cache_duration)
        
        # 데이터 처리기
        self.processor = DataProcessor()
        
        # 구독 관리
        self.subscribed_codes = set()
        self.subscription_lock = threading.Lock()
        
        # 콜백 관리
        self.callbacks = defaultdict(list)
        self.callback_lock = threading.Lock()
        
        # 스레드 관리
        self.running = False
        self.collection_thread = None
        self.processing_thread = None
        self.monitoring_thread = None
        
        # 성능 모니터링
        self.stats = {
            'data_received': 0,
            'data_processed': 0,
            'errors': 0,
            'start_time': None,
            'last_update': None
        }
        
        # 초기화
        self._initialize_api()
        
    def _initialize_api(self):
        """API 초기화"""
        try:
            from PyQt5.QtWidgets import QApplication
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            self.api = KiwoomAPI()
            
            # 실시간 데이터 콜백 설정
            self.api.set_real_data_callback(self._on_real_data_received)
            
            logger.info("실시간 데이터 수집기 API 초기화 완료")
            
        except Exception as e:
            handle_error(
                ErrorType.INITIALIZATION,
                "실시간 데이터 수집기 API 초기화 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
    
    def start(self):
        """데이터 수집 시작"""
        if self.running:
            logger.warning("이미 실행 중입니다")
            return
            
        try:
            # API 로그인
            if not self.api.login(timeout=30):
                raise Exception("API 로그인 실패")
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            # 스레드 시작
            self.collection_thread = threading.Thread(target=self._collection_worker, daemon=True)
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            
            self.collection_thread.start()
            self.processing_thread.start()
            self.monitoring_thread.start()
            
            logger.info("실시간 데이터 수집 시작")
            
        except Exception as e:
            handle_error(
                ErrorType.INITIALIZATION,
                "실시간 데이터 수집 시작 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
    
    def stop(self):
        """데이터 수집 중지"""
        if not self.running:
            return
            
        self.running = False
        
        # 모든 구독 해제
        with self.subscription_lock:
            for code in list(self.subscribed_codes):
                try:
                    self.api.unsubscribe_real_data(code)
                except Exception as e:
                    logger.error(f"구독 해제 실패: {code} - {e}")
            self.subscribed_codes.clear()
        
        # 스레드 종료 대기
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("실시간 데이터 수집 중지")
    
    def subscribe(self, codes: List[str]):
        """종목 구독"""
        with self.subscription_lock:
            for code in codes:
                if code not in self.subscribed_codes:
                    try:
                        self.api.subscribe_real_data(code)
                        self.subscribed_codes.add(code)
                        logger.info(f"종목 구독: {code}")
                    except Exception as e:
                        handle_error(
                            ErrorType.API,
                            f"종목 구독 실패: {code}",
                            exception=e,
                            error_level=ErrorLevel.ERROR
                        )
    
    def unsubscribe(self, codes: List[str]):
        """종목 구독 해제"""
        with self.subscription_lock:
            for code in codes:
                if code in self.subscribed_codes:
                    try:
                        self.api.unsubscribe_real_data(code)
                        self.subscribed_codes.remove(code)
                        logger.info(f"종목 구독 해제: {code}")
                    except Exception as e:
                        handle_error(
                            ErrorType.API,
                            f"종목 구독 해제 실패: {code}",
                            exception=e,
                            error_level=ErrorLevel.ERROR
                        )
    
    def add_callback(self, callback_type: str, callback: Callable):
        """콜백 함수 등록"""
        with self.callback_lock:
            self.callbacks[callback_type].append(callback)
    
    def remove_callback(self, callback_type: str, callback: Callable):
        """콜백 함수 제거"""
        with self.callback_lock:
            if callback_type in self.callbacks:
                try:
                    self.callbacks[callback_type].remove(callback)
                except ValueError:
                    pass
    
    def _on_real_data_received(self, code: str, data: Dict):
        """실시간 데이터 수신 처리"""
        try:
            # RealTimeData 객체 생성
            real_time_data = RealTimeData(
                code=code,
                name=data.get('name', ''),
                current_price=data.get('current_price', 0),
                change_rate=data.get('change_rate', 0),
                volume=data.get('volume', 0),
                amount=data.get('amount', 0),
                open_price=data.get('open_price', 0),
                high_price=data.get('high_price', 0),
                low_price=data.get('low_price', 0),
                prev_close=data.get('prev_close', 0),
                timestamp=datetime.now(),
                data_type='stock_tick',
                additional_data=data
            )
            
            # 캐시에 저장
            if self.config.enable_caching:
                self.cache.set(code, real_time_data)
            
            # 큐에 추가
            try:
                self.data_queue.put_nowait(real_time_data)
                self.stats['data_received'] += 1
                self.stats['last_update'] = datetime.now()
            except queue.Full:
                logger.warning("데이터 큐가 가득 찼습니다")
                
        except Exception as e:
            handle_error(
                ErrorType.DATA_PROCESSING,
                f"실시간 데이터 수신 처리 오류: {code}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            self.stats['errors'] += 1
    
    def _collection_worker(self):
        """데이터 수집 워커 스레드"""
        while self.running:
            try:
                # API 상태 확인
                if not self.api.is_connected():
                    logger.warning("API 연결이 끊어졌습니다. 재연결 시도...")
                    self._reconnect_api()
                
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "데이터 수집 워커 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                time.sleep(5)
    
    def _processing_worker(self):
        """데이터 처리 워커 스레드"""
        while self.running:
            try:
                # 큐에서 데이터 가져오기
                try:
                    data = self.data_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 데이터 처리
                processed_data = self.processor.process_data(data)
                
                # 콜백 호출
                with self.callback_lock:
                    for callback in self.callbacks.get('data_processed', []):
                        try:
                            callback(data, processed_data)
                        except Exception as e:
                            logger.error(f"콜백 실행 오류: {e}")
                
                self.stats['data_processed'] += 1
                
            except Exception as e:
                handle_error(
                    ErrorType.DATA_PROCESSING,
                    "데이터 처리 워커 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                self.stats['errors'] += 1
    
    def _monitoring_worker(self):
        """모니터링 워커 스레드"""
        while self.running:
            try:
                # 성능 통계 기록
                if self.config.enable_monitoring:
                    record_data_processed(
                        data_count=self.stats['data_processed'],
                        error_count=self.stats['errors']
                    )
                
                # 통계 로깅
                if self.stats['data_processed'] % 100 == 0:
                    logger.info(f"데이터 처리 통계: 수신={self.stats['data_received']}, "
                              f"처리={self.stats['data_processed']}, 오류={self.stats['errors']}")
                
                time.sleep(60)  # 1분마다 모니터링
                
            except Exception as e:
                logger.error(f"모니터링 워커 오류: {e}")
                time.sleep(60)
    
    def _reconnect_api(self):
        """API 재연결"""
        try:
            with self.api_lock:
                if self.api.login(timeout=30):
                    # 구독 복원
                    with self.subscription_lock:
                        for code in self.subscribed_codes:
                            try:
                                self.api.subscribe_real_data(code)
                            except Exception as e:
                                logger.error(f"구독 복원 실패: {code} - {e}")
                    logger.info("API 재연결 성공")
                else:
                    logger.error("API 재연결 실패")
        except Exception as e:
            logger.error(f"API 재연결 오류: {e}")
    
    def get_data(self, code: str) -> Optional[RealTimeData]:
        """특정 종목의 최신 데이터 조회"""
        return self.cache.get(code)
    
    def get_all_data(self) -> Dict[str, RealTimeData]:
        """모든 종목의 최신 데이터 조회"""
        return self.cache.cache.copy()
    
    def get_stats(self) -> Dict:
        """수집기 통계 조회"""
        stats = self.stats.copy()
        stats.update({
            'subscribed_count': len(self.subscribed_codes),
            'queue_size': self.data_queue.qsize(),
            'cache_stats': self.cache.get_stats(),
            'running': self.running
        })
        return stats
    
    def export_data(self, filename: str, format: str = 'csv'):
        """데이터 내보내기"""
        try:
            all_data = self.get_all_data()
            if not all_data:
                logger.warning("내보낼 데이터가 없습니다")
                return
            
            data_list = []
            for code, data in all_data.items():
                data_dict = asdict(data)
                data_dict['timestamp'] = data.timestamp.isoformat()
                data_list.append(data_dict)
            
            df = pd.DataFrame(data_list)
            
            if format.lower() == 'csv':
                df.to_csv(filename, index=False, encoding='utf-8-sig')
            elif format.lower() == 'json':
                df.to_json(filename, orient='records', force_ascii=False, indent=2)
            else:
                raise ValueError(f"지원하지 않는 형식: {format}")
            
            logger.info(f"데이터 내보내기 완료: {filename}")
            
        except Exception as e:
            handle_error(
                ErrorType.DATA_EXPORT,
                f"데이터 내보내기 실패: {filename}",
                exception=e,
                error_level=ErrorLevel.ERROR
            )

class RealTimeDataAnalyzer:
    """실시간 데이터 분석기"""
    
    def __init__(self, collector: RealTimeDataCollector):
        self.collector = collector
        self.analysis_results = {}
        self.analysis_lock = threading.Lock()
        
    def analyze_market_trend(self) -> Dict:
        """시장 전체 추세 분석"""
        try:
            all_data = self.collector.get_all_data()
            if not all_data:
                return {}
            
            # 상승/하락 종목 수 계산
            up_count = sum(1 for data in all_data.values() if data.change_rate > 0)
            down_count = sum(1 for data in all_data.values() if data.change_rate < 0)
            flat_count = len(all_data) - up_count - down_count
            
            # 평균 등락률
            avg_change_rate = np.mean([data.change_rate for data in all_data.values()])
            
            # 거래량 분석
            total_volume = sum(data.volume for data in all_data.values())
            avg_volume = total_volume / len(all_data) if all_data else 0
            
            return {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'avg_change_rate': avg_change_rate,
                'total_volume': total_volume,
                'avg_volume': avg_volume,
                'market_sentiment': 'bullish' if avg_change_rate > 0.5 else 'bearish' if avg_change_rate < -0.5 else 'neutral'
            }
            
        except Exception as e:
            handle_error(
                ErrorType.DATA_ANALYSIS,
                "시장 추세 분석 오류",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            return {}
    
    def find_hot_stocks(self, min_change_rate: float = 3.0) -> List[Dict]:
        """급등/급락 종목 찾기"""
        try:
            all_data = self.collector.get_all_data()
            hot_stocks = []
            
            for code, data in all_data.items():
                if abs(data.change_rate) >= min_change_rate:
                    hot_stocks.append({
                        'code': code,
                        'name': data.name,
                        'change_rate': data.change_rate,
                        'current_price': data.current_price,
                        'volume': data.volume,
                        'type': 'up' if data.change_rate > 0 else 'down'
                    })
            
            # 등락률 기준 정렬
            hot_stocks.sort(key=lambda x: abs(x['change_rate']), reverse=True)
            
            return hot_stocks
            
        except Exception as e:
            handle_error(
                ErrorType.DATA_ANALYSIS,
                "급등/급락 종목 분석 오류",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            return []
    
    def calculate_correlation(self, codes: List[str]) -> Dict:
        """종목 간 상관관계 계산"""
        try:
            all_data = self.collector.get_all_data()
            available_codes = [code for code in codes if code in all_data]
            
            if len(available_codes) < 2:
                return {}
            
            # 등락률 데이터 추출
            change_rates = {}
            for code in available_codes:
                change_rates[code] = all_data[code].change_rate
            
            # 상관관계 계산
            correlation_matrix = {}
            for i, code1 in enumerate(available_codes):
                correlation_matrix[code1] = {}
                for code2 in available_codes:
                    if code1 == code2:
                        correlation_matrix[code1][code2] = 1.0
                    else:
                        # 간단한 상관관계 계산 (실제로는 시계열 데이터 필요)
                        correlation_matrix[code1][code2] = 0.0
            
            return correlation_matrix
            
        except Exception as e:
            handle_error(
                ErrorType.DATA_ANALYSIS,
                "상관관계 계산 오류",
                exception=e,
                error_level=ErrorLevel.ERROR
            )
            return {}

def main():
    """메인 함수 - 테스트용"""
    try:
        # 설정
        config = DataCollectionConfig(
            update_interval=1.0,
            max_queue_size=5000,
            cache_duration=300,
            enable_monitoring=True
        )
        
        # 수집기 초기화
        collector = RealTimeDataCollector(config)
        
        # 분석기 초기화
        analyzer = RealTimeDataAnalyzer(collector)
        
        # 콜백 등록
        def on_data_processed(data, processed_data):
            print(f"📊 {data.code} - {data.current_price:,}원 ({data.change_rate:+.2f}%)")
        
        collector.add_callback('data_processed', on_data_processed)
        
        # 테스트 종목 구독
        test_codes = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
        collector.subscribe(test_codes)
        
        # 수집 시작
        collector.start()
        
        print("실시간 데이터 수집 시작...")
        print("Ctrl+C로 중단")
        
        # 30초간 실행
        time.sleep(30)
        
        # 통계 출력
        stats = collector.get_stats()
        print(f"\n📈 수집 통계:")
        print(f"   수신 데이터: {stats['data_received']}")
        print(f"   처리 데이터: {stats['data_processed']}")
        print(f"   오류: {stats['errors']}")
        
        # 시장 분석
        market_trend = analyzer.analyze_market_trend()
        print(f"\n📊 시장 분석:")
        print(f"   상승: {market_trend.get('up_count', 0)}개")
        print(f"   하락: {market_trend.get('down_count', 0)}개")
        print(f"   평균 등락률: {market_trend.get('avg_change_rate', 0):+.2f}%")
        
        # 급등/급락 종목
        hot_stocks = analyzer.find_hot_stocks(min_change_rate=2.0)
        if hot_stocks:
            print(f"\n🔥 급등/급락 종목:")
            for stock in hot_stocks[:5]:
                print(f"   {stock['code']} {stock['name']}: {stock['change_rate']:+.2f}%")
        
        # 데이터 내보내기
        collector.export_data('real_time_data_export.csv', 'csv')
        
        # 정리
        collector.stop()
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        collector.stop()
    except Exception as e:
        logger.error(f"실행 오류: {e}")
        collector.stop()

if __name__ == "__main__":
    main() 