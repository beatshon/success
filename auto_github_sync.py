#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 GitHub 동기화 스크립트
파일 변경을 감지하여 자동으로 GitHub에 동기화
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# GitHub 동기화 관리자 import
from github_sync_manager import GitHubSyncManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_github_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    """파일 변경 감지 핸들러"""
    
    def __init__(self, sync_manager, sync_delay=30):
        self.sync_manager = sync_manager
        self.sync_delay = sync_delay
        self.last_sync_time = 0
        self.pending_changes = set()
        self.sync_lock = threading.Lock()
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, "created")
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, "modified")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, "deleted")
    
    def on_moved(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, "moved")
    
    def _handle_file_change(self, file_path, change_type):
        """파일 변경 처리"""
        # 로그 파일이나 임시 파일은 무시
        if self._should_ignore_file(file_path):
            return
        
        file_path = Path(file_path).relative_to(Path.cwd())
        self.pending_changes.add(str(file_path))
        
        logger.info(f"파일 변경 감지: {file_path} ({change_type})")
        
        # 동기화 스케줄링
        self._schedule_sync()
    
    def _should_ignore_file(self, file_path):
        """무시할 파일인지 확인"""
        ignore_patterns = [
            '.git', '__pycache__', '.pyc', '.log', 
            'logs', 'venv', 'backup_', 'temp'
        ]
        
        file_path_str = str(file_path).lower()
        return any(pattern in file_path_str for pattern in ignore_patterns)
    
    def _schedule_sync(self):
        """동기화 스케줄링"""
        current_time = time.time()
        
        with self.sync_lock:
            if current_time - self.last_sync_time > self.sync_delay:
                # 즉시 동기화
                self._perform_sync()
            else:
                # 지연된 동기화
                threading.Timer(self.sync_delay, self._perform_sync).start()
    
    def _perform_sync(self):
        """실제 동기화 수행"""
        with self.sync_lock:
            if not self.pending_changes:
                return
            
            logger.info(f"자동 동기화 시작: {len(self.pending_changes)}개 파일")
            
            try:
                # GitHub로 동기화
                if self.sync_manager.sync_to_github():
                    logger.info("자동 동기화 완료")
                    self.pending_changes.clear()
                    self.last_sync_time = time.time()
                else:
                    logger.error("자동 동기화 실패")
            except Exception as e:
                logger.error(f"동기화 중 오류 발생: {e}")

class AutoGitHubSync:
    """자동 GitHub 동기화 관리자"""
    
    def __init__(self, config_file="config/github_sync_config.json"):
        self.config_file = Path(config_file)
        self.sync_manager = GitHubSyncManager()
        self.observer = None
        self.handler = None
        
        # 설정 로드
        self.load_config()
    
    def load_config(self):
        """설정 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    self.auto_sync = self.config.get('auto_sync', True)
                    self.sync_interval = self.config.get('sync_interval', 300)
                    logger.info("자동 동기화 설정 로드됨")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
                self.auto_sync = True
                self.sync_interval = 300
        else:
            logger.warning("설정 파일이 없습니다. 기본 설정을 사용합니다.")
            self.auto_sync = True
            self.sync_interval = 300
    
    def start_monitoring(self):
        """파일 변경 모니터링 시작"""
        if not self.auto_sync:
            logger.info("자동 동기화가 비활성화되어 있습니다.")
            return
        
        logger.info("파일 변경 모니터링 시작...")
        
        # 파일 변경 핸들러 생성
        self.handler = FileChangeHandler(self.sync_manager, self.sync_interval)
        
        # Observer 생성 및 시작
        self.observer = Observer()
        self.observer.schedule(self.handler, str(Path.cwd()), recursive=True)
        self.observer.start()
        
        logger.info(f"모니터링 시작됨 (동기화 지연: {self.sync_interval}초)")
    
    def stop_monitoring(self):
        """파일 변경 모니터링 중지"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("모니터링 중지됨")
    
    def manual_sync(self):
        """수동 동기화"""
        logger.info("수동 동기화 시작...")
        
        try:
            # GitHub에서 풀
            if self.sync_manager.sync_from_github():
                logger.info("GitHub에서 풀 완료")
            
            # GitHub로 푸시
            if self.sync_manager.sync_to_github():
                logger.info("GitHub로 푸시 완료")
                return True
            else:
                logger.error("GitHub로 푸시 실패")
                return False
        except Exception as e:
            logger.error(f"수동 동기화 중 오류 발생: {e}")
            return False
    
    def get_status(self):
        """동기화 상태 확인"""
        return {
            'auto_sync_enabled': self.auto_sync,
            'sync_interval': self.sync_interval,
            'monitoring_active': self.observer and self.observer.is_alive(),
            'pending_changes': len(self.handler.pending_changes) if self.handler else 0
        }

def main():
    """메인 함수"""
    print("=" * 60)
    print("자동 GitHub 동기화 시스템")
    print("=" * 60)
    
    auto_sync = AutoGitHubSync()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            print("자동 동기화 모니터링 시작...")
            auto_sync.start_monitoring()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n모니터링 중지 중...")
                auto_sync.stop_monitoring()
        
        elif command == "sync":
            print("수동 동기화 실행...")
            if auto_sync.manual_sync():
                print("✅ 동기화 완료")
            else:
                print("❌ 동기화 실패")
        
        elif command == "status":
            status = auto_sync.get_status()
            print("동기화 상태:")
            print(f"  자동 동기화: {'활성화' if status['auto_sync_enabled'] else '비활성화'}")
            print(f"  동기화 간격: {status['sync_interval']}초")
            print(f"  모니터링: {'활성화' if status['monitoring_active'] else '비활성화'}")
            print(f"  대기 중인 변경사항: {status['pending_changes']}개")
        
        else:
            print("사용법:")
            print("  python auto_github_sync.py start  - 자동 모니터링 시작")
            print("  python auto_github_sync.py sync   - 수동 동기화")
            print("  python auto_github_sync.py status - 상태 확인")
    else:
        print("사용법:")
        print("  python auto_github_sync.py start  - 자동 모니터링 시작")
        print("  python auto_github_sync.py sync   - 수동 동기화")
        print("  python auto_github_sync.py status - 상태 확인")

if __name__ == "__main__":
    main() 