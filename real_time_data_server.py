#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 데이터 수집 API 서버
Flask 기반 실시간 데이터 제공 서버
"""

import sys
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from loguru import logger
import pandas as pd

# 프로젝트 모듈 import
from real_time_data_collector import (
    RealTimeDataCollector, 
    RealTimeDataAnalyzer, 
    DataCollectionConfig,
    RealTimeData
)
from error_handler import ErrorType, ErrorLevel, handle_error
from system_monitor import system_monitor

class RealTimeDataServer:
    """실시간 데이터 API 서버"""
    
    def __init__(self, port: int = 8083):
        self.port = port
        self.app = Flask(__name__)
        self.app.config['JSON_AS_ASCII'] = False
        CORS(self.app)
        
        # 데이터 수집기 초기화
        self.collector = None
        self.analyzer = None
        self.collector_thread = None
        
        # 서버 상태
        self.server_running = False
        
        # 라우트 설정
        self._setup_routes()
        
        # 초기화
        self._initialize_collector()
        
    def _initialize_collector(self):
        """데이터 수집기 초기화"""
        try:
            # 설정
            config = DataCollectionConfig(
                update_interval=1.0,
                max_queue_size=10000,
                cache_duration=300,
                enable_monitoring=True
            )
            
            # 수집기 및 분석기 초기화
            self.collector = RealTimeDataCollector(config)
            self.analyzer = RealTimeDataAnalyzer(self.collector)
            
            # 데이터 처리 콜백 등록
            self.collector.add_callback('data_processed', self._on_data_processed)
            
            logger.info("실시간 데이터 수집기 초기화 완료")
            
        except Exception as e:
            handle_error(
                ErrorType.INITIALIZATION,
                "실시간 데이터 수집기 초기화 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
    
    def _setup_routes(self):
        """API 라우트 설정"""
        
        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('real_time_dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """서버 상태 조회"""
            try:
                collector_stats = self.collector.get_stats() if self.collector else {}
                
                return jsonify({
                    'server_running': self.server_running,
                    'collector_running': self.collector.running if self.collector else False,
                    'collector_stats': collector_stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "서버 상태 조회 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/start')
        def start_collector():
            """데이터 수집 시작"""
            try:
                if not self.collector.running:
                    self.collector.start()
                    self.server_running = True
                    logger.info("실시간 데이터 수집 시작")
                    return jsonify({'status': 'started', 'message': '데이터 수집이 시작되었습니다'})
                else:
                    return jsonify({'status': 'already_running', 'message': '이미 실행 중입니다'})
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "데이터 수집 시작 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop')
        def stop_collector():
            """데이터 수집 중지"""
            try:
                if self.collector.running:
                    self.collector.stop()
                    self.server_running = False
                    logger.info("실시간 데이터 수집 중지")
                    return jsonify({'status': 'stopped', 'message': '데이터 수집이 중지되었습니다'})
                else:
                    return jsonify({'status': 'not_running', 'message': '실행 중이 아닙니다'})
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "데이터 수집 중지 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/subscribe', methods=['POST'])
        def subscribe_stocks():
            """종목 구독"""
            try:
                data = request.get_json()
                codes = data.get('codes', [])
                
                if not codes:
                    return jsonify({'error': '종목 코드가 필요합니다'}), 400
                
                self.collector.subscribe(codes)
                
                return jsonify({
                    'status': 'subscribed',
                    'message': f'{len(codes)}개 종목 구독 완료',
                    'codes': codes
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "종목 구독 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/unsubscribe', methods=['POST'])
        def unsubscribe_stocks():
            """종목 구독 해제"""
            try:
                data = request.get_json()
                codes = data.get('codes', [])
                
                if not codes:
                    return jsonify({'error': '종목 코드가 필요합니다'}), 400
                
                self.collector.unsubscribe(codes)
                
                return jsonify({
                    'status': 'unsubscribed',
                    'message': f'{len(codes)}개 종목 구독 해제 완료',
                    'codes': codes
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "종목 구독 해제 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data')
        def get_all_data():
            """모든 실시간 데이터 조회"""
            try:
                all_data = self.collector.get_all_data()
                
                # JSON 직렬화 가능한 형태로 변환
                data_list = []
                for code, data in all_data.items():
                    data_dict = {
                        'code': data.code,
                        'name': data.name,
                        'current_price': data.current_price,
                        'change_rate': data.change_rate,
                        'volume': data.volume,
                        'amount': data.amount,
                        'open_price': data.open_price,
                        'high_price': data.high_price,
                        'low_price': data.low_price,
                        'prev_close': data.prev_close,
                        'timestamp': data.timestamp.isoformat(),
                        'data_type': data.data_type
                    }
                    data_list.append(data_dict)
                
                return jsonify({
                    'data': data_list,
                    'count': len(data_list),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "실시간 데이터 조회 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data/<code>')
        def get_stock_data(code):
            """특정 종목 데이터 조회"""
            try:
                data = self.collector.get_data(code)
                
                if not data:
                    return jsonify({'error': '데이터가 없습니다'}), 404
                
                data_dict = {
                    'code': data.code,
                    'name': data.name,
                    'current_price': data.current_price,
                    'change_rate': data.change_rate,
                    'volume': data.volume,
                    'amount': data.amount,
                    'open_price': data.open_price,
                    'high_price': data.high_price,
                    'low_price': data.low_price,
                    'prev_close': data.prev_close,
                    'timestamp': data.timestamp.isoformat(),
                    'data_type': data.data_type
                }
                
                return jsonify(data_dict)
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    f"종목 데이터 조회 오류: {code}",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analysis/market-trend')
        def get_market_trend():
            """시장 추세 분석"""
            try:
                trend_data = self.analyzer.analyze_market_trend()
                return jsonify({
                    'analysis': trend_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "시장 추세 분석 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analysis/hot-stocks')
        def get_hot_stocks():
            """급등/급락 종목 조회"""
            try:
                min_change_rate = request.args.get('min_change_rate', 3.0, type=float)
                hot_stocks = self.analyzer.find_hot_stocks(min_change_rate)
                
                return jsonify({
                    'hot_stocks': hot_stocks,
                    'count': len(hot_stocks),
                    'min_change_rate': min_change_rate,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "급등/급락 종목 분석 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analysis/correlation')
        def get_correlation():
            """종목 간 상관관계 분석"""
            try:
                codes = request.args.get('codes', '').split(',')
                if not codes or codes == ['']:
                    return jsonify({'error': '종목 코드가 필요합니다'}), 400
                
                correlation = self.analyzer.calculate_correlation(codes)
                
                return jsonify({
                    'correlation': correlation,
                    'codes': codes,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "상관관계 분석 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export')
        def export_data():
            """데이터 내보내기"""
            try:
                format_type = request.args.get('format', 'csv')
                filename = f"real_time_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
                
                self.collector.export_data(filename, format_type)
                
                return jsonify({
                    'status': 'exported',
                    'filename': filename,
                    'format': format_type,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "데이터 내보내기 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """상세 통계 조회"""
            try:
                collector_stats = self.collector.get_stats()
                
                return jsonify({
                    'collector_stats': collector_stats,
                    'server_stats': {
                        'server_running': self.server_running,
                        'uptime': self._get_uptime(),
                        'timestamp': datetime.now().isoformat()
                    }
                })
            except Exception as e:
                handle_error(
                    ErrorType.API,
                    "통계 조회 오류",
                    exception=e,
                    error_level=ErrorLevel.ERROR
                )
                return jsonify({'error': str(e)}), 500
    
    def _on_data_processed(self, data: RealTimeData, processed_data: Dict):
        """데이터 처리 콜백"""
        try:
            # 여기서 추가 처리 가능 (웹소켓, 알림 등)
            pass
        except Exception as e:
            logger.error(f"데이터 처리 콜백 오류: {e}")
    
    def _get_uptime(self) -> str:
        """서버 가동 시간 계산"""
        if not self.collector or not self.collector.stats.get('start_time'):
            return "0:00:00"
        
        start_time = self.collector.stats['start_time']
        uptime = datetime.now() - start_time
        return str(uptime).split('.')[0]
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"실시간 데이터 API 서버 시작: http://localhost:{self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
        except Exception as e:
            handle_error(
                ErrorType.INITIALIZATION,
                "실시간 데이터 API 서버 시작 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
    
    def stop(self):
        """서버 중지"""
        try:
            if self.collector and self.collector.running:
                self.collector.stop()
            logger.info("실시간 데이터 API 서버 중지")
        except Exception as e:
            logger.error(f"서버 중지 오류: {e}")

def main():
    """메인 함수"""
    try:
        # 서버 초기화
        server = RealTimeDataServer(port=8083)
        
        # 기본 종목 구독 (테스트용)
        test_codes = ['005930', '000660', '035420', '051910', '006400']
        server.collector.subscribe(test_codes)
        
        # 서버 시작
        server.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ 서버 중지")
        server.stop()
    except Exception as e:
        logger.error(f"서버 실행 오류: {e}")
        server.stop()

if __name__ == "__main__":
    main() 