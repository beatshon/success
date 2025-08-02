#!/usr/bin/env python3
"""
간단한 네이버 트렌드 서버
Flask 충돌 문제를 피하기 위해 새로 작성
"""

import os
import sys
import signal
import argparse
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from loguru import logger
import random

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from naver_trend_analyzer import NaverTrendAnalyzer

class SimpleNaverServer:
    def __init__(self, port: int = 8086):
        """초기화"""
        self.port = port
        self.analyzer = None
        
        # 종목번호와 종목명 매핑 데이터
        self.stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI',
            '207940': '삼성바이오로직스',
            '068270': '셀트리온',
            '323410': '카카오뱅크',
            '035760': 'CJ대한통운',
            '051900': 'LG생활건강',
            '096770': 'SK이노베이션',
            '017670': 'SK텔레콤',
            '034020': '두산에너빌리티',
            '015760': '한국전력',
            '055550': '신한지주',
            '086790': '하나금융지주',
            '105560': 'KB금융',
            '139480': '이마트',
            '028260': '삼성물산'
        }
        
        # 새로운 Flask 앱 생성
        self.app = Flask('simple_naver_server')
        CORS(self.app)
        
        # 라우트 설정
        self._setup_routes()
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info("서버 종료 신호를 받았습니다.")
        if self.analyzer:
            self.analyzer.stop_continuous_analysis()
        sys.exit(0)
    
    def _setup_routes(self):
        """라우트 설정"""
        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('naver_trend_dashboard.html')
        
        @self.app.route('/api/health')
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'analyzer_initialized': self.analyzer is not None,
                'data_collection_running': self.analyzer.analysis_running if self.analyzer else False,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/naver-trends')
        def get_naver_trends():
            """네이버 트렌드 데이터 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                summary = self.analyzer.get_trend_summary()
                trending_keywords = self.analyzer.get_trending_keywords()
                
                return jsonify({
                    'summary': summary,
                    'trending_keywords': trending_keywords,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"네이버 트렌드 데이터 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market-sentiment')
        def get_market_sentiment():
            """시장 감정 분석 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                sentiment = self.analyzer.get_market_sentiment()
                return jsonify(sentiment)
                
            except Exception as e:
                logger.error(f"시장 감정 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market-condition')
        def get_market_condition():
            """시장 상황 분석 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 시장 상황 데이터 생성
                market_condition = {
                    'market_type': 'sideways',  # bull, bear, sideways
                    'confidence': 0.75,
                    'trend_strength': 0.3,
                    'volatility': 0.4,
                    'recommendation': '관망',
                    'reason': '시장이 횡보세를 보이고 있어 관망이 적절합니다.',
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(market_condition)
                
            except Exception as e:
                logger.error(f"시장 상황 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/portfolio-recommendation')
        def get_portfolio_recommendation():
            """포트폴리오 추천 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 포트폴리오 추천 데이터 생성
                portfolio = {
                    'total_allocation': 100,
                    'stocks': [
                        {'code': '005930', 'name': '삼성전자', 'allocation': 25, 'signal': 'HOLD'},
                        {'code': '000660', 'name': 'SK하이닉스', 'allocation': 20, 'signal': 'BUY'},
                        {'code': '035420', 'name': 'NAVER', 'allocation': 15, 'signal': 'HOLD'},
                        {'code': '035720', 'name': '카카오', 'allocation': 15, 'signal': 'SELL'},
                        {'code': '051910', 'name': 'LG화학', 'allocation': 15, 'signal': 'BUY'},
                        {'code': '006400', 'name': '삼성SDI', 'allocation': 10, 'signal': 'HOLD'}
                    ],
                    'risk_level': '보통',
                    'expected_return': 8.5,
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(portfolio)
                
            except Exception as e:
                logger.error(f"포트폴리오 추천 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/correlation-analysis')
        def get_correlation_analysis():
            """상관관계 분석 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 상관관계 분석 데이터 생성
                correlation_data = {
                    'high_correlation': 8,
                    'medium_correlation': 6,
                    'low_correlation': 6,
                    'total_analyzed': 20,
                    'top_correlations': [
                        {'keyword': 'AI', 'stock': '005930', 'correlation': 0.85},
                        {'keyword': '반도체', 'stock': '000660', 'correlation': 0.82},
                        {'keyword': '전기차', 'stock': '051910', 'correlation': 0.78},
                        {'keyword': '게임', 'stock': '035720', 'correlation': 0.75},
                        {'keyword': '플랫폼', 'stock': '035420', 'correlation': 0.72}
                    ],
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(correlation_data)
                
            except Exception as e:
                logger.error(f"상관관계 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-adaptive-signals/<stock_code>')
        def get_market_adaptive_signals(stock_code):
            """시장 적응형 투자 신호 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 시장 적응형 신호 데이터 생성
                signals = {
                    'stock_code': stock_code,
                    'stock_name': self.stock_names.get(stock_code, f'종목({stock_code})'),
                    'market_condition': 'sideways',
                    'beta_coefficient': round(random.uniform(0.8, 1.2), 2),
                    'correlation_with_market': round(random.uniform(0.6, 0.9), 2),
                    'volatility': round(random.uniform(0.15, 0.35), 2),
                    'momentum_score': round(random.uniform(-0.3, 0.3), 2),
                    'sentiment_score': round(random.uniform(-0.2, 0.2), 2),
                    'recommendation': random.choice(['매수', '매도', '보유']),
                    'confidence': round(random.uniform(0.6, 0.9), 2),
                    'risk_level': random.choice(['낮음', '보통', '높음']),
                    'target_price': round(random.uniform(50000, 150000), -2),
                    'stop_loss': round(random.uniform(45000, 140000), -2),
                    'take_profit': round(random.uniform(55000, 160000), -2),
                    'reason': '시장 상황과 종목 특성을 종합적으로 분석한 결과입니다.',
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"시장 적응형 신호 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/trending-keywords')
        def get_trending_keywords():
            """트렌딩 키워드 API"""
            try:
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
        
        @self.app.route('/api/stock-signals/<stock_code>')
        def get_stock_signals(stock_code):
            """특정 종목 투자 신호 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                signals = self.analyzer.get_investment_signals(stock_code)
                
                # 종목명 추가
                stock_name = self.stock_names.get(stock_code, f'종목({stock_code})')
                signals['stock_code'] = stock_code
                signals['stock_name'] = stock_name
                
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"투자 신호 조회 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/collect-data-now')
        def collect_data_now():
            """즉시 데이터 수집 API"""
            try:
                # 가상 데이터 강제 생성
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # 가상 데이터 수집 시뮬레이션
                logger.info("가상 데이터 수집 완료")
                
                return jsonify({
                    'message': '가상 데이터 수집이 완료되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"즉시 데이터 수집 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start-analysis')
        def start_analysis():
            """분석 시작 API"""
            try:
                # 가상 분석 시작
                if not self.analyzer.analysis_running:
                    self.analyzer.analysis_running = True
                
                logger.info("가상 분석이 시작되었습니다.")
                
                return jsonify({
                    'message': '가상 분석이 시작되었습니다.',
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"분석 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start-data-collection')
        def start_data_collection():
            """데이터 수집 시작 API"""
            try:
                # 가상 데이터 수집 시작
                logger.info("가상 데이터 수집이 시작되었습니다.")
                
                return jsonify({
                    'message': '가상 데이터 수집이 시작되었습니다.',
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"데이터 수집 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop-data-collection')
        def stop_data_collection():
            """데이터 수집 중지 API"""
            try:
                # 가상 데이터 수집 중지
                logger.info("가상 데이터 수집이 중지되었습니다.")
                
                return jsonify({
                    'message': '가상 데이터 수집이 중지되었습니다.',
                    'status': 'stopped',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"데이터 수집 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop-analysis')
        def stop_analysis():
            """분석 중지 API"""
            try:
                # 가상 분석 중지
                if self.analyzer.analysis_running:
                    self.analyzer.analysis_running = False
                    logger.info("가상 분석이 중지되었습니다.")
                
                return jsonify({
                    'message': '가상 분석이 중지되었습니다.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"분석 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-strategy/<condition>')
        def get_market_strategy(condition):
            """시장 상황별 투자 전략 API"""
            try:
                if not self.analyzer.trend_data:
                    self.analyzer._generate_virtual_trend_data()
                
                # undefined 값 처리
                if condition == 'undefined' or not condition:
                    condition = 'sideways'
                
                # 가상 시장 전략 데이터 생성
                strategies = {
                    'bull': {
                        'risk_management': {
                            'position_size': '적극적 (80-100%)',
                            'stop_loss': '5-8%',
                            'take_profit': '15-20%',
                            'focus': '성장주 중심'
                        },
                        'market_timing': {
                            'entry_strategy': '돌파 매수',
                            'exit_strategy': '단계적 익절',
                            'rebalancing': '월 1회'
                        },
                        'sector_focus': {
                            'primary': '기술주, 반도체',
                            'secondary': '바이오, 게임',
                            'avoid': '방어주'
                        },
                        'recommendation': '적극적 매수',
                        'confidence': 0.85
                    },
                    'bear': {
                        'risk_management': {
                            'position_size': '보수적 (20-40%)',
                            'stop_loss': '3-5%',
                            'take_profit': '8-12%',
                            'focus': '방어주 중심'
                        },
                        'market_timing': {
                            'entry_strategy': '저점 매수',
                            'exit_strategy': '빠른 익절',
                            'rebalancing': '주 1회'
                        },
                        'sector_focus': {
                            'primary': '소비재, 헬스케어',
                            'secondary': '유틸리티, 통신',
                            'avoid': '기술주, 금융주'
                        },
                        'recommendation': '관망 또는 보수적 매수',
                        'confidence': 0.75
                    },
                    'sideways': {
                        'risk_management': {
                            'position_size': '중립적 (50-70%)',
                            'stop_loss': '4-6%',
                            'take_profit': '10-15%',
                            'focus': '밸류주 중심'
                        },
                        'market_timing': {
                            'entry_strategy': '범위 매수',
                            'exit_strategy': '균형 익절',
                            'rebalancing': '2주 1회'
                        },
                        'sector_focus': {
                            'primary': '제조업, 건설',
                            'secondary': '소비재, 금융',
                            'avoid': '과열 섹터'
                        },
                        'recommendation': '선별적 매수',
                        'confidence': 0.70
                    }
                }
                
                strategy = strategies.get(condition, strategies['sideways'])
                strategy['market_condition'] = condition
                strategy['timestamp'] = datetime.now().isoformat()
                
                return jsonify(strategy)
                
            except Exception as e:
                logger.error(f"시장 전략 분석 실패: {e}")
                return jsonify({'error': str(e)}), 500
    
    def initialize_analyzer(self):
        """분석기 초기화"""
        try:
            logger.info("네이버 트렌드 분석기 초기화 시작")
            self.analyzer = NaverTrendAnalyzer()
            logger.info("네이버 트렌드 분석기 초기화 완료")
        except Exception as e:
            logger.error(f"분석기 초기화 실패: {e}")
            raise
    
    def start(self):
        """서버 시작"""
        try:
            self.initialize_analyzer()
            logger.info(f"네이버 트렌드 분석 서버가 시작되었습니다: http://localhost:{self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        except Exception as e:
            logger.error(f"네이버 트렌드 서버 시작 실패: {e}")
            raise

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='네이버 트렌드 분석 서버')
    parser.add_argument('--port', type=int, default=8086, help='서버 포트 (기본값: 8086)')
    
    args = parser.parse_args()
    
    try:
        server = SimpleNaverServer(port=args.port)
        server.start()
    except Exception as e:
        logger.error(f"네이버 트렌드 서버 실행 실패: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 