#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cross_platform_trader import KiwoomAPI, RealtimeTrader
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def test_order_retry_system():
    """주문 재시도 및 미체결 관리 시스템 테스트"""
    print("=" * 60)
    print("🔄 주문 재시도 및 미체결 관리 시스템 테스트")
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
        
        # 1. 기본 주문 재시도 테스트
        print("\n1️⃣ 기본 주문 재시도 테스트")
        trader1 = RealtimeTrader(api, account, max_retry=3, retry_delay=0.1)
        trader1.initialize()
        
        # 매수 주문 테스트
        order_id = trader1.send_order_with_retry("매수", 1, "005930.KS", 5, 80000, "00")
        if order_id:
            print(f"✅ 주문 성공: {order_id}")
            print(f"주문 상태: {trader1.order_status}")
        else:
            print("❌ 주문 실패")
        
        # 2. 주문 상태 확인 테스트
        print("\n2️⃣ 주문 상태 확인 테스트")
        if order_id:
            for i in range(3):
                status = trader1.check_order_status(order_id)
                print(f"체크 {i+1}: {order_id} -> {status}")
                time.sleep(0.2)
        
        # 3. 미체결 주문 관리 테스트
        print("\n3️⃣ 미체결 주문 관리 테스트")
        trader2 = RealtimeTrader(api, account, max_retry=2, retry_delay=0.1)
        trader2.initialize()
        
        # 여러 주문 생성
        orders = []
        for i in range(3):
            order_id = trader2.send_order_with_retry("매수", 1, f"000660.KS", 1, 30000, "00")
            if order_id:
                orders.append(order_id)
                print(f"주문 생성: {order_id}")
        
        # 주문 상태 확인
        for order_id in orders:
            trader2.check_order_status(order_id)
        
        print(f"주문 현황: {trader2.get_order_summary()}")
        
        # 미체결 주문 관리 실행
        trader2.manage_unfilled_orders()
        print(f"관리 후 주문 현황: {trader2.get_order_summary()}")
        
        # 4. 통합 테스트
        print("\n4️⃣ 통합 테스트")
        trader3 = RealtimeTrader(api, account, max_retry=3, retry_delay=0.1)
        trader3.initialize()
        
        # 매수 실행
        result = trader3.execute_buy("035420.KS")
        if result:
            print("✅ 매수 실행 성공")
            print(f"보유 종목: {len(trader3.positions)}개")
            print(f"주문 현황: {trader3.get_order_summary()}")
        else:
            print("❌ 매수 실행 실패")
        
        print("\n🎉 주문 재시도 및 미체결 관리 테스트 완료!")
        
    except Exception as e:
        logging.error(f"테스트 중 오류 발생: {e}")
        print(f"❌ 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("🔄 주문 재시도 및 미체결 관리 시스템 테스트")
    print("이 테스트는 주문 재시도, 미체결 관리 기능을 검증합니다.")
    
    response = input("\n계속하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("테스트를 취소합니다.")
        return
    
    test_order_retry_system()

if __name__ == "__main__":
    main() 