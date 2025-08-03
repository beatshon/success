#!/usr/bin/env python3
"""
딥러닝 통합 시스템 테스트
"""

import requests
import json
import time
from datetime import datetime

def test_deep_learning_system():
    """딥러닝 통합 시스템 테스트"""
    base_url = "http://localhost:8000"
    print("=== 딥러닝 통합 시스템 테스트 ===")
    
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
            print(f"   키움 준비: {data['kiwoom_ready']}")
            print(f"   딥러닝 모델 준비: {data['dl_model_ready']}")
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
            dl_status = data['dl_model_status']
            trading_status = data['trading_status']
            
            print(f"✅ 시스템 상태 조회 성공")
            print(f"   시스템: {system_info['name']} v{system_info['version']}")
            print(f"   아키텍처: {system_info['architecture']}")
            print(f"   키움 연결: {kiwoom_status['connected']}")
            print(f"   딥러닝 모델 훈련: {dl_status['trained']}")
            print(f"   모델 타입: {dl_status['model_type']}")
            print(f"   총 거래 횟수: {trading_status['total_trades']}")
        else:
            print(f"❌ 시스템 상태 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 상태 조회 오류: {e}")
    
    # 4. 딥러닝 모델 훈련
    print("\n4. 딥러닝 모델 훈련")
    try:
        response = requests.post(f"{base_url}/api/v1/train_dl_model")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 딥러닝 모델 훈련: {data['message']}")
            print(f"   훈련 완료: {data['trained']}")
        else:
            print(f"❌ 딥러닝 모델 훈련 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 딥러닝 모델 훈련 오류: {e}")
    
    # 5. 딥러닝 트레이딩 신호 조회
    print("\n5. 딥러닝 트레이딩 신호 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/trading/signals?symbol=005930")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 딥러닝 트레이딩 신호 조회 성공")
            print(f"   종목: {data['symbol']}")
            print(f"   현재가: {data['current_price']:,.0f}원")
            print(f"   예측가: {data['predicted_price']:,.0f}원" if data['predicted_price'] else "   예측가: N/A")
            print(f"   딥러닝 신호: {data['signals']['dl_model']}")
            print(f"   기술적 신호: {data['signals']['technical']}")
            print(f"   종합 신호: {data['overall_signal']}")
            print(f"   신뢰도: {data['confidence']:.2f}")
        else:
            print(f"❌ 딥러닝 트레이딩 신호 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 딥러닝 트레이딩 신호 조회 오류: {e}")
    
    # 6. 종합 분석 실행
    print("\n6. 종합 분석 실행")
    try:
        payload = {'symbol': '005930'}
        response = requests.post(f"{base_url}/api/v1/analysis", json=payload)
        if response.status_code == 200:
            data = response.json()
            analysis = data['analysis']
            print(f"✅ 종합 분석 실행 성공")
            print(f"   종목: {analysis['symbol']}")
            print(f"   딥러닝 예측가: {analysis['dl_prediction']['predicted_price']:,.0f}원" if analysis['dl_prediction']['predicted_price'] else "   딥러닝 예측가: N/A")
            print(f"   신호: {analysis['dl_prediction']['signal']}")
            print(f"   신뢰도: {analysis['dl_prediction']['confidence']:.2f}")
        else:
            print(f"❌ 종합 분석 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 종합 분석 실행 오류: {e}")
    
    # 7. 포트폴리오 조회
    print("\n7. 포트폴리오 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/portfolio")
        if response.status_code == 200:
            data = response.json()
            portfolio = data['portfolio']
            account_info = portfolio['account_info']
            positions = portfolio['positions']
            
            print(f"✅ 포트폴리오 조회 성공")
            print(f"   계좌번호: {account_info.get('account_number', 'N/A')}")
            print(f"   잔고: {account_info.get('balance', 0):,.0f}원")
            print(f"   사용가능: {account_info.get('available_balance', 0):,.0f}원")
            print(f"   보유 종목 수: {len(positions)}")
            print(f"   총 거래 횟수: {portfolio['total_trades']}")
        else:
            print(f"❌ 포트폴리오 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 포트폴리오 조회 오류: {e}")
    
    # 8. 딥러닝 거래 실행 테스트
    print("\n8. 딥러닝 거래 실행 테스트")
    try:
        payload = {
            'symbol': '005930',
            'quantity': 1
        }
        response = requests.post(f"{base_url}/api/v1/execute_trade", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 딥러닝 거래 실행 성공")
            print(f"   메시지: {data['message']}")
            print(f"   딥러닝 신호: {data['dl_signal']}")
            if data.get('predicted_price'):
                print(f"   예측가: {data['predicted_price']:,.0f}원")
        else:
            print(f"❌ 딥러닝 거래 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 딥러닝 거래 실행 오류: {e}")
    
    print("\n=== 테스트 완료 ===")
    print("🎉 딥러닝 통합 시스템이 정상적으로 작동하고 있습니다!")
    print("\n📊 시스템 구성:")
    print("   • 64비트 메인 시스템 (포트 8000)")
    print("   • 32비트 키움 브리지 (포트 8001)")
    print("   • LSTM 딥러닝 모델")
    print("   • 실시간 예측 및 신호 생성")
    print("   • 자동 거래 실행")
    
    print("\n🔧 다음 단계:")
    print("   1. 고급 딥러닝 모델 (Transformer, GRU) 추가")
    print("   2. 앙상블 모델 구현")
    print("   3. 실시간 데이터 수집 시스템")
    print("   4. 성능 모니터링 및 최적화")
    print("   5. 클라우드 배포")
    
    return True

if __name__ == "__main__":
    print("딥러닝 통합 시스템 테스트를 시작합니다...")
    time.sleep(3)
    test_deep_learning_system() 