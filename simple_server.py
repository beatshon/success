#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트용 Flask 서버
AWS EC2 배포 테스트용
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# 간단한 HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>키움 트레이딩 시스템 - AWS EC2 배포 성공!</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
        h1 { text-align: center; color: #fff; margin-bottom: 30px; }
        .status { background: rgba(0,255,0,0.2); padding: 15px; border-radius: 10px; margin: 20px 0; }
        .info { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0; }
        .feature { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin: 5px 0; }
        .timestamp { text-align: center; font-size: 0.9em; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 키움 트레이딩 시스템</h1>
        <div class="status">
            <h2>✅ AWS EC2 클라우드 배포 성공!</h2>
            <p>24시간 운영되는 자동매매 시스템이 성공적으로 배포되었습니다.</p>
        </div>
        
        <div class="info">
            <h3>📊 시스템 정보</h3>
            <div class="feature">🖥️ 서버: AWS EC2 t3.micro</div>
            <div class="feature">🌐 IP 주소: {{ ip_address }}</div>
            <div class="feature">🐳 컨테이너: Docker</div>
            <div class="feature">⚡ 상태: 정상 운영 중</div>
        </div>
        
        <div class="info">
            <h3>🎯 주요 기능</h3>
            <div class="feature">📈 실시간 주식 데이터 수집</div>
            <div class="feature">🤖 AI 기반 투자 신호 생성</div>
            <div class="feature">📊 포트폴리오 최적화</div>
            <div class="feature">🔔 실시간 알림 시스템</div>
            <div class="feature">📱 웹 대시보드</div>
        </div>
        
        <div class="info">
            <h3>📈 실시간 데이터</h3>
            <div class="feature">삼성전자: {{ samsung_price }}원 ({{ samsung_change }})</div>
            <div class="feature">SK하이닉스: {{ sk_price }}원 ({{ sk_change }})</div>
            <div class="feature">LG에너지솔루션: {{ lg_price }}원 ({{ lg_change }})</div>
        </div>
        
        <div class="timestamp">
            마지막 업데이트: {{ timestamp }}
        </div>
    </div>
    
    <script>
        // 5초마다 페이지 새로고침
        setTimeout(function() {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """메인 페이지"""
    # 가상 주식 데이터 생성
    samsung_price = random.randint(70000, 80000)
    sk_price = random.randint(120000, 130000)
    lg_price = random.randint(400000, 450000)
    
    samsung_change = f"+{random.randint(1000, 3000)}" if random.random() > 0.5 else f"-{random.randint(1000, 3000)}"
    sk_change = f"+{random.randint(2000, 5000)}" if random.random() > 0.5 else f"-{random.randint(2000, 5000)}"
    lg_change = f"+{random.randint(5000, 10000)}" if random.random() > 0.5 else f"-{random.randint(5000, 10000)}"
    
    return render_template_string(HTML_TEMPLATE, 
                                ip_address="43.202.66.120",
                                samsung_price=samsung_price,
                                sk_price=sk_price,
                                lg_price=lg_price,
                                samsung_change=samsung_change,
                                sk_change=sk_change,
                                lg_change=lg_change,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/status')
def status():
    """API 상태 확인"""
    return jsonify({
        "status": "running",
        "message": "키움 트레이딩 시스템이 정상적으로 운영 중입니다.",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "deployment": "AWS EC2",
        "container": "Docker"
    })

@app.route('/api/stock-data')
def stock_data():
    """주식 데이터 API"""
    return jsonify({
        "005930": {
            "name": "삼성전자",
            "price": random.randint(70000, 80000),
            "change": random.randint(-3000, 3000),
            "volume": random.randint(1000000, 10000000)
        },
        "000660": {
            "name": "SK하이닉스",
            "price": random.randint(120000, 130000),
            "change": random.randint(-5000, 5000),
            "volume": random.randint(500000, 5000000)
        },
        "035420": {
            "name": "LG에너지솔루션",
            "price": random.randint(400000, 450000),
            "change": random.randint(-10000, 10000),
            "volume": random.randint(200000, 2000000)
        }
    })

@app.route('/api/portfolio')
def portfolio():
    """포트폴리오 데이터 API"""
    return jsonify({
        "total_value": 10000000,
        "total_profit": random.randint(300000, 700000),
        "profit_rate": random.uniform(0.03, 0.07),
        "positions": [
            {
                "code": "005930",
                "name": "삼성전자",
                "quantity": 10,
                "avg_price": 70000,
                "current_price": 75000,
                "profit": 50000
            },
            {
                "code": "000660",
                "name": "SK하이닉스",
                "quantity": 5,
                "avg_price": 120000,
                "current_price": 125000,
                "profit": 25000
            }
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False) 