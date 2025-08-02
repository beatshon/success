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
                
                # 투자 신호 목록
                signals = []
                for stock_code, data in self.analyzer.trend_data.items():
                    if stock_code != 'market' and isinstance(data, dict):
                        signals.append(data)
                
                # 트렌딩 키워드 (예시 데이터)
                trending_keywords = [
                    {'name': '삼성전자', 'change': 15.2, 'trend': 'up'},
                    {'name': '전기차', 'change': 8.7, 'trend': 'up'},
                    {'name': 'AI', 'change': 12.3, 'trend': 'up'},
                    {'name': '부동산', 'change': -5.1, 'trend': 'down'},
                    {'name': '금리', 'change': -3.2, 'trend': 'down'}
                ]
                
                return jsonify({
                    'summary': summary,
                    'signals': signals,
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
                if signals:
                    return jsonify(signals)
                else:
                    return jsonify({'error': '해당 종목의 신호를 찾을 수 없습니다.'}), 404
                    
            except Exception as e:
                logger.error(f"종목 신호 조회 실패: {stock_code} - {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market-sentiment')
        def get_market_sentiment():
            """시장 감정 분석 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                sentiment = self.analyzer.get_market_sentiment()
                if sentiment:
                    return jsonify(sentiment)
                else:
                    return jsonify({'error': '시장 감정 데이터를 가져올 수 없습니다.'}), 500
                    
            except Exception as e:
                logger.error(f"시장 감정 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/search-trend/<keyword>')
        def get_search_trend(keyword):
            """검색 트렌드 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                trend = self.analyzer.get_search_trend(keyword)
                if trend:
                    return jsonify(trend)
                else:
                    return jsonify({'error': '검색 트렌드 데이터를 가져올 수 없습니다.'}), 500
                    
            except Exception as e:
                logger.error(f"검색 트렌드 조회 실패: {keyword} - {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/shopping-trend/<category>')
        def get_shopping_trend(category):
            """쇼핑 트렌드 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                trend = self.analyzer.get_shopping_trend(category)
                if trend:
                    return jsonify(trend)
                else:
                    return jsonify({'error': '쇼핑 트렌드 데이터를 가져올 수 없습니다.'}), 500
                    
            except Exception as e:
                logger.error(f"쇼핑 트렌드 조회 실패: {category} - {e}")
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
                logger.error(f"뉴스 감정 분석 실패: {keyword} - {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'analyzer_running': self.analyzer.running if self.analyzer else False,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/start-analysis')
        def start_analysis():
            """분석 시작"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                if not self.analyzer.running:
                    self.analyzer.start_continuous_analysis()
                    return jsonify({'message': '트렌드 분석이 시작되었습니다.'})
                else:
                    return jsonify({'message': '트렌드 분석이 이미 실행 중입니다.'})
                    
            except Exception as e:
                logger.error(f"분석 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop-analysis')
        def stop_analysis():
            """분석 중지"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '트렌드 분석기가 초기화되지 않았습니다.'}), 500
                
                if self.analyzer.running:
                    self.analyzer.stop_continuous_analysis()
                    return jsonify({'message': '트렌드 분석이 중지되었습니다.'})
                else:
                    return jsonify({'message': '트렌드 분석이 실행 중이 아닙니다.'})
                    
            except Exception as e:
                logger.error(f"분석 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500
    
    def initialize_analyzer(self):
        """트렌드 분석기 초기화"""
        try:
            logger.info("네이버 트렌드 분석기 초기화 중...")
            
            self.analyzer = NaverTrendAnalyzer(self.client_id, self.client_secret)
            
            # 연속 분석 시작
            self.analyzer.start_continuous_analysis()
            
            logger.info("네이버 트렌드 분석기 초기화 완료")
            
        except Exception as e:
            logger.error(f"트렌드 분석기 초기화 실패: {e}")
            raise
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"네이버 트렌드 서버 시작: http://localhost:{self.port}")
            
            # 트렌드 분석기 초기화
            self.initialize_analyzer()
            
            # Flask 서버 시작
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            self.stop()
            raise
    
    def stop(self):
        """서버 중지"""
        try:
            if self.analyzer:
                self.analyzer.stop_continuous_analysis()
            
            logger.info("네이버 트렌드 서버 중지")
            
        except Exception as e:
            logger.error(f"서버 중지 오류: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="네이버 트렌드 분석 서버")
    parser.add_argument("--port", type=int, default=8085, 
                       help="서버 포트 (기본값: 8085)")
    parser.add_argument("--client-id", type=str, 
                       help="네이버 API 클라이언트 ID")
    parser.add_argument("--client-secret", type=str, 
                       help="네이버 API 클라이언트 시크릿")
    parser.add_argument("--config-file", type=str,
                       help="설정 파일 경로")
    
    args = parser.parse_args()
    
    try:
        # 설정 파일에서 API 키 로드 (선택사항)
        client_id = args.client_id
        client_secret = args.client_secret
        
        if args.config_file:
            import json
            with open(args.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                client_id = client_id or config.get('naver_client_id')
                client_secret = client_secret or config.get('naver_client_secret')
        
        # 서버 초기화
        server = NaverTrendServer(
            port=args.port,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # 서버 시작
        server.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        server.stop()
    except Exception as e:
        logger.error(f"서버 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 