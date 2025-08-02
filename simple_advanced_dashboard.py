from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List
from loguru import logger

class SimpleAdvancedDashboard:
    """간단한 고급 분석 대시보드"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self._setup_routes()
        logger.info("간단한 고급 대시보드 초기화 완료")
    
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.route('/')
        def index():
            return render_template('advanced_dashboard.html')
        
        @self.app.route('/api/dashboard-data')
        def get_dashboard_data():
            """대시보드 데이터 API"""
            try:
                data = self._get_analysis_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"대시보드 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/chart-data/<chart_type>')
        def get_chart_data(chart_type):
            """차트 데이터 API"""
            try:
                chart_data = self._generate_chart_data(chart_type)
                return jsonify(chart_data)
            except Exception as e:
                logger.error(f"차트 데이터 조회 실패: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _get_analysis_data(self) -> Dict:
        """분석 데이터 조회"""
        try:
            # 최신 뉴스 분석 결과 로드
            analysis_data = self._load_latest_analysis()
            
            # 기본 대시보드 데이터
            dashboard_data = {
                'summary': self._generate_summary(analysis_data),
                'top_stocks': self._get_top_stocks(analysis_data),
                'last_updated': datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"분석 데이터 조회 실패: {e}")
            return {}
    
    def _load_latest_analysis(self) -> pd.DataFrame:
        """최신 분석 결과 로드"""
        try:
            # data/news_analysis 디렉토리에서 최신 CSV 파일 찾기
            analysis_dir = "data/news_analysis"
            csv_files = [f for f in os.listdir(analysis_dir) if f.endswith('.csv')]
            
            if not csv_files:
                return pd.DataFrame()
            
            # 가장 최신 파일 선택
            latest_file = max(csv_files)
            file_path = os.path.join(analysis_dir, latest_file)
            
            # CSV 파일 로드
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            return df
            
        except Exception as e:
            logger.error(f"분석 결과 로드 실패: {e}")
            return pd.DataFrame()
    
    def _generate_summary(self, df: pd.DataFrame) -> Dict:
        """요약 정보 생성"""
        if df.empty:
            return {}
        
        return {
            'total_stocks': len(df),
            'avg_investment_score': df['investment_score'].mean(),
            'high_score_stocks': len(df[df['investment_score'] >= 70]),
            'medium_score_stocks': len(df[(df['investment_score'] >= 50) & (df['investment_score'] < 70)]),
            'low_score_stocks': len(df[df['investment_score'] < 50]),
            'top_performer': df.loc[df['investment_score'].idxmax(), 'stock_name'] if not df.empty else '',
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def _get_top_stocks(self, df: pd.DataFrame, limit: int = 10) -> List[Dict]:
        """상위 종목 조회"""
        if df.empty:
            return []
        
        # 투자점수 기준 상위 종목
        top_stocks = df.nlargest(limit, 'investment_score')
        
        result = []
        for _, row in top_stocks.iterrows():
            # 뉴스 링크 파싱
            recent_news = []
            if pd.notna(row.get('recent_news_links')):
                news_links = row['recent_news_links'].split('|')
                for link in news_links:
                    if '|' in link:
                        title, url = link.split('|', 1)
                        if title.strip() and url.strip():
                            recent_news.append({
                                'title': title.strip(),
                                'link': url.strip()
                            })
            
            stock_data = {
                'stock_code': row['stock_code'],
                'stock_name': row['stock_name'],
                'investment_score': float(row['investment_score']),
                'sentiment_score': float(row.get('sentiment_score', 0)),
                'risk_level': row.get('risk_level', 'medium'),
                'news_count': len(recent_news),
                'recent_news': recent_news,  # 뉴스 제목과 링크 추가
                'recommendation': self._get_recommendation(row['investment_score'])
            }
            result.append(stock_data)
        
        return result
    
    def _get_recommendation(self, score: float) -> str:
        """투자점수 기반 추천"""
        if score >= 80:
            return "강력매수"
        elif score >= 70:
            return "매수"
        elif score >= 50:
            return "관망"
        elif score >= 30:
            return "매도"
        else:
            return "강력매도"
    
    def _generate_chart_data(self, chart_type: str) -> Dict:
        """차트 데이터 생성"""
        try:
            df = self._load_latest_analysis()
            
            if chart_type == 'investment_scores':
                return self._create_investment_scores_chart(df)
            elif chart_type == 'sector_performance':
                return self._create_sector_performance_chart(df)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"차트 데이터 생성 실패: {e}")
            return {}
    
    def _create_investment_scores_chart(self, df: pd.DataFrame) -> Dict:
        """투자점수 차트 생성"""
        if df.empty:
            return {}
        
        top_stocks = df.nlargest(10, 'investment_score')
        
        return {
            'type': 'bar',
            'data': {
                'labels': top_stocks['stock_name'].tolist(),
                'datasets': [{
                    'label': '투자점수',
                    'data': top_stocks['investment_score'].tolist(),
                    'backgroundColor': [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                        '#FF6384', '#36A2EB'
                    ][:len(top_stocks)]
                }]
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        }
    
    def _create_sector_performance_chart(self, df: pd.DataFrame) -> Dict:
        """섹터별 성과 차트 생성"""
        if df.empty:
            return {}
        
        # 간단한 섹터 분류
        sector_scores = {}
        for _, row in df.iterrows():
            sector = self._get_stock_sector(row['stock_code'])
            if sector not in sector_scores:
                sector_scores[sector] = []
            sector_scores[sector].append(row['investment_score'])
        
        sector_analysis = {}
        for sector, scores in sector_scores.items():
            sector_analysis[sector] = np.mean(scores)
        
        return {
            'type': 'doughnut',
            'data': {
                'labels': list(sector_analysis.keys()),
                'datasets': [{
                    'data': list(sector_analysis.values()),
                    'backgroundColor': [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40'
                    ][:len(sector_analysis)]
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                }
            }
        }
    
    def _get_stock_sector(self, stock_code: str) -> str:
        """종목 코드로 섹터 판단"""
        # 간단한 섹터 매핑
        sector_mapping = {
            '005930': '반도체',  # 삼성전자
            '000660': '반도체',  # SK하이닉스
            '035420': 'IT',      # NAVER
            '035720': 'IT',      # 카카오
            '051910': '화학',    # LG화학
            '006400': '화학',    # 삼성SDI
            '005380': '자동차',  # 현대자동차
            '000270': '자동차',  # 기아
            '005490': '철강',    # POSCO
            '068270': '바이오',  # 셀트리온
        }
        
        return sector_mapping.get(stock_code, '기타')
    
    def start_dashboard(self, host: str = 'localhost', port: int = 8081):
        """대시보드 시작"""
        try:
            logger.info(f"간단한 고급 분석 대시보드가 시작되었습니다: http://{host}:{port}")
            self.app.run(host=host, port=port, debug=False)
        except Exception as e:
            logger.error(f"대시보드 시작 실패: {e}")

if __name__ == "__main__":
    dashboard = SimpleAdvancedDashboard()
    dashboard.start_dashboard() 