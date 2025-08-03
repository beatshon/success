#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 딥러닝 모델 시스템
LSTM, Transformer, CNN, Attention Mechanism 등을 활용한 정교한 투자 예측 모델
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import warnings
warnings.filterwarnings('ignore')

# 딥러닝 라이브러리들
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        LSTM, Dense, Dropout, Conv1D, MaxPooling1D, 
        Input, MultiHeadAttention, LayerNormalization,
        GlobalAveragePooling1D, Bidirectional, Add
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("TensorFlow가 설치되지 않았습니다. 가상 모델을 사용합니다.")

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from loguru import logger

class ModelType(Enum):
    """모델 타입"""
    LSTM = "lstm"
    BIDIRECTIONAL_LSTM = "bidirectional_lstm"
    TRANSFORMER = "transformer"
    CNN_LSTM = "cnn_lstm"
    ATTENTION_LSTM = "attention_lstm"
    ENSEMBLE = "ensemble"

@dataclass
class ModelConfig:
    """모델 설정"""
    model_type: ModelType
    sequence_length: int = 60
    n_features: int = 10
    n_targets: int = 1
    hidden_units: List[int] = None
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100

@dataclass
class ModelPerformance:
    """모델 성능"""
    model_name: str
    mse: float
    mae: float
    r2_score: float
    timestamp: datetime

class AdvancedDeepLearningModels:
    """고도화된 딥러닝 모델 시스템"""
    
    def __init__(self):
        """초기화"""
        logger.info("고도화된 딥러닝 모델 시스템 초기화")
        
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow가 없어서 가상 모델을 사용합니다.")
        
        # 모델 저장소
        self.models = {}
        self.performance_history = []
        
        # 기본 설정
        self.default_config = ModelConfig(
            model_type=ModelType.LSTM,
            sequence_length=60,
            n_features=10,
            hidden_units=[128, 64, 32],
            dropout_rate=0.2,
            learning_rate=0.001
        )
        
        logger.info("딥러닝 모델 시스템 초기화 완료")
    
    def create_lstm_model(self, config: ModelConfig) -> Any:
        """LSTM 모델 생성"""
        if not TENSORFLOW_AVAILABLE:
            return self._create_virtual_model("LSTM")
        
        model = Sequential()
        
        # 첫 번째 LSTM 레이어
        model.add(LSTM(
            units=config.hidden_units[0],
            return_sequences=True,
            input_shape=(config.sequence_length, config.n_features)
        ))
        model.add(Dropout(config.dropout_rate))
        
        # 중간 LSTM 레이어들
        for units in config.hidden_units[1:-1]:
            model.add(LSTM(units=units, return_sequences=True))
            model.add(Dropout(config.dropout_rate))
        
        # 마지막 LSTM 레이어
        model.add(LSTM(units=config.hidden_units[-1], return_sequences=False))
        model.add(Dropout(config.dropout_rate))
        
        # 출력 레이어
        model.add(Dense(config.n_targets, activation='linear'))
        
        # 컴파일
        model.compile(
            optimizer=Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def create_transformer_model(self, config: ModelConfig) -> Any:
        """Transformer 모델 생성"""
        if not TENSORFLOW_AVAILABLE:
            return self._create_virtual_model("Transformer")
        
        # 입력 레이어
        inputs = Input(shape=(config.sequence_length, config.n_features))
        
        # Multi-Head Attention 레이어
        attention_output = MultiHeadAttention(
            num_heads=8, 
            key_dim=config.n_features
        )(inputs, inputs)
        
        # Add & Norm
        attention_output = Add()([inputs, attention_output])
        attention_output = LayerNormalization(epsilon=1e-6)(attention_output)
        
        # Feed Forward Network
        ffn_output = Dense(config.hidden_units[0], activation='relu')(attention_output)
        ffn_output = Dense(config.n_features)(ffn_output)
        
        # Add & Norm
        ffn_output = Add()([attention_output, ffn_output])
        ffn_output = LayerNormalization(epsilon=1e-6)(ffn_output)
        
        # Global Average Pooling
        pooled_output = GlobalAveragePooling1D()(ffn_output)
        
        # 출력 레이어
        outputs = Dense(config.n_targets, activation='linear')(pooled_output)
        
        model = Model(inputs=inputs, outputs=outputs)
        
        # 컴파일
        model.compile(
            optimizer=Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _create_virtual_model(self, model_name: str) -> Any:
        """가상 모델 생성 (TensorFlow가 없을 때)"""
        class VirtualModel:
            def __init__(self, name):
                self.name = name
                self.is_trained = False
            
            def fit(self, *args, **kwargs):
                self.is_trained = True
                logger.info(f"{self.name} 가상 훈련 완료")
                return type('History', (), {'history': {'loss': [0.1], 'val_loss': [0.15]}})()
            
            def predict(self, X):
                return np.random.normal(0, 0.1, (X.shape[0], 1))
        
        return VirtualModel(model_name)
    
    def prepare_data(self, data: pd.DataFrame, config: ModelConfig) -> Tuple[np.ndarray, np.ndarray]:
        """데이터 준비"""
        X, y = [], []
        
        for i in range(config.sequence_length, len(data)):
            X.append(data.iloc[i-config.sequence_length:i].values)
            y.append(data.iloc[i, 0])
        
        X = np.array(X)
        y = np.array(y).reshape(-1, 1)
        
        return X, y
    
    def train_model(self, model_name: str, model: Any, X_train: np.ndarray, 
                   y_train: np.ndarray, config: ModelConfig) -> Dict:
        """모델 훈련"""
        logger.info(f"{model_name} 모델 훈련 시작")
        
        # 콜백 설정
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)
        ]
        
        # 훈련
        history = model.fit(
            X_train, y_train,
            batch_size=config.batch_size,
            epochs=config.epochs,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=1
        )
        
        # 성능 평가
        y_pred = model.predict(X_train)
        mse = mean_squared_error(y_train, y_pred)
        mae = mean_absolute_error(y_train, y_pred)
        r2 = r2_score(y_train, y_pred)
        
        performance = ModelPerformance(
            model_name=model_name,
            mse=mse,
            mae=mae,
            r2_score=r2,
            timestamp=datetime.now()
        )
        
        self.performance_history.append(performance)
        
        logger.info(f"{model_name} 모델 훈련 완료 - MSE: {mse:.6f}, MAE: {mae:.6f}, R²: {r2:.6f}")
        
        return {
            'history': history.history,
            'performance': performance
        }
    
    def get_model_summary(self) -> Dict:
        """모델 시스템 요약"""
        return {
            'total_models': len(self.models),
            'model_types': [model_type.value for model_type in ModelType],
            'performance_history': len(self.performance_history),
            'tensorflow_available': TENSORFLOW_AVAILABLE
        }

def main():
    """메인 실행 함수"""
    logger.info("고도화된 딥러닝 모델 시스템 테스트")
    
    # 시스템 초기화
    dl_system = AdvancedDeepLearningModels()
    
    # 가상 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=500, freq='D')
    data = pd.DataFrame({
        'price': np.cumsum(np.random.randn(500) * 0.01) + 100,
        'volume': np.random.randint(1000000, 10000000, 500),
        'rsi': np.random.uniform(0, 100, 500),
        'macd': np.random.randn(500),
        'bollinger': np.random.uniform(95, 105, 500)
    }, index=dates)
    
    # 모델 설정
    config = ModelConfig(
        model_type=ModelType.LSTM,
        sequence_length=30,
        n_features=5,
        hidden_units=[64, 32, 16],
        dropout_rate=0.2,
        learning_rate=0.001,
        epochs=10
    )
    
    # 데이터 준비
    X, y = dl_system.prepare_data(data, config)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # LSTM 모델 생성 및 훈련
    lstm_model = dl_system.create_lstm_model(config)
    
    try:
        dl_system.train_model("LSTM", lstm_model, X_train, y_train, config)
    except Exception as e:
        logger.error(f"LSTM 모델 훈련 실패: {e}")
    
    # Transformer 모델 생성 및 훈련
    config.model_type = ModelType.TRANSFORMER
    transformer_model = dl_system.create_transformer_model(config)
    
    try:
        dl_system.train_model("Transformer", transformer_model, X_train, y_train, config)
    except Exception as e:
        logger.error(f"Transformer 모델 훈련 실패: {e}")
    
    # 시스템 요약
    summary = dl_system.get_model_summary()
    logger.info(f"딥러닝 모델 시스템 요약: {summary}")
    
    logger.info("고도화된 딥러닝 모델 시스템 테스트 완료")

if __name__ == "__main__":
    main() 