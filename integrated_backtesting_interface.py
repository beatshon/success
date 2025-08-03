#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 백테스팅 인터페이스
백테스팅 시스템과 자동매매 시스템을 연결하여 전략 검증 및 최적화를 제공합니다.
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np

# 시스템 모듈들
from backtesting_system import (
    BacktestingEngine, BacktestConfig, BacktestMode, 
    MonteCarloSimulator, BacktestAnalyzer
)
from integrated_auto_trader import IntegratedAutoTrader, TradeConfig, TradingMode
from trading_strategy import (
    StrategyManager, create_default_strategies, 
    StrategyConfig, StrategyType
)

class OptimizationMode(Enum):
    """최적화 모드"""
    PARAMETER = "파라미터"
    STRATEGY = "전략"
    PORTFOLIO = "포트폴리오"
    RISK = "위험관리"

@dataclass
class OptimizationResult:
    """최적화 결과"""
    strategy_name: str
    parameters: Dict
    backtest_result: any
    performance_score: float
    risk_score: float
    combined_score: float

class IntegratedBacktestingInterface:
    """통합 백테스팅 인터페이스"""
    
    def __init__(self):
        self.backtest_engine = None
        self.auto_trader = None
        self.optimization_results = []
        self.current_strategy = None
        
        logger.info("통합 백테스팅 인터페이스 초기화 완료")
    
    def setup_backtesting(self, config: BacktestConfig) -> bool:
        """백테스팅 시스템 설정"""
        try:
            logger.info("백테스팅 시스템 설정")
            
            self.backtest_engine = BacktestingEngine(config)
            
            if not self.backtest_engine.load_data():
                logger.error("백테스팅 데이터 로드 실패")
                return False
            
            logger.info("백테스팅 시스템 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"백테스팅 시스템 설정 오류: {e}")
            return False
    
    def setup_auto_trader(self, config: TradeConfig) -> bool:
        """자동매매 시스템 설정"""
        try:
            logger.info("자동매매 시스템 설정")
            
            self.auto_trader = IntegratedAutoTrader(config)
            
            if not self.auto_trader.initialize():
                logger.error("자동매매 시스템 초기화 실패")
                return False
            
            logger.info("자동매매 시스템 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"자동매매 시스템 설정 오류: {e}")
            return False
    
    def validate_strategy(self, strategy_config: StrategyConfig) -> Dict:
        """전략 검증"""
        try:
            logger.info(f"전략 검증: {strategy_config.strategy_type.value}")
            
            # 백테스팅으로 전략 검증
            if not self.backtest_engine:
                logger.error("백테스팅 엔진이 설정되지 않았습니다.")
                return {}
            
            # 전략 매니저 설정
            strategy_manager = StrategyManager()
            
            # 전략 생성 및 추가
            strategy = self._create_strategy(strategy_config)
            if not strategy:
                logger.error("전략 생성 실패")
                return {}
            
            strategy_manager.add_strategy("validation", strategy)
            self.backtest_engine.strategy_manager = strategy_manager
            
            # 백테스트 실행
            result = self.backtest_engine.run_backtest()
            if not result:
                logger.error("백테스트 실행 실패")
                return {}
            
            # 결과 분석
            validation_result = {
                'strategy_name': strategy_config.strategy_type.value,
                'parameters': strategy_config.parameters,
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'win_rate': result.win_rate,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'total_trades': result.total_trades,
                'volatility': result.volatility,
                'calmar_ratio': result.calmar_ratio,
                'validation_score': self._calculate_validation_score(result)
            }
            
            logger.info(f"전략 검증 완료: 수익률 {result.total_return:.2%}, 승률 {result.win_rate:.1f}%")
            return validation_result
            
        except Exception as e:
            logger.error(f"전략 검증 오류: {e}")
            return {}
    
    def optimize_strategy(self, strategy_type: StrategyType, 
                         parameter_ranges: Dict, 
                         optimization_criteria: str = "sharpe_ratio") -> OptimizationResult:
        """전략 최적화"""
        try:
            logger.info(f"전략 최적화 시작: {strategy_type.value}")
            
            best_result = None
            best_params = None
            best_score = -float('inf')
            
            # 파라미터 조합 생성
            param_combinations = self._generate_parameter_combinations(parameter_ranges)
            
            logger.info(f"총 {len(param_combinations)}개 파라미터 조합 테스트")
            
            for i, params in enumerate(param_combinations):
                logger.info(f"파라미터 조합 {i+1}/{len(param_combinations)}: {params}")
                
                # 전략 설정
                strategy_config = StrategyConfig(
                    strategy_type=strategy_type,
                    parameters=params
                )
                
                # 전략 검증
                validation_result = self.validate_strategy(strategy_config)
                if not validation_result:
                    continue
                
                # 최적화 점수 계산
                score = self._calculate_optimization_score(validation_result, optimization_criteria)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = validation_result
            
            if best_result:
                optimization_result = OptimizationResult(
                    strategy_name=strategy_type.value,
                    parameters=best_params,
                    backtest_result=best_result,
                    performance_score=best_result['total_return'],
                    risk_score=1 - best_result['max_drawdown'],  # 낙폭이 작을수록 높은 점수
                    combined_score=best_score
                )
                
                self.optimization_results.append(optimization_result)
                
                logger.info(f"최적화 완료: {best_params}")
                logger.info(f"최고 점수: {best_score:.4f}")
                
                return optimization_result
            
            logger.error("최적화 실패: 유효한 결과가 없습니다.")
            return None
            
        except Exception as e:
            logger.error(f"전략 최적화 오류: {e}")
            return None
    
    def run_comprehensive_analysis(self) -> Dict:
        """종합 분석 실행"""
        try:
            logger.info("종합 분석 시작")
            
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'strategy_analysis': [],
                'optimization_results': [],
                'recommendations': []
            }
            
            # 1. 기본 전략 분석
            basic_strategies = [
                (StrategyType.MOVING_AVERAGE_CROSSOVER, {'short_period': 5, 'long_period': 20}),
                (StrategyType.RSI_STRATEGY, {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70}),
                (StrategyType.BOLLINGER_BANDS, {'period': 20, 'std_dev': 2.0}),
                (StrategyType.MACD_STRATEGY, {'fast_period': 12, 'slow_period': 26, 'signal_period': 9})
            ]
            
            for strategy_type, params in basic_strategies:
                strategy_config = StrategyConfig(strategy_type=strategy_type, parameters=params)
                validation_result = self.validate_strategy(strategy_config)
                
                if validation_result:
                    analysis_result['strategy_analysis'].append(validation_result)
            
            # 2. 최적화 결과 분석
            for opt_result in self.optimization_results:
                analysis_result['optimization_results'].append({
                    'strategy_name': opt_result.strategy_name,
                    'parameters': opt_result.parameters,
                    'performance_score': opt_result.performance_score,
                    'risk_score': opt_result.risk_score,
                    'combined_score': opt_result.combined_score
                })
            
            # 3. 권장사항 생성
            analysis_result['recommendations'] = self._generate_recommendations(analysis_result)
            
            logger.info("종합 분석 완료")
            return analysis_result
            
        except Exception as e:
            logger.error(f"종합 분석 오류: {e}")
            return {}
    
    def apply_optimized_strategy(self, optimization_result: OptimizationResult) -> bool:
        """최적화된 전략을 자동매매 시스템에 적용"""
        try:
            logger.info("최적화된 전략 적용")
            
            if not self.auto_trader:
                logger.error("자동매매 시스템이 설정되지 않았습니다.")
                return False
            
            # 최적화된 전략 생성
            strategy_config = StrategyConfig(
                strategy_type=self._get_strategy_type(optimization_result.strategy_name),
                parameters=optimization_result.parameters
            )
            
            strategy = self._create_strategy(strategy_config)
            if not strategy:
                logger.error("전략 생성 실패")
                return False
            
            # 자동매매 시스템에 전략 적용
            self.auto_trader.strategy_manager = StrategyManager()
            self.auto_trader.strategy_manager.add_strategy("optimized", strategy)
            
            logger.info("최적화된 전략 적용 완료")
            return True
            
        except Exception as e:
            logger.error(f"전략 적용 오류: {e}")
            return False
    
    def generate_performance_report(self) -> str:
        """성과 리포트 생성"""
        try:
            report = "=== 통합 백테스팅 성과 리포트 ===\n"
            report += f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # 전략 분석 결과
            if hasattr(self, 'optimization_results') and self.optimization_results:
                report += "=== 최적화 결과 ===\n"
                for i, result in enumerate(self.optimization_results, 1):
                    report += f"{i}. {result.strategy_name}\n"
                    report += f"   파라미터: {result.parameters}\n"
                    report += f"   성과 점수: {result.performance_score:.2%}\n"
                    report += f"   위험 점수: {result.risk_score:.2%}\n"
                    report += f"   종합 점수: {result.combined_score:.4f}\n\n"
            
            # 권장사항
            if hasattr(self, 'current_strategy') and self.current_strategy:
                report += "=== 현재 적용된 전략 ===\n"
                report += f"전략: {self.current_strategy}\n\n"
            
            return report
            
        except Exception as e:
            logger.error(f"성과 리포트 생성 오류: {e}")
            return "리포트 생성 실패"
    
    def _create_strategy(self, strategy_config: StrategyConfig):
        """전략 생성"""
        try:
            if strategy_config.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
                from trading_strategy import MovingAverageCrossoverStrategy
                return MovingAverageCrossoverStrategy(strategy_config)
            elif strategy_config.strategy_type == StrategyType.RSI_STRATEGY:
                from trading_strategy import RSIStrategy
                return RSIStrategy(strategy_config)
            elif strategy_config.strategy_type == StrategyType.BOLLINGER_BANDS:
                from trading_strategy import BollingerBandsStrategy
                return BollingerBandsStrategy(strategy_config)
            elif strategy_config.strategy_type == StrategyType.MACD_STRATEGY:
                from trading_strategy import MACDStrategy
                return MACDStrategy(strategy_config)
            else:
                logger.error(f"지원하지 않는 전략 타입: {strategy_config.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"전략 생성 오류: {e}")
            return None
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict) -> List[Dict]:
        """파라미터 조합 생성"""
        import itertools
        
        try:
            # 파라미터 값 리스트 생성
            param_values = []
            param_names = []
            
            for param_name, param_range in parameter_ranges.items():
                if isinstance(param_range, (list, tuple)):
                    param_values.append(param_range)
                elif isinstance(param_range, dict):
                    # 범위 지정 (start, end, step)
                    start = param_range.get('start', 0)
                    end = param_range.get('end', 100)
                    step = param_range.get('step', 1)
                    param_values.append(list(range(start, end + 1, step)))
                else:
                    param_values.append([param_range])
                
                param_names.append(param_name)
            
            # 모든 조합 생성
            combinations = list(itertools.product(*param_values))
            
            # 딕셔너리 형태로 변환
            result = []
            for combo in combinations:
                param_dict = {}
                for i, param_name in enumerate(param_names):
                    param_dict[param_name] = combo[i]
                result.append(param_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"파라미터 조합 생성 오류: {e}")
            return []
    
    def _calculate_validation_score(self, result: any) -> float:
        """검증 점수 계산"""
        try:
            # 수익률, 승률, 샤프 비율, 낙폭을 종합한 점수
            return_score = result.total_return * 0.4
            win_score = result.win_rate / 100 * 0.2
            sharpe_score = min(result.sharpe_ratio / 2, 1.0) * 0.3  # 샤프 비율 2를 최대값으로
            drawdown_score = (1 - result.max_drawdown) * 0.1  # 낙폭이 작을수록 높은 점수
            
            return return_score + win_score + sharpe_score + drawdown_score
            
        except Exception as e:
            logger.error(f"검증 점수 계산 오류: {e}")
            return 0.0
    
    def _calculate_optimization_score(self, validation_result: Dict, criteria: str) -> float:
        """최적화 점수 계산"""
        try:
            if criteria == "total_return":
                return validation_result['total_return']
            elif criteria == "sharpe_ratio":
                return validation_result['sharpe_ratio']
            elif criteria == "win_rate":
                return validation_result['win_rate'] / 100
            elif criteria == "calmar_ratio":
                return validation_result['calmar_ratio']
            elif criteria == "combined":
                return validation_result['validation_score']
            else:
                return validation_result['validation_score']
                
        except Exception as e:
            logger.error(f"최적화 점수 계산 오류: {e}")
            return 0.0
    
    def _get_strategy_type(self, strategy_name: str) -> StrategyType:
        """전략 이름으로 타입 반환"""
        strategy_map = {
            "이동평균크로스오버": StrategyType.MOVING_AVERAGE_CROSSOVER,
            "RSI전략": StrategyType.RSI_STRATEGY,
            "볼린저밴드": StrategyType.BOLLINGER_BANDS,
            "MACD전략": StrategyType.MACD_STRATEGY
        }
        return strategy_map.get(strategy_name, StrategyType.MOVING_AVERAGE_CROSSOVER)
    
    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        try:
            # 전략 분석 결과에서 최고 성과 전략 찾기
            if analysis_result['strategy_analysis']:
                best_strategy = max(analysis_result['strategy_analysis'], 
                                  key=lambda x: x['validation_score'])
                
                recommendations.append(f"최고 성과 전략: {best_strategy['strategy_name']} (수익률: {best_strategy['total_return']:.2%})")
            
            # 최적화 결과에서 최고 점수 전략 찾기
            if analysis_result['optimization_results']:
                best_optimized = max(analysis_result['optimization_results'], 
                                   key=lambda x: x['combined_score'])
                
                recommendations.append(f"최적화된 전략: {best_optimized['strategy_name']} (종합점수: {best_optimized['combined_score']:.4f})")
            
            # 위험 관리 권장사항
            recommendations.append("위험 관리: 최대 낙폭 20% 이하 유지 권장")
            recommendations.append("포지션 관리: 단일 종목 최대 20% 비중 권장")
            
        except Exception as e:
            logger.error(f"권장사항 생성 오류: {e}")
        
        return recommendations

def main():
    """메인 함수"""
    logger.info("통합 백테스팅 인터페이스 시작")
    
    # 인터페이스 생성
    interface = IntegratedBacktestingInterface()
    
    try:
        # 1. 백테스팅 시스템 설정
        backtest_config = BacktestConfig(
            mode=BacktestMode.SINGLE_STOCK,
            start_date="2023-01-01",
            end_date="2024-01-01",
            initial_capital=10000000
        )
        
        if not interface.setup_backtesting(backtest_config):
            logger.error("백테스팅 시스템 설정 실패")
            return False
        
        # 2. 자동매매 시스템 설정
        trade_config = TradeConfig(
            trading_mode=TradingMode.PAPER_TRADING,
            initial_capital=10000000
        )
        
        if not interface.setup_auto_trader(trade_config):
            logger.error("자동매매 시스템 설정 실패")
            return False
        
        # 3. 전략 최적화
        parameter_ranges = {
            'short_period': [3, 5, 7, 10],
            'long_period': [15, 20, 25, 30]
        }
        
        optimization_result = interface.optimize_strategy(
            StrategyType.MOVING_AVERAGE_CROSSOVER,
            parameter_ranges,
            "combined"
        )
        
        if optimization_result:
            logger.info(f"최적화 완료: {optimization_result.parameters}")
        
        # 4. 종합 분석
        analysis_result = interface.run_comprehensive_analysis()
        
        # 5. 성과 리포트 생성
        report = interface.generate_performance_report()
        print(report)
        
        # 6. 최적화된 전략 적용
        if optimization_result:
            if interface.apply_optimized_strategy(optimization_result):
                logger.info("최적화된 전략 적용 완료")
        
        logger.info("🎉 통합 백테스팅 인터페이스 완료")
        return True
        
    except Exception as e:
        logger.error(f"통합 백테스팅 인터페이스 오류: {e}")
        return False

if __name__ == "__main__":
    exit(0 if main() else 1) 