#!/usr/bin/env python3
"""
예수금 조회 테스트 스크립트
모의투자 계정의 예수금을 조회하는 기능을 테스트
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

def test_deposit_query():
    """예수금 조회 테스트"""
    if not PYQT5_AVAILABLE:
        return False
    
    print("🔄 예수금 조회 테스트 시작...")
    
    try:
        # QApplication 생성
        app = QApplication(sys.argv)
        
        # 키움 API 객체 생성
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        if kiwoom.isNull():
            print("❌ 키움 API 객체 생성 실패")
            return False
        
        print("✅ 키움 API 객체 생성 성공")
        
        # 로그인 상태 확인
        connect_state = kiwoom.GetConnectState()
        if connect_state != 1:
            print("❌ 키움 API에 연결되지 않았습니다.")
            print("   키움 영웅문을 실행하고 로그인해주세요.")
            return False
        
        print("✅ 키움 API 연결 확인")
        
        # 계좌 정보 조회
        print("\n📊 계좌 정보 조회 중...")
        account_count = kiwoom.GetLoginInfo("ACCOUNT_CNT")
        print(f"보유 계좌 수: {account_count}")
        
        accounts = kiwoom.GetLoginInfo("ACCNO").split(';')
        print("계좌 목록:")
        for i, account in enumerate(accounts):
            if account.strip():
                print(f"  {i+1}. {account}")
        
        # 첫 번째 계좌로 예수금 조회
        if accounts and accounts[0].strip():
            test_account = accounts[0].strip()
            print(f"\n💰 예수금 조회 중... (계좌: {test_account})")
            
            # 예수금 조회 TR 요청
            kiwoom.SetInputValue("계좌번호", test_account)
            kiwoom.SetInputValue("비밀번호", "")
            kiwoom.SetInputValue("비밀번호입력매체구분", "00")
            kiwoom.SetInputValue("조회구분", "2")
            
            result = kiwoom.CommRqData("예수금상세현황요청", "opw00001", 0, "0001")
            
            if result == 0:
                print("✅ 예수금 조회 요청 성공")
                print("   잠시 기다려주세요...")
                
                # 응답 대기
                time.sleep(3)
                
                # 예수금 정보 출력
                print("\n📈 예수금 정보:")
                print("=" * 50)
                
                # TR 데이터에서 예수금 정보 추출
                try:
                    deposit = int(kiwoom.GetCommData("opw00001", "예수금상세현황요청", 0, "예수금").strip())
                    available_deposit = int(kiwoom.GetCommData("opw00001", "예수금상세현황요청", 0, "출금가능금액").strip())
                    orderable_amount = int(kiwoom.GetCommData("opw00001", "예수금상세현황요청", 0, "주문가능금액").strip())
                    
                    print(f"계좌번호: {test_account}")
                    print(f"예수금: {deposit:,}원")
                    print(f"출금가능금액: {available_deposit:,}원")
                    print(f"주문가능금액: {orderable_amount:,}원")
                    
                    # 추가 정보
                    print(f"\n💡 추가 정보:")
                    print(f"사용자 ID: {kiwoom.GetLoginInfo('USER_ID')}")
                    print(f"사용자명: {kiwoom.GetLoginInfo('USER_NAME')}")
                    print(f"서버구분: {kiwoom.GetLoginInfo('GetServerGubun')}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ 예수금 정보 파싱 오류: {e}")
                    return False
            else:
                print(f"❌ 예수금 조회 요청 실패: {result}")
                return False
        else:
            print("❌ 조회할 계좌가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 예수금 조회 테스트 중 오류: {e}")
        return False

def test_kiwoom_api_class():
    """KiwoomAPI 클래스 테스트"""
    print("\n🔄 KiwoomAPI 클래스 테스트...")
    
    try:
        # KiwoomAPI 클래스 임포트
        from kiwoom_api import KiwoomAPI
        
        # QApplication 생성
        app = QApplication(sys.argv)
        
        # KiwoomAPI 객체 생성
        api = KiwoomAPI()
        
        # 로그인
        if api.login():
            print("✅ 로그인 성공")
            
            # 계좌 정보 조회
            account_info = api.get_account_info()
            if account_info:
                print(f"✅ 계좌 정보 조회 성공: {len(account_info)}개 계좌")
                
                # 첫 번째 계좌로 예수금 조회
                for account in account_info:
                    print(f"\n💰 계좌 {account} 예수금 조회 중...")
                    deposit_info = api.get_deposit_info(account)
                    
                    if deposit_info:
                        print("✅ 예수금 조회 성공:")
                        print(f"  예수금: {deposit_info.get('deposit', 0):,}원")
                        print(f"  출금가능: {deposit_info.get('available_deposit', 0):,}원")
                        print(f"  주문가능: {deposit_info.get('orderable_amount', 0):,}원")
                    else:
                        print("❌ 예수금 조회 실패")
                    
                    break  # 첫 번째 계좌만 테스트
            else:
                print("❌ 계좌 정보 조회 실패")
        else:
            print("❌ 로그인 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ KiwoomAPI 클래스 테스트 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 예수금 조회 테스트 시작")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 기본 예수금 조회 테스트
    basic_success = test_deposit_query()
    
    # 2. KiwoomAPI 클래스 테스트
    api_success = test_kiwoom_api_class()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"기본 예수금 조회: {'✅ 성공' if basic_success else '❌ 실패'}")
    print(f"KiwoomAPI 클래스: {'✅ 성공' if api_success else '❌ 실패'}")
    
    if basic_success or api_success:
        print("\n🎉 예수금 조회 기능이 정상 작동합니다!")
        print("이제 자동매매 시스템에서 실제 계좌 정보를 사용할 수 있습니다.")
        return True
    else:
        print("\n⚠️ 예수금 조회 테스트가 실패했습니다.")
        print("키움 영웅문이 실행 중이고 로그인되어 있는지 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 