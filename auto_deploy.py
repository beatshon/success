#!/usr/bin/env python3
"""
자동 배포 스크립트
개발 → GitHub → Windows 서버 배포 자동화
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

class AutoDeployer:
    def __init__(self):
        self.project_dir = Path("/Users/jaceson/kiwoom_trading")
        self.git_remote = "origin"
        self.git_branch = "main"
        
    def run_command(self, command, description=""):
        """명령어 실행"""
        print(f"\n🔄 {description}")
        print(f"실행: {command}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {description} 완료")
                if result.stdout.strip():
                    print(f"출력: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ {description} 실패")
                print(f"오류: {result.stderr.strip()}")
                return False
                
        except Exception as e:
            print(f"❌ {description} 중 오류: {e}")
            return False
    
    def check_git_status(self):
        """Git 상태 확인"""
        print("\n📊 Git 상태 확인 중...")
        
        # 변경사항 확인
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            print("변경된 파일들:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"  {line}")
            return True
        else:
            print("변경사항이 없습니다.")
            return False
    
    def run_tests(self):
        """테스트 실행"""
        print("\n🧪 테스트 실행 중...")
        
        # 전략 테스트
        if self.run_command("python test_strategy.py", "전략 테스트"):
            print("✅ 전략 테스트 통과")
        else:
            print("❌ 전략 테스트 실패")
            return False
        
        # 기타 테스트들...
        return True
    
    def commit_and_push(self, message=None):
        """커밋 및 푸시"""
        if not message:
            message = f"자동 업데이트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"\n💾 커밋 메시지: {message}")
        
        # 모든 변경사항 추가
        if not self.run_command("git add .", "변경사항 스테이징"):
            return False
        
        # 커밋
        if not self.run_command(f'git commit -m "{message}"', "커밋"):
            return False
        
        # 푸시
        if not self.run_command(f"git push {self.git_remote} {self.git_branch}", "GitHub 푸시"):
            return False
        
        return True
    
    def notify_windows_server(self):
        """Windows 서버에 배포 알림"""
        print("\n🖥️ Windows 서버 배포 알림")
        print("Windows 서버에서 다음 명령어를 실행하세요:")
        print("  cd C:\\kiwoom_trading")
        print("  git pull")
        print("  python auto_trader.py")
    
    def deploy(self, message=None, run_tests=True):
        """전체 배포 프로세스"""
        print("🚀 자동 배포 시작")
        print("=" * 50)
        
        # 1. Git 상태 확인
        if not self.check_git_status():
            print("변경사항이 없어 배포를 건너뜁니다.")
            return True
        
        # 2. 테스트 실행 (선택사항)
        if run_tests:
            if not self.run_tests():
                print("❌ 테스트 실패로 배포를 중단합니다.")
                return False
        
        # 3. 커밋 및 푸시
        if not self.commit_and_push(message):
            print("❌ Git 푸시 실패")
            return False
        
        # 4. Windows 서버 알림
        self.notify_windows_server()
        
        print("\n🎉 배포 완료!")
        return True

def main():
    deployer = AutoDeployer()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        message = sys.argv[1]
        run_tests = "--no-test" not in sys.argv
    else:
        message = None
        run_tests = True
    
    # 배포 실행
    success = deployer.deploy(message, run_tests)
    
    if success:
        print("\n✅ 배포가 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n❌ 배포 중 오류가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 