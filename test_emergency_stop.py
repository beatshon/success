#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cross_platform_trader import KiwoomAPI, RealtimeTrader
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def test_emergency_stop():
    """비상정지 기능 테스트"""
    print("=" * 60)
    print("🚨 비상정지 기능 테스트")
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
        
        # 1. 정상 매수 테스트
        print("\n1️⃣ 정상 매수 테스트")
        result = trader.execute_buy("005930.KS")
        if result:
            print("✅ 매수 성공")
            print(f"보유 종목: {len(trader.positions)}개")
            print(f"예수금: {trader.account_info['예수금']:,}원")
        else:
            print("❌ 매수 실패")
        
        # 2. 비상정지 테스트
        print("\n2️⃣ 비상정지 테스트")
        print("의도적으로 오류를 발생시켜 비상정지를 테스트합니다...")
        
        # 의도적으로 오류 발생
        trader.emergency_stop_trading("테스트용 비상정지")
        
        print("✅ 비상정지 실행 완료")
        print(f"비상정지 플래그: {trader.emergency_stop}")
        print(f"보유 종목: {len(trader.positions)}개")
        print(f"최종 예수금: {trader.account_info['예수금']:,}원")
        
        # 3. 로그 파일 확인
        print("\n3️⃣ 로그 파일 확인")
        log_dir = trader.logger.log_dir
        print(f"로그 디렉토리: {log_dir}")
        
        # 로그 파일 목록 출력
        import os
        for file in os.listdir(log_dir):
            file_path = os.path.join(log_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  📄 {file} ({size} bytes)")
        
        print("\n🎉 비상정지 테스트 완료!")
        print("로그 파일에서 상세 내용을 확인하세요.")
        
    except Exception as e:
        logging.error(f"테스트 중 오류 발생: {e}")
        print(f"❌ 테스트 실패: {e}")

def test_error_logging():
    """오류 로깅 테스트"""
    print("\n" + "=" * 60)
    print("📝 오류 로깅 테스트")
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
        
        # 다양한 오류 로깅 테스트
        print("다양한 오류 상황을 로깅합니다...")
        
        trader.logger.log_error("테스트오류1", "매수 주문 실패", "발생")
        trader.logger.log_error("테스트오류2", "API 연결 오류", "발생")
        trader.logger.log_error("테스트오류3", "데이터 수신 실패", "발생")
        trader.logger.log_error("테스트오류4", "메모리 부족", "발생")
        
        print("✅ 오류 로깅 테스트 완료")
        
        # 오류 로그 파일 확인
        error_log_file = trader.logger.error_log_file
        print(f"오류 로그 파일: {error_log_file}")
        
        # 파일 내용 확인
        import csv
        with open(error_log_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            print(f"총 {len(rows)-1}개의 오류 로그가 기록되었습니다.")
            
            for i, row in enumerate(rows[1:], 1):  # 헤더 제외
                print(f"  {i}. {row[1]}: {row[2]} ({row[3]})")
        
    except Exception as e:
        logging.error(f"오류 로깅 테스트 중 오류 발생: {e}")
        print(f"❌ 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("🚨 비상정지 및 로깅 시스템 테스트")
    print("이 테스트는 의도적으로 오류를 발생시켜 비상정지 기능을 검증합니다.")
    
    response = input("\n계속하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("테스트를 취소합니다.")
        return
    
    # 1. 비상정지 테스트
    test_emergency_stop()
    
    # 2. 오류 로깅 테스트
    test_error_logging()
    
    print("\n🎯 모든 테스트 완료!")
    print("logs/2025-08-03/ 디렉토리에서 상세 로그를 확인하세요.")

if __name__ == "__main__":
    main() 