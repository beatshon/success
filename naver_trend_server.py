#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 트렌드 분석 서버
Flask 기반 API 서버
"""

import sys
import time
import threading
import signal
import argparse
import asyncio
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from loguru import logger

# 프로젝트 모듈 import
from naver_trend_analyzer import NaverTrendAnalyzer
from error_handler import ErrorType, ErrorLevel, handle_error

class NaverTrendServer:
    """네이버 트렌드 분석 서버"""
    
    def __init__(self, port: int = 8085, client_id: str = None, client_secret: str = None):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 네이버 API 설정
        self.client_id = client_id or "YOUR_NAVER_CLIENT_ID"
        self.client_secret = client_secret or "YOUR_NAVER_CLIENT_SECRET"
        
        # 트렌드 분석기
        self.analyzer = None
        
        # 실시간 데이터 수집 상태
        self.data_collection_running = False
        self.collection_thread = None
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 라우트 설정
        self._setup_routes()
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신. 서버를 종료합니다.")
        self.stop()
        
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('naver_trend_dashboard.html')
        
        @self.app.route('/api/naver-trends')
        def get_naver_trends():
            """네이버 트렌드 데이터 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                # 트렌드 요약
                summary = self.analyzer.get_trend_summary()
                
                # 시장 감정 분석
                market_sentiment = self.analyzer.get_market_sentiment()
                
                # 트렌딩 키워드
                trending_keywords = market_sentiment.get('trending_keywords', [])
                
                return jsonify({
                    'summary': summary,
                    'market_sentiment': market_sentiment,
                    'trending_keywords': trending_keywords,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"트렌드 데이터 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stock-signals/<stock_code>')
        def get_stock_signals(stock_code):
            """특정 종목 투자 신호 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                signals = self.analyzer.get_investment_signals(stock_code)
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"투자 신호 조회 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market-sentiment')
        def get_market_sentiment():
            """시장 감정 분석 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                sentiment = self.analyzer.get_market_sentiment()
                return jsonify(sentiment)
                
            except Exception as e:
                logger.error(f"시장 감정 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/search-trend/<keyword>')
        def get_search_trend(keyword):
            """검색 트렌드 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                period = request.args.get('period', '1month')
                trend_data = self.analyzer.get_search_trend(keyword, period)
                return jsonify(trend_data)
                
            except Exception as e:
                logger.error(f"검색 트렌드 조회 실패 ({keyword}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/shopping-trend/<category>')
        def get_shopping_trend(category):
            """쇼핑 트렌드 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                trend_data = self.analyzer.get_shopping_trend(category)
                return jsonify(trend_data)
                
            except Exception as e:
                logger.error(f"쇼핑 트렌드 조회 실패 ({category}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/news-sentiment/<keyword>')
        def get_news_sentiment(keyword):
            """뉴스 감정 분석 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                sentiment = self.analyzer.get_news_sentiment(keyword)
                return jsonify({
                    'keyword': keyword,
                    'sentiment_score': sentiment,
                    'sentiment_level': self.analyzer._get_sentiment_level(sentiment),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"뉴스 감정 분석 실패 ({keyword}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/historical-data/<keyword>')
        def get_historical_data(keyword):
            """과거 트렌드 데이터 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                days = int(request.args.get('days', 30))
                historical_data = self.analyzer.get_historical_trend_data(keyword, days)
                
                # 데이터 직렬화
                serialized_data = []
                for trend in historical_data:
                    serialized_data.append({
                        'keyword': trend.keyword,
                        'trend_type': trend.trend_type.value,
                        'value': trend.value,
                        'timestamp': trend.timestamp.isoformat(),
                        'sentiment_score': trend.sentiment_score,
                        'volume_change': trend.volume_change,
                        'momentum_score': trend.momentum_score,
                        'volatility': trend.volatility
                    })
                
                return jsonify({
                    'keyword': keyword,
                    'data': serialized_data,
                    'count': len(serialized_data)
                })
                
            except Exception as e:
                logger.error(f"과거 데이터 조회 실패 ({keyword}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/correlation/<keyword>')
        def get_correlation(keyword):
            """트렌드-주식 상관관계 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                # 가상의 주식 데이터 (실제로는 주식 API에서 가져와야 함)
                stock_data = {
                    'prices': [100 + i * 0.5 + np.random.normal(0, 1) for i in range(30)]
                }
                
                correlation = self.analyzer.analyze_trend_correlation(keyword, stock_data)
                
                if correlation:
                    return jsonify({
                        'keyword': correlation.keyword,
                        'stock_code': correlation.stock_code,
                        'stock_name': correlation.stock_name,
                        'correlation_score': correlation.correlation_score,
                        'trend_direction': correlation.trend_direction,
                        'confidence_level': correlation.confidence_level,
                        'impact_score': correlation.impact_score,
                        'prediction_accuracy': correlation.prediction_accuracy,
                        'last_updated': correlation.last_updated.isoformat()
                    })
                else:
                    return jsonify({'error': '상관관계 데이터를 찾을 수 없습니다.'}), 404
                
            except Exception as e:
                logger.error(f"상관관계 분석 실패 ({keyword}): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trending-keywords')
        def get_trending_keywords():
            """트렌딩 키워드 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                trending_keywords = self.analyzer._find_trending_keywords()
                return jsonify({
                    'trending_keywords': trending_keywords,
                    'count': len(trending_keywords),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"트렌딩 키워드 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def health_check():
            """헬스 체크 API"""
            return jsonify({
                'status': 'healthy',
                'analyzer_initialized': self.analyzer is not None,
                'data_collection_running': self.data_collection_running,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/start-analysis')
        def start_analysis():
            """연속 분석 시작 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                self.analyzer.start_continuous_analysis()
                return jsonify({
                    'status': 'success',
                    'message': '연속 분석이 시작되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"연속 분석 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop-analysis')
        def stop_analysis():
            """연속 분석 중지 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                self.analyzer.stop_continuous_analysis()
                return jsonify({
                    'status': 'success',
                    'message': '연속 분석이 중지되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"연속 분석 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/start-data-collection')
        def start_data_collection():
            """실시간 데이터 수집 시작 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                if self.data_collection_running:
                    return jsonify({'error': '이미 데이터 수집이 실행 중입니다.'}), 400
                
                self.data_collection_running = True
                self.collection_thread = threading.Thread(target=self._data_collection_worker)
                self.collection_thread.daemon = True
                self.collection_thread.start()
                
                return jsonify({
                    'status': 'success',
                    'message': '실시간 데이터 수집이 시작되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"데이터 수집 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop-data-collection')
        def stop_data_collection():
            """실시간 데이터 수집 중지 API"""
            try:
                if not self.data_collection_running:
                    return jsonify({'error': '데이터 수집이 실행 중이 아닙니다.'}), 400
                
                self.data_collection_running = False
                if self.collection_thread:
                    self.collection_thread.join(timeout=5)
                
                return jsonify({
                    'status': 'success',
                    'message': '실시간 데이터 수집이 중지되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"데이터 수집 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/collect-data-now')
        def collect_data_now():
            """즉시 데이터 수집 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                # 비동기 데이터 수집 실행
                asyncio.run(self.analyzer.collect_real_time_data())
                
                return jsonify({
                    'status': 'success',
                    'message': '데이터 수집이 완료되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"즉시 데이터 수집 실패: {e}")
                return jsonify({'error': str(e)}), 500

    def _data_collection_worker(self):
        """데이터 수집 워커 스레드"""
        while self.data_collection_running:
            try:
                # 비동기 데이터 수집 실행
                asyncio.run(self.analyzer.collect_real_time_data())
                
                # 30분 대기
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"데이터 수집 워커 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기

    def initialize_analyzer(self):
        """트렌드 분석기 초기화"""
        try:
            self.analyzer = NaverTrendAnalyzer(self.client_id, self.client_secret)
            logger.info("네이버 트렌드 분석기가 초기화되었습니다.")
            
            # 연속 분석 시작
            self.analyzer.start_continuous_analysis()
            
        except Exception as e:
            logger.error(f"트렌드 분석기 초기화 실패: {e}")
            handle_error(ErrorType.INITIALIZATION_ERROR, ErrorLevel.ERROR, f"네이버 트렌드 분석기 초기화 실패: {e}")

    def start(self):
        """서버 시작"""
        try:
            # 분석기 초기화
            self.initialize_analyzer()
            
            # Flask 서버 시작
            logger.info(f"네이버 트렌드 분석 서버가 시작되었습니다: http://localhost:{self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"네이버 트렌드 서버 시작 실패: {e}")

    def stop(self):
        """서버 중지"""
        try:
            # 데이터 수집 중지
            if self.data_collection_running:
                self.data_collection_running = False
                if self.collection_thread:
                    self.collection_thread.join(timeout=5)
            
            # 분석기 중지
            if self.analyzer:
                self.analyzer.stop_continuous_analysis()
            
            logger.info("네이버 트렌드 분석 서버가 중지되었습니다.")
            
        except Exception as e:
            logger.error(f"서버 중지 실패: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='네이버 트렌드 분석 서버')
    parser.add_argument('--port', type=int, default=8085, help='서버 포트 (기본값: 8085)')
    parser.add_argument('--client-id', help='네이버 API 클라이언트 ID')
    parser.add_argument('--client-secret', help='네이버 API 클라이언트 시크릿')
    
    args = parser.parse_args()
    
    try:
        # 환경 변수에서 API 키 로드
        client_id = args.client_id or os.getenv('NAVER_CLIENT_ID', 'YOUR_NAVER_CLIENT_ID')
        client_secret = args.client_secret or os.getenv('NAVER_CLIENT_SECRET', 'YOUR_NAVER_CLIENT_SECRET')
        
        # 서버 생성 및 시작
        server = NaverTrendServer(args.port, client_id, client_secret)
        server.start()
        
    except KeyboardInterrupt:
        logger.info("서버 종료 요청됨")
    except Exception as e:
        logger.error(f"서버 실행 실패: {e}")
        handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"네이버 트렌드 서버 실행 실패: {e}")

if __name__ == "__main__":
    main() 