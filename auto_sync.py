#!/usr/bin/env python3
"""
자동 파일 동기화 스크립트
맥에서 윈도우 서버로 파일을 자동으로 동기화
"""

import os
import shutil
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileSyncHandler(FileSystemEventHandler):
    def __init__(self, local_dir, remote_dir):
        self.local_dir = Path(local_dir)
        self.remote_dir = remote_dir
        self.last_sync = time.time()
        self.sync_delay = 5  # 5초 딜레이
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # 파일 확장자 필터링
        if event.src_path.endswith(('.py', '.txt', '.md', '.json', '.yaml', '.yml')):
            current_time = time.time()
            if current_time - self.last_sync > self.sync_delay:
                print(f"📝 파일 변경 감지: {event.src_path}")
                self.sync_files()
                self.last_sync = current_time
    
    def sync_files(self):
        """파일 동기화 실행"""
        try:
            # rsync 명령어 실행
            cmd = [
                'rsync', '-avz', '--delete',
                '--exclude=venv/',
                '--exclude=logs/',
                '--exclude=__pycache__/',
                '--exclude=*.pyc',
                '--exclude=.git/',
                f"{self.local_dir}/",
                f"{self.remote_dir}/"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 동기화 완료")
            else:
                print(f"❌ 동기화 실패: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 동기화 오류: {e}")

def main():
    # 설정
    LOCAL_DIR = "/Users/jaceson/kiwoom_trading"
    REMOTE_DIR = "Administrator@your-windows-server-ip:C:/kiwoom_trading"
    
    print("🔄 자동 파일 동기화 시작...")
    print(f"로컬: {LOCAL_DIR}")
    print(f"원격: {REMOTE_DIR}")
    print("Ctrl+C로 중단")
    
    # 이벤트 핸들러 생성
    event_handler = FileSyncHandler(LOCAL_DIR, REMOTE_DIR)
    
    # Observer 설정
    observer = Observer()
    observer.schedule(event_handler, LOCAL_DIR, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n⏹️ 동기화 중단")
    
    observer.join()

if __name__ == "__main__":
    main() 