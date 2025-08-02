#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 실시간 통신 시스템 시작 스크립트
"""

import sys
import time
import threading
import signal
import argparse
from datetime import datetime
from loguru import logger

# 프로젝트 모듈 import
from websocket_server import WebSocketServer
from real_time_data_collector import RealTimeDataCollector, DataCollectionConfig

class WebSocketSystem:
    """WebSocket 실시간 통신 시스템 관리자"""
    
    def __init__(self, ws_port: int = 8084, api_port: int = 8083):
        self.ws_port = ws_port
        self.api_port = api_port
        self.ws_server = None
        self.collector = None
        self.running = False
        
        # 기본 종목 리스트 (KOSPI 대표 종목들)
        self.default_stocks = [
            '005930',  # 삼성전자
            '000660',  # SK하이닉스
            '035420',  # NAVER
            '051910',  # LG화학
            '006400',  # 삼성SDI
            '035720',  # 카카오
            '207940',  # 삼성바이오로직스
            '068270',  # 셀트리온
            '323410',  # 카카오뱅크
            '373220',  # LG에너지솔루션
            '005380',  # 현대차
            '000270',  # 기아
            '015760',  # 한국전력
            '017670',  # SK텔레콤
            '032830',  # 삼성생명
            '086790',  # 하나금융지주
            '105560',  # KB금융
            '055550',  # 신한지주
            '034020',  # 두산에너빌리티
            '028260'   # 삼성물산
        ]
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신. 시스템을 종료합니다.")
        self.stop()
        
    def start(self):
        """시스템 시작"""
        try:
            logger.info("WebSocket 실시간 통신 시스템 시작...")
            
            # 데이터 수집기 초기화
            config = DataCollectionConfig(
                update_interval=1.0,
                max_queue_size=10000,
                cache_duration=300,
                enable_monitoring=True
            )
            
            self.collector = RealTimeDataCollector(config)
            
            # WebSocket 서버 초기화
            self.ws_server = WebSocketServer(port=self.ws_port)
            self.ws_server.set_collector(self.collector)
            
            # 기본 종목 구독
            logger.info(f"기본 종목 {len(self.default_stocks)}개 구독 중...")
            self.collector.subscribe(self.default_stocks)
            
            # 데이터 수집 시작
            logger.info("데이터 수집 시작...")
            self.collector.start()
            
            # 모니터링 스레드 시작
            self.running = True
            monitor_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            monitor_thread.start()
            
            logger.info(f"WebSocket 실시간 통신 시스템이 시작되었습니다.")
            logger.info(f"WebSocket 서버: http://localhost:{self.ws_port}")
            logger.info(f"WebSocket 대시보드: http://localhost:{self.ws_port}")
            logger.info(f"기존 API 서버: http://localhost:{self.api_port}")
            logger.info("Ctrl+C로 종료할 수 있습니다.")
            
            # WebSocket 서버 시작 (블로킹)
            self.ws_server.start()
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            self.stop()
            raise
    
    def stop(self):
        """시스템 중지"""
        if not self.running:
            return
            
        logger.info("WebSocket 실시간 통신 시스템 종료 중...")
        self.running = False
        
        try:
            if self.collector:
                self.collector.stop()
            if self.ws_server:
                self.ws_server.stop()
            logger.info("시스템이 안전하게 종료되었습니다.")
        except Exception as e:
            logger.error(f"시스템 종료 중 오류: {e}")
    
    def _monitoring_worker(self):
        """모니터링 워커 스레드"""
        while self.running:
            try:
                # 30초마다 상태 로깅
                if self.collector:
                    stats = self.collector.get_stats()
                    
                    logger.info(f"WebSocket 시스템 상태 - "
                              f"수신: {stats.get('data_received', 0)}, "
                              f"처리: {stats.get('data_processed', 0)}, "
                              f"오류: {stats.get('errors', 0)}, "
                              f"구독: {stats.get('subscribed_count', 0)}개, "
                              f"클라이언트: {len(self.ws_server.clients) if self.ws_server else 0}개")
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(30)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="WebSocket 실시간 통신 시스템")
    parser.add_argument("--ws-port", type=int, default=8084, 
                       help="WebSocket 서버 포트 (기본값: 8084)")
    parser.add_argument("--api-port", type=int, default=8083, 
                       help="기존 API 서버 포트 (기본값: 8083)")
    parser.add_argument("--stocks", nargs='+', 
                       help="구독할 종목 코드 목록 (기본값: KOSPI 대표 종목들)")
    
    args = parser.parse_args()
    
    try:
        # 시스템 초기화
        system = WebSocketSystem(ws_port=args.ws_port, api_port=args.api_port)
        
        # 사용자 지정 종목이 있으면 설정
        if args.stocks:
            system.default_stocks = args.stocks
            logger.info(f"사용자 지정 종목 {len(args.stocks)}개 설정")
        
        # 시스템 시작
        system.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        system.stop()
    except Exception as e:
        logger.error(f"시스템 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 