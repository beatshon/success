#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
import os
import sys
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# 텔레그램 설정 (cross_platform_trader.py에서 가져옴)
TELEGRAM_TOKEN = "7836338625:AAGYUMdBZF2gkqa2gEiVMkOVB-Ex1_wiZfM"
TELEGRAM_CHAT_ID = "8461829055"
TELEGRAM_ENABLED = True

def send_telegram_message(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_ENABLED:
        logging.info(f"[텔레그램] {message}")
        return True
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            logging.info("텔레그램 메시지 전송 성공")
            return True
        else:
            logging.error(f"텔레그램 전송 실패: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"텔레그램 전송 중 오류: {e}")
        return False

def send_daily_summary(date_str=None):
    """일일 매매 요약 리포트 생성 및 전송"""
    try:
        # 날짜 설정
        if date_str:
            today = date_str
        else:
            today = datetime.now().strftime("%Y-%m-%d")
        
        folder = f"logs/{today}"
        
        # 로그 폴더가 없으면 매매 내역 없음 메시지 전송
        if not os.path.exists(folder):
            send_telegram_message(f"📊 {today} 매매 내역 없음")
            logging.info(f"{today} 매매 내역 없음 - 일일 요약 전송 완료")
            return True

        summary_msg = [f"📊 {today} 매매 요약"]

        # 매수 로그
        buy_file = os.path.join(folder, "buy_log.csv")
        if os.path.exists(buy_file):
            buy_df = pd.read_csv(buy_file)
            summary_msg.append(f"🟢 매수: {len(buy_df)}건, 총 {buy_df['총액'].sum():,}원")
        else:
            summary_msg.append("🟢 매수: 없음")

        # 매도 로그
        sell_file = os.path.join(folder, "sell_log.csv")
        if os.path.exists(sell_file):
            sell_df = pd.read_csv(sell_file)
            if not sell_df.empty:
                avg_profit = sell_df['수익률'].mean()
                summary_msg.append(f"🔴 매도: {len(sell_df)}건, 평균 수익률 {avg_profit:.2f}%")
            else:
                summary_msg.append("🔴 매도: 없음")
        else:
            summary_msg.append("🔴 매도: 없음")

        # 오류 로그
        error_file = os.path.join(folder, "error_log.csv")
        if os.path.exists(error_file):
            error_df = pd.read_csv(error_file)
            summary_msg.append(f"⚠️ 오류: {len(error_df)}건 발생")
        else:
            summary_msg.append("⚠️ 오류: 없음")

        # 텔레그램 전송
        final_message = "\n".join(summary_msg)
        success = send_telegram_message(final_message)
        
        if success:
            logging.info(f"{today} 일일 요약 리포트 전송 완료")
        else:
            logging.error(f"{today} 일일 요약 리포트 전송 실패")
        
        return success
        
    except Exception as e:
        logging.error(f"일일 요약 리포트 생성 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("📊 독립 실행 일일 요약 리포트")
    print("=" * 50)
    
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        print(f"지정된 날짜: {date_str}")
    else:
        date_str = None
        print(f"오늘 날짜: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 텔레그램 설정 확인
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("⚠️ 텔레그램 토큰이 설정되지 않았습니다.")
        print("TELEGRAM_TOKEN과 TELEGRAM_CHAT_ID를 설정하세요.")
        return
    
    # 일일 요약 실행
    print("\n일일 요약 리포트를 생성하고 전송합니다...")
    success = send_daily_summary(date_str)
    
    if success:
        print("✅ 일일 요약 리포트 전송 완료!")
    else:
        print("❌ 일일 요약 리포트 전송 실패")

if __name__ == "__main__":
    main() 