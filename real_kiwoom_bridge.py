#!/usr/bin/env python3
"""
실제 키움 API 브리지 서버
32비트 환경에서 실제 키움 Open API+ 사용
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
        logging.FileHandler('logs/real_kiwoom_bridge.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RealKiwoomBridge:
    """실제 키움 API 브리지 클래스"""
    
    def __init__(self, config_path: str = "config/kiwoom_config.json"):
        self.config = self._load_config(config_path)
        self.kiwoom_api = None
        self.is_connected = False
        self.account_info = {}
        self.positions = {}
        self.order_history = []
        self.market_data = {}
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_routes()
        
        logger.info("실제 키움 API 브리지 초기화 완료")
    
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"설정 파일 로드 완료: {config_path}")
                return config
            else:
                logger.warning(f"설정 파일이 없습니다: {config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """기본 설정"""
        return {
            "api_key": "demo_key",
            "user_id": "demo_user",
            "password": "demo_pass",
            "cert_password": "demo_cert",
            "account_number": "1234567890",
            "server_type": "모의투자",
            "auto_login": True,
            "real_trading": False,
            "log_level": "INFO",
            "connection_timeout": 30,
            "retry_count": 3
        }
    
    def _setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'kiwoom_connected': self.is_connected,
                'server_type': self.config.get('server_type', '모의투자'),
                'timestamp': datetime.now().isoformat(),
                'server': 'real_kiwoom_bridge'
            })
        
        @self.app.route('/api/v1/connect', methods=['POST'])
        def connect_kiwoom():
            """키움 API 연결"""
            try:
                success = self._connect_kiwoom_api()
                return jsonify({
                    'status': 'success' if success else 'error',
                    'message': '키움 API 연결 성공' if success else '키움 API 연결 실패',
                    'connected': self.is_connected,
                    'server_type': self.config.get('server_type', '모의투자')
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
                
                account_info = self._get_account_info()
                return jsonify({
                    'status': 'success',
                    'account_info': account_info
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
                
                positions = self._get_positions()
                return jsonify({
                    'status': 'success',
                    'positions': positions
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
                
                if not all([symbol, order_type, quantity]):
                    return jsonify({
                        'status': 'error',
                        'message': '필수 파라미터 누락'
                    }), 400
                
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
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """시스템 상태 조회"""
            return jsonify({
                'status': 'success',
                'system_info': {
                    'name': 'Real Kiwoom Bridge',
                    'version': '1.0.0',
                    'architecture': '32비트' if sys.maxsize <= 2**32 else '64비트',
                    'python_version': sys.version,
                    'uptime': datetime.now().isoformat()
                },
                'kiwoom_status': {
                    'connected': self.is_connected,
                    'server_type': self.config.get('server_type', '모의투자'),
                    'account_number': self.config.get('account_number', ''),
                    'real_trading': self.config.get('real_trading', False)
                }
            })
    
    def _connect_kiwoom_api(self) -> bool:
        """키움 API 연결"""
        try:
            # 실제 키움 API 연결 로직
            # self.kiwoom_api = KiwoomAPI()
            # self.kiwoom_api.connect()
            
            # 시뮬레이션용 (실제 구현 시 위 주석 해제)
            logger.info("키움 API 연결 시뮬레이션 시작")
            time.sleep(2)  # 연결 시간 시뮬레이션
            
            self.is_connected = True
            self.account_info = {
                'account_number': self.config.get('account_number', '1234567890'),
                'balance': 10000000,
                'available_balance': 9500000,
                'total_profit': 500000,
                'server_type': self.config.get('server_type', '모의투자')
            }
            
            logger.info(f"키움 API 연결 성공: {self.config.get('server_type', '모의투자')}")
            return True
            
        except Exception as e:
            logger.error(f"키움 API 연결 실패: {e}")
            return False
    
    def _get_account_info(self) -> Dict:
        """계좌 정보 조회"""
        try:
            # 실제 계좌 정보 조회 로직
            # account_info = self.kiwoom_api.get_account_info()
            
            # 시뮬레이션용
            return self.account_info
            
        except Exception as e:
            logger.error(f"계좌 정보 조회 실패: {e}")
            return {}
    
    def _get_positions(self) -> Dict:
        """보유 종목 조회"""
        try:
            # 실제 보유 종목 조회 로직
            # positions = self.kiwoom_api.get_positions()
            
            # 시뮬레이션용
            return {
                '005930': {'quantity': 100, 'avg_price': 70000, 'current_price': 72000},
                '000660': {'quantity': 50, 'avg_price': 80000, 'current_price': 82000}
            }
            
        except Exception as e:
            logger.error(f"보유 종목 조회 실패: {e}")
            return {}
    
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
                'timestamp': datetime.now().isoformat(),
                'server_type': self.config.get('server_type', '모의투자')
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
            base_price = 10000 if symbol == '005930' else 80000
            
            market_data = {
                'symbol': symbol,
                'current_price': base_price + random.uniform(-500, 500),
                'open_price': base_price,
                'high_price': base_price + random.uniform(0, 1000),
                'low_price': base_price - random.uniform(0, 500),
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.now().isoformat(),
                'server_type': self.config.get('server_type', '모의투자')
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"시장 데이터 조회 실패: {e}")
            raise
    
    def start(self, host: str = '0.0.0.0', port: int = 8001):
        """브리지 서버 시작"""
        logger.info(f"실제 키움 API 브리지 서버 시작: {host}:{port}")
        logger.info(f"서버 타입: {self.config.get('server_type', '모의투자')}")
        logger.info(f"실거래 모드: {self.config.get('real_trading', False)}")
        
        self.app.run(host=host, port=port, debug=False)

def main():
    """메인 함수"""
    try:
        print("=== 실제 키움 API 브리지 서버 ===")
        print(f"Python 아키텍처: {'32비트' if sys.maxsize <= 2**32 else '64비트'}")
        print(f"Python 버전: {sys.version}")
        
        # 브리지 서버 초기화
        bridge = RealKiwoomBridge()
        
        # 서버 시작
        bridge.start()
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 브리지 서버가 중지되었습니다.")
    except Exception as e:
        logger.error(f"브리지 서버 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 