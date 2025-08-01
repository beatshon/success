"""
키움증권 API 연동 테스트
"""

import sys
import time
from PyQt5.QtWidgets import QApplication
from loguru import logger
from kiwoom_api import KiwoomAPI
from config import KIWOOM_CONFIG, validate_config, get_error_message

def test_api_connection():
    """API 연동 테스트"""
    print("=" * 50)
    print("키움증권 API 연동 테스트 시작")
    print("=" * 50)
    
    try:
        # 설정 유효성 검사
        validate_config()
        print("✅ 설정 파일 검증 완료")
        
        # QApplication 생성 (PyQt5 필요)
        app = QApplication(sys.argv)
        
        # API 객체 생성
        api = KiwoomAPI()
        print("✅ API 객체 생성 완료")
        
        # 로그인 테스트
        print("\n🔐 로그인 테스트 중...")
        if api.login(timeout=30):
            print("✅ 로그인 성공!")
            
            # 계좌 정보 조회
            print("\n📊 계좌 정보 조회 중...")
            account_info = api.get_account_info()
            if account_info:
                print("✅ 계좌 정보 조회 성공!")
                for account, info in account_info.items():
                    print(f"   계좌번호: {account}")
                    print(f"   사용자명: {info.get('user_name', 'N/A')}")
                    print(f"   사용자ID: {info.get('user_id', 'N/A')}")
            else:
                print("❌ 계좌 정보 조회 실패")
            
            # 종목 정보 조회 테스트
            print("\n📈 종목 정보 조회 테스트...")
            test_codes = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
            
            for code in test_codes:
                print(f"\n   종목코드 {code} 조회 중...")
                stock_info = api.get_stock_basic_info(code)
                if stock_info and stock_info.get('name'):
                    print(f"   ✅ {code} - {stock_info['name']}")
                else:
                    print(f"   ❌ {code} - 조회 실패")
            
            # 현재가 조회 테스트
            print("\n💰 현재가 조회 테스트...")
            for code in test_codes[:2]:  # 처음 2개 종목만 테스트
                print(f"\n   {code} 현재가 조회 중...")
                price_info = api.get_current_price(code)
                if price_info and price_info.get('current_price'):
                    print(f"   ✅ 현재가: {price_info['current_price']:,}원")
                else:
                    print(f"   ❌ 현재가 조회 실패")
                time.sleep(1)  # API 제한 고려
            
            print("\n" + "=" * 50)
            print("🎉 API 연동 테스트 완료!")
            print("=" * 50)
            
        else:
            print("❌ 로그인 실패!")
            print("   - 영웅문이 실행되어 있는지 확인하세요")
            print("   - 모의투자 계좌로 로그인되어 있는지 확인하세요")
            print("   - API 키가 올바르게 설정되어 있는지 확인하세요")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        logger.error(f"API 테스트 오류: {e}")

def test_real_time_data():
    """실시간 데이터 테스트"""
    print("\n" + "=" * 50)
    print("실시간 데이터 테스트 시작")
    print("=" * 50)
    
    try:
        app = QApplication(sys.argv)
        api = KiwoomAPI()
        
        if api.login(timeout=30):
            print("✅ 로그인 성공")
            
            # 실시간 데이터 콜백 설정
            def on_real_data(code, data):
                print(f"📊 실시간 데이터: {code} - {data.get('current_price', 0):,}원 ({data.get('change_rate', 0):+.2f}%)")
            
            api.set_real_data_callback(on_real_data)
            
            # 실시간 데이터 구독
            test_code = '005930'  # 삼성전자
            print(f"\n📡 {test_code} 실시간 데이터 구독 중...")
            api.subscribe_real_data(test_code)
            
            print("⏰ 10초간 실시간 데이터 수신 대기 중...")
            print("   (Ctrl+C로 중단 가능)")
            
            # 10초간 대기
            time.sleep(10)
            
            # 구독 해제
            api.unsubscribe_real_data(test_code)
            print("✅ 실시간 데이터 테스트 완료")
            
        else:
            print("❌ 로그인 실패")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 실시간 데이터 테스트 오류: {e}")

def main():
    """메인 함수"""
    print("키움증권 API 테스트 프로그램")
    print("1. 기본 API 연동 테스트")
    print("2. 실시간 데이터 테스트")
    print("3. 전체 테스트")
    
    try:
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == '1':
            test_api_connection()
        elif choice == '2':
            test_real_time_data()
        elif choice == '3':
            test_api_connection()
            test_real_time_data()
        else:
            print("잘못된 선택입니다.")
            
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main() 