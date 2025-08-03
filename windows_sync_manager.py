#!/usr/bin/env python3
"""
Windows 서버 동기화 관리자
맥에서 전송된 파일을 자동으로 수신하고 처리
"""

import os
import sys
import time
import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WindowsSyncManager:
    def __init__(self):
        self.config = self.load_config()
        self.project_root = Path(self.config['WINDOWS_PATH'])
        self.logs_dir = self.project_root / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
    def load_config(self):
        """설정 파일 로드"""
        config_path = Path('config/windows_server.conf')
        if not config_path.exists():
            logger.error("설정 파일이 없습니다: config/windows_server.conf")
            sys.exit(1)
            
        config = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        return config
    
    def sync_from_mac(self):
        """맥에서 파일 동기화 수신"""
        logger.info("🔄 맥에서 파일 동기화 시작")
        
        # 동기화할 파일 목록
        files_to_sync = [
            'kiwoom_api.py',
            'auto_trader.py', 
            'trading_strategy.py',
            'hybrid_trading_system.py',
            'requirements.txt',
            'config.py'
        ]
        
        # 동기화할 디렉토리 목록
        dirs_to_sync = [
            'config',
            'logs'
        ]
        
        success_count = 0
        total_count = len(files_to_sync) + len(dirs_to_sync)
        
        # 파일 동기화
        for file_name in files_to_sync:
            file_path = self.project_root / file_name
            if file_path.exists():
                logger.info(f"📄 파일 확인: {file_name}")
                success_count += 1
            else:
                logger.warning(f"⚠️ 파일 없음: {file_name}")
        
        # 디렉토리 동기화
        for dir_name in dirs_to_sync:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                logger.info(f"📁 디렉토리 확인: {dir_name}")
                success_count += 1
            else:
                logger.warning(f"⚠️ 디렉토리 없음: {dir_name}")
        
        logger.info(f"✅ 동기화 완료: {success_count}/{total_count}")
        return success_count == total_count
    
    def restart_services(self):
        """서비스 재시작"""
        logger.info("🔄 서비스 재시작 중...")
        
        try:
            # 기존 Python 프로세스 종료
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                         capture_output=True, check=False)
            time.sleep(2)
            
            # Windows API 서버 재시작
            server_script = self.project_root / 'windows_api_server.py'
            if server_script.exists():
                subprocess.Popen([
                    'python', str(server_script),
                    '--host', '0.0.0.0',
                    '--port', self.config.get('API_PORT', '8080')
                ], cwd=str(self.project_root))
                logger.info("✅ Windows API 서버 재시작 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 재시작 실패: {e}")
    
    def check_git_updates(self):
        """GitHub 업데이트 확인"""
        logger.info("🔍 GitHub 업데이트 확인 중...")
        
        try:
            # Git 경로 설정
            git_path = r"C:\Program Files\Git\bin\git.exe"
            
            # Git 상태 확인
            result = subprocess.run([git_path, 'fetch', 'origin'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                # 변경사항 확인
                status_result = subprocess.run([git_path, 'status', '-uno'], 
                                             capture_output=True, text=True, cwd=os.getcwd())
                
                if 'behind' in status_result.stdout:
                    logger.info("📥 새로운 변경사항 발견!")
                    
                    # Pull 실행
                    pull_result = subprocess.run([git_path, 'pull', 'origin', 'main'], 
                                               capture_output=True, text=True, cwd=os.getcwd())
                    
                    if pull_result.returncode == 0:
                        logger.info("✅ GitHub 업데이트 완료")
                        return True
                    else:
                        logger.error(f"❌ GitHub 업데이트 실패: {pull_result.stderr}")
                else:
                    logger.info("✅ 최신 상태입니다")
            else:
                logger.error(f"❌ Git fetch 실패: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ GitHub 확인 오류: {e}")
        
        return False
    
    def run_auto_sync(self):
        """자동 동기화 실행"""
        logger.info("🚀 자동 동기화 시작")
        
        sync_interval = int(self.config.get('SYNC_INTERVAL', '30'))
        auto_restart = self.config.get('AUTO_RESTART', 'true').lower() == 'true'
        
        while True:
            try:
                # GitHub 업데이트 확인
                if self.check_git_updates():
                    # 맥에서 동기화 확인
                    if self.sync_from_mac():
                        if auto_restart:
                            self.restart_services()
                
                logger.info(f"⏰ {sync_interval}초 후 다시 확인합니다...")
                time.sleep(sync_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️ 자동 동기화 중단")
                break
            except Exception as e:
                logger.error(f"❌ 동기화 오류: {e}")
                time.sleep(sync_interval)

def main():
    """메인 함수"""
    print("🔄 Windows 서버 동기화 관리자")
    print("=" * 40)
    
    manager = WindowsSyncManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'sync':
            manager.sync_from_mac()
        elif command == 'restart':
            manager.restart_services()
        elif command == 'git':
            manager.check_git_updates()
        elif command == 'auto':
            manager.run_auto_sync()
        else:
            print("사용법:")
            print("  python windows_sync_manager.py sync    - 파일 동기화")
            print("  python windows_sync_manager.py restart - 서비스 재시작")
            print("  python windows_sync_manager.py git     - GitHub 업데이트")
            print("  python windows_sync_manager.py auto    - 자동 동기화")
    else:
        # 대화형 모드
        print("1. 파일 동기화")
        print("2. 서비스 재시작")
        print("3. GitHub 업데이트")
        print("4. 자동 동기화 시작")
        print("5. 종료")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-5): ").strip()
                
                if choice == '1':
                    manager.sync_from_mac()
                elif choice == '2':
                    manager.restart_services()
                elif choice == '3':
                    manager.check_git_updates()
                elif choice == '4':
                    manager.run_auto_sync()
                elif choice == '5':
                    print("👋 종료합니다")
                    break
                else:
                    print("❌ 잘못된 선택입니다")
                    
            except KeyboardInterrupt:
                print("\n👋 종료합니다")
                break

if __name__ == "__main__":
    main() 