#!/usr/bin/env python3
"""
모의투자 환경 키움 API 테스트
"""

import sys
import time
from datetime import datetime

def test_demo_environment():
    """모의투자 환경 테스트"""
    print("=" * 50)
    print("모의투자 환경 키움 API 테스트")
    print("=" * 50)
    
    print("📋 테스트 환경 확인:")
    print(f"   테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Python 버전: {sys.version}")
    print(f"   운영체제: {sys.platform}")
    
    print("\n🔍 키움 API 환경 확인:")
    
    # PyQt5 확인
    try:
        from PyQt5.QAxContainer import QAxWidget
        from PyQt5.QtWidgets import QApplication
        print("   ✅ PyQt5 모듈 로드 성공")
    except ImportError as e:
        print(f"   ❌ PyQt5 모듈 로드 실패: {e}")
        return False
    
    # 키움 API 객체 생성 테스트
    try:
        app = QApplication(sys.argv)
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        if kiwoom.isNull():
            print("   ❌ 키움 API 객체 생성 실패")
            return False
        else:
            print("   ✅ 키움 API 객체 생성 성공")
            
    except Exception as e:
        print(f"   ❌ 키움 API 객체 생성 오류: {e}")
        return False
    
    print("\n📊 모의투자 환경 설정:")
    print("   1. 키움 영웅문 실행")
    print("   2. 모의투자 계좌로 로그인")
    print("   3. Open API+ 사용 신청 완료")
    print("   4. API 키 설정 완료")
    
    print("\n🎯 다음 단계:")
    print("   - 키움 영웅문에서 모의투자 계좌 로그인")
    print("   - Open API+ 사용 신청 및 승인")
    print("   - API 키 발급 및 설정")
    
    print("\n" + "=" * 50)
    print("✅ 모의투자 환경 테스트 완료")
    print("=" * 50)
    
    return True

def test_basic_functions():
    """기본 기능 테스트 (모의투자)"""
    print("\n🔄 기본 기능 테스트...")
    
    try:
        from PyQt5.QAxContainer import QAxWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 핸들러 설정
        def on_event_connect(err_code):
            if err_code == 0:
                print("   ✅ 로그인 성공")
            else:
                print(f"   ❌ 로그인 실패: {err_code}")
        
        kiwoom.OnEventConnect.connect(on_event_connect)
        
        # 로그인 시도
        print("   🔐 로그인 시도 중...")
        login_result = kiwoom.CommConnect()
        
        if login_result == 0:
            print("   ✅ 로그인 요청 성공")
            print("   ⏰ 5초 대기 중...")
            time.sleep(5)
            
            # 연결 상태 확인
            connect_state = kiwoom.GetConnectState()
            if connect_state == 1:
                print("   ✅ 키움 API 연결 성공!")
                
                # 계좌 정보 조회
                account_count = kiwoom.GetLoginInfo("ACCOUNT_CNT")
                print(f"   📊 보유 계좌 수: {account_count}")
                
                for i in range(int(account_count)):
                    account = kiwoom.GetLoginInfo("ACCNO")
                    print(f"   📋 계좌번호: {account}")
                
                return True
            else:
                print(f"   ❌ 키움 API 연결 실패: {connect_state}")
                return False
        else:
            print(f"   ❌ 로그인 요청 실패: {login_result}")
            return False
            
    except Exception as e:
        print(f"   ❌ 기본 기능 테스트 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 모의투자 환경 키움 API 테스트 시작")
    
    # 환경 테스트
    if not test_demo_environment():
        print("❌ 환경 테스트 실패")
        return
    
    # 기본 기능 테스트
    if test_basic_functions():
        print("\n🎉 모든 테스트 통과!")
        print("✅ 키움 API가 정상적으로 작동합니다.")
    else:
        print("\n❌ 일부 테스트 실패")
        print("🔧 키움 영웅문 설정을 확인해주세요.")

if __name__ == "__main__":
    main() 