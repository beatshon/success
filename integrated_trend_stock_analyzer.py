#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 트렌드-주식 분석기
실제 주식 데이터와 네이버 트렌드 분석을 결합한 시스템
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import os

# 프로젝트 모듈 import
from real_stock_data_api import RealStockDataAPI
from naver_trend_analyzer import NaverTrendAnalyzer, TrendType, TrendData, StockTrendCorrelation
from enhanced_risk_management import EnhancedRiskManager, RiskLevel, MarketVolatility
from error_handler import ErrorType, ErrorLevel, handle_error

class SignalStrength(Enum):
    """신호 강도"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class MarketCondition(Enum):
    """시장 상황"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"

@dataclass
class IntegratedSignal:
    """통합 투자 신호"""
    stock_code: str
    stock_name: str
    signal_strength: SignalStrength
    confidence_score: float
    trend_impact: float
    technical_impact: float
    market_impact: float
    reasoning: List[str]
    timestamp: datetime
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    risk_level: str = "medium"
    market_volatility: str = "medium"
    stop_loss_percent: float = 5.0
    take_profit_percent: float = 10.0
    risk_reward_ratio: float = 2.0
    max_loss: Optional[float] = None
    potential_profit: Optional[float] = None
    holding_period: str = "medium_term"

@dataclass
class MarketAnalysis:
    """시장 분석 결과"""
    market_condition: MarketCondition
    overall_sentiment: float
    sector_performance: Dict[str, float]
    trending_sectors: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    timestamp: datetime

class IntegratedTrendStockAnalyzer:
    """통합 트렌드-주식 분석기"""
    
    def __init__(self):
        """초기화"""
        try:
            logger.info("통합 트렌드-주식 분석기 초기화 시작")
            
            # 하위 시스템 초기화
            self.stock_api = RealStockDataAPI()
            self.trend_analyzer = NaverTrendAnalyzer()
            self.risk_manager = EnhancedRiskManager()  # 향상된 리스크 관리자 추가
            
            # 분석 설정
            self.target_stocks = [
                '005930',  # 삼성전자
                '000660',  # SK하이닉스
                '035420',  # 네이버
                '035720',  # 카카오
                '051910',  # LG화학
                '006400',  # 삼성SDI
                '051910',  # 현대차
                '006400'   # 기아
            ]
            
            # 데이터 저장소
            self.integrated_signals = {}
            self.market_analysis = None
            self.analysis_history = []
            
            # 분석 상태
            self.is_analyzing = False
            self.analysis_thread = None
            
            # 캐시 설정
            self.cache_duration = 300  # 5분
            self.last_analysis_time = None
            
            # 리스크 관리 설정
            self.available_capital = 10000000  # 1000만원 (기본값)
            
            logger.info("통합 트렌드-주식 분석기 초기화 완료")
            
        except Exception as e:
            handle_error(ErrorType.INITIALIZATION_ERROR, ErrorLevel.CRITICAL, 
                        f"통합 분석기 초기화 실패: {e}")
            raise
    
    async def collect_integrated_data(self) -> Dict[str, Any]:
        """통합 데이터 수집"""
        try:
            logger.info("통합 데이터 수집 시작")
            
            # 실제 주식 데이터 수집
            stock_data = {}
            for stock_code in self.target_stocks:
                try:
                    data = await self.stock_api.get_stock_data(stock_code)
                    stock_data[stock_code] = data
                except Exception as e:
                    logger.warning(f"주식 데이터 수집 실패 ({stock_code}): {e}")
            
            # 네이버 트렌드 데이터 수집
            trend_data = {}
            for stock_code in self.target_stocks:
                try:
                    stock_name = stock_data.get(stock_code, {}).get('name', '')
                    if stock_name:
                        trend_info = await self.trend_analyzer.get_search_trend(stock_name)
                        trend_data[stock_code] = trend_info
                except Exception as e:
                    logger.warning(f"트렌드 데이터 수집 실패 ({stock_code}): {e}")
            
            # 시장 데이터 수집
            market_data = await self.stock_api.get_market_summary()
            
            result = {
                'stock_data': stock_data,
                'trend_data': trend_data,
                'market_data': market_data,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"통합 데이터 수집 완료: {len(stock_data)}개 종목")
            return result
            
        except Exception as e:
            handle_error(ErrorType.DATA_COLLECTION_ERROR, ErrorLevel.HIGH, 
                        f"통합 데이터 수집 실패: {e}")
            return {}
    
    def analyze_stock_trend_correlation(self, stock_code: str, stock_data: Dict, trend_data: Dict) -> Dict:
        """주식-트렌드 상관관계 분석"""
        try:
            if not stock_data or not trend_data:
                return {}
            
            # 기본 정보 추출
            current_price = stock_data.get('current_price', 0)
            price_change = stock_data.get('price_change_percent', 0)
            volume = stock_data.get('volume', 0)
            
            # 트렌드 지표 추출
            trend_value = trend_data.get('value', 0)
            trend_momentum = trend_data.get('momentum', 0)
            sentiment_score = trend_data.get('sentiment_score', 0)
            
            # 상관관계 분석
            correlation_score = self._calculate_correlation_score(
                price_change, trend_value, sentiment_score
            )
            
            # 신호 강도 결정
            signal_strength = self._determine_signal_strength(
                correlation_score, price_change, trend_momentum
            )
            
            # 신뢰도 계산
            confidence_score = self._calculate_confidence_score(
                stock_data, trend_data
            )
            
            return {
                'correlation_score': correlation_score,
                'signal_strength': signal_strength.value,
                'confidence_score': confidence_score,
                'trend_impact': trend_value,
                'technical_impact': price_change,
                'reasoning': self._generate_reasoning(stock_data, trend_data, signal_strength)
            }
            
        except Exception as e:
            logger.error(f"상관관계 분석 실패 ({stock_code}): {e}")
            return {}
    
    def _calculate_correlation_score(self, price_change: float, trend_value: float, sentiment: float) -> float:
        """상관관계 점수 계산"""
        try:
            # 가격 변화와 트렌드의 상관관계
            price_trend_corr = np.corrcoef([price_change], [trend_value])[0, 1] if not np.isnan(price_change) else 0
            
            # 감정 점수 반영
            sentiment_weight = 0.3
            trend_weight = 0.7
            
            correlation_score = (trend_weight * price_trend_corr + sentiment_weight * sentiment)
            
            # -1 ~ 1 범위로 정규화
            return max(-1.0, min(1.0, correlation_score))
            
        except Exception as e:
            logger.error(f"상관관계 점수 계산 실패: {e}")
            return 0.0
    
    def _determine_signal_strength(self, correlation: float, price_change: float, trend_momentum: float) -> SignalStrength:
        """신호 강도 결정"""
        try:
            # 종합 점수 계산
            score = (correlation * 0.4 + price_change * 0.3 + trend_momentum * 0.3)
            
            if score >= 0.7:
                return SignalStrength.STRONG_BUY
            elif score >= 0.3:
                return SignalStrength.BUY
            elif score >= -0.3:
                return SignalStrength.HOLD
            elif score >= -0.7:
                return SignalStrength.SELL
            else:
                return SignalStrength.STRONG_SELL
                
        except Exception as e:
            logger.error(f"신호 강도 결정 실패: {e}")
            return SignalStrength.HOLD
    
    def _calculate_confidence_score(self, stock_data: Dict, trend_data: Dict) -> float:
        """신뢰도 점수 계산"""
        try:
            confidence_factors = []
            
            # 데이터 품질 점수
            if stock_data and trend_data:
                confidence_factors.append(0.8)
            elif stock_data or trend_data:
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.1)
            
            # 가격 데이터 신뢰도
            if stock_data.get('current_price') and stock_data.get('current_price') > 0:
                confidence_factors.append(0.9)
            else:
                confidence_factors.append(0.3)
            
            # 트렌드 데이터 신뢰도
            if trend_data.get('value') is not None:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.4)
            
            return np.mean(confidence_factors)
            
        except Exception as e:
            logger.error(f"신뢰도 점수 계산 실패: {e}")
            return 0.5
    
    def _generate_reasoning(self, stock_data: Dict, trend_data: Dict, signal_strength: SignalStrength) -> List[str]:
        """투자 근거 생성"""
        reasoning = []
        
        try:
            # 가격 변화 분석
            price_change = stock_data.get('price_change_percent', 0)
            if price_change > 2:
                reasoning.append(f"가격 상승세 강함 (+{price_change:.1f}%)")
            elif price_change > 0:
                reasoning.append(f"가격 상승세 (+{price_change:.1f}%)")
            elif price_change < -2:
                reasoning.append(f"가격 하락세 강함 ({price_change:.1f}%)")
            elif price_change < 0:
                reasoning.append(f"가격 하락세 ({price_change:.1f}%)")
            else:
                reasoning.append("가격 안정적")
            
            # 트렌드 분석
            trend_value = trend_data.get('value', 0)
            if trend_value > 70:
                reasoning.append("검색 트렌드 매우 높음")
            elif trend_value > 50:
                reasoning.append("검색 트렌드 높음")
            elif trend_value < 30:
                reasoning.append("검색 트렌드 낮음")
            else:
                reasoning.append("검색 트렌드 보통")
            
            # 감정 분석
            sentiment = trend_data.get('sentiment_score', 0)
            if sentiment > 0.6:
                reasoning.append("긍정적 시장 감정")
            elif sentiment < -0.6:
                reasoning.append("부정적 시장 감정")
            else:
                reasoning.append("중립적 시장 감정")
            
            # 신호 강도에 따른 추가 근거
            if signal_strength in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
                reasoning.append("매수 신호 강함")
            elif signal_strength in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
                reasoning.append("매도 신호 강함")
            else:
                reasoning.append("관망 권장")
                
        except Exception as e:
            logger.error(f"투자 근거 생성 실패: {e}")
            reasoning.append("분석 데이터 부족")
        
        return reasoning
    
    async def generate_integrated_signals(self) -> Dict[str, IntegratedSignal]:
        """통합 투자 신호 생성"""
        try:
            logger.info("통합 투자 신호 생성 시작")
            
            # 데이터 수집
            integrated_data = await self.collect_integrated_data()
            stock_data = integrated_data.get('stock_data', {})
            trend_data = integrated_data.get('trend_data', {})
            
            signals = {}
            
            for stock_code in self.target_stocks:
                try:
                    stock_info = stock_data.get(stock_code, {})
                    trend_info = trend_data.get(stock_code, {})
                    
                    if not stock_info:
                        continue
                    
                    # 상관관계 분석
                    correlation_analysis = self.analyze_stock_trend_correlation(
                        stock_code, stock_info, trend_info
                    )
                    
                    if not correlation_analysis:
                        continue
                    
                    # 향상된 리스크 관리 계산
                    enhanced_risk = self._calculate_enhanced_risk_management(
                        stock_info, correlation_analysis, integrated_data.get('market_data')
                    )
                    
                    # 통합 신호 생성
                    signal = IntegratedSignal(
                        stock_code=stock_code,
                        stock_name=stock_info.get('name', ''),
                        signal_strength=SignalStrength(correlation_analysis['signal_strength']),
                        confidence_score=correlation_analysis['confidence_score'],
                        trend_impact=correlation_analysis['trend_impact'],
                        technical_impact=correlation_analysis['technical_impact'],
                        market_impact=0.0,  # 시장 영향도는 별도 계산
                        reasoning=correlation_analysis['reasoning'],
                        timestamp=datetime.now(),
                        price_target=self._calculate_price_target(stock_info, correlation_analysis),
                        stop_loss=enhanced_risk.get('stop_loss') if enhanced_risk else self._calculate_stop_loss(stock_info, correlation_analysis),
                        take_profit=enhanced_risk.get('take_profit') if enhanced_risk else None,
                        position_size=enhanced_risk.get('position_size') if enhanced_risk else None,
                        risk_level=enhanced_risk.get('risk_level', 'medium') if enhanced_risk else self._determine_risk_level(correlation_analysis),
                        market_volatility=enhanced_risk.get('market_volatility', 'medium') if enhanced_risk else 'medium',
                        stop_loss_percent=enhanced_risk.get('stop_loss_percent', 5.0) if enhanced_risk else 5.0,
                        take_profit_percent=enhanced_risk.get('take_profit_percent', 10.0) if enhanced_risk else 10.0,
                        risk_reward_ratio=enhanced_risk.get('risk_summary', {}).get('risk_reward_ratio', 2.0) if enhanced_risk else 2.0,
                        max_loss=enhanced_risk.get('risk_summary', {}).get('max_loss') if enhanced_risk else None,
                        potential_profit=enhanced_risk.get('risk_summary', {}).get('potential_profit') if enhanced_risk else None,
                        holding_period=self._determine_holding_period(correlation_analysis)
                    )
                    
                    signals[stock_code] = signal
                    
                except Exception as e:
                    logger.error(f"신호 생성 실패 ({stock_code}): {e}")
            
            self.integrated_signals = signals
            logger.info(f"통합 투자 신호 생성 완료: {len(signals)}개")
            
            return signals
            
        except Exception as e:
            handle_error(ErrorType.ANALYSIS_ERROR, ErrorLevel.HIGH, 
                        f"통합 신호 생성 실패: {e}")
            return {}
    
    def _calculate_price_target(self, stock_data: Dict, analysis: Dict) -> Optional[float]:
        """목표가 계산 (향상된 시스템)"""
        try:
            current_price = stock_data.get('current_price', 0)
            if current_price <= 0:
                return None
            
            # 상관관계 점수에 따른 목표가 조정
            correlation_score = analysis.get('correlation_score', 0)
            adjustment_factor = 1 + (correlation_score * 0.1)  # ±10% 조정
            
            return current_price * adjustment_factor
            
        except Exception as e:
            logger.error(f"목표가 계산 실패: {e}")
            return None
    
    def _calculate_enhanced_risk_management(self, stock_data: Dict, analysis: Dict, market_data: Dict = None) -> Dict:
        """향상된 리스크 관리 계산"""
        try:
            current_price = stock_data.get('current_price', 0)
            if current_price <= 0:
                return {}
            
            signal_strength = analysis.get('signal_strength', 'hold')
            confidence_score = analysis.get('confidence_score', 0.5)
            
            # 변동성 계산 (간단한 방법)
            volatility = abs(stock_data.get('price_change_percent', 0)) / 100
            stock_volatility = volatility
            
            # 시장 상황 결정
            market_condition = 'sideways'  # 기본값
            if market_data:
                kospi_change = market_data.get('kospi_change_percent', 0)
                if kospi_change > 1:
                    market_condition = 'bull_market'
                elif kospi_change < -1:
                    market_condition = 'bear_market'
                elif abs(kospi_change) > 0.5:
                    market_condition = 'volatile'
            
            # 향상된 리스크 관리자로 손절/익절 계산
            stop_loss, take_profit, risk_info = self.risk_manager.calculate_stop_loss_and_take_profit(
                current_price,
                signal_strength,
                confidence_score,
                volatility,
                market_condition,
                stock_volatility
            )
            
            # 포지션 크기 계산
            risk_level = RiskLevel(risk_info.get('risk_level', 'medium'))
            position_size = self.risk_manager.calculate_position_size(
                self.available_capital,
                risk_level,
                confidence_score,
                stock_volatility
            )
            
            # 리스크 관리 요약
            risk_summary = self.risk_manager.get_risk_management_summary(
                current_price,
                stop_loss,
                take_profit,
                position_size,
                self.available_capital
            )
            
            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': position_size,
                'risk_level': risk_info.get('risk_level', 'medium'),
                'market_volatility': risk_info.get('market_volatility', 'medium'),
                'stop_loss_percent': risk_info.get('stop_loss_percent', 5.0),
                'take_profit_percent': risk_info.get('take_profit_percent', 10.0),
                'risk_summary': risk_summary
            }
            
        except Exception as e:
            logger.error(f"향상된 리스크 관리 계산 실패: {e}")
            return {}
    
    def _calculate_stop_loss(self, stock_data: Dict, analysis: Dict) -> Optional[float]:
        """손절가 계산 (기존 방식 - 호환성 유지)"""
        try:
            current_price = stock_data.get('current_price', 0)
            if current_price <= 0:
                return None
            
            # 신호 강도에 따른 손절가 설정
            signal_strength = analysis.get('signal_strength', 'hold')
            
            if signal_strength in ['strong_buy', 'buy']:
                stop_loss_ratio = 0.95  # 5% 손절
            elif signal_strength in ['strong_sell', 'sell']:
                stop_loss_ratio = 1.05  # 5% 익절
            else:
                stop_loss_ratio = 0.98  # 2% 손절
            
            return current_price * stop_loss_ratio
            
        except Exception as e:
            logger.error(f"손절가 계산 실패: {e}")
            return None
    
    def _determine_risk_level(self, analysis: Dict) -> str:
        """위험도 결정"""
        try:
            confidence_score = analysis.get('confidence_score', 0.5)
            correlation_score = abs(analysis.get('correlation_score', 0))
            
            if confidence_score < 0.3 or correlation_score < 0.2:
                return "high"
            elif confidence_score < 0.6 or correlation_score < 0.5:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"위험도 결정 실패: {e}")
            return "medium"
    
    def _determine_holding_period(self, analysis: Dict) -> str:
        """보유 기간 결정"""
        try:
            signal_strength = analysis.get('signal_strength', 'hold')
            
            if signal_strength in ['strong_buy', 'strong_sell']:
                return "long_term"
            elif signal_strength in ['buy', 'sell']:
                return "medium_term"
            else:
                return "short_term"
                
        except Exception as e:
            logger.error(f"보유 기간 결정 실패: {e}")
            return "medium_term"
    
    async def analyze_market_condition(self) -> MarketAnalysis:
        """시장 상황 분석"""
        try:
            logger.info("시장 상황 분석 시작")
            
            # 시장 데이터 수집
            market_data = await self.stock_api.get_market_summary()
            
            # 종합 신호 분석
            if not self.integrated_signals:
                await self.generate_integrated_signals()
            
            # 시장 감정 계산
            sentiment_scores = []
            for signal in self.integrated_signals.values():
                if signal.signal_strength in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
                    sentiment_scores.append(1.0)
                elif signal.signal_strength in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
                    sentiment_scores.append(-1.0)
                else:
                    sentiment_scores.append(0.0)
            
            overall_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            # 시장 상황 판단
            market_condition = self._determine_market_condition(overall_sentiment, market_data)
            
            # 섹터별 성과 분석
            sector_performance = self._analyze_sector_performance()
            
            # 트렌딩 섹터 식별
            trending_sectors = self._identify_trending_sectors()
            
            # 위험 요소 및 기회 요소 식별
            risk_factors, opportunities = self._identify_market_factors(market_condition, overall_sentiment)
            
            market_analysis = MarketAnalysis(
                market_condition=market_condition,
                overall_sentiment=overall_sentiment,
                sector_performance=sector_performance,
                trending_sectors=trending_sectors,
                risk_factors=risk_factors,
                opportunities=opportunities,
                timestamp=datetime.now()
            )
            
            self.market_analysis = market_analysis
            logger.info(f"시장 상황 분석 완료: {market_condition.value}")
            
            return market_analysis
            
        except Exception as e:
            handle_error(ErrorType.ANALYSIS_ERROR, ErrorLevel.HIGH, 
                        f"시장 상황 분석 실패: {e}")
            return None
    
    def _determine_market_condition(self, sentiment: float, market_data: Dict) -> MarketCondition:
        """시장 상황 판단"""
        try:
            # KOSPI 변화율 확인
            kospi_change = market_data.get('kospi_change_percent', 0)
            
            if sentiment > 0.5 and kospi_change > 1:
                return MarketCondition.BULL_MARKET
            elif sentiment < -0.5 and kospi_change < -1:
                return MarketCondition.BEAR_MARKET
            elif abs(sentiment) < 0.2 and abs(kospi_change) < 0.5:
                return MarketCondition.SIDEWAYS
            elif abs(sentiment) > 0.3:
                return MarketCondition.VOLATILE
            elif kospi_change > 0.5:
                return MarketCondition.TRENDING_UP
            elif kospi_change < -0.5:
                return MarketCondition.TRENDING_DOWN
            else:
                return MarketCondition.SIDEWAYS
                
        except Exception as e:
            logger.error(f"시장 상황 판단 실패: {e}")
            return MarketCondition.SIDEWAYS
    
    def _analyze_sector_performance(self) -> Dict[str, float]:
        """섹터별 성과 분석"""
        try:
            sector_performance = {}
            
            # 섹터별 종목 그룹화
            sector_stocks = {
                '반도체': ['005930', '000660'],
                'IT': ['035420', '035720'],
                '화학': ['051910', '006400'],
                '자동차': ['051910', '006400']
            }
            
            for sector, stock_codes in sector_stocks.items():
                sector_scores = []
                for stock_code in stock_codes:
                    if stock_code in self.integrated_signals:
                        signal = self.integrated_signals[stock_code]
                        if signal.signal_strength in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
                            sector_scores.append(1.0)
                        elif signal.signal_strength in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
                            sector_scores.append(-1.0)
                        else:
                            sector_scores.append(0.0)
                
                if sector_scores:
                    sector_performance[sector] = np.mean(sector_scores)
                else:
                    sector_performance[sector] = 0.0
            
            return sector_performance
            
        except Exception as e:
            logger.error(f"섹터별 성과 분석 실패: {e}")
            return {}
    
    def _identify_trending_sectors(self) -> List[str]:
        """트렌딩 섹터 식별"""
        try:
            trending_sectors = []
            
            if self.market_analysis:
                sector_performance = self.market_analysis.sector_performance
                
                for sector, performance in sector_performance.items():
                    if performance > 0.5:
                        trending_sectors.append(f"{sector} (상승세)")
                    elif performance < -0.5:
                        trending_sectors.append(f"{sector} (하락세)")
            
            return trending_sectors
            
        except Exception as e:
            logger.error(f"트렌딩 섹터 식별 실패: {e}")
            return []
    
    def _identify_market_factors(self, market_condition: MarketCondition, sentiment: float) -> Tuple[List[str], List[str]]:
        """시장 위험 요소 및 기회 요소 식별"""
        try:
            risk_factors = []
            opportunities = []
            
            # 시장 상황에 따른 요소 식별
            if market_condition == MarketCondition.BEAR_MARKET:
                risk_factors.extend([
                    "시장 전체 하락세",
                    "투자 심리 위축",
                    "유동성 부족 가능성"
                ])
                opportunities.extend([
                    "저평가 종목 발굴 기회",
                    "방어적 포트폴리오 구성",
                    "장기 투자 기회"
                ])
            elif market_condition == MarketCondition.BULL_MARKET:
                risk_factors.extend([
                    "과열 우려",
                    "조정 가능성",
                    "이익 실현 압박"
                ])
                opportunities.extend([
                    "성장주 투자 기회",
                    "모멘텀 활용",
                    "적극적 포트폴리오 확대"
                ])
            elif market_condition == MarketCondition.VOLATILE:
                risk_factors.extend([
                    "급격한 가격 변동",
                    "예측 어려움",
                    "손실 위험 증가"
                ])
                opportunities.extend([
                    "단기 매매 기회",
                    "변동성 활용",
                    "리스크 관리 중요"
                ])
            
            # 감정 점수에 따른 추가 요소
            if sentiment > 0.7:
                opportunities.append("강한 매수 심리")
            elif sentiment < -0.7:
                risk_factors.append("강한 매도 심리")
            
            return risk_factors, opportunities
            
        except Exception as e:
            logger.error(f"시장 요소 식별 실패: {e}")
            return [], []
    
    def start_continuous_analysis(self):
        """연속 분석 시작"""
        try:
            if self.is_analyzing:
                logger.warning("이미 분석이 실행 중입니다.")
                return
            
            self.is_analyzing = True
            self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
            self.analysis_thread.start()
            
            logger.info("연속 분석 시작")
            
        except Exception as e:
            handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.HIGH, 
                        f"연속 분석 시작 실패: {e}")
    
    def stop_continuous_analysis(self):
        """연속 분석 중지"""
        try:
            self.is_analyzing = False
            if self.analysis_thread:
                self.analysis_thread.join(timeout=5)
            
            logger.info("연속 분석 중지")
            
        except Exception as e:
            logger.error(f"연속 분석 중지 실패: {e}")
    
    def _analysis_worker(self):
        """분석 워커 스레드"""
        try:
            while self.is_analyzing:
                try:
                    # 비동기 함수를 동기적으로 실행
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 통합 신호 생성
                    signals = loop.run_until_complete(self.generate_integrated_signals())
                    
                    # 시장 상황 분석
                    market_analysis = loop.run_until_complete(self.analyze_market_condition())
                    
                    # 분석 히스토리 저장
                    self.analysis_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'signals_count': len(signals),
                        'market_condition': market_analysis.market_condition.value if market_analysis else 'unknown'
                    })
                    
                    # 최근 100개만 유지
                    if len(self.analysis_history) > 100:
                        self.analysis_history = self.analysis_history[-100:]
                    
                    loop.close()
                    
                    logger.info(f"분석 완료: {len(signals)}개 신호, 시장상황: {market_analysis.market_condition.value if market_analysis else 'unknown'}")
                    
                    # 5분 대기
                    time.sleep(300)
                    
                except Exception as e:
                    logger.error(f"분석 워커 오류: {e}")
                    time.sleep(60)  # 오류 시 1분 대기
                    
        except Exception as e:
            logger.error(f"분석 워커 스레드 실패: {e}")
    
    def get_analysis_summary(self) -> Dict:
        """분석 요약 반환"""
        try:
            return {
                'total_signals': len(self.integrated_signals),
                'market_condition': self.market_analysis.market_condition.value if self.market_analysis else 'unknown',
                'overall_sentiment': self.market_analysis.overall_sentiment if self.market_analysis else 0.0,
                'analysis_running': self.is_analyzing,
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'analysis_history_count': len(self.analysis_history),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"분석 요약 생성 실패: {e}")
            return {}
    
    def get_signals_for_stock(self, stock_code: str) -> Optional[IntegratedSignal]:
        """특정 종목의 신호 반환"""
        try:
            return self.integrated_signals.get(stock_code)
        except Exception as e:
            logger.error(f"종목 신호 조회 실패 ({stock_code}): {e}")
            return None
    
    def get_all_signals(self) -> Dict[str, IntegratedSignal]:
        """모든 신호 반환"""
        try:
            return self.integrated_signals.copy()
        except Exception as e:
            logger.error(f"전체 신호 조회 실패: {e}")
            return {}
    
    def get_market_analysis(self) -> Optional[MarketAnalysis]:
        """시장 분석 결과 반환"""
        try:
            return self.market_analysis
        except Exception as e:
            logger.error(f"시장 분석 결과 조회 실패: {e}")
            return None

# 테스트 함수
async def test_integrated_analyzer():
    """통합 분석기 테스트"""
    try:
        logger.info("=== 통합 트렌드-주식 분석기 테스트 시작 ===")
        
        analyzer = IntegratedTrendStockAnalyzer()
        
        # 통합 신호 생성 테스트
        logger.info("통합 신호 생성 테스트...")
        signals = await analyzer.generate_integrated_signals()
        logger.info(f"생성된 신호 수: {len(signals)}")
        
        # 시장 상황 분석 테스트
        logger.info("시장 상황 분석 테스트...")
        market_analysis = await analyzer.analyze_market_condition()
        if market_analysis:
            logger.info(f"시장 상황: {market_analysis.market_condition.value}")
            logger.info(f"전체 감정: {market_analysis.overall_sentiment:.2f}")
        
        # 분석 요약 테스트
        logger.info("분석 요약 테스트...")
        summary = analyzer.get_analysis_summary()
        logger.info(f"분석 요약: {summary}")
        
        logger.info("=== 통합 트렌드-주식 분석기 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"통합 분석기 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_integrated_analyzer()) 