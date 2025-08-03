#!/usr/bin/env python3
"""
64비트 환경에서 키움 API 브리지와 통신하는 클라이언트
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KiwoomClient:
    """키움 API 클라이언트 (64비트 환경)"""
    
    def __init__(self, bridge_url: str = "http://localhost:8001"):
        self.bridge_url = bridge_url
        self.session = requests.Session()
        self.session.timeout = 10
        
        logger.info(f"키움 API 클라이언트 초기화: {bridge_url}")
    
    def check_bridge_health(self) -> bool:
        """브리지 서버 상태 확인"""
        try:
            response = self.session.get(f"{self.bridge_url}/health")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"브리지 서버 상태: {data['status']}")
                return data.get('kiwoom_connected', False)
            else:
                logger.error(f"브리지 서버 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"브리지 서버 연결 실패: {e}")
            return False
    
    def connect_kiwoom(self) -> bool:
        """키움 API 연결"""
        try:
            response = self.session.post(f"{self.bridge_url}/api/v1/connect")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"키움 API 연결: {data['message']}")
                return data.get('connected', False)
            else:
                logger.error(f"키움 API 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"키움 API 연결 오류: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """계좌 정보 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/account")
            if response.status_code == 200:
                data = response.json()
                return data.get('account_info')
            else:
                logger.error(f"계좌 정보 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"계좌 정보 조회 오류: {e}")
            return None
    
    def get_positions(self) -> Optional[Dict]:
        """보유 종목 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/positions")
            if response.status_code == 200:
                data = response.json()
                return data.get('positions')
            else:
                logger.error(f"보유 종목 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"보유 종목 조회 오류: {e}")
            return None
    
    def place_order(self, symbol: str, order_type: str, quantity: int, price: float = 0) -> Optional[Dict]:
        """주문 실행"""
        try:
            payload = {
                'symbol': symbol,
                'order_type': order_type,
                'quantity': quantity,
                'price': price
            }
            
            response = self.session.post(f"{self.bridge_url}/api/v1/order", json=payload)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"주문 실행 성공: {symbol} {order_type} {quantity}주")
                return data.get('order_result')
            else:
                logger.error(f"주문 실행 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"주문 실행 오류: {e}")
            return None
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """시장 데이터 조회"""
        try:
            response = self.session.get(f"{self.bridge_url}/api/v1/market_data", params={'symbol': symbol})
            if response.status_code == 200:
                data = response.json()
                return data.get('market_data')
            else:
                logger.error(f"시장 데이터 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            return None

def test_kiwoom_client():
    """키움 클라이언트 테스트"""
    print("=== 키움 API 클라이언트 테스트 ===")
    
    # 클라이언트 초기화
    client = KiwoomClient()
    
    # 1. 브리지 서버 상태 확인
    print("\n1. 브리지 서버 상태 확인")
    if client.check_bridge_health():
        print("✅ 브리지 서버 정상")
    else:
        print("❌ 브리지 서버 연결 실패")
        return False
    
    # 2. 키움 API 연결
    print("\n2. 키움 API 연결")
    if client.connect_kiwoom():
        print("✅ 키움 API 연결 성공")
    else:
        print("❌ 키움 API 연결 실패")
        return False
    
    # 3. 계좌 정보 조회
    print("\n3. 계좌 정보 조회")
    account_info = client.get_account_info()
    if account_info:
        print("✅ 계좌 정보 조회 성공")
        print(f"   계좌번호: {account_info['account_number']}")
        print(f"   잔고: {account_info['balance']:,.0f}원")
        print(f"   사용가능: {account_info['available_balance']:,.0f}원")
    else:
        print("❌ 계좌 정보 조회 실패")
    
    # 4. 보유 종목 조회
    print("\n4. 보유 종목 조회")
    positions = client.get_positions()
    if positions:
        print("✅ 보유 종목 조회 성공")
        print(f"   보유 종목 수: {len(positions)}")
    else:
        print("❌ 보유 종목 조회 실패")
    
    # 5. 시장 데이터 조회
    print("\n5. 시장 데이터 조회")
    market_data = client.get_market_data("005930")  # 삼성전자
    if market_data:
        print("✅ 시장 데이터 조회 성공")
        print(f"   종목: {market_data['symbol']}")
        print(f"   현재가: {market_data['current_price']:,.0f}원")
        print(f"   거래량: {market_data['volume']:,}")
    else:
        print("❌ 시장 데이터 조회 실패")
    
    # 6. 주문 실행 (시뮬레이션)
    print("\n6. 주문 실행 테스트")
    order_result = client.place_order("005930", "buy", 10, 70000)
    if order_result:
        print("✅ 주문 실행 성공")
        print(f"   주문번호: {order_result['order_id']}")
        print(f"   종목: {order_result['symbol']}")
        print(f"   수량: {order_result['quantity']}주")
    else:
        print("❌ 주문 실행 실패")
    
    print("\n=== 테스트 완료 ===")
    return True

if __name__ == "__main__":
    test_kiwoom_client() 