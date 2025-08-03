#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 백테스팅 시스템
과거 데이터를 기반으로 트레이딩 전략을 검증하고 성과를 분석합니다.
"""

import sys
import time
import json
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from concurrent.futures import ThreadPoolExecutor, as_completed

# 트레이딩 시스템 모듈들
from trading_strategy import (
    StrategyManager, create_default_strategies, TradingSignal, 
    SignalType, StrategyType, StrategyConfig
)
from technical_indicators import (
    calculate_sma, calculate_ema, calculate_rsi, 
    calculate_bollinger_bands, calculate_macd
)

# 실제 데이터 API 추가
from real_stock_data_api import StockDataAPI, DataManager, StockData

class BacktestMode(Enum):
    """백테스트 모드"""
    SINGLE_STOCK = "단일종목"
    PORTFOLIO = "포트폴리오"
    MONTE_CARLO = "몬테카를로"
    WALK_FORWARD = "워크포워드"

@dataclass
class BacktestConfig:
    """백테스트 설정"""
    # 기본 설정
    mode: BacktestMode = BacktestMode.SINGLE_STOCK
    start_date: str = "2023-01-01"
    end_date: str = "2023-12-28"  # 실제 데이터가 있는 기간으로 수정
    initial_capital: float = 10000000  # 1천만원
    
    # 거래 설정 - 더 관대한 설정으로 조정
    commission_rate: float = 0.0001   # 수수료 0.01% (감소)
    slippage_rate: float = 0.00005    # 슬리피지 0.005% (감소)
    min_trade_amount: float = 10000   # 최소 거래 금액 1만원 (감소)
    
    # 포지션 관리 - 더 관대한 설정
    max_positions: int = 10           # 최대 포지션 수 증가
    position_size_ratio: float = 0.1  # 전체 자금의 10% (감소)
    
    # 위험 관리
    stop_loss_rate: float = 0.05      # 5% 손절
    take_profit_rate: float = 0.10    # 10% 익절
    max_drawdown_limit: float = 0.20  # 20% 최대 낙폭
    
    # 성과 분석
    benchmark: str = "KOSPI"          # 벤치마크
    risk_free_rate: float = 0.03      # 무위험 수익률 3%

@dataclass
class Trade:
    """거래 기록"""
    timestamp: datetime
    code: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float
    slippage: float
    total_cost: float
    signal: TradingSignal = None

@dataclass
class Position:
    """포지션 정보"""
    code: str
    quantity: int
    avg_price: float
    entry_time: datetime
    stop_loss_price: float
    take_profit_price: float

@dataclass
class BacktestResult:
    """백테스트 결과"""
    # 기본 정보
    config: BacktestConfig
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # 거래 정보
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # 수익률 정보
    total_return: float
    annual_return: float
    total_profit: float
    total_loss: float
    net_profit: float
    
    # 위험 지표
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # 거래 기록
    trades: List[Trade]
    equity_curve: List[Dict]
    drawdown_curve: List[Dict]
    
    # 전략별 성과
    strategy_performance: Dict
    
    # Monte Carlo 통계 (선택적)
    monte_carlo_stats: Dict = None

class BacktestingEngine:
    """백테스팅 엔진"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy_manager = None
        self.data = {}
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.current_capital = config.initial_capital
        
        # 성과 추적
        self.peak_capital = config.initial_capital
        self.max_drawdown = 0.0
        self.max_drawdown_start = None
        self.max_drawdown_end = None
        
        logger.info("백테스팅 엔진 초기화 완료")
    
    def add_strategy(self, strategy_manager: StrategyManager):
        """전략 매니저 추가"""
        self.strategy_manager = strategy_manager
        logger.info(f"전략 매니저 추가 완료: {len(strategy_manager.strategies)}개 전략")
    
    def load_data(self, codes: List[str] = None, data_source: str = "yahoo") -> bool:
        """과거 데이터 로드"""
        try:
            logger.info("과거 데이터 로드 시작")
            
            # 기본 종목 리스트
            if codes is None:
                codes = ['005930', '000660', '035420', '035720', '051910', '006400']
            
            # 실제 데이터 API 사용
            if data_source in ["yahoo", "kiwoom"]:
                self._load_real_data(codes, data_source)
            else:
                # 샘플 데이터 생성 (fallback)
                self._generate_sample_data()
            
            logger.info(f"데이터 로드 완료: {len(self.data)}개 종목")
            return True
            
        except Exception as e:
            logger.error(f"데이터 로드 오류: {e}")
            return False
    
    def _load_real_data(self, codes: List[str], data_source: str):
        """실제 데이터 로드"""
        try:
            # 데이터 API 초기화
            api = StockDataAPI(data_source=data_source)
            manager = DataManager(api)
            
            # 백테스트용 데이터 준비
            stock_data = manager.get_backtest_data(
                codes, 
                self.config.start_date, 
                self.config.end_date,
                validate=True,
                clean=True
            )
            
            # 데이터 변환
            for code, stock_data_obj in stock_data.items():
                self.data[code] = stock_data_obj.data
                
            logger.info(f"실제 데이터 로드 완료: {len(self.data)}개 종목")
            
        except Exception as e:
            logger.error(f"실제 데이터 로드 오류: {e}")
            # 실패시 샘플 데이터로 fallback
            self._generate_sample_data()
    
    def _generate_sample_data(self):
        """샘플 데이터 생성 (fallback용)"""
        # 주요 종목들
        stocks = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스', 
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI'
        }
        
        start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(self.config.end_date, "%Y-%m-%d")
        
        for code, name in stocks.items():
            # 가격 데이터 생성 (랜덤 워크 + 트렌드)
            dates = pd.date_range(start_date, end_date, freq='D')
            prices = []
            
            # 초기 가격
            base_price = random.uniform(50000, 200000)
            current_price = base_price
            
            for i, date in enumerate(dates):
                # 주말 제외
                if date.weekday() >= 5:
                    continue
                
                # 랜덤 워크 + 트렌드
                trend = 0.0001 * i  # 약간의 상승 트렌드
                noise = random.gauss(0, 0.02)  # 2% 변동성
                
                change = trend + noise
                current_price *= (1 + change)
                
                # OHLC 데이터 생성
                high = current_price * random.uniform(1.0, 1.05)
                low = current_price * random.uniform(0.95, 1.0)
                open_price = current_price * random.uniform(0.98, 1.02)
                close_price = current_price
                volume = random.randint(1000000, 10000000)
                
                prices.append({
                    'date': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price,
                    'volume': volume
                })
            
            self.data[code] = pd.DataFrame(prices)
            self.data[code].set_index('date', inplace=True)
    
    def run_backtest(self) -> BacktestResult:
        """백테스트 실행"""
        try:
            logger.info("백테스트 시작")
            
            # 전략 매니저 초기화
            self.strategy_manager = create_default_strategies()
            
            # 초기화
            self.positions = {}
            self.trades = []
            self.equity_curve = []
            self.current_capital = self.config.initial_capital
            self.peak_capital = self.config.initial_capital
            
            # 날짜 범위
            start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(self.config.end_date, "%Y-%m-%d")
            
            # 백테스트 모드별 실행
            if self.config.mode == BacktestMode.SINGLE_STOCK:
                result = self._run_single_stock_backtest(start_date, end_date)
            elif self.config.mode == BacktestMode.PORTFOLIO:
                result = self._run_portfolio_backtest(start_date, end_date)
            elif self.config.mode == BacktestMode.MONTE_CARLO:
                result = self._run_monte_carlo_backtest(start_date, end_date)
            elif self.config.mode == BacktestMode.WALK_FORWARD:
                result = self._run_walk_forward_backtest(start_date, end_date)
            else:
                logger.error(f"지원하지 않는 백테스트 모드: {self.config.mode}")
                return None
            
            logger.info("백테스트 완료")
            return result
            
        except Exception as e:
            logger.error(f"백테스트 실행 오류: {e}")
            return None
    
    def _run_single_stock_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """단일 종목 백테스트"""
        logger.info("단일 종목 백테스트 시작")
        
        # 초기화
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.current_capital = self.config.initial_capital
        self.peak_capital = self.config.initial_capital
        
        logger.debug(f"백테스트 기간: {start_date} ~ {end_date}")
        logger.debug(f"초기 자본: {self.current_capital:,.0f}원")
        
        # 실제 데이터가 있는 날짜만 처리
        if self.data:
            first_code = list(self.data.keys())[0]
            df = self.data[first_code]
            
            # 시간대 정보 안전하게 처리
            try:
                if df.index.tz is not None:
                    df_index_naive = df.index.tz_localize(None)
                else:
                    df_index_naive = df.index
            except:
                df_index_naive = df.index
            
            start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
            end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
            
            # 데이터가 있는 날짜만 필터링
            available_dates = df_index_naive[(df_index_naive >= start_date_naive) & (df_index_naive <= end_date_naive)]
            available_dates = available_dates[available_dates.weekday < 5]  # 주중만
            
            logger.info(f"처리할 날짜 수: {len(available_dates)}개")
            
            # 일별 데이터 처리
            for date in available_dates:
                logger.debug(f"일별 데이터 처리: {date.strftime('%Y-%m-%d')}")
                self._process_daily_data(date)
        
        logger.info("단일 종목 백테스트 완료")
        return self._generate_results(start_date, end_date)
    
    def _run_portfolio_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """포트폴리오 백테스트"""
        logger.info("포트폴리오 백테스트 시작")
        
        # 포트폴리오 가중치 설정 (동일 가중치)
        portfolio_weights = {}
        total_stocks = len(self.data)
        weight_per_stock = 1.0 / total_stocks
        
        for code in self.data.keys():
            portfolio_weights[code] = weight_per_stock
        
        # 일별 백테스트 실행
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 주중만
                self._process_portfolio_daily_data(current_date, portfolio_weights)
            
            current_date += timedelta(days=1)
        
        # 결과 생성
        return self._generate_results(start_date, end_date)
    
    def _run_monte_carlo_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Monte Carlo 백테스트"""
        logger.info("Monte Carlo 백테스트 시작")
        
        # 기본 백테스트 실행
        base_result = self._run_single_stock_backtest(start_date, end_date)
        
        # Monte Carlo 시뮬레이션
        simulator = MonteCarloSimulator(base_result, num_simulations=1000)
        simulation_results = simulator.run_simulations()
        
        # 결과에 Monte Carlo 통계 추가
        if simulation_results:
            stats = simulator.get_statistics()
            base_result.monte_carlo_stats = stats
        
        return base_result
    
    def _run_walk_forward_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Walk Forward 백테스트"""
        logger.info("Walk Forward 백테스트 시작")
        
        # 기간을 여러 구간으로 나누어 백테스트
        total_days = (end_date - start_date).days
        window_size = total_days // 4  # 4개 구간으로 분할
        
        all_results = []
        
        for i in range(4):
            window_start = start_date + timedelta(days=i * window_size)
            window_end = start_date + timedelta(days=(i + 1) * window_size)
            
            if i == 3:  # 마지막 구간은 end_date까지
                window_end = end_date
            
            logger.info(f"구간 {i+1} 백테스트: {window_start.strftime('%Y-%m-%d')} ~ {window_end.strftime('%Y-%m-%d')}")
            
            # 구간별 백테스트 실행
            window_result = self._run_single_stock_backtest(window_start, window_end)
            if window_result:
                all_results.append(window_result)
        
        # 전체 결과 통합
        return self._combine_walk_forward_results(all_results, start_date, end_date)
    
    def _combine_walk_forward_results(self, results: List[BacktestResult], 
                                    start_date: datetime, end_date: datetime) -> BacktestResult:
        """Walk Forward 결과 통합"""
        if not results:
            return None
        
        # 첫 번째 결과를 기본으로 사용
        combined_result = results[0]
        
        # 거래 기록 통합
        all_trades = []
        all_equity_curve = []
        
        for result in results:
            all_trades.extend(result.trades)
            all_equity_curve.extend(result.equity_curve)
        
        # 시간순 정렬
        all_trades.sort(key=lambda x: x.timestamp)
        all_equity_curve.sort(key=lambda x: x['date'])
        
        # 통합된 결과 생성
        combined_result.trades = all_trades
        combined_result.equity_curve = all_equity_curve
        combined_result.start_date = start_date
        combined_result.end_date = end_date
        
        # 성과 지표 재계산
        combined_result = self._recalculate_performance(combined_result)
        
        return combined_result
    
    def _recalculate_performance(self, result: BacktestResult) -> BacktestResult:
        """성과 지표 재계산"""
        try:
            # 기본 정보
            final_capital = result.equity_curve[-1]['capital'] if result.equity_curve else result.initial_capital
            total_return = (final_capital - result.initial_capital) / result.initial_capital
            
            # 거래 통계 재계산
            total_trades = len(result.trades)
            winning_trades = 0
            total_profit = 0
            total_loss = 0
            
            for trade in result.trades:
                if trade.action == 'SELL':
                    # 수익/손실 계산
                    buy_trade = None
                    for t in result.trades:
                        if t.code == trade.code and t.action == 'BUY' and t.timestamp < trade.timestamp:
                            buy_trade = t
                            break
                    
                    if buy_trade:
                        profit = (trade.price - buy_trade.price) * trade.quantity
                        if profit > 0:
                            winning_trades += 1
                            total_profit += profit
                        else:
                            total_loss += abs(profit)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 수익률 계산
            days = (result.end_date - result.start_date).days
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # 위험 지표 재계산
            returns = self._calculate_returns_from_equity_curve(result.equity_curve)
            volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            calmar_ratio = annual_return / result.max_drawdown if result.max_drawdown > 0 else 0
            
            # 결과 업데이트
            result.final_capital = final_capital
            result.total_return = total_return
            result.annual_return = annual_return
            result.total_trades = total_trades
            result.winning_trades = winning_trades
            result.losing_trades = total_trades - winning_trades
            result.win_rate = win_rate
            result.total_profit = total_profit
            result.total_loss = total_loss
            result.net_profit = total_profit - total_loss
            result.volatility = volatility
            result.sharpe_ratio = sharpe_ratio
            result.sortino_ratio = sortino_ratio
            result.calmar_ratio = calmar_ratio
            
            return result
            
        except Exception as e:
            logger.error(f"성과 지표 재계산 오류: {e}")
            return result
    
    def _calculate_returns_from_equity_curve(self, equity_curve: List[Dict]) -> List[float]:
        """자본금 곡선에서 수익률 계산"""
        returns = []
        
        if len(equity_curve) < 2:
            return returns
        
        for i in range(1, len(equity_curve)):
            prev_capital = equity_curve[i-1]['capital']
            curr_capital = equity_curve[i]['capital']
            daily_return = (curr_capital - prev_capital) / prev_capital
            returns.append(daily_return)
        
        return returns
    
    def _process_daily_data(self, date: datetime):
        """일별 데이터 처리"""
        try:
            logger.debug(f"일별 데이터 처리 시작: {date.strftime('%Y-%m-%d')}")
            
            # 각 종목에 대해 처리
            for code, df in self.data.items():
                # 날짜 비교를 위해 시간대 정보 제거
                date_naive = date.replace(tzinfo=None) if date.tzinfo else date
                
                # 데이터 인덱스에서 시간대 정보 제거
                if df.index.tz is not None:
                    df_index_naive = df.index.tz_localize(None)
                else:
                    df_index_naive = df.index
                
                # 날짜가 데이터에 있는지 확인
                if date_naive not in df_index_naive:
                    logger.debug(f"날짜 {date.strftime('%Y-%m-%d')}가 {code} 데이터에 없음")
                    continue
                
                logger.debug(f"종목 {code} 처리 중...")
                
                # 현재가 조회 (시간대 정보 제거된 날짜 사용)
                current_price = df.loc[date_naive, 'close']
                logger.debug(f"현재가: {current_price:,.0f}원")
                
                # 전략 신호 생성
                signals = self._generate_signals(date)
                logger.debug(f"생성된 신호: {len(signals)}개")
                
                # 신호 처리
                for signal in signals:
                    self._process_signal(signal, date)
                
                # 포지션 업데이트
                self._update_positions(code, current_price, date)
            
            # 자본금 업데이트
            self._update_equity(date)
            
        except Exception as e:
            logger.error(f"일별 데이터 처리 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _generate_signals(self, date: datetime) -> List[TradingSignal]:
        """신호 생성"""
        signals = []
        
        try:
            # 각 종목에 대해 신호 생성
            for code, df in self.data.items():
                # 날짜 비교를 위해 시간대 정보 제거
                date_naive = date.replace(tzinfo=None) if date.tzinfo else date
                
                # 데이터 인덱스에서 시간대 정보 제거
                if df.index.tz is not None:
                    df_index_naive = df.index.tz_localize(None)
                else:
                    df_index_naive = df.index
                
                if date_naive not in df_index_naive:
                    continue
                
                current_price = df.loc[date_naive, 'close']
                logger.debug(f"신호 생성 시작: {code} @ {date.strftime('%Y-%m-%d')} - 현재가: {current_price:,.0f}원")
                
                # 현재 날짜까지의 데이터만 가져오기 (시간대 정보 제거된 날짜 사용)
                available_data = df.loc[:date_naive]
                logger.debug(f"사용 가능한 데이터: {len(available_data)}개")
                
                if len(available_data) < 10:  # 최소 10개 데이터 필요 (줄임)
                    logger.debug(f"데이터 부족: {len(available_data)}개 < 10개")
                    continue
                
                # 각 전략에 데이터 추가
                for name, strategy in self.strategy_manager.strategies.items():
                    # 기존 데이터 초기화
                    strategy.price_history = []
                    
                    # 가격 데이터 추가
                    for data_date, row in available_data.iterrows():
                        strategy.add_data(data_date, row)
                    
                    logger.debug(f"{name} 전략에 {len(strategy.price_history)}개 데이터 추가")
                
                # 신호 생성
                for name, strategy in self.strategy_manager.strategies.items():
                    signal = strategy.generate_signal()
                    if signal:
                        signal.code = code
                        signal.price = current_price
                        signal.timestamp = date
                        signal.strategy_name = name
                        signals.append(signal)
                        logger.info(f"{date.strftime('%Y-%m-%d')} {code} {name}: {signal.signal_type} 신호 생성")
                    else:
                        logger.debug(f"{date.strftime('%Y-%m-%d')} {code} {name}: 신호 없음")
        
        except Exception as e:
            logger.error(f"신호 생성 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.debug(f"총 생성된 신호: {len(signals)}개")
        return signals
    
    def _process_signal(self, signal: TradingSignal, date: datetime):
        """신호 처리"""
        try:
            code = signal.code
            price = signal.price
            
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                self._execute_buy(code, price, date, signal)
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                self._execute_sell(code, price, date, signal)
        
        except Exception as e:
            logger.error(f"신호 처리 오류: {e}")
    
    def _execute_buy(self, code: str, price: float, date: datetime, signal: TradingSignal):
        """매수 실행"""
        try:
            logger.debug(f"매수 실행 시작: {code} @ {price:,.0f}원")
            
            # 이미 보유 중인지 확인
            if code in self.positions:
                logger.debug(f"이미 보유 중인 종목: {code}")
                return
            
            # 최대 포지션 수 확인
            if len(self.positions) >= self.config.max_positions:
                logger.debug(f"최대 포지션 수 초과: {len(self.positions)}/{self.config.max_positions}")
                return
            
            # 주문 수량 계산
            available_capital = self.current_capital * self.config.position_size_ratio
            quantity = int(available_capital / price)
            
            logger.debug(f"사용 가능 자본: {available_capital:,.0f}원, 계산된 수량: {quantity}주")
            
            if quantity <= 0:
                logger.debug(f"주문 수량이 0: {available_capital:,.0f} / {price:,.0f} = {available_capital/price:.2f}")
                return
            
            # 수수료 및 슬리피지 계산
            commission = price * quantity * self.config.commission_rate
            slippage = price * quantity * self.config.slippage_rate
            total_cost = price * quantity + commission + slippage
            
            logger.debug(f"주문 금액: {price * quantity:,.0f}원, 수수료: {commission:,.0f}원, 슬리피지: {slippage:,.0f}원")
            logger.debug(f"총 비용: {total_cost:,.0f}원, 현재 자본: {self.current_capital:,.0f}원")
            
            # 자본금 확인
            if total_cost > self.current_capital:
                logger.debug(f"자본금 부족: 필요 {total_cost:,.0f}원, 보유 {self.current_capital:,.0f}원")
                return
            
            # 거래 실행
            self.current_capital -= total_cost
            
            # 포지션 생성
            self.positions[code] = Position(
                code=code,
                quantity=quantity,
                avg_price=price,
                entry_time=date,
                stop_loss_price=price * (1 - self.config.stop_loss_rate),
                take_profit_price=price * (1 + self.config.take_profit_rate)
            )
            
            # 거래 기록
            trade = Trade(
                timestamp=date,
                code=code,
                action='BUY',
                quantity=quantity,
                price=price,
                commission=commission,
                slippage=slippage,
                total_cost=total_cost,
                signal=signal
            )
            self.trades.append(trade)
            
            logger.info(f"매수 완료: {code} {quantity}주 @ {price:,.0f}원 (총 비용: {total_cost:,.0f}원)")
            
        except Exception as e:
            logger.error(f"매수 실행 오류: {e}")
    
    def _execute_sell(self, code: str, price: float, date: datetime, signal: TradingSignal):
        """매도 실행"""
        try:
            # 보유 중인지 확인
            if code not in self.positions:
                return
            
            position = self.positions[code]
            quantity = position.quantity
            
            # 수수료 및 슬리피지 계산
            commission = price * quantity * self.config.commission_rate
            slippage = price * quantity * self.config.slippage_rate
            total_revenue = price * quantity - commission - slippage
            
            # 거래 실행
            self.current_capital += total_revenue
            
            # 포지션 제거
            del self.positions[code]
            
            # 거래 기록
            trade = Trade(
                timestamp=date,
                code=code,
                action='SELL',
                quantity=quantity,
                price=price,
                commission=commission,
                slippage=slippage,
                total_cost=total_revenue,
                signal=signal
            )
            self.trades.append(trade)
            
        except Exception as e:
            logger.error(f"매도 실행 오류: {e}")
    
    def _update_positions(self, code: str, price: float, date: datetime):
        """포지션 업데이트 (손절/익절)"""
        try:
            if code not in self.positions:
                return
            
            position = self.positions[code]
            
            # 손절 체크
            if price <= position.stop_loss_price:
                logger.info(f"손절 실행: {code} @ {price:,}원")
                self._execute_sell(code, price, date, None)
            
            # 익절 체크
            elif price >= position.take_profit_price:
                logger.info(f"익절 실행: {code} @ {price:,}원")
                self._execute_sell(code, price, date, None)
        
        except Exception as e:
            logger.error(f"포지션 업데이트 오류: {e}")
    
    def _process_portfolio_daily_data(self, date: datetime, portfolio_weights: Dict[str, float]):
        """포트폴리오 일별 데이터 처리"""
        try:
            # 각 종목에 대해 처리
            for code, df in self.data.items():
                if date not in df.index:
                    continue
                
                # 현재가 조회
                current_price = df.loc[date, 'close']
                
                # 전략 신호 생성
                signals = self._generate_signals(date)
                
                # 신호 처리
                for signal in signals:
                    self._process_signal(signal, date)
                
                # 포지션 업데이트
                self._update_positions(code, current_price, date)
            
            # 자본금 업데이트
            self._update_equity(date)
            
        except Exception as e:
            logger.error(f"포트폴리오 일별 데이터 처리 오류: {e}")
    
    def _rebalance_portfolio(self, date: datetime, portfolio_weights: Dict[str, float]):
        """포트폴리오 리밸런싱"""
        try:
            logger.info(f"포트폴리오 리밸런싱: {date.strftime('%Y-%m-%d')}")
            
            # 현재 포지션 가치 계산
            current_weights = {}
            total_value = self.current_capital
            
            for code, position in self.positions.items():
                if code in self.data and date in self.data[code].index:
                    current_price = self.data[code].loc[date, 'close']
                    position_value = current_price * position.quantity
                    total_value += position_value
            
            # 목표 가중치에 맞게 조정
            for code, target_weight in portfolio_weights.items():
                if code in self.data and date in self.data[code].index:
                    current_price = self.data[code].loc[date, 'close']
                    target_value = total_value * target_weight
                    
                    if code in self.positions:
                        current_value = current_price * self.positions[code].quantity
                        value_diff = target_value - current_value
                        
                        if abs(value_diff) > self.config.min_trade_amount:
                            if value_diff > 0:  # 매수 필요
                                quantity = int(value_diff / current_price)
                                if quantity > 0:
                                    self._execute_buy(code, current_price, date, None)
                            else:  # 매도 필요
                                quantity = int(abs(value_diff) / current_price)
                                if quantity > 0:
                                    self._execute_sell(code, current_price, date, None)
                    else:
                        # 새로운 종목 매수
                        if target_value > self.config.min_trade_amount:
                            quantity = int(target_value / current_price)
                            if quantity > 0:
                                self._execute_buy(code, current_price, date, None)
        
        except Exception as e:
            logger.error(f"포트폴리오 리밸런싱 오류: {e}")
    
    def _update_equity(self, date: datetime):
        """자본금 업데이트"""
        try:
            # 현재 포지션 가치 계산
            position_value = 0
            for code, position in self.positions.items():
                if code in self.data and date in self.data[code].index:
                    current_price = self.data[code].loc[date, 'close']
                    position_value += current_price * position.quantity
            
            # 총 자본금
            total_capital = self.current_capital + position_value
            
            # 최고점 업데이트
            if total_capital > self.peak_capital:
                self.peak_capital = total_capital
            
            # 낙폭 계산
            drawdown = (self.peak_capital - total_capital) / self.peak_capital
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
            
            # 자본금 곡선 기록
            self.equity_curve.append({
                'date': date,
                'capital': total_capital,
                'drawdown': drawdown,
                'positions_count': len(self.positions)
            })
        
        except Exception as e:
            logger.error(f"자본금 업데이트 오류: {e}")
    
    def _generate_results(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """백테스트 결과 생성"""
        try:
            # 기본 정보
            if self.equity_curve and len(self.equity_curve) > 0:
                final_capital = self.equity_curve[-1]['capital']
            else:
                final_capital = self.config.initial_capital
                
            total_return = (final_capital - self.config.initial_capital) / self.config.initial_capital
            
            # 거래 통계
            total_trades = len(self.trades)
            winning_trades = 0
            total_profit = 0
            total_loss = 0
            
            for trade in self.trades:
                if trade.action == 'SELL':
                    # 수익/손실 계산
                    buy_trade = None
                    for t in self.trades:
                        if t.code == trade.code and t.action == 'BUY' and t.timestamp < trade.timestamp:
                            buy_trade = t
                            break
                    
                    if buy_trade:
                        profit = (trade.price - buy_trade.price) * trade.quantity
                        if profit > 0:
                            winning_trades += 1
                            total_profit += profit
                        else:
                            total_loss += abs(profit)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 수익률 계산
            days = (end_date - start_date).days
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # 위험 지표 계산
            returns = self._calculate_returns()
            volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            calmar_ratio = annual_return / self.max_drawdown if self.max_drawdown > 0 else 0
            
            # 전략별 성과
            strategy_performance = {}
            if self.strategy_manager:
                strategy_performance = self.strategy_manager.get_performance_summary()
            
            return BacktestResult(
                config=self.config,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config.initial_capital,
                final_capital=final_capital,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=total_trades - winning_trades,
                win_rate=win_rate,
                total_return=total_return,
                annual_return=annual_return,
                total_profit=total_profit,
                total_loss=total_loss,
                net_profit=total_profit - total_loss,
                max_drawdown=self.max_drawdown,
                max_drawdown_duration=0,  # TODO: 계산 필요
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                trades=self.trades,
                equity_curve=self.equity_curve,
                drawdown_curve=[],  # TODO: 계산 필요
                strategy_performance=strategy_performance
            )
        
        except Exception as e:
            logger.error(f"결과 생성 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_returns(self) -> List[float]:
        """수익률 계산"""
        returns = []
        
        if len(self.equity_curve) < 2:
            return returns
        
        for i in range(1, len(self.equity_curve)):
            prev_capital = self.equity_curve[i-1]['capital']
            curr_capital = self.equity_curve[i]['capital']
            daily_return = (curr_capital - prev_capital) / prev_capital
            returns.append(daily_return)
        
        return returns
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """샤프 비율 계산"""
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 연율화
        sharpe = (avg_return - self.config.risk_free_rate / 252) / std_return * np.sqrt(252)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """소르티노 비율 계산"""
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf')
        
        downside_std = np.std(negative_returns)
        
        if downside_std == 0:
            return 0.0
        
        # 연율화
        sortino = (avg_return - self.config.risk_free_rate / 252) / downside_std * np.sqrt(252)
        return sortino

class MonteCarloSimulator:
    """Monte Carlo 시뮬레이터"""
    
    def __init__(self, backtest_result: BacktestResult, num_simulations: int = 1000):
        self.backtest_result = backtest_result
        self.num_simulations = num_simulations
        self.simulation_results = []
    
    def run_simulations(self) -> List[Dict]:
        """Monte Carlo 시뮬레이션 실행"""
        logger.info(f"Monte Carlo 시뮬레이션 시작 ({self.num_simulations}회)")
        
        try:
            # 원본 거래 데이터에서 수익률 추출
            returns = self._extract_returns()
            
            if not returns:
                logger.error("수익률 데이터가 없습니다.")
                return []
            
            # 병렬 처리로 시뮬레이션 실행
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for i in range(self.num_simulations):
                    future = executor.submit(self._run_single_simulation, returns, i)
                    futures.append(future)
                
                # 결과 수집
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        self.simulation_results.append(result)
            
            logger.info(f"Monte Carlo 시뮬레이션 완료: {len(self.simulation_results)}회")
            return self.simulation_results
            
        except Exception as e:
            logger.error(f"Monte Carlo 시뮬레이션 오류: {e}")
            return []
    
    def _extract_returns(self) -> List[float]:
        """거래 데이터에서 수익률 추출"""
        returns = []
        
        for trade in self.backtest_result.trades:
            if trade.action == 'SELL':
                # 해당 매수 거래 찾기
                buy_trade = None
                for t in self.backtest_result.trades:
                    if (t.code == trade.code and t.action == 'BUY' and 
                        t.timestamp < trade.timestamp):
                        buy_trade = t
                        break
                
                if buy_trade:
                    return_rate = (trade.price - buy_trade.price) / buy_trade.price
                    returns.append(return_rate)
        
        return returns
    
    def _run_single_simulation(self, returns: List[float], sim_id: int) -> Dict:
        """단일 시뮬레이션 실행"""
        try:
            # 랜덤하게 거래 순서 재배열
            shuffled_returns = returns.copy()
            random.shuffle(shuffled_returns)
            
            # 시뮬레이션 실행
            initial_capital = self.backtest_result.initial_capital
            current_capital = initial_capital
            max_capital = initial_capital
            max_drawdown = 0.0
            
            for return_rate in shuffled_returns:
                current_capital *= (1 + return_rate)
                
                if current_capital > max_capital:
                    max_capital = current_capital
                
                drawdown = (max_capital - current_capital) / max_capital
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            total_return = (current_capital - initial_capital) / initial_capital
            
            return {
                'simulation_id': sim_id,
                'final_capital': current_capital,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': total_return / max_drawdown if max_drawdown > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"시뮬레이션 {sim_id} 오류: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """시뮬레이션 통계"""
        if not self.simulation_results:
            return {}
        
        returns = [r['total_return'] for r in self.simulation_results]
        drawdowns = [r['max_drawdown'] for r in self.simulation_results]
        sharpe_ratios = [r['sharpe_ratio'] for r in self.simulation_results]
        
        return {
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            'mean_drawdown': np.mean(drawdowns),
            'max_drawdown': np.max(drawdowns),
            'mean_sharpe': np.mean(sharpe_ratios),
            'win_rate': len([r for r in returns if r > 0]) / len(returns) * 100,
            'var_95': np.percentile(returns, 5),  # 95% VaR
            'cvar_95': np.mean([r for r in returns if r <= np.percentile(returns, 5)])  # 95% CVaR
        }

class BacktestAnalyzer:
    """백테스트 결과 분석기"""
    
    def __init__(self, result: BacktestResult):
        self.result = result
    
    def generate_report(self) -> str:
        """상세 리포트 생성"""
        report = f"""
=== 백테스트 결과 리포트 ===
백테스트 모드: {self.result.config.mode.value}
기간: {self.result.start_date.strftime('%Y-%m-%d')} ~ {self.result.end_date.strftime('%Y-%m-%d')}
초기 자본: {self.result.initial_capital:,.0f}원
최종 자본: {self.result.final_capital:,.0f}원

=== 수익률 분석 ===
총 수익률: {self.result.total_return:.2%}
연간 수익률: {self.result.annual_return:.2%}
총 수익: {self.result.total_profit:,.0f}원
총 손실: {self.result.total_loss:,.0f}원
순 수익: {self.result.net_profit:,.0f}원

=== 거래 통계 ===
총 거래 수: {self.result.total_trades}회
승리 거래: {self.result.winning_trades}회
패배 거래: {self.result.losing_trades}회
승률: {self.result.win_rate:.1f}%

=== 위험 지표 ===
최대 낙폭: {self.result.max_drawdown:.2%}
변동성: {self.result.volatility:.2%}
샤프 비율: {self.result.sharpe_ratio:.2f}
소르티노 비율: {self.result.sortino_ratio:.2f}
칼마 비율: {self.result.calmar_ratio:.2f}

=== 전략별 성과 ===
"""
        
        for strategy, performance in self.result.strategy_performance.items():
            report += f"{strategy}: {performance}\n"
        
        # Monte Carlo 통계 추가
        if self.result.monte_carlo_stats:
            report += f"""
=== Monte Carlo 시뮬레이션 결과 ===
평균 수익률: {self.result.monte_carlo_stats.get('mean_return', 0):.2%}
수익률 표준편차: {self.result.monte_carlo_stats.get('std_return', 0):.2%}
최소 수익률: {self.result.monte_carlo_stats.get('min_return', 0):.2%}
최대 수익률: {self.result.monte_carlo_stats.get('max_return', 0):.2%}
95% VaR: {self.result.monte_carlo_stats.get('var_95', 0):.2%}
95% CVaR: {self.result.monte_carlo_stats.get('cvar_95', 0):.2%}
승률: {self.result.monte_carlo_stats.get('win_rate', 0):.1f}%
"""
        
        return report
    
    def plot_results(self, save_path: str = None):
        """결과 시각화"""
        try:
            # 자본금 곡선
            dates = [e['date'] for e in self.result.equity_curve]
            capitals = [e['capital'] for e in self.result.equity_curve]
            drawdowns = [e['drawdown'] for e in self.result.equity_curve]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 자본금 곡선
            ax1.plot(dates, capitals, label='Portfolio Value', linewidth=2)
            ax1.axhline(y=self.result.initial_capital, color='r', linestyle='--', label='Initial Capital')
            ax1.set_title('Portfolio Value Over Time')
            ax1.set_ylabel('Capital (KRW)')
            ax1.legend()
            ax1.grid(True)
            
            # 낙폭 곡선
            ax2.fill_between(dates, drawdowns, 0, alpha=0.3, color='red', label='Drawdown')
            ax2.plot(dates, drawdowns, color='red', linewidth=1)
            ax2.set_title('Drawdown Over Time')
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_xlabel('Date')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"차트 저장: {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"차트 생성 오류: {e}")

def main():
    """메인 함수"""
    logger.info("백테스팅 시스템 시작")
    
    # 다양한 백테스트 설정
    test_configs = [
        {
            "name": "단일 종목 백테스트",
            "config": BacktestConfig(
                mode=BacktestMode.SINGLE_STOCK,
                start_date="2023-01-01",
                end_date="2024-01-01",
                initial_capital=10000000
            )
        },
        {
            "name": "포트폴리오 백테스트",
            "config": BacktestConfig(
                mode=BacktestMode.PORTFOLIO,
                start_date="2023-01-01",
                end_date="2024-01-01",
                initial_capital=10000000
            )
        },
        {
            "name": "Monte Carlo 백테스트",
            "config": BacktestConfig(
                mode=BacktestMode.MONTE_CARLO,
                start_date="2023-01-01",
                end_date="2024-01-01",
                initial_capital=10000000
            )
        },
        {
            "name": "Walk Forward 백테스트",
            "config": BacktestConfig(
                mode=BacktestMode.WALK_FORWARD,
                start_date="2023-01-01",
                end_date="2024-01-01",
                initial_capital=10000000
            )
        }
    ]
    
    results = {}
    
    for test_config in test_configs:
        try:
            logger.info(f"\n=== {test_config['name']} 시작 ===")
            
            # 백테스팅 엔진 생성
            engine = BacktestingEngine(test_config['config'])
            
            # 데이터 로드 (실제 데이터 사용)
            codes = ['005930', '000660', '035420', '035720', '051910', '006400']
            if not engine.load_data(codes=codes, data_source="yahoo"):
                logger.warning(f"{test_config['name']}: 데이터 로드 실패, 샘플 데이터 사용")
                engine.load_data(data_source="sample")
            
            # 백테스트 실행
            result = engine.run_backtest()
            if not result:
                logger.error(f"{test_config['name']}: 백테스트 실행 실패")
                continue
            
            # 결과 저장
            results[test_config['name']] = result
            
            # 결과 분석
            analyzer = BacktestAnalyzer(result)
            report = analyzer.generate_report()
            print(f"\n{test_config['name']} 결과:")
            print(report)
            
            # 차트 생성
            chart_filename = f"backtest_{test_config['config'].mode.value.lower()}_results.png"
            analyzer.plot_results(chart_filename)
            
            logger.info(f"{test_config['name']} 완료")
            
        except Exception as e:
            logger.error(f"{test_config['name']} 오류: {e}")
    
    # 종합 결과 요약
    if results:
        print("\n=== 종합 결과 요약 ===")
        for name, result in results.items():
            print(f"{name}:")
            print(f"  총 수익률: {result.total_return:.2%}")
            print(f"  샤프 비율: {result.sharpe_ratio:.2f}")
            print(f"  최대 낙폭: {result.max_drawdown:.2%}")
            print(f"  승률: {result.win_rate:.1f}%")
            print()
    
    logger.info("백테스팅 시스템 완료")
    return True

if __name__ == "__main__":
    main() 