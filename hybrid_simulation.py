#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from loguru import logger

class HybridSimulation:
    def __init__(self, initial_capital=10000000):
        self.initial_capital = initial_capital
        self.data_dir = "data/simulation_results"
        self.hybrid_data_dir = "data/hybrid_analysis"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """데이터 디렉토리가 존재하는지 확인하고 생성합니다."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"시뮬레이션 데이터 디렉토리 생성: {self.data_dir}")
    
    def load_hybrid_analysis_data(self):
        """하이브리드 분석 데이터를 로드합니다."""
        try:
            if not os.path.exists(self.hybrid_data_dir):
                logger.warning("하이브리드 분석 데이터 디렉토리가 존재하지 않습니다.")
                return None
            
            csv_files = [f for f in os.listdir(self.hybrid_data_dir) if f.endswith('.csv')]
            if not csv_files:
                logger.warning("하이브리드 분석 CSV 파일을 찾을 수 없습니다.")
                return None
            
            # 가장 최신 파일 선택
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.hybrid_data_dir, x)))
            file_path = os.path.join(self.hybrid_data_dir, latest_file)
            
            # 다양한 인코딩으로 시도
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"하이브리드 분석 데이터 로드 완료: {latest_file}")
                    return data
                except Exception as e:
                    logger.debug(f"인코딩 {encoding} 실패: {e}")
                    continue
            
            logger.error("모든 인코딩으로 파일 읽기 실패")
            return None
            
        except Exception as e:
            logger.error(f"하이브리드 분석 데이터 로드 실패: {e}")
            return None
    
    def generate_hybrid_simulation_data(self, days=252):
        """하이브리드 분석 기반 시뮬레이션 데이터를 생성합니다."""
        try:
            # 하이브리드 분석 데이터 로드
            hybrid_data = self.load_hybrid_analysis_data()
            
            if hybrid_data is None:
                logger.warning("하이브리드 분석 데이터가 없어 기본 시뮬레이션을 실행합니다.")
                return self.generate_basic_simulation_data(days)
            
            # 날짜 범위 생성
            start_date = datetime.now() - timedelta(days=days)
            dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
            
            # 포트폴리오 가치 시뮬레이션
            np.random.seed(42)
            
            # 하이브리드 분석 기반 수익률 생성
            portfolio_values = [self.initial_capital]
            trades = []
            trade_values = []
            stock_names = []
            sectors = []
            signals = []
            
            # 매수 신호를 가진 종목들
            buy_signals = hybrid_data[hybrid_data['final_signal'] == '매수']
            sell_signals = hybrid_data[hybrid_data['final_signal'] == '매도']
            hold_signals = hybrid_data[hybrid_data['final_signal'] == '관망']
            
            for i in range(len(dates)):
                # 기본 수익률 (시장 수익률)
                base_return = np.random.normal(0.0003, 0.015)
                
                # 하이브리드 신호에 따른 추가 수익률
                signal_bonus = 0
                current_trade = 0
                current_trade_value = 0
                current_stock = ''
                current_sector = ''
                current_signal = '관망'
                
                # 매수 신호가 있는 종목들에 대한 거래 시뮬레이션
                if len(buy_signals) > 0 and np.random.random() < 0.05:  # 5% 확률로 매수
                    selected_stock = buy_signals.iloc[np.random.randint(0, len(buy_signals))]
                    signal_bonus = selected_stock['combined_score'] / 100 * 0.01  # 점수 기반 보너스
                    current_trade = np.random.randint(100, 500)
                    current_trade_value = current_trade * np.random.uniform(50000, 200000)
                    current_stock = selected_stock['stock_name']
                    current_sector = selected_stock['sector']
                    current_signal = '매수'
                
                # 매도 신호가 있는 종목들에 대한 거래 시뮬레이션
                elif len(sell_signals) > 0 and np.random.random() < 0.03:  # 3% 확률로 매도
                    selected_stock = sell_signals.iloc[np.random.randint(0, len(sell_signals))]
                    signal_bonus = -selected_stock['combined_score'] / 100 * 0.005  # 점수 기반 페널티
                    current_trade = -np.random.randint(100, 300)
                    current_trade_value = abs(current_trade) * np.random.uniform(50000, 200000)
                    current_stock = selected_stock['stock_name']
                    current_sector = selected_stock['sector']
                    current_signal = '매도'
                
                # 관망 신호에 대한 처리
                elif len(hold_signals) > 0 and np.random.random() < 0.02:  # 2% 확률로 관망 거래
                    selected_stock = hold_signals.iloc[np.random.randint(0, len(hold_signals))]
                    signal_bonus = 0
                    current_trade = 0
                    current_trade_value = 0
                    current_stock = selected_stock['stock_name']
                    current_sector = selected_stock['sector']
                    current_signal = '관망'
                
                # 포트폴리오 가치 업데이트
                total_return = base_return + signal_bonus
                new_value = portfolio_values[-1] * (1 + total_return)
                portfolio_values.append(new_value)
                
                trades.append(current_trade)
                trade_values.append(current_trade_value)
                stock_names.append(current_stock)
                sectors.append(current_sector)
                signals.append(current_signal)
            
            # 데이터프레임 생성
            simulation_data = pd.DataFrame({
                'date': dates,
                'portfolio_value': portfolio_values[1:],  # 첫 번째 값 제외 (초기값)
                'trades': trades,
                'trade_value': trade_values,
                'stock_name': stock_names,
                'sector': sectors,
                'signal': signals,
                'daily_return': [portfolio_values[i+1]/portfolio_values[i] - 1 for i in range(len(portfolio_values)-1)]
            })
            
            simulation_data.set_index('date', inplace=True)
            
            return simulation_data
            
        except Exception as e:
            logger.error(f"하이브리드 시뮬레이션 데이터 생성 실패: {e}")
            return self.generate_basic_simulation_data(days)
    
    def generate_basic_simulation_data(self, days=252):
        """기본 시뮬레이션 데이터를 생성합니다."""
        try:
            # 날짜 범위 생성
            start_date = datetime.now() - timedelta(days=days)
            dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
            
            # 포트폴리오 가치 시뮬레이션
            np.random.seed(42)
            
            # 일간 수익률 생성 (정규분포 기반)
            daily_returns = np.random.normal(0.0005, 0.02, len(dates))
            
            # 포트폴리오 가치 계산
            portfolio_values = [self.initial_capital]
            for i in range(1, len(dates)):
                new_value = portfolio_values[-1] * (1 + daily_returns[i])
                portfolio_values.append(new_value)
            
            # 거래 데이터 생성
            trades = []
            trade_values = []
            stock_names = []
            sectors = []
            signals = []
            
            # 랜덤하게 거래 발생
            for i in range(len(dates)):
                if np.random.random() < 0.1:  # 10% 확률로 거래 발생
                    trade_amount = np.random.choice([-100, 100, -200, 200, -500, 500])
                    trades.append(trade_amount)
                    trade_values.append(abs(trade_amount) * np.random.uniform(50000, 200000))
                    
                    # 샘플 종목명과 섹터
                    sample_stocks = ['삼성전자', 'SK하이닉스', 'NAVER', '카카오', 'LG에너지솔루션', 
                                   '현대차', '기아', 'POSCO홀딩스', '삼성바이오로직스', 'LG화학']
                    sample_sectors = ['전자', '반도체', 'IT', 'IT', '전기전자', 
                                    '자동차', '자동차', '철강', '바이오', '화학']
                    sample_signals = ['매수', '매도', '관망']
                    
                    idx = np.random.randint(0, len(sample_stocks))
                    stock_names.append(sample_stocks[idx])
                    sectors.append(sample_sectors[idx])
                    signals.append(np.random.choice(sample_signals))
                else:
                    trades.append(0)
                    trade_values.append(0)
                    stock_names.append('')
                    sectors.append('')
                    signals.append('')
            
            # 데이터프레임 생성
            simulation_data = pd.DataFrame({
                'date': dates,
                'portfolio_value': portfolio_values[1:],
                'trades': trades,
                'trade_value': trade_values,
                'stock_name': stock_names,
                'sector': sectors,
                'signal': signals,
                'daily_return': daily_returns
            })
            
            simulation_data.set_index('date', inplace=True)
            
            return simulation_data
            
        except Exception as e:
            logger.error(f"기본 시뮬레이션 데이터 생성 실패: {e}")
            return None
    
    def run_simulation(self, days=252):
        """하이브리드 시뮬레이션을 실행합니다."""
        try:
            logger.info(f"하이브리드 시뮬레이션 시작: {days}일, 초기 자본 {self.initial_capital:,}원")
            
            # 하이브리드 시뮬레이션 데이터 생성
            simulation_data = self.generate_hybrid_simulation_data(days)
            
            if simulation_data is None:
                logger.error("시뮬레이션 데이터 생성 실패")
                return None
            
            # 성능 지표 계산
            performance_metrics = self.calculate_performance_metrics(simulation_data)
            
            # 결과 출력
            self.print_simulation_results(simulation_data, performance_metrics)
            
            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hybrid_simulation_results_{timestamp}.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            simulation_data.to_csv(filepath, encoding='utf-8-sig')
            logger.info(f"하이브리드 시뮬레이션 결과 저장 완료: {filepath}")
            
            return simulation_data
            
        except Exception as e:
            logger.error(f"하이브리드 시뮬레이션 실행 실패: {e}")
            return None
    
    def calculate_performance_metrics(self, data):
        """성능 지표를 계산합니다."""
        try:
            # 기본 수익률
            total_return = ((data['portfolio_value'].iloc[-1] - data['portfolio_value'].iloc[0]) / 
                           data['portfolio_value'].iloc[0]) * 100
            
            # 연간 수익률
            annual_return = total_return * (252 / len(data))
            
            # 변동성
            returns = data['portfolio_value'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            
            # 샤프 비율 (무위험 수익률 2% 가정)
            risk_free_rate = 0.02
            sharpe_ratio = (annual_return/100 - risk_free_rate) / (volatility/100) if volatility > 0 else 0
            
            # 최대 낙폭
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            # 거래 통계
            trade_data = data[data['trades'] != 0]
            total_trades = len(trade_data)
            winning_trades = len(trade_data[trade_data['trades'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 신호별 통계
            signal_stats = data['signal'].value_counts()
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'signal_stats': signal_stats.to_dict()
            }
            
        except Exception as e:
            logger.error(f"성능 지표 계산 실패: {e}")
            return {}
    
    def print_simulation_results(self, data, metrics):
        """시뮬레이션 결과를 출력합니다."""
        print("=" * 60)
        print("🔗 하이브리드 시뮬레이션 결과 요약")
        print("=" * 60)
        
        print(f"\n💰 포트폴리오 성과:")
        print(f"• 초기 자본: {data['portfolio_value'].iloc[0]:,.0f}원")
        print(f"• 최종 자본: {data['portfolio_value'].iloc[-1]:,.0f}원")
        print(f"• 총 수익률: {metrics['total_return']:.2f}%")
        print(f"• 연간 수익률: {metrics['annual_return']:.2f}%")
        
        print(f"\n📈 위험 지표:")
        print(f"• 변동성: {metrics['volatility']:.2f}%")
        print(f"• 샤프 비율: {metrics['sharpe_ratio']:.2f}")
        print(f"• 최대 낙폭: {metrics['max_drawdown']:.2f}%")
        
        print(f"\n🔄 거래 통계:")
        print(f"• 총 거래 수: {metrics['total_trades']}회")
        print(f"• 수익 거래: {metrics['winning_trades']}회")
        print(f"• 승률: {metrics['win_rate']:.1f}%")
        
        if 'signal_stats' in metrics:
            print(f"\n📊 신호별 통계:")
            for signal, count in metrics['signal_stats'].items():
                if signal:  # 빈 문자열이 아닌 경우만
                    print(f"• {signal}: {count}회")
        
        print(f"\n📅 시뮬레이션 기간: {len(data)}일")
        print("=" * 60)

def main():
    """메인 함수"""
    # 하이브리드 시뮬레이션 실행
    simulation = HybridSimulation(initial_capital=10000000)  # 1천만원 초기 자본
    simulation.run_simulation(days=252)  # 1년 시뮬레이션

if __name__ == "__main__":
    main() 