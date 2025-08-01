#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 주문 시스템 테스트
키움 API의 강화된 주문 기능을 테스트합니다.
"""

import sys
import time
from PyQt5.QtWidgets import QApplication
from kiwoom_api import KiwoomAPI, OrderType, OrderStatus
from loguru import logger

def test_order_system():
    """주문 시스템 테스트"""
    
    # QApplication 생성
    app = QApplication(sys.argv)
    
    # 키움 API 인스턴스 생성
    kiwoom = KiwoomAPI()
    
    # 로그인 콜백 설정
    def on_login(status):
        if status:
            logger.info("✅ 로그인 성공")
            # 계좌 정보 조회
            account_info = kiwoom.get_account_info()
            if account_info:
                account = list(account_info.keys())[0]  # 첫 번째 계좌 사용
                logger.info(f"계좌번호: {account}")
                
                # 테스트 주문 실행
                run_order_tests(kiwoom, account)
        else:
            logger.error("❌ 로그인 실패")
    
    kiwoom.set_login_callback(on_login)
    
    # 주문 콜백 설정
    def on_order(order_info):
        logger.info(f"📋 주문 상태 업데이트: {order_info}")
    
    kiwoom.set_order_callback(on_order)
    
    # 로그인
    logger.info("🔐 로그인 시도 중...")
    kiwoom.login()
    
    # 이벤트 루프 실행
    app.exec_()

def run_order_tests(kiwoom, account):
    """주문 테스트 실행"""
    logger.info("🧪 주문 시스템 테스트 시작")
    
    # 테스트용 종목 코드 (삼성전자)
    test_code = "005930"
    
    try:
        # 1. 예수금 조회
        logger.info("1️⃣ 예수금 조회 테스트")
        deposit_info = kiwoom.get_deposit_info(account)
        logger.info(f"예수금: {deposit_info.get('예수금', 0):,}원")
        
        # 2. 보유 종목 조회
        logger.info("2️⃣ 보유 종목 조회 테스트")
        position_info = kiwoom.get_position_info(account)
        logger.info(f"보유 종목 수: {len(position_info)}")
        
        # 3. 주문 검증 테스트
        logger.info("3️⃣ 주문 검증 테스트")
        is_valid, message = kiwoom.validate_order(account, test_code, 1, 50000, OrderType.BUY.value)
        logger.info(f"주문 검증 결과: {is_valid} - {message}")
        
        # 4. 매수 주문 테스트 (1주, 50,000원)
        logger.info("4️⃣ 매수 주문 테스트")
        order_no = kiwoom.buy_stock(account, test_code, 1, 50000)
        if order_no:
            logger.info(f"매수 주문 성공: 주문번호 {order_no}")
            
            # 주문 상태 확인
            time.sleep(2)
            order_status = kiwoom.get_order_status(order_no)
            if order_status:
                logger.info(f"주문 상태: {order_status}")
            
            # 대기 중인 주문 조회
            pending_orders = kiwoom.get_pending_orders()
            logger.info(f"대기 중인 주문: {len(pending_orders)}건")
            
            # 5. 주문 정정 테스트
            logger.info("5️⃣ 주문 정정 테스트")
            modify_result = kiwoom.modify_order(account, order_no, test_code, 1, 49000)
            if modify_result:
                logger.info(f"주문 정정 성공: {modify_result}")
            
            # 6. 주문 취소 테스트
            logger.info("6️⃣ 주문 취소 테스트")
            cancel_result = kiwoom.cancel_order(account, order_no, test_code, 1)
            if cancel_result:
                logger.info(f"주문 취소 성공: {cancel_result}")
        
        # 7. 시장가 주문 테스트
        logger.info("7️⃣ 시장가 주문 테스트")
        market_order_no = kiwoom.buy_market_order(account, test_code, 1)
        if market_order_no:
            logger.info(f"시장가 매수 주문 성공: {market_order_no}")
            
            # 즉시 취소
            time.sleep(1)
            kiwoom.cancel_order(account, market_order_no, test_code, 1)
        
        # 8. 전체 주문 취소 테스트
        logger.info("8️⃣ 전체 주문 취소 테스트")
        cancelled_count = kiwoom.cancel_all_orders(account)
        logger.info(f"전체 취소된 주문: {cancelled_count}건")
        
        logger.info("✅ 주문 시스템 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 주문 테스트 오류: {e}")

def test_order_validation():
    """주문 검증 테스트"""
    logger.info("🔍 주문 검증 테스트")
    
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    
    # 로그인
    if kiwoom.login():
        account_info = kiwoom.get_account_info()
        if account_info:
            account = list(account_info.keys())[0]
            
            # 다양한 검증 테스트
            test_cases = [
                (account, "005930", 1, 50000, OrderType.BUY.value, "정상 매수"),
                (account, "005930", 0, 50000, OrderType.BUY.value, "수량 0"),
                (account, "005930", 1, 0, OrderType.BUY.value, "가격 0"),
                ("", "005930", 1, 50000, OrderType.BUY.value, "계좌번호 없음"),
                (account, "", 1, 50000, OrderType.BUY.value, "종목코드 없음"),
            ]
            
            for account, code, quantity, price, order_type, description in test_cases:
                is_valid, message = kiwoom.validate_order(account, code, quantity, price, order_type)
                status = "✅" if is_valid else "❌"
                logger.info(f"{status} {description}: {message}")
    
    app.exec_()

if __name__ == "__main__":
    # 로그 설정
    logger.add("logs/order_test.log", rotation="1 day", retention="7 days")
    
    print("🔧 키움 API 주문 시스템 테스트")
    print("1. 전체 주문 시스템 테스트")
    print("2. 주문 검증 테스트")
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        test_order_system()
    elif choice == "2":
        test_order_validation()
    else:
        print("잘못된 선택입니다.") 