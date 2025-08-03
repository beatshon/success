#!/usr/bin/env python3
"""
투자 관리 시스템
일일 투자 총비용 제한 및 분산투자 로직 관리
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
import json
import os

class InvestmentManager:
    """투자 관리 시스템"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.daily_investment_file = "investment_data/daily_investment.json"
        self.portfolio_file = "investment_data/portfolio.json"
        
        # 디렉토리 생성
        os.makedirs("investment_data", exist_ok=True)
        
        # 일일 투자 내역 로드
        self.daily_investments = self._load_daily_investments()
        self.portfolio = self._load_portfolio()
        
        # 오늘 날짜
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def _get_default_config(self) -> Dict:
        """기본 설정"""
        return {
            'daily_investment_limit': 2000000,  # 일일 투자 한도 (200만원)
            'max_single_investment': 500000,    # 단일 종목 최대 투자 (50만원)
            'max_sector_allocation': 0.4,       # 섹터별 최대 배분 (40%)
            'max_stock_allocation': 0.15,       # 종목별 최대 배분 (15%)
            'min_diversification': 5,           # 최소 분산 종목 수
            'max_diversification': 15,          # 최대 분산 종목 수
            'risk_level': 'moderate',           # 위험도 (conservative, moderate, aggressive)
            'rebalance_threshold': 0.1,         # 리밸런싱 임계값 (10%)
            'stop_loss_threshold': 0.05,        # 손절매 임계값 (5%)
            'take_profit_threshold': 0.15,      # 익절매 임계값 (15%)
        }
        
    def _load_daily_investments(self) -> Dict:
        """일일 투자 내역 로드"""
        if os.path.exists(self.daily_investment_file):
            try:
                with open(self.daily_investment_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("일일 투자 내역 로드 완료")
                return data
            except Exception as e:
                logger.error(f"일일 투자 내역 로드 실패: {e}")
        return {}
        
    def _save_daily_investments(self):
        """일일 투자 내역 저장"""
        try:
            with open(self.daily_investment_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_investments, f, ensure_ascii=False, indent=0, default=str)
            # logger.info("일일 투자 내역 저장 완료")  # 로그 제거로 성능 향상
        except Exception as e:
            logger.error(f"일일 투자 내역 저장 실패: {e}")
            
    def _load_portfolio(self) -> Dict:
        """포트폴리오 로드"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("포트폴리오 로드 완료")
                return data
            except Exception as e:
                logger.error(f"포트폴리오 로드 실패: {e}")
        return {
            'stocks': {},
            'sectors': {},
            'total_investment': 0,
            'last_updated': datetime.now().isoformat()
        }
        
    def _save_portfolio(self):
        """포트폴리오 저장"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, ensure_ascii=False, indent=0, default=str)
            # logger.info("포트폴리오 저장 완료")  # 로그 제거로 성능 향상
        except Exception as e:
            logger.error(f"포트폴리오 저장 실패: {e}")
            
    def get_daily_investment_status(self) -> Dict:
        """일일 투자 현황 조회"""
        if self.today not in self.daily_investments:
            self.daily_investments[self.today] = {
                'total_invested': 0,
                'investments': [],
                'remaining_limit': self.config['daily_investment_limit']
            }
            
        daily_data = self.daily_investments[self.today]
        
        return {
            'date': self.today,
            'total_invested': daily_data['total_invested'],
            'remaining_limit': daily_data['remaining_limit'],
            'limit_used_percent': (daily_data['total_invested'] / self.config['daily_investment_limit']) * 100,
            'can_invest': daily_data['remaining_limit'] > 0,
            'investments_count': len(daily_data['investments'])
        }
        
    def can_invest_in_stock(self, stock_code: str, amount: int, stock_info: Dict) -> Tuple[bool, str]:
        """종목 투자 가능 여부 확인"""
        # 1. 일일 투자 한도 확인
        daily_status = self.get_daily_investment_status()
        if not daily_status['can_invest']:
            return False, "일일 투자 한도 초과"
            
        if amount > daily_status['remaining_limit']:
            return False, f"일일 투자 한도 부족 (남은 한도: {daily_status['remaining_limit']:,}원)"
            
        # 2. 단일 종목 투자 한도 확인
        if amount > self.config['max_single_investment']:
            return False, f"단일 종목 투자 한도 초과 (최대: {self.config['max_single_investment']:,}원)"
            
        # 3. 섹터별 배분 한도 확인
        sector = stock_info.get('sector', 'Unknown')
        sector_allocation = self._get_sector_allocation(sector)
        max_sector_amount = self.portfolio['total_investment'] * self.config['max_sector_allocation']
        
        if sector_allocation + amount > max_sector_amount:
            return False, f"섹터별 배분 한도 초과 ({sector})"
            
        # 4. 종목별 배분 한도 확인
        stock_allocation = self._get_stock_allocation(stock_code)
        max_stock_amount = self.portfolio['total_investment'] * self.config['max_stock_allocation']
        
        if stock_allocation + amount > max_stock_amount:
            return False, f"종목별 배분 한도 초과"
            
        # 5. 분산 투자 확인
        if not self._check_diversification(stock_code):
            return False, "분산 투자 기준 미달"
            
        return True, "투자 가능"
        
    def _get_sector_allocation(self, sector: str) -> int:
        """섹터별 현재 배분 금액"""
        return self.portfolio['sectors'].get(sector, {}).get('total_amount', 0)
        
    def _get_stock_allocation(self, stock_code: str) -> int:
        """종목별 현재 배분 금액"""
        return self.portfolio['stocks'].get(stock_code, {}).get('total_amount', 0)
        
    def _check_diversification(self, stock_code: str) -> bool:
        """분산 투자 기준 확인"""
        current_stocks = len(self.portfolio['stocks'])
        
        # 이미 보유 중인 종목이면 분산 기준 만족
        if stock_code in self.portfolio['stocks']:
            return True
            
        # 최소 분산 종목 수 확인
        if current_stocks < self.config['min_diversification']:
            return True
            
        # 최대 분산 종목 수 확인
        if current_stocks >= self.config['max_diversification']:
            return False
            
        return True
        
    def calculate_optimal_investment_amount(self, stock_code: str, stock_info: Dict, available_cash: int) -> int:
        """최적 투자 금액 계산"""
        # 기본 투자 금액 (가용 자금의 10%)
        base_amount = int(available_cash * 0.1)
        
        # 점수에 따른 조정
        score = stock_info.get('score', 5.0)
        if score > 8.0:
            base_amount = int(available_cash * 0.15)  # 높은 점수: 15%
        elif score < 3.0:
            base_amount = int(available_cash * 0.05)  # 낮은 점수: 5%
            
        # 위험도에 따른 조정
        if self.config['risk_level'] == 'conservative':
            base_amount = int(base_amount * 0.7)
        elif self.config['risk_level'] == 'aggressive':
            base_amount = int(base_amount * 1.3)
            
        # 섹터별 배분 고려
        sector = stock_info.get('sector', 'Unknown')
        sector_allocation = self._get_sector_allocation(sector)
        max_sector_amount = self.portfolio['total_investment'] * self.config['max_sector_allocation']
        sector_remaining = max(0, max_sector_amount - sector_allocation)
        
        # 종목별 배분 고려
        stock_allocation = self._get_stock_allocation(stock_code)
        max_stock_amount = self.portfolio['total_investment'] * self.config['max_stock_allocation']
        stock_remaining = max(0, max_stock_amount - stock_allocation)
        
        # 일일 투자 한도 고려
        daily_status = self.get_daily_investment_status()
        daily_remaining = daily_status['remaining_limit']
        
        # 최소값 선택
        optimal_amount = min(
            base_amount,
            self.config['max_single_investment'],
            sector_remaining,
            stock_remaining,
            daily_remaining
        )
        
        # 최소 투자 금액 (10만원)
        return max(100000, optimal_amount)
        
    def record_investment(self, stock_code: str, amount: int, stock_info: Dict):
        """투자 기록"""
        # 일일 투자 기록
        if self.today not in self.daily_investments:
            self.daily_investments[self.today] = {
                'total_invested': 0,
                'investments': [],
                'remaining_limit': self.config['daily_investment_limit']
            }
            
        daily_data = self.daily_investments[self.today]
        daily_data['total_invested'] += amount
        daily_data['remaining_limit'] = max(0, daily_data['remaining_limit'] - amount)
        
        investment_record = {
            'timestamp': datetime.now().isoformat(),
            'stock_code': stock_code,
            'stock_name': stock_info.get('name', ''),
            'sector': stock_info.get('sector', ''),
            'amount': amount,
            'score': stock_info.get('score', 0),
            'strategy': stock_info.get('strategy', ''),
            'reason': stock_info.get('reason', '')
        }
        
        daily_data['investments'].append(investment_record)
        
        # 포트폴리오 업데이트
        self._update_portfolio(stock_code, amount, stock_info)
        
        # 저장
        self._save_daily_investments()
        self._save_portfolio()
        
        # logger.info(f"투자 기록 완료: {stock_info.get('name', stock_code)} - {amount:,}원")  # 로그 제거로 성능 향상
        
    def _update_portfolio(self, stock_code: str, amount: int, stock_info: Dict):
        """포트폴리오 업데이트"""
        sector = stock_info.get('sector', 'Unknown')
        
        # 종목별 정보 업데이트
        if stock_code not in self.portfolio['stocks']:
            self.portfolio['stocks'][stock_code] = {
                'name': stock_info.get('name', ''),
                'sector': sector,
                'total_amount': 0,
                'shares': 0,
                'avg_price': 0,
                'first_investment': datetime.now().isoformat(),
                'last_investment': datetime.now().isoformat()
            }
            
        stock_data = self.portfolio['stocks'][stock_code]
        stock_data['total_amount'] += amount
        stock_data['last_investment'] = datetime.now().isoformat()
        
        # 섹터별 정보 업데이트
        if sector not in self.portfolio['sectors']:
            self.portfolio['sectors'][sector] = {
                'total_amount': 0,
                'stock_count': 0,
                'stocks': []
            }
            
        sector_data = self.portfolio['sectors'][sector]
        sector_data['total_amount'] += amount
        if stock_code not in sector_data['stocks']:
            sector_data['stocks'].append(stock_code)
            sector_data['stock_count'] = len(sector_data['stocks'])
            
        # 전체 투자 금액 업데이트
        self.portfolio['total_investment'] += amount
        self.portfolio['last_updated'] = datetime.now().isoformat()
        
    def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약"""
        if not self.portfolio['stocks']:
            return {
                'total_investment': 0,
                'stock_count': 0,
                'sector_count': 0,
                'diversification_score': 0,
                'sector_allocation': {},
                'top_stocks': []
            }
            
        # 섹터별 배분 비율
        sector_allocation = {}
        for sector, data in self.portfolio['sectors'].items():
            allocation_percent = (data['total_amount'] / self.portfolio['total_investment']) * 100
            sector_allocation[sector] = {
                'amount': data['total_amount'],
                'percentage': round(allocation_percent, 2),
                'stock_count': data['stock_count']
            }
            
        # 상위 종목
        top_stocks = sorted(
            self.portfolio['stocks'].items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        )[:5]
        
        # 분산 투자 점수 (0-100)
        stock_count = len(self.portfolio['stocks'])
        sector_count = len(self.portfolio['sectors'])
        diversification_score = min(100, (stock_count * 10) + (sector_count * 20))
        
        return {
            'total_investment': self.portfolio['total_investment'],
            'stock_count': stock_count,
            'sector_count': sector_count,
            'diversification_score': diversification_score,
            'sector_allocation': sector_allocation,
            'top_stocks': [
                {
                    'code': code,
                    'name': data['name'],
                    'amount': data['total_amount'],
                    'percentage': round((data['total_amount'] / self.portfolio['total_investment']) * 100, 2)
                }
                for code, data in top_stocks
            ]
        }
        
    def get_investment_recommendations(self, available_cash: int) -> List[Dict]:
        """투자 추천"""
        recommendations = []
        
        # 현재 포트폴리오 분석
        portfolio_summary = self.get_portfolio_summary()
        daily_status = self.get_daily_investment_status()
        
        # 분산 투자 개선 필요 여부
        if portfolio_summary['diversification_score'] < 70:
            recommendations.append({
                'type': 'diversification',
                'priority': 'high',
                'message': f"분산 투자 개선 필요 (현재 점수: {portfolio_summary['diversification_score']})",
                'action': "새로운 섹터나 종목 추가 고려"
            })
            
        # 섹터별 과다 배분 확인
        for sector, data in portfolio_summary['sector_allocation'].items():
            if data['percentage'] > self.config['max_sector_allocation'] * 100:
                recommendations.append({
                    'type': 'sector_allocation',
                    'priority': 'medium',
                    'message': f"{sector} 섹터 과다 배분 ({data['percentage']}%)",
                    'action': f"다른 섹터 투자 확대"
                })
                
        # 일일 투자 한도 확인
        if daily_status['limit_used_percent'] > 80:
            recommendations.append({
                'type': 'daily_limit',
                'priority': 'high',
                'message': f"일일 투자 한도 {daily_status['limit_used_percent']:.1f}% 사용",
                'action': "투자 한도 관리 필요"
            })
            
        return recommendations
        
    def generate_investment_report(self) -> str:
        """투자 리포트 생성"""
        daily_status = self.get_daily_investment_status()
        portfolio_summary = self.get_portfolio_summary()
        recommendations = self.get_investment_recommendations(0)
        
        report = f"""
💰 투자 관리 리포트 - {self.today}
{'='*60}
📊 일일 투자 현황:
  • 총 투자 금액: {daily_status['total_invested']:,}원
  • 남은 한도: {daily_status['remaining_limit']:,}원
  • 한도 사용률: {daily_status['limit_used_percent']:.1f}%
  • 투자 종목 수: {daily_status['investments_count']}개

📈 포트폴리오 현황:
  • 총 투자 금액: {portfolio_summary['total_investment']:,}원
  • 보유 종목 수: {portfolio_summary['stock_count']}개
  • 섹터 수: {portfolio_summary['sector_count']}개
  • 분산 투자 점수: {portfolio_summary['diversification_score']}/100

📊 섹터별 배분:"""
        
        for sector, data in portfolio_summary['sector_allocation'].items():
            report += f"\n  • {sector}: {data['amount']:,}원 ({data['percentage']}%) - {data['stock_count']}개 종목"
            
        report += f"\n\n🏆 상위 투자 종목:"
        for stock in portfolio_summary['top_stocks']:
            report += f"\n  • {stock['name']}({stock['code']}): {stock['amount']:,}원 ({stock['percentage']}%)"
            
        if recommendations:
            report += f"\n\n⚠️ 투자 추천사항:"
            for rec in recommendations:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
                report += f"\n  {priority_icon} {rec['message']}"
                report += f"\n     → {rec['action']}"
                
        return report

def main():
    """메인 함수"""
    print("💰 투자 관리 시스템 시작")
    print("=" * 60)
    
    # 투자 관리 시스템 생성
    investment_manager = InvestmentManager()
    
    # 일일 투자 현황 확인
    daily_status = investment_manager.get_daily_investment_status()
    print(f"📊 일일 투자 현황:")
    print(f"  • 총 투자: {daily_status['total_invested']:,}원")
    print(f"  • 남은 한도: {daily_status['remaining_limit']:,}원")
    print(f"  • 사용률: {daily_status['limit_used_percent']:.1f}%")
    
    # 포트폴리오 요약
    portfolio_summary = investment_manager.get_portfolio_summary()
    print(f"\n📈 포트폴리오 요약:")
    print(f"  • 총 투자: {portfolio_summary['total_investment']:,}원")
    print(f"  • 종목 수: {portfolio_summary['stock_count']}개")
    print(f"  • 섹터 수: {portfolio_summary['sector_count']}개")
    print(f"  • 분산 점수: {portfolio_summary['diversification_score']}/100")
    
    # 투자 추천
    recommendations = investment_manager.get_investment_recommendations(10000000)
    if recommendations:
        print(f"\n💡 투자 추천:")
        for rec in recommendations:
            print(f"  • {rec['message']}")
    
    print("\n" + "=" * 60)
    print("✅ 투자 관리 시스템 준비 완료!")

if __name__ == "__main__":
    main() 