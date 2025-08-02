#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, Response
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
        
        @self.app.route('/api/data-validation')
        def get_data_validation():
            try:
                validation = self._validate_data_quality()
                return jsonify(validation)
            except Exception as e:
                logger.error(f"데이터 검증 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/alerts')
        def get_alerts():
            try:
                alerts = self._get_alerts()
                return jsonify(alerts)
            except Exception as e:
                logger.error(f"알림 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/export/hybrid-data')
        def export_hybrid_data():
            try:
                hybrid_data = self._get_latest_hybrid_data()
                if hybrid_data is None:
                    return jsonify({"error": "하이브리드 데이터가 없습니다"})
                
                # CSV 형식으로 변환
                csv_data = hybrid_data.to_csv(index=False, encoding='utf-8-sig')
                
                response = Response(csv_data, mimetype='text/csv')
                response.headers['Content-Disposition'] = f'attachment; filename=hybrid_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                return response
                
            except Exception as e:
                logger.error(f"하이브리드 데이터 내보내기 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/export/simulation-data')
        def export_simulation_data():
            try:
                simulation_data = self._get_latest_simulation_data()
                if simulation_data is None:
                    return jsonify({"error": "시뮬레이션 데이터가 없습니다"})
                
                # CSV 형식으로 변환
                csv_data = simulation_data.to_csv(index=True, encoding='utf-8-sig')
                
                response = Response(csv_data, mimetype='text/csv')
                response.headers['Content-Disposition'] = f'attachment; filename=simulation_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                return response
                
            except Exception as e:
                logger.error(f"시뮬레이션 데이터 내보내기 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/settings')
        def get_settings():
            try:
                settings = self._get_settings()
                return jsonify(settings)
            except Exception as e:
                logger.error(f"설정 조회 실패: {e}")
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
                logger.warning(f"시뮬레이션 데이터 디렉토리가 존재하지 않습니다: {self.simulation_data_dir}")
                return None
            
            csv_files = [f for f in os.listdir(self.simulation_data_dir) if f.endswith('.csv')]
            if not csv_files:
                logger.warning("시뮬레이션 CSV 파일을 찾을 수 없습니다.")
                return None
            
            # 가장 최신 파일 선택
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.simulation_data_dir, x)))
            file_path = os.path.join(self.simulation_data_dir, latest_file)
            
            # 다양한 인코딩으로 시도
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding)
                    
                    # 날짜 컬럼이 있으면 인덱스로 설정
                    if 'date' in data.columns:
                        data['date'] = pd.to_datetime(data['date'])
                        data.set_index('date', inplace=True)
                    
                    logger.info(f"시뮬레이션 데이터 로드 완료: {latest_file}")
                    return data
                except Exception as e:
                    logger.warning(f"인코딩 {encoding}로 로드 실패: {e}")
                    continue
            
            logger.error("모든 인코딩으로 시도했지만 데이터 로드에 실패했습니다.")
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
                    "avg_score": round(hybrid_data['combined_score'].mean(), 2) if hybrid_data is not None else 0
                },
                "simulation": {
                    "total_return": 0,
                    "win_rate": 0,
                    "total_trades": 0,
                    "max_drawdown": 0,
                    "sharpe_ratio": 0
                }
            }
            
            if simulation_data is not None:
                if 'portfolio_value' in simulation_data.columns:
                    initial_value = simulation_data['portfolio_value'].iloc[0]
                    final_value = simulation_data['portfolio_value'].iloc[-1]
                    overview["simulation"]["total_return"] = round(((final_value - initial_value) / initial_value) * 100, 2)
                    
                    # 샤프 비율 계산
                    returns = simulation_data['portfolio_value'].pct_change().dropna()
                    if len(returns) > 0:
                        sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0
                        overview["simulation"]["sharpe_ratio"] = round(sharpe_ratio, 2)
                
                if 'trades' in simulation_data.columns:
                    trade_data = simulation_data[simulation_data['trades'] != 0]
                    total_trades = len(trade_data)
                    winning_trades = len(trade_data[trade_data['trades'] > 0])
                    overview["simulation"]["total_trades"] = total_trades
                    overview["simulation"]["win_rate"] = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0
                
                if 'portfolio_value' in simulation_data.columns:
                    returns = simulation_data['portfolio_value'].pct_change().dropna()
                    cumulative_returns = (1 + returns).cumprod()
                    rolling_max = cumulative_returns.expanding().max()
                    drawdown = (cumulative_returns - rolling_max) / rolling_max
                    overview["simulation"]["max_drawdown"] = round(drawdown.min() * 100, 2)
            
            return overview
            
        except Exception as e:
            logger.error(f"개요 데이터 생성 실패: {e}")
            return {}
    
    def _validate_data_quality(self):
        """데이터 품질을 검증합니다."""
        try:
            validation_results = {
                "hybrid_data": {
                    "valid": False,
                    "issues": [],
                    "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "simulation_data": {
                    "valid": False,
                    "issues": [],
                    "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            # 하이브리드 데이터 검증
            hybrid_data = self._get_latest_hybrid_data()
            if hybrid_data is not None:
                validation_results["hybrid_data"]["valid"] = True
                
                # 필수 컬럼 확인
                required_columns = ['stock_name', 'final_signal', 'combined_score']
                missing_columns = [col for col in required_columns if col not in hybrid_data.columns]
                if missing_columns:
                    validation_results["hybrid_data"]["issues"].append(f"필수 컬럼 누락: {missing_columns}")
                
                # 데이터 타입 검증
                if 'combined_score' in hybrid_data.columns:
                    if not pd.api.types.is_numeric_dtype(hybrid_data['combined_score']):
                        validation_results["hybrid_data"]["issues"].append("combined_score가 숫자 타입이 아닙니다")
                
                # 신호 값 검증
                if 'final_signal' in hybrid_data.columns:
                    valid_signals = ['매수', '매도', '관망']
                    invalid_signals = hybrid_data[~hybrid_data['final_signal'].isin(valid_signals)]
                    if len(invalid_signals) > 0:
                        validation_results["hybrid_data"]["issues"].append(f"잘못된 신호 값: {len(invalid_signals)}개")
            else:
                validation_results["hybrid_data"]["issues"].append("데이터 파일을 찾을 수 없습니다")
            
            # 시뮬레이션 데이터 검증
            simulation_data = self._get_latest_simulation_data()
            if simulation_data is not None:
                validation_results["simulation_data"]["valid"] = True
                
                # 필수 컬럼 확인
                required_columns = ['portfolio_value']
                missing_columns = [col for col in required_columns if col not in simulation_data.columns]
                if missing_columns:
                    validation_results["simulation_data"]["issues"].append(f"필수 컬럼 누락: {missing_columns}")
                
                # 데이터 타입 검증
                if 'portfolio_value' in simulation_data.columns:
                    if not pd.api.types.is_numeric_dtype(simulation_data['portfolio_value']):
                        validation_results["simulation_data"]["issues"].append("portfolio_value가 숫자 타입이 아닙니다")
                    
                    # 음수 값 확인
                    negative_values = simulation_data[simulation_data['portfolio_value'] < 0]
                    if len(negative_values) > 0:
                        validation_results["simulation_data"]["issues"].append(f"음수 포트폴리오 값: {len(negative_values)}개")
            else:
                validation_results["simulation_data"]["issues"].append("데이터 파일을 찾을 수 없습니다")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"데이터 품질 검증 실패: {e}")
            return {
                "hybrid_data": {"valid": False, "issues": [str(e)], "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                "simulation_data": {"valid": False, "issues": [str(e)], "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            }
    
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
    
    def _get_performance_trend(self):
        """성과 트렌드 차트 데이터를 생성합니다."""
        try:
            simulation_data = self._get_latest_simulation_data()
            
            if simulation_data is None or 'portfolio_value' not in simulation_data.columns:
                return {"dates": [], "values": [], "returns": []}
            
            # 포트폴리오 가치 변화
            dates = simulation_data.index.tolist()
            values = simulation_data['portfolio_value'].tolist()
            
            # 수익률 계산
            initial_value = values[0]
            returns = [((value - initial_value) / initial_value) * 100 for value in values]
            
            return {
                "dates": dates,
                "values": values,
                "returns": returns
            }
            
        except Exception as e:
            logger.error(f"성과 트렌드 데이터 생성 실패: {e}")
            return {"dates": [], "values": [], "returns": []}
    
    def _get_signal_distribution(self):
        """신호 분포 차트 데이터를 생성합니다."""
        try:
            hybrid_data = self._get_latest_hybrid_data()
            
            if hybrid_data is None or 'final_signal' not in hybrid_data.columns:
                return {"signals": [], "counts": []}
            
            signal_counts = hybrid_data['final_signal'].value_counts()
            
            return {
                "signals": signal_counts.index.tolist(),
                "counts": signal_counts.values.tolist()
            }
            
        except Exception as e:
            logger.error(f"신호 분포 데이터 생성 실패: {e}")
            return {"signals": [], "counts": []}
    
    def _get_portfolio_growth(self):
        """포트폴리오 성장 차트 데이터를 생성합니다."""
        try:
            simulation_data = self._get_latest_simulation_data()
            
            if simulation_data is None or 'portfolio_value' not in simulation_data.columns:
                return {"dates": [], "growth": []}
            
            # 성장률 계산 (일별)
            portfolio_values = simulation_data['portfolio_value']
            growth_rates = portfolio_values.pct_change().fillna(0) * 100
            
            return {
                "dates": simulation_data.index.tolist(),
                "growth": growth_rates.tolist()
            }
            
        except Exception as e:
            logger.error(f"포트폴리오 성장 데이터 생성 실패: {e}")
            return {"dates": [], "growth": []}
    
    def _get_system_status(self):
        """시스템 상태를 확인합니다."""
        try:
            status = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hybrid_data": {
                    "available": False,
                    "last_update": None,
                    "data_count": 0
                },
                "simulation_data": {
                    "available": False,
                    "last_update": None,
                    "data_count": 0
                },
                "services": {
                    "hybrid_dashboard": "unknown",
                    "simulation_dashboard": "unknown"
                }
            }
            
            # 하이브리드 데이터 상태
            hybrid_data = self._get_latest_hybrid_data()
            if hybrid_data is not None:
                status["hybrid_data"]["available"] = True
                status["hybrid_data"]["data_count"] = len(hybrid_data)
                status["hybrid_data"]["last_update"] = datetime.now().strftime("%H:%M")
            
            # 시뮬레이션 데이터 상태
            simulation_data = self._get_latest_simulation_data()
            if simulation_data is not None:
                status["simulation_data"]["available"] = True
                status["simulation_data"]["data_count"] = len(simulation_data)
                status["simulation_data"]["last_update"] = datetime.now().strftime("%H:%M")
            
            return status
            
        except Exception as e:
            logger.error(f"시스템 상태 확인 실패: {e}")
            return {"error": str(e)}
    
    def _get_alerts(self):
        """알림을 생성합니다."""
        try:
            alerts = []
            
            # 데이터 검증 결과 확인
            validation = self._validate_data_quality()
            
            # 하이브리드 데이터 알림
            if not validation["hybrid_data"]["valid"]:
                alerts.append({
                    "type": "error",
                    "title": "하이브리드 데이터 오류",
                    "message": f"데이터 품질 문제: {', '.join(validation['hybrid_data']['issues'])}",
                    "time": datetime.now().strftime("%H:%M"),
                    "priority": "high"
                })
            elif validation["hybrid_data"]["issues"]:
                alerts.append({
                    "type": "warning",
                    "title": "하이브리드 데이터 경고",
                    "message": f"데이터 품질 경고: {', '.join(validation['hybrid_data']['issues'])}",
                    "time": datetime.now().strftime("%H:%M"),
                    "priority": "medium"
                })
            
            # 시뮬레이션 데이터 알림
            if not validation["simulation_data"]["valid"]:
                alerts.append({
                    "type": "error",
                    "title": "시뮬레이션 데이터 오류",
                    "message": f"데이터 품질 문제: {', '.join(validation['simulation_data']['issues'])}",
                    "time": datetime.now().strftime("%H:%M"),
                    "priority": "high"
                })
            elif validation["simulation_data"]["issues"]:
                alerts.append({
                    "type": "warning",
                    "title": "시뮬레이션 데이터 경고",
                    "message": f"데이터 품질 경고: {', '.join(validation['simulation_data']['issues'])}",
                    "time": datetime.now().strftime("%H:%M"),
                    "priority": "medium"
                })
            
            # 성과 알림
            overview = self._get_overview_data()
            if overview and "simulation" in overview:
                sim_data = overview["simulation"]
                
                # 높은 수익률 알림
                if sim_data.get("total_return", 0) > 10:
                    alerts.append({
                        "type": "success",
                        "title": "높은 수익률 달성",
                        "message": f"총 수익률 {sim_data['total_return']}% 달성!",
                        "time": datetime.now().strftime("%H:%M"),
                        "priority": "low"
                    })
                
                # 높은 승률 알림
                if sim_data.get("win_rate", 0) > 70:
                    alerts.append({
                        "type": "success",
                        "title": "높은 승률 달성",
                        "message": f"승률 {sim_data['win_rate']}% 달성!",
                        "time": datetime.now().strftime("%H:%M"),
                        "priority": "low"
                    })
                
                # 큰 손실 알림
                if sim_data.get("max_drawdown", 0) < -20:
                    alerts.append({
                        "type": "error",
                        "title": "큰 손실 발생",
                        "message": f"최대 낙폭 {sim_data['max_drawdown']}% 발생",
                        "time": datetime.now().strftime("%H:%M"),
                        "priority": "high"
                    })
            
            # 데이터 신선도 알림
            hybrid_data = self._get_latest_hybrid_data()
            if hybrid_data is not None:
                # 파일 수정 시간 확인 (간단한 예시)
                csv_files = [f for f in os.listdir(self.hybrid_data_dir) if f.endswith('.csv')]
                if csv_files:
                    latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.hybrid_data_dir, x)))
                    file_path = os.path.join(self.hybrid_data_dir, latest_file)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    time_diff = datetime.now() - file_time
                    
                    if time_diff.total_seconds() > 3600:  # 1시간 이상
                        alerts.append({
                            "type": "warning",
                            "title": "데이터 신선도 경고",
                            "message": f"하이브리드 데이터가 {int(time_diff.total_seconds() / 3600)}시간 전에 업데이트됨",
                            "time": datetime.now().strftime("%H:%M"),
                            "priority": "medium"
                        })
            
            return {"alerts": alerts}
            
        except Exception as e:
            logger.error(f"알림 생성 실패: {e}")
            return {"alerts": []}
    
    def _get_settings(self):
        """통합 대시보드의 설정을 반환합니다."""
        return {
            "dashboard_title": "통합 대시보드",
            "data_refresh_interval": 300, # 초 단위
            "alerts_refresh_interval": 60, # 초 단위
            "export_file_format": "csv",
            "data_directories": {
                "hybrid_analysis": self.hybrid_data_dir,
                "simulation_results": self.simulation_data_dir
            }
        }
    
    def start_dashboard(self, host='0.0.0.0', port=8080, debug=False):
        """통합 대시보드를 시작합니다."""
        logger.info(f"통합 대시보드가 시작되었습니다: http://localhost:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    dashboard = IntegratedDashboard()
    dashboard.start_dashboard() 