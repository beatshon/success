#!/usr/bin/env python3
"""
실시간 파일 감시 및 Windows 서버 동기화
파일이 변경되면 자동으로 Windows 서버에 반영
"""

import os
import time
import json
import subprocess
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

# 로그 설정
logger.add("logs/watch_and_sync.log", rotation="1 day", retention="7 days")

class FileChangeHandler(FileSystemEventHandler):
    """파일 변경 이벤트 핸들러"""
    
    def __init__(self, sync_script_path):
        self.sync_script_path = sync_script_path
        self.last_sync_time = {}
        self.sync_cooldown = 5  # 5초 쿨다운
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        current_time = time.time()
        
        # 쿨다운 체크 (같은 파일의 연속 변경 방지)
        if file_path in self.last_sync_time:
            if current_time - self.last_sync_time[file_path] < self.sync_cooldown:
                return
        
        self.last_sync_time[file_path] = current_time
        
        # 동기화할 파일인지 확인
        if self.should_sync_file(file_path):
            logger.info(f"파일 변경 감지: {file_path}")
            self.sync_to_windows(file_path)
    
    def should_sync_file(self, file_path):
        """동기화할 파일인지 확인"""
        sync_extensions = ['.py', '.json', '.txt', '.md', '.sh']
        sync_files = [
            'windows_api_server.py',
            'kiwoom_api.py',
            'auto_trader.py',
            'trading_strategy.py',
            'requirements.txt'
        ]
        
        # 파일명으로 확인
        filename = os.path.basename(file_path)
        if filename in sync_files:
            return True
        
        # 확장자로 확인
        _, ext = os.path.splitext(file_path)
        if ext in sync_extensions:
            return True
        
        return False
    
    def sync_to_windows(self, file_path):
        """Windows 서버로 파일 동기화"""
        try:
            logger.info(f"Windows 서버 동기화 시작: {file_path}")
            
            # 동기화 스크립트 실행
            result = subprocess.run([
                'bash', self.sync_script_path, 'files'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 동기화 성공: {file_path}")
            else:
                logger.error(f"❌ 동기화 실패: {file_path}")
                logger.error(f"오류: {result.stderr}")
                
        except Exception as e:
            logger.error(f"동기화 오류: {e}")

class RealTimeSync:
    """실시간 동기화 클래스"""
    
    def __init__(self):
        self.config = self.load_config()
        self.observer = None
        self.sync_script_path = "sync_to_windows.sh"
        
    def load_config(self):
        """설정 파일 로드"""
        config_file = "config/windows_server.conf"
        
        if os.path.exists(config_file):
            try:
                # bash 설정 파일을 Python 딕셔너리로 변환
                config = {}
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"')
                return config
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        
        return {}
    
    def test_windows_connection(self):
        """Windows 서버 연결 테스트"""
        try:
            host = self.config.get('WINDOWS_HOST', 'localhost')
            port = self.config.get('API_PORT', '8080')
            
            url = f"http://{host}:{port}/api/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ Windows 서버 연결 성공")
                return True
            else:
                logger.error(f"❌ Windows 서버 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Windows 서버 연결 실패: {e}")
            return False
    
    def start_watching(self):
        """파일 감시 시작"""
        try:
            # Windows 서버 연결 테스트
            if not self.test_windows_connection():
                logger.warning("⚠️ Windows 서버에 연결할 수 없습니다. 로컬 감시만 실행합니다.")
            
            # 감시할 디렉토리 설정
            watch_directories = ['.', 'config']
            
            # Observer 설정
            self.observer = Observer()
            event_handler = FileChangeHandler(self.sync_script_path)
            
            # 디렉토리 감시 등록
            for directory in watch_directories:
                if os.path.exists(directory):
                    self.observer.schedule(event_handler, directory, recursive=True)
                    logger.info(f"📁 감시 시작: {directory}")
            
            # 감시 시작
            self.observer.start()
            logger.info("🚀 실시간 파일 감시 시작")
            
            # 초기 동기화
            logger.info("🔄 초기 동기화 실행")
            subprocess.run(['bash', self.sync_script_path, 'files'])
            
            return True
            
        except Exception as e:
            logger.error(f"파일 감시 시작 실패: {e}")
            return False
    
    def stop_watching(self):
        """파일 감시 중지"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 실시간 파일 감시 중지")
    
    def run(self):
        """실행"""
        try:
            logger.info("🔄 실시간 동기화 시스템 시작")
            
            if not self.start_watching():
                return False
            
            # 무한 루프로 실행
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단됨")
            
            self.stop_watching()
            return True
            
        except Exception as e:
            logger.error(f"실행 오류: {e}")
            return False

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="실시간 파일 감시 및 Windows 서버 동기화")
    parser.add_argument("--test", action="store_true", help="Windows 서버 연결 테스트")
    parser.add_argument("--sync", action="store_true", help="수동 동기화 실행")
    
    args = parser.parse_args()
    
    sync_system = RealTimeSync()
    
    if args.test:
        # 연결 테스트
        sync_system.test_windows_connection()
    elif args.sync:
        # 수동 동기화
        subprocess.run(['bash', 'sync_to_windows.sh'])
    else:
        # 실시간 감시 시작
        sync_system.run()

if __name__ == "__main__":
    main() 