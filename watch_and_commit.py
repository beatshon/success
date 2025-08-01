#!/usr/bin/env python3
"""
실시간 파일 감시 및 자동 커밋
파일이 변경되면 자동으로 GitHub에 푸시
"""

import os
import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

# 로그 설정
logger.add("logs/github_sync.log", rotation="1 day", retention="7 days")

class GitSyncHandler(FileSystemEventHandler):
    """Git 동기화 이벤트 핸들러"""
    
    def __init__(self):
        self.last_commit_time = {}
        self.commit_cooldown = 30  # 30초 쿨다운
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        current_time = time.time()
        
        # 쿨다운 체크
        if file_path in self.last_commit_time:
            if current_time - self.last_commit_time[file_path] < self.commit_cooldown:
                return
        
        self.last_commit_time[file_path] = current_time
        
        # 동기화할 파일인지 확인
        if self.should_sync_file(file_path):
            logger.info(f"파일 변경 감지: {file_path}")
            self.auto_commit_and_push()
    
    def should_sync_file(self, file_path):
        """동기화할 파일인지 확인"""
        # .gitignore에 있는 파일 제외
        ignore_patterns = [
            '__pycache__', '.git', 'venv', 'logs', 
            '.DS_Store', '*.log', '*.tmp'
        ]
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return False
        
        # 특정 확장자만 동기화
        sync_extensions = ['.py', '.md', '.txt', '.json', '.bat', '.sh']
        _, ext = os.path.splitext(file_path)
        
        return ext in sync_extensions
    
    def auto_commit_and_push(self):
        """자동 커밋 및 푸시"""
        try:
            logger.info("자동 커밋 및 푸시 시작")
            
            # 변경사항 확인
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                logger.info("변경사항이 없습니다.")
                return
            
            # 변경사항 스테이징
            subprocess.run(['git', 'add', '.'], check=True)
            
            # 커밋
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto sync: {timestamp}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            # 푸시
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            logger.info("✅ 자동 동기화 완료")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 자동 동기화 실패: {e}")
        except Exception as e:
            logger.error(f"❌ 자동 동기화 오류: {e}")

def main():
    """메인 실행 함수"""
    logger.info("🔄 GitHub 자동 동기화 시스템 시작")
    
    # 감시할 디렉토리 설정
    watch_directories = ['.', 'config']
    
    # Observer 설정
    observer = Observer()
    event_handler = GitSyncHandler()
    
    # 디렉토리 감시 등록
    for directory in watch_directories:
        if os.path.exists(directory):
            observer.schedule(event_handler, directory, recursive=True)
            logger.info(f"📁 감시 시작: {directory}")
    
    # 감시 시작
    observer.start()
    logger.info("🚀 실시간 파일 감시 시작")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    
    observer.stop()
    observer.join()
    logger.info("🛑 GitHub 자동 동기화 시스템 종료")

if __name__ == "__main__":
    main()
