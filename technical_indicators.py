#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기술적 지표 계산 모듈
트레이딩 전략에서 사용하는 다양한 기술적 지표들을 계산합니다.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from loguru import logger

def calculate_sma(prices: List[float], period: int) -> List[float]:
    """
    단순 이동평균 (Simple Moving Average) 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간
        
    Returns:
        이동평균 리스트
    """
    if len(prices) < period:
        return []
    
    sma_values = []
    for i in range(period - 1, len(prices)):
        sma = np.mean(prices[i - period + 1:i + 1])
        sma_values.append(sma)
    
    return sma_values

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    지수 이동평균 (Exponential Moving Average) 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간
        
    Returns:
        지수 이동평균 리스트
    """
    if len(prices) < period:
        return []
    
    # 가중치 계산
    alpha = 2.0 / (period + 1)
    
    ema_values = []
    # 첫 번째 EMA는 SMA로 계산
    first_ema = np.mean(prices[:period])
    ema_values.append(first_ema)
    
    # 나머지 EMA 계산
    for i in range(period, len(prices)):
        ema = alpha * prices[i] + (1 - alpha) * ema_values[-1]
        ema_values.append(ema)
    
    return ema_values

def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    상대강도지수 (Relative Strength Index) 계산
    
    Args:
        prices: 가격 리스트
        period: RSI 계산 기간 (기본값: 14)
        
    Returns:
        RSI 값 리스트
    """
    if len(prices) < period + 1:
        return []
    
    # 가격 변화 계산
    deltas = np.diff(prices)
    
    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    rsi_values = []
    
    # 첫 번째 평균 계산
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
    
    # 나머지 RSI 계산 (지수 이동평균 방식)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
    
    return rsi_values

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
    """
    볼린저 밴드 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간 (기본값: 20)
        std_dev: 표준편차 배수 (기본값: 2.0)
        
    Returns:
        볼린저 밴드 데이터 (상단, 중간, 하단)
    """
    if len(prices) < period:
        return {}
    
    # 중간선 (SMA)
    middle = calculate_sma(prices, period)
    
    if not middle:
        return {}
    
    # 표준편차 계산
    upper = []
    lower = []
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        std = np.std(window)
        sma = np.mean(window)
        
        upper.append(sma + (std_dev * std))
        lower.append(sma - (std_dev * std))
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
    """
    MACD (Moving Average Convergence Divergence) 계산
    
    Args:
        prices: 가격 리스트
        fast_period: 빠른 EMA 기간 (기본값: 12)
        slow_period: 느린 EMA 기간 (기본값: 26)
        signal_period: 시그널선 기간 (기본값: 9)
        
    Returns:
        MACD 데이터 (MACD, 시그널, 히스토그램)
    """
    if len(prices) < slow_period + signal_period:
        return {}
    
    # EMA 계산
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    if not fast_ema or not slow_ema:
        return {}
    
    # MACD 라인 계산 (빠른 EMA - 느린 EMA)
    macd_line = []
    min_length = min(len(fast_ema), len(slow_ema))
    
    for i in range(min_length):
        macd = fast_ema[i] - slow_ema[i]
        macd_line.append(macd)
    
    # 시그널 라인 계산 (MACD의 EMA)
    signal_line = calculate_ema(macd_line, signal_period)
    
    if not signal_line:
        return {}
    
    # 히스토그램 계산 (MACD - 시그널)
    histogram = []
    min_length = min(len(macd_line), len(signal_line))
    
    for i in range(min_length):
        hist = macd_line[i] - signal_line[i]
        histogram.append(hist)
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_stochastic(prices: List[float], high_prices: List[float], low_prices: List[float], 
                        k_period: int = 14, d_period: int = 3) -> Dict[str, List[float]]:
    """
    스토캐스틱 계산
    
    Args:
        prices: 종가 리스트
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        k_period: %K 계산 기간 (기본값: 14)
        d_period: %D 계산 기간 (기본값: 3)
        
    Returns:
        스토캐스틱 데이터 (%K, %D)
    """
    if len(prices) < k_period or len(high_prices) < k_period or len(low_prices) < k_period:
        return {}
    
    k_values = []
    
    for i in range(k_period - 1, len(prices)):
        highest_high = max(high_prices[i - k_period + 1:i + 1])
        lowest_low = min(low_prices[i - k_period + 1:i + 1])
        current_close = prices[i]
        
        if highest_high == lowest_low:
            k = 50.0
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        k_values.append(k)
    
    # %D 계산 (%K의 이동평균)
    d_values = calculate_sma(k_values, d_period)
    
    return {
        'k': k_values,
        'd': d_values
    }

def calculate_atr(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                 period: int = 14) -> List[float]:
    """
    평균진폭 (Average True Range) 계산
    
    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: ATR 계산 기간 (기본값: 14)
        
    Returns:
        ATR 값 리스트
    """
    if len(high_prices) < period + 1 or len(low_prices) < period + 1 or len(close_prices) < period + 1:
        return []
    
    true_ranges = []
    
    for i in range(1, len(high_prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = close_prices[i - 1]
        
        # True Range 계산
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = max(tr1, tr2, tr3)
        true_ranges.append(true_range)
    
    # ATR 계산 (지수 이동평균 사용)
    atr_values = calculate_ema(true_ranges, period)
    
    return atr_values

def calculate_momentum(prices: List[float], period: int = 10) -> List[float]:
    """
    모멘텀 지표 계산
    
    Args:
        prices: 가격 리스트
        period: 모멘텀 계산 기간 (기본값: 10)
        
    Returns:
        모멘텀 값 리스트
    """
    if len(prices) < period:
        return []
    
    momentum_values = []
    
    for i in range(period, len(prices)):
        momentum = prices[i] - prices[i - period]
        momentum_values.append(momentum)
    
    return momentum_values

def calculate_rate_of_change(prices: List[float], period: int = 10) -> List[float]:
    """
    변화율 (Rate of Change) 계산
    
    Args:
        prices: 가격 리스트
        period: ROC 계산 기간 (기본값: 10)
        
    Returns:
        ROC 값 리스트 (%)
    """
    if len(prices) < period:
        return []
    
    roc_values = []
    
    for i in range(period, len(prices)):
        if prices[i - period] == 0:
            roc = 0.0
        else:
            roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
        roc_values.append(roc)
    
    return roc_values

def calculate_williams_r(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                        period: int = 14) -> List[float]:
    """
    윌리엄스 %R 계산
    
    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 계산 기간 (기본값: 14)
        
    Returns:
        윌리엄스 %R 값 리스트
    """
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    williams_r_values = []
    
    for i in range(period - 1, len(high_prices)):
        highest_high = max(high_prices[i - period + 1:i + 1])
        lowest_low = min(low_prices[i - period + 1:i + 1])
        current_close = close_prices[i]
        
        if highest_high == lowest_low:
            williams_r = -50.0
        else:
            williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100
        
        williams_r_values.append(williams_r)
    
    return williams_r_values

def calculate_cci(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                 period: int = 20) -> List[float]:
    """
    CCI (Commodity Channel Index) 계산
    
    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 계산 기간 (기본값: 20)
        
    Returns:
        CCI 값 리스트
    """
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    # 전형적 가격 계산
    typical_prices = []
    for i in range(len(close_prices)):
        tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        typical_prices.append(tp)
    
    cci_values = []
    
    for i in range(period - 1, len(typical_prices)):
        window = typical_prices[i - period + 1:i + 1]
        sma = np.mean(window)
        mean_deviation = np.mean([abs(tp - sma) for tp in window])
        
        if mean_deviation == 0:
            cci = 0.0
        else:
            cci = (typical_prices[i] - sma) / (0.015 * mean_deviation)
        
        cci_values.append(cci)
    
    return cci_values

def calculate_adx(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                 period: int = 14) -> Dict[str, List[float]]:
    """
    ADX (Average Directional Index) 계산
    
    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 계산 기간 (기본값: 14)
        
    Returns:
        ADX 데이터 (ADX, +DI, -DI)
    """
    if len(high_prices) < period + 1 or len(low_prices) < period + 1 or len(close_prices) < period + 1:
        return {}
    
    # True Range 계산
    tr_values = []
    dm_plus = []
    dm_minus = []
    
    for i in range(1, len(high_prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_high = high_prices[i - 1]
        prev_low = low_prices[i - 1]
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - prev_high)
        tr3 = abs(low - prev_low)
        tr = max(tr1, tr2, tr3)
        tr_values.append(tr)
        
        # Directional Movement
        up_move = high - prev_high
        down_move = prev_low - low
        
        if up_move > down_move and up_move > 0:
            dm_plus.append(up_move)
        else:
            dm_plus.append(0)
        
        if down_move > up_move and down_move > 0:
            dm_minus.append(down_move)
        else:
            dm_minus.append(0)
    
    # Smoothed TR, +DM, -DM 계산
    tr_smoothed = calculate_ema(tr_values, period)
    dm_plus_smoothed = calculate_ema(dm_plus, period)
    dm_minus_smoothed = calculate_ema(dm_minus, period)
    
    if not tr_smoothed or not dm_plus_smoothed or not dm_minus_smoothed:
        return {}
    
    # +DI, -DI 계산
    di_plus = []
    di_minus = []
    
    min_length = min(len(tr_smoothed), len(dm_plus_smoothed), len(dm_minus_smoothed))
    
    for i in range(min_length):
        if tr_smoothed[i] == 0:
            di_plus.append(0)
            di_minus.append(0)
        else:
            di_plus.append((dm_plus_smoothed[i] / tr_smoothed[i]) * 100)
            di_minus.append((dm_minus_smoothed[i] / tr_smoothed[i]) * 100)
    
    # DX 계산
    dx_values = []
    for i in range(len(di_plus)):
        if di_plus[i] + di_minus[i] == 0:
            dx = 0
        else:
            dx = (abs(di_plus[i] - di_minus[i]) / (di_plus[i] + di_minus[i])) * 100
        dx_values.append(dx)
    
    # ADX 계산 (DX의 이동평균)
    adx_values = calculate_sma(dx_values, period)
    
    return {
        'adx': adx_values,
        'di_plus': di_plus,
        'di_minus': di_minus
    }

def calculate_obv(prices: List[float], volumes: List[float]) -> List[float]:
    """
    OBV (On-Balance Volume) 계산
    
    Args:
        prices: 가격 리스트
        volumes: 거래량 리스트
        
    Returns:
        OBV 값 리스트
    """
    if len(prices) != len(volumes) or len(prices) < 2:
        return []
    
    obv_values = [volumes[0]]  # 첫 번째 OBV는 첫 번째 거래량
    
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            obv_values.append(obv_values[-1] + volumes[i])
        elif prices[i] < prices[i - 1]:
            obv_values.append(obv_values[-1] - volumes[i])
        else:
            obv_values.append(obv_values[-1])
    
    return obv_values

def calculate_vwap(prices: List[float], volumes: List[float]) -> List[float]:
    """
    VWAP (Volume Weighted Average Price) 계산
    
    Args:
        prices: 가격 리스트
        volumes: 거래량 리스트
        
    Returns:
        VWAP 값 리스트
    """
    if len(prices) != len(volumes):
        return []
    
    vwap_values = []
    cumulative_pv = 0
    cumulative_volume = 0
    
    for i in range(len(prices)):
        cumulative_pv += prices[i] * volumes[i]
        cumulative_volume += volumes[i]
        
        if cumulative_volume == 0:
            vwap = prices[i]
        else:
            vwap = cumulative_pv / cumulative_volume
        
        vwap_values.append(vwap)
    
    return vwap_values

def calculate_support_resistance(prices: List[float], window: int = 20, threshold: float = 0.02) -> Dict[str, List[float]]:
    """
    지지선과 저항선 계산
    
    Args:
        prices: 가격 리스트
        window: 분석 윈도우 크기 (기본값: 20)
        threshold: 지지/저항 판단 임계값 (기본값: 0.02)
        
    Returns:
        지지선과 저항선 리스트
    """
    if len(prices) < window:
        return {'support': [], 'resistance': []}
    
    support_levels = []
    resistance_levels = []
    
    for i in range(window, len(prices) - window):
        current_price = prices[i]
        left_window = prices[i - window:i]
        right_window = prices[i + 1:i + window + 1]
        
        # 지지선 확인 (현재가가 양쪽 윈도우의 최소값보다 높고, 임계값 내에 있을 때)
        left_min = min(left_window)
        right_min = min(right_window)
        
        if (current_price > left_min and current_price > right_min and
            abs(current_price - left_min) / left_min < threshold and
            abs(current_price - right_min) / right_min < threshold):
            support_levels.append(current_price)
        
        # 저항선 확인 (현재가가 양쪽 윈도우의 최대값보다 낮고, 임계값 내에 있을 때)
        left_max = max(left_window)
        right_max = max(right_window)
        
        if (current_price < left_max and current_price < right_max and
            abs(current_price - left_max) / left_max < threshold and
            abs(current_price - right_max) / right_max < threshold):
            resistance_levels.append(current_price)
    
    return {
        'support': support_levels,
        'resistance': resistance_levels
    }

def calculate_fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
    """
    피보나치 되돌림 레벨 계산
    
    Args:
        high: 최고가
        low: 최저가
        
    Returns:
        피보나치 되돌림 레벨들
    """
    diff = high - low
    
    return {
        '0.0': low,
        '0.236': low + 0.236 * diff,
        '0.382': low + 0.382 * diff,
        '0.5': low + 0.5 * diff,
        '0.618': low + 0.618 * diff,
        '0.786': low + 0.786 * diff,
        '1.0': high
    }

def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    피벗 포인트 계산
    
    Args:
        high: 전일 고가
        low: 전일 저가
        close: 전일 종가
        
    Returns:
        피벗 포인트 레벨들
    """
    pivot = (high + low + close) / 3
    
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    
    return {
        'pivot': pivot,
        'r1': r1,
        'r2': r2,
        'r3': r3,
        's1': s1,
        's2': s2,
        's3': s3
    }

if __name__ == "__main__":
    # 테스트 코드
    logger.info("기술적 지표 계산 모듈 테스트")
    
    # 샘플 데이터
    prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
              111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    
    # SMA 테스트
    sma = calculate_sma(prices, 5)
    logger.info(f"SMA(5): {sma}")
    
    # RSI 테스트
    rsi = calculate_rsi(prices, 14)
    logger.info(f"RSI(14): {rsi}")
    
    # 볼린저 밴드 테스트
    bb = calculate_bollinger_bands(prices, 20, 2.0)
    logger.info(f"볼린저 밴드: {bb}")
    
    # MACD 테스트
    macd = calculate_macd(prices, 12, 26, 9)
    logger.info(f"MACD: {macd}")
    
    logger.info("기술적 지표 계산 모듈 테스트 완료") 