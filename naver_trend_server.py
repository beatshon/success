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
import os
import numpy as np
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
        # 헬스 체크를 먼저 정의
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'analyzer_initialized': self.analyzer is not None,
                'data_collection_running': self.analyzer.analysis_running if self.analyzer else False,
                'timestamp': datetime.now().isoformat()
            })

        # 메인 페이지는 마지막에 정의
        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('naver_trend_dashboard.html')

        @self.app.route('/api/naver-trends', methods=['GET'])
        def get_naver_trends():
            """네이버 트렌드 데이터 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                summary = self.analyzer.get_trend_summary()
                trending_keywords = self.analyzer.get_trending_keywords()
                market_sentiment = self.analyzer.get_market_sentiment()
                
                return jsonify({
                    'summary': summary,
                    'trending_keywords': trending_keywords,
                    'market_sentiment': market_sentiment,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"네이버 트렌드 데이터 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stock-signals/<stock_code>', methods=['GET'])
        def get_stock_signals(stock_code):
            """특정 종목 투자 신호 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                signals = self.analyzer.get_investment_signals(stock_code)
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"투자 신호 조회 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-sentiment', methods=['GET'])
        def get_market_sentiment():
            """시장 감정 분석 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                sentiment = self.analyzer.get_market_sentiment()
                return jsonify(sentiment)
                
            except Exception as e:
                logger.error(f"시장 감정 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/trending-keywords', methods=['GET'])
        def get_trending_keywords():
            """트렌딩 키워드 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                trending_keywords = self.analyzer.get_trending_keywords()
                
                return jsonify({
                    'trending_keywords': trending_keywords,
                    'count': len(trending_keywords),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"트렌딩 키워드 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 시장 적응 투자 신호 API
        @self.app.route('/api/market-adaptive-signals/<stock_code>', methods=['GET'])
        def get_market_adaptive_signals(stock_code):
            """시장 적응 투자 신호 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 시장 데이터 생성
                market_data = {
                    'KOSPI': {
                        'prices': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105],
                        'volatility': 0.15
                    }
                }
                
                signals = self.analyzer.get_market_adaptive_signals(stock_code, market_data)
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"시장 적응 신호 조회 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        # 시장 상관관계 분석 API
        @self.app.route('/api/market-correlation/<stock_code>', methods=['GET'])
        def get_market_correlation(stock_code):
            """시장 상관관계 분석 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 시장 데이터 생성
                market_data = {
                    'KOSPI': {
                        'prices': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105],
                        'volatility': 0.15
                    }
                }
                
                correlation = self.analyzer.analyze_market_correlation(stock_code, market_data)
                return jsonify(correlation)
                
            except Exception as e:
                logger.error(f"시장 상관관계 분석 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        # 시장 상황 판단 API
        @self.app.route('/api/market-condition', methods=['GET'])
        def get_market_condition():
            """시장 상황 판단 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 시장 데이터 생성
                market_data = {
                    'KOSPI': {
                        'prices': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105],
                        'volatility': 0.15
                    }
                }
                
                condition = self.analyzer.determine_market_condition(market_data)
                strategy = self.analyzer.market_strategies.get(condition, {})
                
                return jsonify({
                    'condition': condition,
                    'description': self._get_market_condition_description(condition),
                    'strategy': strategy,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"시장 상황 판단 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 시장 상황별 전략 API
        @self.app.route('/api/market-strategy/<market_condition>', methods=['GET'])
        def get_market_strategy(market_condition):
            """시장 상황별 전략 API"""
            try:
                strategy = self.analyzer.market_strategies.get(market_condition, {})
                
                # 리스크 관리 및 시장 타이밍 조언 생성
                risk_management = self.analyzer._get_risk_management_advice(market_condition)
                market_timing = self.analyzer._get_market_timing_advice(market_condition)
                
                return jsonify({
                    'strategy': strategy,
                    'risk_management': risk_management,
                    'market_timing': market_timing,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"시장 전략 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 포트폴리오 추천 API
        @self.app.route('/api/portfolio-recommendation', methods=['GET'])
        def get_portfolio_recommendation():
            """포트폴리오 추천 API"""
            try:
                # 가상 시장 데이터 생성
                market_data = {
                    'KOSPI': {
                        'prices': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105],
                        'volatility': 0.15
                    }
                }
                
                recommendation = self.analyzer.get_portfolio_recommendation(market_data)
                return jsonify(recommendation)
                
            except Exception as e:
                logger.error(f"포트폴리오 추천 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 상관관계 분석 API
        @self.app.route('/api/correlation-analysis', methods=['GET'])
        def get_correlation_analysis():
            """상관관계 분석 API"""
            try:
                # 가상 시장 데이터 생성
                market_data = {
                    'KOSPI': {
                        'prices': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105],
                        'volatility': 0.15
                    }
                }
                
                # 주요 종목들의 상관관계 분석
                major_stocks = ['005930', '000660', '035420', '035720', '051910', '006400']
                detailed_analysis = []
                high_correlation_stocks = []
                low_correlation_stocks = []
                
                for stock in major_stocks:
                    correlation = self.analyzer.analyze_market_correlation(stock, market_data)
                    detailed_analysis.append({
                        'stock_code': stock,
                        'correlation': correlation['correlation'],
                        'beta': correlation['beta'],
                        'correlation_level': correlation['correlation_level'],
                        'market_sensitivity': correlation['market_sensitivity']
                    })
                    
                    if correlation['correlation_level'] == 'HIGH':
                        high_correlation_stocks.append(stock)
                    elif correlation['correlation_level'] == 'LOW':
                        low_correlation_stocks.append(stock)
                
                return jsonify({
                    'high_correlation_count': len(high_correlation_stocks),
                    'medium_correlation_count': len(major_stocks) - len(high_correlation_stocks) - len(low_correlation_stocks),
                    'low_correlation_count': len(low_correlation_stocks),
                    'high_correlation_stocks': high_correlation_stocks,
                    'low_correlation_stocks': low_correlation_stocks,
                    'detailed_analysis': detailed_analysis,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"상관관계 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 즉시 데이터 수집 API
        @self.app.route('/api/collect-data-now', methods=['GET'])
        def collect_data_now():
            """즉시 데이터 수집 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 실시간 데이터 수집 실행
                self.analyzer.collect_real_time_data()
                
                return jsonify({
                    'message': '데이터 수집이 완료되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"즉시 데이터 수집 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 분석 시작 API
        @self.app.route('/api/start-analysis', methods=['GET'])
        def start_analysis():
            """분석 시작 API"""
            try:
                self.analyzer.start_continuous_analysis()
                return jsonify({
                    'message': '연속 분석이 시작되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"분석 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500

        # 분석 중지 API
        @self.app.route('/api/stop-analysis', methods=['GET'])
        def stop_analysis():
            """분석 중지 API"""
            try:
                self.analyzer.stop_continuous_analysis()
                return jsonify({
                    'message': '연속 분석이 중지되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"분석 중지 실패: {e}")
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
            logger.info("네이버 트렌드 분석기 초기화 시작")
            self.analyzer = NaverTrendAnalyzer()
            
            # 가상 데이터 강제 생성
            if not self.analyzer.trend_data:
                self.analyzer._generate_virtual_trend_data()
                logger.info("가상 데이터 생성 완료")
            
            logger.info("네이버 트렌드 분석기 초기화 완료")
        except Exception as e:
            logger.error(f"트렌드 분석기 초기화 실패: {e}")
            raise Exception(f"네이버 트렌드 분석기 초기화 실패: {e}")

    def start(self):
        """서버 시작"""
        try:
            self.initialize_analyzer()
            self._setup_routes() # Changed from setup_routes to _setup_routes
            
            logger.info(f"네이버 트렌드 서버가 포트 {self.port}에서 시작되었습니다.")
            self.app.run(host='0.0.0.0', port=self.port, debug=True)
            
        except Exception as e:
            logger.error(f"네이버 트렌드 서버 시작 실패: {e}")
            raise Exception(f"네이버 트렌드 서버 시작 실패: {e}")

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

    def _get_market_condition_description(self, market_condition: str) -> str:
        """시장 상황 설명"""
        descriptions = {
            'BULL_MARKET': '확실한 상승장 - 적극적 투자 전략 권장',
            'BEAR_MARKET': '확실한 하락장 - 보수적 투자 전략 권장',
            'SIDEWAYS_MARKET': '횡보장 - 균형잡힌 투자 전략 권장',
            'VOLATILE_BULL_MARKET': '변동성 높은 상승장 - 신중한 적극 투자',
            'VOLATILE_BEAR_MARKET': '변동성 높은 하락장 - 매우 보수적 투자',
            'VOLATILE_SIDEWAYS_MARKET': '불안정한 횡보장 - 리스크 관리 중시'
        }
        
        return descriptions.get(market_condition, '알 수 없는 시장 상황')

def main():
    """메인 함수"""
    try:
        # 명령행 인수 파싱
        parser = argparse.ArgumentParser(description='네이버 트렌드 분석 서버')
        parser.add_argument('--port', type=int, default=8085, help='서버 포트 (기본값: 8085)')
        parser.add_argument('--host', type=str, default='0.0.0.0', help='서버 호스트 (기본값: 0.0.0.0)')
        args = parser.parse_args()
        
        # 서버 생성 및 시작
        server = NaverTrendServer(port=args.port)
        server.start()
        
    except KeyboardInterrupt:
        logger.info("서버가 사용자에 의해 중지되었습니다.")
    except Exception as e:
        logger.error(f"네이버 트렌드 서버 실행 실패: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 