#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cross_platform_trader import KiwoomAPI, RealtimeTrader
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def test_daily_summary():
    """일일 요약 기능 테스트"""
    print("=" * 60)
    print("📊 일일 요약 리포트 테스트")
    print("=" * 60)
    
    try:
        # API 초기화
        api = KiwoomAPI()
        api.login()
        
        # 계좌 정보 조회
        account_info = api.get_account_info()
        account = account_info["계좌번호"]
        
        # 트레이더 초기화
        trader = RealtimeTrader(api, account)
        trader.initialize()
        
        print("✅ 시스템 초기화 완료")
        print(f"계좌: {account}")
        print(f"초기 예수금: {trader.account_info['예수금']:,}원")
        
        # 1. 매수 테스트 (로그 생성)
        print("\n1️⃣ 매수 테스트 (로그 생성)")
        result1 = trader.execute_buy("005930.KS")
        result2 = trader.execute_buy("000660.KS")
        
        if result1 and result2:
            print("✅ 매수 성공 - 로그 파일 생성됨")
            print(f"보유 종목: {len(trader.positions)}개")
            print(f"예수금: {trader.account_info['예수금']:,}원")
        else:
            print("❌ 매수 실패")
        
        # 2. 일일 요약 테스트
        print("\n2️⃣ 일일 요약 테스트")
        print("일일 요약 리포트를 생성하고 텔레그램으로 전송합니다...")
        
        trader.daily_summary()
        
        print("✅ 일일 요약 리포트 전송 완료")
        
        # 3. 로그 파일 확인
        print("\n3️⃣ 로그 파일 확인")
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        log_dir = f'logs/{today}'
        
        if os.path.exists(log_dir):
            print(f"로그 디렉토리: {log_dir}")
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  📄 {file} ({size} bytes)")
        else:
            print("❌ 로그 디렉토리가 존재하지 않습니다")
        
        print("\n🎉 일일 요약 테스트 완료!")
        print("텔레그램에서 일일 요약 리포트를 확인하세요.")
        
    except Exception as e:
        logging.error(f"테스트 중 오류 발생: {e}")
        print(f"❌ 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("📊 일일 요약 리포트 테스트")
    print("이 테스트는 일일 매매 요약 리포트 기능을 검증합니다.")
    
    response = input("\n계속하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("테스트를 취소합니다.")
        return
    
    test_daily_summary()

if __name__ == "__main__":
    main() 