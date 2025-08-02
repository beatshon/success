#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하이브리드 트레이딩 시스템
뉴스 분석 + 기술적 분석을 결합한 종합 매매 시스템
"""

import pandas as pd
import numpy as np
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import yfinance as yf
import pandas_ta as ta

@dataclass
class TechnicalSignal:
    """기술적 분석 신호"""
    stock_code: str
    stock_name: str
    rsi: float
    macd_signal: str  # 'buy', 'sell', 'hold'
    moving_average_signal: str  # 'above', 'below', 'cross'
    volume_signal: str  # 'high', 'normal', 'low'
    support_level: float
    resistance_level: float
    overall_signal: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    confidence: float  # 0-100

@dataclass
class HybridSignal:
    """하이브리드 매매 신호"""
    stock_code: str
    stock_name: str
    news_score: float
    technical_score: float
    combined_score: float
    final_signal: str  # '매수', '매도', '관망', '강력매수', '강력매도'
    confidence: float
    reasoning: str

class TechnicalAnalyzer:
    """기술적 분석 엔진"""
    
    def __init__(self):
        self.logger = logger
    
    def get_stock_data(self, stock_code: str, period: str = "1mo") -> pd.DataFrame:
        """주식 데이터 수집"""
        try:
            # 한국 주식은 .KS 접미사 추가
            ticker = f"{stock_code}.KS"
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty:
                self.logger.warning(f"주식 데이터를 가져올 수 없습니다: {stock_code}")
                return pd.DataFrame()
            
            return data
        except Exception as e:
            self.logger.error(f"주식 데이터 수집 오류: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """RSI 계산"""
        if len(data) < period:
            return 50.0
        
        try:
            rsi = talib.RSI(data['Close'].values, timeperiod=period)
            return float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0
        except:
            return 50.0
    
    def calculate_macd(self, data: pd.DataFrame) -> Tuple[str, float]:
        """MACD 신호 계산"""
        if len(data) < 26:
            return 'hold', 0.0
        
        try:
            macd, signal, hist = talib.MACD(data['Close'].values)
            
            if len(macd) < 2 or len(signal) < 2:
                return 'hold', 0.0
            
            # MACD가 시그널선을 상향돌파
            if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
                return 'buy', float(hist[-1])
            # MACD가 시그널선을 하향돌파
            elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
                return 'sell', float(hist[-1])
            else:
                return 'hold', float(hist[-1])
        except:
            return 'hold', 0.0
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> Tuple[str, float]:
        """이동평균 신호 계산"""
        if len(data) < 20:
            return 'below', 0.0
        
        try:
            ma5 = talib.SMA(data['Close'].values, timeperiod=5)
            ma20 = talib.SMA(data['Close'].values, timeperiod=20)
            
            current_price = data['Close'].iloc[-1]
            ma5_current = ma5[-1]
            ma20_current = ma20[-1]
            
            # 골든크로스 (5일선이 20일선을 상향돌파)
            if ma5_current > ma20_current and ma5[-2] <= ma20[-2]:
                return 'cross_up', current_price
            # 데드크로스 (5일선이 20일선을 하향돌파)
            elif ma5_current < ma20_current and ma5[-2] >= ma20[-2]:
                return 'cross_down', current_price
            # 5일선이 20일선 위에 있음
            elif ma5_current > ma20_current:
                return 'above', current_price
            else:
                return 'below', current_price
        except:
            return 'below', 0.0
    
    def calculate_volume_signal(self, data: pd.DataFrame) -> str:
        """거래량 신호 계산"""
        if len(data) < 20:
            return 'normal'
        
        try:
            avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            
            if current_volume > avg_volume * 1.5:
                return 'high'
            elif current_volume < avg_volume * 0.5:
                return 'low'
            else:
                return 'normal'
        except:
            return 'normal'
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Tuple[float, float]:
        """지지/저항선 계산"""
        if len(data) < 20:
            return 0.0, 0.0
        
        try:
            # 최근 20일간의 최저/최고가
            support = data['Low'].tail(20).min()
            resistance = data['High'].tail(20).max()
            return float(support), float(resistance)
        except:
            return 0.0, 0.0
    
    def analyze_stock(self, stock_code: str, stock_name: str) -> TechnicalSignal:
        """종목 기술적 분석"""
        data = self.get_stock_data(stock_code)
        
        if data.empty:
            return TechnicalSignal(
                stock_code=stock_code,
                stock_name=stock_name,
                rsi=50.0,
                macd_signal='hold',
                moving_average_signal='below',
                volume_signal='normal',
                support_level=0.0,
                resistance_level=0.0,
                overall_signal='hold',
                confidence=0.0
            )
        
        # 각종 지표 계산
        rsi = self.calculate_rsi(data)
        macd_signal, macd_value = self.calculate_macd(data)
        ma_signal, current_price = self.calculate_moving_averages(data)
        volume_signal = self.calculate_volume_signal(data)
        support, resistance = self.calculate_support_resistance(data)
        
        # 종합 신호 계산
        overall_signal, confidence = self._calculate_overall_signal(
            rsi, macd_signal, ma_signal, volume_signal, current_price, support, resistance
        )
        
        return TechnicalSignal(
            stock_code=stock_code,
            stock_name=stock_name,
            rsi=rsi,
            macd_signal=macd_signal,
            moving_average_signal=ma_signal,
            volume_signal=volume_signal,
            support_level=support,
            resistance_level=resistance,
            overall_signal=overall_signal,
            confidence=confidence
        )
    
    def _calculate_overall_signal(self, rsi: float, macd: str, ma: str, 
                                volume: str, price: float, support: float, resistance: float) -> Tuple[str, float]:
        """종합 신호 계산"""
        score = 0
        reasons = []
        
        # RSI 분석
        if rsi < 30:
            score += 20
            reasons.append("RSI 과매도")
        elif rsi > 70:
            score -= 20
            reasons.append("RSI 과매수")
        elif 40 <= rsi <= 60:
            score += 10
            reasons.append("RSI 중립")
        
        # MACD 분석
        if macd == 'buy':
            score += 15
            reasons.append("MACD 매수신호")
        elif macd == 'sell':
            score -= 15
            reasons.append("MACD 매도신호")
        
        # 이동평균 분석
        if ma == 'cross_up':
            score += 20
            reasons.append("골든크로스")
        elif ma == 'cross_down':
            score -= 20
            reasons.append("데드크로스")
        elif ma == 'above':
            score += 10
            reasons.append("상승추세")
        elif ma == 'below':
            score -= 10
            reasons.append("하락추세")
        
        # 거래량 분석
        if volume == 'high':
            score += 5
            reasons.append("거래량 급증")
        elif volume == 'low':
            score -= 5
            reasons.append("거래량 감소")
        
        # 지지/저항 분석
        if support > 0 and price <= support * 1.02:
            score += 10
            reasons.append("지지선 근처")
        if resistance > 0 and price >= resistance * 0.98:
            score -= 10
            reasons.append("저항선 근처")
        
        # 신호 결정
        if score >= 30:
            signal = 'strong_buy'
        elif score >= 15:
            signal = 'buy'
        elif score <= -30:
            signal = 'strong_sell'
        elif score <= -15:
            signal = 'sell'
        else:
            signal = 'hold'
        
        # 신뢰도 계산 (0-100)
        confidence = min(100, max(0, abs(score) * 2))
        
        return signal, confidence

class HybridTradingSystem:
    """하이브리드 트레이딩 시스템"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.logger = logger
        
        # 종목 정보
        self.stocks = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI',
            '373220': 'LG에너지솔루션',
            '005380': '현대자동차',
            '000270': '기아',
            '005490': 'POSCO',
            '207940': '삼성바이오로직스',
            '068270': '셀트리온',
            '030200': 'KT',
            '017670': 'SK텔레콤',
            '035000': 'HS애드',
            '068400': 'AJ렌터카',
            '035250': '강원랜드',
            '051900': 'LG생활건강',
            '323410': '카카오뱅크',
            '015760': '한국전력'
        }
    
    def load_news_analysis(self) -> Dict[str, float]:
        """뉴스 분석 결과 로드"""
        try:
            # 최신 뉴스 분석 파일 찾기
            import glob
            import os
            
            news_files = glob.glob('data/news_analysis/stock_analysis_*.csv')
            if not news_files:
                self.logger.warning("뉴스 분석 파일을 찾을 수 없습니다.")
                return {}
            
            latest_file = max(news_files, key=os.path.getctime)
            df = pd.read_csv(latest_file)
            
            news_scores = {}
            for _, row in df.iterrows():
                stock_code = str(row['stock_code']).zfill(6)
                investment_score = float(row['investment_score'])
                news_scores[stock_code] = investment_score
            
            return news_scores
        except Exception as e:
            self.logger.error(f"뉴스 분석 로드 오류: {e}")
            return {}
    
    def analyze_all_stocks(self) -> List[HybridSignal]:
        """모든 종목 하이브리드 분석"""
        self.logger.info("하이브리드 분석 시작...")
        
        # 뉴스 분석 결과 로드
        news_scores = self.load_news_analysis()
        
        hybrid_signals = []
        
        for stock_code, stock_name in self.stocks.items():
            try:
                # 기술적 분석
                technical_signal = self.technical_analyzer.analyze_stock(stock_code, stock_name)
                
                # 뉴스 점수 (기본값 50)
                news_score = news_scores.get(stock_code, 50.0)
                
                # 하이브리드 신호 생성
                hybrid_signal = self._create_hybrid_signal(
                    stock_code, stock_name, news_score, technical_signal
                )
                
                hybrid_signals.append(hybrid_signal)
                
                self.logger.info(f"{stock_name}({stock_code}): {hybrid_signal.final_signal} "
                               f"(뉴스: {news_score:.1f}, 기술: {technical_signal.confidence:.1f})")
                
            except Exception as e:
                self.logger.error(f"{stock_name}({stock_code}) 분석 오류: {e}")
                continue
        
        # 점수 순으로 정렬
        hybrid_signals.sort(key=lambda x: x.combined_score, reverse=True)
        
        return hybrid_signals
    
    def _create_hybrid_signal(self, stock_code: str, stock_name: str, 
                            news_score: float, technical: TechnicalSignal) -> HybridSignal:
        """하이브리드 신호 생성"""
        
        # 기술적 점수를 0-100 스케일로 변환
        technical_score = technical.confidence
        if technical.overall_signal in ['sell', 'strong_sell']:
            technical_score = 100 - technical_score
        
        # 가중 평균 계산 (뉴스 40%, 기술 60%)
        combined_score = (news_score * 0.4) + (technical_score * 0.6)
        
        # 최종 신호 결정
        if combined_score >= 80:
            final_signal = "강력매수"
        elif combined_score >= 60:
            final_signal = "매수"
        elif combined_score <= 20:
            final_signal = "강력매도"
        elif combined_score <= 40:
            final_signal = "매도"
        else:
            final_signal = "관망"
        
        # 신뢰도 계산
        confidence = min(100, combined_score)
        
        # 추론 과정 설명
        reasoning = self._generate_reasoning(news_score, technical, final_signal)
        
        return HybridSignal(
            stock_code=stock_code,
            stock_name=stock_name,
            news_score=news_score,
            technical_score=technical_score,
            combined_score=combined_score,
            final_signal=final_signal,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _generate_reasoning(self, news_score: float, technical: TechnicalSignal, 
                          final_signal: str) -> str:
        """추론 과정 생성"""
        reasons = []
        
        # 뉴스 분석 결과
        if news_score >= 70:
            reasons.append("뉴스 감정 매우 긍정적")
        elif news_score >= 50:
            reasons.append("뉴스 감정 중립적")
        else:
            reasons.append("뉴스 감정 부정적")
        
        # 기술적 분석 결과
        if technical.overall_signal == 'strong_buy':
            reasons.append("기술적 지표 강력 매수")
        elif technical.overall_signal == 'buy':
            reasons.append("기술적 지표 매수")
        elif technical.overall_signal == 'strong_sell':
            reasons.append("기술적 지표 강력 매도")
        elif technical.overall_signal == 'sell':
            reasons.append("기술적 지표 매도")
        else:
            reasons.append("기술적 지표 중립")
        
        # RSI 정보
        if technical.rsi < 30:
            reasons.append("RSI 과매도")
        elif technical.rsi > 70:
            reasons.append("RSI 과매수")
        
        # 이동평균 정보
        if technical.moving_average_signal == 'cross_up':
            reasons.append("골든크로스 발생")
        elif technical.moving_average_signal == 'cross_down':
            reasons.append("데드크로스 발생")
        
        return " | ".join(reasons)
    
    def save_analysis_results(self, signals: List[HybridSignal]):
        """분석 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # CSV 파일로 저장
            data = []
            for signal in signals:
                data.append({
                    'stock_code': signal.stock_code,
                    'stock_name': signal.stock_name,
                    'news_score': signal.news_score,
                    'technical_score': signal.technical_score,
                    'combined_score': signal.combined_score,
                    'final_signal': signal.final_signal,
                    'confidence': signal.confidence,
                    'reasoning': signal.reasoning,
                    'timestamp': timestamp
                })
            
            df = pd.DataFrame(data)
            filename = f'data/hybrid_analysis/hybrid_analysis_{timestamp}.csv'
            
            # 디렉토리 생성
            import os
            os.makedirs('data/hybrid_analysis', exist_ok=True)
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"하이브리드 분석 결과 저장: {filename}")
            
            # 요약 리포트 생성
            self._create_summary_report(signals, timestamp)
            
        except Exception as e:
            self.logger.error(f"결과 저장 오류: {e}")
    
    def _create_summary_report(self, signals: List[HybridSignal], timestamp: str):
        """요약 리포트 생성"""
        try:
            report = f"""
=== 하이브리드 트레이딩 분석 리포트 ===
분석 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
총 분석 종목: {len(signals)}개

📈 매수 추천 종목:
"""
            
            buy_signals = [s for s in signals if '매수' in s.final_signal]
            for signal in buy_signals[:5]:  # 상위 5개
                report += f"• {signal.stock_name}({signal.stock_code}): {signal.final_signal} "
                report += f"(종합점수: {signal.combined_score:.1f})\n"
            
            report += f"\n📉 매도 추천 종목:\n"
            sell_signals = [s for s in signals if '매도' in s.final_signal]
            for signal in sell_signals[:5]:  # 상위 5개
                report += f"• {signal.stock_name}({signal.stock_code}): {signal.final_signal} "
                report += f"(종합점수: {signal.combined_score:.1f})\n"
            
            report += f"\n📊 섹터별 분석:\n"
            sector_analysis = self._analyze_sectors(signals)
            for sector, count in sector_analysis.items():
                report += f"• {sector}: {count}개 종목\n"
            
            # 파일로 저장
            filename = f'data/hybrid_analysis/hybrid_report_{timestamp}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"요약 리포트 저장: {filename}")
            
        except Exception as e:
            self.logger.error(f"리포트 생성 오류: {e}")
    
    def _analyze_sectors(self, signals: List[HybridSignal]) -> Dict[str, int]:
        """섹터별 분석"""
        sector_mapping = {
            '005930': '반도체', '000660': '반도체',
            '035420': 'IT', '035720': 'IT',
            '051910': '화학', '006400': '화학', '373220': '화학', '051900': '화학',
            '005380': '자동차', '000270': '자동차',
            '005490': '철강',
            '207940': '바이오', '068270': '바이오',
            '030200': '통신', '017670': '통신',
            '035000': '서비스', '068400': '서비스', '035250': '서비스',
            '323410': '금융',
            '015760': '에너지'
        }
        
        sector_counts = {}
        for signal in signals:
            sector = sector_mapping.get(signal.stock_code, '기타')
            if '매수' in signal.final_signal:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        return sector_counts

def main():
    """메인 실행 함수"""
    logger.info("하이브리드 트레이딩 시스템 시작")
    
    # 시스템 초기화
    system = HybridTradingSystem()
    
    # 하이브리드 분석 실행
    signals = system.analyze_all_stocks()
    
    # 결과 저장
    system.save_analysis_results(signals)
    
    # 상위 10개 종목 출력
    logger.info("\n=== 상위 10개 종목 ===")
    for i, signal in enumerate(signals[:10], 1):
        logger.info(f"{i:2d}. {signal.stock_name}({signal.stock_code}): "
                   f"{signal.final_signal} (점수: {signal.combined_score:.1f})")
    
    logger.info("하이브리드 트레이딩 시스템 완료")

if __name__ == "__main__":
    main() 