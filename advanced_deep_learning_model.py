#!/usr/bin/env python3
"""
고급 딥러닝 트레이딩 모델
TensorFlow/Keras 기반 고급 주식 예측 모델 (LSTM, GRU, Transformer, 앙상블)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import logging

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

# Scikit-learn imports
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/advanced_dl_model.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AdvancedDeepLearningModel:
    """고급 딥러닝 트레이딩 모델 클래스"""
    
    def __init__(self, config_path: str = "config/model_config.json"):
        self.config = self._load_config(config_path)
        self.scaler = MinMaxScaler()
        self.models = {}
        self.history = {}
        self.predictions = {}
        
        # GPU 설정
        self._setup_gpu()
        
        logger.info("고급 딥러닝 모델 초기화 완료")
    
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"모델 설정 파일 로드 완료: {config_path}")
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
            "model_types": ["lstm", "gru", "transformer", "ensemble"],
            "sequence_length": 60,
            "features": ["close", "volume", "ma_5", "ma_20", "rsi", "macd"],
            "lstm_config": {
                "units": [128, 64, 32],
                "dropout": 0.2,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100
            },
            "gru_config": {
                "units": [128, 64, 32],
                "dropout": 0.2,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100
            },
            "transformer_config": {
                "num_heads": 8,
                "ff_dim": 128,
                "num_transformer_blocks": 4,
                "mlp_units": [128, 64],
                "dropout": 0.1,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100
            },
            "ensemble_config": {
                "weights": [0.4, 0.3, 0.3],
                "voting_method": "weighted_average"
            }
        }
    
    def _setup_gpu(self):
        """GPU 설정"""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"GPU 설정 완료: {len(gpus)}개 GPU 사용 가능")
            else:
                logger.info("GPU가 없습니다. CPU를 사용합니다.")
        except Exception as e:
            logger.warning(f"GPU 설정 실패: {e}")
    
    def create_sample_data(self, symbol: str = "005930", days: int = 1000) -> pd.DataFrame:
        """샘플 주식 데이터 생성"""
        try:
            np.random.seed(42)
            dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
            
            # 기본 가격 데이터 생성
            base_price = 70000
            price_changes = np.random.normal(0, 0.02, days)
            prices = [base_price]
            
            for change in price_changes[1:]:
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, 1000))  # 최소 가격 보장
            
            # 거래량 생성
            volumes = np.random.randint(1000000, 10000000, days)
            
            # 기술적 지표 계산
            df = pd.DataFrame({
                'date': dates,
                'close': prices,
                'volume': volumes,
                'open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
                'high': [p * (1 + abs(np.random.normal(0, 0.015))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.015))) for p in prices]
            })
            
            # 이동평균 계산
            df['ma_5'] = df['close'].rolling(window=5).mean()
            df['ma_20'] = df['close'].rolling(window=20).mean()
            
            # RSI 계산
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD 계산
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            # NaN 값 제거
            df = df.dropna()
            
            logger.info(f"샘플 데이터 생성 완료: {symbol}, {len(df)}개 데이터")
            return df
            
        except Exception as e:
            logger.error(f"샘플 데이터 생성 실패: {e}")
            return pd.DataFrame()
    
    def prepare_data(self, df: pd.DataFrame, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """데이터 전처리 및 시퀀스 생성"""
        try:
            # 특성 선택
            features = self.config.get('features', ['close', 'volume', 'ma_5', 'ma_20', 'rsi', 'macd'])
            feature_data = df[features].values
            
            # 정규화
            scaled_data = self.scaler.fit_transform(feature_data)
            
            # 시퀀스 데이터 생성
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i])
                y.append(scaled_data[i, 0])  # 종가 예측
            
            X = np.array(X)
            y = np.array(y)
            
            logger.info(f"데이터 전처리 완료: X shape {X.shape}, y shape {y.shape}")
            return X, y
            
        except Exception as e:
            logger.error(f"데이터 전처리 실패: {e}")
            return np.array([]), np.array([])
    
    def create_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """LSTM 모델 생성"""
        try:
            config = self.config.get('lstm_config', {})
            
            model = Sequential([
                LSTM(units=config.get('units', [128])[0], 
                     return_sequences=True, 
                     input_shape=input_shape),
                Dropout(config.get('dropout', 0.2)),
                
                LSTM(units=config.get('units', [128, 64])[1], 
                     return_sequences=True),
                Dropout(config.get('dropout', 0.2)),
                
                LSTM(units=config.get('units', [128, 64, 32])[2]),
                Dropout(config.get('dropout', 0.2)),
                
                Dense(32, activation='relu'),
                Dense(1, activation='linear')
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=config.get('learning_rate', 0.001)),
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("LSTM 모델 생성 완료")
            return model
            
        except Exception as e:
            logger.error(f"LSTM 모델 생성 실패: {e}")
            return None
    
    def create_gru_model(self, input_shape: Tuple[int, int]) -> Model:
        """GRU 모델 생성"""
        try:
            config = self.config.get('gru_config', {})
            
            model = Sequential([
                layers.GRU(units=config.get('units', [128])[0], 
                          return_sequences=True, 
                          input_shape=input_shape),
                Dropout(config.get('dropout', 0.2)),
                
                layers.GRU(units=config.get('units', [128, 64])[1], 
                          return_sequences=True),
                Dropout(config.get('dropout', 0.2)),
                
                layers.GRU(units=config.get('units', [128, 64, 32])[2]),
                Dropout(config.get('dropout', 0.2)),
                
                Dense(32, activation='relu'),
                Dense(1, activation='linear')
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=config.get('learning_rate', 0.001)),
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("GRU 모델 생성 완료")
            return model
            
        except Exception as e:
            logger.error(f"GRU 모델 생성 실패: {e}")
            return None
    
    def create_transformer_model(self, input_shape: Tuple[int, int]) -> Model:
        """Transformer 모델 생성"""
        try:
            config = self.config.get('transformer_config', {})
            
            def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
                # Multi-head attention
                attention_output = layers.MultiHeadAttention(
                    num_heads=num_heads, key_dim=head_size, dropout=dropout
                )(inputs, inputs)
                attention_output = layers.Dropout(dropout)(attention_output)
                attention_output = layers.LayerNormalization(epsilon=1e-6)(inputs + attention_output)
                
                # Feed-forward network
                ffn_output = layers.Dense(ff_dim, activation="relu")(attention_output)
                ffn_output = layers.Dense(inputs.shape[-1])(ffn_output)
                ffn_output = layers.Dropout(dropout)(ffn_output)
                ffn_output = layers.LayerNormalization(epsilon=1e-6)(attention_output + ffn_output)
                
                return ffn_output
            
            inputs = layers.Input(shape=input_shape)
            x = inputs
            
            # Transformer blocks
            for _ in range(config.get('num_transformer_blocks', 4)):
                x = transformer_encoder(
                    x, 
                    head_size=config.get('num_heads', 8), 
                    num_heads=config.get('num_heads', 8), 
                    ff_dim=config.get('ff_dim', 128), 
                    dropout=config.get('dropout', 0.1)
                )
            
            # Global average pooling
            x = layers.GlobalAveragePooling1D()(x)
            
            # MLP layers
            for dim in config.get('mlp_units', [128, 64]):
                x = layers.Dense(dim, activation="relu")(x)
                x = layers.Dropout(config.get('dropout', 0.1))(x)
            
            outputs = layers.Dense(1, activation="linear")(x)
            
            model = Model(inputs=inputs, outputs=outputs)
            model.compile(
                optimizer=Adam(learning_rate=config.get('learning_rate', 0.001)),
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("Transformer 모델 생성 완료")
            return model
            
        except Exception as e:
            logger.error(f"Transformer 모델 생성 실패: {e}")
            return None
    
    def train_model(self, model: Model, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray, model_name: str) -> Dict:
        """모델 훈련"""
        try:
            config = self.config.get(f"{model_name}_config", {})
            
            # 콜백 설정
            callbacks_list = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7),
                ModelCheckpoint(
                    f'models/{model_name}_best.h5',
                    monitor='val_loss',
                    save_best_only=True,
                    verbose=1
                )
            ]
            
            # 모델 훈련
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=config.get('epochs', 100),
                batch_size=config.get('batch_size', 32),
                callbacks=callbacks_list,
                verbose=1
            )
            
            self.history[model_name] = history.history
            logger.info(f"{model_name} 모델 훈련 완료")
            
            return history.history
            
        except Exception as e:
            logger.error(f"{model_name} 모델 훈련 실패: {e}")
            return {}
    
    def evaluate_model(self, model: Model, X_test: np.ndarray, y_test: np.ndarray, 
                      model_name: str) -> Dict:
        """모델 평가"""
        try:
            # 예측
            y_pred = model.predict(X_test)
            
            # 역정규화
            y_test_original = self.scaler.inverse_transform(
                np.concatenate([y_test.reshape(-1, 1), np.zeros((len(y_test), len(self.config['features'])-1))], axis=1)
            )[:, 0]
            y_pred_original = self.scaler.inverse_transform(
                np.concatenate([y_pred.reshape(-1, 1), np.zeros((len(y_pred), len(self.config['features'])-1))], axis=1)
            )[:, 0]
            
            # 메트릭 계산
            mse = mean_squared_error(y_test_original, y_pred_original)
            mae = mean_absolute_error(y_test_original, y_pred_original)
            r2 = r2_score(y_test_original, y_pred_original)
            
            # 예측 결과 저장
            self.predictions[model_name] = {
                'y_test': y_test_original,
                'y_pred': y_pred_original,
                'metrics': {
                    'mse': mse,
                    'mae': mae,
                    'r2': r2,
                    'rmse': np.sqrt(mse)
                }
            }
            
            logger.info(f"{model_name} 모델 평가 완료: MSE={mse:.2f}, MAE={mae:.2f}, R²={r2:.4f}")
            
            return self.predictions[model_name]['metrics']
            
        except Exception as e:
            logger.error(f"{model_name} 모델 평가 실패: {e}")
            return {}
    
    def create_ensemble_model(self, models: Dict[str, Model], X_test: np.ndarray) -> np.ndarray:
        """앙상블 모델 생성"""
        try:
            config = self.config.get('ensemble_config', {})
            weights = config.get('weights', [0.4, 0.3, 0.3])
            voting_method = config.get('voting_method', 'weighted_average')
            
            predictions = []
            for model_name, model in models.items():
                pred = model.predict(X_test)
                predictions.append(pred.flatten())
            
            predictions = np.array(predictions)
            
            if voting_method == 'weighted_average':
                ensemble_pred = np.average(predictions, axis=0, weights=weights)
            else:
                ensemble_pred = np.mean(predictions, axis=0)
            
            logger.info("앙상블 모델 생성 완료")
            return ensemble_pred
            
        except Exception as e:
            logger.error(f"앙상블 모델 생성 실패: {e}")
            return np.array([])
    
    def generate_trading_signals(self, symbol: str, current_data: Dict) -> Dict:
        """트레이딩 신호 생성"""
        try:
            # 현재 데이터로 예측
            predictions = {}
            for model_name, model in self.models.items():
                if model is not None:
                    # 데이터 전처리
                    features = self.config.get('features', ['close', 'volume', 'ma_5', 'ma_20', 'rsi', 'macd'])
                    feature_values = [current_data.get(f, 0) for f in features]
                    
                    # 시퀀스 데이터 생성 (샘플 데이터 사용)
                    sample_data = self.create_sample_data(symbol, 100)
                    X, _ = self.prepare_data(sample_data, self.config.get('sequence_length', 60))
                    
                    if len(X) > 0:
                        # 예측
                        pred = model.predict(X[-1:])
                        pred_price = self.scaler.inverse_transform(
                            np.concatenate([pred, np.zeros((1, len(features)-1))], axis=1)
                        )[0, 0]
                        predictions[model_name] = pred_price
            
            # 앙상블 예측
            if len(predictions) > 1:
                weights = self.config.get('ensemble_config', {}).get('weights', [0.4, 0.3, 0.3])
                ensemble_pred = np.average(list(predictions.values()), weights=weights[:len(predictions)])
                predictions['ensemble'] = ensemble_pred
            
            # 신호 생성
            current_price = current_data.get('close', 0)
            signals = {}
            
            for model_name, pred_price in predictions.items():
                if current_price > 0:
                    change_pct = (pred_price - current_price) / current_price * 100
                    
                    if change_pct > 2:
                        signals[model_name] = 'buy'
                    elif change_pct < -2:
                        signals[model_name] = 'sell'
                    else:
                        signals[model_name] = 'hold'
                else:
                    signals[model_name] = 'hold'
            
            # 종합 신호
            buy_count = sum(1 for signal in signals.values() if signal == 'buy')
            sell_count = sum(1 for signal in signals.values() if signal == 'sell')
            
            if buy_count > sell_count:
                overall_signal = 'buy'
            elif sell_count > buy_count:
                overall_signal = 'sell'
            else:
                overall_signal = 'hold'
            
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'predictions': predictions,
                'signals': signals,
                'overall_signal': overall_signal,
                'confidence': max(buy_count, sell_count) / len(signals) if signals else 0
            }
            
            logger.info(f"트레이딩 신호 생성 완료: {symbol} - {overall_signal}")
            return result
            
        except Exception as e:
            logger.error(f"트레이딩 신호 생성 실패: {e}")
            return {
                'symbol': symbol,
                'current_price': 0,
                'predictions': {},
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0
            }
    
    def plot_results(self, model_name: str, save_path: str = None):
        """결과 시각화"""
        try:
            if model_name not in self.predictions:
                logger.warning(f"{model_name} 모델의 예측 결과가 없습니다.")
                return
            
            pred_data = self.predictions[model_name]
            y_test = pred_data['y_test']
            y_pred = pred_data['y_pred']
            
            # Plotly를 사용한 인터랙티브 차트
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                y=y_test,
                mode='lines',
                name='실제 가격',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                y=y_pred,
                mode='lines',
                name='예측 가격',
                line=dict(color='red')
            ))
            
            fig.update_layout(
                title=f'{model_name} 모델 예측 결과',
                xaxis_title='시간',
                yaxis_title='가격',
                hovermode='x unified'
            )
            
            if save_path:
                fig.write_html(f"{save_path}/{model_name}_predictions.html")
                logger.info(f"차트 저장 완료: {save_path}/{model_name}_predictions.html")
            
            fig.show()
            
        except Exception as e:
            logger.error(f"결과 시각화 실패: {e}")
    
    def save_model(self, model: Model, model_name: str, save_path: str = "models"):
        """모델 저장"""
        try:
            os.makedirs(save_path, exist_ok=True)
            model.save(f"{save_path}/{model_name}.h5")
            logger.info(f"모델 저장 완료: {save_path}/{model_name}.h5")
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
    
    def load_model(self, model_name: str, load_path: str = "models") -> Model:
        """모델 로드"""
        try:
            model_path = f"{load_path}/{model_name}.h5"
            if os.path.exists(model_path):
                model = keras.models.load_model(model_path)
                logger.info(f"모델 로드 완료: {model_path}")
                return model
            else:
                logger.warning(f"모델 파일이 없습니다: {model_path}")
                return None
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return None

def main():
    """메인 함수 - 모델 테스트"""
    try:
        print("=== 고급 딥러닝 트레이딩 모델 테스트 ===")
        
        # 모델 초기화
        dl_model = AdvancedDeepLearningModel()
        
        # 샘플 데이터 생성
        print("1. 샘플 데이터 생성 중...")
        sample_data = dl_model.create_sample_data("005930", 1000)
        
        if sample_data.empty:
            print("❌ 샘플 데이터 생성 실패")
            return
        
        print(f"✅ 샘플 데이터 생성 완료: {len(sample_data)}개 데이터")
        
        # 데이터 전처리
        print("2. 데이터 전처리 중...")
        X, y = dl_model.prepare_data(sample_data, 60)
        
        if len(X) == 0:
            print("❌ 데이터 전처리 실패")
            return
        
        print(f"✅ 데이터 전처리 완료: X shape {X.shape}, y shape {y.shape}")
        
        # 데이터 분할
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
        
        print(f"✅ 데이터 분할 완료: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")
        
        # 모델 생성 및 훈련
        models_to_train = ['lstm', 'gru', 'transformer']
        
        for model_type in models_to_train:
            print(f"3. {model_type.upper()} 모델 훈련 중...")
            
            if model_type == 'lstm':
                model = dl_model.create_lstm_model((X_train.shape[1], X_train.shape[2]))
            elif model_type == 'gru':
                model = dl_model.create_gru_model((X_train.shape[1], X_train.shape[2]))
            elif model_type == 'transformer':
                model = dl_model.create_transformer_model((X_train.shape[1], X_train.shape[2]))
            
            if model is not None:
                dl_model.models[model_type] = model
                
                # 모델 훈련
                history = dl_model.train_model(model, X_train, y_train, X_val, y_val, model_type)
                
                # 모델 평가
                metrics = dl_model.evaluate_model(model, X_test, y_test, model_type)
                
                print(f"✅ {model_type.upper()} 모델 완료: R²={metrics.get('r2', 0):.4f}")
            else:
                print(f"❌ {model_type.upper()} 모델 생성 실패")
        
        # 앙상블 모델
        print("4. 앙상블 모델 생성 중...")
        if len(dl_model.models) > 1:
            ensemble_pred = dl_model.create_ensemble_model(dl_model.models, X_test)
            if len(ensemble_pred) > 0:
                # 앙상블 평가
                y_test_original = dl_model.scaler.inverse_transform(
                    np.concatenate([y_test.reshape(-1, 1), np.zeros((len(y_test), len(dl_model.config['features'])-1))], axis=1)
                )[:, 0]
                
                ensemble_metrics = {
                    'mse': mean_squared_error(y_test_original, ensemble_pred),
                    'mae': mean_absolute_error(y_test_original, ensemble_pred),
                    'r2': r2_score(y_test_original, ensemble_pred)
                }
                
                print(f"✅ 앙상블 모델 완료: R²={ensemble_metrics['r2']:.4f}")
        
        # 트레이딩 신호 생성 테스트
        print("5. 트레이딩 신호 생성 테스트...")
        current_data = {
            'close': 72000,
            'volume': 5000000,
            'ma_5': 71500,
            'ma_20': 71000,
            'rsi': 65,
            'macd': 500
        }
        
        signals = dl_model.generate_trading_signals("005930", current_data)
        print(f"✅ 트레이딩 신호 생성 완료: {signals['overall_signal']}")
        
        print("\n=== 테스트 완료 ===")
        print("🎉 고급 딥러닝 모델이 성공적으로 구축되었습니다!")
        print("\n📊 모델 성능:")
        for model_name, pred_data in dl_model.predictions.items():
            metrics = pred_data['metrics']
            print(f"   • {model_name.upper()}: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.2f}")
        
        print("\n🔧 다음 단계:")
        print("   1. 실시간 예측 시스템 구축")
        print("   2. 자동 거래 시스템 연동")
        print("   3. 성능 모니터링 및 최적화")
        print("   4. 클라우드 배포")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류 발생: {e}")
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main() 