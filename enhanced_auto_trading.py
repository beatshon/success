#!/usr/bin/env python3
"""
향상된 자동매매 시스템
종목 스캐너가 통합된 정교한 자동매매 시스템
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
from loguru import logger
from trading_strategies import create_sample_strategies
from stock_scanner import StockScanner
from demo_trading_system import MockTradingSystem
from trading_analyzer import TradingAnalyzer
from investment_manager import InvestmentManager

class EnhancedAutoTradingSystem:
    """향상된 자동매매 시스템"""
    
    def __init__(self, use_real_api: bool = False):
        self.use_real_api = use_real_api
        self.strategy_manager = create_sample_strategies()
        self.stock_scanner = StockScanner()
        self.trading_system = MockTradingSystem()
        self.trading_analyzer = TradingAnalyzer()  # 매매 분석 시스템 추가
        self.investment_manager = InvestmentManager()  # 투자 관리 시스템 추가
        self.is_running = False
        self.trade_history = []
        self.performance_metrics = {}
        self.current_watchlist = []
        
        # 키움 API 연결 (실제 API 사용 시)
        if use_real_api:
            try:
                from pykiwoom.kiwoom import Kiwoom
                self.kiwoom = Kiwoom()
                logger.info("키움 API 연결 성공")
            except Exception as e:
                logger.error(f"키움 API 연결 실패: {e}")
                self.use_real_api = False
        else:
            logger.info("모의 거래 시스템 사용")
            
        # 모든 전략 활성화
        for strategy_name in self.strategy_manager.strategies.keys():
            self.strategy_manager.activate_strategy(strategy_name)
            
    def update_watchlist(self):
        """감시 종목 리스트 업데이트"""
        logger.info("📊 감시 종목 리스트 업데이트 중...")
        
        # 종목 스캔 실행
        scan_results = self.stock_scanner.run_comprehensive_scan()
        recommended_stocks = self.stock_scanner.get_recommended_stocks(max_stocks=10)
        
        # 기존 감시 종목과 새로운 추천 종목 결합
        current_codes = {stock['code'] for stock in self.current_watchlist}
        
        # 새로운 추천 종목 추가
        for stock in recommended_stocks:
            if stock['code'] not in current_codes:
                self.current_watchlist.append(stock)
                logger.info(f"새로운 감시 종목 추가: {stock['name']}({stock['code']})")
                
        # 감시 종목 수 제한 (최대 15개)
        if len(self.current_watchlist) > 15:
            # 점수 기준으로 상위 종목만 유지
            self.current_watchlist.sort(key=lambda x: x['score'], reverse=True)
            self.current_watchlist = self.current_watchlist[:15]
            
        logger.info(f"감시 종목 리스트 업데이트 완료: {len(self.current_watchlist)}개 종목")
        
    def analyze_stock(self, stock_code: str) -> Optional[Dict]:
        """주식 분석 및 매매 신호 생성"""
        try:
            # 주식 데이터 조회
            data = self.get_stock_data(stock_code, days=30)
            if data.empty:
                logger.warning(f"데이터 없음: {stock_code}")
                return None
                
            current_price = data['close'].iloc[-1]
            
            # 전략들의 합의 신호 확인
            consensus_signal = self.strategy_manager.get_consensus_signal(
                stock_code, current_price, data
            )
            
            if consensus_signal:
                # 감시 종목 정보 추가
                watchlist_info = next((stock for stock in self.current_watchlist if stock['code'] == stock_code), None)
                if watchlist_info:
                    consensus_signal['stock_name'] = watchlist_info['name']
                    consensus_signal['sector'] = watchlist_info['sector']
                    consensus_signal['score'] = watchlist_info['score']
                    consensus_signal['selection_reason'] = watchlist_info['reason']
                    
                logger.info(f"매매 신호 생성: {stock_code} - {consensus_signal['action']} - {consensus_signal['reason']}")
                return consensus_signal
                
            return None
            
        except Exception as e:
            logger.error(f"주식 분석 오류 ({stock_code}): {e}")
            return None
            
    def get_stock_data(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """주식 데이터 조회"""
        if self.use_real_api:
            # 실제 키움 API를 통한 데이터 조회
            return self._get_real_stock_data(stock_code, days)
        else:
            # 모의 데이터 생성
            return self._generate_mock_data(stock_code, days)
            
    def _get_real_stock_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """실제 키움 API를 통한 주식 데이터 조회"""
        # TODO: 실제 키움 API 구현
        return self._generate_mock_data(stock_code, days)
        
    def _generate_mock_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """모의 주식 데이터 생성"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 랜덤 가격 데이터 생성
        base_price = 50000 + np.random.randint(0, 100000)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        prices = []
        current_price = base_price
        
        for _ in range(len(dates)):
            # 일일 변동률 (-5% ~ +5%)
            change_rate = np.random.uniform(-0.05, 0.05)
            current_price = int(current_price * (1 + change_rate))
            prices.append(current_price)
            
        data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        return data
        
    def execute_trade(self, signal: Dict) -> bool:
        """매매 신호 실행"""
        try:
            stock_code = signal['stock_code']
            action = signal['action']
            current_price = signal['current_price']
            
            if action == 'BUY':
                # 매수 실행
                available_cash = self.trading_system.account_balance
                quantity = self._calculate_buy_quantity(stock_code, current_price, available_cash, signal)
                
                if quantity > 0:
                    success, message = self.trading_system.buy_stock(stock_code, quantity, current_price)
                    if success:
                        logger.info(f"매수 성공: {stock_code} {quantity}주 @ {current_price:,}원")
                        self._record_trade(signal, 'BUY', quantity, current_price)
                        return True
                    else:
                        logger.warning(f"매수 실패: {message}")
                        
            elif action == 'SELL':
                # 매도 실행
                if stock_code in self.trading_system.positions:
                    position = self.trading_system.positions[stock_code]
                    quantity = position['quantity']
                    
                    success, message = self.trading_system.sell_stock(stock_code, quantity, current_price)
                    if success:
                        logger.info(f"매도 성공: {stock_code} {quantity}주 @ {current_price:,}원")
                        self._record_trade(signal, 'SELL', quantity, current_price)
                        return True
                    else:
                        logger.warning(f"매도 실패: {message}")
                        
            return False
            
        except Exception as e:
            logger.error(f"매매 실행 오류: {e}")
            return False
            
    def _calculate_buy_quantity(self, stock_code: str, price: float, available_cash: float, signal: Dict) -> int:
        """매수 수량 계산 (투자 관리 시스템 기반)"""
        # 투자 가능 여부 확인
        stock_info = {
            'name': signal.get('stock_name', ''),
            'sector': signal.get('sector', ''),
            'score': signal.get('score', 5.0),
            'strategy': signal.get('strategy', ''),
            'reason': signal.get('reason', '')
        }
        
        # 최적 투자 금액 계산
        optimal_amount = self.investment_manager.calculate_optimal_investment_amount(
            stock_code, stock_info, available_cash
        )
        
        # 투자 가능 여부 확인
        can_invest, reason = self.investment_manager.can_invest_in_stock(
            stock_code, optimal_amount, stock_info
        )
        
        if not can_invest:
            logger.warning(f"투자 제한: {stock_code} - {reason}")
            return 0
            
        # 수량 계산
        quantity = int(optimal_amount / price)
        
        # 최소 1주 이상
        return max(1, quantity)
        
    def _record_trade(self, signal: Dict, action: str, quantity: int, price: float):
        """거래 기록"""
        trade_record = {
            'timestamp': datetime.now(),
            'stock_code': signal['stock_code'],
            'stock_name': signal.get('stock_name', ''),
            'sector': signal.get('sector', ''),
            'action': action,
            'quantity': quantity,
            'price': price,
            'total': quantity * price,
            'strategy': signal.get('strategy', 'Consensus'),
            'reason': signal.get('reason', ''),
            'score': signal.get('score', 0),
            'selection_reason': signal.get('selection_reason', '')
        }
        
        self.trade_history.append(trade_record)
        
        # 매매 분석 시스템에 거래 기록 추가
        self.trading_analyzer.add_trade(trade_record)
        
        # 투자 관리 시스템에 투자 기록 추가 (매수인 경우)
        if action == 'BUY':
            stock_info = {
                'name': signal.get('stock_name', ''),
                'sector': signal.get('sector', ''),
                'score': signal.get('score', 0),
                'strategy': signal.get('strategy', ''),
                'reason': signal.get('reason', '')
            }
            self.investment_manager.record_investment(
                signal['stock_code'], 
                quantity * price, 
                stock_info
            )
        
    def run_trading_cycle(self):
        """거래 사이클 실행"""
        logger.info("🔄 향상된 거래 사이클 시작")
        
        # 1. 감시 종목 리스트 업데이트 (매 3회 사이클마다)
        if len(self.trade_history) % 3 == 0:
            self.update_watchlist()
            
        # 2. 감시 종목 분석
        for stock in self.current_watchlist:
            stock_code = stock['code']
            stock_name = stock['name']
            
            logger.info(f"분석 중: {stock_name}({stock_code}) - 점수: {stock['score']}")
            
            # 매매 신호 분석
            signal = self.analyze_stock(stock_code)
            
            if signal:
                # 매매 실행
                success = self.execute_trade(signal)
                if success:
                    logger.info(f"거래 완료: {stock_name}")
                    
            # API 호출 제한 고려
            time.sleep(1)
            
        logger.info("향상된 거래 사이클 완료")
        
    def start_auto_trading(self, interval_minutes: int = 5):
        """자동매매 시작"""
        self.is_running = True
        logger.info(f"🚀 향상된 자동매매 시작 (간격: {interval_minutes}분)")
        
        # 초기 감시 종목 리스트 설정
        self.update_watchlist()
        
        try:
            while self.is_running:
                start_time = datetime.now()
                
                # 거래 사이클 실행
                self.run_trading_cycle()
                
                # 성능 지표 업데이트
                self._update_performance_metrics()
                
                # 매매 분석 및 리포트 생성
                self._generate_trading_reports()
                
                # 향상된 성능 리포트 출력
                self._print_enhanced_performance_report()
                
                # 다음 사이클까지 대기
                elapsed_time = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, (interval_minutes * 60) - elapsed_time)
                
                if sleep_time > 0:
                    logger.info(f"다음 사이클까지 {sleep_time/60:.1f}분 대기")
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("자동매매 중단 요청")
            self.stop_auto_trading()
        except Exception as e:
            logger.error(f"자동매매 오류: {e}")
            self.stop_auto_trading()
            
    def stop_auto_trading(self):
        """자동매매 중단"""
        self.is_running = False
        logger.info("자동매매 중단")
        
        # 최종 리포트 생성
        self._generate_trading_reports()
        
    def _update_performance_metrics(self):
        """성능 지표 업데이트"""
        if not self.trade_history:
            return
            
        # 총 거래 횟수
        total_trades = len(self.trade_history)
        
        # 수익성 계산
        buy_trades = [t for t in self.trade_history if t['action'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['action'] == 'SELL']
        
        total_buy_amount = sum(t['total'] for t in buy_trades)
        total_sell_amount = sum(t['total'] for t in sell_trades)
        
        if total_buy_amount > 0:
            profit_rate = ((total_sell_amount - total_buy_amount) / total_buy_amount) * 100
        else:
            profit_rate = 0.0
            
        # 승률 계산
        if total_trades > 0:
            profitable_trades = len([t for t in sell_trades if t['total'] > 0])
            win_rate = (profitable_trades / len(sell_trades)) * 100 if sell_trades else 0
        else:
            win_rate = 0.0
            
        # 섹터별 성과 분석
        sector_performance = {}
        for trade in sell_trades:
            sector = trade.get('sector', 'Unknown')
            if sector not in sector_performance:
                sector_performance[sector] = {'trades': 0, 'profit': 0}
            sector_performance[sector]['trades'] += 1
            sector_performance[sector]['profit'] += trade.get('profit', 0)
            
        self.performance_metrics = {
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'profit_rate': profit_rate,
            'win_rate': win_rate,
            'current_balance': self.trading_system.account_balance,
            'total_value': self.trading_system.get_account_info()['total_value'],
            'watchlist_count': len(self.current_watchlist),
            'sector_performance': sector_performance
        }
        
    def _generate_trading_reports(self):
        """매매 리포트 생성"""
        try:
            # 일일 리포트 생성
            daily_report = self.trading_analyzer.generate_daily_report()
            logger.info("일일 매매 리포트 생성 완료")
            
            # 승패 요인 분석 리포트 생성
            analysis_report = self.trading_analyzer.generate_analysis_report()
            logger.info("승패 요인 분석 리포트 생성 완료")
            
            # 리포트 저장
            self.trading_analyzer.save_reports()
            
        except Exception as e:
            logger.error(f"리포트 생성 오류: {e}")
        
    def _print_enhanced_performance_report(self):
        """향상된 성능 리포트 출력"""
        if not self.performance_metrics:
            return
            
        metrics = self.performance_metrics
        
        print("\n" + "=" * 70)
        print("📊 향상된 자동매매 성능 리포트")
        print("=" * 70)
        print(f"총 거래 횟수: {metrics['total_trades']}회")
        print(f"매수 거래: {metrics['buy_trades']}회")
        print(f"매도 거래: {metrics['sell_trades']}회")
        print(f"총 매수 금액: {metrics['total_buy_amount']:,}원")
        print(f"총 매도 금액: {metrics['total_sell_amount']:,}원")
        print(f"수익률: {metrics['profit_rate']:+.2f}%")
        print(f"승률: {metrics['win_rate']:.1f}%")
        print(f"현금 잔고: {metrics['current_balance']:,}원")
        print(f"총 자산: {metrics['total_value']:,}원")
        print(f"감시 종목 수: {metrics['watchlist_count']}개")
        
        # 섹터별 성과
        if metrics['sector_performance']:
            print("\n📈 섹터별 성과:")
            for sector, perf in metrics['sector_performance'].items():
                avg_profit = perf['profit'] / perf['trades'] if perf['trades'] > 0 else 0
                print(f"  - {sector}: {perf['trades']}회 거래, 평균 수익: {avg_profit:+,}원")
                
        # 매매 분석 요약
        trade_summary = self.trading_analyzer.get_trade_summary()
        if trade_summary:
            print(f"\n📋 매매 분석 요약:")
            print(f"  - 총 거래: {trade_summary['total_trades']}회")
            print(f"  - 총 수익: {trade_summary['total_profit']:,}원")
            print(f"  - 마지막 거래: {trade_summary['last_trade_date']}")
            
        # 투자 관리 요약
        daily_investment_status = self.investment_manager.get_daily_investment_status()
        portfolio_summary = self.investment_manager.get_portfolio_summary()
        
        print(f"\n💰 투자 관리 요약:")
        print(f"  - 일일 투자: {daily_investment_status['total_invested']:,}원")
        print(f"  - 남은 한도: {daily_investment_status['remaining_limit']:,}원")
        print(f"  - 포트폴리오 총액: {portfolio_summary['total_investment']:,}원")
        print(f"  - 보유 종목: {portfolio_summary['stock_count']}개")
        print(f"  - 분산 점수: {portfolio_summary['diversification_score']}/100")
                
        print("=" * 70)
        
    def get_trade_history(self) -> List[Dict]:
        """거래 내역 조회"""
        return self.trade_history
        
    def get_performance_metrics(self) -> Dict:
        """성능 지표 조회"""
        return self.performance_metrics
        
    def get_current_watchlist(self) -> List[Dict]:
        """현재 감시 종목 리스트 조회"""
        return self.current_watchlist
        
    def get_trading_analysis(self) -> Dict:
        """매매 분석 결과 조회"""
        return {
            'daily_stats': self.trading_analyzer.daily_stats,
            'performance_metrics': self.trading_analyzer.performance_metrics,
            'win_loss_analysis': self.trading_analyzer.win_loss_analysis
        }

def main():
    """메인 함수"""
    print("🚀 향상된 자동매매 시스템 시작")
    print("=" * 70)
    
    # 향상된 자동매매 시스템 생성 (모의 거래 모드)
    trading_system = EnhancedAutoTradingSystem(use_real_api=False)
    
    print("📋 설정된 전략:")
    for name, strategy in trading_system.strategy_manager.strategies.items():
        print(f"  - {name}: {strategy.description}")
        
    print("\n🔍 종목 스캐너 기능:")
    print("  - 거래량 상위 종목 스캔")
    print("  - 모멘텀 상위 종목 스캔")
    print("  - 과매수/과매도 종목 스캔")
    print("  - 브레이크아웃 종목 스캔")
    print("  - 섹터별 리더 종목 스캔")
    print("  - 종합 점수 기반 종목 선정")
    
    print("\n📊 매매 분석 시스템:")
    print("  - 실시간 거래 기록")
    print("  - 일일 성과 분석")
    print("  - 승패 요인 분석")
    print("  - 섹터별/전략별 성과")
    print("  - 자동 리포트 생성")
    
    print("\n💰 투자 관리 시스템:")
    print("  - 일일 투자 한도 관리 (200만원)")
    print("  - 단일 종목 투자 한도 (50만원)")
    print("  - 섹터별 배분 제한 (40%)")
    print("  - 종목별 배분 제한 (15%)")
    print("  - 분산 투자 관리 (5-15개 종목)")
    print("  - 최적 투자 금액 계산")
    print("  - 포트폴리오 리밸런싱")
    
    print("\n📊 초기 계좌 상태:")
    account_info = trading_system.trading_system.get_account_info()
    print(f"  - 현금 잔고: {account_info['cash_balance']:,}원")
    print(f"  - 총 자산: {account_info['total_value']:,}원")
    
    print("\n💡 향상된 자동매매를 시작하려면 다음 명령을 실행하세요:")
    print("   trading_system.start_auto_trading(interval_minutes=5)")
    
    print("\n" + "=" * 70)
    print("✅ 향상된 자동매매 시스템 준비 완료!")

if __name__ == "__main__":
    main() 