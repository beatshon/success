#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
단타 전용 설정 파일
손절 -2%~3%, 익절 +4%~6% (손익비 최소 2:1) 기준
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

class DayTradingRiskLevel(Enum):
    """단타 위험도 레벨"""
    CONSERVATIVE = "conservative"  # 보수적 (2% 손절, 4% 익절)
    MODERATE = "moderate"         # 중간 (2.5% 손절, 5% 익절)
    AGGRESSIVE = "aggressive"     # 공격적 (3% 손절, 6% 익절)

class MarketCondition(Enum):
    """시장 상황"""
    BULL = "bull"           # 상승장
    BEAR = "bear"           # 하락장
    SIDEWAYS = "sideways"   # 횡보장
    VOLATILE = "volatile"   # 변동성 장

@dataclass
class DayTradingConfig:
    """단타 설정"""
    
    # 기본 손절/익절 비율 (손익비 2:1)
    base_stop_loss: float = 0.025    # 2.5%
    base_take_profit: float = 0.05   # 5%
    
    # 위험도별 설정 (포지션 사이즈 제한: 1종목당 자본의 5~10%)
    risk_levels = {
        DayTradingRiskLevel.CONSERVATIVE: {
            "stop_loss": 0.02,      # 2% 손절
            "take_profit": 0.04,    # 4% 익절
            "risk_reward_ratio": 2.0,
            "max_position_size": 0.05  # 자본의 5% (보수적)
        },
        DayTradingRiskLevel.MODERATE: {
            "stop_loss": 0.025,     # 2.5% 손절
            "take_profit": 0.05,    # 5% 익절
            "risk_reward_ratio": 2.0,
            "max_position_size": 0.08  # 자본의 8% (중간)
        },
        DayTradingRiskLevel.AGGRESSIVE: {
            "stop_loss": 0.03,      # 3% 손절
            "take_profit": 0.06,    # 6% 익절
            "risk_reward_ratio": 2.0,
            "max_position_size": 0.10  # 자본의 10% (공격적)
        }
    }
    
    # 시장 상황별 조정 계수
    market_adjustments = {
        MarketCondition.BULL: {
            "stop_loss_multiplier": 1.0,    # 기본값
            "take_profit_multiplier": 1.1,  # 익절 10% 증가
            "position_size_multiplier": 1.2  # 포지션 크기 20% 증가
        },
        MarketCondition.BEAR: {
            "stop_loss_multiplier": 0.8,    # 손절 20% 감소 (더 타이트)
            "take_profit_multiplier": 0.9,  # 익절 10% 감소
            "position_size_multiplier": 0.7  # 포지션 크기 30% 감소
        },
        MarketCondition.SIDEWAYS: {
            "stop_loss_multiplier": 0.9,    # 손절 10% 감소
            "take_profit_multiplier": 1.0,  # 기본값
            "position_size_multiplier": 0.8  # 포지션 크기 20% 감소
        },
        MarketCondition.VOLATILE: {
            "stop_loss_multiplier": 0.7,    # 손절 30% 감소 (매우 타이트)
            "take_profit_multiplier": 0.8,  # 익절 20% 감소
            "position_size_multiplier": 0.5  # 포지션 크기 50% 감소
        }
    }
    
    # 시간대별 조정 (단타는 시간대가 중요)
    time_adjustments = {
        "market_open": {      # 장 시작 (9:00-10:00)
            "stop_loss_multiplier": 0.8,    # 손절 20% 감소
            "take_profit_multiplier": 1.0,
            "position_size_multiplier": 0.7
        },
        "morning": {          # 오전 (10:00-12:00)
            "stop_loss_multiplier": 1.0,    # 기본값
            "take_profit_multiplier": 1.0,
            "position_size_multiplier": 1.0
        },
        "lunch": {            # 점심시간 (12:00-13:00)
            "stop_loss_multiplier": 0.9,    # 손절 10% 감소
            "take_profit_multiplier": 0.9,
            "position_size_multiplier": 0.8
        },
        "afternoon": {        # 오후 (13:00-15:00)
            "stop_loss_multiplier": 1.0,    # 기본값
            "take_profit_multiplier": 1.0,
            "position_size_multiplier": 1.0
        },
        "market_close": {     # 장 마감 (15:00-15:30)
            "stop_loss_multiplier": 0.6,    # 손절 40% 감소 (매우 타이트)
            "take_profit_multiplier": 0.7,  # 익절 30% 감소
            "position_size_multiplier": 0.4  # 포지션 크기 60% 감소
        }
    }
    
    # 최대 손실 제한 (일일)
    max_daily_loss: float = 0.05  # 일일 최대 손실 5%
    
    # 최대 거래 횟수 (일일)
    max_daily_trades: int = 10
    
    # 최소 거래 간격 (분)
    min_trade_interval: int = 5
    
    # 손절 실행 조건
    stop_loss_conditions = {
        "immediate": True,        # 즉시 손절
        "volume_spike": True,     # 거래량 급증 시 손절
        "price_gap": True,        # 갭 발생 시 손절
        "time_based": True        # 시간 기반 손절 (30분 후)
    }
    
    # 익절 실행 조건
    take_profit_conditions = {
        "target_reached": True,   # 목표가 도달 시 익절
        "momentum_fade": True,    # 모멘텀 감소 시 익절
        "volume_decline": True,   # 거래량 감소 시 익절
        "time_based": True        # 시간 기반 익절 (2시간 후)
    }

def get_day_trading_config() -> DayTradingConfig:
    """단타 설정 반환"""
    return DayTradingConfig()

def calculate_day_trading_risk_reward(
    current_price: float,
    risk_level: DayTradingRiskLevel,
    market_condition: MarketCondition,
    time_period: str = "morning"
) -> Dict:
    """단타 리스크/리워드 계산"""
    config = get_day_trading_config()
    
    # 기본 설정 가져오기
    base_config = config.risk_levels[risk_level]
    market_adj = config.market_adjustments[market_condition]
    time_adj = config.time_adjustments.get(time_period, {
        "stop_loss_multiplier": 1.0,
        "take_profit_multiplier": 1.0,
        "position_size_multiplier": 1.0
    })
    
    # 최종 손절/익절 비율 계산
    final_stop_loss = base_config["stop_loss"] * market_adj["stop_loss_multiplier"] * time_adj["stop_loss_multiplier"]
    final_take_profit = base_config["take_profit"] * market_adj["take_profit_multiplier"] * time_adj["take_profit_multiplier"]
    
    # 손절가/익절가 계산
    stop_loss_price = current_price * (1 - final_stop_loss)
    take_profit_price = current_price * (1 + final_take_profit)
    
    return {
        "current_price": current_price,
        "stop_loss_price": stop_loss_price,
        "take_profit_price": take_profit_price,
        "stop_loss_percent": final_stop_loss * 100,
        "take_profit_percent": final_take_profit * 100,
        "risk_reward_ratio": final_take_profit / final_stop_loss,
        "risk_level": risk_level.value,
        "market_condition": market_condition.value,
        "time_period": time_period
    }

# 테스트 함수
def test_day_trading_config():
    """단타 설정 테스트"""
    print("=== 단타 설정 테스트 ===")
    
    test_cases = [
        (80000, DayTradingRiskLevel.MODERATE, MarketCondition.BULL, "morning"),
        (170000, DayTradingRiskLevel.CONSERVATIVE, MarketCondition.SIDEWAYS, "afternoon"),
        (220000, DayTradingRiskLevel.AGGRESSIVE, MarketCondition.VOLATILE, "market_close")
    ]
    
    for price, risk, market, time in test_cases:
        result = calculate_day_trading_risk_reward(price, risk, market, time)
        print(f"\n현재가: {price:,}원")
        print(f"손절가: {result['stop_loss_price']:,.0f}원 ({result['stop_loss_percent']:.1f}%)")
        print(f"익절가: {result['take_profit_price']:,.0f}원 ({result['take_profit_percent']:.1f}%)")
        print(f"손익비: {result['risk_reward_ratio']:.2f}")
        print(f"설정: {risk.value} / {market.value} / {time}")

if __name__ == "__main__":
    test_day_trading_config() 