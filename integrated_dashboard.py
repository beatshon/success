#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for
from loguru import logger

class IntegratedDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.hybrid_data_dir = "data/hybrid_analysis"
        self.simulation_data_dir = "data/simulation_results"
        self.setup_routes()
        logger.info("통합 대시보드 초기화 완료")
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('integrated_dashboard.html')
        
        @self.app.route('/hybrid')
        def hybrid_dashboard():
            return redirect('http://localhost:8082')
        
        @self.app.route('/simulation')
        def simulation_dashboard():
            return redirect('http://localhost:8083')
        
        @self.app.route('/api/overview')
        def get_overview():
            try:
                overview_data = self._get_overview_data()
                return jsonify(overview_data)
            except Exception as e:
                logger.error(f"개요 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/quick-stats')
        def get_quick_stats():
            try:
                stats = self._get_quick_stats()
                return jsonify(stats)
            except Exception as e:
                logger.error(f"빠른 통계 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/recent-activity')
        def get_recent_activity():
            try:
                activity = self._get_recent_activity()
                return jsonify(activity)
            except Exception as e:
                logger.error(f"최근 활동 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/chart-data/performance-trend')
        def get_performance_trend():
            try:
                trend_data = self._get_performance_trend()
                return jsonify(trend_data)
            except Exception as e:
                logger.error(f"성과 트렌드 차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/chart-data/signal-distribution')
        def get_signal_distribution():
            try:
                signal_data = self._get_signal_distribution()
                return jsonify(signal_data)
            except Exception as e:
                logger.error(f"신호 분포 차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/chart-data/portfolio-growth')
        def get_portfolio_growth():
            try:
                growth_data = self._get_portfolio_growth()
                return jsonify(growth_data)
            except Exception as e:
                logger.error(f"포트폴리오 성장 차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/system-status')
        def get_system_status():
            try:
                status = self._get_system_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"시스템 상태 조회 실패: {e}")
                return jsonify({"error": str(e)})
    
    def _get_latest_hybrid_data(self):
        """최신 하이브리드 분석 데이터를 로드합니다."""
        try:
            if not os.path.exists(self.hybrid_data_dir):
                return None
            
            csv_files = [f for f in os.listdir(self.hybrid_data_dir) if f.endswith('.csv')]
            if not csv_files:
                return None
            
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.hybrid_data_dir, x)))
            file_path = os.path.join(self.hybrid_data_dir, latest_file)
            
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding)
                    return data
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"하이브리드 데이터 로드 실패: {e}")
            return None
    
    def _get_latest_simulation_data(self):
        """최신 시뮬레이션 데이터를 로드합니다."""
        try:
            if not os.path.exists(self.simulation_data_dir):
                return None
            
            csv_files = [f for f in os.listdir(self.simulation_data_dir) if f.endswith('.csv')]
            if not csv_files:
                return None
            
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.simulation_data_dir, x)))
            file_path = os.path.join(self.simulation_data_dir, latest_file)
            
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding)
                    return data
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 로드 실패: {e}")
            return None
    
    def _get_overview_data(self):
        """개요 데이터를 생성합니다."""
        try:
            hybrid_data = self._get_latest_hybrid_data()
            simulation_data = self._get_latest_simulation_data()
            
            overview = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hybrid_analysis": {
                    "total_stocks": len(hybrid_data) if hybrid_data is not None else 0,
                    "buy_signals": len(hybrid_data[hybrid_data['final_signal'] == '매수']) if hybrid_data is not None else 0,
                    "sell_signals": len(hybrid_data[hybrid_data['final_signal'] == '매도']) if hybrid_data is not None else 0,
                    "hold_signals": len(hybrid_data[hybrid_data['final_signal'] == '관망']) if hybrid_data is not None else 0,
                    "avg_score": hybrid_data['combined_score'].mean() if hybrid_data is not None else 0
                },
                "simulation": {
                    "total_return": 0,
                    "win_rate": 0,
                    "total_trades": 0,
                    "max_drawdown": 0
                }
            }
            
            if simulation_data is not None:
                if 'portfolio_value' in simulation_data.columns:
                    initial_value = simulation_data['portfolio_value'].iloc[0]
                    final_value = simulation_data['portfolio_value'].iloc[-1]
                    overview["simulation"]["total_return"] = ((final_value - initial_value) / initial_value) * 100
                
                if 'trades' in simulation_data.columns:
                    trade_data = simulation_data[simulation_data['trades'] != 0]
                    total_trades = len(trade_data)
                    winning_trades = len(trade_data[trade_data['trades'] > 0])
                    overview["simulation"]["total_trades"] = total_trades
                    overview["simulation"]["win_rate"] = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                if 'portfolio_value' in simulation_data.columns:
                    returns = simulation_data['portfolio_value'].pct_change().dropna()
                    cumulative_returns = (1 + returns).cumprod()
                    rolling_max = cumulative_returns.expanding().max()
                    drawdown = (cumulative_returns - rolling_max) / rolling_max
                    overview["simulation"]["max_drawdown"] = drawdown.min() * 100
            
            return overview
            
        except Exception as e:
            logger.error(f"개요 데이터 생성 실패: {e}")
            return {}
    
    def _get_quick_stats(self):
        """빠른 통계를 생성합니다."""
        try:
            hybrid_data = self._get_latest_hybrid_data()
            simulation_data = self._get_latest_simulation_data()
            
            stats = {
                "top_performers": [],
                "sector_distribution": {},
                "recent_trades": []
            }
            
            if hybrid_data is not None:
                # 상위 성과 종목
                top_stocks = hybrid_data.nlargest(5, 'combined_score')[['stock_name', 'combined_score', 'final_signal']]
                stats["top_performers"] = [
                    {
                        "name": row['stock_name'],
                        "score": round(row['combined_score'], 1),
                        "signal": row['final_signal']
                    }
                    for _, row in top_stocks.iterrows()
                ]
                
                # 섹터 분포
                if 'sector' in hybrid_data.columns:
                    sector_counts = hybrid_data['sector'].value_counts().head(5)
                    stats["sector_distribution"] = sector_counts.to_dict()
            
            if simulation_data is not None:
                # 최근 거래
                if 'trades' in simulation_data.columns:
                    recent_trades = simulation_data[simulation_data['trades'] != 0].tail(5)
                    stats["recent_trades"] = [
                        {
                            "date": str(idx),
                            "type": "매수" if row['trades'] > 0 else "매도",
                            "stock": row.get('stock_name', 'N/A'),
                            "amount": abs(row['trades'])
                        }
                        for idx, row in recent_trades.iterrows()
                    ]
            
            return stats
            
        except Exception as e:
            logger.error(f"빠른 통계 생성 실패: {e}")
            return {}
    
    def _get_recent_activity(self):
        """최근 활동을 생성합니다."""
        try:
            activities = []
            
            # 하이브리드 분석 활동
            hybrid_data = self._get_latest_hybrid_data()
            if hybrid_data is not None:
                activities.append({
                    "type": "analysis",
                    "title": "하이브리드 분석 완료",
                    "description": f"{len(hybrid_data)}개 종목 분석 완료",
                    "time": datetime.now().strftime("%H:%M"),
                    "status": "success"
                })
            
            # 시뮬레이션 활동
            simulation_data = self._get_latest_simulation_data()
            if simulation_data is not None:
                activities.append({
                    "type": "simulation",
                    "title": "시뮬레이션 실행",
                    "description": f"{len(simulation_data)}일 시뮬레이션 완료",
                    "time": datetime.now().strftime("%H:%M"),
                    "status": "success"
                })
            
            return {"activities": activities}
            
        except Exception as e:
            logger.error(f"최근 활동 생성 실패: {e}")
            return {"activities": []}
    
    def start_dashboard(self, host='0.0.0.0', port=8080, debug=False):
        """통합 대시보드를 시작합니다."""
        logger.info(f"통합 대시보드가 시작되었습니다: http://localhost:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    dashboard = IntegratedDashboard()
    dashboard.start_dashboard() 