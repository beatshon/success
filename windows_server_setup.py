"""
윈도우 서버용 키움 자동매매 시스템 설정
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import logging

def setup_logging():
    """로깅 설정"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/server_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """필요한 패키지 확인 및 설치"""
    required_packages = [
        'PyQt5',
        'loguru',
        'pandas',
        'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 설치 필요")
    
    if missing_packages:
        print(f"\n설치 중: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} 설치 완료")
            except subprocess.CalledProcessError:
                print(f"❌ {package} 설치 실패")
                return False
    
    return True

def check_kiwoom_installation():
    """키움 영웅문 설치 확인"""
    kiwoom_paths = [
        r"C:\Program Files (x86)\Kiwoom\KiwoomAPI\OpenAPI.exe",
        r"C:\Program Files\Kiwoom\KiwoomAPI\OpenAPI.exe"
    ]
    
    for path in kiwoom_paths:
        if os.path.exists(path):
            print(f"✅ 키움 영웅문 발견: {path}")
            return path
    
    print("❌ 키움 영웅문을 찾을 수 없습니다.")
    print("   키움증권 홈페이지에서 영웅문을 다운로드하여 설치하세요.")
    return None

def create_startup_script():
    """시작 스크립트 생성"""
    script_content = '''@echo off
echo 키움 자동매매 시스템 시작
echo.

REM 환경 변수 설정
set LANG=ko_KR.UTF-8
set LC_ALL=ko_KR.UTF-8

REM 코드 페이지 설정
chcp 949

echo 현재 시간: %date% %time%
echo.

REM Python 스크립트 실행
python gui_trader.py

pause
'''
    
    with open('start_trading.bat', 'w', encoding='cp949') as f:
        f.write(script_content)
    
    print("✅ 시작 스크립트 생성: start_trading.bat")

def create_service_script():
    """서비스용 스크립트 생성 (백그라운드 실행)"""
    script_content = '''@echo off
echo 키움 자동매매 시스템 (서비스 모드)
echo.

REM 환경 변수 설정
set LANG=ko_KR.UTF-8
set LC_ALL=ko_KR.UTF-8
chcp 949

REM 무한 루프로 실행
:loop
echo [%date% %time%] 자동매매 시스템 시작
python gui_trader.py

echo [%date% %time%] 프로그램 종료됨. 30초 후 재시작...
timeout /t 30 /nobreak > nul
goto loop
'''
    
    with open('run_service.bat', 'w', encoding='cp949') as f:
        f.write(script_content)
    
    print("✅ 서비스 스크립트 생성: run_service.bat")

def setup_windows_task():
    """Windows 작업 스케줄러 설정"""
    print("\n📅 Windows 작업 스케줄러 설정")
    print("다음 명령어를 관리자 권한으로 실행하세요:")
    print()
    print("schtasks /create /tn \"KiwoomAutoTrading\" /tr \"C:\\kiwoom_trading\\run_service.bat\" /sc onstart /ru SYSTEM")
    print()
    print("또는 수동으로 작업 스케줄러에서 설정:")
    print("1. 작업 스케줄러 열기")
    print("2. '작업 만들기' 클릭")
    print("3. 트리거: '시스템 시작 시'")
    print("4. 동작: '프로그램 시작'")
    print("5. 프로그램: C:\\kiwoom_trading\\run_service.bat")

def main():
    """메인 설정 함수"""
    print("=" * 60)
    print("윈도우 서버용 키움 자동매매 시스템 설정")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging()
    
    # 1. 의존성 확인
    print("\n1️⃣ 필요한 패키지 확인 중...")
    if not check_dependencies():
        print("❌ 의존성 설치 실패")
        return
    
    # 2. 키움 영웅문 확인
    print("\n2️⃣ 키움 영웅문 확인 중...")
    kiwoom_path = check_kiwoom_installation()
    if not kiwoom_path:
        print("❌ 키움 영웅문 설치 필요")
        return
    
    # 3. 시작 스크립트 생성
    print("\n3️⃣ 시작 스크립트 생성 중...")
    create_startup_script()
    create_service_script()
    
    # 4. 작업 스케줄러 설정 안내
    print("\n4️⃣ 자동 시작 설정 안내...")
    setup_windows_task()
    
    print("\n" + "=" * 60)
    print("✅ 설정 완료!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. 키움 영웅문 실행 및 로그인")
    print("2. config.py에서 API 키 설정")
    print("3. start_trading.bat 실행하여 테스트")
    print("4. 정상 동작 확인 후 run_service.bat로 서비스 실행")
    print("\n주의사항:")
    print("- 서버 재부팅 시 자동 시작되도록 작업 스케줄러 설정")
    print("- 방화벽에서 키움 API 포트 허용")
    print("- 정기적인 로그 확인 및 백업")

if __name__ == "__main__":
    main() 