#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 웹 서버 시작 스크립트
"""

import sys
import os
from loguru import logger

def start_server():
    """서버 시작"""
    try:
        logger.info("=== 통합 트렌드-주식 분석 서버 시작 ===")
        
        # 현재 디렉토리를 프로젝트 루트로 설정
        project_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_root)
        
        # 서버 import 및 시작
        from integrated_trend_stock_server import IntegratedTrendStockServer
        
        # 서버 인스턴스 생성
        server = IntegratedTrendStockServer(port=8086)
        
        logger.info("서버 초기화 완료")
        logger.info("웹 브라우저에서 http://localhost:8086 접속하세요")
        logger.info("서버를 중지하려면 Ctrl+C를 누르세요")
        
        # 서버 시작
        server.start()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_server() 