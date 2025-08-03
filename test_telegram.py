#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

class TelegramTester:
    """텔레그램 알림 테스트 클래스"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        
    def send_test_message(self, message: str) -> bool:
        """테스트 메시지 전송"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"✅ 텔레그램 메시지 전송 성공: {message[:50]}...")
                return True
            else:
                logging.error(f"❌ 텔레그램 메시지 전송 실패: {response.status_code}")
                logging.error(f"응답: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ 텔레그램 메시지 전송 오류: {e}")
            return False
    
    def test_trade_notification(self):
        """매매 알림 테스트"""
        message = f"🟢 [매수] 005930.KS 10주 @ 126,018원 | 예수금 8,739,820원"
        
        return self.send_test_message(message)
    
    def test_error_notification(self):
        """오류 알림 테스트"""
        message = f"⚠️ [비상정지] 이유: API 연결 오류"
        
        return self.send_test_message(message)
    
    def test_system_start(self):
        """시스템 시작 알림 테스트"""
        message = f"🚀 [시스템시작] 크로스 플랫폼 트레이딩 시스템\n환경: Mac (Mock API)\n계좌: 1234567890\n초기자금: 10,000,000원"
        
        return self.send_test_message(message)

    def test_emergency_report(self):
        """비상정지 리포트 테스트"""
        message = f"🚨 비상정지 리포트\n"
        message += f"총자산: 10,000,000원\n"
        message += f"예수금: 9,507,754원\n"
        message += f"보유종목: 1개\n"
        message += f"\n보유종목 상세:\n"
        message += f"• 005930.KS: 6주 @ 82,041원 (+0.00%)"
        
        return self.send_test_message(message)

    def test_daily_summary(self):
        """일일 요약 테스트"""
        message = f"📊 2025-08-03 매매 요약\n"
        message += f"🟢 매수: 2건, 총 1,351,360원\n"
        message += f"🔴 매도: 없음\n"
        message += f"⚠️ 오류: 없음\n"
        message += f"💰 현재 예수금: 8,121,175원\n"
        message += f"📈 보유종목: 2개"
        
        return self.send_test_message(message)

def main():
    """메인 함수"""
    print("=" * 60)
    print("📱 텔레그램 알림 테스트")
    print("=" * 60)
    
    # 텔레그램 설정 (실제 사용 시 입력)
    token = input("텔레그램 봇 토큰을 입력하세요 (테스트 시 Enter): ").strip()
    chat_id = input("채팅 ID를 입력하세요 (테스트 시 Enter): ").strip()
    
    if not token or not chat_id:
        print("\n⚠️  토큰 또는 채팅 ID가 없어 테스트를 건너뜁니다.")
        print("실제 사용 시:")
        print("1. @BotFather에서 봇 생성 후 토큰 획득")
        print("2. 봇과 대화 시작 후 @userinfobot에서 채팅 ID 확인")
        print("3. cross_platform_trader.py에서 TELEGRAM_ENABLED = True 설정")
        return
    
    tester = TelegramTester(token, chat_id)
    
    print(f"\n🔧 설정 정보:")
    print(f"토큰: {token[:10]}...")
    print(f"채팅 ID: {chat_id}")
    
    print(f"\n🧪 테스트 시작...")
    
    # 1. 시스템 시작 알림 테스트
    print("\n1️⃣ 시스템 시작 알림 테스트")
    if tester.test_system_start():
        print("✅ 성공")
    else:
        print("❌ 실패")
    
    # 2. 매매 알림 테스트
    print("\n2️⃣ 매매 알림 테스트")
    if tester.test_trade_notification():
        print("✅ 성공")
    else:
        print("❌ 실패")
    
    # 3. 오류 알림 테스트
    print("\n3️⃣ 오류 알림 테스트")
    if tester.test_error_notification():
        print("✅ 성공")
    else:
        print("❌ 실패")
    
    # 4. 비상정지 리포트 테스트
    print("\n4️⃣ 비상정지 리포트 테스트")
    if tester.test_emergency_report():
        print("✅ 성공")
    else:
        print("❌ 실패")
    
    # 5. 일일 요약 테스트
    print("\n5️⃣ 일일 요약 테스트")
    if tester.test_daily_summary():
        print("✅ 성공")
    else:
        print("❌ 실패")
    
    print(f"\n🎉 테스트 완료!")
    print(f"텔레그램에서 메시지를 확인하세요.")

if __name__ == "__main__":
    main() 