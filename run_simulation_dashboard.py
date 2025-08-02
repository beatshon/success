#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from loguru import logger

def main():
    """시뮬레이션 대시보드를 실행합니다."""
    try:
        # 필요한 모듈 확인
        try:
            from simulation_dashboard import SimulationDashboard
        except ImportError as e:
            logger.error(f"시뮬레이션 대시보드 모듈을 불러올 수 없습니다: {e}")
            logger.info("필요한 패키지를 설치해주세요: pip install flask plotly pandas numpy loguru")
            return
        
        # 시뮬레이션 데이터 확인
        data_dir = "data/simulation_results"
        if not os.path.exists(data_dir):
            logger.warning("시뮬레이션 데이터 디렉토리가 존재하지 않습니다.")
            logger.info("먼저 시뮬레이션을 실행해주세요: python simple_simulation.py")
            return
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            logger.warning("시뮬레이션 데이터 파일이 없습니다.")
            logger.info("먼저 시뮬레이션을 실행해주세요: python simple_simulation.py")
            return
        
        logger.info(f"시뮬레이션 데이터 파일 {len(csv_files)}개 발견")
        
        # 대시보드 시작
        dashboard = SimulationDashboard()
        logger.info("시뮬레이션 대시보드를 시작합니다...")
        logger.info("브라우저에서 http://localhost:8083 을 열어주세요")
        
        dashboard.start_dashboard(host='0.0.0.0', port=8083, debug=False)
        
    except KeyboardInterrupt:
        logger.info("시뮬레이션 대시보드가 종료되었습니다.")
    except Exception as e:
        logger.error(f"시뮬레이션 대시보드 실행 실패: {e}")

if __name__ == "__main__":
    main() 