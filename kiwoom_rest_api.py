#!/usr/bin/env python3
"""
키움증권 REST API 연동 (ActiveX 대안)
"""

import requests
import json
import time
from datetime import datetime
from loguru import logger

class KiwoomRESTAPI:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://openapi.kiwoom.com"
        self.access_token = None
        
    def get_access_token(self):
        """액세스 토큰 발급"""
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            headers = {
                "content-type": "application/json"
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                logger.info("액세스 토큰 발급 성공")
                return True
            else:
                logger.error(f"액세스 토큰 발급 실패: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"액세스 토큰 발급 오류: {e}")
            return False
    
    def get_stock_price(self, stock_code):
        """주식 현재가 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appKey": self.app_key,
                "appSecret": self.app_secret,
                "tr_id": "FHKST01010100"
            }
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    output = result.get("output", {})
                    return {
                        "code": stock_code,
                        "name": output.get("hts_kor_isnm", ""),
                        "current_price": int(output.get("stck_prpr", 0)),
                        "change": int(output.get("prdy_vrss", 0)),
                        "change_rate": float(output.get("prdy_ctrt", 0)),
                        "volume": int(output.get("acml_vol", 0))
                    }
                else:
                    logger.error(f"주식 가격 조회 실패: {result.get('msg1')}")
                    return None
            else:
                logger.error(f"주식 가격 조회 오류: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"주식 가격 조회 오류: {e}")
            return None
    
    def get_account_info(self):
        """계좌 정보 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading-inquire/balance"
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appKey": self.app_key,
                "appSecret": self.app_secret,
                "tr_id": "TTTC8434R"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    return result.get("output", {})
                else:
                    logger.error(f"계좌 정보 조회 실패: {result.get('msg1')}")
                    return None
            else:
                logger.error(f"계좌 정보 조회 오류: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"계좌 정보 조회 오류: {e}")
            return None

def test_rest_api():
    """REST API 테스트"""
    print("=" * 50)
    print("키움증권 REST API 테스트")
    print("=" * 50)
    
    try:
        # 설정에서 API 키 가져오기
        from config import KIWOOM_CONFIG
        
        api = KiwoomRESTAPI(
            KIWOOM_CONFIG['app_key'],
            KIWOOM_CONFIG['app_secret']
        )
        
        # 액세스 토큰 발급 테스트
        print("🔐 액세스 토큰 발급 테스트...")
        if api.get_access_token():
            print("✅ 액세스 토큰 발급 성공")
            
            # 주식 가격 조회 테스트
            print("\n📊 주식 가격 조회 테스트...")
            test_codes = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
            
            for code in test_codes:
                print(f"\n   {code} 조회 중...")
                stock_info = api.get_stock_price(code)
                if stock_info:
                    print(f"   ✅ {stock_info['name']}: {stock_info['current_price']:,}원 ({stock_info['change_rate']:+.2f}%)")
                else:
                    print(f"   ❌ {code} 조회 실패")
                time.sleep(1)  # API 제한 고려
            
            print("\n" + "=" * 50)
            print("🎉 REST API 테스트 완료!")
            print("=" * 50)
            
        else:
            print("❌ 액세스 토큰 발급 실패")
            
    except Exception as e:
        print(f"❌ REST API 테스트 오류: {e}")

if __name__ == "__main__":
    test_rest_api() 