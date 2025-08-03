#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 실시간 주식 데이터 서버
실제 주식 데이터 API를 연동하여 실시간 데이터 제공
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import threading
import time
from loguru import logger

# 실제 주식 데이터 API import
try:
    from real_stock_data_api import RealStockDataAPI
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    logger.warning("실제 주식 데이터 API를 사용할 수 없습니다. 가상 데이터를 사용합니다.")

app = Flask(__name__)
CORS(app)

class EnhancedRealTimeServer:
    """고도화된 실시간 서버"""
    
    def __init__(self):
        self.stock_data = {}
        self.technical_indicators = {}
        self.market_summary = {}
        self.portfolio_data = {}
        self.investment_signals = {}
        
        # 실제 주식 데이터 API 초기화
        if REAL_DATA_AVAILABLE:
            self.stock_api = RealStockDataAPI()
            logger.info("실제 주식 데이터 API 연동 완료")
        else:
            self.stock_api = None
            logger.info("가상 주식 데이터 사용")
        
        # 모니터링할 주식 목록
        self.watchlist = ["005930", "000660", "035420"]
        
        # 데이터 업데이트 스레드 시작
        self.is_running = True
        self.update_thread = threading.Thread(target=self._data_update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("고도화된 실시간 서버 초기화 완료")
    
    def _data_update_loop(self):
        """데이터 업데이트 루프"""
        while self.is_running:
            try:
                self._update_stock_data()
                self._update_technical_indicators()
                self._update_market_summary()
                self._update_portfolio_data()
                self._generate_investment_signals()
                
                # 30초마다 업데이트
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"데이터 업데이트 중 오류: {e}")
                time.sleep(60)
    
    def _update_stock_data(self):
        """주식 데이터 업데이트"""
        try:
            if self.stock_api:
                # 실제 데이터 수집
                data = self.stock_api.get_multiple_stocks_data(self.watchlist)
                self.stock_data = data
            else:
                # 가상 데이터 생성
                self._generate_virtual_stock_data()
            
            logger.info(f"주식 데이터 업데이트 완료: {len(self.stock_data)}개 종목")
            
        except Exception as e:
            logger.error(f"주식 데이터 업데이트 실패: {e}")
    
    def _generate_virtual_stock_data(self):
        """가상 주식 데이터 생성"""
        import random
        
        base_prices = {
            "005930": 75000,  # 삼성전자
            "000660": 125000,  # SK하이닉스
            "035420": 425000,  # LG에너지솔루션
        }
        
        stock_names = {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035420": "LG에너지솔루션",
        }
        
        for symbol in self.watchlist:
            base_price = base_prices.get(symbol, 50000)
            
            # 가격 변동 (±2%)
            variation = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + variation)
            
            change = current_price - base_price
            change_percent = (change / base_price) * 100
            
            self.stock_data[symbol] = {
                "symbol": symbol,
                "name": stock_names.get(symbol, symbol),
                "price": round(current_price, 0),
                "open": base_price,
                "high": max(current_price, base_price),
                "low": min(current_price, base_price),
                "volume": random.randint(1000000, 10000000),
                "change": round(change, 0),
                "change_percent": round(change_percent, 2),
                "timestamp": datetime.now().isoformat(),
                "source": "Virtual Data"
            }
    
    def _update_technical_indicators(self):
        """기술적 지표 업데이트"""
        try:
            if self.stock_api:
                for symbol in self.watchlist:
                    indicators = self.stock_api.get_technical_indicators(symbol)
                    if indicators:
                        self.technical_indicators[symbol] = indicators
            else:
                # 가상 기술적 지표 생성
                self._generate_virtual_indicators()
            
        except Exception as e:
            logger.error(f"기술적 지표 업데이트 실패: {e}")
    
    def _generate_virtual_indicators(self):
        """가상 기술적 지표 생성"""
        import random
        
        for symbol in self.watchlist:
            if symbol in self.stock_data:
                current_price = self.stock_data[symbol]["price"]
                
                self.technical_indicators[symbol] = {
                    "ma5": round(current_price * random.uniform(0.98, 1.02), 2),
                    "ma20": round(current_price * random.uniform(0.95, 1.05), 2),
                    "rsi": round(random.uniform(30, 70), 2),
                    "macd": round(random.uniform(-1000, 1000), 2),
                    "current_price": current_price
                }
    
    def _update_market_summary(self):
        """시장 요약 정보 업데이트"""
        try:
            if self.stock_api:
                self.market_summary = self.stock_api.get_market_summary()
            else:
                # 가상 시장 요약 생성
                import random
                self.market_summary = {
                    "timestamp": datetime.now().isoformat(),
                    "indices": {
                        "KOSPI": {
                            "value": round(2650 + random.uniform(-50, 50), 2),
                            "change": round(random.uniform(-30, 30), 2),
                            "change_percent": round(random.uniform(-1.5, 1.5), 2),
                        }
                    },
                    "market_status": "open" if 9 <= datetime.now().hour < 15 else "closed"
                }
            
        except Exception as e:
            logger.error(f"시장 요약 업데이트 실패: {e}")
    
    def _update_portfolio_data(self):
        """포트폴리오 데이터 업데이트"""
        try:
            total_value = 10000000
            total_profit = 0
            
            positions = []
            for symbol in self.watchlist:
                if symbol in self.stock_data:
                    data = self.stock_data[symbol]
                    quantity = 10 if symbol == "005930" else 5
                    avg_price = data["price"] * 0.95
                    current_value = data["price"] * quantity
                    profit = current_value - (avg_price * quantity)
                    
                    positions.append({
                        "code": symbol,
                        "name": data["name"],
                        "quantity": quantity,
                        "current_price": data["price"],
                        "profit": round(profit, 0),
                        "profit_rate": round((profit / (avg_price * quantity)) * 100, 2)
                    })
                    
                    total_profit += profit
            
            self.portfolio_data = {
                "total_value": total_value,
                "total_profit": round(total_profit, 0),
                "profit_rate": round((total_profit / total_value) * 100, 2),
                "positions": positions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"포트폴리오 데이터 업데이트 실패: {e}")
    
    def _generate_investment_signals(self):
        """투자 신호 생성"""
        try:
            for symbol in self.watchlist:
                if symbol in self.stock_data and symbol in self.technical_indicators:
                    data = self.stock_data[symbol]
                    indicators = self.technical_indicators[symbol]
                    
                    # 간단한 신호 생성 로직
                    signal = self._calculate_signal(data, indicators)
                    
                    self.investment_signals[symbol] = {
                        "symbol": symbol,
                        "name": data["name"],
                        "signal": signal["signal"],
                        "confidence": signal["confidence"],
                        "target_price": signal["target_price"],
                        "timestamp": datetime.now().isoformat()
                    }
            
        except Exception as e:
            logger.error(f"투자 신호 생성 실패: {e}")
    
    def _calculate_signal(self, data: dict, indicators: dict) -> dict:
        """신호 계산"""
        import random
        
        price = data["price"]
        change_percent = data["change_percent"]
        rsi = indicators.get("rsi", 50)
        
        # 간단한 신호 로직
        if change_percent > 2 and rsi < 70:
            signal = "BUY"
            confidence = 0.7
        elif change_percent < -2 and rsi > 30:
            signal = "SELL"
            confidence = 0.6
        elif rsi > 80:
            signal = "SELL"
            confidence = 0.8
        elif rsi < 20:
            signal = "BUY"
            confidence = 0.8
        else:
            signal = "HOLD"
            confidence = 0.5
        
        # 목표가 계산
        if signal == "BUY":
            target_price = price * 1.05
        elif signal == "SELL":
            target_price = price * 0.95
        else:
            target_price = price
        
        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "target_price": round(target_price, 0)
        }
    
    def stop(self):
        """서버 중지"""
        self.is_running = False
        logger.info("실시간 서버 중지")

# 서버 인스턴스 생성
server = EnhancedRealTimeServer()

# 간단한 HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>고도화된 키움 트레이딩 시스템</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .card { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { margin: 0 0 15px 0; }
        .stock-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        .signal-buy { background: rgba(74, 222, 128, 0.2); }
        .signal-sell { background: rgba(248, 113, 113, 0.2); }
        .signal-hold { background: rgba(148, 163, 184, 0.2); }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width">
            <h1>🚀 고도화된 키움 트레이딩 시스템</h1>
            <p><strong>실시간 데이터 연동</strong> | 서버: AWS EC2 | IP: 43.202.66.120</p>
        </div>
        
        <div class="card">
            <h2>📈 실시간 주식 데이터</h2>
            <div id="stock-data"></div>
        </div>
        
        <div class="card">
            <h2>📊 시장 요약</h2>
            <div id="market-summary"></div>
        </div>
        
        <div class="card">
            <h2>💼 포트폴리오 현황</h2>
            <div id="portfolio-data"></div>
        </div>
        
        <div class="card">
            <h2>🎯 투자 신호</h2>
            <div id="investment-signals"></div>
        </div>
        
        <div class="card full-width">
            <h2>📊 기술적 지표</h2>
            <div id="technical-indicators"></div>
        </div>
    </div>
    
    <script>
        function updateData() {
            fetch('/api/all-data')
                .then(response => response.json())
                .then(data => {
                    updateStockData(data.stock_data);
                    updateMarketSummary(data.market_summary);
                    updatePortfolioData(data.portfolio_data);
                    updateInvestmentSignals(data.investment_signals);
                    updateTechnicalIndicators(data.technical_indicators);
                });
        }
        
        function updateStockData(stockData) {
            const container = document.getElementById('stock-data');
            container.innerHTML = '';
            
            Object.values(stockData).forEach(stock => {
                const changeClass = stock.change_percent >= 0 ? 'positive' : 'negative';
                const item = document.createElement('div');
                item.className = 'stock-item';
                item.innerHTML = `
                    <div><strong>${stock.name}</strong></div>
                    <div style="text-align: right;">
                        <div>${stock.price.toLocaleString()}원</div>
                        <div class="${changeClass}">${stock.change_percent >= 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%</div>
                    </div>
                `;
                container.appendChild(item);
            });
        }
        
        function updateMarketSummary(summary) {
            const container = document.getElementById('market-summary');
            container.innerHTML = '';
            
            Object.entries(summary.indices).forEach(([index, data]) => {
                const changeClass = data.change_percent >= 0 ? 'positive' : 'negative';
                const item = document.createElement('div');
                item.className = 'stock-item';
                item.innerHTML = `
                    <div><strong>${index}</strong></div>
                    <div style="text-align: right;">
                        <div>${data.value.toFixed(2)}</div>
                        <div class="${changeClass}">${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%</div>
                    </div>
                `;
                container.appendChild(item);
            });
        }
        
        function updatePortfolioData(portfolio) {
            const container = document.getElementById('portfolio-data');
            const profitClass = portfolio.profit_rate >= 0 ? 'positive' : 'negative';
            
            container.innerHTML = `
                <div class="stock-item">
                    <div><strong>총 자산</strong></div>
                    <div>${portfolio.total_value.toLocaleString()}원</div>
                </div>
                <div class="stock-item">
                    <div><strong>총 수익</strong></div>
                    <div class="${profitClass}">${portfolio.profit_rate >= 0 ? '+' : ''}${portfolio.profit_rate.toFixed(2)}%</div>
                </div>
            `;
        }
        
        function updateInvestmentSignals(signals) {
            const container = document.getElementById('investment-signals');
            container.innerHTML = '';
            
            Object.values(signals).forEach(signal => {
                const signalClass = `signal-${signal.signal.toLowerCase()}`;
                const item = document.createElement('div');
                item.className = `stock-item ${signalClass}`;
                item.innerHTML = `
                    <div><strong>${signal.name}</strong></div>
                    <div style="text-align: right;">
                        <div>${signal.signal}</div>
                        <div>${signal.target_price.toLocaleString()}원</div>
                    </div>
                `;
                container.appendChild(item);
            });
        }
        
        function updateTechnicalIndicators(indicators) {
            const container = document.getElementById('technical-indicators');
            container.innerHTML = '';
            
            Object.entries(indicators).forEach(([symbol, data]) => {
                const item = document.createElement('div');
                item.className = 'stock-item';
                item.innerHTML = `
                    <div><strong>${symbol}</strong></div>
                    <div>RSI: ${data.rsi} | MACD: ${data.macd}</div>
                `;
                container.appendChild(item);
            });
        }
        
        // 초기 데이터 로드
        updateData();
        
        // 30초마다 자동 업데이트
        setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    """API 상태 확인"""
    return jsonify({
        "status": "running",
        "message": "고도화된 키움 트레이딩 시스템이 정상적으로 운영 중입니다.",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "deployment": "AWS EC2",
        "data_source": "Real Stock Data API" if REAL_DATA_AVAILABLE else "Virtual Data"
    })

@app.route('/api/all-data')
def all_data():
    """모든 데이터 통합 API"""
    return jsonify({
        "stock_data": server.stock_data,
        "technical_indicators": server.technical_indicators,
        "market_summary": server.market_summary,
        "portfolio_data": server.portfolio_data,
        "investment_signals": server.investment_signals,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stock-data')
def stock_data():
    """주식 데이터 API"""
    return jsonify(server.stock_data)

@app.route('/api/portfolio')
def portfolio():
    """포트폴리오 API"""
    return jsonify(server.portfolio_data)

@app.route('/api/signals')
def signals():
    """투자 신호 API"""
    return jsonify(server.investment_signals)

def main():
    """메인 실행 함수"""
    logger.info("고도화된 실시간 서버 시작")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("서버 종료 요청")
    finally:
        server.stop()
        logger.info("서버 종료")

if __name__ == '__main__':
    main() 