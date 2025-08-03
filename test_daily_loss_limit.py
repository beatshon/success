#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cross_platform_trader import KiwoomAPI, RealtimeTrader
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def test_daily_loss_limit():
    """하루 손실 상한선 기능 테스트"""
    print("=" * 60)
    print("📉 하루 손실 상한선 기능 테스트")
    print("=" * 60)
    
    try:
        # API 초기화
        api = KiwoomAPI()
        api.login()
        
        # 계좌 정보 조회
        account_info = api.get_account_info()
        account = account_info["계좌번호"]
        
        print("✅ 시스템 초기화 완료")
        print(f"계좌: {account}")
        print(f"계좌 정보: {account_info}")
        
        # 1. 정상 상황 테스트 (손실 한도 -3%)
        print("\n1️⃣ 정상 상황 테스트 (손실 한도 -3%)")
        trader1 = RealtimeTrader(api, account, daily_loss_limit=-3.0)
        trader1.initialize()
        
        # 매수 실행
        result1 = trader1.execute_buy("005930.KS")
        if result1:
            print("✅ 매수 성공")
            print(f"보유 종목: {len(trader1.positions)}개")
            print(f"예수금: {trader1.account_info['예수금']:,}원")
            
            # 손실 상한선 체크
            if trader1.check_daily_loss_limit():
                print("❌ 손실 상한선 초과 (예상과 다름)")
            else:
                print("✅ 손실 상한선 내에서 정상 운영")
        else:
            print("❌ 매수 실패")
        
        # 2. 극단적 손실 상황 테스트 (손실 한도 -1%)
        print("\n2️⃣ 극단적 손실 상황 테스트 (손실 한도 -1%)")
        trader2 = RealtimeTrader(api, account, daily_loss_limit=-1.0)
        trader2.initialize()
        
        # 여러 번 매수하여 손실 발생 시뮬레이션
        for i in range(3):
            result = trader2.execute_buy(f"000660.KS")
            if result:
                print(f"✅ 매수 {i+1}회 성공")
            else:
                print(f"❌ 매수 {i+1}회 실패")
        
        print(f"보유 종목: {len(trader2.positions)}개")
        print(f"예수금: {trader2.account_info['예수금']:,}원")
        
        # 손실 상한선 체크
        if trader2.check_daily_loss_limit():
            print("✅ 손실 상한선 초과로 비상정지 실행됨")
        else:
            print("ℹ️ 손실 상한선 내에서 정상 운영 중")
        
        # 3. 자정 리셋 테스트
        print("\n3️⃣ 자정 리셋 기능 테스트")
        trader3 = RealtimeTrader(api, account, daily_loss_limit=-2.0)
        trader3.initialize()
        
        # 초기 잔고 설정
        initial_balance = trader3.get_total_balance()
        print(f"초기 기준 잔고: {initial_balance:,}원")
        
        # 리셋 실행
        trader3.reset_daily_limit()
        print("✅ 자정 리셋 기능 테스트 완료")
        
        print("\n🎉 하루 손실 상한선 테스트 완료!")
        
    except Exception as e:
        logging.error(f"테스트 중 오류 발생: {e}")
        print(f"❌ 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("📉 하루 손실 상한선 기능 테스트")
    print("이 테스트는 하루 손실 상한선 기능을 검증합니다.")
    
    response = input("\n계속하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("테스트를 취소합니다.")
        return
    
    test_daily_loss_limit()

if __name__ == "__main__":
    main() 