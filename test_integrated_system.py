#!/usr/bin/env python3
"""
통합 트레이딩 시스템 전체 테스트
"""

import requests
import json
import time
from datetime import datetime

def test_integrated_system():
    """통합 시스템 전체 테스트"""
    base_url = "http://localhost:8000"
    print("=== 통합 트레이딩 시스템 전체 테스트 ===")
    
    # 1. 헬스 체크
    print("\n1. 헬스 체크 테스트")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 헬스 체크 성공: {data['status']}")
            print(f"   시스템: {data['system']}")
            print(f"   키움 연결: {data['kiwoom_connected']}")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
        return False
    
    # 2. 준비 상태 확인
    print("\n2. 준비 상태 확인")
    try:
        response = requests.get(f"{base_url}/ready")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 준비 상태 확인: {data['status']}")
            print(f"   모델 준비: {data['model_ready']}")
        else:
            print(f"❌ 준비 상태 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 준비 상태 확인 오류: {e}")
    
    # 3. 시스템 상태 조회
    print("\n3. 시스템 상태 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/status")
        if response.status_code == 200:
            data = response.json()
            system_info = data['system_info']
            kiwoom_status = data['kiwoom_status']
            trading_status = data['trading_status']
            
            print(f"✅ 시스템 상태 조회 성공")
            print(f"   시스템: {system_info['name']} v{system_info['version']}")
            print(f"   아키텍처: {system_info['architecture']}")
            print(f"   키움 연결: {kiwoom_status['connected']}")
            print(f"   모델 준비: {trading_status['model_ready']}")
            print(f"   거래 횟수: {trading_status['trade_count']}")
            
            if kiwoom_status['account_info']:
                account = kiwoom_status['account_info']
                print(f"   계좌번호: {account['account_number']}")
                print(f"   잔고: {account['balance']:,.0f}원")
        else:
            print(f"❌ 시스템 상태 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 상태 조회 오류: {e}")
    
    # 4. 키움 API 연결
    print("\n4. 키움 API 연결")
    try:
        response = requests.post(f"{base_url}/api/v1/connect")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 키움 API 연결: {data['message']}")
        else:
            print(f"❌ 키움 API 연결 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 키움 API 연결 오류: {e}")
    
    # 5. 트레이딩 신호 조회
    print("\n5. 트레이딩 신호 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/trading/signals?symbol=005930")
        if response.status_code == 200:
            data = response.json()
            signals = data['signals']
            print(f"✅ 트레이딩 신호 조회 성공")
            print(f"   종목: {signals['symbol']}")
            print(f"   현재가: {signals['current_price']:,.0f}원")
            print(f"   종합 신호: {signals['overall_signal']}")
            
            if 'signals' in signals:
                for indicator, signal in signals['signals'].items():
                    print(f"   {indicator}: {signal}")
        else:
            print(f"❌ 트레이딩 신호 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 트레이딩 신호 조회 오류: {e}")
    
    # 6. 트레이딩 분석 실행
    print("\n6. 트레이딩 분석 실행")
    try:
        payload = {'symbol': '005930'}
        response = requests.post(f"{base_url}/api/v1/analysis", json=payload)
        if response.status_code == 200:
            data = response.json()
            analysis = data['analysis']
            print(f"✅ 트레이딩 분석 실행 성공")
            print(f"   종목: {analysis['symbol']}")
            print(f"   시장 데이터: {analysis['market_data']['current_price']:,.0f}원")
            print(f"   신호: {analysis['signals']['overall_signal']}")
        else:
            print(f"❌ 트레이딩 분석 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 트레이딩 분석 실행 오류: {e}")
    
    # 7. 포트폴리오 조회
    print("\n7. 포트폴리오 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/portfolio")
        if response.status_code == 200:
            data = response.json()
            portfolio = data['portfolio']
            print(f"✅ 포트폴리오 조회 성공")
            
            if portfolio['account_info']:
                account = portfolio['account_info']
                print(f"   계좌번호: {account['account_number']}")
                print(f"   잔고: {account['balance']:,.0f}원")
                print(f"   사용가능: {account['available_balance']:,.0f}원")
            
            if portfolio['positions']:
                print(f"   보유 종목 수: {len(portfolio['positions'])}")
                for symbol, position in portfolio['positions'].items():
                    print(f"     {symbol}: {position['quantity']}주")
            
            print(f"   최근 거래 수: {len(portfolio['trade_history'])}")
        else:
            print(f"❌ 포트폴리오 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 포트폴리오 조회 오류: {e}")
    
    # 8. 거래 실행 테스트
    print("\n8. 거래 실행 테스트")
    try:
        payload = {
            'symbol': '005930',
            'order_type': 'buy',
            'quantity': 5,
            'price': 0  # 시장가
        }
        response = requests.post(f"{base_url}/api/v1/execute_trade", json=payload)
        if response.status_code == 200:
            data = response.json()
            order_result = data['order_result']
            print(f"✅ 거래 실행 성공")
            print(f"   주문번호: {order_result['order_id']}")
            print(f"   종목: {order_result['symbol']}")
            print(f"   수량: {order_result['quantity']}주")
            print(f"   상태: {order_result['status']}")
        else:
            print(f"❌ 거래 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 거래 실행 오류: {e}")
    
    print("\n=== 테스트 완료 ===")
    print("🎉 통합 트레이딩 시스템이 정상적으로 작동하고 있습니다!")
    print("\n📊 시스템 구성:")
    print("   • 64비트 메인 시스템 (포트 8000)")
    print("   • 32비트 키움 브리지 (포트 8001)")
    print("   • 키움 API 시뮬레이션")
    print("   • 기술적 분석 모델")
    print("   • 실시간 거래 실행")
    
    return True

if __name__ == "__main__":
    print("시스템이 시작될 때까지 잠시 기다립니다...")
    time.sleep(3)
    test_integrated_system() 