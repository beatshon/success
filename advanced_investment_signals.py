#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 투자 신호 생성 알고리즘
머신러닝, 딥러닝, 멀티팩터 분석을 통한 정교한 투자 신호 생성
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D
from tensorflow.keras.optimizers import Adam
import talib
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

class SignalType(Enum):
    """신호 타입"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WEAK_BUY = "WEAK_BUY"
    HOLD = "HOLD"
    WEAK_SELL = "WEAK_SELL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class FactorType(Enum):
    """팩터 타입"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"

@dataclass
class FactorData:
    """팩터 데이터"""
    factor_type: FactorType
    name: str
    value: float
    weight: float
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict = None

@dataclass
class AdvancedSignal:
    """고도화된 투자 신호"""
    stock_code: str
    signal_type: SignalType
    confidence: float
    score: float
    factors: List[FactorData]
    timestamp: datetime
    model_prediction: float = 0.0
    risk_level: str = "MEDIUM"
    target_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    holding_period: int = 0
    metadata: Dict = None

class AdvancedInvestmentSignals:
    """고도화된 투자 신호 생성기"""
    
    def __init__(self):
        """초기화"""
        logger.info("고도화된 투자 신호 생성기 초기화")
        
        # 모델 초기화
        self.rf_model = None
        self.gb_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        
        # 설정
        self.min_confidence = 0.6
        self.max_risk_level = 0.8
        self.lookback_period = 60
        self.prediction_horizon = 5
        
        # 팩터 가중치
        self.factor_weights = {
            FactorType.TECHNICAL: 0.25,
            FactorType.FUNDAMENTAL: 0.20,
            FactorType.SENTIMENT: 0.20,
            FactorType.MACRO: 0.15,
            FactorType.MOMENTUM: 0.15,
            FactorType.VOLATILITY: 0.05
        }
        
        # 모델 성능 추적
        self.model_performance = {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'last_updated': None
        }
        
        logger.info("고도화된 투자 신호 생성기 초기화 완료")

    def calculate_technical_factors(self, price_data: pd.DataFrame) -> List[FactorData]:
        """기술적 지표 계산"""
        try:
            factors = []
            
            if len(price_data) < 50:
                return factors
            
            # 기본 가격 데이터
            close = price_data['close'].values
            high = price_data['high'].values
            low = price_data['low'].values
            volume = price_data['volume'].values
            
            # 이동평균
            ma5 = talib.SMA(close, timeperiod=5)
            ma20 = talib.SMA(close, timeperiod=20)
            ma50 = talib.SMA(close, timeperiod=50)
            
            # RSI
            rsi = talib.RSI(close, timeperiod=14)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close)
            
            # 볼린저 밴드
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            
            # 스토캐스틱
            slowk, slowd = talib.STOCH(high, low, close)
            
            # ATR (Average True Range)
            atr = talib.ATR(high, low, close)
            
            # 현재 값들
            current_close = close[-1]
            current_ma5 = ma5[-1]
            current_ma20 = ma20[-1]
            current_ma50 = ma50[-1]
            current_rsi = rsi[-1]
            current_macd = macd[-1]
            current_macd_signal = macd_signal[-1]
            current_bb_upper = bb_upper[-1]
            current_bb_lower = bb_lower[-1]
            current_slowk = slowk[-1]
            current_atr = atr[-1]
            
            # 이동평균 신호
            if current_close > current_ma5 > current_ma20:
                ma_signal = 1.0
            elif current_close < current_ma5 < current_ma20:
                ma_signal = -1.0
            else:
                ma_signal = 0.0
            
            factors.append(FactorData(
                factor_type=FactorType.TECHNICAL,
                name="MA_SIGNAL",
                value=ma_signal,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=0.8
            ))
            
            # RSI 신호
            if current_rsi < 30:
                rsi_signal = 1.0  # 과매도
            elif current_rsi > 70:
                rsi_signal = -1.0  # 과매수
            else:
                rsi_signal = 0.0
            
            factors.append(FactorData(
                factor_type=FactorType.TECHNICAL,
                name="RSI_SIGNAL",
                value=rsi_signal,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            # MACD 신호
            if current_macd > current_macd_signal:
                macd_signal = 1.0
            else:
                macd_signal = -1.0
            
            factors.append(FactorData(
                factor_type=FactorType.TECHNICAL,
                name="MACD_SIGNAL",
                value=macd_signal,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.6
            ))
            
            # 볼린저 밴드 신호
            bb_position = (current_close - current_bb_lower) / (current_bb_upper - current_bb_lower)
            if bb_position < 0.2:
                bb_signal = 1.0  # 하단 밴드 근처
            elif bb_position > 0.8:
                bb_signal = -1.0  # 상단 밴드 근처
            else:
                bb_signal = 0.0
            
            factors.append(FactorData(
                factor_type=FactorType.TECHNICAL,
                name="BB_SIGNAL",
                value=bb_signal,
                weight=0.15,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            # 스토캐스틱 신호
            if current_slowk < 20:
                stoch_signal = 1.0
            elif current_slowk > 80:
                stoch_signal = -1.0
            else:
                stoch_signal = 0.0
            
            factors.append(FactorData(
                factor_type=FactorType.TECHNICAL,
                name="STOCH_SIGNAL",
                value=stoch_signal,
                weight=0.15,
                timestamp=datetime.now(),
                confidence=0.6
            ))
            
            return factors
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            return []

    def calculate_momentum_factors(self, price_data: pd.DataFrame) -> List[FactorData]:
        """모멘텀 팩터 계산"""
        try:
            factors = []
            
            if len(price_data) < 20:
                return factors
            
            close = price_data['close'].values
            
            # 가격 변화율
            returns = np.diff(close) / close[:-1]
            
            # 단기 모멘텀 (5일)
            short_momentum = (close[-1] - close[-6]) / close[-6] if len(close) >= 6 else 0
            
            # 중기 모멘텀 (20일)
            medium_momentum = (close[-1] - close[-21]) / close[-21] if len(close) >= 21 else 0
            
            # 장기 모멘텀 (60일)
            long_momentum = (close[-1] - close[-61]) / close[-61] if len(close) >= 61 else 0
            
            # 모멘텀 가속도
            momentum_acceleration = short_momentum - medium_momentum
            
            # 볼륨 가중 모멘텀
            volume = price_data['volume'].values
            if len(volume) >= 5:
                recent_volume_avg = np.mean(volume[-5:])
                historical_volume_avg = np.mean(volume[-20:]) if len(volume) >= 20 else recent_volume_avg
                volume_weight = recent_volume_avg / historical_volume_avg if historical_volume_avg > 0 else 1.0
                volume_weighted_momentum = short_momentum * volume_weight
            else:
                volume_weighted_momentum = short_momentum
            
            factors.append(FactorData(
                factor_type=FactorType.MOMENTUM,
                name="SHORT_MOMENTUM",
                value=short_momentum,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=0.8
            ))
            
            factors.append(FactorData(
                factor_type=FactorType.MOMENTUM,
                name="MEDIUM_MOMENTUM",
                value=medium_momentum,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=0.8
            ))
            
            factors.append(FactorData(
                factor_type=FactorType.MOMENTUM,
                name="MOMENTUM_ACCELERATION",
                value=momentum_acceleration,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            factors.append(FactorData(
                factor_type=FactorType.MOMENTUM,
                name="VOLUME_WEIGHTED_MOMENTUM",
                value=volume_weighted_momentum,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.6
            ))
            
            return factors
            
        except Exception as e:
            logger.error(f"모멘텀 팩터 계산 실패: {e}")
            return []

    def calculate_volatility_factors(self, price_data: pd.DataFrame) -> List[FactorData]:
        """변동성 팩터 계산"""
        try:
            factors = []
            
            if len(price_data) < 20:
                return factors
            
            close = price_data['close'].values
            returns = np.diff(close) / close[:-1]
            
            # 과거 변동성 (20일)
            historical_volatility = np.std(returns[-20:]) * np.sqrt(252) if len(returns) >= 20 else 0
            
            # 최근 변동성 (5일)
            recent_volatility = np.std(returns[-5:]) * np.sqrt(252) if len(returns) >= 5 else 0
            
            # 변동성 변화율
            volatility_change = (recent_volatility - historical_volatility) / historical_volatility if historical_volatility > 0 else 0
            
            # 변동성 신호 (낮은 변동성 = 매수 신호, 높은 변동성 = 매도 신호)
            if recent_volatility < historical_volatility * 0.8:
                volatility_signal = 1.0  # 변동성 감소 = 매수 신호
            elif recent_volatility > historical_volatility * 1.2:
                volatility_signal = -1.0  # 변동성 증가 = 매도 신호
            else:
                volatility_signal = 0.0
            
            factors.append(FactorData(
                factor_type=FactorType.VOLATILITY,
                name="VOLATILITY_SIGNAL",
                value=volatility_signal,
                weight=0.6,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            factors.append(FactorData(
                factor_type=FactorType.VOLATILITY,
                name="VOLATILITY_CHANGE",
                value=volatility_change,
                weight=0.4,
                timestamp=datetime.now(),
                confidence=0.6
            ))
            
            return factors
            
        except Exception as e:
            logger.error(f"변동성 팩터 계산 실패: {e}")
            return []

    def calculate_sentiment_factors(self, sentiment_data: Dict) -> List[FactorData]:
        """감정 팩터 계산"""
        try:
            factors = []
            
            # 뉴스 감정 점수
            news_sentiment = sentiment_data.get('news_sentiment', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.SENTIMENT,
                name="NEWS_SENTIMENT",
                value=news_sentiment,
                weight=0.4,
                timestamp=datetime.now(),
                confidence=sentiment_data.get('news_confidence', 0.5)
            ))
            
            # 소셜 미디어 감정 점수
            social_sentiment = sentiment_data.get('social_sentiment', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.SENTIMENT,
                name="SOCIAL_SENTIMENT",
                value=social_sentiment,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=sentiment_data.get('social_confidence', 0.5)
            ))
            
            # 검색 트렌드 감정 점수
            search_sentiment = sentiment_data.get('search_sentiment', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.SENTIMENT,
                name="SEARCH_SENTIMENT",
                value=search_sentiment,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=sentiment_data.get('search_confidence', 0.5)
            ))
            
            return factors
            
        except Exception as e:
            logger.error(f"감정 팩터 계산 실패: {e}")
            return []

    def calculate_macro_factors(self, macro_data: Dict) -> List[FactorData]:
        """거시경제 팩터 계산"""
        try:
            factors = []
            
            # 금리 변화
            interest_rate_change = macro_data.get('interest_rate_change', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.MACRO,
                name="INTEREST_RATE_CHANGE",
                value=interest_rate_change,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=0.8
            ))
            
            # 환율 변화
            exchange_rate_change = macro_data.get('exchange_rate_change', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.MACRO,
                name="EXCHANGE_RATE_CHANGE",
                value=exchange_rate_change,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            # 시장 지수 변화
            market_index_change = macro_data.get('market_index_change', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.MACRO,
                name="MARKET_INDEX_CHANGE",
                value=market_index_change,
                weight=0.3,
                timestamp=datetime.now(),
                confidence=0.8
            ))
            
            # 섹터 지수 변화
            sector_index_change = macro_data.get('sector_index_change', 0.0)
            factors.append(FactorData(
                factor_type=FactorType.MACRO,
                name="SECTOR_INDEX_CHANGE",
                value=sector_index_change,
                weight=0.2,
                timestamp=datetime.now(),
                confidence=0.7
            ))
            
            return factors
            
        except Exception as e:
            logger.error(f"거시경제 팩터 계산 실패: {e}")
            return []

    def train_ml_models(self, training_data: pd.DataFrame):
        """머신러닝 모델 훈련"""
        try:
            logger.info("머신러닝 모델 훈련 시작")
            
            if len(training_data) < 100:
                logger.warning("훈련 데이터가 부족합니다")
                return
            
            # 특성과 타겟 분리
            features = training_data.drop(['target', 'timestamp'], axis=1, errors='ignore')
            target = training_data['target']
            
            # 데이터 분할
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42
            )
            
            # 특성 스케일링
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 랜덤 포레스트 모델
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.rf_model.fit(X_train_scaled, y_train)
            
            # 그래디언트 부스팅 모델
            self.gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            self.gb_model.fit(X_train_scaled, y_train)
            
            # 모델 성능 평가
            rf_pred = self.rf_model.predict(X_test_scaled)
            gb_pred = self.gb_model.predict(X_test_scaled)
            
            self.model_performance['accuracy'] = accuracy_score(y_test, rf_pred)
            self.model_performance['precision'] = precision_score(y_test, rf_pred, average='weighted')
            self.model_performance['recall'] = recall_score(y_test, rf_pred, average='weighted')
            self.model_performance['f1_score'] = f1_score(y_test, rf_pred, average='weighted')
            self.model_performance['last_updated'] = datetime.now()
            
            logger.info(f"모델 훈련 완료 - 정확도: {self.model_performance['accuracy']:.3f}")
            
        except Exception as e:
            logger.error(f"머신러닝 모델 훈련 실패: {e}")

    def build_lstm_model(self, sequence_length: int = 20, n_features: int = 10):
        """LSTM 모델 구축"""
        try:
            self.lstm_model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, n_features)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1, activation='sigmoid')
            ])
            
            self.lstm_model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            logger.info("LSTM 모델 구축 완료")
            
        except Exception as e:
            logger.error(f"LSTM 모델 구축 실패: {e}")

    def generate_advanced_signal(self, stock_code: str, price_data: pd.DataFrame, 
                               sentiment_data: Dict = None, macro_data: Dict = None) -> AdvancedSignal:
        """고도화된 투자 신호 생성"""
        try:
            logger.info(f"고도화된 투자 신호 생성 시작: {stock_code}")
            
            # 모든 팩터 수집
            all_factors = []
            
            # 기술적 팩터
            technical_factors = self.calculate_technical_factors(price_data)
            all_factors.extend(technical_factors)
            
            # 모멘텀 팩터
            momentum_factors = self.calculate_momentum_factors(price_data)
            all_factors.extend(momentum_factors)
            
            # 변동성 팩터
            volatility_factors = self.calculate_volatility_factors(price_data)
            all_factors.extend(volatility_factors)
            
            # 감정 팩터
            if sentiment_data:
                sentiment_factors = self.calculate_sentiment_factors(sentiment_data)
                all_factors.extend(sentiment_factors)
            
            # 거시경제 팩터
            if macro_data:
                macro_factors = self.calculate_macro_factors(macro_data)
                all_factors.extend(macro_factors)
            
            if not all_factors:
                logger.warning(f"팩터 데이터가 없습니다: {stock_code}")
                return self._generate_default_signal(stock_code)
            
            # 종합 점수 계산
            total_score = 0.0
            total_weight = 0.0
            total_confidence = 0.0
            
            for factor in all_factors:
                weighted_score = factor.value * factor.weight * factor.confidence
                total_score += weighted_score
                total_weight += factor.weight * factor.confidence
                total_confidence += factor.confidence
            
            if total_weight > 0:
                final_score = total_score / total_weight
                final_confidence = total_confidence / len(all_factors)
            else:
                final_score = 0.0
                final_confidence = 0.0
            
            # 신호 타입 결정
            signal_type = self._determine_signal_type(final_score, final_confidence)
            
            # 리스크 레벨 계산
            risk_level = self._calculate_risk_level(all_factors)
            
            # 목표가 및 손절가 계산
            current_price = price_data['close'].iloc[-1] if len(price_data) > 0 else 0
            target_price, stop_loss, take_profit = self._calculate_price_targets(
                current_price, final_score, risk_level
            )
            
            # 보유 기간 추정
            holding_period = self._estimate_holding_period(final_score, risk_level)
            
            # 머신러닝 모델 예측
            ml_prediction = self._get_ml_prediction(all_factors) if self.rf_model else 0.0
            
            signal = AdvancedSignal(
                stock_code=stock_code,
                signal_type=signal_type,
                confidence=final_confidence,
                score=final_score,
                factors=all_factors,
                timestamp=datetime.now(),
                model_prediction=ml_prediction,
                risk_level=risk_level,
                target_price=target_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                holding_period=holding_period,
                metadata={
                    'factor_count': len(all_factors),
                    'model_performance': self.model_performance
                }
            )
            
            logger.info(f"고도화된 투자 신호 생성 완료: {stock_code} - {signal_type.value}")
            return signal
            
        except Exception as e:
            logger.error(f"고도화된 투자 신호 생성 실패 ({stock_code}): {e}")
            return self._generate_default_signal(stock_code)

    def _determine_signal_type(self, score: float, confidence: float) -> SignalType:
        """신호 타입 결정"""
        if confidence < self.min_confidence:
            return SignalType.HOLD
        
        if score > 0.6:
            return SignalType.STRONG_BUY
        elif score > 0.2:
            return SignalType.BUY
        elif score > 0.05:
            return SignalType.WEAK_BUY
        elif score < -0.6:
            return SignalType.STRONG_SELL
        elif score < -0.2:
            return SignalType.SELL
        elif score < -0.05:
            return SignalType.WEAK_SELL
        else:
            return SignalType.HOLD

    def _calculate_risk_level(self, factors: List[FactorData]) -> str:
        """리스크 레벨 계산"""
        volatility_score = 0.0
        volatility_count = 0
        
        for factor in factors:
            if factor.factor_type == FactorType.VOLATILITY:
                volatility_score += abs(factor.value)
                volatility_count += 1
        
        if volatility_count > 0:
            avg_volatility = volatility_score / volatility_count
            if avg_volatility > 0.7:
                return "HIGH"
            elif avg_volatility > 0.4:
                return "MEDIUM"
            else:
                return "LOW"
        
        return "MEDIUM"

    def _calculate_price_targets(self, current_price: float, score: float, risk_level: str) -> Tuple[float, float, float]:
        """목표가 및 손절가 계산"""
        if current_price <= 0:
            return 0.0, 0.0, 0.0
        
        # 리스크 레벨별 승률 설정
        win_rates = {
            "LOW": 0.7,
            "MEDIUM": 0.6,
            "HIGH": 0.5
        }
        
        win_rate = win_rates.get(risk_level, 0.6)
        
        # 손익비 계산 (Kelly Criterion 기반)
        if score > 0:
            # 매수 신호
            target_return = abs(score) * 0.1  # 10% 기준
            stop_loss = current_price * (1 - target_return * (1 - win_rate) / win_rate)
            target_price = current_price * (1 + target_return)
            take_profit = target_price
        else:
            # 매도 신호
            target_return = abs(score) * 0.1
            target_price = current_price * (1 - target_return)
            stop_loss = current_price * (1 + target_return * (1 - win_rate) / win_rate)
            take_profit = target_price
        
        return target_price, stop_loss, take_profit

    def _estimate_holding_period(self, score: float, risk_level: str) -> int:
        """보유 기간 추정 (일)"""
        base_period = 5  # 기본 5일
        
        # 점수에 따른 조정
        if abs(score) > 0.6:
            period_multiplier = 0.5  # 강한 신호 = 단기 보유
        elif abs(score) > 0.2:
            period_multiplier = 1.0  # 보통 신호 = 중기 보유
        else:
            period_multiplier = 2.0  # 약한 신호 = 장기 보유
        
        # 리스크 레벨에 따른 조정
        risk_multipliers = {
            "LOW": 1.5,
            "MEDIUM": 1.0,
            "HIGH": 0.7
        }
        
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        return int(base_period * period_multiplier * risk_multiplier)

    def _get_ml_prediction(self, factors: List[FactorData]) -> float:
        """머신러닝 모델 예측"""
        try:
            if not self.rf_model:
                return 0.0
            
            # 팩터를 특성 벡터로 변환
            feature_vector = []
            for factor in factors:
                feature_vector.append(factor.value)
                feature_vector.append(factor.confidence)
            
            # 특성 벡터를 DataFrame으로 변환
            feature_df = pd.DataFrame([feature_vector])
            
            # 스케일링
            feature_scaled = self.scaler.transform(feature_df)
            
            # 예측
            prediction = self.rf_model.predict_proba(feature_scaled)[0]
            
            # 매수 확률 반환
            return prediction[1] if len(prediction) > 1 else 0.0
            
        except Exception as e:
            logger.error(f"머신러닝 예측 실패: {e}")
            return 0.0

    def _generate_default_signal(self, stock_code: str) -> AdvancedSignal:
        """기본 신호 생성"""
        return AdvancedSignal(
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            confidence=0.0,
            score=0.0,
            factors=[],
            timestamp=datetime.now(),
            risk_level="MEDIUM",
            target_price=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            holding_period=0
        )

    def save_models(self, filepath: str):
        """모델 저장"""
        try:
            model_data = {
                'rf_model': self.rf_model,
                'gb_model': self.gb_model,
                'scaler': self.scaler,
                'model_performance': self.model_performance,
                'factor_weights': self.factor_weights
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"모델 저장 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")

    def load_models(self, filepath: str):
        """모델 로드"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.rf_model = model_data['rf_model']
            self.gb_model = model_data['gb_model']
            self.scaler = model_data['scaler']
            self.model_performance = model_data['model_performance']
            self.factor_weights = model_data['factor_weights']
            
            logger.info(f"모델 로드 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")

def main():
    """테스트 함수"""
    # 고도화된 투자 신호 생성기 초기화
    signal_generator = AdvancedInvestmentSignals()
    
    # 샘플 데이터 생성
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    price_data = pd.DataFrame({
        'date': dates,
        'open': np.random.normal(100, 5, len(dates)),
        'high': np.random.normal(105, 5, len(dates)),
        'low': np.random.normal(95, 5, len(dates)),
        'close': np.random.normal(100, 5, len(dates)),
        'volume': np.random.normal(1000000, 200000, len(dates))
    })
    
    # 고도화된 신호 생성
    signal = signal_generator.generate_advanced_signal(
        stock_code="005930",
        price_data=price_data,
        sentiment_data={
            'news_sentiment': 0.3,
            'social_sentiment': 0.2,
            'search_sentiment': 0.4
        },
        macro_data={
            'interest_rate_change': 0.01,
            'exchange_rate_change': -0.02,
            'market_index_change': 0.03
        }
    )
    
    print(f"생성된 신호: {signal.signal_type.value}")
    print(f"신뢰도: {signal.confidence:.3f}")
    print(f"점수: {signal.score:.3f}")
    print(f"리스크 레벨: {signal.risk_level}")
    print(f"목표가: {signal.target_price:.2f}")
    print(f"손절가: {signal.stop_loss:.2f}")
    print(f"보유 기간: {signal.holding_period}일")

if __name__ == "__main__":
    main() 