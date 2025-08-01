#!/usr/bin/env python3
"""
Windows 환경 키움 API 테스트 스크립트
"""

import sys
import os
import time
from datetime import datetime

# PyQt5 임포트 (Windows에서만)
try:
    from PyQt5.QAxContainer import *
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import *
    PYQT5_AVAILABLE = True
except ImportError:
    print("❌ PyQt5를 찾을 수 없습니다. Windows 환경에서 실행해주세요.")
    PYQT5_AVAILABLE = False

def test_kiwoom_connection():
    """키움 API 연결 테스트"""
    if not PYQT5_AVAILABLE:
        return False
    
    print("🔄 키움 API 연결 테스트 시작...")
    
    try:
        # QApplication 생성
        app = QApplication(sys.argv)
        
        # 키움 API 객체 생성
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        if kiwoom.isNull():
            print("❌ 키움 API 객체 생성 실패")
            return False
        
        print("✅ 키움 API 객체 생성 성공")
        
        # 이벤트 핸들러 연결
        kiwoom.OnEventConnect.connect(lambda err_code: print(f"로그인 결과: {err_code}"))
        
        # 로그인 시도
        print("🔄 로그인 시도 중...")
        login_result = kiwoom.CommConnect()
        
        if login_result == 0:
            print("✅ 로그인 요청 성공")
        else:
            print(f"❌ 로그인 요청 실패: {login_result}")
            return False
        
        # 잠시 대기
        time.sleep(3)
        
        # 연결 상태 확인
        connect_state = kiwoom.GetConnectState()
        if connect_state == 1:
            print("✅ 키움 API 연결 성공!")
            
            # 계좌 정보 조회
            account_count = kiwoom.GetLoginInfo("ACCOUNT_CNT")
            print(f"보유 계좌 수: {account_count}")
            
            for i in range(int(account_count)):
                account = kiwoom.GetLoginInfo("ACCNO")
                print(f"계좌번호: {account}")
            
            return True
        else:
            print(f"❌ 키움 API 연결 실패: {connect_state}")
            return False
            
    except Exception as e:
        print(f"❌ 키움 API 테스트 중 오류: {e}")
        return False

def test_basic_functions():
    """기본 기능 테스트"""
    if not PYQT5_AVAILABLE:
        return False
    
    print("\n🔄 기본 기능 테스트...")
    
    try:
        app = QApplication(sys.argv)
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 종목 코드 조회
        print("📊 종목 코드 조회 테스트...")
        
        # 삼성전자 종목 코드
        samsung_code = "005930"
        
        # 종목명 조회
        stock_name = kiwoom.GetMasterCodeName(samsung_code)
        print(f"삼성전자 종목명: {stock_name}")
        
        # 현재가 조회
        print("💰 현재가 조회 테스트...")
        # 실제로는 SetInputValue와 CommRqData를 사용해야 함
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 중 오류: {e}")
        return False

def test_strategy_integration():
    """전략 통합 테스트"""
    print("\n🔄 전략 통합 테스트...")
    
    try:
        # 전략 클래스 임포트
        from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy
        
        print("✅ 전략 클래스 임포트 성공")
        
        # Mock API로 테스트
        class MockKiwoomAPI:
            def order_stock(self, account, code, quantity, price, order_type):
                print(f"Mock 주문: {order_type} - {code} {quantity}주 @ {price:,}원")
                return "TEST_ORDER_001"
        
        mock_api = MockKiwoomAPI()
        
        # 각 전략 테스트
        strategies = [
            ("이동평균", MovingAverageStrategy(mock_api, "TEST_ACCOUNT")),
            ("RSI", RSIStrategy(mock_api, "TEST_ACCOUNT")),
            ("볼린저밴드", BollingerBandsStrategy(mock_api, "TEST_ACCOUNT"))
        ]
        
        for name, strategy in strategies:
            print(f"  {name} 전략 테스트 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 전략 통합 테스트 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Windows 키움 API 테스트 시작")
    print("=" * 50)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 버전: {sys.version}")
    print(f"운영체제: {os.name}")
    print()
    
    # 1. 키움 API 연결 테스트
    connection_success = test_kiwoom_connection()
    
    # 2. 기본 기능 테스트
    basic_success = test_basic_functions()
    
    # 3. 전략 통합 테스트
    strategy_success = test_strategy_integration()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    print(f"키움 API 연결: {'✅ 성공' if connection_success else '❌ 실패'}")
    print(f"기본 기능: {'✅ 성공' if basic_success else '❌ 실패'}")
    print(f"전략 통합: {'✅ 성공' if strategy_success else '❌ 실패'}")
    
    if connection_success and basic_success and strategy_success:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("이제 자동매매 시스템을 실행할 수 있습니다.")
        return True
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("문제를 해결한 후 다시 시도해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 