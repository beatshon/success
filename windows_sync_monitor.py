#!/usr/bin/env python3
"""
Windows 서버 동기화 모니터링 (개선된 버전)
GitHub 변경사항을 감지하고 명확한 메시지 출력
"""

import os
import time
import subprocess
import json
from datetime import datetime
from loguru import logger

# 로그 설정
logger.add("logs/windows_sync.log", rotation="1 day", retention="7 days")

class WindowsSyncMonitor:
    """Windows 동기화 모니터링 클래스"""
    
    def __init__(self):
        self.last_commit_hash = None
        self.check_interval = 30  # 30초
        self.project_path = os.getcwd()
        
    def get_current_commit_hash(self):
        """현재 커밋 해시 가져오기"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_path
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"커밋 해시 가져오기 실패: {e}")
        return None
    
    def get_remote_commit_hash(self):
        """원격 커밋 해시 가져오기"""
        try:
            # 원격 정보 업데이트
            subprocess.run(['git', 'fetch', 'origin'], cwd=self.project_path)
            
            result = subprocess.run(
                ['git', 'rev-parse', 'origin/main'],
                capture_output=True, text=True, cwd=self.project_path
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"원격 커밋 해시 가져오기 실패: {e}")
        return None
    
    def check_for_updates(self):
        """업데이트 확인"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"[{current_time}] 🔄 GitHub 업데이트 확인 중...")
        
        # 현재 커밋 해시
        current_hash = self.get_current_commit_hash()
        remote_hash = self.get_remote_commit_hash()
        
        if not current_hash or not remote_hash:
            logger.error(f"[{current_time}] ❌ 커밋 해시 가져오기 실패")
            return False
        
        # 변경사항 확인
        if current_hash != remote_hash:
            logger.info(f"[{current_time}] 📥 새로운 변경사항 발견!")
            logger.info(f"[{current_time}] 🔄 변경사항을 가져오는 중...")
            
            # 변경사항 가져오기
            success = self.pull_changes()
            
            if success:
                logger.success(f"[{current_time}] ✅ 풀 완료")
                self.show_changed_files()
                self.last_commit_hash = remote_hash
                return True
            else:
                logger.error(f"[{current_time}] ❌ 풀 실패")
                return False
        else:
            logger.info(f"[{current_time}] ✅ 최신 상태입니다.")
            logger.info(f"[{current_time}] 📊 현재 상태: 최신 커밋과 동기화됨")
            return False
    
    def pull_changes(self):
        """변경사항 가져오기"""
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                capture_output=True, text=True, cwd=self.project_path
            )
            
            if result.returncode == 0:
                logger.info("변경사항 가져오기 성공")
                return True
            else:
                logger.error(f"변경사항 가져오기 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"변경사항 가져오기 오류: {e}")
            return False
    
    def show_changed_files(self):
        """변경된 파일 목록 표시"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_path
            )
            
            if result.returncode == 0 and result.stdout.strip():
                changed_files = result.stdout.strip().split('\n')
                logger.info(f"📋 변경된 파일 ({len(changed_files)}개):")
                for file in changed_files:
                    if file.strip():
                        logger.info(f"  - {file.strip()}")
            else:
                logger.info("📋 변경된 파일 없음")
                
        except Exception as e:
            logger.error(f"변경된 파일 목록 가져오기 실패: {e}")
    
    def run(self):
        """모니터링 실행"""
        logger.info("🚀 Windows 동기화 모니터링 시작")
        logger.info(f"📁 프로젝트 경로: {self.project_path}")
        logger.info(f"⏰ 확인 간격: {self.check_interval}초")
        
        # 초기 커밋 해시 저장
        self.last_commit_hash = self.get_current_commit_hash()
        
        while True:
            try:
                # 업데이트 확인
                has_changes = self.check_for_updates()
                
                # 변경사항이 있으면 추가 작업 수행
                if has_changes:
                    self.handle_changes()
                
                # 대기
                logger.info(f"⏰ {self.check_interval}초 후 다시 확인합니다...")
                logger.info("=" * 50)
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 사용자에 의해 중단됨")
                break
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(self.check_interval)
    
    def handle_changes(self):
        """변경사항 처리"""
        logger.info("🔄 변경사항 처리 중...")
        
        # 여기에 추가 작업을 넣을 수 있습니다
        # 예: 서버 재시작, 설정 파일 업데이트 등
        
        logger.info("✅ 변경사항 처리 완료")

def main():
    """메인 함수"""
    monitor = WindowsSyncMonitor()
    monitor.run()

if __name__ == "__main__":
    main() 