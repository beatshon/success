#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
윈도우 서버용 API 서버 실행 스크립트
맥에서 작업한 파일을 윈도우 서버에서 API 테스트할 때 사용
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

# Flask 및 관련 라이브러리
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 설정 파일 로드
try:
    from config.kiwoom_api_keys import *
    from config.kiwoom_config import *
except ImportError as e:
    print(f"설정 파일 로드 실패: {e}")
    print("config 폴더의 설정 파일을 확인해주세요.")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/windows_api_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask 앱 생성
app = Flask(__name__)
CORS(app)  # CORS 활성화

# 서버 상태
server_status = {
    "start_time": datetime.now().isoformat(),
    "status": "running",
    "requests_count": 0,
    "last_request": None
}

class WindowsAPIServer:
    def __init__(self):
        self.port = 8080
        self.host = "0.0.0.0"
        self.debug = True
        
        # API 엔드포인트 등록
        self.register_routes()
    
    def register_routes(self):
        """API 라우트 등록"""
        
        @app.route('/')
        def home():
            """홈페이지"""
            return jsonify({
                "message": "윈도우 서버 API 서버",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route('/status')
        def status():
            """서버 상태 확인"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            return jsonify({
                "status": "running",
                "uptime": str(datetime.now() - datetime.fromisoformat(server_status["start_time"])),
                "requests_count": server_status["requests_count"],
                "last_request": server_status["last_request"]
            })
        
        @app.route('/api/account/info')
        def account_info():
            """계좌 정보 조회 (모의 데이터)"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            # 모의 계좌 정보
            account_data = {
                "account_number": "1234567890",
                "account_name": "테스트 계좌",
                "balance": 10000000,
                "available_balance": 9500000,
                "currency": "KRW",
                "last_updated": datetime.now().isoformat()
            }
            
            return jsonify(account_data)
        
        @app.route('/api/stock/price')
        def stock_price():
            """주식 시세 조회 (모의 데이터)"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            stock_code = request.args.get('code', '005930')
            
            # 모의 주식 데이터
            stock_data = {
                "code": stock_code,
                "name": "삼성전자" if stock_code == "005930" else f"주식{stock_code}",
                "current_price": 75000,
                "change": 1500,
                "change_rate": 2.04,
                "volume": 15000000,
                "market_cap": 450000000000000,
                "last_updated": datetime.now().isoformat()
            }
            
            return jsonify(stock_data)
        
        @app.route('/api/order/available')
        def order_available():
            """주문 가능 금액 조회 (모의 데이터)"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            available_data = {
                "available_amount": 9500000,
                "order_limit": 5000000,
                "daily_order_count": 0,
                "daily_order_limit": 100,
                "last_updated": datetime.now().isoformat()
            }
            
            return jsonify(available_data)
        
        @app.route('/api/realtime/status')
        def realtime_status():
            """실시간 데이터 서버 상태"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            return jsonify({
                "status": "connected",
                "connected_stocks": ["005930", "000660", "035420"],
                "last_update": datetime.now().isoformat()
            })
        
        @app.route('/api/news/status')
        def news_status():
            """뉴스 분석 서버 상태"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            return jsonify({
                "status": "active",
                "last_collected": datetime.now().isoformat(),
                "total_articles": 150,
                "analyzed_today": 25
            })
        
        @app.route('/api/ml/status')
        def ml_status():
            """딥러닝 시스템 상태"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            return jsonify({
                "status": "ready",
                "model_loaded": True,
                "last_prediction": datetime.now().isoformat(),
                "accuracy": 0.85
            })
        
        @app.route('/api/test/connection')
        def test_connection():
            """연결 테스트"""
            server_status["requests_count"] += 1
            server_status["last_request"] = datetime.now().isoformat()
            
            return jsonify({
                "message": "연결 성공",
                "timestamp": datetime.now().isoformat(),
                "server_info": {
                    "host": self.host,
                    "port": self.port,
                    "python_version": sys.version
                }
            })
        
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "API 엔드포인트를 찾을 수 없습니다",
                "available_endpoints": [
                    "/",
                    "/status",
                    "/api/account/info",
                    "/api/stock/price",
                    "/api/order/available",
                    "/api/realtime/status",
                    "/api/news/status",
                    "/api/ml/status",
                    "/api/test/connection"
                ]
            }), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "error": "서버 내부 오류가 발생했습니다",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def start_server(self):
        """API 서버 시작"""
        logger.info("=" * 50)
        logger.info("윈도우 서버 API 서버 시작")
        logger.info("=" * 50)
        logger.info(f"서버 주소: http://{self.host}:{self.port}")
        logger.info(f"디버그 모드: {self.debug}")
        logger.info("=" * 50)
        
        try:
            # logs 디렉토리 생성
            os.makedirs("logs", exist_ok=True)
            
            # Flask 서버 실행
            app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                threaded=True
            )
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            sys.exit(1)

def main():
    """메인 함수"""
    print("윈도우 서버 API 서버 시작 중...")
    
    # API 서버 생성 및 시작
    server = WindowsAPIServer()
    server.start_server()

if __name__ == "__main__":
    main() 