#!/usr/bin/env python3
"""
장 열림 시간 확인
현재 시간과 장 열림 시간을 확인합니다.
"""
from datetime import datetime, time

def check_market_status():
    """장 열림 상태 확인"""
    now = datetime.now()
    current_time = now.time()
    current_weekday = now.weekday()  # 0=월요일, 6=일요일
    
    print("📅 장 열림 시간 확인")
    print("=" * 50)
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"요일: {now.strftime('%A')}")
    print("=" * 50)
    
    # 주말 확인
    if current_weekday >= 5:  # 토요일(5) 또는 일요일(6)
        print("❌ 주말입니다. 장이 열리지 않습니다.")
        print("📅 다음 거래일: 월요일 09:00")
        return False
    
    # 정규장 시간 확인 (09:00-15:30)
    market_open = time(9, 0)
    market_close = time(15, 30)
    
    if market_open <= current_time <= market_close:
        print("✅ 정규장이 열려있습니다!")
        print(f"🕐 거래 시간: 09:00-15:30")
        print(f"⏰ 남은 시간: {market_close.hour - current_time.hour}시간 {market_close.minute - current_time.minute}분")
        return True
    else:
        print("❌ 정규장이 닫혀있습니다.")
        print(f"🕐 정규장 시간: 09:00-15:30")
        
        if current_time < market_open:
            print(f"📅 다음 거래일: {now.strftime('%A')} 09:00")
        else:
            print(f"📅 다음 거래일: {(now.replace(day=now.day+1) if current_weekday < 4 else now.replace(day=now.day+3)).strftime('%A')} 09:00")
        
        return False

def get_next_trading_day():
    """다음 거래일 계산"""
    now = datetime.now()
    current_weekday = now.weekday()
    
    if current_weekday < 5:  # 평일
        if now.time() >= time(15, 30):  # 장 마감 후
            days_to_add = 1 if current_weekday < 4 else 3  # 금요일이면 월요일까지
        else:
            days_to_add = 0  # 오늘 다시 열림
    else:  # 주말
        days_to_add = 2 if current_weekday == 5 else 1  # 토요일이면 월요일, 일요일이면 월요일
    
    next_trading_day = now.replace(day=now.day + days_to_add)
    return next_trading_day.strftime('%Y-%m-%d %A 09:00')

if __name__ == "__main__":
    is_market_open = check_market_status()
    
    print("\n💡 자동매매 실행 가능 여부:")
    if is_market_open:
        print("✅ 지금 자동매매를 실행할 수 있습니다!")
        print("🚀 python start_real_trading.py")
    else:
        print("❌ 지금은 자동매매를 실행할 수 없습니다.")
        print(f"📅 다음 거래일: {get_next_trading_day()}")
        print("\n🔧 대안:")
        print("1. 모의 거래 테스트 실행")
        print("2. 전략 백테스팅 실행")
        print("3. 시스템 설정 점검") 