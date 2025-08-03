#!/usr/bin/env python3
"""
간단한 투자 관리 시스템 테스트
"""
from investment_manager import InvestmentManager
import time

def simple_test():
    """간단한 테스트"""
    print("💰 간단한 투자 관리 시스템 테스트")
    print("=" * 50)
    
    start_time = time.time()
    
    # 1. 시스템 생성
    print("1. 시스템 생성 중...")
    manager = InvestmentManager()
    print(f"   ✅ 생성 완료 ({time.time() - start_time:.2f}초)")
    
    # 2. 일일 투자 현황
    print("2. 일일 투자 현황 확인...")
    daily_status = manager.get_daily_investment_status()
    print(f"   ✅ 일일 투자: {daily_status['total_invested']:,}원")
    print(f"   ✅ 남은 한도: {daily_status['remaining_limit']:,}원")
    
    # 3. 포트폴리오 요약
    print("3. 포트폴리오 요약...")
    portfolio = manager.get_portfolio_summary()
    print(f"   ✅ 총 투자: {portfolio['total_investment']:,}원")
    print(f"   ✅ 종목 수: {portfolio['stock_count']}개")
    
    # 4. 샘플 투자 기록
    print("4. 샘플 투자 기록...")
    sample_stock = {
        'name': '테스트종목',
        'sector': '테스트섹터',
        'score': 8.0,
        'strategy': '테스트전략',
        'reason': '테스트이유'
    }
    
    manager.record_investment('TEST001', 100000, sample_stock)
    print("   ✅ 투자 기록 완료")
    
    # 5. 최종 확인
    print("5. 최종 확인...")
    final_status = manager.get_daily_investment_status()
    final_portfolio = manager.get_portfolio_summary()
    
    print(f"   ✅ 일일 투자: {final_status['total_invested']:,}원")
    print(f"   ✅ 포트폴리오: {final_portfolio['total_investment']:,}원")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 총 소요 시간: {total_time:.2f}초")
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    simple_test() 