#!/usr/bin/env python3
"""
키움 REST API 연결 테스트
ActiveX 컨트롤 없이 HTTP 요청으로 API 테스트
"""
import requests
import json
import time
from datetime import datetime
import config

def test_rest_api_connection():
    """키움 REST API 연결 테스트"""
    print("🚀 키움 REST API 연결 테스트")
    print("=" * 50)
    
    # API 설정
    app_key = config.KIWOOM_CONFIG['app_key']
    app_secret = config.KIWOOM_CONFIG['app_secret']
    
    print(f"📋 API 키: {app_key[:10]}...")
    print(f"📋 API 시크릿: {app_secret[:10]}...")
    
    # 1. 액세스 토큰 발급 테스트
    print("\n1️⃣ 액세스 토큰 발급 시도...")
    try:
        token_url = "https://openapi.kiwoom.com/oauth2/tokenP"
        token_data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 내용: {response.text[:200]}...")
        
        if response.status_code == 200:
            token_info = response.json()
            print("✅ 액세스 토큰 발급 성공!")
            print(f"📋 토큰 타입: {token_info.get('token_type', 'N/A')}")
            print(f"📋 만료 시간: {token_info.get('expires_in', 'N/A')}초")
            return True
        else:
            print("❌ 액세스 토큰 발급 실패")
            return False
            
    except Exception as e:
        print(f"❌ 토큰 발급 중 오류: {e}")
        return False

def test_stock_info():
    """주식 정보 조회 테스트"""
    print("\n2️⃣ 주식 정보 조회 테스트...")
    try:
        # 삼성전자 정보 조회
        stock_url = "https://openapi.kiwoom.com/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {config.KIWOOM_CONFIG['app_key']}",
            "appkey": config.KIWOOM_CONFIG['app_key'],
            "appsecret": config.KIWOOM_CONFIG['app_secret'],
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930"
        }
        
        response = requests.get(stock_url, headers=headers, params=params, timeout=10)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 내용: {response.text[:300]}...")
        
        if response.status_code == 200:
            print("✅ 주식 정보 조회 성공!")
            return True
        else:
            print("❌ 주식 정보 조회 실패")
            return False
            
    except Exception as e:
        print(f"❌ 주식 정보 조회 중 오류: {e}")
        return False

def test_account_info():
    """계좌 정보 조회 테스트"""
    print("\n3️⃣ 계좌 정보 조회 테스트...")
    try:
        account_url = "https://openapi.kiwoom.com/uapi/domestic-stock/v1/trading-inquire/balance"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {config.KIWOOM_CONFIG['app_key']}",
            "appkey": config.KIWOOM_CONFIG['app_key'],
            "appsecret": config.KIWOOM_CONFIG['app_secret'],
            "tr_id": "TTTC8434R"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "2",
            "FID_INPUT_ISCD": "",
            "FID_DT_CLOSE_CODE": "1",
            "FID_COND_MRKT_DIV_CODE": "J"
        }
        
        response = requests.get(account_url, headers=headers, params=params, timeout=10)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 내용: {response.text[:300]}...")
        
        if response.status_code == 200:
            print("✅ 계좌 정보 조회 성공!")
            return True
        else:
            print("❌ 계좌 정보 조회 실패")
            return False
            
    except Exception as e:
        print(f"❌ 계좌 정보 조회 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🔍 키움 REST API 종합 테스트 시작")
    print("=" * 60)
    
    # 1. 액세스 토큰 테스트
    token_success = test_rest_api_connection()
    
    if token_success:
        # 2. 주식 정보 조회 테스트
        stock_success = test_stock_info()
        
        # 3. 계좌 정보 조회 테스트
        account_success = test_account_info()
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약:")
        print(f"✅ 액세스 토큰: {'성공' if token_success else '실패'}")
        print(f"✅ 주식 정보 조회: {'성공' if stock_success else '실패'}")
        print(f"✅ 계좌 정보 조회: {'성공' if account_success else '실패'}")
        
        if token_success and stock_success and account_success:
            print("\n🎉 모든 테스트 성공! REST API 연동 완료!")
        else:
            print("\n⚠️ 일부 테스트 실패. 추가 설정이 필요할 수 있습니다.")
    else:
        print("\n❌ 액세스 토큰 발급 실패. API 키 설정을 확인해주세요.")

if __name__ == "__main__":
    main() 