#!/usr/bin/env python3
"""
통합 고급 트레이딩 시스템
딥러닝 모델, 고급 분석, 클라우드 배포를 통합한 완전한 시스템
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

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

# 필요한 모듈들 import
try:
    import numpy as np
    import pandas as pd
    from flask import Flask, jsonify, request
    
    # 커스텀 모듈들
    from deep_learning_trading_model import DeepLearningTradingModel
    from advanced_analytics_system import AdvancedAnalyticsSystem
    
except ImportError as e:
    logger.error(f"필요한 모듈을 import할 수 없습니다: {e}")
    logger.info("requirements_advanced.txt를 설치해주세요: pip install -r requirements_advanced.txt")
    sys.exit(1)

class IntegratedAdvancedSystem:
    """통합 고급 트레이딩 시스템"""
    
    def __init__(self, config_path: str = "config/system_config.json"):
        self.config = self._load_config(config_path)
        self.is_running = False
        self.start_time = None
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self._setup_flask_routes()
        
        logger.info("통합 고급 트레이딩 시스템 초기화 완료")
    
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
                "name": "Integrated Advanced Trading System",
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "log_level": os.getenv("LOG_LEVEL", "INFO")
            },
            "trading": {
                "max_positions": 10,
                "max_daily_investment": 10000000,
                "max_single_investment": 2000000,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.10
            },
            "models": {
                "lstm": {
                    "sequence_length": 60,
                    "prediction_horizon": 5,
                    "epochs": 100,
                    "batch_size": 32
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": int(os.getenv("API_PORT", "8000")),
                "debug": os.getenv("FLASK_DEBUG", "False").lower() == "true"
            }
        }
    
    def _initialize_components(self):
        """시스템 컴포넌트 초기화"""
        logger.info("시스템 컴포넌트 초기화 시작")
        
        try:
            # 딥러닝 모델 초기화
            self.dl_model = DeepLearningTradingModel(
                model_type='lstm',
                sequence_length=self.config["models"]["lstm"]["sequence_length"],
                prediction_horizon=self.config["models"]["lstm"]["prediction_horizon"]
            )
            
            # 고급 분석 시스템 초기화
            self.analytics_system = AdvancedAnalyticsSystem()
            
            logger.info("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")
            raise
    
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
            components_status = {
                'models': self.dl_model is not None,
                'analytics': self.analytics_system is not None
            }
            
            is_ready = all(components_status.values())
            
            return jsonify({
                'ready': is_ready,
                'components': components_status,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_system_status():
            """시스템 상태 조회"""
            return jsonify({
                'is_running': self.is_running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': self._get_uptime(),
                'model_status': 'initialized'
            })
        
        @self.app.route('/api/v1/models/train', methods=['POST'])
        def train_models():
            """모델 학습"""
            try:
                data = request.get_json()
                model_type = data.get('model_type', 'lstm')
                
                if model_type == 'lstm':
                    self._train_model_async()
                    message = "LSTM 모델 학습 시작"
                else:
                    return jsonify({'error': '지원하지 않는 모델 타입'}), 400
                
                return jsonify({'message': message, 'status': 'started'})
            
        except Exception as e:
                logger.error(f"모델 학습 요청 실패: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/analysis', methods=['POST'])
        def run_analysis():
            """고급 분석 실행"""
            try:
                data = request.get_json()
                symbols = data.get('symbols', ['AAPL', 'GOOGL'])
                
                # 분석 실행
                analysis_results = self._run_comprehensive_analysis(symbols)
                
                return jsonify({
                    'analysis_results': analysis_results,
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
                logger.error(f"분석 실행 실패: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _get_uptime(self) -> str:
        """시스템 가동 시간 계산"""
        if not self.start_time:
            return "0:00:00"
        
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _train_model_async(self):
        """비동기 모델 학습"""
        def train_worker():
            try:
                logger.info("LSTM 모델 학습 시작")
                
                # 샘플 데이터로 학습
                sample_data = self._generate_sample_data()
                
                # 모델 학습
                history = self.dl_model.train(
                    sample_data,
                    epochs=self.config["models"]["lstm"]["epochs"],
                    batch_size=self.config["models"]["lstm"]["batch_size"]
                )
                
                # 모델 저장
                self.dl_model.save_model("lstm_trained")
                
                logger.info("LSTM 모델 학습 완료")
            
        except Exception as e:
                logger.error(f"LSTM 모델 학습 실패: {e}")
        
        # 별도 스레드에서 학습 실행
        thread = threading.Thread(target=train_worker)
        thread.daemon = True
        thread.start()
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """샘플 데이터 생성"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=1000, freq='D')
        
        data = pd.DataFrame({
            'open': np.random.normal(100, 10, 1000).cumsum() + 1000,
            'high': np.random.normal(105, 12, 1000).cumsum() + 1000,
            'low': np.random.normal(95, 8, 1000).cumsum() + 1000,
            'close': np.random.normal(100, 10, 1000).cumsum() + 1000,
            'volume': np.random.randint(1000000, 10000000, 1000)
        }, index=dates)
        
        return data
    
    def _run_comprehensive_analysis(self, symbols: List[str]) -> Dict:
        """종합 분석 실행"""
        analysis_results = {}
        
        for symbol in symbols:
            try:
                # 시장 데이터 수집
                market_data = self._get_market_data(symbol)
                
                if market_data is not None and not market_data.empty:
                    # 고급 분석 실행
                    analysis = self.analytics_system.comprehensive_analysis(
                        market_data=market_data,
                        news_data=self._get_news_data(symbol),
                        portfolio=self._get_portfolio_for_symbol(symbol)
                    )
                    
                    analysis_results[symbol] = analysis
                    
                except Exception as e:
                logger.error(f"{symbol} 분석 실패: {e}")
                analysis_results[symbol] = {'error': str(e)}
            
        return analysis_results
            
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """시장 데이터 수집"""
        try:
            # 샘플 데이터 반환
            return self._generate_sample_data()
        except Exception as e:
            logger.error(f"{symbol} 시장 데이터 수집 실패: {e}")
            return None
    
    def _get_news_data(self, symbol: str) -> List[Dict]:
        """뉴스 데이터 수집"""
        return [
            {
                'id': 1,
                'title': f'{symbol} 관련 긍정적 뉴스',
                'content': f'{symbol}의 실적이 예상보다 좋습니다.',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def _get_portfolio_for_symbol(self, symbol: str) -> Dict:
        """특정 종목의 포트폴리오 정보"""
        return {
            symbol: {
                'quantity': 100,
                'price': 1000,
                'current_value': 100000
            }
        }
    
    def start(self):
        """시스템 시작"""
        if self.is_running:
            logger.warning("시스템이 이미 실행 중입니다.")
                return
            
        logger.info("통합 고급 트레이딩 시스템 시작")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Flask 앱 시작
        api_config = self.config["api"]
        self.app.run(
            host=api_config["host"],
            port=api_config["port"],
            debug=api_config["debug"]
        )
    
    def stop(self):
        """시스템 중지"""
        logger.info("통합 고급 트레이딩 시스템 중지")
        self.is_running = False

def main():
    """메인 함수"""
    try:
        # 시스템 초기화
    system = IntegratedAdvancedSystem()
    
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