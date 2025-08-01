#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스 기반 주식 거래 시스템 통합 실행 스크립트
네이버 뉴스 수집, 분석, 거래, 모니터링을 한 번에 실행하는 메인 스크립트
"""

import os
import sys
import json
import time
import argparse
import subprocess
import threading
from datetime import datetime
from loguru import logger

def check_dependencies():
    """필요한 패키지 설치 확인"""
    required_packages = [
        "requests", "pandas", "numpy", "loguru"
    ]
    
    optional_packages = [
        "flask", "flask-socketio"
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        logger.error(f"필수 패키지가 설치되지 않았습니다: {', '.join(missing_required)}")
        logger.info("설치 명령어: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        logger.warning(f"선택적 패키지가 설치되지 않았습니다: {', '.join(missing_optional)}")
        logger.info("웹 대시보드를 사용하려면: pip install " + " ".join(missing_optional))
    
    return True

def check_config_files():
    """설정 파일 확인"""
    config_files = [
        "config/news_config.json",
        "config/news_trading_config.json"
    ]
    
    missing_configs = []
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            missing_configs.append(config_file)
    
    if missing_configs:
        logger.warning(f"설정 파일이 없습니다: {', '.join(missing_configs)}")
        logger.info("시스템을 처음 실행하면 자동으로 생성됩니다.")
        return False
    
    return True

def check_api_keys():
    """API 키 설정 확인"""
    try:
        with open("config/news_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        client_id = config.get("naver_api", {}).get("client_id")
        client_secret = config.get("naver_api", {}).get("client_secret")
        
        if client_id == "your_naver_client_id" or client_secret == "your_naver_client_secret":
            logger.error("네이버 API 키가 설정되지 않았습니다.")
            logger.info("NAVER_API_SETUP_GUIDE.md 파일을 참고하여 API 키를 설정하세요.")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"API 키 확인 중 오류: {e}")
        return False

def run_news_analysis():
    """뉴스 분석 실행"""
    try:
        logger.info("뉴스 분석을 시작합니다...")
        
        # 뉴스 분석 실행
        result = subprocess.run([
            sys.executable, "run_news_analysis.py", "--test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ 뉴스 분석이 완료되었습니다.")
            return True
        else:
            logger.error(f"❌ 뉴스 분석 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"뉴스 분석 실행 중 오류: {e}")
        return False

def run_trading_system(test_mode=True):
    """거래 시스템 실행"""
    try:
        logger.info("거래 시스템을 시작합니다...")
        
        cmd = [sys.executable, "news_trading_integration.py"]
        if test_mode:
            cmd.append("--test")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ 거래 시스템이 완료되었습니다.")
            return True
        else:
            logger.error(f"❌ 거래 시스템 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"거래 시스템 실행 중 오류: {e}")
        return False

def run_dashboard(host="localhost", port=5000):
    """웹 대시보드 실행"""
    try:
        logger.info(f"웹 대시보드를 시작합니다... (http://{host}:{port})")
        
        # 대시보드 템플릿 생성
        subprocess.run([
            sys.executable, "news_monitoring_dashboard.py", "--create-template"
        ], capture_output=True)
        
        # 대시보드 실행
        dashboard_process = subprocess.Popen([
            sys.executable, "news_monitoring_dashboard.py",
            "--host", host, "--port", str(port)
        ])
        
        logger.info(f"✅ 웹 대시보드가 시작되었습니다: http://{host}:{port}")
        return dashboard_process
        
    except Exception as e:
        logger.error(f"웹 대시보드 실행 중 오류: {e}")
        return None

def run_comprehensive_test():
    """종합 테스트 실행"""
    logger.info("="*60)
    logger.info("🧪 뉴스 기반 주식 거래 시스템 종합 테스트")
    logger.info("="*60)
    
    # 1. 의존성 확인
    logger.info("1️⃣ 의존성 확인 중...")
    if not check_dependencies():
        return False
    
    # 2. 설정 파일 확인
    logger.info("2️⃣ 설정 파일 확인 중...")
    check_config_files()
    
    # 3. API 키 확인
    logger.info("3️⃣ API 키 확인 중...")
    if not check_api_keys():
        logger.warning("API 키가 설정되지 않아 테스트를 건너뜁니다.")
        return False
    
    # 4. 뉴스 분석 테스트
    logger.info("4️⃣ 뉴스 분석 테스트 중...")
    if not run_news_analysis():
        return False
    
    # 5. 거래 시스템 테스트
    logger.info("5️⃣ 거래 시스템 테스트 중...")
    if not run_trading_system(test_mode=True):
        return False
    
    logger.info("✅ 모든 테스트가 성공적으로 완료되었습니다!")
    return True

def run_full_system():
    """전체 시스템 실행"""
    logger.info("="*60)
    logger.info("🚀 뉴스 기반 주식 거래 시스템 전체 실행")
    logger.info("="*60)
    
    # 1. 시스템 검증
    if not check_dependencies():
        return False
    
    if not check_api_keys():
        return False
    
    # 2. 뉴스 분석 실행
    logger.info("📰 뉴스 수집 및 분석을 시작합니다...")
    if not run_news_analysis():
        logger.error("뉴스 분석에 실패했습니다.")
        return False
    
    # 3. 거래 시스템 실행
    logger.info("💰 거래 시스템을 시작합니다...")
    if not run_trading_system(test_mode=False):
        logger.error("거래 시스템에 실패했습니다.")
        return False
    
    logger.info("✅ 전체 시스템이 성공적으로 완료되었습니다!")
    return True

def run_monitoring_mode():
    """모니터링 모드 실행"""
    logger.info("="*60)
    logger.info("📊 뉴스 모니터링 대시보드 실행")
    logger.info("="*60)
    
    # 1. 의존성 확인
    if not check_dependencies():
        return False
    
    # 2. 대시보드 실행
    dashboard_process = run_dashboard()
    if not dashboard_process:
        return False
    
    try:
        logger.info("대시보드가 실행 중입니다. Ctrl+C를 눌러 종료하세요.")
        dashboard_process.wait()
    except KeyboardInterrupt:
        logger.info("대시보드를 종료합니다...")
        dashboard_process.terminate()
    
    return True

def print_system_status():
    """시스템 상태 출력"""
    logger.info("="*60)
    logger.info("📋 뉴스 기반 주식 거래 시스템 상태")
    logger.info("="*60)
    
    # 파일 존재 확인
    files_to_check = [
        ("뉴스 수집기", "news_collector.py"),
        ("뉴스 분석기", "stock_news_analyzer.py"),
        ("거래 통합 시스템", "news_trading_integration.py"),
        ("모니터링 대시보드", "news_monitoring_dashboard.py"),
        ("키움 API", "kiwoom_api.py"),
        ("설정 파일", "config/news_config.json"),
        ("거래 설정", "config/news_trading_config.json")
    ]
    
    for name, file_path in files_to_check:
        if os.path.exists(file_path):
            logger.info(f"✅ {name}: {file_path}")
        else:
            logger.warning(f"❌ {name}: {file_path} (없음)")
    
    # 데이터 디렉토리 확인
    data_dirs = [
        ("뉴스 분석 데이터", "data/news_analysis"),
        ("거래 결과", "data/trading_results"),
        ("로그", "logs")
    ]
    
    for name, dir_path in data_dirs:
        if os.path.exists(dir_path):
            file_count = len(os.listdir(dir_path))
            logger.info(f"📁 {name}: {dir_path} ({file_count}개 파일)")
        else:
            logger.warning(f"📁 {name}: {dir_path} (없음)")
    
    # API 키 상태
    if check_api_keys():
        logger.info("🔑 네이버 API 키: 설정됨")
    else:
        logger.warning("🔑 네이버 API 키: 설정되지 않음")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="뉴스 기반 주식 거래 시스템 통합 실행 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python start_news_trading_system.py --test          # 종합 테스트 실행
  python start_news_trading_system.py --full          # 전체 시스템 실행
  python start_news_trading_system.py --monitor       # 모니터링 대시보드 실행
  python start_news_trading_system.py --status        # 시스템 상태 확인
        """
    )
    
    parser.add_argument("--test", action="store_true", 
                       help="종합 테스트 실행 (뉴스 분석 + 거래 시스템 테스트)")
    parser.add_argument("--full", action="store_true", 
                       help="전체 시스템 실행 (실제 거래 포함)")
    parser.add_argument("--monitor", action="store_true", 
                       help="웹 모니터링 대시보드 실행")
    parser.add_argument("--status", action="store_true", 
                       help="시스템 상태 확인")
    parser.add_argument("--host", default="localhost", 
                       help="대시보드 호스트 주소 (기본값: localhost)")
    parser.add_argument("--port", type=int, default=5000, 
                       help="대시보드 포트 번호 (기본값: 5000)")
    
    args = parser.parse_args()
    
    # 로그 설정
    logger.remove()
    logger.add(sys.stdout, level="INFO", 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # 명령어가 없으면 도움말 출력
    if not any([args.test, args.full, args.monitor, args.status]):
        parser.print_help()
        return
    
    try:
        if args.status:
            print_system_status()
        
        elif args.test:
            success = run_comprehensive_test()
            if success:
                logger.info("🎉 테스트가 성공적으로 완료되었습니다!")
            else:
                logger.error("❌ 테스트에 실패했습니다.")
                sys.exit(1)
        
        elif args.full:
            success = run_full_system()
            if success:
                logger.info("🎉 전체 시스템이 성공적으로 완료되었습니다!")
            else:
                logger.error("❌ 시스템 실행에 실패했습니다.")
                sys.exit(1)
        
        elif args.monitor:
            success = run_monitoring_mode()
            if not success:
                logger.error("❌ 모니터링 대시보드 실행에 실패했습니다.")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 