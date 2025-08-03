import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Input, MultiHeadAttention, LayerNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta
import logging
from typing import List, Tuple, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepLearningTradingModel:
    """딥러닝 기반 주식 예측 모델"""
    
    def __init__(self, model_type: str = 'lstm', sequence_length: int = 60, 
                 prediction_horizon: int = 5, features: List[str] = None):
        """
        Args:
            model_type: 모델 타입 ('lstm', 'gru', 'transformer')
            sequence_length: 시퀀스 길이 (과거 데이터 포인트 수)
            prediction_horizon: 예측 기간 (몇 일 후까지 예측할지)
            features: 사용할 특성들
        """
        self.model_type = model_type
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.features = features or ['close', 'volume', 'high', 'low', 'open']
        
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
        # 모델 저장 경로
        self.model_dir = 'models'
        os.makedirs(self.model_dir, exist_ok=True)
        
        # GPU 설정
        self._setup_gpu()
        
    def _setup_gpu(self):
        """GPU 설정"""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"GPU 사용 가능: {len(gpus)}개")
            else:
                logger.info("GPU 없음, CPU 사용")
        except Exception as e:
            logger.warning(f"GPU 설정 실패: {e}")
    
    def _create_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """LSTM 모델 생성"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(self.prediction_horizon, activation='linear')
        ])
        return model
    
    def _create_gru_model(self, input_shape: Tuple[int, int]) -> Model:
        """GRU 모델 생성"""
        model = Sequential([
            GRU(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            GRU(64, return_sequences=True),
            Dropout(0.2),
            GRU(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(self.prediction_horizon, activation='linear')
        ])
        return model
    
    def _create_transformer_model(self, input_shape: Tuple[int, int]) -> Model:
        """Transformer 모델 생성"""
        inputs = Input(shape=input_shape)
        
        # Multi-head attention
        attention_output = MultiHeadAttention(
            num_heads=8, key_dim=64
        )(inputs, inputs)
        attention_output = LayerNormalization(epsilon=1e-6)(attention_output + inputs)
        
        # Feed forward network
        ffn_output = Dense(256, activation='relu')(attention_output)
        ffn_output = Dense(input_shape[1])(ffn_output)
        ffn_output = LayerNormalization(epsilon=1e-6)(ffn_output + attention_output)
        
        # Global average pooling
        pooled_output = tf.keras.layers.GlobalAveragePooling1D()(ffn_output)
        
        # Output layers
        dense_output = Dense(64, activation='relu')(pooled_output)
        dense_output = Dropout(0.2)(dense_output)
        outputs = Dense(self.prediction_horizon, activation='linear')(dense_output)
        
        model = Model(inputs=inputs, outputs=outputs)
        return model
    
    def _prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """데이터 전처리"""
        # 특성 선택
        feature_data = data[self.features].values
        
        # 정규화
        scaled_data = self.scaler.fit_transform(feature_data)
        
        # 시퀀스 데이터 생성
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data) - self.prediction_horizon + 1):
            X.append(scaled_data[i-self.sequence_length:i])
            y.append(scaled_data[i:i+self.prediction_horizon, 0])  # 종가만 예측
        
        return np.array(X), np.array(y)
    
    def train(self, data: pd.DataFrame, validation_split: float = 0.2, 
              epochs: int = 100, batch_size: int = 32) -> Dict:
        """모델 학습"""
        logger.info(f"{self.model_type.upper()} 모델 학습 시작")
        
        # 데이터 준비
        X, y = self._prepare_data(data)
        logger.info(f"데이터 형태: X={X.shape}, y={y.shape}")
        
        # 모델 생성
        if self.model_type == 'lstm':
            self.model = self._create_lstm_model((X.shape[1], X.shape[2]))
        elif self.model_type == 'gru':
            self.model = self._create_gru_model((X.shape[1], X.shape[2]))
        elif self.model_type == 'transformer':
            self.model = self._create_transformer_model((X.shape[1], X.shape[2]))
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {self.model_type}")
        
        # 모델 컴파일
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # 콜백 설정
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        # 모델 학습
        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        logger.info("모델 학습 완료")
        
        return {
            'loss': history.history['loss'],
            'val_loss': history.history['val_loss'],
            'mae': history.history['mae'],
            'val_mae': history.history['val_mae']
        }
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """예측 수행"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다. train() 메서드를 먼저 호출하세요.")
        
        # 데이터 준비
        feature_data = data[self.features].values
        scaled_data = self.scaler.transform(feature_data)
        
        # 마지막 시퀀스만 사용
        last_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, len(self.features))
        
        # 예측
        predictions = self.model.predict(last_sequence)
        
        # 역정규화 (종가 기준)
        predictions_denorm = self.scaler.inverse_transform(
            np.zeros((predictions.shape[0], len(self.features)))
        )
        predictions_denorm[:, 0] = predictions.flatten()
        
        return predictions_denorm[:, 0]  # 종가만 반환
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict:
        """모델 평가"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        # 테스트 데이터 준비
        X_test, y_test = self._prepare_data(test_data)
        
        # 예측
        y_pred = self.model.predict(X_test)
        
        # 실제값 역정규화
        y_test_denorm = self.scaler.inverse_transform(
            np.zeros((y_test.shape[0], len(self.features)))
        )
        y_test_denorm[:, 0] = y_test.flatten()
        y_test_denorm = y_test_denorm[:, 0]
        
        # 예측값 역정규화
        y_pred_denorm = self.scaler.inverse_transform(
            np.zeros((y_pred.shape[0], len(self.features)))
        )
        y_pred_denorm[:, 0] = y_pred.flatten()
        y_pred_denorm = y_pred_denorm[:, 0]
        
        # 평가 지표 계산
        mse = mean_squared_error(y_test_denorm, y_pred_denorm)
        mae = mean_absolute_error(y_test_denorm, y_pred_denorm)
        rmse = np.sqrt(mse)
        
        # 수익률 예측 정확도
        actual_returns = np.diff(y_test_denorm) / y_test_denorm[:-1]
        predicted_returns = np.diff(y_pred_denorm) / y_pred_denorm[:-1]
        
        direction_accuracy = np.mean(
            (actual_returns > 0) == (predicted_returns > 0)
        )
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'direction_accuracy': direction_accuracy,
            'actual_prices': y_test_denorm,
            'predicted_prices': y_pred_denorm
        }
    
    def save_model(self, filename: str = None):
        """모델 저장"""
        if not self.is_trained:
            raise ValueError("학습된 모델이 없습니다.")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.model_type}_{timestamp}"
        
        # 모델 저장
        model_path = os.path.join(self.model_dir, f"{filename}.h5")
        self.model.save(model_path)
        
        # 스케일러 저장
        scaler_path = os.path.join(self.model_dir, f"{filename}_scaler.pkl")
        joblib.dump(self.scaler, scaler_path)
        
        # 설정 저장
        config = {
            'model_type': self.model_type,
            'sequence_length': self.sequence_length,
            'prediction_horizon': self.prediction_horizon,
            'features': self.features
        }
        config_path = os.path.join(self.model_dir, f"{filename}_config.json")
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"모델 저장 완료: {model_path}")
    
    def load_model(self, filename: str):
        """모델 로드"""
        # 모델 로드
        model_path = os.path.join(self.model_dir, f"{filename}.h5")
        self.model = tf.keras.models.load_model(model_path)
        
        # 스케일러 로드
        scaler_path = os.path.join(self.model_dir, f"{filename}_scaler.pkl")
        self.scaler = joblib.load(scaler_path)
        
        # 설정 로드
        config_path = os.path.join(self.model_dir, f"{filename}_config.json")
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.model_type = config['model_type']
        self.sequence_length = config['sequence_length']
        self.prediction_horizon = config['prediction_horizon']
        self.features = config['features']
        
        self.is_trained = True
        logger.info(f"모델 로드 완료: {model_path}")
    
    def get_trading_signals(self, data: pd.DataFrame, threshold: float = 0.02) -> Dict:
        """트레이딩 신호 생성"""
        predictions = self.predict(data)
        current_price = data['close'].iloc[-1]
        
        # 예측 수익률 계산
        predicted_return = (predictions[0] - current_price) / current_price
        
        # 신호 생성
        if predicted_return > threshold:
            signal = 'BUY'
            confidence = min(abs(predicted_return) / threshold, 1.0)
        elif predicted_return < -threshold:
            signal = 'SELL'
            confidence = min(abs(predicted_return) / threshold, 1.0)
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'predicted_return': predicted_return,
            'current_price': current_price,
            'predicted_price': predictions[0],
            'predictions': predictions
        }

class EnsembleTradingModel:
    """앙상블 딥러닝 모델"""
    
    def __init__(self, models: List[DeepLearningTradingModel]):
        self.models = models
        self.weights = None
    
    def train_ensemble(self, data: pd.DataFrame, validation_split: float = 0.2):
        """앙상블 모델 학습"""
        logger.info("앙상블 모델 학습 시작")
        
        # 각 모델 학습
        for model in self.models:
            model.train(data, validation_split)
        
        # 앙상블 가중치 최적화
        self._optimize_weights(data, validation_split)
        
        logger.info("앙상블 모델 학습 완료")
    
    def _optimize_weights(self, data: pd.DataFrame, validation_split: float):
        """앙상블 가중치 최적화"""
        # 검증 데이터로 각 모델의 성능 평가
        performances = []
        for model in self.models:
            eval_result = model.evaluate(data)
            performances.append(1 / (1 + eval_result['rmse']))  # RMSE 역수
        
        # 가중치 계산 (성능에 비례)
        total_performance = sum(performances)
        self.weights = [p / total_performance for p in performances]
        
        logger.info(f"앙상블 가중치: {self.weights}")
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """앙상블 예측"""
        predictions = []
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(data)
            predictions.append(pred * weight)
        
        return np.sum(predictions, axis=0)
    
    def get_trading_signals(self, data: pd.DataFrame, threshold: float = 0.02) -> Dict:
        """앙상블 트레이딩 신호"""
        predictions = self.predict(data)
        current_price = data['close'].iloc[-1]
        
        predicted_return = (predictions[0] - current_price) / current_price
        
        if predicted_return > threshold:
            signal = 'BUY'
            confidence = min(abs(predicted_return) / threshold, 1.0)
        elif predicted_return < -threshold:
            signal = 'SELL'
            confidence = min(abs(predicted_return) / threshold, 1.0)
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'predicted_return': predicted_return,
            'current_price': current_price,
            'predicted_price': predictions[0],
            'predictions': predictions
        }

def create_sample_data(days: int = 1000) -> pd.DataFrame:
    """샘플 데이터 생성"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
    
    # 기본 가격 시뮬레이션
    base_price = 10000
    returns = np.random.normal(0.001, 0.02, days)  # 일일 수익률
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # OHLCV 데이터 생성
    data = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    # high, low 정렬
    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    data['low'] = data[['open', 'close', 'low']].min(axis=1)
    
    return data.set_index('date')

if __name__ == "__main__":
    # 샘플 데이터 생성
    data = create_sample_data(1000)
    print("샘플 데이터 생성 완료")
    print(f"데이터 형태: {data.shape}")
    print(data.head())
    
    # LSTM 모델 테스트
    print("\n=== LSTM 모델 테스트 ===")
    lstm_model = DeepLearningTradingModel(model_type='lstm', sequence_length=30, prediction_horizon=5)
    
    # 학습/테스트 데이터 분할
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    
    # 모델 학습
    history = lstm_model.train(train_data, epochs=50)
    
    # 모델 평가
    eval_result = lstm_model.evaluate(test_data)
    print(f"테스트 결과:")
    print(f"  RMSE: {eval_result['rmse']:.2f}")
    print(f"  MAE: {eval_result['mae']:.2f}")
    print(f"  방향 정확도: {eval_result['direction_accuracy']:.2%}")
    
    # 트레이딩 신호 생성
    signals = lstm_model.get_trading_signals(test_data)
    print(f"\n트레이딩 신호:")
    print(f"  신호: {signals['signal']}")
    print(f"  신뢰도: {signals['confidence']:.2%}")
    print(f"  예측 수익률: {signals['predicted_return']:.2%}")
    
    # 모델 저장
    lstm_model.save_model("lstm_sample_model")
    
    print("\n딥러닝 모델 테스트 완료!") 