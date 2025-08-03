#!/usr/bin/env python3
"""
실제 키움 API 자동매매 시작
실제 키움 API를 연결하여 자동매매를 시작합니다.
"""
import time
import sys
from datetime import datetime
from auto_trading_system import AutoTradingSystem
from loguru import logger

def check_kiwoom_connection():
    """키움 API 연결 상태 확인"""
    print("🔌 키움 API 연결 상태 확인 중...")
    
    try:
        from pykiwoom.kiwoom import Kiwoom
        
        kiwoom = Kiwoom()
        connected = kiwoom.GetConnectState()
        
        if connected == 1:
            print("✅ 키움 API 연결 성공!")
            
            # 계좌 정보 조회
            account_no = kiwoom.GetLoginInfo("ACCNO")
            user_id = kiwoom.GetLoginInfo("USER_ID")
            user_name = kiwoom.GetLoginInfo("USER_NAME")
            
            print(f"📊 계좌번호: {account_no}")
            print(f"📊 사용자 ID: {user_id}")
            print(f"📊 사용자명: {user_name}")
            
            return True
        else:
            print("❌ 키움 API 연결 실패")
            print("💡 다음을 확인하세요:")
            print("   - 키움 영웅문이 실행되어 있는지")
            print("   - 로그인이 완료되었는지")
            print("   - RDP 세션이 활성화되어 있는지")
            return False
            
    except Exception as e:
        print(f"❌ 키움 API 연결 오류: {e}")
        return False

def start_real_auto_trading():
    """실제 자동매매 시작"""
    print("🚀 실제 키움 API 자동매매 시작")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 키움 API 연결 확인
    if not check_kiwoom_connection():
        print("\n❌ 키움 API 연결 실패로 자동매매를 시작할 수 없습니다.")
        print("💡 키움 영웅문을 실행하고 로그인한 후 다시 시도하세요.")
        return False
    
    # 2. 자동매매 시스템 생성 (실제 API 모드)
    print("\n📊 자동매매 시스템 초기화 중...")
    trading_system = AutoTradingSystem(use_real_api=True)
    
    print("📋 설정된 전략:")
    for name, strategy in trading_system.strategy_manager.strategies.items():
        print(f"  - {name}: {strategy.description}")
    
    # 3. 초기 계좌 상태 확인
    print("\n💰 초기 계좌 상태:")
    try:
        account_info = trading_system.trading_system.get_account_info()
        print(f"  - 현금 잔고: {account_info['cash_balance']:,}원")
        print(f"  - 총 자산: {account_info['total_value']:,}원")
        print(f"  - 보유 종목 수: {account_info['positions']}개")
    except Exception as e:
        print(f"  - 계좌 정보 조회 실패: {e}")
    
    # 4. 자동매매 시작
    print("\n🎯 자동매매 시작!")
    print("⚠️  주의사항:")
    print("   - 실제 거래가 실행됩니다")
    print("   - 중단하려면 Ctrl+C를 누르세요")
    print("   - 거래 간격: 5분")
    print("=" * 60)
    
    try:
        # 자동매매 시작 (5분 간격)
        trading_system.start_auto_trading(interval_minutes=5)
        
    except KeyboardInterrupt:
        print("\n⏹️  자동매매 중단 요청")
        trading_system.stop_auto_trading()
        
        # 최종 성능 리포트
        print("\n📊 최종 성능 리포트")
        trading_system._print_performance_report()
        
    except Exception as e:
        print(f"\n❌ 자동매매 오류: {e}")
        trading_system.stop_auto_trading()
        return False
    
    print("\n✅ 자동매매 완료!")
    return True

def main():
    """메인 함수"""
    print("🎯 키움 API 실제 자동매매 시스템")
    print("=" * 60)
    
    # 사용자 확인
    print("⚠️  실제 거래가 실행됩니다!")
    print("다음 사항을 확인하세요:")
    print("1. 키움 영웅문이 실행되어 있는지")
    print("2. 로그인이 완료되었는지")
    print("3. RDP 세션이 활성화되어 있는지")
    print("4. 모의투자 계좌인지 확인")
    
    response = input("\n자동매매를 시작하시겠습니까? (y/N): ")
    
    if response.lower() in ['y', 'yes', 'ㅇ']:
        success = start_real_auto_trading()
        if success:
            print("\n🎉 자동매매가 성공적으로 완료되었습니다!")
        else:
            print("\n❌ 자동매매 실행 중 오류가 발생했습니다.")
    else:
        print("\n❌ 자동매매가 취소되었습니다.")

if __name__ == "__main__":
    main() 