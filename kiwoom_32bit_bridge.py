#!/usr/bin/env python3
"""
32비트 키움 API 브리지 서버
64비트 메인 시스템과 키움 API 사이의 중계 역할
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

# 32비트 환경 확인
if sys.maxsize > 2**32:
    print("경고: 이 스크립트는 32비트 Python 환경에서 실행해야 합니다.")
    print("키움 API는 32비트 환경에서만 안정적으로 작동합니다.")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/kiwoom_bridge.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KiwoomBridge:
    """키움 API 브리지 클래스"""
    
    def __init__(self):
        self.kiwoom_api = None
        self.is_connected = False
        self.account_info = {}
        self.positions = {}
        self.order_history = []
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_routes()
        
        logger.info("키움 API 브리지 초기화 완료")
    
    def _setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'kiwoom_connected': self.is_connected,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/connect', methods=['POST'])
        def connect_kiwoom():
            """키움 API 연결"""
            try:
                # 키움 API 연결 로직
                self._connect_kiwoom_api()
                
                return jsonify({
                    'status': 'success',
                    'message': '키움 API 연결 성공',
                    'connected': self.is_connected
                })
                
            except Exception as e:
                logger.error(f"키움 API 연결 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/account', methods=['GET'])
        def get_account_info():
            """계좌 정보 조회"""
            try:
                if not self.is_connected:
                    return jsonify({
                        'status': 'error',
                        'message': '키움 API가 연결되지 않았습니다.'
                    }), 400
                
                return jsonify({
                    'status': 'success',
                    'account_info': self.account_info
                })
                
            except Exception as e:
                logger.error(f"계좌 정보 조회 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/positions', methods=['GET'])
        def get_positions():
            """보유 종목 조회"""
            try:
                if not self.is_connected:
                    return jsonify({
                        'status': 'error',
                        'message': '키움 API가 연결되지 않았습니다.'
                    }), 400
                
                return jsonify({
                    'status': 'success',
                    'positions': self.positions
                })
                
            except Exception as e:
                logger.error(f"보유 종목 조회 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/order', methods=['POST'])
        def place_order():
            """주문 실행"""
            try:
                if not self.is_connected:
                    return jsonify({
                        'status': 'error',
                        'message': '키움 API가 연결되지 않았습니다.'
                    }), 400
                
                data = request.get_json()
                symbol = data.get('symbol')
                order_type = data.get('order_type')  # 'buy' or 'sell'
                quantity = data.get('quantity')
                price = data.get('price', 0)  # 0이면 시장가
                
                # 주문 실행 로직
                order_result = self._execute_order(symbol, order_type, quantity, price)
                
                return jsonify({
                    'status': 'success',
                    'order_result': order_result
                })
                
            except Exception as e:
                logger.error(f"주문 실행 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/market_data', methods=['GET'])
        def get_market_data():
            """시장 데이터 조회"""
            try:
                symbol = request.args.get('symbol')
                if not symbol:
                    return jsonify({
                        'status': 'error',
                        'message': '종목 코드가 필요합니다.'
                    }), 400
                
                # 시장 데이터 조회 로직
                market_data = self._get_market_data(symbol)
                
                return jsonify({
                    'status': 'success',
                    'market_data': market_data
                })
                
            except Exception as e:
                logger.error(f"시장 데이터 조회 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def _connect_kiwoom_api(self):
        """키움 API 연결"""
        try:
            # 실제 키움 API 연결 로직
            # self.kiwoom_api = KiwoomAPI()
            # self.kiwoom_api.connect()
            
            # 시뮬레이션용
            self.is_connected = True
            self.account_info = {
                'account_number': '1234567890',
                'balance': 10000000,
                'available_balance': 9500000,
                'total_profit': 500000
            }
            
            logger.info("키움 API 연결 성공")
            
        except Exception as e:
            logger.error(f"키움 API 연결 실패: {e}")
            raise
    
    def _execute_order(self, symbol: str, order_type: str, quantity: int, price: float) -> Dict:
        """주문 실행"""
        try:
            # 실제 주문 실행 로직
            # order_result = self.kiwoom_api.place_order(symbol, order_type, quantity, price)
            
            # 시뮬레이션용
            order_result = {
                'order_id': f"ORDER_{int(time.time())}",
                'symbol': symbol,
                'order_type': order_type,
                'quantity': quantity,
                'price': price,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
            # 주문 내역 저장
            self.order_history.append(order_result)
            
            logger.info(f"주문 실행: {symbol} {order_type} {quantity}주 @ {price}")
            
            return order_result
            
        except Exception as e:
            logger.error(f"주문 실행 실패: {e}")
            raise
    
    def _get_market_data(self, symbol: str) -> Dict:
        """시장 데이터 조회"""
        try:
            # 실제 시장 데이터 조회 로직
            # market_data = self.kiwoom_api.get_market_data(symbol)
            
            # 시뮬레이션용
            import random
            base_price = 10000
            market_data = {
                'symbol': symbol,
                'current_price': base_price + random.uniform(-500, 500),
                'open_price': base_price,
                'high_price': base_price + random.uniform(0, 1000),
                'low_price': base_price - random.uniform(0, 500),
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.now().isoformat()
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"시장 데이터 조회 실패: {e}")
            raise
    
    def start(self, host: str = '0.0.0.0', port: int = 8001):
        """브리지 서버 시작"""
        logger.info(f"키움 API 브리지 서버 시작: {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

def main():
    """메인 함수"""
    try:
        # 브리지 서버 초기화
        bridge = KiwoomBridge()
        
        # 서버 시작
        bridge.start()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 브리지 서버가 중지되었습니다.")
    except Exception as e:
        logger.error(f"브리지 서버 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 