#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from loguru import logger
import plotly.graph_objs as go
import plotly.utils

class SimulationDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.data_dir = "data/simulation_results"
        self.setup_routes()
        logger.info("시뮬레이션 대시보드 초기화 완료")
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('simulation_dashboard.html')
        
        @self.app.route('/api/simulation-data')
        def get_simulation_data():
            try:
                latest_data = self._get_latest_simulation_data()
                if latest_data is None:
                    return jsonify({"error": "시뮬레이션 데이터를 찾을 수 없습니다."})
                
                summary_stats = self._generate_simulation_summary(latest_data)
                performance_metrics = self._calculate_performance_metrics(latest_data)
                
                return jsonify({
                    "summary": summary_stats,
                    "performance": performance_metrics,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                logger.error(f"시뮬레이션 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/chart-data/<chart_type>')
        def get_chart_data(chart_type):
            try:
                latest_data = self._get_latest_simulation_data()
                if latest_data is None:
                    return jsonify({"error": "데이터를 찾을 수 없습니다."})
                
                if chart_type == 'portfolio_value':
                    return jsonify(self._create_portfolio_value_chart(latest_data))
                elif chart_type == 'returns_distribution':
                    return jsonify(self._create_returns_distribution_chart(latest_data))
                elif chart_type == 'drawdown_analysis':
                    return jsonify(self._create_drawdown_chart(latest_data))
                elif chart_type == 'trade_analysis':
                    return jsonify(self._create_trade_analysis_chart(latest_data))
                elif chart_type == 'sector_performance':
                    return jsonify(self._create_sector_performance_chart(latest_data))
                elif chart_type == 'risk_metrics':
                    return jsonify(self._create_risk_metrics_chart(latest_data))
                else:
                    return jsonify({"error": "지원하지 않는 차트 타입입니다."})
            except Exception as e:
                logger.error(f"차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/trade-details')
        def get_trade_details():
            try:
                latest_data = self._get_latest_simulation_data()
                if latest_data is None:
                    return jsonify({"error": "데이터를 찾을 수 없습니다."})
                
                trade_details = self._get_trade_details_data(latest_data)
                return jsonify(trade_details)
            except Exception as e:
                logger.error(f"거래 상세 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
    
    def _get_latest_simulation_data(self):
        """최신 시뮬레이션 데이터를 로드합니다."""
        try:
            if not os.path.exists(self.data_dir):
                logger.warning(f"시뮬레이션 데이터 디렉토리가 존재하지 않습니다: {self.data_dir}")
                return None
            
            csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
            if not csv_files:
                logger.warning("시뮬레이션 CSV 파일을 찾을 수 없습니다.")
                return None
            
            # 가장 최신 파일 선택
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.data_dir, x)))
            file_path = os.path.join(self.data_dir, latest_file)
            
            # 다양한 인코딩으로 시도
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"시뮬레이션 데이터 로드 완료: {latest_file}")
                    return data
                except Exception as e:
                    logger.debug(f"인코딩 {encoding} 실패: {e}")
                    continue
            
            logger.error("모든 인코딩으로 파일 읽기 실패")
            return None
            
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 로드 실패: {e}")
            return None
    
    def _generate_simulation_summary(self, data):
        """시뮬레이션 요약 통계를 생성합니다."""
        try:
            if 'portfolio_value' in data.columns:
                initial_value = data['portfolio_value'].iloc[0]
                final_value = data['portfolio_value'].iloc[-1]
                total_return = ((final_value - initial_value) / initial_value) * 100
            else:
                initial_value = final_value = total_return = 0
            
            if 'trades' in data.columns:
                total_trades = len(data[data['trades'] != 0])
                winning_trades = len(data[(data['trades'] > 0) & (data['trades'] != 0)])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            else:
                total_trades = winning_trades = win_rate = 0
            
            return {
                "initial_value": f"{initial_value:,.0f}원",
                "final_value": f"{final_value:,.0f}원",
                "total_return": f"{total_return:.2f}%",
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": f"{win_rate:.1f}%",
                "simulation_period": f"{len(data)}일"
            }
        except Exception as e:
            logger.error(f"요약 통계 생성 실패: {e}")
            return {}
    
    def _calculate_performance_metrics(self, data):
        """성능 지표를 계산합니다."""
        try:
            if 'portfolio_value' not in data.columns:
                return {}
            
            # 수익률 계산
            returns = data['portfolio_value'].pct_change().dropna()
            
            # 기본 지표
            total_return = ((data['portfolio_value'].iloc[-1] - data['portfolio_value'].iloc[0]) / 
                           data['portfolio_value'].iloc[0]) * 100
            
            # 연간 수익률 (252일 기준)
            annual_return = total_return * (252 / len(data))
            
            # 변동성 (표준편차)
            volatility = returns.std() * np.sqrt(252) * 100
            
            # 샤프 비율 (무위험 수익률 2% 가정)
            risk_free_rate = 0.02
            sharpe_ratio = (annual_return/100 - risk_free_rate) / (volatility/100) if volatility > 0 else 0
            
            # 최대 낙폭 (MDD)
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            return {
                "total_return": f"{total_return:.2f}%",
                "annual_return": f"{annual_return:.2f}%",
                "volatility": f"{volatility:.2f}%",
                "sharpe_ratio": f"{sharpe_ratio:.2f}",
                "max_drawdown": f"{max_drawdown:.2f}%"
            }
        except Exception as e:
            logger.error(f"성능 지표 계산 실패: {e}")
            return {}
    
    def _create_portfolio_value_chart(self, data):
        """포트폴리오 가치 변화 차트를 생성합니다."""
        try:
            if 'portfolio_value' not in data.columns:
                return {"error": "포트폴리오 가치 데이터가 없습니다."}
            
            dates = pd.date_range(start=data.index[0], periods=len(data), freq='D')
            
            trace = go.Scatter(
                x=dates,
                y=data['portfolio_value'],
                mode='lines',
                name='포트폴리오 가치',
                line=dict(color='#1f77b4', width=2)
            )
            
            layout = go.Layout(
                title='포트폴리오 가치 변화',
                xaxis=dict(title='날짜'),
                yaxis=dict(title='포트폴리오 가치 (원)'),
                hovermode='x unified'
            )
            
            fig = go.Figure(data=[trace], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"포트폴리오 가치 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_returns_distribution_chart(self, data):
        """수익률 분포 차트를 생성합니다."""
        try:
            if 'portfolio_value' not in data.columns:
                return {"error": "포트폴리오 가치 데이터가 없습니다."}
            
            returns = data['portfolio_value'].pct_change().dropna()
            
            trace = go.Histogram(
                x=returns * 100,
                nbinsx=30,
                name='수익률 분포',
                marker=dict(color='#2ca02c', opacity=0.7)
            )
            
            layout = go.Layout(
                title='일간 수익률 분포',
                xaxis=dict(title='일간 수익률 (%)'),
                yaxis=dict(title='빈도'),
                showlegend=False
            )
            
            fig = go.Figure(data=[trace], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"수익률 분포 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_drawdown_chart(self, data):
        """낙폭 분석 차트를 생성합니다."""
        try:
            if 'portfolio_value' not in data.columns:
                return {"error": "포트폴리오 가치 데이터가 없습니다."}
            
            returns = data['portfolio_value'].pct_change().dropna()
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max * 100
            
            dates = pd.date_range(start=data.index[0], periods=len(drawdown), freq='D')
            
            trace = go.Scatter(
                x=dates,
                y=drawdown,
                mode='lines',
                name='낙폭',
                line=dict(color='#d62728', width=2),
                fill='tonexty'
            )
            
            layout = go.Layout(
                title='낙폭 분석',
                xaxis=dict(title='날짜'),
                yaxis=dict(title='낙폭 (%)'),
                hovermode='x unified'
            )
            
            fig = go.Figure(data=[trace], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"낙폭 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_trade_analysis_chart(self, data):
        """거래 분석 차트를 생성합니다."""
        try:
            if 'trades' not in data.columns:
                return {"error": "거래 데이터가 없습니다."}
            
            trade_data = data[data['trades'] != 0]
            
            if len(trade_data) == 0:
                return {"error": "거래 데이터가 없습니다."}
            
            # 거래 결과 분류
            winning_trades = trade_data[trade_data['trades'] > 0]
            losing_trades = trade_data[trade_data['trades'] < 0]
            
            trace1 = go.Bar(
                x=['수익 거래', '손실 거래'],
                y=[len(winning_trades), len(losing_trades)],
                name='거래 수',
                marker=dict(color=['#2ca02c', '#d62728'])
            )
            
            layout = go.Layout(
                title='거래 결과 분석',
                xaxis=dict(title='거래 결과'),
                yaxis=dict(title='거래 수'),
                showlegend=False
            )
            
            fig = go.Figure(data=[trace1], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"거래 분석 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_sector_performance_chart(self, data):
        """섹터별 성과 차트를 생성합니다."""
        try:
            if 'sector' not in data.columns or 'returns' not in data.columns:
                return {"error": "섹터 또는 수익률 데이터가 없습니다."}
            
            sector_performance = data.groupby('sector')['returns'].agg(['mean', 'count']).reset_index()
            
            trace = go.Bar(
                x=sector_performance['sector'],
                y=sector_performance['mean'] * 100,
                name='평균 수익률',
                marker=dict(color='#ff7f0e')
            )
            
            layout = go.Layout(
                title='섹터별 평균 수익률',
                xaxis=dict(title='섹터'),
                yaxis=dict(title='평균 수익률 (%)'),
                showlegend=False
            )
            
            fig = go.Figure(data=[trace], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"섹터 성과 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_risk_metrics_chart(self, data):
        """위험 지표 차트를 생성합니다."""
        try:
            if 'portfolio_value' not in data.columns:
                return {"error": "포트폴리오 가치 데이터가 없습니다."}
            
            returns = data['portfolio_value'].pct_change().dropna()
            
            # 위험 지표 계산
            volatility = returns.std() * np.sqrt(252) * 100
            var_95 = np.percentile(returns * 100, 5)  # 95% VaR
            cvar_95 = returns[returns * 100 <= var_95].mean() * 100  # 95% CVaR
            
            metrics = ['변동성', 'VaR (95%)', 'CVaR (95%)']
            values = [volatility, abs(var_95), abs(cvar_95)]
            
            trace = go.Bar(
                x=metrics,
                y=values,
                name='위험 지표',
                marker=dict(color=['#1f77b4', '#ff7f0e', '#2ca02c'])
            )
            
            layout = go.Layout(
                title='위험 지표',
                xaxis=dict(title='위험 지표'),
                yaxis=dict(title='값 (%)'),
                showlegend=False
            )
            
            fig = go.Figure(data=[trace], layout=layout)
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        except Exception as e:
            logger.error(f"위험 지표 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _get_trade_details_data(self, data):
        """거래 상세 데이터를 반환합니다."""
        try:
            if 'trades' not in data.columns:
                return {"error": "거래 데이터가 없습니다."}
            
            trade_data = data[data['trades'] != 0].copy()
            
            if len(trade_data) == 0:
                return {"trades": []}
            
            # 거래 상세 정보 생성
            trades = []
            for idx, row in trade_data.iterrows():
                trade_info = {
                    "date": str(idx),
                    "trade_type": "매수" if row['trades'] > 0 else "매도",
                    "amount": abs(row['trades']),
                    "value": row.get('trade_value', 0)
                }
                
                if 'stock_name' in row:
                    trade_info["stock"] = row['stock_name']
                if 'sector' in row:
                    trade_info["sector"] = row['sector']
                
                trades.append(trade_info)
            
            return {"trades": trades}
        except Exception as e:
            logger.error(f"거래 상세 데이터 생성 실패: {e}")
            return {"error": str(e)}
    
    def start_dashboard(self, host='0.0.0.0', port=8083, debug=False):
        """시뮬레이션 대시보드를 시작합니다."""
        logger.info(f"시뮬레이션 대시보드가 시작되었습니다: http://localhost:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    dashboard = SimulationDashboard()
    dashboard.start_dashboard() 