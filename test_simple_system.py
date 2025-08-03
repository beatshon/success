#!/usr/bin/env python3
"""
간단한 시스템 테스트
"""

import requests
import time
import json

def test_system():
    """시스템 테스트"""
    base_url = "http://localhost:8000"
    
    print("=== 간단한 고급 트레이딩 시스템 테스트 ===")
    
    # 1. 헬스 체크
    print("\n1. 헬스 체크 테스트")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 헬스 체크 성공")
            print(f"   상태: {data['status']}")
            print(f"   시스템: {data['system_info']['name']}")
            print(f"   버전: {data['system_info']['version']}")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
        return False
    
    # 2. 준비 상태 체크
    print("\n2. 준비 상태 체크")
    try:
        response = requests.get(f"{base_url}/ready", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 준비 상태 체크 성공")
            print(f"   준비 상태: {data['ready']}")
            print(f"   컴포넌트: {data['components']}")
        else:
            print(f"❌ 준비 상태 체크 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 준비 상태 체크 오류: {e}")
    
    # 3. 시스템 상태 조회
    print("\n3. 시스템 상태 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 시스템 상태 조회 성공")
            print(f"   실행 상태: {data['is_running']}")
            print(f"   모델 상태: {data['model_status']}")
        else:
            print(f"❌ 시스템 상태 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 상태 조회 오류: {e}")
    
    # 4. 트레이딩 신호 조회
    print("\n4. 트레이딩 신호 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/trading/signals?symbols=AAPL,GOOGL", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 트레이딩 신호 조회 성공")
            for symbol, signal in data['signals'].items():
                print(f"   {symbol}: {signal['signal']} (신뢰도: {signal['confidence']:.2%})")
        else:
            print(f"❌ 트레이딩 신호 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 트레이딩 신호 조회 오류: {e}")
    
    # 5. 포트폴리오 조회
    print("\n5. 포트폴리오 조회")
    try:
        response = requests.get(f"{base_url}/api/v1/portfolio", timeout=5)
        if response.status_code == 200:
            data = response.json()
            portfolio = data['portfolio']
            print(f"✅ 포트폴리오 조회 성공")
            print(f"   총 가치: {portfolio['total_value']:,.0f}원")
            print(f"   현재 자본: {portfolio['current_capital']:,.0f}원")
            print(f"   총 손익: {portfolio['total_pnl']:,.0f}원")
            print(f"   수익률: {portfolio['return_percentage']:.2f}%")
        else:
            print(f"❌ 포트폴리오 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 포트폴리오 조회 오류: {e}")
    
    # 6. 분석 실행
    print("\n6. 분석 실행")
    try:
        payload = {"symbols": ["AAPL", "GOOGL", "MSFT"]}
        response = requests.post(f"{base_url}/api/v1/analysis", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 분석 실행 성공")
            for symbol, analysis in data['analysis_results'].items():
                print(f"   {symbol}:")
                print(f"     감정: {analysis['sentiment']['sentiment']}")
                print(f"     트렌드: {analysis['indicators']['trend']}")
                print(f"     신호: {analysis['prediction']['signal']}")
        else:
            print(f"❌ 분석 실행 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 분석 실행 오류: {e}")
    
    print("\n=== 테스트 완료 ===")
    return True

if __name__ == "__main__":
    print("시스템이 시작될 때까지 잠시 기다립니다...")
    time.sleep(5)  # 시스템 시작 대기
    
    test_system() 