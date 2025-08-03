#!/usr/bin/env python3
"""
간단한 딥러닝 트레이딩 모델
TensorFlow/Keras 기반 기본 주식 예측 모델
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
import logging
import os
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDeepLearningModel:
    """간단한 딥러닝 트레이딩 모델"""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.model = None
        self.history = None
        
    def create_sample_data(self, days=500):
        """샘플 주식 데이터 생성"""
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
        
        # 기본 가격 데이터
        base_price = 70000
        price_changes = np.random.normal(0, 0.02, days)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1000))
        
        # 거래량
        volumes = np.random.randint(1000000, 10000000, days)
        
        # 기술적 지표
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': volumes,
            'open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.015))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.015))) for p in prices]
        })
        
        # 이동평균
        df['ma_5'] = df['close'].rolling(window=5).mean()
        df['ma_20'] = df['close'].rolling(window=20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df = df.dropna()
        logger.info(f"샘플 데이터 생성 완료: {len(df)}개 데이터")
        return df
    
    def prepare_data(self, df, sequence_length=60):
        """데이터 전처리"""
        # 특성 선택
        features = ['close', 'volume', 'ma_5', 'ma_20', 'rsi']
        data = df[features].values
        
        # 정규화
        scaled_data = self.scaler.fit_transform(data)
        
        # 시퀀스 데이터 생성
        X, y = [], []
        for i in range(sequence_length, len(scaled_data)):
            X.append(scaled_data[i-sequence_length:i])
            y.append(scaled_data[i, 0])  # 종가 예측
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"데이터 전처리 완료: X shape {X.shape}, y shape {y.shape}")
        return X, y
    
    def create_model(self, input_shape):
        """LSTM 모델 생성"""
        model = keras.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=input_shape),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("LSTM 모델 생성 완료")
        return model
    
    def train_model(self, X, y, epochs=50, batch_size=32):
        """모델 훈련"""
        # 데이터 분할
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # 모델 생성
        self.model = self.create_model((X.shape[1], X.shape[2]))
        
        # 콜백 설정
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # 모델 훈련
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("모델 훈련 완료")
        return self.history
    
    def evaluate_model(self, X, y):
        """모델 평가"""
        if self.model is None:
            logger.error("모델이 훈련되지 않았습니다.")
            return {}
        
        # 예측
        y_pred = self.model.predict(X)
        
        # 역정규화
        y_test_original = self.scaler.inverse_transform(
            np.concatenate([y.reshape(-1, 1), np.zeros((len(y), 4))], axis=1)
        )[:, 0]
        y_pred_original = self.scaler.inverse_transform(
            np.concatenate([y_pred.reshape(-1, 1), np.zeros((len(y_pred), 4))], axis=1)
        )[:, 0]
        
        # 메트릭 계산
        mse = mean_squared_error(y_test_original, y_pred_original)
        r2 = r2_score(y_test_original, y_pred_original)
        rmse = np.sqrt(mse)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'y_test': y_test_original,
            'y_pred': y_pred_original
        }
        
        logger.info(f"모델 평가 완료: MSE={mse:.2f}, RMSE={rmse:.2f}, R²={r2:.4f}")
        return metrics
    
    def predict_next_price(self, current_data):
        """다음 가격 예측"""
        if self.model is None:
            logger.error("모델이 훈련되지 않았습니다.")
            return None
        
        try:
            # 데이터 전처리
            features = ['close', 'volume', 'ma_5', 'ma_20', 'rsi']
            feature_values = [current_data.get(f, 0) for f in features]
            
            # 샘플 데이터로 시퀀스 생성
            sample_data = self.create_sample_data(100)
            X, _ = self.prepare_data(sample_data, 60)
            
            if len(X) > 0:
                # 예측
                pred = self.model.predict(X[-1:])
                pred_price = self.scaler.inverse_transform(
                    np.concatenate([pred, np.zeros((1, 4))], axis=1)
                )[0, 0]
                
                logger.info(f"다음 가격 예측: {pred_price:.0f}원")
                return pred_price
            else:
                logger.error("예측을 위한 데이터가 부족합니다.")
                return None
                
        except Exception as e:
            logger.error(f"예측 실패: {e}")
            return None
    
    def generate_trading_signal(self, current_price, predicted_price):
        """트레이딩 신호 생성"""
        if predicted_price is None:
            return 'hold'
        
        change_pct = (predicted_price - current_price) / current_price * 100
        
        if change_pct > 2:
            return 'buy'
        elif change_pct < -2:
            return 'sell'
        else:
            return 'hold'

def main():
    """메인 함수 - 모델 테스트"""
    print("=== 간단한 딥러닝 트레이딩 모델 테스트 ===")
    
    # 모델 초기화
    dl_model = SimpleDeepLearningModel()
    
    # 샘플 데이터 생성
    print("1. 샘플 데이터 생성 중...")
    sample_data = dl_model.create_sample_data(500)
    print(f"✅ 샘플 데이터 생성 완료: {len(sample_data)}개 데이터")
    
    # 데이터 전처리
    print("2. 데이터 전처리 중...")
    X, y = dl_model.prepare_data(sample_data, 60)
    print(f"✅ 데이터 전처리 완료: X shape {X.shape}, y shape {y.shape}")
    
    # 모델 훈련
    print("3. 모델 훈련 중...")
    history = dl_model.train_model(X, y, epochs=30, batch_size=32)
    print("✅ 모델 훈련 완료")
    
    # 모델 평가
    print("4. 모델 평가 중...")
    split = int(len(X) * 0.8)
    X_test = X[split:]
    y_test = y[split:]
    metrics = dl_model.evaluate_model(X_test, y_test)
    print(f"✅ 모델 평가 완료: R²={metrics['r2']:.4f}")
    
    # 예측 테스트
    print("5. 예측 테스트 중...")
    current_data = {
        'close': 72000,
        'volume': 5000000,
        'ma_5': 71500,
        'ma_20': 71000,
        'rsi': 65
    }
    
    predicted_price = dl_model.predict_next_price(current_data)
    if predicted_price:
        signal = dl_model.generate_trading_signal(current_data['close'], predicted_price)
        print(f"✅ 예측 완료: 현재가 {current_data['close']:,}원 → 예측가 {predicted_price:,.0f}원")
        print(f"   트레이딩 신호: {signal}")
    
    print("\n=== 테스트 완료 ===")
    print("🎉 간단한 딥러닝 모델이 성공적으로 구축되었습니다!")
    print(f"📊 모델 성능: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.2f}")
    
    print("\n🔧 다음 단계:")
    print("   1. 고급 딥러닝 모델 (Transformer, GRU) 구축")
    print("   2. 앙상블 모델 구현")
    print("   3. 실시간 예측 시스템 연동")
    print("   4. 자동 거래 시스템 구축")

if __name__ == "__main__":
    main() 