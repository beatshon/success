#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 뉴스 분석 대시보드
키움 API 의존성 없이 뉴스 분석 결과만 표시
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import pandas as pd

# Flask 웹 프레임워크
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask가 설치되지 않아 웹 대시보드를 사용할 수 없습니다.")

# 로컬 모듈 임포트 (키움 API 제외)
from news_collector import NaverNewsCollector, NewsItem
from stock_news_analyzer import StockNewsAnalyzer, StockAnalysis

@dataclass
class DashboardData:
    """대시보드 데이터 클래스"""
    timestamp: str
    total_news: int
    analyzed_stocks: int
    top_stocks: List[Dict]
    recent_news: List[Dict]
    market_sentiment: float
    risk_alerts: List[str]

class SimpleNewsDashboard:
    """간단한 뉴스 분석 대시보드"""
    
    def __init__(self, config_file: str = "config/news_config.json"):
        """
        대시보드 초기화
        
        Args:
            config_file: 설정 파일 경로
        """
        if not FLASK_AVAILABLE:
            logger.error("Flask가 설치되지 않아 대시보드를 실행할 수 없습니다.")
            logger.info("설치 명령어: pip install flask flask-socketio")
            return
        
        self.config = self._load_config(config_file)
        self.news_collector = None
        self.news_analyzer = StockNewsAnalyzer()
        self.dashboard_data = None
        self.is_running = False
        
        # Flask 앱 초기화
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'simple_news_dashboard_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 라우트 설정
        self._setup_routes()
        
        # 로그 설정
        self._setup_logging()
        
        logger.info("간단한 뉴스 분석 대시보드 초기화 완료")
    
    def _load_config(self, config_file: str) -> Dict:
        """설정 파일 로드"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"설정 파일 로드 완료: {config_file}")
            else:
                config = {}
                logger.warning(f"설정 파일을 찾을 수 없습니다: {config_file}")
            
            return config
            
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    def _setup_logging(self):
        """로깅 설정"""
        # 로그 디렉토리 생성
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일 설정
        log_file = f"{log_dir}/simple_dashboard_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 기존 핸들러 제거
        logger.remove()
        
        # 콘솔 출력
        logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        
        # 파일 출력
        logger.add(log_file, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", rotation="1 day", retention="30 days")
    
    def _setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/')
        def index():
            """메인 대시보드 페이지"""
            return render_template('simple_dashboard.html')
        
        @self.app.route('/api/dashboard-data')
        def get_dashboard_data():
            """대시보드 데이터 API"""
            if self.dashboard_data:
                return jsonify(asdict(self.dashboard_data))
            else:
                return jsonify({"error": "데이터가 없습니다."})
        
        @self.app.route('/api/refresh')
        def refresh_data():
            """데이터 새로고침 API"""
            try:
                self._update_dashboard_data()
                return jsonify({"success": True, "message": "데이터가 새로고침되었습니다."})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/news-analysis')
        def get_news_analysis():
            """뉴스 분석 결과 API"""
            try:
                analysis = self._get_latest_news_analysis()
                return jsonify(analysis)
            except Exception as e:
                return jsonify({"error": str(e)})
        
        @self.socketio.on('connect')
        def handle_connect():
            """클라이언트 연결 처리"""
            logger.info("클라이언트가 대시보드에 연결되었습니다.")
            emit('status', {'message': '대시보드에 연결되었습니다.'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """클라이언트 연결 해제 처리"""
            logger.info("클라이언트가 대시보드에서 연결 해제되었습니다.")
    
    def _update_dashboard_data(self):
        """대시보드 데이터 업데이트"""
        try:
            # 뉴스 수집기 초기화 (필요한 경우)
            if not self.news_collector:
                client_id = self.config.get("naver_api", {}).get("client_id")
                client_secret = self.config.get("naver_api", {}).get("client_secret")
                
                if client_id and client_secret and client_id != "your_naver_client_id":
                    self.news_collector = NaverNewsCollector(client_id, client_secret)
                else:
                    logger.warning("네이버 API 키가 설정되지 않아 기존 분석 결과를 사용합니다.")
            
            # 기존 분석 결과 사용
            stock_analysis = self._get_latest_news_analysis()
            
            if not stock_analysis:
                logger.warning("뉴스 분석 결과가 없습니다.")
                return
            
            # 상위 종목 추출
            top_stocks = []
            for stock in stock_analysis.get("analysis", []):
                if stock["investment_score"] > 30:  # 30점 이상만
                    top_stocks.append({
                        "stock_code": stock["stock_code"],
                        "stock_name": stock["stock_name"],
                        "investment_score": stock["investment_score"],
                        "news_count": stock["news_count"],
                        "sentiment_score": stock["sentiment_score"],
                        "recommendation": stock["recommendation"],
                        "risk_level": stock["risk_level"],
                        "recent_news": stock.get("recent_news", [])
                    })
            
            # 상위 10개만 선택
            top_stocks.sort(key=lambda x: x["investment_score"], reverse=True)
            top_stocks = top_stocks[:10]
            
            # 시장 감정 점수 계산
            total_sentiment = sum(stock["sentiment_score"] for stock in stock_analysis.get("analysis", []))
            market_sentiment = total_sentiment / len(stock_analysis.get("analysis", [])) if stock_analysis.get("analysis") else 0.0
            
            # 위험 알림 생성
            risk_alerts = []
            for stock in stock_analysis.get("analysis", []):
                if stock["risk_level"] == "High":
                    risk_alerts.append(f"{stock['stock_name']}: 높은 위험도 감지")
                if stock["investment_score"] < 20:
                    risk_alerts.append(f"{stock['stock_name']}: 낮은 투자 점수")
            
            # 대시보드 데이터 생성
            self.dashboard_data = DashboardData(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_news=sum(stock["news_count"] for stock in stock_analysis.get("analysis", [])),
                analyzed_stocks=len(stock_analysis.get("analysis", [])),
                top_stocks=top_stocks,
                recent_news=[],  # 간단한 버전에서는 생략
                market_sentiment=market_sentiment,
                risk_alerts=risk_alerts
            )
            
            # 실시간 업데이트 전송
            self.socketio.emit('dashboard_update', asdict(self.dashboard_data))
            
            logger.info("대시보드 데이터 업데이트 완료")
            
        except Exception as e:
            logger.error(f"대시보드 데이터 업데이트 실패: {e}")
    
    def _get_latest_news_analysis(self) -> Dict:
        """최신 뉴스 분석 결과 조회"""
        try:
            # 최신 분석 결과 파일 찾기
            analysis_dir = "data/news_analysis"
            if not os.path.exists(analysis_dir):
                return {}
            
            files = [f for f in os.listdir(analysis_dir) if f.startswith("stock_analysis_") and f.endswith(".csv")]
            if not files:
                return {}
            
            # 가장 최신 파일 읽기
            latest_file = max(files)
            file_path = os.path.join(analysis_dir, latest_file)
            
            # CSV 파일 읽기 (오류 처리 강화)
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig', lineterminator='\n')
            except Exception as csv_error:
                logger.error(f"CSV 파일 읽기 실패: {csv_error}")
                # 다른 인코딩으로 시도
                try:
                    df = pd.read_csv(file_path, encoding='utf-8', lineterminator='\n')
                except:
                    df = pd.read_csv(file_path, encoding='cp949', lineterminator='\n')
            
            # 분석 결과 반환
            analysis_results = []
            for _, row in df.iterrows():
                try:
                    # 뉴스 제목과 링크 파싱
                    recent_news = []
                    if "recent_news_links" in row and pd.notna(row["recent_news_links"]):
                        links_str = str(row["recent_news_links"]).strip()
                        if links_str and links_str != "nan" and links_str != "":
                            news_items = [item.strip() for item in links_str.split(" | ") if item.strip()]
                            for news_item in news_items:
                                if "|" in news_item:
                                    title, link = news_item.split("|", 1)
                                    recent_news.append({"title": title.strip(), "link": link.strip()})
                                else:
                                    # 기존 형식 (링크만 있는 경우)
                                    recent_news.append({"title": f"뉴스 {len(recent_news)+1}", "link": news_item})
                            stock_name = str(row["stock_name"])
                            logger.info(f"파싱된 뉴스: {stock_name} - {len(recent_news)}개 뉴스")
                    
                    analysis_results.append({
                        "stock_code": str(row["stock_code"]),
                        "stock_name": str(row["stock_name"]),
                        "news_count": int(row["news_count"]),
                        "investment_score": float(row["investment_score"]),
                        "sentiment_score": float(row["sentiment_score"]),
                        "recommendation": str(row["recommendation"]),
                        "risk_level": str(row["risk_level"]),
                        "recent_news": recent_news
                    })
                except Exception as row_error:
                    logger.error(f"행 처리 실패: {row_error}, 행: {row}")
                    continue
            
            logger.info(f"뉴스 분석 결과 로드 완료: {len(analysis_results)}개 종목")
            return {"analysis": analysis_results}
            
        except Exception as e:
            logger.error(f"뉴스 분석 결과 조회 실패: {e}")
            return {}
    
    def start_monitoring(self, interval: int = 300):
        """
        모니터링 시작
        
        Args:
            interval: 업데이트 간격 (초)
        """
        if not FLASK_AVAILABLE:
            logger.error("Flask가 설치되지 않아 모니터링을 시작할 수 없습니다.")
            return
        
        self.is_running = True
        
        def monitoring_loop():
            """모니터링 루프"""
            while self.is_running:
                try:
                    self._update_dashboard_data()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"모니터링 루프 오류: {e}")
                    time.sleep(60)  # 오류 시 1분 대기
        
        # 모니터링 스레드 시작
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        logger.info(f"모니터링이 시작되었습니다. (업데이트 간격: {interval}초)")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("모니터링이 중지되었습니다.")
    
    def run_dashboard(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """
        대시보드 실행
        
        Args:
            host: 호스트 주소
            port: 포트 번호
            debug: 디버그 모드
        """
        if not FLASK_AVAILABLE:
            logger.error("Flask가 설치되지 않아 대시보드를 실행할 수 없습니다.")
            return
        
        try:
            # 초기 데이터 로드
            self._update_dashboard_data()
            
            # 모니터링 시작
            self.start_monitoring()
            
            logger.info(f"대시보드가 시작되었습니다: http://{host}:{port}")
            
            # Flask 앱 실행
            self.socketio.run(self.app, host=host, port=port, debug=debug)
            
        except Exception as e:
            logger.error(f"대시보드 실행 실패: {e}")
        finally:
            self.stop_monitoring()

def create_simple_dashboard_template():
    """간단한 대시보드 HTML 템플릿 생성"""
    template_dir = "templates"
    os.makedirs(template_dir, exist_ok=True)
    
    html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>뉴스 분석 대시보드</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .status-item {
            text-align: center;
        }
        
        .status-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .status-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .card h3 {
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .stock-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .stock-info {
            flex: 1;
        }
        
        .stock-name {
            font-weight: bold;
            color: #333;
        }
        
        .stock-code {
            font-size: 12px;
            color: #666;
        }
        
        .stock-score {
            text-align: right;
        }
        
        .score-value {
            font-size: 18px;
            font-weight: bold;
            color: #28a745;
        }
        
        .alert-item {
            padding: 10px;
            margin: 5px 0;
            background: #f8d7da;
            border-radius: 8px;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        
        .chart-container {
            height: 300px;
            margin-top: 15px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .recommendation {
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }
        
        .recommendation.strong-buy {
            background: #28a745;
        }
        
        .recommendation.buy {
            background: #17a2b8;
        }
        
        .recommendation.hold {
            background: #ffc107;
            color: #333;
        }
        
        .recommendation.sell {
            background: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 뉴스 분석 대시보드</h1>
            <p>실시간 뉴스 분석 결과 모니터링</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-value" id="total-news">-</div>
                <div class="status-label">총 뉴스 수</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="analyzed-stocks">-</div>
                <div class="status-label">분석 종목</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="market-sentiment">-</div>
                <div class="status-label">시장 감정</div>
            </div>
            <div class="status-item">
                <button class="refresh-btn" onclick="refreshData()">🔄 새로고침</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📈 상위 투자 종목</h3>
                <div id="top-stocks">
                    <div class="loading">데이터를 불러오는 중...</div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚠️ 위험 알림</h3>
                <div id="risk-alerts">
                    <div class="loading">데이터를 불러오는 중...</div>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 투자 점수 분포</h3>
                <div class="chart-container">
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Socket.IO 연결
        const socket = io();
        
        // 차트 객체
        let scoreChart = null;
        
        // 페이지 로드 시 데이터 로드
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            initializeChart();
        });
        
        // 실시간 업데이트 수신
        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
        });
        
        // 상태 업데이트 수신
        socket.on('status', function(data) {
            console.log('Status:', data.message);
        });
        
        function loadDashboardData() {
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error:', data.error);
                        return;
                    }
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Error loading data:', error);
                });
        }
        
        function updateDashboard(data) {
            // 상태 바 업데이트
            document.getElementById('total-news').textContent = data.total_news || 0;
            document.getElementById('analyzed-stocks').textContent = data.analyzed_stocks || 0;
            document.getElementById('market-sentiment').textContent = (data.market_sentiment || 0).toFixed(2);
            
            // 상위 종목 업데이트
            updateTopStocks(data.top_stocks || []);
            
            // 위험 알림 업데이트
            updateRiskAlerts(data.risk_alerts || []);
            
            // 차트 업데이트
            updateChart(data.top_stocks || []);
        }
        
        function updateTopStocks(stocks) {
            const container = document.getElementById('top-stocks');
            
            if (stocks.length === 0) {
                container.innerHTML = '<div class="loading">데이터가 없습니다.</div>';
                return;
            }
            
            container.innerHTML = stocks.map(stock => {
                const recClass = getRecommendationClass(stock.recommendation);
                return `
                    <div class="stock-item">
                        <div class="stock-info">
                            <div class="stock-name">${stock.stock_name}</div>
                            <div class="stock-code">${stock.stock_code}</div>
                        </div>
                        <div class="stock-score">
                            <div class="score-value">${stock.investment_score.toFixed(1)}</div>
                            <div class="recommendation ${recClass}">${stock.recommendation}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function getRecommendationClass(recommendation) {
            if (recommendation.includes('강력 매수')) return 'strong-buy';
            if (recommendation.includes('매수')) return 'buy';
            if (recommendation.includes('관망')) return 'hold';
            if (recommendation.includes('매도')) return 'sell';
            return 'hold';
        }
        
        function updateRiskAlerts(alerts) {
            const container = document.getElementById('risk-alerts');
            
            if (alerts.length === 0) {
                container.innerHTML = '<div class="loading">위험 알림이 없습니다.</div>';
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div class="alert-item">${alert}</div>
            `).join('');
        }
        
        function initializeChart() {
            const ctx = document.getElementById('scoreChart').getContext('2d');
            scoreChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: '투자 점수',
                        data: [],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        
        function updateChart(stocks) {
            if (!scoreChart) return;
            
            const labels = stocks.map(stock => stock.stock_name);
            const data = stocks.map(stock => stock.investment_score);
            
            scoreChart.data.labels = labels;
            scoreChart.data.datasets[0].data = data;
            scoreChart.update();
        }
        
        function refreshData() {
            fetch('/api/refresh')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Data refreshed successfully');
                    } else {
                        console.error('Error refreshing data:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                });
        }
        
        // 5분마다 자동 새로고침
        setInterval(refreshData, 300000);
    </script>
</body>
</html>"""
    
    template_path = os.path.join(template_dir, "simple_dashboard.html")
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    logger.info(f"간단한 대시보드 템플릿이 생성되었습니다: {template_path}")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="간단한 뉴스 분석 대시보드")
    parser.add_argument("--host", default="localhost", help="호스트 주소")
    parser.add_argument("--port", type=int, default=5000, help="포트 번호")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    parser.add_argument("--config", default="config/news_config.json", help="설정 파일 경로")
    parser.add_argument("--create-template", action="store_true", help="HTML 템플릿 생성")
    
    args = parser.parse_args()
    
    # 템플릿 생성
    if args.create_template:
        create_simple_dashboard_template()
        return
    
    # 대시보드 실행
    dashboard = SimpleNewsDashboard(args.config)
    dashboard.run_dashboard(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 