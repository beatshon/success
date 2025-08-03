#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
맥 전용 개발 환경 설정 스크립트
윈도우 서버 없이 맥에서 모든 개발 작업을 수행할 수 있도록 설정
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from loguru import logger

class MacDevelopmentSetup:
    """맥 개발 환경 설정"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_file = self.project_root / "config" / "mac_config.json"
        self.setup_config()
    
    def setup_config(self):
        """맥 전용 설정 파일 생성"""
        config = {
            "development": {
                "mode": "mac_only",
                "server_port": 8081,
                "websocket_port": 8082,
                "debug": True
            },
            "data": {
                "use_virtual_data": True,
                "virtual_data_interval": 5,
                "stock_codes": ["005930", "000660", "035420", "051910", "006400"]
            },
            "trading": {
                "simulation_mode": True,
                "paper_trading": True,
                "max_positions": 10,
                "position_size": 0.1
            },
            "api": {
                "naver_api_enabled": False,
                "use_mock_data": True,
                "mock_data_quality": "high"
            }
        }
        
        # config 디렉토리 생성
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        # 설정 파일 저장
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"맥 전용 설정 파일 생성: {self.config_file}")
    
    def install_dependencies(self):
        """필요한 패키지 설치"""
        packages = [
            "flask",
            "flask-cors", 
            "requests",
            "pandas",
            "numpy",
            "loguru",
            "scikit-learn",
            "matplotlib",
            "seaborn",
            "plotly",
            "fastapi",
            "uvicorn[standard]",
            "websockets"
        ]
        
        logger.info("필요한 패키지 설치 중...")
        for package in packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                logger.info(f"✓ {package} 설치 완료")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠ {package} 설치 실패: {e}")
    
    def create_mac_optimized_files(self):
        """맥 최적화 파일들 생성"""
        
        # 1. 맥 전용 실시간 데이터 서버
        self.create_mac_real_time_server()
        
        # 2. 맥 전용 대시보드
        self.create_mac_dashboard()
        
        # 3. 맥 전용 테스트 스크립트
        self.create_mac_test_scripts()
        
        # 4. 맥 전용 실행 스크립트
        self.create_mac_run_scripts()
    
    def create_mac_real_time_server(self):
        """맥 전용 실시간 데이터 서버 생성"""
        server_code = '''#!/usr/bin/env python3
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
'''
        
        with open("mac_real_time_server.py", "w", encoding="utf-8") as f:
            f.write(server_code)
        
        logger.info("맥 전용 실시간 데이터 서버 생성 완료")
    
    def create_mac_dashboard(self):
        """맥 전용 대시보드 생성"""
        dashboard_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>맥 전용 투자 대시보드</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #f8f9fa; }
        .card { border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .status-running { background-color: #28a745; }
        .status-stopped { background-color: #dc3545; }
        .profit-positive { color: #28a745; }
        .profit-negative { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container-fluid mt-3">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">
                            🍎 맥 전용 투자 대시보드
                            <span class="status-indicator status-running" id="serverStatus"></span>
                            <small class="float-end" id="lastUpdate"></small>
                        </h4>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-3">
            <!-- 포트폴리오 요약 -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>📊 포트폴리오 요약</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <h6>총 자산</h6>
                                <h4 id="totalValue">₩0</h4>
                            </div>
                            <div class="col-6">
                                <h6>수익률</h6>
                                <h4 id="profitRate" class="profit-positive">0%</h4>
                            </div>
                        </div>
                        <div class="mt-3">
                            <h6>총 수익</h6>
                            <h4 id="totalProfit" class="profit-positive">₩0</h4>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 실시간 주가 -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>📈 실시간 주가</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>종목코드</th>
                                        <th>현재가</th>
                                        <th>변동</th>
                                        <th>거래량</th>
                                    </tr>
                                </thead>
                                <tbody id="stockTable">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-3">
            <!-- 투자 신호 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>🎯 투자 신호</h5>
                    </div>
                    <div class="card-body">
                        <div id="signalsList">
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 뉴스 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>📰 최신 뉴스</h5>
                    </div>
                    <div class="card-body">
                        <div id="newsList">
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 제어 패널 -->
        <div class="row mt-3">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>⚙️ 제어 패널</h5>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-success me-2" onclick="startVirtualData()">가상 데이터 시작</button>
                        <button class="btn btn-danger me-2" onclick="stopVirtualData()">가상 데이터 중지</button>
                        <button class="btn btn-primary" onclick="refreshData()">데이터 새로고침</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let updateInterval;
        
        // 페이지 로드 시 초기화
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            updateInterval = setInterval(refreshData, 5000); // 5초마다 업데이트
        });
        
        async function refreshData() {
            try {
                // 서버 상태 확인
                const statusResponse = await fetch('/api/status');
                const status = await statusResponse.json();
                
                // 주식 데이터
                const stockResponse = await fetch('/api/stock-data');
                const stockData = await stockResponse.json();
                
                // 포트폴리오 데이터
                const portfolioResponse = await fetch('/api/portfolio');
                const portfolio = await portfolioResponse.json();
                
                // 투자 신호
                const signalsResponse = await fetch('/api/signals');
                const signals = await signalsResponse.json();
                
                // 뉴스 데이터
                const newsResponse = await fetch('/api/news');
                const news = await newsResponse.json();
                
                // UI 업데이트
                updateUI(status, stockData, portfolio, signals, news);
                
            } catch (error) {
                console.error('데이터 로드 실패:', error);
            }
        }
        
        function updateUI(status, stockData, portfolio, signals, news) {
            // 서버 상태
            document.getElementById('serverStatus').className = 
                `status-indicator ${status.virtual_data_running ? 'status-running' : 'status-stopped'}`;
            
            // 마지막 업데이트 시간
            document.getElementById('lastUpdate').textContent = 
                new Date().toLocaleTimeString();
            
            // 포트폴리오 업데이트
            document.getElementById('totalValue').textContent = 
                `₩${portfolio.total_value.toLocaleString()}`;
            document.getElementById('totalProfit').textContent = 
                `₩${portfolio.total_profit.toLocaleString()}`;
            document.getElementById('profitRate').textContent = 
                `${(portfolio.profit_rate * 100).toFixed(2)}%`;
            
            // 수익률 색상
            const profitRateElement = document.getElementById('profitRate');
            const totalProfitElement = document.getElementById('totalProfit');
            if (portfolio.profit_rate >= 0) {
                profitRateElement.className = 'profit-positive';
                totalProfitElement.className = 'profit-positive';
            } else {
                profitRateElement.className = 'profit-negative';
                totalProfitElement.className = 'profit-negative';
            }
            
            // 주식 테이블 업데이트
            updateStockTable(stockData);
            
            // 투자 신호 업데이트
            updateSignalsList(signals);
            
            // 뉴스 업데이트
            updateNewsList(news);
        }
        
        function updateStockTable(stockData) {
            const tbody = document.getElementById('stockTable');
            tbody.innerHTML = '';
            
            Object.entries(stockData).forEach(([code, data]) => {
                const row = document.createElement('tr');
                const changeClass = data.change >= 0 ? 'profit-positive' : 'profit-negative';
                const changeSymbol = data.change >= 0 ? '+' : '';
                
                row.innerHTML = `
                    <td><strong>${code}</strong></td>
                    <td>₩${data.current_price.toLocaleString()}</td>
                    <td class="${changeClass}">${changeSymbol}${data.change.toLocaleString()}</td>
                    <td>${data.volume.toLocaleString()}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateSignalsList(signals) {
            const container = document.getElementById('signalsList');
            container.innerHTML = '';
            
            signals.forEach(signal => {
                const signalElement = document.createElement('div');
                signalElement.className = 'alert alert-info mb-2';
                signalElement.innerHTML = `
                    <strong>${signal.name} (${signal.code})</strong><br>
                    신호: <span class="badge bg-primary">${signal.signal}</span>
                    신뢰도: ${(signal.confidence * 100).toFixed(1)}%
                    목표가: ₩${signal.target_price.toLocaleString()}
                `;
                container.appendChild(signalElement);
            });
        }
        
        function updateNewsList(news) {
            const container = document.getElementById('newsList');
            container.innerHTML = '';
            
            news.forEach(item => {
                const newsElement = document.createElement('div');
                newsElement.className = 'alert alert-secondary mb-2';
                const sentimentClass = item.sentiment === 'positive' ? 'text-success' : 'text-danger';
                newsElement.innerHTML = `
                    <div class="${sentimentClass}"><strong>${item.title}</strong></div>
                    <small class="text-muted">${new Date(item.timestamp).toLocaleString()}</small>
                `;
                container.appendChild(newsElement);
            });
        }
        
        async function startVirtualData() {
            try {
                await fetch('/api/start-virtual-data', { method: 'POST' });
                alert('가상 데이터 생성이 시작되었습니다.');
            } catch (error) {
                alert('가상 데이터 시작 실패: ' + error.message);
            }
        }
        
        async function stopVirtualData() {
            try {
                await fetch('/api/stop-virtual-data', { method: 'POST' });
                alert('가상 데이터 생성이 중지되었습니다.');
            } catch (error) {
                alert('가상 데이터 중지 실패: ' + error.message);
            }
        }
    </script>
</body>
</html>'''
        
        # templates 디렉토리 생성
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        with open(templates_dir / "mac_dashboard.html", "w", encoding="utf-8") as f:
            f.write(dashboard_html)
        
        logger.info("맥 전용 대시보드 생성 완료")
    
    def create_mac_test_scripts(self):
        """맥 전용 테스트 스크립트 생성"""
        test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
맥 전용 테스트 스크립트
모든 기능을 맥에서 테스트
"""

import requests
import json
import time
from datetime import datetime
from loguru import logger

def test_mac_server():
    """맥 서버 테스트"""
    base_url = "http://localhost:8081"
    
    logger.info("맥 전용 서버 테스트 시작")
    
    try:
        # 1. 서버 상태 확인
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            status = response.json()
            logger.info(f"✓ 서버 상태: {status}")
        else:
            logger.error("✗ 서버 상태 확인 실패")
            return False
        
        # 2. 가상 데이터 시작
        response = requests.post(f"{base_url}/api/start-virtual-data")
        if response.status_code == 200:
            logger.info("✓ 가상 데이터 시작 성공")
        else:
            logger.error("✗ 가상 데이터 시작 실패")
        
        # 3. 주식 데이터 확인
        response = requests.get(f"{base_url}/api/stock-data")
        if response.status_code == 200:
            stock_data = response.json()
            logger.info(f"✓ 주식 데이터: {len(stock_data)}개 종목")
        else:
            logger.error("✗ 주식 데이터 조회 실패")
        
        # 4. 포트폴리오 데이터 확인
        response = requests.get(f"{base_url}/api/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            logger.info(f"✓ 포트폴리오: 총 자산 {portfolio['total_value']:,}원")
        else:
            logger.error("✗ 포트폴리오 데이터 조회 실패")
        
        # 5. 투자 신호 확인
        response = requests.get(f"{base_url}/api/signals")
        if response.status_code == 200:
            signals = response.json()
            logger.info(f"✓ 투자 신호: {len(signals)}개")
        else:
            logger.error("✗ 투자 신호 조회 실패")
        
        # 6. 뉴스 데이터 확인
        response = requests.get(f"{base_url}/api/news")
        if response.status_code == 200:
            news = response.json()
            logger.info(f"✓ 뉴스 데이터: {len(news)}개")
        else:
            logger.error("✗ 뉴스 데이터 조회 실패")
        
        logger.info("맥 전용 서버 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        return False

def test_data_generation():
    """데이터 생성 테스트"""
    logger.info("데이터 생성 테스트 시작")
    
    # 가상 데이터 생성 테스트
    import random
    import pandas as pd
    
    # 주식 데이터 생성
    stock_codes = ["005930", "000660", "035420", "051910", "006400"]
    data = {}
    
    for code in stock_codes:
        prices = []
        for i in range(100):
            if i == 0:
                price = random.uniform(50000, 200000)
            else:
                change = random.uniform(-0.02, 0.02)
                price = prices[-1] * (1 + change)
            prices.append(price)
        
        data[code] = prices
    
    df = pd.DataFrame(data)
    logger.info(f"✓ 가상 주가 데이터 생성: {df.shape}")
    
    # 포트폴리오 데이터 생성
    portfolio = {
        "total_value": 10000000,
        "positions": []
    }
    
    for code in stock_codes[:3]:
        position = {
            "code": code,
            "quantity": random.randint(1, 10),
            "avg_price": random.uniform(50000, 200000),
            "current_price": random.uniform(50000, 200000)
        }
        position["profit"] = (position["current_price"] - position["avg_price"]) * position["quantity"]
        portfolio["positions"].append(position)
    
    portfolio["total_profit"] = sum(pos["profit"] for pos in portfolio["positions"])
    portfolio["profit_rate"] = portfolio["total_profit"] / portfolio["total_value"]
    
    logger.info(f"✓ 포트폴리오 데이터 생성: 수익률 {portfolio['profit_rate']:.2%}")
    
    return True

if __name__ == "__main__":
    logger.info("맥 전용 테스트 시작")
    
    # 데이터 생성 테스트
    test_data_generation()
    
    # 서버 테스트 (서버가 실행 중일 때)
    try:
        test_mac_server()
    except requests.exceptions.ConnectionError:
        logger.warning("서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요.")
        logger.info("서버 시작 명령어: python mac_real_time_server.py")
    
    logger.info("맥 전용 테스트 완료")
'''
        
        with open("test_mac_environment.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        
        logger.info("맥 전용 테스트 스크립트 생성 완료")
    
    def create_mac_run_scripts(self):
        """맥 전용 실행 스크립트 생성"""
        
        # 실행 스크립트
        run_script = '''#!/bin/bash
# 맥 전용 실행 스크립트

echo "🍎 맥 전용 투자 시스템 시작"
echo "================================"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "가상환경이 없습니다. 새로 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask flask-cors requests pandas numpy loguru
fi

# 서버 시작
echo "실시간 데이터 서버 시작 중..."
python mac_real_time_server.py
'''
        
        with open("run_mac_system.sh", "w", encoding="utf-8") as f:
            f.write(run_script)
        
        # 실행 권한 부여
        os.chmod("run_mac_system.sh", 0o755)
        
        logger.info("맥 전용 실행 스크립트 생성 완료")
    
    def run_setup(self):
        """전체 설정 실행"""
        logger.info("맥 전용 개발 환경 설정 시작")
        
        # 1. 패키지 설치
        self.install_dependencies()
        
        # 2. 맥 최적화 파일 생성
        self.create_mac_optimized_files()
        
        logger.info("✅ 맥 전용 개발 환경 설정 완료!")
        logger.info("다음 명령어로 시스템을 시작하세요:")
        logger.info("  python mac_real_time_server.py")
        logger.info("  또는")
        logger.info("  ./run_mac_system.sh")

def main():
    """메인 실행 함수"""
    setup = MacDevelopmentSetup()
    setup.run_setup()

if __name__ == "__main__":
    main() 