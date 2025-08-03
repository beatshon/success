#!/usr/bin/env python3
"""
Windows 동기화 서비스
백그라운드에서 자동으로 맥과 동기화를 수행
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import win32serviceutil
import win32service
import win32event
import servicemanager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WindowsSyncService(win32serviceutil.ServiceFramework):
    _svc_name_ = "KiwoomSyncService"
    _svc_display_name_ = "Kiwoom Trading Sync Service"
    _svc_description_ = "맥과 윈도우 서버 간 자동 동기화 서비스"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False
        
    def SvcStop(self):
        """서비스 중지"""
        logger.info("🛑 서비스 중지 요청")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
    def SvcDoRun(self):
        """서비스 실행"""
        logger.info("🚀 동기화 서비스 시작")
        self.running = True
        self.main()
        
    def load_config(self):
        """설정 파일 로드"""
        config_path = Path('config/windows_server.conf')
        if not config_path.exists():
            logger.error("설정 파일이 없습니다")
            return {}
            
        config = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        return config
    
    def check_git_updates(self):
        """GitHub 업데이트 확인"""
        try:
            # Git 상태 확인
            result = subprocess.run(['git', 'fetch', 'origin'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                # 변경사항 확인
                status_result = subprocess.run(['git', 'status', '-uno'], 
                                             capture_output=True, text=True, cwd=os.getcwd())
                
                if 'behind' in status_result.stdout:
                    logger.info("📥 새로운 변경사항 발견!")
                    
                    # Pull 실행
                    pull_result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                                               capture_output=True, text=True, cwd=os.getcwd())
                    
                    if pull_result.returncode == 0:
                        logger.info("✅ GitHub 업데이트 완료")
                        return True
                    else:
                        logger.error(f"❌ GitHub 업데이트 실패: {pull_result.stderr}")
                else:
                    logger.debug("✅ 최신 상태입니다")
            else:
                logger.error(f"❌ Git fetch 실패: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ GitHub 확인 오류: {e}")
        
        return False
    
    def restart_services(self):
        """서비스 재시작"""
        try:
            # Windows API 서버 재시작
            server_script = Path('windows_api_server.py')
            if server_script.exists():
                # 기존 프로세스 종료
                subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                             capture_output=True, check=False)
                time.sleep(2)
                
                # 새 서버 시작
                subprocess.Popen([
                    'python', str(server_script),
                    '--host', '0.0.0.0',
                    '--port', '8080'
                ])
                logger.info("✅ Windows API 서버 재시작 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 재시작 실패: {e}")
    
    def main(self):
        """메인 루프"""
        config = self.load_config()
        sync_interval = int(config.get('SYNC_INTERVAL', '30'))
        auto_restart = config.get('AUTO_RESTART', 'true').lower() == 'true'
        
        logger.info(f"🔄 동기화 간격: {sync_interval}초")
        logger.info(f"🔄 자동 재시작: {auto_restart}")
        
        while self.running:
            try:
                # GitHub 업데이트 확인
                if self.check_git_updates():
                    if auto_restart:
                        self.restart_services()
                
                # 서비스 중지 이벤트 대기
                if win32event.WaitForSingleObject(self.stop_event, sync_interval * 1000) == win32event.WAIT_OBJECT_0:
                    break
                    
            except Exception as e:
                logger.error(f"❌ 동기화 오류: {e}")
                time.sleep(sync_interval)
        
        logger.info("⏹️ 동기화 서비스 종료")

def main():
    """메인 함수"""
    if len(sys.argv) == 1:
        # 서비스로 실행
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WindowsSyncService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # 명령어 처리
        win32serviceutil.HandleCommandLine(WindowsSyncService)

if __name__ == '__main__':
    main() 