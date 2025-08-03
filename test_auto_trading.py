#!/usr/bin/env python3
"""
자동매매 시스템 테스트
실제 자동매매를 테스트합니다.
"""
import time
from datetime import datetime
import config
from auto_trading_system import AutoTradingSystem

def test_single_cycle():
    """단일 거래 사이클 테스트"""
    print("🔄 단일 거래 사이클 테스트")
    print("=" * 50)
    
    # 자동매매 시스템 생성
    trading_system = AutoTradingSystem(use_real_api=False)
    
    # 단일 사이클 실행
    trading_system.run_trading_cycle()
    
    # 결과 확인
    print("\n📊 거래 결과:")
    trade_history = trading_system.get_trade_history()
    
    if trade_history:
        for trade in trade_history:
            print(f"  - {trade['timestamp'].strftime('%H:%M:%S')} - {trade['action']}: "
                  f"{trade['stock_code']} {trade['quantity']}주 @ {trade['price']:,}원")
    else:
        print("  - 거래 없음")
        
    # 계좌 상태 확인
    account_info = trading_system.trading_system.get_account_info()
    print(f"\n💰 계좌 상태:")
    print(f"  - 현금 잔고: {account_info['cash_balance']:,}원")
    print(f"  - 총 자산: {account_info['total_value']:,}원")
    print(f"  - 보유 종목 수: {account_info['positions']}개")

def test_multiple_cycles():
    """다중 거래 사이클 테스트"""
    print("🔄 다중 거래 사이클 테스트")
    print("=" * 50)
    
    # 자동매매 시스템 생성
    trading_system = AutoTradingSystem(use_real_api=False)
    
    # 3회 사이클 실행
    for cycle in range(3):
        print(f"\n📈 사이클 {cycle + 1}/3 실행 중...")
        trading_system.run_trading_cycle()
        
        # 성능 지표 업데이트
        trading_system._update_performance_metrics()
        
        # 중간 결과 출력
        metrics = trading_system.get_performance_metrics()
        if metrics:
            print(f"  - 총 거래: {metrics['total_trades']}회")
            print(f"  - 수익률: {metrics['profit_rate']:+.2f}%")
            print(f"  - 총 자산: {metrics['total_value']:,}원")
            
        time.sleep(2)  # 사이클 간 대기
        
    # 최종 성능 리포트
    trading_system._print_performance_report()

def test_strategy_signals():
    """전략 신호 테스트"""
    print("🔍 전략 신호 테스트")
    print("=" * 50)
    
    # 자동매매 시스템 생성
    trading_system = AutoTradingSystem(use_real_api=False)
    
    # 각 종목별 신호 분석
    for stock in config.WATCH_STOCKS:
        stock_code = stock['code']
        stock_name = stock['name']
        
        print(f"\n📊 {stock_name}({stock_code}) 분석:")
        
        # 개별 전략 신호 확인
        all_signals = trading_system.strategy_manager.get_all_signals(
            stock_code, 100000, trading_system.get_stock_data(stock_code, 30)
        )
        
        if all_signals:
            for signal in all_signals:
                print(f"  - {signal['strategy']}: {signal['action']} - {signal['reason']}")
        else:
            print("  - 신호 없음")
            
        # 합의 신호 확인
        consensus = trading_system.strategy_manager.get_consensus_signal(
            stock_code, 100000, trading_system.get_stock_data(stock_code, 30)
        )
        
        if consensus:
            print(f"  - 합의 신호: {consensus['action']} - {consensus['reason']}")
        else:
            print("  - 합의 신호 없음")

def main():
    """메인 테스트 함수"""
    print("🧪 자동매매 시스템 테스트 시작")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 단일 사이클 테스트
    test_single_cycle()
    
    print("\n" + "=" * 60)
    
    # 2. 다중 사이클 테스트
    test_multiple_cycles()
    
    print("\n" + "=" * 60)
    
    # 3. 전략 신호 테스트
    test_strategy_signals()
    
    print("\n" + "=" * 60)
    print("✅ 자동매매 시스템 테스트 완료!")
    
    print("\n💡 실제 자동매매를 시작하려면:")
    print("   trading_system = AutoTradingSystem(use_real_api=True)")
    print("   trading_system.start_auto_trading(interval_minutes=5)")

if __name__ == "__main__":
    main() 