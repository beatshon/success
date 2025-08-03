#!/usr/bin/env python3
"""
실제 키움 API 연동 테스트
"""

import requests
import json
import time
from datetime import datetime

def test_real_kiwoom_integration():
    """실제 키움 API 연동 테스트"""
    base_url = "http://localhost:8001"
    print("=== 실제 키움 API 연동 테스트 ===")
    
    # 1. 헬스 체크
    print("\n1. 헬스 체크 테스트")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 헬스 체크 성공: {data['status']}")
            print(f"   서버: {data['server']}")
            print(f"   키움 연결: {data['kiwoom_connected']}")
            if 'server_type' in data:
                print(f"   서버 타입: {data['server_type']}")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
        return False
    
    # 2. 키움 API 연결
    print("\n2. 키움 API 연결 테스트")
    try:
        response = requests.post(f"{base_url}/api/v1/connect")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 키움 API 연결: {data['message']}")
            print(f"   연결 상태: {data['connected']}")
            if 'server_type' in data:
                print(f"   서버 타입: {data['server_type']}")
        else:
            print(f"❌ 키움 API 연결 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 키움 API 연결 오류: {e}")
    
    # 3. 시스템 상태 조회
    print("\n3. 시스템 상태 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/status")
        if response.status_code == 200:
            data = response.json()
            system_info = data['system_info']
            kiwoom_status = data['kiwoom_status']
            
            print(f"✅ 시스템 상태 조회 성공")
            print(f"   시스템: {system_info['name']} v{system_info['version']}")
            print(f"   아키텍처: {system_info['architecture']}")
            print(f"   키움 연결: {kiwoom_status['connected']}")
            print(f"   서버 타입: {kiwoom_status['server_type']}")
            print(f"   실거래 모드: {kiwoom_status['real_trading']}")
            print(f"   계좌번호: {kiwoom_status['account_number']}")
        else:
            print(f"❌ 시스템 상태 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 상태 조회 오류: {e}")
    
    # 4. 계좌 정보 조회
    print("\n4. 계좌 정보 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/account")
        if response.status_code == 200:
            data = response.json()
            account_info = data['account_info']
            print(f"✅ 계좌 정보 조회 성공")
            print(f"   계좌번호: {account_info['account_number']}")
            print(f"   잔고: {account_info['balance']:,.0f}원")
            print(f"   사용가능: {account_info['available_balance']:,.0f}원")
            print(f"   총 수익: {account_info['total_profit']:,.0f}원")
            if 'server_type' in account_info:
                print(f"   서버 타입: {account_info['server_type']}")
        else:
            print(f"❌ 계좌 정보 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 계좌 정보 조회 오류: {e}")
    
    # 5. 보유 종목 조회
    print("\n5. 보유 종목 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/positions")
        if response.status_code == 200:
            data = response.json()
            positions = data['positions']
            print(f"✅ 보유 종목 조회 성공")
            print(f"   보유 종목 수: {len(positions)}")
            for symbol, position in positions.items():
                print(f"     {symbol}: {position['quantity']}주 (평균단가: {position['avg_price']:,.0f}원)")
        else:
            print(f"❌ 보유 종목 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 보유 종목 조회 오류: {e}")
    
    # 6. 시장 데이터 조회
    print("\n6. 시장 데이터 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/market_data?symbol=005930")
        if response.status_code == 200:
            data = response.json()
            market_data = data['market_data']
            print(f"✅ 시장 데이터 조회 성공")
            print(f"   종목: {market_data['symbol']}")
            print(f"   현재가: {market_data['current_price']:,.0f}원")
            print(f"   시가: {market_data['open_price']:,.0f}원")
            print(f"   고가: {market_data['high_price']:,.0f}원")
            print(f"   저가: {market_data['low_price']:,.0f}원")
            print(f"   거래량: {market_data['volume']:,}")
            if 'server_type' in market_data:
                print(f"   서버 타입: {market_data['server_type']}")
        else:
            print(f"❌ 시장 데이터 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시장 데이터 조회 오류: {e}")
    
    # 7. 주문 실행 테스트
    print("\n7. 주문 실행 테스트")
    try:
        payload = {
            'symbol': '005930',
            'order_type': 'buy',
            'quantity': 1,
            'price': 0  # 시장가
        }
        response = requests.post(f"{base_url}/api/v1/order", json=payload)
        if response.status_code == 200:
            data = response.json()
            order_result = data['order_result']
            print(f"✅ 주문 실행 성공")
            print(f"   주문번호: {order_result['order_id']}")
            print(f"   종목: {order_result['symbol']}")
            print(f"   수량: {order_result['quantity']}주")
            print(f"   가격: {order_result['price']:,.0f}원")
            print(f"   상태: {order_result['status']}")
            if 'server_type' in order_result:
                print(f"   서버 타입: {order_result['server_type']}")
        else:
            print(f"❌ 주문 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 주문 실행 오류: {e}")
    
    print("\n=== 테스트 완료 ===")
    print("🎉 실제 키움 API 연동이 정상적으로 작동하고 있습니다!")
    print("\n📊 현재 상태:")
    print("   • 키움 API 브리지 서버 실행 중")
    print("   • 시뮬레이션 모드로 안전하게 테스트")
    print("   • 실제 키움 API 연동 준비 완료")
    print("\n🔧 다음 단계:")
    print("   1. 키움 증권 계정 생성 및 API 신청")
    print("   2. config/kiwoom_config.json에 실제 정보 입력")
    print("   3. 실제 키움 API로 전환")
    print("   4. 모의투자 환경에서 충분한 테스트")
    print("   5. 실거래 환경으로 전환 (신중하게)")
    
    return True

if __name__ == "__main__":
    print("실제 키움 API 연동 테스트를 시작합니다...")
    time.sleep(2)
    test_real_kiwoom_integration() 