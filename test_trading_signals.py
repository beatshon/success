#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매매 신호 테스트 스크립트
자동 매매 시스템이 신호를 감지하는지 테스트
"""

import time
import sqlite3
from datetime import datetime
from auto_trading_system import AutoTradingSystem
from day_trading_config import DayTradingConfig

def test_trading_signals():
    """매매 신호 테스트"""
    print("🧪 매매 신호 테스트 시작")
    print("=" * 50)
    
    try:
        # 자동 매매 시스템 초기화
        trading_system = AutoTradingSystem()
        
        # 자동 매매 시작
        print("1. 자동 매매 시스템 시작...")
        trading_system.start_auto_trading()
        
        # 상태 확인
        print("2. 시스템 상태 확인...")
        status = trading_system.get_trading_status()
        print(f"   - 실행 중: {status.get('is_running', False)}")
        print(f"   - 매매 활성화: {status.get('is_trading_enabled', False)}")
        print(f"   - 일일 손익: {status.get('daily_pnl', 0):,.0f}원")
        print(f"   - 거래 횟수: {status.get('daily_trades', 0)}회")
        
        # 매매 신호 확인
        print("3. 매매 신호 확인...")
        signals = trading_system.analyzer.get_all_signals()
        print(f"   - 감지된 신호 수: {len(signals)}")
        
        for stock_code, signal in signals.items():
            print(f"   - {signal.stock_name} ({stock_code}): {signal.signal_strength.value}")
            print(f"     신뢰도: {signal.confidence_score:.2f}")
            print(f"     목표가: {signal.price_target:,.0f}원")
        
        # 포지션 확인
        print("4. 현재 포지션 확인...")
        positions = trading_system.get_positions()
        print(f"   - 포지션 수: {len(positions)}")
        
        # 주문 이력 확인
        print("5. 주문 이력 확인...")
        history = trading_system.get_order_history()
        print(f"   - 주문 이력 수: {len(history)}")
        
        print("=" * 50)
        print("✅ 테스트 완료")
        print("💡 자동 매매가 활성화되었습니다.")
        print("🌐 브라우저에서 http://localhost:8087 접속하여 대시보드 확인")
        
        # 30초간 대기 (모니터링 확인용)
        print("⏳ 30초간 모니터링 중...")
        for i in range(30, 0, -1):
            print(f"   {i}초 남음...", end='\r')
            time.sleep(1)
        
        print("\n🏁 테스트 종료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def create_test_signals():
    """테스트용 매매 신호 생성"""
    print("🔧 테스트용 매매 신호 생성")
    
    try:
        # 데이터베이스에 테스트 신호 삽입
        conn = sqlite3.connect('auto_trading.db')
        cursor = conn.cursor()
        
        # 테스트 주문 삽입
        test_orders = [
            ('TEST_BUY_001', '005930', 'buy', 80000, 100, 'executed', datetime.now().isoformat()),
            ('TEST_SELL_001', '000660', 'sell', 170000, 50, 'executed', datetime.now().isoformat()),
        ]
        
        for order in test_orders:
            cursor.execute('''
                INSERT OR REPLACE INTO orders 
                (order_id, stock_code, order_type, price, quantity, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', order)
            
            cursor.execute('''
                INSERT INTO trade_history 
                (stock_code, order_type, price, quantity, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (order[1], order[2], order[3], order[4], order[6]))
        
        conn.commit()
        conn.close()
        
        print("✅ 테스트 신호 생성 완료")
        
    except Exception as e:
        print(f"❌ 테스트 신호 생성 실패: {e}")

if __name__ == "__main__":
    print("매매 신호 테스트를 선택하세요:")
    print("1. 자동 매매 시스템 테스트")
    print("2. 테스트 신호 생성")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        test_trading_signals()
    elif choice == "2":
        create_test_signals()
    else:
        print("잘못된 선택입니다.") 