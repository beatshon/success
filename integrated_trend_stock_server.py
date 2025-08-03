#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 트렌드-주식 분석 서버
실제 주식 데이터와 네이버 트렌드 분석을 결합한 웹 서버
"""

import sys
import time
import threading
import signal
import argparse
import asyncio
import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from loguru import logger

# 프로젝트 모듈 import
from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer, SignalStrength, MarketCondition
from error_handler import ErrorType, ErrorLevel, handle_error

class IntegratedTrendStockServer:
    """통합 트렌드-주식 분석 서버"""
    
    def __init__(self, port: int = 8086):
        """초기화"""
        self.port = port
        self.analyzer = None
        
        # Flask 앱 생성
        self.app = Flask('integrated_trend_stock_server', 
                        template_folder='templates',
                        static_folder='static')
        
        # CORS 설정
        CORS(self.app)
        
        # 라우트 설정
        self._setup_routes()
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신. 서버를 종료합니다.")
        self.stop()
        
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'analyzer_initialized': self.analyzer is not None,
                'analysis_running': self.analyzer.is_analyzing if self.analyzer else False,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('integrated_dashboard.html')

        @self.app.route('/api/integrated-signals', methods=['GET'])
        def get_integrated_signals():
            """통합 투자 신호 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                signals = self.analyzer.get_all_signals()
                
                # dataclass를 dict로 변환
                signals_dict = {}
                for stock_code, signal in signals.items():
                    signals_dict[stock_code] = {
                        'stock_code': signal.stock_code,
                        'stock_name': signal.stock_name,
                        'signal_strength': signal.signal_strength.value,
                        'confidence_score': signal.confidence_score,
                        'trend_impact': signal.trend_impact,
                        'technical_impact': signal.technical_impact,
                        'market_impact': signal.market_impact,
                        'reasoning': signal.reasoning,
                        'timestamp': signal.timestamp.isoformat(),
                        'price_target': signal.price_target,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'position_size': signal.position_size,
                        'risk_level': signal.risk_level,
                        'market_volatility': signal.market_volatility,
                        'stop_loss_percent': signal.stop_loss_percent,
                        'take_profit_percent': signal.take_profit_percent,
                        'risk_reward_ratio': signal.risk_reward_ratio,
                        'max_loss': signal.max_loss,
                        'potential_profit': signal.potential_profit,
                        'holding_period': signal.holding_period
                    }
                
                return jsonify({
                    'signals': signals_dict,
                    'total_count': len(signals_dict),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"통합 신호 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stock-signal/<stock_code>', methods=['GET'])
        def get_stock_signal(stock_code):
            """특정 종목 신호 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                signal = self.analyzer.get_signals_for_stock(stock_code)
                
                if not signal:
                    return jsonify({'error': f'종목 {stock_code}의 신호를 찾을 수 없습니다.'}), 404
                
                return jsonify({
                    'stock_code': signal.stock_code,
                    'stock_name': signal.stock_name,
                    'signal_strength': signal.signal_strength.value,
                    'confidence_score': signal.confidence_score,
                    'trend_impact': signal.trend_impact,
                    'technical_impact': signal.technical_impact,
                    'market_impact': signal.market_impact,
                    'reasoning': signal.reasoning,
                    'timestamp': signal.timestamp.isoformat(),
                    'price_target': signal.price_target,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'position_size': signal.position_size,
                    'risk_level': signal.risk_level,
                    'market_volatility': signal.market_volatility,
                    'stop_loss_percent': signal.stop_loss_percent,
                    'take_profit_percent': signal.take_profit_percent,
                    'risk_reward_ratio': signal.risk_reward_ratio,
                    'max_loss': signal.max_loss,
                    'potential_profit': signal.potential_profit,
                    'holding_period': signal.holding_period
                })
                
            except Exception as e:
                logger.error(f"종목 신호 조회 실패 ({stock_code}): {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-analysis', methods=['GET'])
        def get_market_analysis():
            """시장 분석 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                market_analysis = self.analyzer.get_market_analysis()
                
                if not market_analysis:
                    return jsonify({'error': '시장 분석 데이터가 없습니다.'}), 404
                
                return jsonify({
                    'market_condition': market_analysis.market_condition.value,
                    'overall_sentiment': market_analysis.overall_sentiment,
                    'sector_performance': market_analysis.sector_performance,
                    'trending_sectors': market_analysis.trending_sectors,
                    'risk_factors': market_analysis.risk_factors,
                    'opportunities': market_analysis.opportunities,
                    'timestamp': market_analysis.timestamp.isoformat()
                })
                
            except Exception as e:
                logger.error(f"시장 분석 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analysis-summary', methods=['GET'])
        def get_analysis_summary():
            """분석 요약 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                summary = self.analyzer.get_analysis_summary()
                
                return jsonify(summary)
                
            except Exception as e:
                logger.error(f"분석 요약 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/generate-signals', methods=['POST'])
        def generate_signals():
            """신호 생성 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                # 비동기 함수 실행
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                signals = loop.run_until_complete(self.analyzer.generate_integrated_signals())
                market_analysis = loop.run_until_complete(self.analyzer.analyze_market_condition())
                
                loop.close()
                
                return jsonify({
                    'message': '신호 생성 완료',
                    'signals_count': len(signals),
                    'market_condition': market_analysis.market_condition.value if market_analysis else 'unknown',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"신호 생성 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start-analysis', methods=['POST'])
        def start_analysis():
            """연속 분석 시작 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                self.analyzer.start_continuous_analysis()
                
                return jsonify({
                    'message': '연속 분석이 시작되었습니다.',
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"연속 분석 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop-analysis', methods=['POST'])
        def stop_analysis():
            """연속 분석 중지 API"""
            try:
                if not self.analyzer:
                    return jsonify({'error': '분석기가 초기화되지 않았습니다.'}), 500
                
                self.analyzer.stop_continuous_analysis()
                
                return jsonify({
                    'message': '연속 분석이 중지되었습니다.',
                    'status': 'stopped',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"연속 분석 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/market-condition-description/<condition>', methods=['GET'])
        def get_market_condition_description(condition):
            """시장 상황 설명 API"""
            try:
                descriptions = {
                    'bull_market': {
                        'name': '상승장',
                        'description': '시장이 전반적으로 상승하는 구간으로, 투자 심리가 긍정적입니다.',
                        'strategy': '성장주 중심의 적극적 투자 전략을 권장합니다.',
                        'risk_level': '중간',
                        'color': 'green'
                    },
                    'bear_market': {
                        'name': '하락장',
                        'description': '시장이 전반적으로 하락하는 구간으로, 투자 심리가 위축됩니다.',
                        'strategy': '방어적 포트폴리오 구성과 현금 보유를 권장합니다.',
                        'risk_level': '높음',
                        'color': 'red'
                    },
                    'sideways': {
                        'name': '횡보장',
                        'description': '시장이 특정 범위 내에서 등락을 반복하는 구간입니다.',
                        'strategy': '개별 종목 분석을 통한 선택적 투자를 권장합니다.',
                        'risk_level': '중간',
                        'color': 'yellow'
                    },
                    'volatile': {
                        'name': '변동성 장',
                        'description': '시장 변동성이 높아 예측이 어려운 구간입니다.',
                        'strategy': '리스크 관리에 중점을 둔 투자를 권장합니다.',
                        'risk_level': '높음',
                        'color': 'orange'
                    },
                    'trending_up': {
                        'name': '상승 추세',
                        'description': '시장이 상승 추세를 보이는 구간입니다.',
                        'strategy': '추세 추종 전략을 활용한 투자를 권장합니다.',
                        'risk_level': '중간',
                        'color': 'lightgreen'
                    },
                    'trending_down': {
                        'name': '하락 추세',
                        'description': '시장이 하락 추세를 보이는 구간입니다.',
                        'strategy': '보수적 투자와 현금 보유를 권장합니다.',
                        'risk_level': '높음',
                        'color': 'lightcoral'
                    }
                }
                
                description = descriptions.get(condition, {
                    'name': '알 수 없음',
                    'description': '시장 상황을 분석할 수 없습니다.',
                    'strategy': '추가 분석이 필요합니다.',
                    'risk_level': '알 수 없음',
                    'color': 'gray'
                })
                
                return jsonify(description)
                
            except Exception as e:
                logger.error(f"시장 상황 설명 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/signal-strength-description/<strength>', methods=['GET'])
        def get_signal_strength_description(strength):
            """신호 강도 설명 API"""
            try:
                descriptions = {
                    'strong_buy': {
                        'name': '강력 매수',
                        'description': '매우 강한 매수 신호입니다.',
                        'action': '적극적인 매수 고려',
                        'confidence': '높음',
                        'color': 'darkgreen'
                    },
                    'buy': {
                        'name': '매수',
                        'description': '매수 신호입니다.',
                        'action': '매수 고려',
                        'confidence': '중간',
                        'color': 'green'
                    },
                    'hold': {
                        'name': '관망',
                        'description': '현재 상태 유지를 권장합니다.',
                        'action': '관망',
                        'confidence': '중간',
                        'color': 'yellow'
                    },
                    'sell': {
                        'name': '매도',
                        'description': '매도 신호입니다.',
                        'action': '매도 고려',
                        'confidence': '중간',
                        'color': 'red'
                    },
                    'strong_sell': {
                        'name': '강력 매도',
                        'description': '매우 강한 매도 신호입니다.',
                        'action': '적극적인 매도 고려',
                        'confidence': '높음',
                        'color': 'darkred'
                    }
                }
                
                description = descriptions.get(strength, {
                    'name': '알 수 없음',
                    'description': '신호를 분석할 수 없습니다.',
                    'action': '추가 분석 필요',
                    'confidence': '알 수 없음',
                    'color': 'gray'
                })
                
                return jsonify(description)
                
            except Exception as e:
                logger.error(f"신호 강도 설명 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

    def initialize_analyzer(self):
        """분석기 초기화"""
        try:
            logger.info("통합 분석기 초기화 시작")
            self.analyzer = IntegratedTrendStockAnalyzer()
            logger.info("통합 분석기 초기화 완료")
            
        except Exception as e:
            logger.error(f"통합 분석기 초기화 실패: {e}")
            raise
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"통합 트렌드-주식 분석 서버 시작 (포트: {self.port})")
            
            # 분석기 초기화
            self.initialize_analyzer()
            
            # 서버 실행
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            raise
    
    def stop(self):
        """서버 중지"""
        try:
            if self.analyzer:
                self.analyzer.stop_continuous_analysis()
            
            logger.info("통합 트렌드-주식 분석 서버 종료")
            
        except Exception as e:
            logger.error(f"서버 종료 실패: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 트렌드-주식 분석 서버')
    parser.add_argument('--port', type=int, default=8086, help='서버 포트 (기본값: 8086)')
    
    args = parser.parse_args()
    
    try:
        server = IntegratedTrendStockServer(port=args.port)
        server.start()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 