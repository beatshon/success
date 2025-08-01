#!/usr/bin/env python3
"""
Windows API 서버 서비스 스크립트
백그라운드에서 실행되며 자동 재시작 기능 포함
"""

import sys
import os
import time
import subprocess
import signal
import threading
from datetime import datetime
from loguru import logger

# 로그 설정
logger.add("logs/windows_server_service.log", rotation="1 day", retention="7 days")

class WindowsServerService:
    """Windows API 서버 서비스 클래스"""
    
    def __init__(self):
        self.server_process = None
        self.is_running = False
        self.restart_count = 0
        self.max_restarts = 5
        
    def start_server(self):
        """서버 시작"""
        try:
            logger.info("🚀 Windows API 서버 시작")
            
            # 서버 프로세스 시작
            self.server_process = subprocess.Popen([
                sys.executable, "windows_api_server.py",
                "--host", "0.0.0.0",
                "--port", "8080"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.is_running = True
            logger.info(f"✅ 서버 프로세스 시작됨 (PID: {self.server_process.pid})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 서버 시작 실패: {e}")
            return False
    
    def stop_server(self):
        """서버 중지"""
        try:
            if self.server_process:
                logger.info("🛑 서버 중지 중...")
                
                # 프로세스 종료
                self.server_process.terminate()
                
                # 5초 대기 후 강제 종료
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ 프로세스 강제 종료")
                    self.server_process.kill()
                
                self.is_running = False
                logger.info("✅ 서버 중지 완료")
                
        except Exception as e:
            logger.error(f"❌ 서버 중지 실패: {e}")
    
    def restart_server(self):
        """서버 재시작"""
        try:
            logger.info("🔄 서버 재시작 중...")
            
            self.stop_server()
            time.sleep(2)  # 2초 대기
            
            if self.start_server():
                self.restart_count += 1
                logger.info(f"✅ 서버 재시작 완료 (재시작 횟수: {self.restart_count})")
            else:
                logger.error("❌ 서버 재시작 실패")
                
        except Exception as e:
            logger.error(f"❌ 서버 재시작 오류: {e}")
    
    def monitor_server(self):
        """서버 모니터링"""
        try:
            while self.is_running and self.server_process:
                # 프로세스 상태 확인
                if self.server_process.poll() is not None:
                    logger.warning("⚠️ 서버 프로세스가 종료됨")
                    
                    if self.restart_count < self.max_restarts:
                        logger.info("🔄 자동 재시작 시도...")
                        self.restart_server()
                    else:
                        logger.error(f"❌ 최대 재시작 횟수 초과 ({self.max_restarts}회)")
                        break
                
                time.sleep(5)  # 5초마다 확인
                
        except Exception as e:
            logger.error(f"❌ 서버 모니터링 오류: {e}")
    
    def health_check(self):
        """헬스 체크"""
        try:
            import requests
            
            response = requests.get("http://localhost:8080/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ 서버 헬스 체크 성공")
                return True
            else:
                logger.warning(f"⚠️ 서버 헬스 체크 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 서버 헬스 체크 오류: {e}")
            return False
    
    def run(self):
        """서비스 실행"""
        try:
            logger.info("🔄 Windows API 서버 서비스 시작")
            
            # 서버 시작
            if not self.start_server():
                logger.error("❌ 서버 시작 실패")
                return False
            
            # 모니터링 스레드 시작
            monitor_thread = threading.Thread(target=self.monitor_server, daemon=True)
            monitor_thread.start()
            
            # 헬스 체크 스레드 시작
            def health_check_loop():
                while self.is_running:
                    self.health_check()
                    time.sleep(30)  # 30초마다 헬스 체크
            
            health_thread = threading.Thread(target=health_check_loop, daemon=True)
            health_thread.start()
            
            # 메인 루프
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단됨")
            
            # 서버 중지
            self.stop_server()
            logger.info("✅ 서비스 종료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 서비스 실행 오류: {e}")
            return False

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Windows API 서버 서비스")
    parser.add_argument("--start", action="store_true", help="서비스 시작")
    parser.add_argument("--stop", action="store_true", help="서비스 중지")
    parser.add_argument("--restart", action="store_true", help="서비스 재시작")
    parser.add_argument("--status", action="store_true", help="서비스 상태 확인")
    
    args = parser.parse_args()
    
    service = WindowsServerService()
    
    if args.start:
        service.run()
    elif args.stop:
        service.stop_server()
    elif args.restart:
        service.restart_server()
    elif args.status:
        if service.is_running:
            print("✅ 서비스 실행 중")
        else:
            print("❌ 서비스 중지됨")
    else:
        # 기본적으로 서비스 시작
        service.run()

if __name__ == "__main__":
    main() 