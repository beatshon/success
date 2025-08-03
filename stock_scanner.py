#!/usr/bin/env python3
"""
주식 종목 스캐너
실시간으로 주식 종목을 스캔하고 선정 기준에 맞는 종목을 찾습니다.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import config
from loguru import logger

class StockScanner:
    """주식 종목 스캐너"""
    
    def __init__(self):
        self.scan_results = {}
        self.selected_stocks = []
        self.scan_criteria = {
            'volume_threshold': 1000000,  # 거래량 기준 (1백만주)
            'price_range': (5000, 500000),  # 가격 범위 (5천원 ~ 50만원)
            'market_cap_min': 1000000000000,  # 시가총액 최소 (1조원)
            'volatility_min': 0.02,  # 변동성 최소 (2%)
            'momentum_threshold': 0.05,  # 모멘텀 기준 (5%)
            'rsi_range': (20, 80),  # RSI 범위
            'ma_trend': True,  # 이동평균 트렌드 확인
        }
        
    def generate_market_data(self) -> pd.DataFrame:
        """전체 시장 데이터 생성 (모의 데이터)"""
        # KOSPI 상위 종목들 (실제로는 API에서 가져옴)
        kospi_stocks = [
            {'code': '005930', 'name': '삼성전자', 'sector': '전기전자'},
            {'code': '000660', 'name': 'SK하이닉스', 'sector': '전기전자'},
            {'code': '035420', 'name': 'NAVER', 'sector': '서비스업'},
            {'code': '051910', 'name': 'LG화학', 'sector': '화학'},
            {'code': '006400', 'name': '삼성SDI', 'sector': '전기전자'},
            {'code': '035720', 'name': '카카오', 'sector': '서비스업'},
            {'code': '207940', 'name': '삼성바이오로직스', 'sector': '의약품'},
            {'code': '068270', 'name': '셀트리온', 'sector': '의약품'},
            {'code': '323410', 'name': '카카오뱅크', 'sector': '금융업'},
            {'code': '373220', 'name': 'LG에너지솔루션', 'sector': '전기전자'},
            {'code': '005380', 'name': '현대차', 'sector': '운수장비'},
            {'code': '000270', 'name': '기아', 'sector': '운수장비'},
            {'code': '051900', 'name': 'LG생활건강', 'sector': '화학'},
            {'code': '006980', 'name': '우성사료', 'sector': '음식료품'},
            {'code': '017670', 'name': 'SK텔레콤', 'sector': '통신업'},
        ]
        
        market_data = []
        
        for stock in kospi_stocks:
            # 랜덤 시장 데이터 생성
            base_price = np.random.randint(10000, 200000)
            current_price = base_price * (1 + np.random.uniform(-0.1, 0.1))
            volume = np.random.randint(100000, 5000000)
            market_cap = current_price * np.random.randint(1000000, 100000000)
            
            # 기술적 지표 계산
            rsi = np.random.uniform(10, 90)
            momentum = np.random.uniform(-0.2, 0.2)
            volatility = np.random.uniform(0.01, 0.1)
            
            # 이동평균 계산
            ma5 = current_price * (1 + np.random.uniform(-0.05, 0.05))
            ma20 = current_price * (1 + np.random.uniform(-0.1, 0.1))
            ma_trend = ma5 > ma20
            
            market_data.append({
                'code': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'current_price': int(current_price),
                'volume': volume,
                'market_cap': int(market_cap),
                'rsi': round(rsi, 2),
                'momentum': round(momentum, 4),
                'volatility': round(volatility, 4),
                'ma5': int(ma5),
                'ma20': int(ma20),
                'ma_trend': ma_trend,
                'price_change': round(np.random.uniform(-0.1, 0.1) * 100, 2),
                'volume_change': round(np.random.uniform(-0.5, 2.0) * 100, 2),
            })
            
        return pd.DataFrame(market_data)
        
    def scan_volume_leaders(self, market_data: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """거래량 상위 종목 스캔"""
        volume_leaders = market_data.nlargest(top_n, 'volume')
        logger.info(f"거래량 상위 {top_n}종목 스캔 완료")
        return volume_leaders
        
    def scan_momentum_stocks(self, market_data: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
        """모멘텀 상위 종목 스캔"""
        momentum_stocks = market_data[market_data['momentum'] > threshold].copy()
        momentum_stocks = momentum_stocks.sort_values('momentum', ascending=False)
        logger.info(f"모멘텀 상위 종목 {len(momentum_stocks)}개 발견")
        return momentum_stocks
        
    def scan_oversold_stocks(self, market_data: pd.DataFrame, rsi_threshold: int = 30) -> pd.DataFrame:
        """과매도 종목 스캔"""
        oversold_stocks = market_data[market_data['rsi'] < rsi_threshold].copy()
        oversold_stocks = oversold_stocks.sort_values('rsi', ascending=True)
        logger.info(f"과매도 종목 {len(oversold_stocks)}개 발견")
        return oversold_stocks
        
    def scan_overbought_stocks(self, market_data: pd.DataFrame, rsi_threshold: int = 70) -> pd.DataFrame:
        """과매수 종목 스캔"""
        overbought_stocks = market_data[market_data['rsi'] > rsi_threshold].copy()
        overbought_stocks = overbought_stocks.sort_values('rsi', ascending=False)
        logger.info(f"과매수 종목 {len(overbought_stocks)}개 발견")
        return overbought_stocks
        
    def scan_breakout_stocks(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """브레이크아웃 종목 스캔 (이동평균 상향 돌파)"""
        breakout_stocks = market_data[
            (market_data['ma_trend'] == True) & 
            (market_data['current_price'] > market_data['ma5']) &
            (market_data['ma5'] > market_data['ma20'])
        ].copy()
        logger.info(f"브레이크아웃 종목 {len(breakout_stocks)}개 발견")
        return breakout_stocks
        
    def scan_sector_leaders(self, market_data: pd.DataFrame, sector: str) -> pd.DataFrame:
        """섹터별 리더 종목 스캔"""
        sector_stocks = market_data[market_data['sector'] == sector].copy()
        if len(sector_stocks) > 0:
            sector_leaders = sector_stocks.nlargest(3, 'market_cap')
            logger.info(f"{sector} 섹터 리더 {len(sector_leaders)}개 발견")
            return sector_leaders
        return pd.DataFrame()
        
    def apply_selection_criteria(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """종목 선정 기준 적용"""
        criteria = self.scan_criteria
        
        # 기본 필터링
        filtered_stocks = market_data[
            (market_data['volume'] >= criteria['volume_threshold']) &
            (market_data['current_price'] >= criteria['price_range'][0]) &
            (market_data['current_price'] <= criteria['price_range'][1]) &
            (market_data['market_cap'] >= criteria['market_cap_min']) &
            (market_data['volatility'] >= criteria['volatility_min'])
        ].copy()
        
        # 모멘텀 필터링
        momentum_stocks = filtered_stocks[
            abs(filtered_stocks['momentum']) >= criteria['momentum_threshold']
        ]
        
        # RSI 필터링
        rsi_stocks = filtered_stocks[
            (filtered_stocks['rsi'] >= criteria['rsi_range'][0]) &
            (filtered_stocks['rsi'] <= criteria['rsi_range'][1])
        ]
        
        # 이동평균 트렌드 필터링
        if criteria['ma_trend']:
            trend_stocks = filtered_stocks[filtered_stocks['ma_trend'] == True]
        else:
            trend_stocks = filtered_stocks
            
        # 종합 점수 계산
        filtered_stocks['score'] = (
            filtered_stocks['momentum'] * 0.3 +
            (50 - abs(filtered_stocks['rsi'] - 50)) * 0.2 +
            filtered_stocks['volume'] / 1000000 * 0.2 +
            filtered_stocks['volatility'] * 0.3
        )
        
        # 상위 종목 선정
        selected_stocks = filtered_stocks.nlargest(10, 'score')
        
        logger.info(f"선정 기준 적용 완료: {len(selected_stocks)}개 종목 선정")
        return selected_stocks
        
    def run_comprehensive_scan(self) -> Dict[str, pd.DataFrame]:
        """종합 스캔 실행"""
        logger.info("🔍 종합 주식 스캔 시작")
        
        # 시장 데이터 생성
        market_data = self.generate_market_data()
        
        # 다양한 스캔 실행
        scan_results = {
            'volume_leaders': self.scan_volume_leaders(market_data),
            'momentum_stocks': self.scan_momentum_stocks(market_data),
            'oversold_stocks': self.scan_oversold_stocks(market_data),
            'overbought_stocks': self.scan_overbought_stocks(market_data),
            'breakout_stocks': self.scan_breakout_stocks(market_data),
            'selected_stocks': self.apply_selection_criteria(market_data)
        }
        
        # 섹터별 리더 스캔
        sectors = ['전기전자', '서비스업', '화학', '의약품']
        for sector in sectors:
            sector_leaders = self.scan_sector_leaders(market_data, sector)
            if not sector_leaders.empty:
                scan_results[f'{sector}_leaders'] = sector_leaders
                
        self.scan_results = scan_results
        return scan_results
        
    def get_recommended_stocks(self, max_stocks: int = 5) -> List[Dict]:
        """추천 종목 리스트 반환"""
        if not self.scan_results:
            self.run_comprehensive_scan()
            
        selected_stocks = self.scan_results.get('selected_stocks', pd.DataFrame())
        
        if selected_stocks.empty:
            return []
            
        # 상위 종목 선택
        top_stocks = selected_stocks.head(max_stocks)
        
        recommended_stocks = []
        for _, stock in top_stocks.iterrows():
            recommended_stocks.append({
                'code': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'current_price': stock['current_price'],
                'score': round(stock['score'], 2),
                'momentum': stock['momentum'],
                'rsi': stock['rsi'],
                'volume': stock['volume'],
                'reason': self._get_selection_reason(stock)
            })
            
        return recommended_stocks
        
    def _get_selection_reason(self, stock: pd.Series) -> str:
        """종목 선정 이유 생성"""
        reasons = []
        
        if stock['momentum'] > 0.05:
            reasons.append("강한 상승 모멘텀")
        elif stock['momentum'] < -0.05:
            reasons.append("강한 하락 모멘텀")
            
        if stock['rsi'] < 30:
            reasons.append("과매도 구간")
        elif stock['rsi'] > 70:
            reasons.append("과매수 구간")
            
        if stock['ma_trend']:
            reasons.append("상승 트렌드")
            
        if stock['volume'] > 2000000:
            reasons.append("높은 거래량")
            
        return ", ".join(reasons) if reasons else "기술적 지표 양호"

def main():
    """메인 함수"""
    print("🔍 주식 종목 스캐너 시작")
    print("=" * 60)
    
    # 스캐너 생성 및 실행
    scanner = StockScanner()
    scan_results = scanner.run_comprehensive_scan()
    
    # 추천 종목 출력
    recommended_stocks = scanner.get_recommended_stocks(max_stocks=5)
    
    print("\n📊 추천 종목 리스트")
    print("=" * 60)
    
    for i, stock in enumerate(recommended_stocks, 1):
        print(f"{i}. {stock['name']}({stock['code']}) - {stock['sector']}")
        print(f"   💰 가격: {stock['current_price']:,}원")
        print(f"   📈 점수: {stock['score']}")
        print(f"   🚀 모멘텀: {stock['momentum']:+.2%}")
        print(f"   📊 RSI: {stock['rsi']:.1f}")
        print(f"   📈 거래량: {stock['volume']:,}주")
        print(f"   💡 선정 이유: {stock['reason']}")
        print()
        
    print("✅ 종목 스캔 완료!")

if __name__ == "__main__":
    main() 