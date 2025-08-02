#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주식 뉴스 분석기
뉴스 데이터를 분석하여 종목별 투자 기회를 찾는 시스템
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import json
import re
from collections import defaultdict, Counter

@dataclass
class StockAnalysis:
    """종목 분석 결과 데이터 클래스"""
    stock_code: str
    stock_name: str
    news_count: int
    positive_news: int
    negative_news: int
    neutral_news: int
    sentiment_score: float
    keyword_frequency: Dict[str, int]
    recent_news: List[str]
    recent_news_links: List[str]  # 뉴스 링크 추가
    investment_score: float
    risk_level: str
    recommendation: str

class StockNewsAnalyzer:
    """주식 뉴스 분석기"""
    
    def __init__(self):
        """뉴스 분석기 초기화"""
        self.stock_names = self._load_stock_names()
        self.positive_keywords = self._load_positive_keywords()
        self.negative_keywords = self._load_negative_keywords()
        self.risk_keywords = self._load_risk_keywords()
        
        logger.info("주식 뉴스 분석기 초기화 완료")
    
    def _load_stock_names(self) -> Dict[str, str]:
        """종목 코드와 이름 매핑"""
        return {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035420": "NAVER",
            "051910": "LG화학",
            "006400": "삼성SDI",
            "035720": "카카오",
            "207940": "삼성바이오로직스",
            "068270": "셀트리온",
            "323410": "카카오뱅크",
            "051900": "LG생활건강",
            "017670": "SK텔레콤",
            "030200": "KT",
            "032640": "LG유플러스",
            "373220": "LG에너지솔루션",
            "005380": "현대자동차",
            "000270": "기아",
            "005490": "POSCO",
            "015760": "한국전력",
            "035250": "강원랜드",
            "068400": "AJ렌터카",
            "035000": "HS애드"
        }
    
    def _load_positive_keywords(self) -> List[str]:
        """긍정적 키워드"""
        return [
            "상승", "급등", "호재", "실적개선", "매출증가", "이익증가",
            "성장", "확장", "신기술", "혁신", "파트너십", "계약",
            "승인", "허가", "특허", "상장", "배당", "자사주매입",
            "매수", "투자", "발전", "성공", "돌파", "신고가",
            "강세", "상향", "긍정", "호전", "회복", "반등"
        ]
    
    def _load_negative_keywords(self) -> List[str]:
        """부정적 키워드"""
        return [
            "하락", "급락", "악재", "실적악화", "매출감소", "이익감소",
            "손실", "적자", "부도", "파산", "폐업", "해고",
            "반발", "소송", "규제", "제재", "벌금", "조사",
            "매도", "청산", "폐쇄", "실패", "하향", "신저가",
            "약세", "부정", "악화", "침체", "하락", "폭락"
        ]
    
    def _load_risk_keywords(self) -> List[str]:
        """위험 키워드"""
        return [
            "리스크", "위험", "불확실성", "변동성", "폭등", "폭락",
            "조작", "부정", "비리", "사기", "허위", "과장",
            "규제", "제재", "조사", "소송", "분쟁", "갈등",
            "정치", "정책", "법안", "세금", "관세", "무역분쟁"
        ]
    
    def analyze_news_sentiment(self, text: str) -> Tuple[float, str]:
        """
        뉴스 텍스트의 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            (감정 점수, 감정 레이블)
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return 0.0, "neutral"
        
        sentiment_score = (positive_count - negative_count) / total_keywords
        
        if sentiment_score > 0.3:
            sentiment_label = "positive"
        elif sentiment_score < -0.3:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return sentiment_score, sentiment_label
    
    def analyze_stock_news(self, news_items: List) -> Dict[str, StockAnalysis]:
        """
        종목별 뉴스 분석
        
        Args:
            news_items: 뉴스 아이템 리스트
            
        Returns:
            종목별 분석 결과
        """
        stock_analysis = {}
        
        # 종목별 뉴스 그룹화
        stock_news = defaultdict(list)
        for news in news_items:
            for stock_code in news.related_stocks:
                stock_news[stock_code].append(news)
        
        # 종목별 분석 수행
        for stock_code, news_list in stock_news.items():
            if len(news_list) == 0:
                continue
            
            # 감정 분석
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            total_sentiment = 0.0
            
            # 키워드 빈도 분석
            keyword_freq = Counter()
            recent_titles = []
            recent_links = []
            
            for news in news_list:
                # 감정 분석
                sentiment_score, sentiment_label = self.analyze_news_sentiment(
                    news.title + " " + news.description
                )
                
                if sentiment_label == "positive":
                    positive_count += 1
                elif sentiment_label == "negative":
                    negative_count += 1
                else:
                    neutral_count += 1
                
                total_sentiment += sentiment_score
                
                # 키워드 빈도
                for keyword in news.keywords:
                    keyword_freq[keyword] += 1
                
                # 최근 뉴스 제목과 링크 (최대 5개)
                if len(recent_titles) < 5:
                    recent_titles.append(news.title)
                    recent_links.append(f"{news.title}|{news.link}")
            
            # 평균 감정 점수
            avg_sentiment = total_sentiment / len(news_list) if news_list else 0.0
            
            # 투자 점수 계산
            investment_score = self._calculate_investment_score(
                len(news_list), positive_count, negative_count, avg_sentiment
            )
            
            # 위험도 평가
            risk_level = self._assess_risk_level(news_list)
            
            # 투자 추천
            recommendation = self._generate_recommendation(investment_score, risk_level)
            
            # 분석 결과 저장
            stock_analysis[stock_code] = StockAnalysis(
                stock_code=stock_code,
                stock_name=self.stock_names.get(stock_code, "Unknown"),
                news_count=len(news_list),
                positive_news=positive_count,
                negative_news=negative_count,
                neutral_news=neutral_count,
                sentiment_score=avg_sentiment,
                keyword_frequency=dict(keyword_freq),
                recent_news=recent_titles,
                recent_news_links=recent_links,
                investment_score=investment_score,
                risk_level=risk_level,
                recommendation=recommendation
            )
        
        return stock_analysis
    
    def _calculate_investment_score(self, total_news: int, positive: int, 
                                  negative: int, sentiment: float) -> float:
        """투자 점수 계산"""
        if total_news == 0:
            return 0.0
        
        # 뉴스 양 점수 (0-30점)
        volume_score = min(30, total_news * 2)
        
        # 긍정/부정 비율 점수 (0-40점)
        if total_news > 0:
            positive_ratio = positive / total_news
            negative_ratio = negative / total_news
            ratio_score = (positive_ratio - negative_ratio) * 40
        else:
            ratio_score = 0
        
        # 감정 점수 (0-30점)
        sentiment_score = (sentiment + 1) * 15  # -1~1을 0~30으로 변환
        
        total_score = volume_score + ratio_score + sentiment_score
        
        return max(0, min(100, total_score))  # 0-100 범위로 제한
    
    def _assess_risk_level(self, news_list: List) -> str:
        """위험도 평가"""
        risk_count = 0
        total_news = len(news_list)
        
        for news in news_list:
            text = news.title + " " + news.description
            text_lower = text.lower()
            
            for risk_keyword in self.risk_keywords:
                if risk_keyword in text_lower:
                    risk_count += 1
                    break
        
        risk_ratio = risk_count / total_news if total_news > 0 else 0
        
        if risk_ratio > 0.3:
            return "high"
        elif risk_ratio > 0.1:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, investment_score: float, risk_level: str) -> str:
        """투자 추천 생성"""
        if risk_level == "high":
            if investment_score > 70:
                return "신중 매수"
            elif investment_score > 50:
                return "관망"
            else:
                return "매도 고려"
        elif risk_level == "medium":
            if investment_score > 80:
                return "매수"
            elif investment_score > 60:
                return "신중 매수"
            elif investment_score > 40:
                return "관망"
            else:
                return "매도"
        else:  # low risk
            if investment_score > 70:
                return "강력 매수"
            elif investment_score > 50:
                return "매수"
            elif investment_score > 30:
                return "관망"
            else:
                return "매도"
    
    def get_top_stocks(self, stock_analysis: Dict[str, StockAnalysis], 
                      top_n: int = 10) -> List[StockAnalysis]:
        """투자 점수가 높은 상위 종목 반환"""
        sorted_stocks = sorted(
            stock_analysis.values(),
            key=lambda x: x.investment_score,
            reverse=True
        )
        return sorted_stocks[:top_n]
    
    def get_high_risk_stocks(self, stock_analysis: Dict[str, StockAnalysis]) -> List[StockAnalysis]:
        """위험도가 높은 종목 반환"""
        return [
            stock for stock in stock_analysis.values()
            if stock.risk_level == "high"
        ]
    
    def generate_report(self, stock_analysis: Dict[str, StockAnalysis], 
                       filename: str = None) -> str:
        """분석 리포트 생성"""
        if filename is None:
            today = datetime.now().strftime("%Y%m%d")
            filename = f"stock_analysis_report_{today}.txt"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("주식 뉴스 분석 리포트")
        report_lines.append(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 상위 종목
        top_stocks = self.get_top_stocks(stock_analysis, 10)
        report_lines.append("📈 투자 점수 상위 종목")
        report_lines.append("-" * 40)
        
        for i, stock in enumerate(top_stocks, 1):
            report_lines.append(f"{i:2d}. {stock.stock_name} ({stock.stock_code})")
            report_lines.append(f"    투자점수: {stock.investment_score:.1f}/100")
            report_lines.append(f"    뉴스수: {stock.news_count}개 (긍정:{stock.positive_news}, 부정:{stock.negative_news})")
            report_lines.append(f"    감정점수: {stock.sentiment_score:.3f}")
            report_lines.append(f"    위험도: {stock.risk_level}")
            report_lines.append(f"    추천: {stock.recommendation}")
            report_lines.append("")
        
        # 위험 종목
        high_risk_stocks = self.get_high_risk_stocks(stock_analysis)
        if high_risk_stocks:
            report_lines.append("⚠️  위험도 높은 종목")
            report_lines.append("-" * 40)
            
            for stock in high_risk_stocks:
                report_lines.append(f"• {stock.stock_name} ({stock.stock_code})")
                report_lines.append(f"  투자점수: {stock.investment_score:.1f}, 추천: {stock.recommendation}")
            report_lines.append("")
        
        # 종목별 상세 분석
        report_lines.append("📊 종목별 상세 분석")
        report_lines.append("=" * 60)
        
        for stock_code, analysis in stock_analysis.items():
            report_lines.append(f"\n{analysis.stock_name} ({stock_code})")
            report_lines.append(f"뉴스 수: {analysis.news_count}개")
            report_lines.append(f"긍정/부정/중립: {analysis.positive_news}/{analysis.negative_news}/{analysis.neutral_news}")
            report_lines.append(f"감정 점수: {analysis.sentiment_score:.3f}")
            report_lines.append(f"투자 점수: {analysis.investment_score:.1f}/100")
            report_lines.append(f"위험도: {analysis.risk_level}")
            report_lines.append(f"추천: {analysis.recommendation}")
            
            if analysis.keyword_frequency:
                top_keywords = sorted(analysis.keyword_frequency.items(), 
                                    key=lambda x: x[1], reverse=True)[:5]
                report_lines.append(f"주요 키워드: {', '.join([f'{k}({v})' for k, v in top_keywords])}")
            
            if analysis.recent_news:
                report_lines.append("최근 뉴스:")
                for title in analysis.recent_news[:3]:
                    report_lines.append(f"  • {title}")
        
        report_content = "\n".join(report_lines)
        
        # 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"분석 리포트를 {filename}에 저장 완료")
        return report_content
    
    def save_analysis_to_csv(self, stock_analysis: Dict[str, StockAnalysis], 
                           filename: str = None):
        """분석 결과를 CSV 파일로 저장"""
        if filename is None:
            today = datetime.now().strftime("%Y%m%d")
            filename = f"stock_analysis_{today}.csv"
        
        data = []
        for analysis in stock_analysis.values():
            # 뉴스 제목과 링크를 문자열로 변환 (최대 3개)
            recent_links_str = " | ".join(analysis.recent_news_links[:3]) if analysis.recent_news_links else ""
            
            data.append({
                "stock_code": analysis.stock_code,
                "stock_name": analysis.stock_name,
                "news_count": analysis.news_count,
                "positive_news": analysis.positive_news,
                "negative_news": analysis.negative_news,
                "neutral_news": analysis.neutral_news,
                "sentiment_score": analysis.sentiment_score,
                "investment_score": analysis.investment_score,
                "risk_level": analysis.risk_level,
                "recommendation": analysis.recommendation,
                "top_keywords": ", ".join([k for k, v in sorted(analysis.keyword_frequency.items(), 
                                                              key=lambda x: x[1], reverse=True)[:5]]),
                "recent_news_links": recent_links_str
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"분석 결과를 {filename}에 저장 완료")

def main():
    """메인 함수 - 테스트용"""
    from news_collector import NaverNewsCollector, NewsItem
    
    # 테스트용 뉴스 데이터 생성
    test_news = [
        NewsItem(
            title="삼성전자 실적 개선으로 주가 상승",
            description="삼성전자가 좋은 실적을 보여주고 있어 주가가 상승하고 있습니다.",
            link="http://example.com/1",
            pub_date="2024-01-01",
            source="test",
            keywords=["삼성전자", "실적", "상승"],
            related_stocks=["005930"]
        ),
        NewsItem(
            title="SK하이닉스 신기술 개발 성공",
            description="SK하이닉스가 새로운 반도체 기술을 개발했습니다.",
            link="http://example.com/2",
            pub_date="2024-01-01",
            source="test",
            keywords=["SK하이닉스", "신기술", "반도체"],
            related_stocks=["000660"]
        )
    ]
    
    # 분석기 초기화
    analyzer = StockNewsAnalyzer()
    
    # 뉴스 분석
    stock_analysis = analyzer.analyze_stock_news(test_news)
    
    # 결과 출력
    print("📊 뉴스 분석 결과")
    print("=" * 50)
    
    for stock_code, analysis in stock_analysis.items():
        print(f"\n{analysis.stock_name} ({stock_code})")
        print(f"투자 점수: {analysis.investment_score:.1f}/100")
        print(f"뉴스 수: {analysis.news_count}개")
        print(f"감정 점수: {analysis.sentiment_score:.3f}")
        print(f"위험도: {analysis.risk_level}")
        print(f"추천: {analysis.recommendation}")
    
    # 리포트 생성
    report = analyzer.generate_report(stock_analysis)
    print(f"\n📄 리포트 생성 완료")
    
    # CSV 저장
    analyzer.save_analysis_to_csv(stock_analysis)
    print("📊 CSV 저장 완료")

if __name__ == "__main__":
    main() 