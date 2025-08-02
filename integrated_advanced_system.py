#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 고도화 시스템
고도화된 투자 신호 생성 + 포트폴리오 최적화 + 리스크 관리
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import threading
import time
from loguru import logger

# 고도화된 모듈들 import
from advanced_investment_signals import AdvancedInvestmentSignals, AdvancedSignal, SignalType
from portfolio_optimizer import PortfolioOptimizer, Portfolio, OptimizationMethod
from naver_trend_analyzer import NaverTrendAnalyzer

class IntegratedAdvancedSystem:
    """통합 고도화 시스템"""
    
    def __init__(self):
        """초기화"""
        logger.info("통합 고도화 시스템 초기화 시작")
        
        # 핵심 컴포넌트 초기화
        self.signal_generator = AdvancedInvestmentSignals()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.trend_analyzer = NaverTrendAnalyzer()
        
        # 시스템 설정
        self.config = {
            'rebalance_frequency': 7,  # 7일마다 리밸런싱
            'max_portfolio_size': 20,  # 최대 20개 종목
            'min_signal_confidence': 0.6,  # 최소 신호 신뢰도
            'risk_tolerance': 'MEDIUM',  # 리스크 허용도
            'target_return': 0.12,  # 12% 목표 수익률
            'max_drawdown_limit': 0.15  # 최대 15% 낙폭 제한
        }
        
        # 상태 관리
        self.is_running = False
        self.current_portfolio = None
        self.signal_history = []
        self.performance_history = []
        
        # 모니터링 스레드
        self.monitoring_thread = None
        
        logger.info("통합 고도화 시스템 초기화 완료")

    def start_system(self):
        """시스템 시작"""
        try:
            logger.info("통합 고도화 시스템 시작")
            
            if self.is_running:
                logger.warning("시스템이 이미 실행 중입니다")
                return False
            
            self.is_running = True
            
            # 모니터링 스레드 시작
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("통합 고도화 시스템 시작 완료")
            return True
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            return False

    def stop_system(self):
        """시스템 중지"""
        try:
            logger.info("통합 고도화 시스템 중지")
            
            self.is_running = False
            
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            logger.info("통합 고도화 시스템 중지 완료")
            
        except Exception as e:
            logger.error(f"시스템 중지 실패: {e}")

    def generate_comprehensive_signals(self, stock_codes: List[str], 
                                    price_data: Dict[str, pd.DataFrame],
                                    sentiment_data: Dict[str, Dict] = None,
                                    macro_data: Dict = None) -> Dict[str, AdvancedSignal]:
        """종합 투자 신호 생성"""
        try:
            logger.info(f"종합 투자 신호 생성 시작: {len(stock_codes)}개 종목")
            
            signals = {}
            
            for stock_code in stock_codes:
                if stock_code not in price_data:
                    logger.warning(f"가격 데이터 없음: {stock_code}")
                    continue
                
                # 개별 종목별 데이터 준비
                stock_price_data = price_data[stock_code]
                stock_sentiment = sentiment_data.get(stock_code, {}) if sentiment_data else None
                
                # 고도화된 신호 생성
                signal = self.signal_generator.generate_advanced_signal(
                    stock_code=stock_code,
                    price_data=stock_price_data,
                    sentiment_data=stock_sentiment,
                    macro_data=macro_data
                )
                
                # 신뢰도 필터링
                if signal.confidence >= self.config['min_signal_confidence']:
                    signals[stock_code] = signal
                    logger.info(f"신호 생성 완료: {stock_code} - {signal.signal_type.value} (신뢰도: {signal.confidence:.3f})")
                else:
                    logger.info(f"신뢰도 부족으로 신호 제외: {stock_code} (신뢰도: {signal.confidence:.3f})")
            
            # 신호 히스토리 저장
            self.signal_history.append({
                'timestamp': datetime.now(),
                'signals': signals,
                'total_signals': len(signals)
            })
            
            logger.info(f"종합 투자 신호 생성 완료: {len(signals)}개 신호")
            return signals
            
        except Exception as e:
            logger.error(f"종합 투자 신호 생성 실패: {e}")
            return {}

    def optimize_portfolio_with_signals(self, signals: Dict[str, AdvancedSignal],
                                      price_data: Dict[str, pd.DataFrame],
                                      current_portfolio: Portfolio = None) -> Portfolio:
        """신호 기반 포트폴리오 최적화"""
        try:
            logger.info("신호 기반 포트폴리오 최적화 시작")
            
            # 신호 강도에 따른 종목 필터링
            strong_signals = {}
            for stock_code, signal in signals.items():
                if signal.signal_type in [SignalType.STRONG_BUY, SignalType.BUY, SignalType.WEAK_BUY]:
                    # 신호 강도를 점수로 변환
                    signal_strength = self._convert_signal_to_strength(signal)
                    strong_signals[stock_code] = signal_strength
            
            if not strong_signals:
                logger.warning("매수 신호가 없습니다")
                return current_portfolio or self._create_default_portfolio()
            
            # 포트폴리오 크기 제한
            if len(strong_signals) > self.config['max_portfolio_size']:
                # 신호 강도 순으로 정렬하여 상위 종목만 선택
                sorted_signals = sorted(strong_signals.items(), key=lambda x: x[1], reverse=True)
                strong_signals = dict(sorted_signals[:self.config['max_portfolio_size']])
            
            # 수익률 데이터 준비
            returns_data = {}
            for stock_code in strong_signals.keys():
                if stock_code in price_data:
                    stock_returns = self.portfolio_optimizer.calculate_returns(price_data[stock_code])
                    if not stock_returns.empty:
                        returns_data[stock_code] = stock_returns
            
            if not returns_data:
                logger.warning("수익률 데이터가 없습니다")
                return current_portfolio or self._create_default_portfolio()
            
            # 수익률 데이터프레임 생성
            returns_df = pd.DataFrame(returns_data)
            
            # 신호 강도를 기대수익률 조정에 반영
            adjusted_returns = self._adjust_returns_with_signals(returns_df, strong_signals)
            
            # 포트폴리오 최적화
            portfolio = self.portfolio_optimizer.optimize_portfolio(
                returns_df,
                method=OptimizationMethod.MAX_SHARPE
            )
            
            # 리스크 관리 검증
            if not self._validate_portfolio_risk(portfolio):
                logger.warning("포트폴리오 리스크가 허용 범위를 초과합니다")
                portfolio = self._create_conservative_portfolio(returns_df)
            
            logger.info(f"포트폴리오 최적화 완료 - 기대 수익률: {portfolio.expected_return:.3f}, 변동성: {portfolio.volatility:.3f}")
            return portfolio
            
        except Exception as e:
            logger.error(f"신호 기반 포트폴리오 최적화 실패: {e}")
            return current_portfolio or self._create_default_portfolio()

    def _convert_signal_to_strength(self, signal: AdvancedSignal) -> float:
        """신호를 강도로 변환"""
        try:
            # 신호 타입별 기본 강도
            base_strengths = {
                SignalType.STRONG_BUY: 1.0,
                SignalType.BUY: 0.7,
                SignalType.WEAK_BUY: 0.4,
                SignalType.HOLD: 0.0,
                SignalType.WEAK_SELL: -0.4,
                SignalType.SELL: -0.7,
                SignalType.STRONG_SELL: -1.0
            }
            
            base_strength = base_strengths.get(signal.signal_type, 0.0)
            
            # 신뢰도와 점수를 반영한 최종 강도
            final_strength = base_strength * signal.confidence * (1 + abs(signal.score))
            
            return final_strength
            
        except Exception as e:
            logger.error(f"신호 강도 변환 실패: {e}")
            return 0.0

    def _adjust_returns_with_signals(self, returns_df: pd.DataFrame, 
                                   signal_strengths: Dict[str, float]) -> pd.DataFrame:
        """신호 강도에 따른 수익률 조정"""
        try:
            # 기본 기대수익률 계산
            base_returns = returns_df.mean() * 252
            
            # 신호 강도에 따른 조정
            adjusted_returns = base_returns.copy()
            for stock_code, strength in signal_strengths.items():
                if stock_code in adjusted_returns.index:
                    # 신호 강도에 따라 기대수익률 조정 (최대 ±20%)
                    adjustment = strength * 0.2
                    adjusted_returns[stock_code] += adjustment
            
            return adjusted_returns
            
        except Exception as e:
            logger.error(f"수익률 조정 실패: {e}")
            return returns_df.mean() * 252

    def _validate_portfolio_risk(self, portfolio: Portfolio) -> bool:
        """포트폴리오 리스크 검증"""
        try:
            # 변동성 검증
            if portfolio.volatility > 0.25:  # 25% 이상 변동성
                return False
            
            # VaR 검증
            if portfolio.var_95 < -0.05:  # 5% 이상 손실 위험
                return False
            
            # 최대 낙폭 검증
            if portfolio.max_drawdown < -self.config['max_drawdown_limit']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"포트폴리오 리스크 검증 실패: {e}")
            return False

    def _create_conservative_portfolio(self, returns_df: pd.DataFrame) -> Portfolio:
        """보수적 포트폴리오 생성"""
        try:
            logger.info("보수적 포트폴리오 생성")
            
            # 최소 분산 포트폴리오로 변경
            portfolio = self.portfolio_optimizer.optimize_portfolio(
                returns_df,
                method=OptimizationMethod.MIN_VARIANCE
            )
            
            return portfolio
            
        except Exception as e:
            logger.error(f"보수적 포트폴리오 생성 실패: {e}")
            return self._create_default_portfolio()

    def _create_default_portfolio(self) -> Portfolio:
        """기본 포트폴리오 생성"""
        try:
            # 현금 보유 포트폴리오
            default_asset = {
                'code': 'CASH',
                'name': '현금',
                'weight': 1.0,
                'expected_return': 0.02,
                'volatility': 0.0
            }
            
            portfolio = Portfolio(
                assets=[default_asset],
                weights=np.array([1.0]),
                expected_return=0.02,
                volatility=0.0,
                sharpe_ratio=0.0,
                var_95=0.0,
                cvar_95=0.0,
                max_drawdown=0.0,
                sector_allocation={'CASH': 1.0},
                risk_contribution={'CASH': 0.0},
                timestamp=datetime.now()
            )
            
            return portfolio
            
        except Exception as e:
            logger.error(f"기본 포트폴리오 생성 실패: {e}")
            return None

    def execute_rebalancing(self, new_portfolio: Portfolio, 
                          current_positions: Dict[str, float]) -> Dict[str, Dict]:
        """포트폴리오 리밸런싱 실행"""
        try:
            logger.info("포트폴리오 리밸런싱 실행")
            
            rebalancing_orders = {}
            
            # 현재 포지션과 목표 포지션 비교
            for asset in new_portfolio.assets:
                stock_code = asset.code
                target_weight = asset.weight
                current_weight = current_positions.get(stock_code, 0.0)
                
                weight_diff = target_weight - current_weight
                
                if abs(weight_diff) > 0.01:  # 1% 이상 차이
                    if weight_diff > 0:
                        # 매수 주문
                        order_type = "BUY"
                        quantity = weight_diff
                    else:
                        # 매도 주문
                        order_type = "SELL"
                        quantity = abs(weight_diff)
                    
                    rebalancing_orders[stock_code] = {
                        'order_type': order_type,
                        'quantity': quantity,
                        'current_weight': current_weight,
                        'target_weight': target_weight,
                        'weight_diff': weight_diff
                    }
            
            logger.info(f"리밸런싱 주문 생성 완료: {len(rebalancing_orders)}개 주문")
            return rebalancing_orders
            
        except Exception as e:
            logger.error(f"포트폴리오 리밸런싱 실행 실패: {e}")
            return {}

    def calculate_performance_metrics(self, portfolio: Portfolio, 
                                   historical_returns: pd.DataFrame) -> Dict:
        """성과 지표 계산"""
        try:
            # 포트폴리오 수익률 계산
            portfolio_returns = (historical_returns * portfolio.weights).sum(axis=1)
            
            # 기본 성과 지표
            total_return = (1 + portfolio_returns).prod() - 1
            annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
            annualized_volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = (annualized_return - self.portfolio_optimizer.risk_free_rate) / annualized_volatility
            
            # 추가 성과 지표
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            # 승률 계산
            positive_days = (portfolio_returns > 0).sum()
            total_days = len(portfolio_returns)
            win_rate = positive_days / total_days if total_days > 0 else 0
            
            performance_metrics = {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'annualized_volatility': annualized_volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'win_rate': win_rate,
                'positive_days': positive_days,
                'total_days': total_days,
                'timestamp': datetime.now()
            }
            
            # 성과 히스토리 저장
            self.performance_history.append(performance_metrics)
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"성과 지표 계산 실패: {e}")
            return {}

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        try:
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            return drawdown.min()
        except Exception as e:
            logger.error(f"최대 낙폭 계산 실패: {e}")
            return 0.0

    def _monitoring_loop(self):
        """모니터링 루프"""
        try:
            logger.info("모니터링 루프 시작")
            
            while self.is_running:
                try:
                    # 시스템 상태 확인
                    self._check_system_health()
                    
                    # 성과 모니터링
                    if self.current_portfolio:
                        self._monitor_portfolio_performance()
                    
                    # 리밸런싱 필요성 확인
                    self._check_rebalancing_needs()
                    
                    # 1시간마다 실행
                    time.sleep(3600)
                    
                except Exception as e:
                    logger.error(f"모니터링 루프 오류: {e}")
                    time.sleep(300)  # 5분 후 재시도
            
            logger.info("모니터링 루프 종료")
            
        except Exception as e:
            logger.error(f"모니터링 루프 시작 실패: {e}")

    def _check_system_health(self):
        """시스템 상태 확인"""
        try:
            # 각 컴포넌트 상태 확인
            components_status = {
                'signal_generator': self.signal_generator is not None,
                'portfolio_optimizer': self.portfolio_optimizer is not None,
                'trend_analyzer': self.trend_analyzer is not None
            }
            
            # 상태 로깅
            for component, status in components_status.items():
                if not status:
                    logger.warning(f"컴포넌트 상태 이상: {component}")
            
        except Exception as e:
            logger.error(f"시스템 상태 확인 실패: {e}")

    def _monitor_portfolio_performance(self):
        """포트폴리오 성과 모니터링"""
        try:
            if not self.current_portfolio:
                return
            
            # 실시간 성과 확인
            current_performance = {
                'expected_return': self.current_portfolio.expected_return,
                'volatility': self.current_portfolio.volatility,
                'sharpe_ratio': self.current_portfolio.sharpe_ratio,
                'max_drawdown': self.current_portfolio.max_drawdown,
                'timestamp': datetime.now()
            }
            
            # 성과 임계값 확인
            if current_performance['sharpe_ratio'] < 0.5:
                logger.warning("샤프 비율이 낮습니다")
            
            if current_performance['max_drawdown'] < -0.1:
                logger.warning("낙폭이 10%를 초과했습니다")
            
        except Exception as e:
            logger.error(f"포트폴리오 성과 모니터링 실패: {e}")

    def _check_rebalancing_needs(self):
        """리밸런싱 필요성 확인"""
        try:
            # 마지막 리밸런싱 시간 확인
            if not self.current_portfolio:
                return
            
            days_since_rebalance = (datetime.now() - self.current_portfolio.timestamp).days
            
            if days_since_rebalance >= self.config['rebalance_frequency']:
                logger.info("리밸런싱이 필요합니다")
                # 여기서 리밸런싱 로직 실행
                
        except Exception as e:
            logger.error(f"리밸런싱 필요성 확인 실패: {e}")

    def get_system_summary(self) -> Dict:
        """시스템 요약 정보"""
        try:
            summary = {
                'system_status': 'RUNNING' if self.is_running else 'STOPPED',
                'current_portfolio': {
                    'expected_return': self.current_portfolio.expected_return if self.current_portfolio else 0.0,
                    'volatility': self.current_portfolio.volatility if self.current_portfolio else 0.0,
                    'sharpe_ratio': self.current_portfolio.sharpe_ratio if self.current_portfolio else 0.0,
                    'asset_count': len(self.current_portfolio.assets) if self.current_portfolio else 0
                },
                'signal_history': {
                    'total_signals': len(self.signal_history),
                    'latest_signals': len(self.signal_history[-1]['signals']) if self.signal_history else 0
                },
                'performance_history': {
                    'total_records': len(self.performance_history),
                    'latest_sharpe': self.performance_history[-1]['sharpe_ratio'] if self.performance_history else 0.0
                },
                'config': self.config,
                'timestamp': datetime.now()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"시스템 요약 정보 생성 실패: {e}")
            return {}

def main():
    """테스트 함수"""
    # 통합 고도화 시스템 초기화
    system = IntegratedAdvancedSystem()
    
    # 샘플 데이터 생성
    stock_codes = ['005930', '000660', '035420', '035720', '051910']
    
    # 가격 데이터 생성
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    price_data = {}
    
    for stock_code in stock_codes:
        price_data[stock_code] = pd.DataFrame({
            'open': np.random.normal(100, 5, len(dates)),
            'high': np.random.normal(105, 5, len(dates)),
            'low': np.random.normal(95, 5, len(dates)),
            'close': np.random.normal(100, 5, len(dates)),
            'volume': np.random.normal(1000000, 200000, len(dates))
        }, index=dates)
    
    # 시스템 시작
    system.start_system()
    
    # 종합 신호 생성
    signals = system.generate_comprehensive_signals(stock_codes, price_data)
    
    # 포트폴리오 최적화
    portfolio = system.optimize_portfolio_with_signals(signals, price_data)
    
    # 성과 지표 계산
    returns_df = pd.DataFrame()
    for stock_code in stock_codes:
        if stock_code in price_data:
            stock_returns = system.portfolio_optimizer.calculate_returns(price_data[stock_code])
            if not stock_returns.empty:
                returns_df[stock_code] = stock_returns
    
    if not returns_df.empty:
        performance = system.calculate_performance_metrics(portfolio, returns_df)
        
        print("=== 통합 고도화 시스템 테스트 결과 ===")
        print(f"생성된 신호 수: {len(signals)}")
        print(f"포트폴리오 자산 수: {len(portfolio.assets)}")
        print(f"기대 수익률: {portfolio.expected_return:.3f}")
        print(f"변동성: {portfolio.volatility:.3f}")
        print(f"샤프 비율: {portfolio.sharpe_ratio:.3f}")
        print(f"총 수익률: {performance.get('total_return', 0):.3f}")
        print(f"승률: {performance.get('win_rate', 0):.3f}")
    
    # 시스템 중지
    system.stop_system()

if __name__ == "__main__":
    main() 