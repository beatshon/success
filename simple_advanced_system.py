#!/usr/bin/env python3
"""
간단한 고급 트레이딩 시스템
32비트 Python 환경에서 작동하는 버전
"""

import os
import sys
import time
import json
import logging
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleTradingModel:
    """간단한 트레이딩 모델 (딥러닝 대신 통계적 방법 사용)"""
    
    def __init__(self, name: str = "simple_model"):
        self.name = name
        self.is_trained = False
        self.performance_history = []
        
    def train(self, data: List[float]) -> Dict:
        """모델 학습 (통계적 방법)"""
        logger.info(f"{self.name} 모델 학습 시작")
        
        # 간단한 통계 계산
        mean_price = sum(data) / len(data)
        volatility = (sum((x - mean_price) ** 2 for x in data) / len(data)) ** 0.5
        
        self.mean_price = mean_price
        self.volatility = volatility
        self.is_trained = True
        
        logger.info(f"{self.name} 모델 학습 완료 - 평균: {mean_price:.2f}, 변동성: {volatility:.2f}")
        
        return {
            'mean_price': mean_price,
            'volatility': volatility,
            'training_samples': len(data)
        }
    
    def predict(self, current_price: float) -> Dict:
        """가격 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        # 간단한 예측 로직
        price_change = (current_price - self.mean_price) / self.mean_price
        predicted_return = price_change * 0.5  # 보수적 예측
        
        # 신호 생성
        if predicted_return > 0.02:
            signal = 'BUY'
            confidence = min(abs(predicted_return) / 0.02, 1.0)
        elif predicted_return < -0.02:
            signal = 'SELL'
            confidence = min(abs(predicted_return) / 0.02, 1.0)
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'predicted_return': predicted_return,
            'current_price': current_price,
            'predicted_price': current_price * (1 + predicted_return)
        }

class SimpleAnalyticsSystem:
    """간단한 분석 시스템"""
    
    def __init__(self):
        self.sentiment_scores = {}
        
    def analyze_sentiment(self, text: str) -> Dict:
        """간단한 감정 분석"""
        # 간단한 키워드 기반 감정 분석
        positive_words = ['상승', '급등', '호재', '성장', '수익', '긍정']
        negative_words = ['하락', '급락', '악재', '손실', '부정', '위험']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = 'POSITIVE'
            score = positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            sentiment = 'NEGATIVE'
            score = -negative_count / (positive_count + negative_count + 1)
        else:
            sentiment = 'NEUTRAL'
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def calculate_market_indicators(self, prices: List[float]) -> Dict:
        """시장 지표 계산"""
        if len(prices) < 2:
            return {}
        
        # 이동평균
        ma_5 = sum(prices[-5:]) / min(5, len(prices))
        ma_20 = sum(prices[-20:]) / min(20, len(prices))
        
        # 모멘텀
        momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        
        # 변동성
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r**2 for r in returns) / len(returns))**0.5 if returns else 0
        
        # RSI (간단한 버전)
        gains = sum(max(0, r) for r in returns)
        losses = sum(max(0, -r) for r in returns)
        rsi = 100 - (100 / (1 + gains / (losses + 1e-8)))
        
        return {
            'ma_5': ma_5,
            'ma_20': ma_20,
            'momentum': momentum,
            'volatility': volatility,
            'rsi': rsi,
            'trend': 'UP' if ma_5 > ma_20 else 'DOWN'
        }

class SimplePortfolioManager:
    """간단한 포트폴리오 관리자"""
    
    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        
    def calculate_position_size(self, price: float, confidence: float) -> int:
        """포지션 크기 계산"""
        max_risk = self.current_capital * 0.02  # 최대 2% 리스크
        position_value = max_risk * confidence
        return int(position_value / price)
    
    def execute_trade(self, symbol: str, signal: str, price: float, confidence: float):
        """거래 실행"""
        if signal == 'BUY' and symbol not in self.positions:
            quantity = self.calculate_position_size(price, confidence)
            if quantity > 0:
                cost = quantity * price
                if cost <= self.current_capital:
                    self.positions[symbol] = {
                        'quantity': quantity,
                        'price': price,
                        'timestamp': datetime.now()
                    }
                    self.current_capital -= cost
                    
                    self.trade_history.append({
                        'symbol': symbol,
                        'action': 'BUY',
                        'quantity': quantity,
                        'price': price,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"매수 실행: {symbol} {quantity}주 @ {price}")
        
        elif signal == 'SELL' and symbol in self.positions:
            position = self.positions[symbol]
            quantity = position['quantity']
            revenue = quantity * price
            self.current_capital += revenue
            
            # 손익 계산
            cost = quantity * position['price']
            pnl = revenue - cost
            
            del self.positions[symbol]
            
            self.trade_history.append({
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': price,
                'pnl': pnl,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"매도 실행: {symbol} {quantity}주 @ {price}, 손익: {pnl:,.0f}원")
    
    def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약"""
        total_value = self.current_capital
        for symbol, position in self.positions.items():
            # 현재 가격은 임시로 매수 가격 사용
            total_value += position['quantity'] * position['price']
        
        total_pnl = total_value - self.initial_capital
        
        return {
            'total_value': total_value,
            'current_capital': self.current_capital,
            'total_pnl': total_pnl,
            'return_percentage': (total_pnl / self.initial_capital) * 100,
            'positions': len(self.positions),
            'total_trades': len(self.trade_history)
        }

class SimpleAdvancedSystem:
    """간단한 고급 트레이딩 시스템"""
    
    def __init__(self, config_path: str = "config/system_config.json"):
        self.config = self._load_config(config_path)
        self.is_running = False
        self.start_time = None
        
        # 컴포넌트 초기화
        self.trading_model = SimpleTradingModel("simple_lstm")
        self.analytics_system = SimpleAnalyticsSystem()
        self.portfolio_manager = SimplePortfolioManager()
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_flask_routes()
        
        # 샘플 데이터
        self.sample_prices = self._generate_sample_prices()
        
        logger.info("간단한 고급 트레이딩 시스템 초기화 완료")
    
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"설정 파일 로드 완료: {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            "system": {
                "name": "Simple Advanced Trading System",
                "version": "1.0.0",
                "environment": "development"
            },
            "trading": {
                "max_positions": 5,
                "max_daily_investment": 5000000,
                "stop_loss_percentage": 0.05
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            }
        }
    
    def _generate_sample_prices(self) -> List[float]:
        """샘플 가격 데이터 생성"""
        base_price = 10000
        prices = [base_price]
        
        for _ in range(100):
            # 랜덤 워크
            change = random.uniform(-0.05, 0.05)
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        return prices
    
    def _setup_flask_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크 엔드포인트"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': self._get_uptime(),
                'system_info': {
                    'name': self.config["system"]["name"],
                    'version': self.config["system"]["version"],
                    'environment': self.config["system"]["environment"]
                }
            })
        
        @self.app.route('/ready', methods=['GET'])
        def readiness_check():
            """준비 상태 체크"""
            return jsonify({
                'ready': True,
                'components': {
                    'trading_model': self.trading_model.is_trained,
                    'analytics': True,
                    'portfolio': True
                },
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_system_status():
            """시스템 상태 조회"""
            return jsonify({
                'is_running': self.is_running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': self._get_uptime(),
                'model_status': 'trained' if self.trading_model.is_trained else 'not_trained'
            })
        
        @self.app.route('/api/v1/models/train', methods=['POST'])
        def train_models():
            """모델 학습"""
            try:
                # 샘플 데이터로 모델 학습
                self.trading_model.train(self.sample_prices)
                
                return jsonify({
                    'message': '모델 학습 완료',
                    'status': 'success',
                    'training_samples': len(self.sample_prices)
                })
                
            except Exception as e:
                logger.error(f"모델 학습 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/analysis', methods=['POST'])
        def run_analysis():
            """분석 실행"""
            try:
                data = request.get_json()
                symbols = data.get('symbols', ['AAPL', 'GOOGL'])
                
                analysis_results = {}
                for symbol in symbols:
                    # 샘플 가격 데이터 사용
                    current_price = self.sample_prices[-1]
                    
                    # 감정 분석
                    sentiment = self.analytics_system.analyze_sentiment(
                        f"{symbol} 주식이 상승하고 있습니다."
                    )
                    
                    # 시장 지표
                    indicators = self.analytics_system.calculate_market_indicators(
                        self.sample_prices[-20:]
                    )
                    
                    # 모델 예측
                    prediction = self.trading_model.predict(current_price)
                    
                    analysis_results[symbol] = {
                        'sentiment': sentiment,
                        'indicators': indicators,
                        'prediction': prediction,
                        'current_price': current_price
                    }
                
                return jsonify({
                    'analysis_results': analysis_results,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"분석 실행 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/portfolio', methods=['GET'])
        def get_portfolio():
            """포트폴리오 정보 조회"""
            try:
                portfolio = self.portfolio_manager.get_portfolio_summary()
                
                return jsonify({
                    'portfolio': portfolio,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"포트폴리오 조회 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/trading/signals', methods=['GET'])
        def get_trading_signals():
            """트레이딩 신호 조회"""
            try:
                symbols = request.args.get('symbols', 'AAPL,GOOGL').split(',')
                
                signals = {}
                for symbol in symbols:
                    current_price = self.sample_prices[-1]
                    prediction = self.trading_model.predict(current_price)
                    
                    signals[symbol] = {
                        'signal': prediction['signal'],
                        'confidence': prediction['confidence'],
                        'predicted_return': prediction['predicted_return'],
                        'current_price': current_price,
                        'timestamp': datetime.now().isoformat()
                    }
                
                return jsonify({
                    'signals': signals,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"트레이딩 신호 생성 실패: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _get_uptime(self) -> str:
        """시스템 가동 시간 계산"""
        if not self.start_time:
            return "0:00:00"
        
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    
    def start(self):
        """시스템 시작"""
        if self.is_running:
            logger.warning("시스템이 이미 실행 중입니다.")
            return
        
        logger.info("간단한 고급 트레이딩 시스템 시작")
        self.is_running = True
        self.start_time = datetime.now()
        
        # 모델 학습
        self.trading_model.train(self.sample_prices)
        
        # Flask 앱 시작
        api_config = self.config["api"]
        self.app.run(
            host=api_config["host"],
            port=api_config["port"],
            debug=api_config["debug"]
        )
    
    def stop(self):
        """시스템 중지"""
        logger.info("간단한 고급 트레이딩 시스템 중지")
        self.is_running = False

def main():
    """메인 함수"""
    try:
        # 시스템 초기화
        system = SimpleAdvancedSystem()
        
        # 시스템 시작
        system.start()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 시스템이 중지되었습니다.")
        if 'system' in locals():
            system.stop()
    except Exception as e:
        logger.error(f"시스템 실행 중 오류 발생: {e}")
        if 'system' in locals():
            system.stop()
        sys.exit(1)

if __name__ == "__main__":
    main() 