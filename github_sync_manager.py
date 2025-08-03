#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 기반 파일 동기화 관리자
맥과 윈도우 서버 간 GitHub를 통한 파일 동기화
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/github_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubSyncManager:
    def __init__(self):
        self.repo_url = None
        self.branch = "main"
        self.local_path = Path.cwd()
        self.config_file = Path("config/github_sync_config.json")
        
        # 설정 로드
        self.load_config()
    
    def load_config(self):
        """GitHub 동기화 설정 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.repo_url = config.get('repo_url')
                    self.branch = config.get('branch', 'main')
                    logger.info(f"설정 로드됨: {self.repo_url}")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        else:
            logger.warning("GitHub 설정 파일이 없습니다. 기본 설정을 사용합니다.")
    
    def check_git_status(self):
        """Git 상태 확인"""
        try:
            result = subprocess.run(['git', 'status'], 
                                  capture_output=True, text=True, cwd=self.local_path)
            if result.returncode == 0:
                logger.info("Git 저장소 상태 확인 완료")
                return True
            else:
                logger.warning("Git 저장소가 초기화되지 않았습니다.")
                return False
        except FileNotFoundError:
            logger.error("Git이 설치되지 않았습니다.")
            return False
    
    def init_git_repo(self):
        """Git 저장소 초기화"""
        try:
            # Git 초기화
            subprocess.run(['git', 'init'], cwd=self.local_path, check=True)
            logger.info("Git 저장소 초기화 완료")
            
            # 원격 저장소 추가
            if self.repo_url:
                subprocess.run(['git', 'remote', 'add', 'origin', self.repo_url], 
                             cwd=self.local_path, check=True)
                logger.info(f"원격 저장소 추가: {self.repo_url}")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 저장소 초기화 실패: {e}")
            return False
    
    def setup_git_config(self):
        """Git 사용자 설정"""
        try:
            # 사용자 이름과 이메일 설정 (실제 값으로 변경 필요)
            subprocess.run(['git', 'config', 'user.name', 'Kiwoom Trading Bot'], 
                         cwd=self.local_path, check=True)
            subprocess.run(['git', 'config', 'user.email', 'trading@example.com'], 
                         cwd=self.local_path, check=True)
            logger.info("Git 사용자 설정 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 사용자 설정 실패: {e}")
            return False
    
    def add_files_to_git(self, file_patterns=None):
        """파일들을 Git에 추가"""
        if file_patterns is None:
            file_patterns = [
                "*.py", "*.bat", "*.sh", "*.md", "*.txt", "*.json",
                "config/*", "templates/*", "logs/*"
            ]
        
        try:
            for pattern in file_patterns:
                subprocess.run(['git', 'add', pattern], cwd=self.local_path, check=True)
            
            logger.info("파일들을 Git에 추가 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"파일 추가 실패: {e}")
            return False
    
    def commit_changes(self, message=None):
        """변경사항 커밋"""
        if message is None:
            message = f"Auto sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.local_path, check=True)
            logger.info(f"변경사항 커밋 완료: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"커밋 실패 (변경사항이 없을 수 있음): {e}")
            return False
    
    def push_to_github(self):
        """GitHub에 푸시"""
        try:
            subprocess.run(['git', 'push', 'origin', self.branch], 
                         cwd=self.local_path, check=True)
            logger.info(f"GitHub 푸시 완료: {self.branch} 브랜치")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub 푸시 실패: {e}")
            return False
    
    def pull_from_github(self):
        """GitHub에서 풀"""
        try:
            subprocess.run(['git', 'pull', 'origin', self.branch], 
                         cwd=self.local_path, check=True)
            logger.info(f"GitHub 풀 완료: {self.branch} 브랜치")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub 풀 실패: {e}")
            return False
    
    def clone_from_github(self, target_path=None):
        """GitHub에서 클론"""
        if target_path is None:
            target_path = self.local_path
        
        try:
            if self.repo_url:
                subprocess.run(['git', 'clone', self.repo_url, str(target_path)], 
                             check=True)
                logger.info(f"GitHub 클론 완료: {target_path}")
                return True
            else:
                logger.error("저장소 URL이 설정되지 않았습니다.")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub 클론 실패: {e}")
            return False
    
    def sync_to_github(self):
        """GitHub로 동기화 (푸시)"""
        logger.info("GitHub로 동기화 시작...")
        
        # Git 상태 확인
        if not self.check_git_status():
            if not self.init_git_repo():
                return False
            if not self.setup_git_config():
                return False
        
        # 파일 추가
        if not self.add_files_to_git():
            return False
        
        # 커밋
        if not self.commit_changes():
            logger.warning("커밋할 변경사항이 없습니다.")
            return True
        
        # 푸시
        if not self.push_to_github():
            return False
        
        logger.info("GitHub 동기화 완료!")
        return True
    
    def sync_from_github(self):
        """GitHub에서 동기화 (풀)"""
        logger.info("GitHub에서 동기화 시작...")
        
        # Git 상태 확인
        if not self.check_git_status():
            logger.error("Git 저장소가 초기화되지 않았습니다.")
            return False
        
        # 풀
        if not self.pull_from_github():
            return False
        
        logger.info("GitHub에서 동기화 완료!")
        return True
    
    def create_backup_branch(self, branch_name=None):
        """백업 브랜치 생성"""
        if branch_name is None:
            branch_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 현재 브랜치에서 새 브랜치 생성
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                         cwd=self.local_path, check=True)
            
            # 백업 브랜치 푸시
            subprocess.run(['git', 'push', 'origin', branch_name], 
                         cwd=self.local_path, check=True)
            
            # 원래 브랜치로 돌아가기
            subprocess.run(['git', 'checkout', self.branch], 
                         cwd=self.local_path, check=True)
            
            logger.info(f"백업 브랜치 생성 완료: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"백업 브랜치 생성 실패: {e}")
            return False
    
    def get_file_status(self):
        """파일 상태 확인"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.local_path)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return {
                    'modified': [f for f in files if f.startswith('M')],
                    'added': [f for f in files if f.startswith('A')],
                    'deleted': [f for f in files if f.startswith('D')],
                    'untracked': [f for f in files if f.startswith('??')]
                }
            else:
                return None
        except subprocess.CalledProcessError:
            return None

def main():
    """메인 함수"""
    print("=" * 60)
    print("GitHub 동기화 관리자")
    print("=" * 60)
    
    sync_manager = GitHubSyncManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "push":
            sync_manager.sync_to_github()
        elif command == "pull":
            sync_manager.sync_from_github()
        elif command == "status":
            status = sync_manager.get_file_status()
            if status:
                print("파일 상태:")
                print(f"  수정됨: {len(status['modified'])}개")
                print(f"  추가됨: {len(status['added'])}개")
                print(f"  삭제됨: {len(status['deleted'])}개")
                print(f"  추적되지 않음: {len(status['untracked'])}개")
            else:
                print("Git 상태를 확인할 수 없습니다.")
        elif command == "backup":
            sync_manager.create_backup_branch()
        else:
            print("사용법:")
            print("  python github_sync_manager.py push   # GitHub로 푸시")
            print("  python github_sync_manager.py pull   # GitHub에서 풀")
            print("  python github_sync_manager.py status # 상태 확인")
            print("  python github_sync_manager.py backup # 백업 브랜치 생성")
    else:
        print("사용법:")
        print("  python github_sync_manager.py push   # GitHub로 푸시")
        print("  python github_sync_manager.py pull   # GitHub에서 풀")
        print("  python github_sync_manager.py status # 상태 확인")
        print("  python github_sync_manager.py backup # 백업 브랜치 생성")

if __name__ == "__main__":
    main() 