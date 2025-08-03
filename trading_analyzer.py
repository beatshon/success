#!/usr/bin/env python3
"""
매매 분석 시스템
매매 내역 기록, 스코어링, 승패 요인 분석
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
from loguru import logger
# import matplotlib.pyplot as plt
# import seaborn as sns
from collections import defaultdict

class TradingAnalyzer:
    """매매 분석 시스템"""
    
    def __init__(self, data_dir: str = "trading_data"):
        self.data_dir = data_dir
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.analysis_file = os.path.join(data_dir, "analysis.json")
        self.reports_dir = os.path.join(data_dir, "reports")
        
        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 매매 내역 로드
        self.trades = self._load_trades()
        
        # 분석 결과
        self.daily_stats = {}
        self.performance_metrics = {}
        self.win_loss_analysis = {}
        
    def _load_trades(self) -> List[Dict]:
        """매매 내역 로드"""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                logger.info(f"매매 내역 로드 완료: {len(trades)}건")
                return trades
            except Exception as e:
                logger.error(f"매매 내역 로드 실패: {e}")
                return []
        return []
        
    def _save_trades(self):
        """매매 내역 저장"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, ensure_ascii=False, indent=2, default=str)
            logger.info("매매 내역 저장 완료")
        except Exception as e:
            logger.error(f"매매 내역 저장 실패: {e}")
            
    def add_trade(self, trade_data: Dict):
        """매매 내역 추가"""
        # 타임스탬프 추가
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now().isoformat()
            
        # 거래 ID 생성
        trade_data['trade_id'] = f"TRADE_{len(self.trades) + 1:06d}"
        
        # 추가 정보 계산
        trade_data = self._calculate_trade_metrics(trade_data)
        
        self.trades.append(trade_data)
        self._save_trades()
        
        logger.info(f"매매 내역 추가: {trade_data['trade_id']} - {trade_data['stock_name']}")
        
    def _calculate_trade_metrics(self, trade: Dict) -> Dict:
        """거래 지표 계산"""
        # 매수/매도 쌍 찾기
        if trade['action'] == 'SELL':
            # 해당 종목의 이전 매수 거래 찾기
            buy_trade = self._find_buy_trade(trade['stock_code'])
            if buy_trade:
                # 수익률 계산
                buy_price = buy_trade['price']
                sell_price = trade['price']
                profit_rate = ((sell_price - buy_price) / buy_price) * 100
                profit_amount = (sell_price - buy_price) * trade['quantity']
                
                trade['buy_price'] = buy_price
                trade['profit_rate'] = round(profit_rate, 2)
                trade['profit_amount'] = int(profit_amount)
                trade['is_profitable'] = profit_amount > 0
                trade['holding_days'] = self._calculate_holding_days(buy_trade, trade)
                
        return trade
        
    def _find_buy_trade(self, stock_code: str) -> Optional[Dict]:
        """해당 종목의 최근 매수 거래 찾기"""
        for trade in reversed(self.trades):
            if (trade['stock_code'] == stock_code and 
                trade['action'] == 'BUY' and 
                'sell_price' not in trade):
                return trade
        return None
        
    def _calculate_holding_days(self, buy_trade: Dict, sell_trade: Dict) -> int:
        """보유 기간 계산"""
        buy_date = datetime.fromisoformat(buy_trade['timestamp'])
        sell_date = datetime.fromisoformat(sell_trade['timestamp'])
        return (sell_date - buy_date).days
        
    def calculate_daily_stats(self, date: Optional[str] = None) -> Dict:
        """일일 통계 계산"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        daily_trades = [t for t in self.trades 
                       if t['timestamp'].startswith(date)]
        
        if not daily_trades:
            return {}
            
        # 기본 통계
        total_trades = len(daily_trades)
        buy_trades = [t for t in daily_trades if t['action'] == 'BUY']
        sell_trades = [t for t in daily_trades if t['action'] == 'SELL']
        
        # 수익성 분석
        total_profit = sum(t.get('profit_amount', 0) for t in sell_trades)
        total_buy_amount = sum(t['total'] for t in buy_trades)
        total_sell_amount = sum(t['total'] for t in sell_trades)
        
        if total_buy_amount > 0:
            daily_profit_rate = (total_profit / total_buy_amount) * 100
        else:
            daily_profit_rate = 0.0
            
        # 승률 계산
        profitable_trades = len([t for t in sell_trades if t.get('is_profitable', False)])
        win_rate = (profitable_trades / len(sell_trades)) * 100 if sell_trades else 0
        
        # 섹터별 성과
        sector_performance = defaultdict(lambda: {'trades': 0, 'profit': 0})
        for trade in sell_trades:
            sector = trade.get('sector', 'Unknown')
            sector_performance[sector]['trades'] += 1
            sector_performance[sector]['profit'] += trade.get('profit_amount', 0)
            
        # 전략별 성과
        strategy_performance = defaultdict(lambda: {'trades': 0, 'profit': 0})
        for trade in sell_trades:
            strategy = trade.get('strategy', 'Unknown')
            strategy_performance[strategy]['trades'] += 1
            strategy_performance[strategy]['profit'] += trade.get('profit_amount', 0)
            
        daily_stats = {
            'date': date,
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_profit': total_profit,
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'daily_profit_rate': round(daily_profit_rate, 2),
            'win_rate': round(win_rate, 1),
            'profitable_trades': profitable_trades,
            'sector_performance': dict(sector_performance),
            'strategy_performance': dict(strategy_performance),
            'avg_holding_days': np.mean([t.get('holding_days', 0) for t in sell_trades]) if sell_trades else 0
        }
        
        self.daily_stats[date] = daily_stats
        return daily_stats
        
    def analyze_win_loss_factors(self) -> Dict:
        """승패 요인 분석"""
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        if not sell_trades:
            return {}
            
        # 승패 분류
        winning_trades = [t for t in sell_trades if t.get('is_profitable', False)]
        losing_trades = [t for t in sell_trades if not t.get('is_profitable', False)]
        
        analysis = {
            'total_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(sell_trades)) * 100,
            'factors': {}
        }
        
        # 1. 섹터별 승률 분석
        sector_analysis = defaultdict(lambda: {'wins': 0, 'total': 0, 'profit': 0})
        for trade in sell_trades:
            sector = trade.get('sector', 'Unknown')
            sector_analysis[sector]['total'] += 1
            sector_analysis[sector]['profit'] += trade.get('profit_amount', 0)
            if trade.get('is_profitable', False):
                sector_analysis[sector]['wins'] += 1
                
        analysis['factors']['sector'] = {
            sector: {
                'win_rate': (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0,
                'avg_profit': data['profit'] / data['total'] if data['total'] > 0 else 0,
                'total_trades': data['total']
            }
            for sector, data in sector_analysis.items()
        }
        
        # 2. 전략별 승률 분석
        strategy_analysis = defaultdict(lambda: {'wins': 0, 'total': 0, 'profit': 0})
        for trade in sell_trades:
            strategy = trade.get('strategy', 'Unknown')
            strategy_analysis[strategy]['total'] += 1
            strategy_analysis[strategy]['profit'] += trade.get('profit_amount', 0)
            if trade.get('is_profitable', False):
                strategy_analysis[strategy]['wins'] += 1
                
        analysis['factors']['strategy'] = {
            strategy: {
                'win_rate': (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0,
                'avg_profit': data['profit'] / data['total'] if data['total'] > 0 else 0,
                'total_trades': data['total']
            }
            for strategy, data in strategy_analysis.items()
        }
        
        # 3. 보유 기간별 승률 분석
        holding_periods = {
            '단기(1-3일)': {'wins': 0, 'total': 0, 'profit': 0},
            '중기(4-7일)': {'wins': 0, 'total': 0, 'profit': 0},
            '장기(8일+)': {'wins': 0, 'total': 0, 'profit': 0}
        }
        
        for trade in sell_trades:
            holding_days = trade.get('holding_days', 0)
            if holding_days <= 3:
                period = '단기(1-3일)'
            elif holding_days <= 7:
                period = '중기(4-7일)'
            else:
                period = '장기(8일+)'
                
            holding_periods[period]['total'] += 1
            holding_periods[period]['profit'] += trade.get('profit_amount', 0)
            if trade.get('is_profitable', False):
                holding_periods[period]['wins'] += 1
                
        analysis['factors']['holding_period'] = {
            period: {
                'win_rate': (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0,
                'avg_profit': data['profit'] / data['total'] if data['total'] > 0 else 0,
                'total_trades': data['total']
            }
            for period, data in holding_periods.items()
        }
        
        # 4. 점수별 승률 분석
        score_ranges = {
            '높음(8점+)': {'wins': 0, 'total': 0, 'profit': 0},
            '중간(5-7점)': {'wins': 0, 'total': 0, 'profit': 0},
            '낮음(5점 미만)': {'wins': 0, 'total': 0, 'profit': 0}
        }
        
        for trade in sell_trades:
            score = trade.get('score', 5.0)
            if score >= 8.0:
                range_key = '높음(8점+)'
            elif score >= 5.0:
                range_key = '중간(5-7점)'
            else:
                range_key = '낮음(5점 미만)'
                
            score_ranges[range_key]['total'] += 1
            score_ranges[range_key]['profit'] += trade.get('profit_amount', 0)
            if trade.get('is_profitable', False):
                score_ranges[range_key]['wins'] += 1
                
        analysis['factors']['score'] = {
            range_key: {
                'win_rate': (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0,
                'avg_profit': data['profit'] / data['total'] if data['total'] > 0 else 0,
                'total_trades': data['total']
            }
            for range_key, data in score_ranges.items()
        }
        
        self.win_loss_analysis = analysis
        return analysis
        
    def calculate_performance_metrics(self) -> Dict:
        """종합 성능 지표 계산"""
        if not self.trades:
            return {}
            
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        if not sell_trades:
            return {}
            
        # 기본 지표
        total_trades = len(sell_trades)
        winning_trades = [t for t in sell_trades if t.get('is_profitable', False)]
        losing_trades = [t for t in sell_trades if not t.get('is_profitable', False)]
        
        total_profit = sum(t.get('profit_amount', 0) for t in sell_trades)
        total_loss = sum(t.get('profit_amount', 0) for t in losing_trades)
        total_gain = sum(t.get('profit_amount', 0) for t in winning_trades)
        
        # 수익률 지표
        avg_win = total_gain / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        profit_factor = abs(total_gain / total_loss) if total_loss != 0 else float('inf')
        
        # 승률 및 기타 지표
        win_rate = (len(winning_trades) / total_trades) * 100
        avg_holding_days = np.mean([t.get('holding_days', 0) for t in sell_trades])
        
        # 최대 낙폭 (MDD) 계산
        cumulative_profit = 0
        peak = 0
        mdd = 0
        
        for trade in sell_trades:
            cumulative_profit += trade.get('profit_amount', 0)
            if cumulative_profit > peak:
                peak = cumulative_profit
            drawdown = peak - cumulative_profit
            if drawdown > mdd:
                mdd = drawdown
                
        # 샤프 비율 계산 (간단한 버전)
        returns = [t.get('profit_rate', 0) for t in sell_trades]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return != 0 else 0
        else:
            sharpe_ratio = 0
            
        metrics = {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'total_profit': total_profit,
            'total_gain': total_gain,
            'total_loss': total_loss,
            'avg_win': round(avg_win, 0),
            'avg_loss': round(avg_loss, 0),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': mdd,
            'sharpe_ratio': round(sharpe_ratio, 2),
            'avg_holding_days': round(avg_holding_days, 1),
            'best_trade': max(sell_trades, key=lambda x: x.get('profit_amount', 0)),
            'worst_trade': min(sell_trades, key=lambda x: x.get('profit_amount', 0))
        }
        
        self.performance_metrics = metrics
        return metrics
        
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """일일 리포트 생성"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        daily_stats = self.calculate_daily_stats(date)
        
        if not daily_stats:
            return f"📅 {date}: 거래 내역이 없습니다."
            
        report = f"""
📊 일일 매매 리포트 - {date}
{'='*60}
📈 기본 통계:
  • 총 거래: {daily_stats['total_trades']}회 (매수: {daily_stats['buy_trades']}회, 매도: {daily_stats['sell_trades']}회)
  • 총 수익: {daily_stats['total_profit']:,}원
  • 수익률: {daily_stats['daily_profit_rate']:+.2f}%
  • 승률: {daily_stats['win_rate']:.1f}%
  • 평균 보유 기간: {daily_stats['avg_holding_days']:.1f}일

📊 섹터별 성과:"""
        
        for sector, perf in daily_stats['sector_performance'].items():
            avg_profit = perf['profit'] / perf['trades'] if perf['trades'] > 0 else 0
            report += f"\n  • {sector}: {perf['trades']}회 거래, 평균 수익: {avg_profit:+,}원"
            
        report += f"\n\n📈 전략별 성과:"
        for strategy, perf in daily_stats['strategy_performance'].items():
            avg_profit = perf['profit'] / perf['trades'] if perf['trades'] > 0 else 0
            report += f"\n  • {strategy}: {perf['trades']}회 거래, 평균 수익: {avg_profit:+,}원"
            
        return report
        
    def generate_analysis_report(self) -> str:
        """승패 요인 분석 리포트 생성"""
        analysis = self.analyze_win_loss_factors()
        metrics = self.calculate_performance_metrics()
        
        if not analysis:
            return "분석할 거래 내역이 없습니다."
            
        report = f"""
🔍 승패 요인 분석 리포트
{'='*60}
📊 전체 성과:
  • 총 거래: {analysis['total_trades']}회
  • 승리: {analysis['winning_trades']}회
  • 패배: {analysis['losing_trades']}회
  • 승률: {analysis['win_rate']:.1f}%
  • 총 수익: {metrics['total_profit']:,}원
  • 수익 팩터: {metrics['profit_factor']}
  • 샤프 비율: {metrics['sharpe_ratio']}
  • 최대 낙폭: {metrics['max_drawdown']:,}원

📈 섹터별 승률:"""
        
        for sector, data in analysis['factors']['sector'].items():
            report += f"\n  • {sector}: {data['win_rate']:.1f}% ({data['total_trades']}회)"
            
        report += f"\n\n🎯 전략별 승률:"
        for strategy, data in analysis['factors']['strategy'].items():
            report += f"\n  • {strategy}: {data['win_rate']:.1f}% ({data['total_trades']}회)"
            
        report += f"\n\n⏰ 보유 기간별 승률:"
        for period, data in analysis['factors']['holding_period'].items():
            report += f"\n  • {period}: {data['win_rate']:.1f}% ({data['total_trades']}회)"
            
        report += f"\n\n⭐ 점수별 승률:"
        for score_range, data in analysis['factors']['score'].items():
            report += f"\n  • {score_range}: {data['win_rate']:.1f}% ({data['total_trades']}회)"
            
        return report
        
    def save_reports(self):
        """리포트 저장"""
        # 일일 리포트
        today = datetime.now().strftime('%Y-%m-%d')
        daily_report = self.generate_daily_report(today)
        
        daily_file = os.path.join(self.reports_dir, f"daily_report_{today}.txt")
        with open(daily_file, 'w', encoding='utf-8') as f:
            f.write(daily_report)
            
        # 분석 리포트
        analysis_report = self.generate_analysis_report()
        analysis_file = os.path.join(self.reports_dir, f"analysis_report_{today}.txt")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(analysis_report)
            
        # JSON 데이터 저장
        analysis_data = {
            'daily_stats': self.daily_stats,
            'performance_metrics': self.performance_metrics,
            'win_loss_analysis': self.win_loss_analysis
        }
        
        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
            
        logger.info(f"리포트 저장 완료: {self.reports_dir}")
        
    def get_trade_summary(self) -> Dict:
        """거래 요약 정보"""
        if not self.trades:
            return {}
            
        return {
            'total_trades': len(self.trades),
            'buy_trades': len([t for t in self.trades if t['action'] == 'BUY']),
            'sell_trades': len([t for t in self.trades if t['action'] == 'SELL']),
            'total_profit': sum(t.get('profit_amount', 0) for t in self.trades if t['action'] == 'SELL'),
            'last_trade_date': max(t['timestamp'] for t in self.trades) if self.trades else None
        }

def main():
    """메인 함수"""
    print("📊 매매 분석 시스템 시작")
    print("=" * 60)
    
    # 분석 시스템 생성
    analyzer = TradingAnalyzer()
    
    # 샘플 데이터 생성 (테스트용)
    sample_trades = [
        {
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'sector': '전기전자',
            'action': 'BUY',
            'quantity': 10,
            'price': 70000,
            'total': 700000,
            'strategy': '이동평균 크로스오버',
            'reason': '단기 이동평균 상향 돌파',
            'score': 8.5,
            'selection_reason': '강한 상승 모멘텀'
        },
        {
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'sector': '전기전자',
            'action': 'SELL',
            'quantity': 10,
            'price': 75000,
            'total': 750000,
            'strategy': '이동평균 크로스오버',
            'reason': '단기 이동평균 하향 돌파',
            'score': 8.5,
            'selection_reason': '강한 상승 모멘텀'
        }
    ]
    
    # 샘플 거래 추가
    for trade in sample_trades:
        analyzer.add_trade(trade)
        
    # 일일 리포트 생성
    daily_report = analyzer.generate_daily_report()
    print(daily_report)
    
    # 분석 리포트 생성
    analysis_report = analyzer.generate_analysis_report()
    print(analysis_report)
    
    # 리포트 저장
    analyzer.save_reports()
    
    print("\n✅ 매매 분석 시스템 준비 완료!")

if __name__ == "__main__":
    main() 