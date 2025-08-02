#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하이브리드 트레이딩 통합 실행 스크립트
뉴스 분석 + 기술적 분석 + 실제 매매 연동
"""

import sys
import time
import argparse
import subprocess
import signal
import os
import threading
from datetime import datetime
from loguru import logger

def setup_logging():
    """로깅 설정"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/hybrid_trading.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

def run_hybrid_analysis():
    """하이브리드 분석 실행"""
    try:
        logger.info("🔍 하이브리드 분석 시작")
        
        # 하이브리드 분석 실행
        result = subprocess.run([
            sys.executable, "hybrid_trading_system.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ 하이브리드 분석 완료")
            return True
        else:
            logger.error(f"❌ 하이브리드 분석 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"하이브리드 분석 실행 오류: {e}")
        return False

def check_system_status():
    """시스템 상태 확인"""
    try:
        logger.info("🔍 시스템 상태 확인")
        
        # 프로세스 확인
        processes = {
            'hybrid_dashboard': subprocess.run(["pgrep", "-f", "hybrid_dashboard.py"], 
                                             capture_output=True, text=True),
            'hybrid_auto_trader': subprocess.run(["pgrep", "-f", "hybrid_auto_trader.py"], 
                                               capture_output=True, text=True)
        }
        
        status = {}
        for name, result in processes.items():
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                status[name] = {
                    'running': True,
                    'pids': pids
                }
                logger.info(f"✅ {name}: 실행 중 (PID: {', '.join(pids)})")
            else:
                status[name] = {
                    'running': False,
                    'pids': []
                }
                logger.info(f"❌ {name}: 중지됨")
        
        # 데이터 파일 확인
        data_files = {
            'hybrid_analysis': os.path.exists('data/hybrid_analysis'),
            'logs': os.path.exists('logs')
        }
        
        for name, exists in data_files.items():
            if exists:
                logger.info(f"✅ {name}: 존재함")
            else:
                logger.warning(f"⚠️ {name}: 없음")
        
        return status
        
    except Exception as e:
        logger.error(f"상태 확인 오류: {e}")
        return {}

def stop_all_processes():
    """모든 프로세스 종료"""
    try:
        logger.info("🛑 모든 프로세스 종료")
        
        processes_to_kill = [
            "hybrid_dashboard.py",
            "hybrid_auto_trader.py",
            "hybrid_trading_system.py"
        ]
        
        for process in processes_to_kill:
            result = subprocess.run(["pkill", "-f", process], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ {process} 종료됨")
            else:
                logger.info(f"ℹ️ {process} 실행 중이 아님")
        
        time.sleep(2)
        
    except Exception as e:
        logger.error(f"프로세스 종료 오류: {e}")

def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.info(f"시그널 {signum} 수신, 시스템 종료 중...")
    stop_all_processes()
    sys.exit(0)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="하이브리드 트레이딩 통합 시스템")
    parser.add_argument('--mode', choices=['full', 'analysis', 'dashboard', 'trading', 'status', 'stop'], 
                       default='full', help="실행 모드")
    parser.add_argument('--interval', type=int, default=300, 
                       help="분석 간격 (초, 기본값: 300)")
    parser.add_argument('--auto-trade', action='store_true', 
                       help="자동매매 활성화")
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 하이브리드 트레이딩 시스템 시작")
    
    try:
        if args.mode == 'stop':
            stop_all_processes()
            return
        
        elif args.mode == 'status':
            check_system_status()
            return
        
        elif args.mode == 'analysis':
            # 분석만 실행
            run_hybrid_analysis()
            return
        
        else:
            logger.info(f"모드 '{args.mode}'는 아직 구현되지 않았습니다")
            logger.info("사용 가능한 모드: status, analysis, stop")
            return
    
    except Exception as e:
        logger.error(f"시스템 실행 오류: {e}")
        stop_all_processes()

if __name__ == "__main__":
    main() 