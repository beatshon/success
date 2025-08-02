#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, jsonify
from loguru import logger

class HybridDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.data_dir = "data/hybrid_analysis"
        self.setup_routes()
        logger.info("하이브리드 대시보드 초기화 완료")
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('hybrid_dashboard.html')
        
        @self.app.route('/api/dashboard-data')
        def get_dashboard_data():
            try:
                latest_data = self._get_latest_hybrid_data()
                if latest_data is None:
                    return jsonify({"error": "하이브리드 분석 데이터를 찾을 수 없습니다."})
                
                summary_stats = self._generate_summary_stats(latest_data)
                top_stocks = self._get_top_stocks(latest_data)
                
                return jsonify({
                    "summary": summary_stats,
                    "top_stocks": top_stocks,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                logger.error(f"대시보드 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/chart-data/<chart_type>')
        def get_chart_data(chart_type):
            try:
                latest_data = self._get_latest_hybrid_data()
                if latest_data is None:
                    return jsonify({"error": "데이터를 찾을 수 없습니다."})
                
                if chart_type == 'score_distribution':
                    return jsonify(self._create_score_distribution_chart(latest_data))
                elif chart_type == 'sector_performance':
                    return jsonify(self._create_sector_performance_chart(latest_data))
                elif chart_type == 'signal_distribution':
                    return jsonify(self._create_signal_distribution_chart(latest_data))
                elif chart_type == 'news_vs_technical':
                    return jsonify(self._create_news_vs_technical_chart(latest_data))
                else:
                    return jsonify({"error": "지원하지 않는 차트 타입입니다."})
            except Exception as e:
                logger.error(f"차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)})
    
    def _get_latest_hybrid_data(self):
        """최신 하이브리드 분석 데이터를 로드합니다."""
        try:
            if not os.path.exists(self.data_dir):
                logger.warning(f"데이터 디렉토리가 존재하지 않습니다: {self.data_dir}")
                return None
            
            csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
            if not csv_files:
                logger.warning("하이브리드 분석 CSV 파일을 찾을 수 없습니다.")
                return None
            
            # 가장 최신 파일 선택
            latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.data_dir, x)))
            file_path = os.path.join(self.data_dir, latest_file)
            
            # 다양한 인코딩으로 시도
            for encoding in ['utf-8-sig', 'utf-8', 'cp949']:
                try:
                    data = pd.read_csv(file_path, encoding=encoding, lineterminator='\n')
                    logger.info(f"하이브리드 분석 데이터 로드 완료: {latest_file}")
                    return data
                except Exception as e:
                    logger.debug(f"인코딩 {encoding} 실패: {e}")
                    continue
            
            logger.error("모든 인코딩으로 파일 읽기 실패")
            return None
            
        except Exception as e:
            logger.error(f"하이브리드 분석 데이터 로드 실패: {e}")
            return None
    
    def _generate_summary_stats(self, data):
        """요약 통계를 생성합니다."""
        try:
            total_stocks = len(data)
            avg_combined_score = data['combined_score'].mean() if 'combined_score' in data.columns else 0
            
            # 신호 분포 계산
            signal_counts = data['final_signal'].value_counts().to_dict() if 'final_signal' in data.columns else {}
            
            # 매수/매도 신호 개수 계산
            buy_signals = sum(1 for signal in data['final_signal'] if '매수' in signal) if 'final_signal' in data.columns else 0
            sell_signals = sum(1 for signal in data['final_signal'] if '매도' in signal) if 'final_signal' in data.columns else 0
            
            return {
                "total_stocks": total_stocks,
                "avg_combined_score": round(avg_combined_score, 2),
                "avg_score": round(avg_combined_score, 2),  # 대시보드에서 사용하는 필드명
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "signal_distribution": signal_counts
            }
        except Exception as e:
            logger.error(f"요약 통계 생성 실패: {e}")
            return {}
    
    def _get_top_stocks(self, data):
        """상위 종목 데이터를 생성합니다."""
        try:
            if 'combined_score' not in data.columns:
                return []
            
            # 점수 순으로 정렬하여 상위 10개 선택
            top_stocks = data.nlargest(10, 'combined_score')
            
            stocks_list = []
            for _, row in top_stocks.iterrows():
                stocks_list.append({
                    'stock_code': row['stock_code'],
                    'stock_name': row['stock_name'],
                    'sector': row.get('sector', '기타'),
                    'news_score': float(row['news_score']),
                    'technical_score': float(row['technical_score']),
                    'combined_score': float(row['combined_score']),
                    'final_signal': row['final_signal'],
                    'reasoning': row.get('reasoning', '')
                })
            
            return stocks_list
        except Exception as e:
            logger.error(f"상위 종목 데이터 생성 실패: {e}")
            return []
    
    def _create_score_distribution_chart(self, data):
        """점수 분포 차트 데이터를 생성합니다."""
        try:
            if 'combined_score' not in data.columns:
                return {"error": "combined_score 컬럼이 없습니다."}
            
            # 점수 구간별 분포
            score_ranges = [
                (0, 20, "매우 낮음 (0-20)"),
                (20, 40, "낮음 (20-40)"),
                (40, 60, "보통 (40-60)"),
                (60, 80, "높음 (60-80)"),
                (80, 100, "매우 높음 (80-100)")
            ]
            
            distribution = []
            for min_score, max_score, label in score_ranges:
                count = len(data[(data['combined_score'] >= min_score) & (data['combined_score'] < max_score)])
                distribution.append({
                    "label": label,
                    "count": count,
                    "percentage": round(count / len(data) * 100, 1)
                })
            
            return {
                "type": "bar",
                "data": {
                    "labels": [d["label"] for d in distribution],
                    "datasets": [{
                        "label": "종목 수",
                        "data": [d["count"] for d in distribution],
                        "backgroundColor": [
                            "#dc3545", "#fd7e14", "#ffc107", "#28a745", "#007bff"
                        ],
                        "borderColor": [
                            "#c82333", "#e55a00", "#e0a800", "#1e7e34", "#0056b3"
                        ],
                        "borderWidth": 1
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {
                            "display": False
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "ticks": {
                                "stepSize": 1
                            }
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"점수 분포 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_sector_performance_chart(self, data):
        """섹터별 성과 차트 데이터를 생성합니다."""
        try:
            if 'sector' not in data.columns or 'combined_score' not in data.columns:
                return {"error": "필요한 컬럼이 없습니다."}
            
            sector_performance = data.groupby('sector')['combined_score'].agg(['mean', 'count']).reset_index()
            sector_performance = sector_performance.sort_values('mean', ascending=False)
            
            return {
                "type": "bar",
                "data": {
                    "labels": sector_performance['sector'].tolist(),
                    "datasets": [{
                        "label": "평균 점수",
                        "data": sector_performance['mean'].round(2).tolist(),
                        "backgroundColor": [
                            "#28a745", "#17a2b8", "#6f42c1", "#fd7e14", "#e83e8c",
                            "#20c997", "#ffc107", "#dc3545", "#6c757d", "#343a40"
                        ],
                        "borderColor": [
                            "#1e7e34", "#138496", "#5a32a3", "#e55a00", "#d63384",
                            "#1ea085", "#e0a800", "#c82333", "#545b62", "#1d2124"
                        ],
                        "borderWidth": 1
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {
                            "display": False
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "max": 100
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"섹터별 성과 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_signal_distribution_chart(self, data):
        """신호 분포 차트 데이터를 생성합니다."""
        try:
            if 'final_signal' not in data.columns:
                return {"error": "final_signal 컬럼이 없습니다."}
            
            signal_counts = data['final_signal'].value_counts()
            
            # 신호별 색상 매핑
            signal_colors = {
                "강력매수": "#28a745",
                "매수": "#6f42c1", 
                "관망": "#ffc107",
                "매도": "#fd7e14",
                "강력매도": "#dc3545"
            }
            
            return {
                "type": "doughnut",
                "data": {
                    "labels": signal_counts.index.tolist(),
                    "datasets": [{
                        "label": "신호 분포",
                        "data": signal_counts.values.tolist(),
                        "backgroundColor": [signal_colors.get(signal, "#6c757d") for signal in signal_counts.index],
                        "borderColor": "#ffffff",
                        "borderWidth": 2
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {
                            "position": "bottom"
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"신호 분포 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def _create_news_vs_technical_chart(self, data):
        """뉴스 vs 기술적 분석 비교 차트 데이터를 생성합니다."""
        try:
            if 'news_score' not in data.columns or 'technical_score' not in data.columns:
                return {"error": "필요한 컬럼이 없습니다."}
            
            # 상위 10개 종목 선택
            top_stocks = data.nlargest(10, 'combined_score')
            
            return {
                "type": "bar",
                "data": {
                    "labels": top_stocks['stock_name'].tolist(),
                    "datasets": [
                        {
                            "label": "뉴스 점수",
                            "data": top_stocks['news_score'].round(2).tolist(),
                            "backgroundColor": "rgba(54, 162, 235, 0.8)",
                            "borderColor": "rgba(54, 162, 235, 1)",
                            "borderWidth": 1
                        },
                        {
                            "label": "기술적 점수",
                            "data": top_stocks['technical_score'].round(2).tolist(),
                            "backgroundColor": "rgba(255, 99, 132, 0.8)",
                            "borderColor": "rgba(255, 99, 132, 1)",
                            "borderWidth": 1
                        },
                        {
                            "label": "종합 점수",
                            "data": top_stocks['combined_score'].round(2).tolist(),
                            "backgroundColor": "rgba(75, 192, 192, 0.8)",
                            "borderColor": "rgba(75, 192, 192, 1)",
                            "borderWidth": 1
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {
                            "position": "top"
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "max": 100
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"뉴스 vs 기술적 분석 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    def start_dashboard(self, host='0.0.0.0', port=8082, debug=False):
        """대시보드를 시작합니다."""
        logger.info(f"하이브리드 분석 대시보드가 시작되었습니다: http://localhost:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    dashboard = HybridDashboard()
    dashboard.start_dashboard(debug=True) 