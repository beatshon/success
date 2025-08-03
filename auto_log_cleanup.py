#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import schedule
import logging
from datetime import datetime
from log_cleanup import LogCleanupManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/auto_cleanup.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class AutoLogCleanupScheduler:
    """자동 로그 정리 스케줄러"""
    
    def __init__(self, retention_days=30, cleanup_time="02:00"):
        self.retention_days = retention_days
        self.cleanup_time = cleanup_time
        self.cleanup_manager = LogCleanupManager(retention_days=retention_days)
        self.running = False
        
    def cleanup_job(self):
        """정기 로그 정리 작업"""
        try:
            logging.info("🔄 자동 로그 정리 작업 시작")
            
            # 통계 출력
            stats = self.cleanup_manager.get_log_statistics()
            if stats:
                logging.info(f"정리 전 - 총 폴더: {stats['total_folders']}개, "
                           f"총 크기: {stats['total_size_mb']:.2f}MB, "
                           f"삭제 대상: {stats['folders_to_delete']}개")
            
            # 로그 정리 실행
            success = self.cleanup_manager.cleanup_logs(dry_run=False)
            
            if success:
                # 정리 후 통계
                stats_after = self.cleanup_manager.get_log_statistics()
                if stats_after:
                    logging.info(f"정리 후 - 총 폴더: {stats_after['total_folders']}개, "
                               f"총 크기: {stats_after['total_size_mb']:.2f}MB")
                
                logging.info("✅ 자동 로그 정리 작업 완료")
            else:
                logging.error("❌ 자동 로그 정리 작업 실패")
                
        except Exception as e:
            logging.error(f"자동 로그 정리 작업 중 오류: {e}")
    
    def daily_summary_job(self):
        """일일 요약 작업"""
        try:
            logging.info("📊 일일 요약 리포트 생성 시작")
            
            # 트레이더 인스턴스 생성 (간단한 버전)
            from cross_platform_trader import KiwoomAPI, RealtimeTrader
            
            api = KiwoomAPI()
            api.login()
            account_info = api.get_account_info()
            account = account_info["계좌번호"]
            
            trader = RealtimeTrader(api, account)
            trader.initialize()
            
            # 일일 요약 생성 및 전송
            trader.daily_summary()
            
            logging.info("✅ 일일 요약 리포트 전송 완료")
            
        except Exception as e:
            logging.error(f"일일 요약 작업 중 오류: {e}")
    
    def start_scheduler(self):
        """스케줄러 시작"""
        try:
            # 매일 지정된 시간에 로그 정리 실행
            schedule.every().day.at(self.cleanup_time).do(self.cleanup_job)
            
            # 매일 오후 6시에 일일 요약 전송
            schedule.every().day.at("18:00").do(self.daily_summary_job)
            
            # 매주 일요일 오전 3시에 주간 통계 출력
            schedule.every().sunday.at("03:00").do(self.weekly_report)
            
            logging.info(f"📅 자동 로그 정리 스케줄러 시작")
            logging.info(f"🕐 정리 시간: 매일 {self.cleanup_time}")
            logging.info(f"📊 일일 요약: 매일 18:00")
            logging.info(f"📈 주간 리포트: 매주 일요일 03:00")
            logging.info(f"📊 보관 기간: {self.retention_days}일")
            
            self.running = True
            
            # 스케줄러 루프
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
                
        except KeyboardInterrupt:
            logging.info("🛑 사용자에 의해 스케줄러 중지")
            self.stop_scheduler()
        except Exception as e:
            logging.error(f"스케줄러 실행 중 오류: {e}")
            self.stop_scheduler()
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        self.running = False
        logging.info("🛑 자동 로그 정리 스케줄러 중지")
    
    def weekly_report(self):
        """주간 로그 통계 리포트"""
        try:
            logging.info("📊 주간 로그 통계 리포트 생성")
            
            stats = self.cleanup_manager.get_log_statistics()
            if stats:
                report = f"""
📈 주간 로그 통계 리포트 ({datetime.now().strftime('%Y-%m-%d')})
{'='*50}
총 로그 폴더: {stats['total_folders']}개
총 크기: {stats['total_size_mb']:.2f}MB
최고 로그: {stats['oldest_log'].strftime('%Y-%m-%d') if stats['oldest_log'] else 'N/A'}
최신 로그: {stats['newest_log'].strftime('%Y-%m-%d') if stats['newest_log'] else 'N/A'}
삭제 대상: {stats['folders_to_delete']}개 폴더
절약 가능: {stats['size_to_free_mb']:.2f}MB
{'='*50}
"""
                logging.info(report)
                
                # 주간 리포트 파일 저장
                report_file = f"logs/weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
                os.makedirs(os.path.dirname(report_file), exist_ok=True)
                
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                logging.info(f"📄 주간 리포트 저장: {report_file}")
            
        except Exception as e:
            logging.error(f"주간 리포트 생성 중 오류: {e}")
    
    def run_once(self):
        """한 번만 실행"""
        logging.info("🚀 즉시 로그 정리 실행")
        self.cleanup_job()


def main():
    """메인 함수"""
    print("🤖 자동 로그 정리 스케줄러")
    print("=" * 60)
    
    # 설정
    retention_days = 30
    cleanup_time = "02:00"
    
    # 명령행 인수 처리
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--run-once":
            # 즉시 실행 모드
            scheduler = AutoLogCleanupScheduler(retention_days=retention_days)
            scheduler.run_once()
            return
        elif sys.argv[1].isdigit():
            retention_days = int(sys.argv[1])
        else:
            print("사용법:")
            print("  python auto_log_cleanup.py                    # 스케줄러 시작")
            print("  python auto_log_cleanup.py --run-once         # 즉시 실행")
            print("  python auto_log_cleanup.py 60                 # 60일 보관으로 스케줄러 시작")
            return
    
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        cleanup_time = f"{sys.argv[2]}:00"
    
    # 스케줄러 초기화
    scheduler = AutoLogCleanupScheduler(
        retention_days=retention_days,
        cleanup_time=cleanup_time
    )
    
    print(f"📅 보관 기간: {retention_days}일")
    print(f"🕐 정리 시간: 매일 {cleanup_time}")
    print(f"📊 주간 리포트: 매주 일요일 03:00")
    print(f"�� 일일 요약: 매일 18:00")
    print("\n스케줄러를 시작합니다... (Ctrl+C로 중지)")
    
    # 스케줄러 시작
    scheduler.start_scheduler()


if __name__ == "__main__":
    main() 