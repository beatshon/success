#!/usr/bin/env python3
"""
자동매매 시스템
거래 전략을 실제로 실행하는 자동매매 시스템
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
from loguru import logger
from trading_strategies import StrategyManager, create_sample_strategies
from demo_trading_system import MockTradingSystem

class AutoTradingSystem:
    """자동매매 시스템"""
    
    def __init__(self, use_real_api: bool = False):
        self.use_real_api = use_real_api
        self.strategy_manager = create_sample_strategies()
        self.trading_system = MockTradingSystem()
        self.is_running = False
        self.trade_history = []
        self.performance_metrics = {}
        
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
        base_price = 50000 + np.random.randint(0, 100000)  # 5만원 ~ 15만원
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
                logger.info(f"매매 신호 생성: {stock_code} - {consensus_signal['action']} - {consensus_signal['reason']}")
                return consensus_signal
                
            return None
            
        except Exception as e:
            logger.error(f"주식 분석 오류 ({stock_code}): {e}")
            return None
            
    def execute_trade(self, signal: Dict) -> bool:
        """매매 신호 실행"""
        try:
            stock_code = signal['stock_code']
            action = signal['action']
            current_price = signal['current_price']
            
            if action == 'BUY':
                # 매수 실행
                available_cash = self.trading_system.account_balance
                quantity = self._calculate_buy_quantity(stock_code, current_price, available_cash)
                
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
            
    def _calculate_buy_quantity(self, stock_code: str, price: float, available_cash: float) -> int:
        """매수 수량 계산"""
        # 가용 자금의 10% 사용
        target_amount = available_cash * 0.1
        quantity = int(target_amount / price)
        
        # 최소 1주 이상
        return max(1, quantity)
        
    def _record_trade(self, signal: Dict, action: str, quantity: int, price: float):
        """거래 기록"""
        trade_record = {
            'timestamp': datetime.now(),
            'stock_code': signal['stock_code'],
            'action': action,
            'quantity': quantity,
            'price': price,
            'total': quantity * price,
            'strategy': signal.get('strategy', 'Consensus'),
            'reason': signal.get('reason', '')
        }
        
        self.trade_history.append(trade_record)
        
    def run_trading_cycle(self):
        """거래 사이클 실행"""
        logger.info("거래 사이클 시작")
        
        # 모니터링 종목 분석
        for stock in config.WATCH_STOCKS:
            stock_code = stock['code']
            stock_name = stock['name']
            
            logger.info(f"분석 중: {stock_name}({stock_code})")
            
            # 매매 신호 분석
            signal = self.analyze_stock(stock_code)
            
            if signal:
                # 매매 실행
                success = self.execute_trade(signal)
                if success:
                    logger.info(f"거래 완료: {stock_name}")
                    
            # API 호출 제한 고려
            time.sleep(1)
            
        logger.info("거래 사이클 완료")
        
    def start_auto_trading(self, interval_minutes: int = 5):
        """자동매매 시작"""
        self.is_running = True
        logger.info(f"자동매매 시작 (간격: {interval_minutes}분)")
        
        try:
            while self.is_running:
                start_time = datetime.now()
                
                # 거래 사이클 실행
                self.run_trading_cycle()
                
                # 성능 지표 업데이트
                self._update_performance_metrics()
                
                # 성능 리포트 출력
                self._print_performance_report()
                
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
            
        self.performance_metrics = {
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'profit_rate': profit_rate,
            'win_rate': win_rate,
            'current_balance': self.trading_system.account_balance,
            'total_value': self.trading_system.get_account_info()['total_value']
        }
        
    def _print_performance_report(self):
        """성능 리포트 출력"""
        if not self.performance_metrics:
            return
            
        metrics = self.performance_metrics
        
        print("\n" + "=" * 60)
        print("📊 자동매매 성능 리포트")
        print("=" * 60)
        print(f"총 거래 횟수: {metrics['total_trades']}회")
        print(f"매수 거래: {metrics['buy_trades']}회")
        print(f"매도 거래: {metrics['sell_trades']}회")
        print(f"총 매수 금액: {metrics['total_buy_amount']:,}원")
        print(f"총 매도 금액: {metrics['total_sell_amount']:,}원")
        print(f"수익률: {metrics['profit_rate']:+.2f}%")
        print(f"승률: {metrics['win_rate']:.1f}%")
        print(f"현금 잔고: {metrics['current_balance']:,}원")
        print(f"총 자산: {metrics['total_value']:,}원")
        print("=" * 60)
        
    def get_trade_history(self) -> List[Dict]:
        """거래 내역 조회"""
        return self.trade_history
        
    def get_performance_metrics(self) -> Dict:
        """성능 지표 조회"""
        return self.performance_metrics

def main():
    """메인 함수"""
    print("🚀 자동매매 시스템 시작")
    print("=" * 60)
    
    # 자동매매 시스템 생성 (모의 거래 모드)
    trading_system = AutoTradingSystem(use_real_api=False)
    
    print("📋 설정된 전략:")
    for name, strategy in trading_system.strategy_manager.strategies.items():
        print(f"  - {name}: {strategy.description}")
        
    print("\n📊 초기 계좌 상태:")
    account_info = trading_system.trading_system.get_account_info()
    print(f"  - 현금 잔고: {account_info['cash_balance']:,}원")
    print(f"  - 총 자산: {account_info['total_value']:,}원")
    
    print("\n💡 자동매매를 시작하려면 다음 명령을 실행하세요:")
    print("   trading_system.start_auto_trading(interval_minutes=5)")
    
    print("\n" + "=" * 60)
    print("✅ 자동매매 시스템 준비 완료!")

if __name__ == "__main__":
    main() 