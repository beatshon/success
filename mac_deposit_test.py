#!/usr/bin/env python3
"""
맥용 예수금 조회 시뮬레이션 스크립트
Windows 환경이 아닌 경우에도 테스트할 수 있도록 시뮬레이션
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

class MacDepositSimulator:
    """맥에서 예수금 조회를 시뮬레이션하는 클래스"""
    
    def __init__(self):
        self.simulated_accounts = {
            "1234567890": {
                "account": "1234567890",
                "user_id": "test_user",
                "user_name": "테스트 사용자",
                "server_gubun": "모의투자",
                "deposit": 10000000,  # 1천만원
                "available_deposit": 9500000,  # 950만원
                "orderable_amount": 9000000,  # 900만원
                "timestamp": datetime.now()
            }
        }
        
        # 시뮬레이션된 종목 데이터
        self.simulated_stocks = {
            "005930": {"name": "삼성전자", "price": 70000},
            "000660": {"name": "SK하이닉스", "price": 120000},
            "035420": {"name": "NAVER", "price": 200000},
            "051910": {"name": "LG화학", "price": 500000},
            "006400": {"name": "삼성SDI", "price": 400000}
        }
    
    def get_account_info(self):
        """계좌 정보 조회 (시뮬레이션)"""
        print("📊 계좌 정보 조회 (시뮬레이션)")
        return self.simulated_accounts
    
    def get_deposit_info(self, account):
        """예수금 조회 (시뮬레이션)"""
        print(f"💰 예수금 조회 (시뮬레이션) - 계좌: {account}")
        
        if account in self.simulated_accounts:
            # 시뮬레이션된 지연
            time.sleep(1)
            
            deposit_info = self.simulated_accounts[account].copy()
            deposit_info['timestamp'] = datetime.now()
            
            print(f"  예수금: {deposit_info['deposit']:,}원")
            print(f"  출금가능: {deposit_info['available_deposit']:,}원")
            print(f"  주문가능: {deposit_info['orderable_amount']:,}원")
            
            return deposit_info
        else:
            print(f"  ❌ 계좌를 찾을 수 없습니다: {account}")
            return {}
    
    def get_stock_basic_info(self, code):
        """종목 기본 정보 조회 (시뮬레이션)"""
        if code in self.simulated_stocks:
            return {
                'code': code,
                'name': self.simulated_stocks[code]['name']
            }
        return {'code': code, 'name': '알 수 없음'}
    
    def get_current_price(self, code):
        """현재가 조회 (시뮬레이션)"""
        if code in self.simulated_stocks:
            # 시뮬레이션된 가격 변동
            import random
            price = self.simulated_stocks[code]['price']
            change_rate = random.uniform(-0.02, 0.02)  # -2% ~ +2%
            new_price = int(price * (1 + change_rate))
            
            return {
                'code': code,
                'name': self.simulated_stocks[code]['name'],
                'current_price': new_price,
                'volume': random.randint(1000, 10000),
                'timestamp': datetime.now()
            }
        return {}

def test_mac_deposit_simulation():
    """맥에서 예수금 조회 시뮬레이션 테스트"""
    print("🔄 맥용 예수금 조회 시뮬레이션 테스트 시작...")
    
    try:
        simulator = MacDepositSimulator()
        
        # 1. 계좌 정보 조회
        print("\n1️⃣ 계좌 정보 조회 테스트")
        account_info = simulator.get_account_info()
        print(f"   조회된 계좌 수: {len(account_info)}")
        
        for account, info in account_info.items():
            print(f"   계좌: {account} - {info['user_name']} ({info['server_gubun']})")
        
        # 2. 예수금 조회
        print("\n2️⃣ 예수금 조회 테스트")
        for account in account_info:
            deposit_info = simulator.get_deposit_info(account)
            if deposit_info:
                print(f"   ✅ 계좌 {account} 예수금 조회 성공")
            else:
                print(f"   ❌ 계좌 {account} 예수금 조회 실패")
        
        # 3. 종목 정보 조회
        print("\n3️⃣ 종목 정보 조회 테스트")
        test_codes = ["005930", "000660", "035420"]
        for code in test_codes:
            stock_info = simulator.get_stock_basic_info(code)
            print(f"   {code}: {stock_info['name']}")
        
        # 4. 현재가 조회
        print("\n4️⃣ 현재가 조회 테스트")
        for code in test_codes:
            price_info = simulator.get_current_price(code)
            if price_info:
                print(f"   {code} ({price_info['name']}): {price_info['current_price']:,}원")
        
        return True
        
    except Exception as e:
        print(f"❌ 시뮬레이션 테스트 중 오류: {e}")
        return False

def test_auto_trader_with_simulation():
    """시뮬레이션된 API로 자동매매 테스트"""
    print("\n🔄 시뮬레이션된 자동매매 테스트...")
    
    try:
        # Mock API 클래스 생성
        class MockKiwoomAPI:
            def __init__(self):
                self.simulator = MacDepositSimulator()
                self.login_status = True
            
            def login(self):
                print("✅ 로그인 성공 (시뮬레이션)")
                return True
            
            def get_account_info(self):
                return self.simulator.get_account_info()
            
            def get_deposit_info(self, account):
                return self.simulator.get_deposit_info(account)
            
            def get_stock_basic_info(self, code):
                return self.simulator.get_stock_basic_info(code)
            
            def get_current_price(self, code):
                return self.simulator.get_current_price(code)
            
            def order_stock(self, account, code, quantity, price, order_type):
                print(f"📈 주문 실행 (시뮬레이션): {order_type} - {code} {quantity}주 @ {price:,}원")
                return f"MOCK_ORDER_{int(time.time())}"
        
        # Mock API로 테스트
        mock_api = MockKiwoomAPI()
        
        # 계좌 정보 조회
        accounts = mock_api.get_account_info()
        if accounts:
            account = list(accounts.keys())[0]
            print(f"   사용 계좌: {account}")
            
            # 예수금 조회
            deposit_info = mock_api.get_deposit_info(account)
            if deposit_info:
                print(f"   예수금: {deposit_info['deposit']:,}원")
                print(f"   주문가능: {deposit_info['orderable_amount']:,}원")
            
            # 종목 조회
            stock_info = mock_api.get_stock_basic_info("005930")
            print(f"   종목: {stock_info['name']} ({stock_info['code']})")
            
            # 현재가 조회
            price_info = mock_api.get_current_price("005930")
            if price_info:
                print(f"   현재가: {price_info['current_price']:,}원")
        
        return True
        
    except Exception as e:
        print(f"❌ 자동매매 시뮬레이션 테스트 중 오류: {e}")
        return False

def generate_test_report():
    """테스트 리포트 생성"""
    print("\n📄 테스트 리포트 생성 중...")
    
    report_data = {
        'test_time': datetime.now().isoformat(),
        'platform': 'macOS',
        'python_version': sys.version,
        'tests': {
            'deposit_simulation': False,
            'auto_trader_simulation': False
        }
    }
    
    # 테스트 실행
    report_data['tests']['deposit_simulation'] = test_mac_deposit_simulation()
    report_data['tests']['auto_trader_simulation'] = test_auto_trader_with_simulation()
    
    # 리포트 저장
    os.makedirs('logs', exist_ok=True)
    report_file = f"logs/mac_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"📄 테스트 리포트 저장: {report_file}")
    
    return report_data, report_file

def main():
    """메인 테스트 함수"""
    print("🚀 맥용 예수금 조회 시뮬레이션 테스트")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"플랫폼: macOS")
    print(f"Python 버전: {sys.version}")
    print()
    
    # 테스트 실행
    report, report_file = generate_test_report()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in report['tests'].items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    success_count = sum(report['tests'].values())
    total_count = len(report['tests'])
    
    print(f"\n성공률: {success_count}/{total_count} ({(success_count/total_count)*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("맥에서도 예수금 조회 기능을 시뮬레이션할 수 있습니다.")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
    
    print(f"\n📄 상세 리포트: {report_file}")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 