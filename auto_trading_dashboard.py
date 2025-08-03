#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 매매 대시보드
실시간 포지션 모니터링 및 자동 매매 제어
"""

import sys
import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from loguru import logger

# 프로젝트 모듈 import
from auto_trading_system import AutoTradingSystem
from day_trading_config import DayTradingConfig

class AutoTradingDashboard:
    """자동 매매 대시보드"""
    
    def __init__(self, port: int = 8087):
        """초기화"""
        self.port = port
        self.trading_system = None
        
        # Flask 앱 생성
        self.app = Flask('auto_trading_dashboard', 
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
                'dashboard_type': 'auto_trading',
                'trading_system_initialized': self.trading_system is not None,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('auto_trading_dashboard.html')

        @self.app.route('/api/trading-status', methods=['GET'])
        def get_trading_status():
            """매매 상태 조회"""
            try:
                if not self.trading_system:
                    return jsonify({'error': '매매 시스템이 초기화되지 않았습니다.'}), 500
                
                status = self.trading_system.get_trading_status()
                return jsonify({
                    'status': 'success',
                    'data': status
                })
                
            except Exception as e:
                logger.error(f"매매 상태 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/positions', methods=['GET'])
        def get_positions():
            """포지션 목록 조회"""
            try:
                if not self.trading_system:
                    return jsonify({'error': '매매 시스템이 초기화되지 않았습니다.'}), 500
                
                positions = self.trading_system.get_positions()
                return jsonify({
                    'status': 'success',
                    'data': positions
                })
                
            except Exception as e:
                logger.error(f"포지션 목록 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/order-history', methods=['GET'])
        def get_order_history():
            """주문 이력 조회"""
            try:
                if not self.trading_system:
                    return jsonify({'error': '매매 시스템이 초기화되지 않았습니다.'}), 500
                
                history = self.trading_system.get_order_history()
                return jsonify({
                    'status': 'success',
                    'data': history
                })
                
            except Exception as e:
                logger.error(f"주문 이력 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start-trading', methods=['POST'])
        def start_trading():
            """자동 매매 시작"""
            try:
                if not self.trading_system:
                    return jsonify({'error': '매매 시스템이 초기화되지 않았습니다.'}), 500
                
                self.trading_system.start_auto_trading()
                return jsonify({
                    'status': 'success',
                    'message': '자동 매매가 시작되었습니다.'
                })
                
            except Exception as e:
                logger.error(f"자동 매매 시작 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop-trading', methods=['POST'])
        def stop_trading():
            """자동 매매 중지"""
            try:
                if not self.trading_system:
                    return jsonify({'error': '매매 시스템이 초기화되지 않았습니다.'}), 500
                
                self.trading_system.stop_auto_trading()
                return jsonify({
                    'status': 'success',
                    'message': '자동 매매가 중지되었습니다.'
                })
                
            except Exception as e:
                logger.error(f"자동 매매 중지 실패: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/trading-config', methods=['GET'])
        def get_trading_config():
            """매매 설정 조회"""
            try:
                config = DayTradingConfig()
                return jsonify({
                    'status': 'success',
                    'data': {
                        'max_daily_loss': config.max_daily_loss * 100,  # 퍼센트로 변환
                        'max_daily_trades': config.max_daily_trades,
                        'min_trade_interval': config.min_trade_interval,
                        'risk_levels': {
                            'conservative': config.risk_levels['conservative'],
                            'moderate': config.risk_levels['moderate'],
                            'aggressive': config.risk_levels['aggressive']
                        }
                    }
                })
                
            except Exception as e:
                logger.error(f"매매 설정 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500

    def initialize_trading_system(self):
        """매매 시스템 초기화"""
        try:
            logger.info("자동 매매 시스템 초기화 시작")
            self.trading_system = AutoTradingSystem()
            logger.info("자동 매매 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"자동 매매 시스템 초기화 실패: {e}")
            raise
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"자동 매매 대시보드 시작 (포트: {self.port})")
            
            # 매매 시스템 초기화
            self.initialize_trading_system()
            
            logger.info("🌐 웹 브라우저에서 http://localhost:8087 접속하세요")
            logger.info("⏹️  서버를 중지하려면 Ctrl+C를 누르세요")
            
            # 서버 실행
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            raise

def main():
    """메인 함수"""
    print("🚀 자동 매매 대시보드 시작")
    print("=" * 50)
    
    try:
        dashboard = AutoTradingDashboard(port=8087)
        dashboard.start()
        
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 