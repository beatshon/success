#!/usr/bin/env python3
"""
간단한 키움 API 연결 테스트
"""
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

def test_kiwoom_connection():
    """키움 API 연결 테스트"""
    print("🚀 간단한 키움 API 연결 테스트")
    print("=" * 50)
    
    # QApplication 생성
    app = QApplication(sys.argv)
    
    try:
        # 1. 키움 API 객체 생성
        print("1️⃣ 키움 API 객체 생성 중...")
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        print("✅ 키움 API 객체 생성 성공")
        
        # 2. 연결 상태 확인
        print("2️⃣ 연결 상태 확인 중...")
        connected = kiwoom.dynamicCall("GetConnectState()")
        print(f"📊 연결 상태: {connected}")
        
        # 3. 로그인 시도
        print("3️⃣ 로그인 시도 중...")
        login_result = kiwoom.dynamicCall("CommConnect()")
        print(f"📊 로그인 결과: {login_result}")
        
        # 4. 5초 대기
        print("4️⃣ 5초 대기 중...")
        time.sleep(5)
        
        # 5. 다시 연결 상태 확인
        print("5️⃣ 재연결 상태 확인 중...")
        connected_after = kiwoom.dynamicCall("GetConnectState()")
        print(f"📊 재연결 상태: {connected_after}")
        
        # 6. 계좌 정보 조회 시도
        print("6️⃣ 계좌 정보 조회 시도...")
        account_count = kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
        print(f"📊 계좌 개수: {account_count}")
        
        if account_count and int(account_count) > 0:
            account_list = kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
            print(f"📊 계좌 목록: {account_list}")
        
        print("=" * 50)
        print("✅ 테스트 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_kiwoom_connection() 