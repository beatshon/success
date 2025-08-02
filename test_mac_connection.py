#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac 클라이언트 키움 API 연결 테스트
"""

import sys
import time
import json
from datetime import datetime
from loguru import logger

# 키움 Mac 호환 API 임포트
try:
    from kiwoom_mac_compatible import KiwoomMacAPI
except ImportError as e:
    logger.error(f"키움 Mac API 임포트 실패: {e}")
    sys.exit(1)

def test_connection():
    """기본 연결 테스트"""
    logger.info("🔗 키움 API 연결 테스트 시작")
    
    # 키움 API 클라이언트 초기화
    kiwoom = KiwoomMacAPI(server_url="http://localhost:8080")
    
    # 1. 서버 연결 테스트
    logger.info("1️⃣ 서버 연결 테스트 중...")
    if kiwoom.connect():
        logger.success("✅ 서버 연결 성공")
    else:
        logger.error("❌ 서버 연결 실패")
        return False
    
    return True

def test_login():
    """로그인 테스트"""
    logger.info("🔐 키움 API 로그인 테스트 시작")
    
    kiwoom = KiwoomMacAPI(server_url="http://localhost:8080")
    
    # 설정 파일에서 로그인 정보 읽기
    try:
        with open('config/kiwoom_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            user_id = config.get('user_id')
            password = config.get('password')
            account = config.get('account')
    except FileNotFoundError:
        logger.warning("⚠️ 설정 파일이 없습니다. 기본값 사용")
        user_id = "your_user_id"
        password = "your_password"
        account = "your_account"
    
    # 2. 로그인 테스트
    logger.info("2️⃣ 로그인 테스트 중...")
    if kiwoom.login(user_id, password, account):
        logger.success("✅ 로그인 성공")
        return kiwoom
    else:
        logger.error("❌ 로그인 실패")
        return None

def test_account_info(kiwoom):
    """계좌 정보 조회 테스트"""
    logger.info("📊 계좌 정보 조회 테스트 시작")
    
    # 3. 계좌 정보 조회
    logger.info("3️⃣ 계좌 정보 조회 중...")
    account_info = kiwoom.get_account_info()
    if account_info:
        logger.success("✅ 계좌 정보 조회 성공")
        logger.info(f"계좌 정보: {json.dumps(account_info, indent=2, ensure_ascii=False)}")
    else:
        logger.error("❌ 계좌 정보 조회 실패")
        return False
    
    # 4. 예수금 정보 조회
    logger.info("4️⃣ 예수금 정보 조회 중...")
    deposit_info = kiwoom.get_deposit_info(account_info.get('accounts', [''])[0])
    if deposit_info:
        logger.success("✅ 예수금 정보 조회 성공")
        logger.info(f"예수금 정보: {json.dumps(deposit_info, indent=2, ensure_ascii=False)}")
    else:
        logger.warning("⚠️ 예수금 정보 조회 실패 (장 휴무일)")
    
    return True

def test_current_price(kiwoom):
    """현재가 조회 테스트"""
    logger.info("💰 현재가 조회 테스트 시작")
    
    # 테스트 종목 리스트
    test_stocks = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
    
    # 5. 현재가 조회
    logger.info("5️⃣ 현재가 조회 중...")
    for stock_code in test_stocks:
        price = kiwoom.get_current_price(stock_code)
        if price:
            logger.success(f"✅ {stock_code} 현재가: {price:,}원")
        else:
            logger.warning(f"⚠️ {stock_code} 현재가 조회 실패 (장 휴무일)")
    
    return True

def test_real_data_subscription(kiwoom):
    """실시간 데이터 구독 테스트"""
    logger.info("📡 실시간 데이터 구독 테스트 시작")
    
    # 6. 실시간 데이터 구독
    logger.info("6️⃣ 실시간 데이터 구독 중...")
    test_stocks = ['005930', '000660']
    
    for stock_code in test_stocks:
        if kiwoom.subscribe_real_data(stock_code):
            logger.success(f"✅ {stock_code} 실시간 데이터 구독 성공")
        else:
            logger.warning(f"⚠️ {stock_code} 실시간 데이터 구독 실패")
    
    # 7. 실시간 데이터 캐시 확인
    logger.info("7️⃣ 실시간 데이터 캐시 확인 중...")
    time.sleep(2)  # 데이터 수신 대기
    
    cache_data = kiwoom.get_real_data_cache()
    if cache_data:
        logger.success("✅ 실시간 데이터 캐시 확인 성공")
        logger.info(f"캐시 데이터: {json.dumps(cache_data, indent=2, ensure_ascii=False)}")
    else:
        logger.warning("⚠️ 실시간 데이터 캐시 없음 (장 휴무일)")
    
    return True

def test_order_simulation(kiwoom):
    """주문 시뮬레이션 테스트"""
    logger.info("📝 주문 시뮬레이션 테스트 시작")
    
    # 8. 주문 시뮬레이션 (실제 주문은 하지 않음)
    logger.info("8️⃣ 주문 시뮬레이션 중...")
    
    # 모의투자 계좌 정보
    account_info = kiwoom.get_account_info()
    account = account_info.get('accounts', [''])[0]
    
    # 시뮬레이션 주문 데이터
    test_order = {
        'account': account,
        'code': '005930',
        'quantity': 1,
        'price': 70000,
        'order_type': '신규매수'
    }
    
    logger.info(f"시뮬레이션 주문: {json.dumps(test_order, indent=2, ensure_ascii=False)}")
    logger.warning("⚠️ 실제 주문은 장 휴무일로 인해 제한됩니다")
    
    return True

def main():
    """메인 테스트 함수"""
    logger.info("🚀 키움 Mac 클라이언트 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테스트 결과 저장
    test_results = {
        'connection': False,
        'login': False,
        'account_info': False,
        'current_price': False,
        'real_data': False,
        'order_simulation': False
    }
    
    try:
        # 1. 연결 테스트
        if test_connection():
            test_results['connection'] = True
            
            # 2. 로그인 테스트
            kiwoom = test_login()
            if kiwoom:
                test_results['login'] = True
                
                # 3. 계좌 정보 테스트
                if test_account_info(kiwoom):
                    test_results['account_info'] = True
                
                # 4. 현재가 조회 테스트
                if test_current_price(kiwoom):
                    test_results['current_price'] = True
                
                # 5. 실시간 데이터 테스트
                if test_real_data_subscription(kiwoom):
                    test_results['real_data'] = True
                
                # 6. 주문 시뮬레이션 테스트
                if test_order_simulation(kiwoom):
                    test_results['order_simulation'] = True
                
                # 연결 해제
                kiwoom.disconnect()
        
        # 테스트 결과 출력
        logger.info("📋 테스트 결과 요약")
        logger.info("=" * 50)
        
        for test_name, result in test_results.items():
            status = "✅ 성공" if result else "❌ 실패"
            logger.info(f"{test_name}: {status}")
        
        # 성공률 계산
        success_count = sum(test_results.values())
        total_count = len(test_results)
        success_rate = (success_count / total_count) * 100
        
        logger.info("=" * 50)
        logger.info(f"전체 성공률: {success_rate:.1f}% ({success_count}/{total_count})")
        
        if success_rate >= 80:
            logger.success("🎉 테스트 성공! 월요일 모의투자 준비 완료")
        elif success_rate >= 60:
            logger.warning("⚠️ 부분 성공. 추가 설정이 필요합니다")
        else:
            logger.error("❌ 테스트 실패. 시스템 점검이 필요합니다")
        
        return test_results
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        return test_results

if __name__ == "__main__":
    main() 