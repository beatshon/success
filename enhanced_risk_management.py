#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
향상된 리스크 관리 시스템
손절/익절 기준을 더 세밀하게 관리
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
from loguru import logger

class RiskLevel(Enum):
    """위험도 레벨"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MarketVolatility(Enum):
    """시장 변동성"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class RiskManagementConfig:
    """리스크 관리 설정"""
    # 단타 기준 손절/익절 비율 (손익비 최소 2:1)
    base_stop_loss: float = 0.025  # 2.5%
    base_take_profit: float = 0.05  # 5% (2:1 비율)
    
    # 위험도별 조정 계수 (단타 기준)
    risk_adjustments = {
        RiskLevel.VERY_LOW: {"stop_loss": 0.8, "take_profit": 1.2},  # 2% 손절, 6% 익절
        RiskLevel.LOW: {"stop_loss": 0.9, "take_profit": 1.1},       # 2.25% 손절, 5.5% 익절
        RiskLevel.MEDIUM: {"stop_loss": 1.0, "take_profit": 1.0},    # 2.5% 손절, 5% 익절
        RiskLevel.HIGH: {"stop_loss": 1.2, "take_profit": 0.8},      # 3% 손절, 4% 익절
        RiskLevel.VERY_HIGH: {"stop_loss": 1.4, "take_profit": 0.7}  # 3.5% 손절, 3.5% 익절
    }
    
    # 변동성별 조정 계수 (단타 기준)
    volatility_adjustments = {
        MarketVolatility.LOW: {"stop_loss": 0.8, "take_profit": 1.2},    # 2% 손절, 6% 익절
        MarketVolatility.MEDIUM: {"stop_loss": 1.0, "take_profit": 1.0}, # 2.5% 손절, 5% 익절
        MarketVolatility.HIGH: {"stop_loss": 1.2, "take_profit": 0.8},   # 3% 손절, 4% 익절
        MarketVolatility.EXTREME: {"stop_loss": 1.4, "take_profit": 0.6} # 3.5% 손절, 3% 익절
    }

class EnhancedRiskManager:
    """향상된 리스크 관리자"""
    
    def __init__(self, config: RiskManagementConfig = None):
        self.config = config or RiskManagementConfig()
    
    def calculate_stop_loss_and_take_profit(
        self, 
        current_price: float,
        signal_strength: str,
        confidence_score: float,
        volatility: float,
        market_condition: str,
        stock_volatility: float = None
    ) -> Tuple[float, float, Dict]:
        """손절가와 익절가 계산"""
        try:
            # 위험도 결정
            risk_level = self._determine_risk_level(signal_strength, confidence_score)
            
            # 시장 변동성 결정
            market_volatility = self._determine_market_volatility(volatility)
            
            # 기본 손절/익절 비율
            base_stop_loss = self.config.base_stop_loss
            base_take_profit = self.config.base_take_profit
            
            # 위험도 조정
            risk_adj = self.config.risk_adjustments[risk_level]
            adjusted_stop_loss = base_stop_loss * risk_adj["stop_loss"]
            adjusted_take_profit = base_take_profit * risk_adj["take_profit"]
            
            # 변동성 조정
            vol_adj = self.config.volatility_adjustments[market_volatility]
            final_stop_loss = adjusted_stop_loss * vol_adj["stop_loss"]
            final_take_profit = adjusted_take_profit * vol_adj["take_profit"]
            
            # 신호 강도별 추가 조정
            if signal_strength in ['strong_buy', 'strong_sell']:
                # 강한 신호는 더 타이트한 손절
                final_stop_loss *= 0.8
                final_take_profit *= 1.2
            elif signal_strength in ['buy', 'sell']:
                # 일반 신호는 기본값 유지
                pass
            else:  # hold
                # 관망 신호는 보수적 접근
                final_stop_loss *= 0.6
                final_take_profit *= 0.8
            
            # 시장 상황별 조정
            if market_condition == 'bull_market':
                # 상승장에서는 익절을 더 높게
                final_take_profit *= 1.1
            elif market_condition == 'bear_market':
                # 하락장에서는 손절을 더 타이트하게
                final_stop_loss *= 0.8
            elif market_condition == 'volatile':
                # 변동성 장에서는 손절을 더 타이트하게
                final_stop_loss *= 0.7
                final_take_profit *= 0.9
            
            # 개별 종목 변동성 조정
            if stock_volatility:
                if stock_volatility > 0.03:  # 3% 이상 변동성
                    final_stop_loss *= 1.2
                    final_take_profit *= 0.9
                elif stock_volatility < 0.01:  # 1% 미만 변동성
                    final_stop_loss *= 0.8
                    final_take_profit *= 1.1
            
            # 최종 손절가/익절가 계산
            stop_loss_price = current_price * (1 - final_stop_loss)
            take_profit_price = current_price * (1 + final_take_profit)
            
            # 매도 신호일 때는 반대로 적용
            if signal_strength in ['sell', 'strong_sell']:
                stop_loss_price = current_price * (1 + final_stop_loss)  # 익절가
                take_profit_price = current_price * (1 - final_take_profit)  # 손절가
            
            return stop_loss_price, take_profit_price, {
                'risk_level': risk_level.value,
                'market_volatility': market_volatility.value,
                'stop_loss_percent': final_stop_loss * 100,
                'take_profit_percent': final_take_profit * 100,
                'confidence_score': confidence_score
            }
            
        except Exception as e:
            logger.error(f"손절/익절 계산 실패: {e}")
            # 기본값 반환
            return current_price * 0.95, current_price * 1.10, {}
    
    def _determine_risk_level(self, signal_strength: str, confidence_score: float) -> RiskLevel:
        """위험도 결정"""
        try:
            # 신뢰도 기반 위험도
            if confidence_score >= 0.8:
                base_risk = RiskLevel.LOW
            elif confidence_score >= 0.6:
                base_risk = RiskLevel.MEDIUM
            elif confidence_score >= 0.4:
                base_risk = RiskLevel.HIGH
            else:
                base_risk = RiskLevel.VERY_HIGH
            
            # 신호 강도에 따른 조정
            if signal_strength in ['strong_buy', 'strong_sell']:
                if base_risk == RiskLevel.VERY_HIGH:
                    return RiskLevel.HIGH
                elif base_risk == RiskLevel.HIGH:
                    return RiskLevel.MEDIUM
                else:
                    return base_risk
            elif signal_strength in ['buy', 'sell']:
                return base_risk
            else:  # hold
                if base_risk == RiskLevel.LOW:
                    return RiskLevel.VERY_LOW
                else:
                    return base_risk
                    
        except Exception as e:
            logger.error(f"위험도 결정 실패: {e}")
            return RiskLevel.MEDIUM
    
    def _determine_market_volatility(self, volatility: float) -> MarketVolatility:
        """시장 변동성 결정"""
        try:
            if volatility < 0.01:  # 1% 미만
                return MarketVolatility.LOW
            elif volatility < 0.02:  # 2% 미만
                return MarketVolatility.MEDIUM
            elif volatility < 0.04:  # 4% 미만
                return MarketVolatility.HIGH
            else:  # 4% 이상
                return MarketVolatility.EXTREME
                
        except Exception as e:
            logger.error(f"시장 변동성 결정 실패: {e}")
            return MarketVolatility.MEDIUM
    
    def calculate_position_size(
        self,
        available_capital: float,
        risk_level: RiskLevel,
        confidence_score: float,
        stock_volatility: float
    ) -> float:
        """포지션 크기 계산"""
        try:
            # 기본 포지션 크기 (총 자본의 10%)
            base_position = available_capital * 0.1
            
            # 위험도별 조정
            risk_adjustments = {
                RiskLevel.VERY_LOW: 1.5,   # 15%
                RiskLevel.LOW: 1.2,        # 12%
                RiskLevel.MEDIUM: 1.0,     # 10%
                RiskLevel.HIGH: 0.7,       # 7%
                RiskLevel.VERY_HIGH: 0.5   # 5%
            }
            
            position_size = base_position * risk_adjustments[risk_level]
            
            # 신뢰도 조정
            confidence_multiplier = 0.5 + (confidence_score * 0.5)  # 0.5 ~ 1.0
            position_size *= confidence_multiplier
            
            # 변동성 조정
            if stock_volatility > 0.03:  # 3% 이상
                position_size *= 0.7
            elif stock_volatility < 0.01:  # 1% 미만
                position_size *= 1.2
            
            return min(position_size, available_capital * 0.2)  # 최대 20% 제한
            
        except Exception as e:
            logger.error(f"포지션 크기 계산 실패: {e}")
            return available_capital * 0.05  # 기본 5%
    
    def get_risk_management_summary(
        self,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        available_capital: float
    ) -> Dict:
        """리스크 관리 요약"""
        try:
            stop_loss_percent = abs((stop_loss - current_price) / current_price) * 100
            take_profit_percent = abs((take_profit - current_price) / current_price) * 100
            position_percent = (position_size / available_capital) * 100
            
            max_loss = position_size * (stop_loss_percent / 100)
            potential_profit = position_size * (take_profit_percent / 100)
            risk_reward_ratio = potential_profit / max_loss if max_loss > 0 else 0
            
            return {
                'current_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_percent': stop_loss_percent,
                'take_profit_percent': take_profit_percent,
                'position_size': position_size,
                'position_percent': position_percent,
                'max_loss': max_loss,
                'potential_profit': potential_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'max_loss_percent': (max_loss / available_capital) * 100
            }
            
        except Exception as e:
            logger.error(f"리스크 관리 요약 생성 실패: {e}")
            return {}

# 테스트 함수
def test_enhanced_risk_management():
    """향상된 리스크 관리 테스트"""
    try:
        logger.info("=== 향상된 리스크 관리 테스트 시작 ===")
        
        risk_manager = EnhancedRiskManager()
        
        # 테스트 케이스
        test_cases = [
            {
                'name': '삼성전자',
                'current_price': 68900,
                'signal_strength': 'strong_buy',
                'confidence_score': 0.8,
                'volatility': 0.02,
                'market_condition': 'bull_market',
                'stock_volatility': 0.025
            },
            {
                'name': 'SK하이닉스',
                'current_price': 258000,
                'signal_strength': 'sell',
                'confidence_score': 0.6,
                'volatility': 0.03,
                'market_condition': 'volatile',
                'stock_volatility': 0.035
            },
            {
                'name': '네이버',
                'current_price': 225000,
                'signal_strength': 'hold',
                'confidence_score': 0.4,
                'volatility': 0.015,
                'market_condition': 'sideways',
                'stock_volatility': 0.018
            }
        ]
        
        available_capital = 10000000  # 1000만원
        
        for case in test_cases:
            logger.info(f"\n{case['name']} 분석:")
            
            # 손절/익절 계산
            stop_loss, take_profit, risk_info = risk_manager.calculate_stop_loss_and_take_profit(
                case['current_price'],
                case['signal_strength'],
                case['confidence_score'],
                case['volatility'],
                case['market_condition'],
                case['stock_volatility']
            )
            
            # 포지션 크기 계산
            risk_level = RiskLevel(risk_info['risk_level'])
            position_size = risk_manager.calculate_position_size(
                available_capital,
                risk_level,
                case['confidence_score'],
                case['stock_volatility']
            )
            
            # 리스크 관리 요약
            summary = risk_manager.get_risk_management_summary(
                case['current_price'],
                stop_loss,
                take_profit,
                position_size,
                available_capital
            )
            
            logger.info(f"  현재가: {case['current_price']:,}원")
            logger.info(f"  손절가: {stop_loss:,.0f}원 ({summary['stop_loss_percent']:.1f}%)")
            logger.info(f"  익절가: {take_profit:,.0f}원 ({summary['take_profit_percent']:.1f}%)")
            logger.info(f"  포지션 크기: {position_size:,.0f}원 ({summary['position_percent']:.1f}%)")
            logger.info(f"  최대 손실: {summary['max_loss']:,.0f}원 ({summary['max_loss_percent']:.1f}%)")
            logger.info(f"  예상 수익: {summary['potential_profit']:,.0f}원")
            logger.info(f"  리스크/리워드 비율: {summary['risk_reward_ratio']:.2f}")
            logger.info(f"  위험도: {risk_info['risk_level']}")
            logger.info(f"  시장 변동성: {risk_info['market_volatility']}")
        
        logger.info("\n=== 향상된 리스크 관리 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")

if __name__ == "__main__":
    test_enhanced_risk_management() 