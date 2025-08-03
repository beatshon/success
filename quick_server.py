#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 테스트용 웹 서버
초기화 시간을 단축한 버전
"""

import sys
import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from loguru import logger

class QuickTestServer:
    """빠른 테스트용 서버"""
    
    def __init__(self, port: int = 8086):
        """초기화"""
        self.port = port
        self.analysis_running = False
        self.start_time = datetime.now()
        
        # Flask 앱 생성
        self.app = Flask('quick_test_server', 
                        template_folder='templates',
                        static_folder='static')
        
        # CORS 설정
        CORS(self.app)
        
        # 라우트 설정
        self._setup_routes()
        
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'server_type': 'quick_test',
                'uptime': str(datetime.now() - self.start_time),
                'analysis_running': self.analysis_running,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('integrated_dashboard.html')

        @self.app.route('/api/integrated-signals', methods=['GET'])
        def get_integrated_signals():
            """통합 투자 신호 API (가상 데이터)"""
            try:
                # 가상 신호 데이터 생성
                virtual_signals = {
                    '005930': {
                        'stock_code': '005930',
                        'stock_name': '삼성전자',
                        'signal_strength': 'buy',
                        'confidence_score': 0.75,
                        'trend_impact': 0.8,
                        'technical_impact': 0.7,
                        'market_impact': 0.6,
                        'reasoning': ['반도체 수요 증가', 'AI 트렌드 긍정적', '기술적 지지선 형성'],
                        'timestamp': datetime.now().isoformat(),
                        'price_target': 84000,
                        'stop_loss': 78000,
                        'take_profit': 84000,
                        'position_size': 2000000,
                        'risk_level': 'medium',
                        'market_volatility': 'medium',
                        'stop_loss_percent': 2.5,
                        'take_profit_percent': 5.0,
                        'risk_reward_ratio': 2.0,
                        'max_loss': 100000,
                        'potential_profit': 200000,
                        'holding_period': 'medium_term'
                    },
                    '000660': {
                        'stock_code': '000660',
                        'stock_name': 'SK하이닉스',
                        'signal_strength': 'strong_buy',
                        'confidence_score': 0.85,
                        'trend_impact': 0.9,
                        'technical_impact': 0.8,
                        'market_impact': 0.7,
                        'reasoning': ['메모리 가격 상승', 'AI 수요 급증', '강한 상승 모멘텀'],
                        'timestamp': datetime.now().isoformat(),
                        'price_target': 178500,
                        'stop_loss': 165750,
                        'take_profit': 178500,
                        'position_size': 3000000,
                        'risk_level': 'low',
                        'market_volatility': 'low',
                        'stop_loss_percent': 2.5,
                        'take_profit_percent': 5.0,
                        'risk_reward_ratio': 2.0,
                        'max_loss': 90000,
                        'potential_profit': 450000,
                        'holding_period': 'long_term'
                    },
                    '035420': {
                        'stock_code': '035420',
                        'stock_name': '네이버',
                        'signal_strength': 'hold',
                        'confidence_score': 0.6,
                        'trend_impact': 0.5,
                        'technical_impact': 0.4,
                        'market_impact': 0.3,
                        'reasoning': ['AI 경쟁 심화', '수익성 압박', '관망 권장'],
                        'timestamp': datetime.now().isoformat(),
                        'price_target': 218900,
                        'stop_loss': 213400,
                        'take_profit': 218900,
                        'position_size': 1000000,
                        'risk_level': 'high',
                        'market_volatility': 'high',
                        'stop_loss_percent': 3.0,
                        'take_profit_percent': 4.0,
                        'risk_reward_ratio': 1.33,
                        'max_loss': 70000,
                        'potential_profit': 80000,
                        'holding_period': 'short_term'
                    }
                }
                
                return jsonify({
                    'status': 'success',
                    'data': virtual_signals,
                    'message': '가상 데이터로 빠른 테스트 중'
                })
                
            except Exception as e:
                logger.error(f"가상 신호 생성 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-analysis', methods=['GET'])
        def get_market_analysis():
            """시장 분석 API (가상 데이터)"""
            try:
                virtual_analysis = {
                    'market_condition': 'bull_market',
                    'overall_sentiment': 0.75,
                    'sector_performance': {
                        '반도체': 0.85,
                        'AI/기술': 0.80,
                        '자동차': 0.70,
                        '금융': 0.60
                    },
                    'trending_sectors': ['반도체', 'AI/기술', '배터리'],
                    'risk_factors': ['금리 인상 가능성', '지정학적 리스크'],
                    'opportunities': ['AI 수요 증가', '반도체 회복'],
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify({
                    'status': 'success',
                    'data': virtual_analysis,
                    'message': '가상 시장 분석 데이터'
                })
                
            except Exception as e:
                logger.error(f"가상 시장 분석 생성 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analysis-summary', methods=['GET'])
        def get_analysis_summary():
            """분석 요약 API"""
            try:
                summary = {
                    'total_stocks_analyzed': 3,
                    'strong_buy_signals': 1,
                    'buy_signals': 1,
                    'hold_signals': 1,
                    'sell_signals': 0,
                    'strong_sell_signals': 0,
                    'average_confidence': 0.73,
                    'market_condition': 'bull_market',
                    'last_updated': datetime.now().isoformat(),
                    'server_type': 'quick_test'
                }
                
                return jsonify({
                    'status': 'success',
                    'data': summary,
                    'message': '빠른 테스트 분석 요약'
                })
                
            except Exception as e:
                logger.error(f"분석 요약 생성 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start-analysis', methods=['POST'])
        def start_analysis():
            """분석 시작"""
            try:
                self.analysis_running = True
                return jsonify({
                    'status': 'success',
                    'message': '빠른 테스트 분석이 시작되었습니다.',
                    'server_type': 'quick_test'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop-analysis', methods=['POST'])
        def stop_analysis():
            """분석 중지"""
            try:
                self.analysis_running = False
                return jsonify({
                    'status': 'success',
                    'message': '빠른 테스트 분석이 중지되었습니다.',
                    'server_type': 'quick_test'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def start(self):
        """서버 시작"""
        try:
            logger.info(f"빠른 테스트 서버 시작 (포트: {self.port})")
            logger.info("🌐 웹 브라우저에서 http://localhost:8086 접속하세요")
            logger.info("⏹️  서버를 중지하려면 Ctrl+C를 누르세요")
            
            # 서버 실행
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            raise

def main():
    """메인 함수"""
    print("🚀 빠른 테스트 서버 시작")
    print("=" * 50)
    
    try:
        server = QuickTestServer(port=8086)
        server.start()
        
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 