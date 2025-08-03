#!/usr/bin/env python3
"""
pykiwoom 라이브러리를 사용한 키움 API 연결 테스트
ActiveX 직접 제어 대신 파이썬 래퍼 사용
"""
import sys
import time
from datetime import datetime

def test_pykiwoom_connection():
    """pykiwoom을 사용한 키움 API 연결 테스트"""
    print("🚀 pykiwoom 키움 API 연결 테스트")
    print("=" * 50)
    
    try:
        # pykiwoom 라이브러리 임포트
        from pykiwoom.kiwoom import Kiwoom
        
        print("1️⃣ pykiwoom 라이브러리 임포트 성공")
        
        # 키움 API 객체 생성
        print("2️⃣ 키움 API 객체 생성 중...")
        kiwoom = Kiwoom()
        print("✅ 키움 API 객체 생성 성공")
        
        # 연결 상태 확인
        print("3️⃣ 초기 연결 상태 확인...")
        connected = kiwoom.GetConnectState()
        print(f"📊 초기 연결 상태: {connected}")
        
        # 로그인 시도 (block=True로 로그인 창 표시)
        print("4️⃣ 로그인 시도 중...")
        print("⚠️ 로그인 창이 표시됩니다. RDP 세션이 활성화되어 있어야 합니다.")
        
        login_result = kiwoom.CommConnect(block=True)
        print(f"📊 로그인 결과: {login_result}")
        
        # 로그인 후 잠시 대기
        print("5️⃣ 로그인 후 3초 대기...")
        time.sleep(3)
        
        # 다시 연결 상태 확인
        print("6️⃣ 로그인 후 연결 상태 확인...")
        connected_after = kiwoom.GetConnectState()
        print(f"📊 로그인 후 연결 상태: {connected_after}")
        
        if connected_after == 1:
            print("✅ 로그인 성공!")
            
            # 계좌 정보 조회
            print("7️⃣ 계좌 정보 조회...")
            account_no = kiwoom.GetLoginInfo("ACCNO")
            user_id = kiwoom.GetLoginInfo("USER_ID")
            user_name = kiwoom.GetLoginInfo("USER_NAME")
            
            print(f"📊 계좌번호: {account_no}")
            print(f"📊 사용자 ID: {user_id}")
            print(f"📊 사용자명: {user_name}")
            
            # 계좌 목록 조회
            print("8️⃣ 계좌 목록 조회...")
            account_list = kiwoom.GetLoginInfo("ACCLIST")
            print(f"📊 계좌 목록: {account_list}")
            
            # 서버 정보 조회
            print("9️⃣ 서버 정보 조회...")
            server_gubun = kiwoom.GetLoginInfo("GetServerGubun")
            print(f"📊 서버 구분: {server_gubun}")
            
            return True
            
        else:
            print("❌ 로그인 실패")
            print("💡 다음을 확인하세요:")
            print("   - 키움 영웅문이 실행되어 있는지")
            print("   - RDP 세션이 활성화되어 있는지")
            print("   - 로그인 창이 표시되었는지")
            return False
            
    except ImportError as e:
        print(f"❌ pykiwoom 라이브러리 임포트 실패: {e}")
        print("💡 pip install pykiwoom 명령으로 설치하세요.")
        return False
        
    except Exception as e:
        print(f"❌ pykiwoom 연결 오류: {e}")
        return False

def test_pykiwoom_basic_functions():
    """pykiwoom 기본 기능 테스트"""
    print("\n🔧 pykiwoom 기본 기능 테스트")
    print("=" * 50)
    
    try:
        from pykiwoom.kiwoom import Kiwoom
        
        kiwoom = Kiwoom()
        
        # 기본 정보 조회
        print("1️⃣ 기본 정보 조회...")
        print(f"📊 API 버전: {kiwoom.GetAPIModulePath()}")
        print(f"📊 연결 상태: {kiwoom.GetConnectState()}")
        
        # 에러 코드 조회
        print("2️⃣ 에러 코드 조회...")
        error_code = kiwoom.GetLastError()
        print(f"📊 마지막 에러 코드: {error_code}")
        
        # TR 요청 제한 확인
        print("3️⃣ TR 요청 제한 확인...")
        tr_count = kiwoom.GetTRCountLimit("005930")
        print(f"📊 TR 요청 제한: {tr_count}")
        
        print("✅ 기본 기능 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 오류: {e}")
        return False

def test_pykiwoom_stock_info():
    """pykiwoom 주식 정보 조회 테스트"""
    print("\n📈 pykiwoom 주식 정보 조회 테스트")
    print("=" * 50)
    
    try:
        from pykiwoom.kiwoom import Kiwoom
        
        kiwoom = Kiwoom()
        
        # 연결 상태 확인
        if kiwoom.GetConnectState() != 1:
            print("⚠️ 로그인이 필요합니다. 먼저 로그인을 진행하세요.")
            return False
        
        # 삼성전자 기본 정보 조회
        print("1️⃣ 삼성전자 기본 정보 조회...")
        stock_code = "005930"
        
        # 종목명 조회
        stock_name = kiwoom.GetMasterCodeName(stock_code)
        print(f"📊 종목명: {stock_name}")
        
        # 종목 상장일 조회
        listing_date = kiwoom.GetMasterListedStockDate(stock_code)
        print(f"📊 상장일: {listing_date}")
        
        # 종목 구분 조회
        stock_type = kiwoom.GetMasterStockInfo(stock_code)
        print(f"📊 종목 구분: {stock_type}")
        
        print("✅ 주식 정보 조회 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 주식 정보 조회 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🔍 pykiwoom 종합 테스트 시작")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 기본 연결 테스트
    connection_success = test_pykiwoom_connection()
    
    if connection_success:
        # 2. 기본 기능 테스트
        basic_success = test_pykiwoom_basic_functions()
        
        # 3. 주식 정보 조회 테스트
        stock_success = test_pykiwoom_stock_info()
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약:")
        print(f"✅ 연결 테스트: {'성공' if connection_success else '실패'}")
        print(f"✅ 기본 기능 테스트: {'성공' if basic_success else '실패'}")
        print(f"✅ 주식 정보 조회: {'성공' if stock_success else '실패'}")
        
        if connection_success and basic_success and stock_success:
            print("\n🎉 모든 테스트 성공! pykiwoom 연동 완료!")
        else:
            print("\n⚠️ 일부 테스트 실패. 추가 설정이 필요할 수 있습니다.")
    else:
        print("\n❌ 연결 테스트 실패. 로그인을 먼저 진행하세요.")
    
    print("\n💡 참고사항:")
    print("- RDP 세션이 활성화되어 있어야 로그인 창이 표시됩니다.")
    print("- 세션이 끊기면 자동매매가 멈출 수 있습니다.")
    print("- 지속 실행을 위해서는 '원격 세션 유지 툴'이나 '가상 디스플레이'를 고려하세요.")
    
    print("\n" + "=" * 60)
    print("✅ pykiwoom 테스트 완료!")

if __name__ == "__main__":
    main() 