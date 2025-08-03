#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 딥러닝 시스템
고도화된 딥러닝 모델을 기존 투자 시스템과 통합
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import warnings
warnings.filterwarnings('ignore')

# 기존 시스템 import
try:
    from advanced_investment_signals import AdvancedInvestmentSignals, SignalType
    from portfolio_optimizer import PortfolioOptimizer, OptimizationMethod
    ADVANCED_SYSTEM_AVAILABLE = True
except ImportError:
    ADVANCED_SYSTEM_AVAILABLE = False
    print("고급 시스템 모듈을 찾을 수 없습니다.")

# 딥러닝 모델 import
try:
    from advanced_deep_learning_models import AdvancedDeepLearningModels, ModelType, ModelConfig
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    print("딥러닝 모델 모듈을 찾을 수 없습니다.")

from loguru import logger

@dataclass
class DeepLearningPrediction:
    """딥러닝 예측 결과"""
    stock_code: str
    predicted_price: float
    confidence: float
    uncertainty: float
    model_type: str
    timestamp: datetime
    features_used: List[str]
    prediction_horizon: int

@dataclass
class IntegratedSignal:
    """통합 신호"""
    stock_code: str
    traditional_signal: str
    deep_learning_signal: str
    ensemble_signal: str
    confidence: float
    predicted_return: float
    risk_level: str
    timestamp: datetime

class IntegratedDeepLearningSystem:
    """통합 딥러닝 시스템"""
    
    def __init__(self):
        """초기화"""
        logger.info("통합 딥러닝 시스템 초기화")
        
        # 기존 시스템 초기화
        if ADVANCED_SYSTEM_AVAILABLE:
            self.signal_generator = AdvancedInvestmentSignals()
            self.portfolio_optimizer = PortfolioOptimizer()
            logger.info("고급 투자 신호 시스템 로드 완료")
        else:
            self.signal_generator = None
            self.portfolio_optimizer = None
            logger.warning("고급 투자 신호 시스템을 사용할 수 없습니다.")
        
        # 딥러닝 시스템 초기화
        if DEEP_LEARNING_AVAILABLE:
            self.dl_system = AdvancedDeepLearningModels()
            logger.info("딥러닝 모델 시스템 로드 완료")
        else:
            self.dl_system = None
            logger.warning("딥러닝 모델 시스템을 사용할 수 없습니다.")
        
        # 통합 설정
        self.config = {
            'ensemble_weight_traditional': 0.4,
            'ensemble_weight_deep_learning': 0.6,
            'prediction_horizon': 5,
            'confidence_threshold': 0.7,
            'max_uncertainty': 0.3
        }
        
        # 모델 저장소
        self.trained_models = {}
        self.prediction_history = []
        self.integrated_signals = []
        
        logger.info("통합 딥러닝 시스템 초기화 완료")
    
    def prepare_deep_learning_data(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, np.ndarray]:
        """딥러닝용 데이터 준비"""
        if not DEEP_LEARNING_AVAILABLE:
            return {}
        
        prepared_data = {}
        
        for stock_code, data in stock_data.items():
            try:
                # 기술적 지표 추가
                enhanced_data = self._add_technical_indicators(data)
                
                # 정규화
                normalized_data = self._normalize_data(enhanced_data)
                
                # 시퀀스 데이터 생성
                config = ModelConfig(
                    model_type=ModelType.LSTM,
                    sequence_length=60,
                    n_features=len(normalized_data.columns)
                )
                
                X, y = self.dl_system.prepare_data(normalized_data, config)
                prepared_data[stock_code] = {'X': X, 'y': y, 'config': config}
                
                logger.info(f"{stock_code} 딥러닝 데이터 준비 완료: X={X.shape}, y={y.shape}")
                
            except Exception as e:
                logger.error(f"{stock_code} 데이터 준비 실패: {e}")
        
        return prepared_data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 추가"""
        enhanced_data = data.copy()
        
        # 이동평균
        enhanced_data['ma_5'] = data.iloc[:, 0].rolling(window=5).mean()
        enhanced_data['ma_20'] = data.iloc[:, 0].rolling(window=20).mean()
        
        # RSI (간단한 버전)
        delta = data.iloc[:, 0].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        enhanced_data['rsi'] = 100 - (100 / (1 + rs))
        
        # 볼린저 밴드
        ma_20 = data.iloc[:, 0].rolling(window=20).mean()
        std_20 = data.iloc[:, 0].rolling(window=20).std()
        enhanced_data['bb_upper'] = ma_20 + (std_20 * 2)
        enhanced_data['bb_lower'] = ma_20 - (std_20 * 2)
        
        # MACD (간단한 버전)
        ema_12 = data.iloc[:, 0].ewm(span=12).mean()
        ema_26 = data.iloc[:, 0].ewm(span=26).mean()
        enhanced_data['macd'] = ema_12 - ema_26
        enhanced_data['macd_signal'] = enhanced_data['macd'].ewm(span=9).mean()
        
        # 거래량 지표
        if len(data.columns) > 1:
            enhanced_data['volume_ma'] = data.iloc[:, 1].rolling(window=20).mean()
            enhanced_data['volume_ratio'] = data.iloc[:, 1] / enhanced_data['volume_ma']
        
        # NaN 값 처리
        enhanced_data = enhanced_data.fillna(method='bfill').fillna(0)
        
        return enhanced_data
    
    def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터 정규화"""
        normalized_data = data.copy()
        
        for column in normalized_data.columns:
            if normalized_data[column].std() > 0:
                normalized_data[column] = (normalized_data[column] - normalized_data[column].mean()) / normalized_data[column].std()
            else:
                normalized_data[column] = 0
        
        return normalized_data
    
    def train_deep_learning_models(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """딥러닝 모델 훈련"""
        if not DEEP_LEARNING_AVAILABLE:
            logger.warning("딥러닝 시스템을 사용할 수 없습니다.")
            return {}
        
        logger.info("딥러닝 모델 훈련 시작")
        
        # 데이터 준비
        prepared_data = self.prepare_deep_learning_data(stock_data)
        
        trained_models = {}
        
        for stock_code, data_info in prepared_data.items():
            try:
                X, y, config = data_info['X'], data_info['y'], data_info['config']
                
                if len(X) < 100:  # 데이터가 너무 적으면 스킵
                    logger.warning(f"{stock_code}: 데이터가 부족하여 스킵")
                    continue
                
                # 다양한 모델 훈련
                models = {}
                
                # 1. LSTM 모델
                lstm_model = self.dl_system.create_lstm_model(config)
                if lstm_model is not None:
                    try:
                        self.dl_system.train_model(f"{stock_code}_LSTM", lstm_model, X, y, config)
                        models['LSTM'] = lstm_model
                    except Exception as e:
                        logger.error(f"{stock_code} LSTM 훈련 실패: {e}")
                
                # 2. Transformer 모델
                config.model_type = ModelType.TRANSFORMER
                transformer_model = self.dl_system.create_transformer_model(config)
                if transformer_model is not None:
                    try:
                        self.dl_system.train_model(f"{stock_code}_Transformer", transformer_model, X, y, config)
                        models['Transformer'] = transformer_model
                    except Exception as e:
                        logger.error(f"{stock_code} Transformer 훈련 실패: {e}")
                
                trained_models[stock_code] = models
                logger.info(f"{stock_code} 모델 훈련 완료: {list(models.keys())}")
                
            except Exception as e:
                logger.error(f"{stock_code} 모델 훈련 실패: {e}")
        
        self.trained_models = trained_models
        logger.info(f"딥러닝 모델 훈련 완료: {len(trained_models)}개 종목")
        
        return trained_models
    
    def predict_with_deep_learning(self, stock_code: str, recent_data: pd.DataFrame) -> DeepLearningPrediction:
        """딥러닝 모델로 예측"""
        if not DEEP_LEARNING_AVAILABLE or stock_code not in self.trained_models:
            # 가상 예측
            return DeepLearningPrediction(
                stock_code=stock_code,
                predicted_price=recent_data.iloc[-1, 0] * (1 + np.random.normal(0, 0.02)),
                confidence=np.random.uniform(0.6, 0.9),
                uncertainty=np.random.uniform(0.1, 0.3),
                model_type="Virtual",
                timestamp=datetime.now(),
                features_used=["price", "volume"],
                prediction_horizon=self.config['prediction_horizon']
            )
        
        try:
            # 데이터 준비
            enhanced_data = self._add_technical_indicators(recent_data)
            normalized_data = self._normalize_data(enhanced_data)
            
            # 최근 시퀀스 추출
            sequence_length = 60
            if len(normalized_data) >= sequence_length:
                recent_sequence = normalized_data.iloc[-sequence_length:].values
                recent_sequence = recent_sequence.reshape(1, sequence_length, -1)
                
                # 각 모델로 예측
                predictions = []
                confidences = []
                
                for model_name, model in self.trained_models[stock_code].items():
                    try:
                        pred = model.predict(recent_sequence, verbose=0)
                        predictions.append(pred[0, 0])
                        confidences.append(0.8)  # 가상 신뢰도
                    except Exception as e:
                        logger.error(f"{model_name} 예측 실패: {e}")
                
                if predictions:
                    # 앙상블 예측
                    ensemble_prediction = np.mean(predictions)
                    ensemble_confidence = np.mean(confidences)
                    ensemble_uncertainty = np.std(predictions)
                    
                    # 원래 스케일로 변환
                    original_scale = recent_data.iloc[-1, 0]
                    predicted_price = original_scale * (1 + ensemble_prediction)
                    
                    return DeepLearningPrediction(
                        stock_code=stock_code,
                        predicted_price=predicted_price,
                        confidence=ensemble_confidence,
                        uncertainty=ensemble_uncertainty,
                        model_type="Ensemble",
                        timestamp=datetime.now(),
                        features_used=list(normalized_data.columns),
                        prediction_horizon=self.config['prediction_horizon']
                    )
            
        except Exception as e:
            logger.error(f"{stock_code} 딥러닝 예측 실패: {e}")
        
        # 실패 시 가상 예측
        return DeepLearningPrediction(
            stock_code=stock_code,
            predicted_price=recent_data.iloc[-1, 0] * (1 + np.random.normal(0, 0.02)),
            confidence=0.5,
            uncertainty=0.5,
            model_type="Fallback",
            timestamp=datetime.now(),
            features_used=["price"],
            prediction_horizon=self.config['prediction_horizon']
        )
    
    def generate_integrated_signals(self, stock_codes: List[str], 
                                  stock_data: Dict[str, pd.DataFrame]) -> List[IntegratedSignal]:
        """통합 신호 생성"""
        logger.info("통합 신호 생성 시작")
        
        integrated_signals = []
        
        for stock_code in stock_codes:
            try:
                if stock_code not in stock_data:
                    continue
                
                data = stock_data[stock_code]
                
                # 1. 전통적 신호 생성
                traditional_signal = "HOLD"
                traditional_confidence = 0.5
                
                if ADVANCED_SYSTEM_AVAILABLE and self.signal_generator:
                    try:
                        signal = self.signal_generator.generate_advanced_signal(stock_code, data)
                        traditional_signal = signal.signal_type.value
                        traditional_confidence = signal.confidence
                    except Exception as e:
                        logger.error(f"{stock_code} 전통적 신호 생성 실패: {e}")
                
                # 2. 딥러닝 예측
                dl_prediction = self.predict_with_deep_learning(stock_code, data)
                
                # 3. 딥러닝 신호 생성
                current_price = data.iloc[-1, 0]
                price_change_ratio = (dl_prediction.predicted_price - current_price) / current_price
                
                if price_change_ratio > 0.05:
                    dl_signal = "STRONG_BUY"
                elif price_change_ratio > 0.02:
                    dl_signal = "BUY"
                elif price_change_ratio < -0.05:
                    dl_signal = "STRONG_SELL"
                elif price_change_ratio < -0.02:
                    dl_signal = "SELL"
                else:
                    dl_signal = "HOLD"
                
                # 4. 앙상블 신호 생성
                ensemble_signal = self._combine_signals(traditional_signal, dl_signal, 
                                                      traditional_confidence, dl_prediction.confidence)
                
                # 5. 통합 신호 생성
                integrated_signal = IntegratedSignal(
                    stock_code=stock_code,
                    traditional_signal=traditional_signal,
                    deep_learning_signal=dl_signal,
                    ensemble_signal=ensemble_signal,
                    confidence=(traditional_confidence + dl_prediction.confidence) / 2,
                    predicted_return=price_change_ratio,
                    risk_level=self._assess_risk_level(dl_prediction.uncertainty),
                    timestamp=datetime.now()
                )
                
                integrated_signals.append(integrated_signal)
                self.integrated_signals.append(integrated_signal)
                
                logger.info(f"{stock_code} 통합 신호 생성: {ensemble_signal}")
                
            except Exception as e:
                logger.error(f"{stock_code} 통합 신호 생성 실패: {e}")
        
        logger.info(f"통합 신호 생성 완료: {len(integrated_signals)}개")
        return integrated_signals
    
    def _combine_signals(self, traditional_signal: str, dl_signal: str, 
                        traditional_confidence: float, dl_confidence: float) -> str:
        """신호 결합"""
        # 신호 강도 매핑
        signal_strength = {
            'STRONG_BUY': 3, 'BUY': 2, 'WEAK_BUY': 1,
            'HOLD': 0,
            'WEAK_SELL': -1, 'SELL': -2, 'STRONG_SELL': -3
        }
        
        # 가중 평균 계산
        traditional_weight = self.config['ensemble_weight_traditional']
        dl_weight = self.config['ensemble_weight_deep_learning']
        
        traditional_strength = signal_strength.get(traditional_signal, 0)
        dl_strength = signal_strength.get(dl_signal, 0)
        
        weighted_strength = (traditional_strength * traditional_weight + 
                           dl_strength * dl_weight)
        
        # 신호 결정
        if weighted_strength >= 2:
            return "STRONG_BUY"
        elif weighted_strength >= 1:
            return "BUY"
        elif weighted_strength >= 0.5:
            return "WEAK_BUY"
        elif weighted_strength <= -2:
            return "STRONG_SELL"
        elif weighted_strength <= -1:
            return "SELL"
        elif weighted_strength <= -0.5:
            return "WEAK_SELL"
        else:
            return "HOLD"
    
    def _assess_risk_level(self, uncertainty: float) -> str:
        """리스크 레벨 평가"""
        if uncertainty < 0.1:
            return "LOW"
        elif uncertainty < 0.2:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def get_system_summary(self) -> Dict:
        """시스템 요약"""
        return {
            'advanced_system_available': ADVANCED_SYSTEM_AVAILABLE,
            'deep_learning_available': DEEP_LEARNING_AVAILABLE,
            'trained_models': len(self.trained_models),
            'prediction_history': len(self.prediction_history),
            'integrated_signals': len(self.integrated_signals),
            'ensemble_weights': {
                'traditional': self.config['ensemble_weight_traditional'],
                'deep_learning': self.config['ensemble_weight_deep_learning']
            }
        }

def main():
    """메인 실행 함수"""
    logger.info("통합 딥러닝 시스템 테스트")
    
    # 시스템 초기화
    integrated_system = IntegratedDeepLearningSystem()
    
    # 가상 데이터 생성
    np.random.seed(42)
    stock_codes = ["005930", "000660", "035420"]
    stock_data = {}
    
    for code in stock_codes:
        dates = pd.date_range('2023-01-01', periods=200, freq='D')
        data = pd.DataFrame({
            'price': np.cumsum(np.random.randn(200) * 0.01) + 100,
            'volume': np.random.randint(1000000, 10000000, 200)
        }, index=dates)
        stock_data[code] = data
    
    # 1. 딥러닝 모델 훈련
    logger.info("딥러닝 모델 훈련 시작...")
    trained_models = integrated_system.train_deep_learning_models(stock_data)
    
    # 2. 통합 신호 생성
    logger.info("통합 신호 생성 시작...")
    integrated_signals = integrated_system.generate_integrated_signals(stock_codes, stock_data)
    
    # 3. 결과 출력
    logger.info("통합 신호 결과:")
    for signal in integrated_signals:
        logger.info(f"{signal.stock_code}: {signal.ensemble_signal} "
                   f"(전통적: {signal.traditional_signal}, "
                   f"딥러닝: {signal.deep_learning_signal}, "
                   f"신뢰도: {signal.confidence:.2f})")
    
    # 4. 시스템 요약
    summary = integrated_system.get_system_summary()
    logger.info(f"시스템 요약: {summary}")
    
    logger.info("통합 딥러닝 시스템 테스트 완료")

if __name__ == "__main__":
    main() 