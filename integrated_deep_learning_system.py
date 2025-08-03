#!/usr/bin/env python3
"""
딥러닝 모델이 통합된 고급 트레이딩 시스템
64비트 메인 시스템 + 딥러닝 예측 + 키움 API 연동
"""

import os
import sys
import json
import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

# 딥러닝 모델 import
from simple_deep_learning_model import SimpleDeepLearningModel

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_dl_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KiwoomBridgeClient:
    """키움 API 브리지 클라이언트"""
    
    def __init__(self, bridge_url: str = "http://localhost:8001"):
        self.bridge_url = bridge_url
        logger.info(f"키움 브리지 클라이언트 초기화: {bridge_url}")
    
    def connect(self) -> bool:
        """키움 API 연결"""
        try:
            response = requests.post(f"{self.bridge_url}/api/v1/connect")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"키움 API 연결: {data.get('message', '연결 성공')}")
                return data.get('connected', False)
            return False
        except Exception as e:
            logger.error(f"키움 API 연결 실패: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """계좌 정보 조회"""
        try:
            response = requests.get(f"{self.bridge_url}/api/v1/account")
            if response.status_code == 200:
                data = response.json()
                return data.get('account_info', {})
            return None
        except Exception as e:
            logger.error(f"계좌 정보 조회 실패: {e}")
            return None
    
    def get_positions(self) -> Optional[Dict]:
        """보유 종목 조회"""
        try:
            response = requests.get(f"{self.bridge_url}/api/v1/positions")
            if response.status_code == 200:
                data = response.json()
                return data.get('positions', {})
            return None
        except Exception as e:
            logger.error(f"보유 종목 조회 실패: {e}")
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
            response = requests.post(f"{self.bridge_url}/api/v1/order", json=payload)
            if response.status_code == 200:
                data = response.json()
                order_result = data.get('order_result', {})
                logger.info(f"주문 실행 성공: {symbol} {order_type} {quantity}주")
                return order_result
            return None
        except Exception as e:
            logger.error(f"주문 실행 실패: {e}")
            return None
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """시장 데이터 조회"""
        try:
            response = requests.get(f"{self.bridge_url}/api/v1/market_data?symbol={symbol}")
            if response.status_code == 200:
                data = response.json()
                return data.get('market_data', {})
            return None
        except Exception as e:
            logger.error(f"시장 데이터 조회 실패: {e}")
            return None

class DeepLearningTradingModel:
    """딥러닝 트레이딩 모델"""
    
    def __init__(self):
        self.dl_model = SimpleDeepLearningModel()
        self.is_trained = False
        logger.info("딥러닝 트레이딩 모델 초기화 완료")
    
    def train_model(self):
        """모델 훈련"""
        try:
            # 샘플 데이터로 모델 훈련
            sample_data = self.dl_model.create_sample_data(500)
            X, y = self.dl_model.prepare_data(sample_data, 60)
            self.dl_model.train_model(X, y, epochs=20, batch_size=32)
            self.is_trained = True
            logger.info("딥러닝 모델 훈련 완료")
            return True
        except Exception as e:
            logger.error(f"딥러닝 모델 훈련 실패: {e}")
            return False
    
    def predict_price(self, market_data: Dict) -> Optional[float]:
        """가격 예측"""
        try:
            if not self.is_trained:
                logger.warning("딥러닝 모델이 훈련되지 않았습니다.")
                return None
            
            # 현재 시장 데이터로 예측
            current_data = {
                'close': market_data.get('current_price', 0),
                'volume': market_data.get('volume', 0),
                'ma_5': market_data.get('current_price', 0),  # 간단화
                'ma_20': market_data.get('current_price', 0),  # 간단화
                'rsi': 50  # 기본값
            }
            
            predicted_price = self.dl_model.predict_next_price(current_data)
            return predicted_price
            
        except Exception as e:
            logger.error(f"가격 예측 실패: {e}")
            return None
    
    def generate_signal(self, current_price: float, predicted_price: float) -> str:
        """트레이딩 신호 생성"""
        try:
            if predicted_price is None:
                return 'hold'
            
            change_pct = (predicted_price - current_price) / current_price * 100
            
            if change_pct > 3:  # 3% 이상 상승 예상
                return 'buy'
            elif change_pct < -3:  # 3% 이상 하락 예상
                return 'sell'
            else:
                return 'hold'
                
        except Exception as e:
            logger.error(f"신호 생성 실패: {e}")
            return 'hold'

class IntegratedDeepLearningSystem:
    """딥러닝 모델이 통합된 트레이딩 시스템"""
    
    def __init__(self):
        self.kiwoom_client = KiwoomBridgeClient()
        self.dl_model = DeepLearningTradingModel()
        self.portfolio = {}
        self.trade_history = []
        self.is_connected = False
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_routes()
        
        logger.info("딥러닝 통합 트레이딩 시스템 초기화 완료")
    
    def _setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'system': 'Deep Learning Integrated Trading System',
                'kiwoom_connected': self.is_connected,
                'dl_model_trained': self.dl_model.is_trained,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/ready', methods=['GET'])
        def ready_check():
            """준비 상태 확인"""
            return jsonify({
                'status': 'ready',
                'kiwoom_ready': self.is_connected,
                'dl_model_ready': self.dl_model.is_trained,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """시스템 상태 조회"""
            account_info = self.kiwoom_client.get_account_info() if self.is_connected else {}
            
            return jsonify({
                'status': 'success',
                'system_info': {
                    'name': 'Deep Learning Integrated Trading System',
                    'version': '3.0.0',
                    'architecture': '64비트',
                    'python_version': sys.version,
                    'timestamp': datetime.now().isoformat()
                },
                'kiwoom_status': {
                    'connected': self.is_connected,
                    'account_number': account_info.get('account_number', ''),
                    'balance': account_info.get('balance', 0),
                    'available_balance': account_info.get('available_balance', 0)
                },
                'dl_model_status': {
                    'trained': self.dl_model.is_trained,
                    'model_type': 'LSTM',
                    'features': ['close', 'volume', 'ma_5', 'ma_20', 'rsi']
                },
                'trading_status': {
                    'total_trades': len(self.trade_history),
                    'portfolio_size': len(self.portfolio)
                }
            })
        
        @self.app.route('/api/v1/connect', methods=['POST'])
        def connect_kiwoom():
            """키움 API 연결"""
            try:
                self.is_connected = self.kiwoom_client.connect()
                return jsonify({
                    'status': 'success',
                    'message': '키움 API 연결 성공' if self.is_connected else '키움 API 연결 실패',
                    'connected': self.is_connected
                })
            except Exception as e:
                logger.error(f"키움 API 연결 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/train_dl_model', methods=['POST'])
        def train_dl_model():
            """딥러닝 모델 훈련"""
            try:
                success = self.dl_model.train_model()
                return jsonify({
                    'status': 'success' if success else 'error',
                    'message': '딥러닝 모델 훈련 완료' if success else '딥러닝 모델 훈련 실패',
                    'trained': self.dl_model.is_trained
                })
            except Exception as e:
                logger.error(f"딥러닝 모델 훈련 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/trading/signals', methods=['GET'])
        def get_trading_signals():
            """딥러닝 기반 트레이딩 신호 조회"""
            try:
                symbol = request.args.get('symbol', '005930')
                
                # 시장 데이터 조회
                market_data = self.kiwoom_client.get_market_data(symbol)
                if not market_data:
                    return jsonify({
                        'status': 'error',
                        'message': '시장 데이터 조회 실패'
                    }), 400
                
                current_price = market_data.get('current_price', 0)
                
                # 딥러닝 예측
                predicted_price = self.dl_model.predict_price(market_data)
                dl_signal = self.dl_model.generate_signal(current_price, predicted_price)
                
                # 기술적 분석 (간단한 이동평균)
                ma_signal = 'hold'
                if 'ma_5' in market_data and 'ma_20' in market_data:
                    if market_data['ma_5'] > market_data['ma_20']:
                        ma_signal = 'buy'
                    elif market_data['ma_5'] < market_data['ma_20']:
                        ma_signal = 'sell'
                
                # 종합 신호
                signals = {
                    'dl_model': dl_signal,
                    'technical': ma_signal
                }
                
                # 가중 평균으로 종합 신호 결정
                if dl_signal == 'buy' and ma_signal == 'buy':
                    overall_signal = 'buy'
                elif dl_signal == 'sell' and ma_signal == 'sell':
                    overall_signal = 'sell'
                else:
                    overall_signal = 'hold'
                
                logger.info(f"딥러닝 트레이딩 신호 생성: {symbol} - {overall_signal}")
                
                return jsonify({
                    'status': 'success',
                    'symbol': symbol,
                    'current_price': current_price,
                    'predicted_price': predicted_price,
                    'signals': signals,
                    'overall_signal': overall_signal,
                    'confidence': 0.8 if predicted_price else 0.5
                })
                
            except Exception as e:
                logger.error(f"트레이딩 신호 생성 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/analysis', methods=['POST'])
        def perform_analysis():
            """종합 분석 실행"""
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
                
                # 딥러닝 예측
                predicted_price = self.dl_model.predict_price(market_data)
                signal = self.dl_model.generate_signal(
                    market_data.get('current_price', 0), 
                    predicted_price
                )
                
                analysis_result = {
                    'symbol': symbol,
                    'market_data': market_data,
                    'dl_prediction': {
                        'predicted_price': predicted_price,
                        'signal': signal,
                        'confidence': 0.8 if predicted_price else 0.5
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"종합 분석 완료: {symbol} - {signal}")
                
                return jsonify({
                    'status': 'success',
                    'analysis': analysis_result
                })
                
            except Exception as e:
                logger.error(f"종합 분석 실패: {e}")
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
                
                portfolio = {
                    'account_info': account_info,
                    'positions': positions,
                    'recent_trades': self.trade_history[-10:] if self.trade_history else [],
                    'total_trades': len(self.trade_history)
                }
                
                return jsonify({
                    'status': 'success',
                    'portfolio': portfolio
                })
                
            except Exception as e:
                logger.error(f"포트폴리오 조회 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/v1/execute_trade', methods=['POST'])
        def execute_trade():
            """딥러닝 기반 거래 실행"""
            try:
                data = request.get_json()
                symbol = data.get('symbol', '005930')
                quantity = data.get('quantity', 1)
                
                # 딥러닝 신호 확인
                market_data = self.kiwoom_client.get_market_data(symbol)
                if market_data:
                    predicted_price = self.dl_model.predict_price(market_data)
                    signal = self.dl_model.generate_signal(
                        market_data.get('current_price', 0), 
                        predicted_price
                    )
                    
                    # 신호에 따른 주문 실행
                    if signal == 'buy':
                        order_result = self.kiwoom_client.place_order(symbol, 'buy', quantity)
                    elif signal == 'sell':
                        order_result = self.kiwoom_client.place_order(symbol, 'sell', quantity)
                    else:
                        return jsonify({
                            'status': 'hold',
                            'message': '현재 매매 신호가 없습니다.',
                            'signal': signal
                        })
                    
                    if order_result:
                        # 거래 내역 저장
                        trade_record = {
                            'timestamp': datetime.now().isoformat(),
                            'symbol': symbol,
                            'order_type': signal,
                            'quantity': quantity,
                            'order_result': order_result,
                            'dl_prediction': predicted_price
                        }
                        self.trade_history.append(trade_record)
                        
                        logger.info(f"딥러닝 거래 실행 성공: {symbol} {signal} {quantity}주")
                        
                        return jsonify({
                            'status': 'success',
                            'message': f'딥러닝 거래 실행 성공: {symbol} {signal} {quantity}주',
                            'order_result': order_result,
                            'dl_signal': signal,
                            'predicted_price': predicted_price
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': '주문 실행 실패'
                        }), 500
                else:
                    return jsonify({
                        'status': 'error',
                        'message': '시장 데이터 조회 실패'
                    }), 400
                    
            except Exception as e:
                logger.error(f"딥러닝 거래 실행 실패: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def start(self, host: str = '0.0.0.0', port: int = 8000):
        """시스템 시작"""
        logger.info(f"딥러닝 통합 트레이딩 시스템 시작: {host}:{port}")
        
        # 키움 API 연결
        self.is_connected = self.kiwoom_client.connect()
        
        # 딥러닝 모델 훈련
        if not self.dl_model.is_trained:
            logger.info("딥러닝 모델 훈련 시작...")
            self.dl_model.train_model()
        
        self.app.run(host=host, port=port, debug=False)

def main():
    """메인 함수"""
    try:
        print("=== 딥러닝 통합 트레이딩 시스템 ===")
        print(f"Python 아키텍처: {'32비트' if sys.maxsize <= 2**32 else '64비트'}")
        print(f"Python 버전: {sys.version}")
        
        # 시스템 초기화
        system = IntegratedDeepLearningSystem()
        
        # 시스템 시작
        system.start()
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 시스템이 중지되었습니다.")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 