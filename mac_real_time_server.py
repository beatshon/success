#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
맥 전용 실시간 데이터 서버
윈도우 서버 없이 맥에서 모든 기능을 제공
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from loguru import logger

# 맥 전용 설정
import os
if hasattr(asyncio, 'set_event_loop_policy'):
    try:
        import asyncio.unix_events
        asyncio.set_event_loop_policy(asyncio.unix_events.DefaultEventLoopPolicy())
    except ImportError:
        pass

app = Flask(__name__)
CORS(app)

class MacRealTimeDataServer:
    """맥 전용 실시간 데이터 서버"""
    
    def __init__(self):
        self.is_running = False
        self.virtual_data_generator = None
        self.stock_data = {}
        self.portfolio_data = {}
        self.news_data = []
        self.signals_data = []
        
        # 설정 로드
        self.load_config()
        
        # 초기 데이터 생성
        self.initialize_data()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            config_path = "config/mac_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "data": {"stock_codes": ["005930", "000660", "035420"]},
                    "development": {"server_port": 8081}
                }
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            self.config = {"data": {"stock_codes": ["005930"]}, "development": {"server_port": 8081}}
    
    def initialize_data(self):
        """초기 데이터 생성"""
        stock_codes = self.config["data"]["stock_codes"]
        
        for code in stock_codes:
            self.stock_data[code] = {
                "current_price": random.uniform(50000, 200000),
                "change": random.uniform(-5000, 5000),
                "change_rate": random.uniform(-0.1, 0.1),
                "volume": random.randint(1000000, 10000000),
                "high": random.uniform(50000, 200000),
                "low": random.uniform(50000, 200000),
                "open": random.uniform(50000, 200000)
            }
        
        # 포트폴리오 데이터
        self.portfolio_data = {
            "total_value": 10000000,
            "total_profit": 500000,
            "profit_rate": 0.05,
            "positions": [
                {"code": "005930", "name": "삼성전자", "quantity": 10, "avg_price": 70000, "current_price": 75000, "profit": 50000},
                {"code": "000660", "name": "SK하이닉스", "quantity": 5, "avg_price": 120000, "current_price": 125000, "profit": 25000}
            ]
        }
        
        # 뉴스 데이터
        self.news_data = [
            {"title": "삼성전자 실적 호조", "sentiment": "positive", "timestamp": datetime.now().isoformat()},
            {"title": "반도체 시장 회복세", "sentiment": "positive", "timestamp": datetime.now().isoformat()},
            {"title": "글로벌 경제 불확실성", "sentiment": "negative", "timestamp": datetime.now().isoformat()}
        ]
        
        # 투자 신호
        self.signals_data = [
            {"code": "005930", "name": "삼성전자", "signal": "BUY", "confidence": 0.75, "target_price": 80000},
            {"code": "000660", "name": "SK하이닉스", "signal": "HOLD", "confidence": 0.60, "target_price": 130000}
        ]
    
    def update_virtual_data(self):
        """가상 데이터 업데이트"""
        for code in self.stock_data:
            current = self.stock_data[code]["current_price"]
            change = random.uniform(-current * 0.02, current * 0.02)
            new_price = current + change
            
            self.stock_data[code].update({
                "current_price": new_price,
                "change": change,
                "change_rate": change / current,
                "volume": random.randint(1000000, 10000000),
                "high": max(new_price, self.stock_data[code]["high"]),
                "low": min(new_price, self.stock_data[code]["low"])
            })
        
        # 포트폴리오 업데이트
        total_profit = sum(pos["profit"] for pos in self.portfolio_data["positions"])
        self.portfolio_data["total_profit"] = total_profit
        self.portfolio_data["profit_rate"] = total_profit / self.portfolio_data["total_value"]
    
    def start_virtual_data_generation(self):
        """가상 데이터 생성 시작"""
        self.is_running = True
        logger.info("가상 데이터 생성 시작")
    
    def stop_virtual_data_generation(self):
        """가상 데이터 생성 중지"""
        self.is_running = False
        logger.info("가상 데이터 생성 중지")

# 서버 인스턴스 생성
server = MacRealTimeDataServer()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('mac_dashboard.html')

@app.route('/api/status')
def get_status():
    """서버 상태 확인"""
    return jsonify({
        "status": "running",
        "mode": "mac_only",
        "timestamp": datetime.now().isoformat(),
        "virtual_data_running": server.is_running
    })

@app.route('/api/stock-data')
def get_stock_data():
    """주식 데이터 조회"""
    if server.is_running:
        server.update_virtual_data()
    return jsonify(server.stock_data)

@app.route('/api/portfolio')
def get_portfolio():
    """포트폴리오 데이터 조회"""
    return jsonify(server.portfolio_data)

@app.route('/api/news')
def get_news():
    """뉴스 데이터 조회"""
    return jsonify(server.news_data)

@app.route('/api/signals')
def get_signals():
    """투자 신호 조회"""
    return jsonify(server.signals_data)

@app.route('/api/start-virtual-data', methods=['POST'])
def start_virtual_data():
    """가상 데이터 생성 시작"""
    server.start_virtual_data_generation()
    return jsonify({"status": "success", "message": "가상 데이터 생성 시작"})

@app.route('/api/stop-virtual-data', methods=['POST'])
def stop_virtual_data():
    """가상 데이터 생성 중지"""
    server.stop_virtual_data_generation()
    return jsonify({"status": "success", "message": "가상 데이터 생성 중지"})

def main():
    """메인 실행 함수"""
    logger.info("맥 전용 실시간 데이터 서버 시작")
    
    port = server.config["development"]["server_port"]
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)

if __name__ == '__main__':
    main()
