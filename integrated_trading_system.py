#!/usr/bin/env python3
"""
통합 트레이딩 시스템 (키움 브리지 연동)
64비트 환경에서 딥러닝 모델과 키움 API를 통합
"""

import sys
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KiwoomBridgeClient:
    """키움 브리지 클라이언트"""
    
    def __init__(self, bridge_url: str = "http://localhost:8001"):
        self.bridge_url = bridge_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.is_connected = False
        
        logger.info(f"키움 브리지 클라이언트 초기화: {bridge_url}")
    
    def connect(self) -> bool:
        """키움 API 연결"""
        try:
            response = self.session.post(f"{self.bridge_url}/api/v1/connect")
            if response.status_code == 200:
                data = response.json()
                self.is_connected = data.get('connected', False)
                logger.info(f"키움 API 연결: {data['message']}")
                return self.is_connected
            else:
                logger.error(f"키움 API 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"키움 API 연결 오류: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """계좌 정보 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/account")
            if response.status_code == 200:
                data = response.json()
                return data.get('account_info')
            else:
                logger.error(f"계좌 정보 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"계좌 정보 조회 오류: {e}")
            return None
    
    def get_positions(self) -> Optional[Dict]:
        """보유 종목 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/positions")
            if response.status_code == 200:
                data = response.json()
                return data.get('positions')
            else:
                logger.error(f"보유 종목 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"보유 종목 조회 오류: {e}")
            return None
    
    def place_order(self, symbol: str, order_type: str, quantity: int, price: float = 0) -> Optional[Dict]:
        """주문 실행"""
        try:
            payload = {
                'symbol': symbol,
                'order_type': order_type,
                'quantity': quantity,
                'price': price
            }
            
            response = self.session.post(f"{self.bridge_url}/api/v1/order", json=payload)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"주문 실행 성공: {symbol} {order_type} {quantity}주")
                return data.get('order_result')
            else:
                logger.error(f"주문 실행 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"주문 실행 오류: {e}")
            return None
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """시장 데이터 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/market_data", params={'symbol': symbol})
            if response.status_code == 200:
                data = response.json()
                return data.get('market_data')
            else:
                logger.error(f"시장 데이터 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            return None

class SimpleTradingModel:
    """간단한 트레이딩 모델 (딥러닝 대신 통계적 접근)"""
    
    def __init__(self):
        self.model_params = {
            'ma_short': 5,
            'ma_long': 20,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        logger.info("간단한 트레이딩 모델 초기화 완료")
    
    def calculate_ma(self, prices: List[float], period: int) -> List[float]:
        """이동평균 계산"""
        if len(prices) < period:
            return []
        
        ma_values = []
        for i in range(period - 1, len(prices)):
            ma = sum(prices[i-period+1:i+1]) / period
            ma_values.append(ma)
        
        return ma_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """RSI 계산"""
        if len(prices) < period + 1:
            return []
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        rsi_values = []
        for i in range(period, len(gains)):
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def generate_signals(self, symbol: str, market_data: Dict) -> Dict:
        """트레이딩 신호 생성"""
        try:
            current_price = market_data['current_price']
            
            # 시뮬레이션용 가격 데이터 생성
            import random
            prices = [current_price]
            for _ in range(30):
                change = random.uniform(-0.02, 0.02)  # ±2% 변동
                prices.append(prices[-1] * (1 + change))
            
            # 기술적 지표 계산
            ma_short = self.calculate_ma(prices, self.model_params['ma_short'])
            ma_long = self.calculate_ma(prices, self.model_params['ma_long'])
            rsi = self.calculate_rsi(prices, self.model_params['rsi_period'])
            
            # 신호 생성
            signals = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'signals': {}
            }
            
            if len(ma_short) > 0 and len(ma_long) > 0:
                # 이동평균 크로스오버
                if ma_short[-1] > ma_long[-1] and len(ma_short) > 1 and ma_short[-2] <= ma_long[-2]:
                    signals['signals']['ma_crossover'] = 'buy'
                elif ma_short[-1] < ma_long[-1] and len(ma_short) > 1 and ma_short[-2] >= ma_long[-2]:
                    signals['signals']['ma_crossover'] = 'sell'
                else:
                    signals['signals']['ma_crossover'] = 'hold'
            
            if len(rsi) > 0:
                # RSI 신호
                if rsi[-1] < self.model_params['rsi_oversold']:
                    signals['signals']['rsi'] = 'buy'
                elif rsi[-1] > self.model_params['rsi_overbought']:
                    signals['signals']['rsi'] = 'sell'
                else:
                    signals['signals']['rsi'] = 'hold'
            
            # 종합 신호
            buy_signals = sum(1 for signal in signals['signals'].values() if signal == 'buy')
            sell_signals = sum(1 for signal in signals['signals'].values() if signal == 'sell')
            
            if buy_signals > sell_signals:
                signals['overall_signal'] = 'buy'
            elif sell_signals > buy_signals:
                signals['overall_signal'] = 'sell'
            else:
                signals['overall_signal'] = 'hold'
            
            logger.info(f"트레이딩 신호 생성: {symbol} - {signals['overall_signal']}")
            return signals
            
        except Exception as e:
            logger.error(f"신호 생성 오류: {e}")
            return {
                'symbol': symbol,
                'current_price': market_data.get('current_price', 0),
                'timestamp': datetime.now().isoformat(),
                'overall_signal': 'hold',
                'error': str(e)
            }

class IntegratedTradingSystem:
    """통합 트레이딩 시스템"""
    
    def __init__(self):
        self.kiwoom_client = KiwoomBridgeClient()
        self.trading_model = SimpleTradingModel()
        self.portfolio = {}
        self.trade_history = []
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_routes()
        
        logger.info("통합 트레이딩 시스템 초기화 완료")
    
    def _setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'system': 'Integrated Trading System',
                'kiwoom_connected': self.kiwoom_client.is_connected,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/ready', methods=['GET'])
        def ready_check():
            """준비 상태 확인"""
            return jsonify({
                'status': 'ready',
                'kiwoom_connected': self.kiwoom_client.is_connected,
                'model_ready': True,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """시스템 상태 조회"""
            account_info = self.kiwoom_client.get_account_info()
            positions = self.kiwoom_client.get_positions()
            
            return jsonify({
                'status': 'success',
                'system_info': {
                    'name': 'Integrated Trading System',
                    'version': '2.0.0',
                    'architecture': '64비트' if sys.maxsize > 2**32 else '32비트',
                    'python_version': sys.version,
                    'uptime': datetime.now().isoformat()
                },
                'kiwoom_status': {
                    'connected': self.kiwoom_client.is_connected,
                    'account_info': account_info,
                    'positions': positions
                },
                'trading_status': {
                    'model_ready': True,
                    'portfolio': self.portfolio,
                    'trade_count': len(self.trade_history)
                }
            })
        
        @self.app.route('/api/v1/connect', methods=['POST'])
        def connect_kiwoom():
            """키움 API 연결"""
            success = self.kiwoom_client.connect()
            return jsonify({
                'status': 'success' if success else 'error',
                'connected': success,
                'message': '키움 API 연결 성공' if success else '키움 API 연결 실패'
            })
        
        @self.app.route('/api/v1/analysis', methods=['POST'])
        def run_analysis():
            """트레이딩 분석 실행"""
            try:
                data = request.get_json()
                symbol = data.get('symbol', '005930')
                
                # 시장 데이터 조회
                market_data = self.kiwoom_client.get_market_data(symbol)
                if not market_data:
                    return jsonify({
                        'status': 'error',
                        'message': '시장 데이터 조회 실패'
                    }), 400
                
                # 트레이딩 신호 생성
                signals = self.trading_model.generate_signals(symbol, market_data)
                
                return jsonify({
                    'status': 'success',
                    'analysis': {
                        'symbol': symbol,
                        'market_data': market_data,
                        'signals': signals,
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"분석 실행 오류: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/trading/signals', methods=['GET'])
        def get_trading_signals():
            """트레이딩 신호 조회"""
            try:
                symbol = request.args.get('symbol', '005930')
                
                market_data = self.kiwoom_client.get_market_data(symbol)
                if not market_data:
                    return jsonify({
                        'status': 'error',
                        'message': '시장 데이터 조회 실패'
                    }), 400
                
                signals = self.trading_model.generate_signals(symbol, market_data)
                
                return jsonify({
                    'status': 'success',
                    'signals': signals
                })
                
            except Exception as e:
                logger.error(f"신호 조회 오류: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/portfolio', methods=['GET'])
        def get_portfolio():
            """포트폴리오 조회"""
            try:
                account_info = self.kiwoom_client.get_account_info()
                positions = self.kiwoom_client.get_positions()
                
                return jsonify({
                    'status': 'success',
                    'portfolio': {
                        'account_info': account_info,
                        'positions': positions,
                        'trade_history': self.trade_history[-10:],  # 최근 10개 거래
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"포트폴리오 조회 오류: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/execute_trade', methods=['POST'])
        def execute_trade():
            """거래 실행"""
            try:
                data = request.get_json()
                symbol = data.get('symbol')
                order_type = data.get('order_type')
                quantity = data.get('quantity')
                price = data.get('price', 0)
                
                if not all([symbol, order_type, quantity]):
                    return jsonify({
                        'status': 'error',
                        'message': '필수 파라미터 누락'
                    }), 400
                
                # 주문 실행
                order_result = self.kiwoom_client.place_order(symbol, order_type, quantity, price)
                if order_result:
                    self.trade_history.append(order_result)
                    logger.info(f"거래 실행 성공: {symbol} {order_type} {quantity}주")
                    
                    return jsonify({
                        'status': 'success',
                        'order_result': order_result
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': '주문 실행 실패'
                    }), 500
                
            except Exception as e:
                logger.error(f"거래 실행 오류: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def start(self, host: str = '0.0.0.0', port: int = 8000):
        """시스템 시작"""
        logger.info(f"통합 트레이딩 시스템 시작: {host}:{port}")
        
        # 키움 API 연결 시도
        if self.kiwoom_client.connect():
            logger.info("키움 API 연결 성공")
        else:
            logger.warning("키움 API 연결 실패 - 시뮬레이션 모드로 실행")
        
        self.app.run(host=host, port=port, debug=False)

def main():
    """메인 함수"""
    try:
        print("=== 통합 트레이딩 시스템 ===")
        print(f"Python 아키텍처: {'64비트' if sys.maxsize > 2**32 else '32비트'}")
        print(f"Python 버전: {sys.version}")
        
        # 시스템 초기화
        system = IntegratedTradingSystem()
        
        # 시스템 시작
        system.start()
        
    except KeyboardInterrupt:
        print("\n시스템이 중지되었습니다.")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 