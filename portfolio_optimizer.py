#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포트폴리오 최적화 시스템
Modern Portfolio Theory, Black-Litterman 모델, 리스크 관리 기반 포트폴리오 최적화
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from scipy.optimize import minimize
from scipy.stats import norm
import cvxpy as cp
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

class OptimizationMethod(Enum):
    """최적화 방법"""
    MARKOWITZ = "markowitz"
    BLACK_LITTERMAN = "black_litterman"
    RISK_PARITY = "risk_parity"
    MAX_SHARPE = "max_sharpe"
    MIN_VARIANCE = "min_variance"
    EQUAL_WEIGHT = "equal_weight"

class RiskMeasure(Enum):
    """리스크 측정 방법"""
    VARIANCE = "variance"
    SEMI_VARIANCE = "semi_variance"
    VAR = "var"  # Value at Risk
    CVAR = "cvar"  # Conditional Value at Risk
    DOWNSIDE_DEVIATION = "downside_deviation"

@dataclass
class Asset:
    """자산 정보"""
    code: str
    name: str
    weight: float = 0.0
    expected_return: float = 0.0
    volatility: float = 0.0
    beta: float = 1.0
    sector: str = ""
    market_cap: float = 0.0
    liquidity_score: float = 0.0

@dataclass
class Portfolio:
    """포트폴리오 정보"""
    assets: List[Asset]
    weights: np.ndarray
    expected_return: float
    volatility: float
    sharpe_ratio: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    sector_allocation: Dict[str, float]
    risk_contribution: Dict[str, float]
    timestamp: datetime
    metadata: Dict = None

class PortfolioOptimizer:
    """포트폴리오 최적화기"""
    
    def __init__(self):
        """초기화"""
        logger.info("포트폴리오 최적화기 초기화")
        
        # 설정
        self.risk_free_rate = 0.02  # 2% 무위험 수익률
        self.target_return = 0.08   # 8% 목표 수익률
        self.max_weight = 0.3       # 최대 자산 비중 30%
        self.min_weight = 0.01      # 최소 자산 비중 1%
        self.rebalance_frequency = 30  # 30일마다 리밸런싱
        
        # 제약조건
        self.constraints = {
            'long_only': True,      # 롱 포지션만
            'sector_limit': 0.4,    # 섹터별 최대 비중 40%
            'liquidity_min': 0.5    # 최소 유동성 점수 0.5
        }
        
        # 성능 추적
        self.performance_history = []
        
        logger.info("포트폴리오 최적화기 초기화 완료")

    def calculate_returns(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """수익률 계산"""
        try:
            returns = price_data.pct_change().dropna()
            return returns
        except Exception as e:
            logger.error(f"수익률 계산 실패: {e}")
            return pd.DataFrame()

    def calculate_covariance_matrix(self, returns: pd.DataFrame) -> np.ndarray:
        """공분산 행렬 계산"""
        try:
            # 샤플-윈도우 방법으로 공분산 행렬 계산
            cov_matrix = returns.ewm(halflife=60).cov()
            
            # 최근 공분산 행렬 추출
            latest_cov = cov_matrix.iloc[-len(returns.columns):, -len(returns.columns):]
            
            return latest_cov.values
            
        except Exception as e:
            logger.error(f"공분산 행렬 계산 실패: {e}")
            return np.eye(len(returns.columns))

    def estimate_expected_returns(self, returns: pd.DataFrame, method: str = "historical") -> np.ndarray:
        """기대수익률 추정"""
        try:
            if method == "historical":
                # 과거 평균 수익률
                expected_returns = returns.mean().values * 252  # 연율화
            elif method == "capm":
                # CAPM 기반 기대수익률
                market_return = returns.mean().mean() * 252
                betas = self._calculate_betas(returns)
                expected_returns = self.risk_free_rate + betas * (market_return - self.risk_free_rate)
            elif method == "black_litterman":
                # Black-Litterman 모델
                expected_returns = self._black_litterman_returns(returns)
            else:
                expected_returns = returns.mean().values * 252
            
            return expected_returns
            
        except Exception as e:
            logger.error(f"기대수익률 추정 실패: {e}")
            return np.zeros(len(returns.columns))

    def _calculate_betas(self, returns: pd.DataFrame) -> np.ndarray:
        """베타 계수 계산"""
        try:
            market_returns = returns.mean(axis=1)  # 시장 수익률 (등가중)
            betas = []
            
            for col in returns.columns:
                asset_returns = returns[col]
                # 베타 = Cov(asset, market) / Var(market)
                covariance = np.cov(asset_returns, market_returns)[0, 1]
                variance = np.var(market_returns)
                beta = covariance / variance if variance > 0 else 1.0
                betas.append(beta)
            
            return np.array(betas)
            
        except Exception as e:
            logger.error(f"베타 계산 실패: {e}")
            return np.ones(len(returns.columns))

    def _black_litterman_returns(self, returns: pd.DataFrame) -> np.ndarray:
        """Black-Litterman 모델 기대수익률"""
        try:
            # 시장 균형 기대수익률 (CAPM 기반)
            market_return = returns.mean().mean() * 252
            betas = self._calculate_betas(returns)
            equilibrium_returns = self.risk_free_rate + betas * (market_return - self.risk_free_rate)
            
            # 투자자 관점 (여기서는 시장 관점과 동일하게 설정)
            investor_views = equilibrium_returns
            
            # 관점의 불확실성
            tau = 0.05  # 스케일링 팩터
            cov_matrix = self.calculate_covariance_matrix(returns)
            omega = tau * cov_matrix
            
            # Black-Litterman 공식
            # μ = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) * [(τΣ)^(-1)Π + P'Ω^(-1)Q]
            # 여기서는 단순화된 버전 사용
            
            bl_returns = 0.7 * equilibrium_returns + 0.3 * investor_views
            
            return bl_returns
            
        except Exception as e:
            logger.error(f"Black-Litterman 수익률 계산 실패: {e}")
            return returns.mean().values * 252

    def optimize_portfolio(self, returns: pd.DataFrame, method: OptimizationMethod = OptimizationMethod.MAX_SHARPE,
                         constraints: Dict = None) -> Portfolio:
        """포트폴리오 최적화"""
        try:
            logger.info(f"포트폴리오 최적화 시작: {method.value}")
            
            # 기본 설정 적용
            if constraints is None:
                constraints = self.constraints
            
            # 기대수익률과 공분산 행렬 계산
            expected_returns = self.estimate_expected_returns(returns)
            cov_matrix = self.calculate_covariance_matrix(returns)
            
            n_assets = len(returns.columns)
            
            if method == OptimizationMethod.MARKOWITZ:
                weights = self._markowitz_optimization(expected_returns, cov_matrix, constraints)
            elif method == OptimizationMethod.MAX_SHARPE:
                weights = self._max_sharpe_optimization(expected_returns, cov_matrix, constraints)
            elif method == OptimizationMethod.MIN_VARIANCE:
                weights = self._min_variance_optimization(cov_matrix, constraints)
            elif method == OptimizationMethod.RISK_PARITY:
                weights = self._risk_parity_optimization(cov_matrix, constraints)
            elif method == OptimizationMethod.EQUAL_WEIGHT:
                weights = np.ones(n_assets) / n_assets
            else:
                weights = self._max_sharpe_optimization(expected_returns, cov_matrix, constraints)
            
            # 포트폴리오 성과 계산
            portfolio = self._calculate_portfolio_performance(
                returns.columns, weights, expected_returns, cov_matrix, returns
            )
            
            logger.info(f"포트폴리오 최적화 완료 - 샤프 비율: {portfolio.sharpe_ratio:.3f}")
            return portfolio
            
        except Exception as e:
            logger.error(f"포트폴리오 최적화 실패: {e}")
            return self._create_default_portfolio(returns.columns)

    def _markowitz_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                              constraints: Dict) -> np.ndarray:
        """마코위츠 최적화"""
        try:
            n_assets = len(expected_returns)
            
            # 목적 함수: 위험 최소화 (수익률 제약 조건 하에서)
            def objective(weights):
                portfolio_variance = weights.T @ cov_matrix @ weights
                return portfolio_variance
            
            # 제약 조건
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # 가중치 합 = 1
                {'type': 'eq', 'fun': lambda x: x @ expected_returns - self.target_return}  # 목표 수익률
            ]
            
            # 경계 조건
            bounds = [(self.min_weight, self.max_weight)] * n_assets
            
            # 초기 가중치 (등가중)
            initial_weights = np.ones(n_assets) / n_assets
            
            # 최적화
            result = minimize(
                objective, initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("마코위츠 최적화 실패, 등가중 사용")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"마코위츠 최적화 실패: {e}")
            return np.ones(len(expected_returns)) / len(expected_returns)

    def _max_sharpe_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                               constraints: Dict) -> np.ndarray:
        """최대 샤프 비율 최적화"""
        try:
            n_assets = len(expected_returns)
            
            # 목적 함수: 샤프 비율 최대화 (음수로 변환하여 최소화)
            def objective(weights):
                portfolio_return = weights @ expected_returns
                portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
                return -sharpe_ratio  # 최대화를 위해 음수 반환
            
            # 제약 조건
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 가중치 합 = 1
            ]
            
            # 경계 조건
            bounds = [(self.min_weight, self.max_weight)] * n_assets
            
            # 초기 가중치
            initial_weights = np.ones(n_assets) / n_assets
            
            # 최적화
            result = minimize(
                objective, initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("최대 샤프 비율 최적화 실패, 등가중 사용")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"최대 샤프 비율 최적화 실패: {e}")
            return np.ones(len(expected_returns)) / len(expected_returns)

    def _min_variance_optimization(self, cov_matrix: np.ndarray, constraints: Dict) -> np.ndarray:
        """최소 분산 최적화"""
        try:
            n_assets = len(cov_matrix)
            
            # 목적 함수: 포트폴리오 분산 최소화
            def objective(weights):
                return weights.T @ cov_matrix @ weights
            
            # 제약 조건
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 가중치 합 = 1
            ]
            
            # 경계 조건
            bounds = [(self.min_weight, self.max_weight)] * n_assets
            
            # 초기 가중치
            initial_weights = np.ones(n_assets) / n_assets
            
            # 최적화
            result = minimize(
                objective, initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("최소 분산 최적화 실패, 등가중 사용")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"최소 분산 최적화 실패: {e}")
            return np.ones(len(cov_matrix)) / len(cov_matrix)

    def _risk_parity_optimization(self, cov_matrix: np.ndarray, constraints: Dict) -> np.ndarray:
        """리스크 패리티 최적화"""
        try:
            n_assets = len(cov_matrix)
            
            # 목적 함수: 리스크 기여도 차이 최소화
            def objective(weights):
                portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
                risk_contributions = weights * (cov_matrix @ weights) / portfolio_volatility
                target_risk = portfolio_volatility / n_assets
                risk_diff = risk_contributions - target_risk
                return np.sum(risk_diff ** 2)
            
            # 제약 조건
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 가중치 합 = 1
            ]
            
            # 경계 조건
            bounds = [(self.min_weight, self.max_weight)] * n_assets
            
            # 초기 가중치
            initial_weights = np.ones(n_assets) / n_assets
            
            # 최적화
            result = minimize(
                objective, initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("리스크 패리티 최적화 실패, 등가중 사용")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"리스크 패리티 최적화 실패: {e}")
            return np.ones(len(cov_matrix)) / len(cov_matrix)

    def _calculate_portfolio_performance(self, asset_names: List[str], weights: np.ndarray,
                                       expected_returns: np.ndarray, cov_matrix: np.ndarray,
                                       returns: pd.DataFrame) -> Portfolio:
        """포트폴리오 성과 계산"""
        try:
            # 기본 성과 지표
            portfolio_return = weights @ expected_returns
            portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # VaR 및 CVaR 계산
            portfolio_returns = (returns * weights).sum(axis=1)
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            # 최대 낙폭 계산
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # 섹터 배분 (간단한 예시)
            sector_allocation = {"TECH": 0.4, "FINANCE": 0.3, "HEALTHCARE": 0.3}
            
            # 리스크 기여도
            risk_contributions = weights * (cov_matrix @ weights) / portfolio_volatility
            risk_contribution_dict = {asset_names[i]: risk_contributions[i] for i in range(len(asset_names))}
            
            # 자산 정보 생성
            assets = []
            for i, name in enumerate(asset_names):
                asset = Asset(
                    code=name,
                    name=name,
                    weight=weights[i],
                    expected_return=expected_returns[i],
                    volatility=np.sqrt(cov_matrix[i, i])
                )
                assets.append(asset)
            
            portfolio = Portfolio(
                assets=assets,
                weights=weights,
                expected_return=portfolio_return,
                volatility=portfolio_volatility,
                sharpe_ratio=sharpe_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                max_drawdown=max_drawdown,
                sector_allocation=sector_allocation,
                risk_contribution=risk_contribution_dict,
                timestamp=datetime.now(),
                metadata={
                    'optimization_method': 'max_sharpe',
                    'risk_free_rate': self.risk_free_rate,
                    'target_return': self.target_return
                }
            )
            
            return portfolio
            
        except Exception as e:
            logger.error(f"포트폴리오 성과 계산 실패: {e}")
            return self._create_default_portfolio(asset_names)

    def _create_default_portfolio(self, asset_names: List[str]) -> Portfolio:
        """기본 포트폴리오 생성"""
        n_assets = len(asset_names)
        weights = np.ones(n_assets) / n_assets
        
        assets = []
        for i, name in enumerate(asset_names):
            asset = Asset(
                code=name,
                name=name,
                weight=weights[i]
            )
            assets.append(asset)
        
        return Portfolio(
            assets=assets,
            weights=weights,
            expected_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            var_95=0.0,
            cvar_95=0.0,
            max_drawdown=0.0,
            sector_allocation={},
            risk_contribution={},
            timestamp=datetime.now()
        )

    def rebalance_portfolio(self, current_portfolio: Portfolio, new_signals: Dict[str, float],
                          returns: pd.DataFrame) -> Portfolio:
        """포트폴리오 리밸런싱"""
        try:
            logger.info("포트폴리오 리밸런싱 시작")
            
            # 새로운 신호를 반영한 기대수익률 조정
            current_returns = self.estimate_expected_returns(returns)
            
            # 신호에 따른 기대수익률 조정
            adjusted_returns = current_returns.copy()
            for asset_code, signal_strength in new_signals.items():
                if asset_code in returns.columns:
                    idx = returns.columns.get_loc(asset_code)
                    # 신호 강도에 따라 기대수익률 조정
                    adjustment = signal_strength * 0.1  # 10% 기준
                    adjusted_returns[idx] += adjustment
            
            # 최적화 실행
            cov_matrix = self.calculate_covariance_matrix(returns)
            new_weights = self._max_sharpe_optimization(adjusted_returns, cov_matrix, self.constraints)
            
            # 새로운 포트폴리오 생성
            new_portfolio = self._calculate_portfolio_performance(
                returns.columns, new_weights, adjusted_returns, cov_matrix, returns
            )
            
            # 리밸런싱 비용 계산
            rebalancing_cost = self._calculate_rebalancing_cost(
                current_portfolio.weights, new_weights
            )
            
            logger.info(f"포트폴리오 리밸런싱 완료 - 비용: {rebalancing_cost:.4f}")
            return new_portfolio
            
        except Exception as e:
            logger.error(f"포트폴리오 리밸런싱 실패: {e}")
            return current_portfolio

    def _calculate_rebalancing_cost(self, old_weights: np.ndarray, new_weights: np.ndarray) -> float:
        """리밸런싱 비용 계산"""
        try:
            # 거래 비용 (0.1% 가정)
            transaction_cost = 0.001
            
            # 가중치 변화량
            weight_changes = np.abs(new_weights - old_weights)
            
            # 총 거래 비용
            total_cost = np.sum(weight_changes) * transaction_cost
            
            return total_cost
            
        except Exception as e:
            logger.error(f"리밸런싱 비용 계산 실패: {e}")
            return 0.0

    def backtest_portfolio(self, returns: pd.DataFrame, rebalance_frequency: int = 30) -> Dict:
        """포트폴리오 백테스팅"""
        try:
            logger.info("포트폴리오 백테스팅 시작")
            
            # 백테스팅 결과 저장
            portfolio_values = []
            weights_history = []
            performance_metrics = []
            
            # 초기 포트폴리오 생성
            initial_returns = returns.iloc[:60]  # 처음 60일 데이터로 초기 포트폴리오 생성
            current_portfolio = self.optimize_portfolio(initial_returns)
            
            # 백테스팅 루프
            for i in range(60, len(returns), rebalance_frequency):
                # 현재 시점까지의 데이터
                current_data = returns.iloc[:i+1]
                
                # 리밸런싱
                if i > 60:  # 첫 번째는 제외
                    current_portfolio = self.rebalance_portfolio(
                        current_portfolio, {}, current_data
                    )
                
                # 포트폴리오 가치 계산
                future_returns = returns.iloc[i:i+rebalance_frequency]
                portfolio_returns = (future_returns * current_portfolio.weights).sum(axis=1)
                
                # 누적 가치 계산
                cumulative_value = (1 + portfolio_returns).cumprod()
                portfolio_values.extend(cumulative_value.values)
                weights_history.append(current_portfolio.weights.copy())
                
                # 성과 지표 계산
                metrics = {
                    'return': portfolio_returns.mean() * 252,
                    'volatility': portfolio_returns.std() * np.sqrt(252),
                    'sharpe_ratio': (portfolio_returns.mean() * 252 - self.risk_free_rate) / (portfolio_returns.std() * np.sqrt(252)),
                    'max_drawdown': self._calculate_max_drawdown(cumulative_value),
                    'var_95': np.percentile(portfolio_returns, 5)
                }
                performance_metrics.append(metrics)
            
            # 전체 성과 요약
            total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
            total_volatility = np.std(np.diff(portfolio_values) / portfolio_values[:-1]) * np.sqrt(252)
            total_sharpe = (total_return - self.risk_free_rate) / total_volatility if total_volatility > 0 else 0
            
            backtest_results = {
                'portfolio_values': portfolio_values,
                'weights_history': weights_history,
                'performance_metrics': performance_metrics,
                'summary': {
                    'total_return': total_return,
                    'total_volatility': total_volatility,
                    'total_sharpe_ratio': total_sharpe,
                    'max_drawdown': self._calculate_max_drawdown(portfolio_values),
                    'rebalance_count': len(weights_history)
                }
            }
            
            logger.info(f"백테스팅 완료 - 총 수익률: {total_return:.3f}")
            return backtest_results
            
        except Exception as e:
            logger.error(f"백테스팅 실패: {e}")
            return {}

    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """최대 낙폭 계산"""
        try:
            peak = values[0]
            max_dd = 0
            
            for value in values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            
            return max_dd
            
        except Exception as e:
            logger.error(f"최대 낙폭 계산 실패: {e}")
            return 0.0

def main():
    """테스트 함수"""
    # 포트폴리오 최적화기 초기화
    optimizer = PortfolioOptimizer()
    
    # 샘플 데이터 생성
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n_assets = 10
    
    # 랜덤 수익률 생성
    returns_data = {}
    for i in range(n_assets):
        asset_name = f"ASSET_{i+1:02d}"
        returns_data[asset_name] = np.random.normal(0.001, 0.02, len(dates))
    
    returns_df = pd.DataFrame(returns_data, index=dates)
    
    # 포트폴리오 최적화
    portfolio = optimizer.optimize_portfolio(
        returns_df, 
        method=OptimizationMethod.MAX_SHARPE
    )
    
    print(f"최적화된 포트폴리오 성과:")
    print(f"기대 수익률: {portfolio.expected_return:.4f}")
    print(f"변동성: {portfolio.volatility:.4f}")
    print(f"샤프 비율: {portfolio.sharpe_ratio:.4f}")
    print(f"VaR (95%): {portfolio.var_95:.4f}")
    print(f"최대 낙폭: {portfolio.max_drawdown:.4f}")
    
    # 백테스팅
    backtest_results = optimizer.backtest_portfolio(returns_df)
    if backtest_results:
        summary = backtest_results['summary']
        print(f"\n백테스팅 결과:")
        print(f"총 수익률: {summary['total_return']:.4f}")
        print(f"총 변동성: {summary['total_volatility']:.4f}")
        print(f"총 샤프 비율: {summary['total_sharpe_ratio']:.4f}")

if __name__ == "__main__":
    main() 