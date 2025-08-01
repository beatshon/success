#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 수집기
네이버 뉴스 API를 이용해서 뉴스를 수집하고 종목과 매칭하는 시스템
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from dataclasses import dataclass
from loguru import logger
import pandas as pd

@dataclass
class NewsItem:
    """뉴스 아이템 데이터 클래스"""
    title: str
    description: str
    link: str
    pub_date: str
    source: str
    keywords: List[str]
    sentiment: float = 0.0  # 감정 점수 (-1.0 ~ 1.0)
    related_stocks: List[str] = None  # 관련 종목 코드 리스트

class NaverNewsCollector:
    """네이버 뉴스 수집기"""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        네이버 뉴스 수집기 초기화
        
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 시크릿
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        
        # 종목명 매칭을 위한 데이터
        self.stock_keywords = self._load_stock_keywords()
        
        logger.info("네이버 뉴스 수집기 초기화 완료")
    
    def _load_stock_keywords(self) -> Dict[str, List[str]]:
        """종목명과 키워드 매칭 데이터 로드"""
        # 주요 종목들의 키워드 매핑
        stock_keywords = {
            "005930": ["삼성전자", "삼성", "갤럭시", "메모리", "반도체"],
            "000660": ["SK하이닉스", "SK", "하이닉스", "메모리", "반도체"],
            "035420": ["NAVER", "네이버", "검색", "포털"],
            "051910": ["LG화학", "LG", "화학", "배터리", "전기차"],
            "006400": ["삼성SDI", "삼성", "SDI", "배터리", "전기차"],
            "035720": ["카카오", "카카오톡", "메신저", "플랫폼"],
            "207940": ["삼성바이오로직스", "삼성", "바이오", "제약"],
            "068270": ["셀트리온", "셀트리온", "바이오", "제약"],
            "323410": ["카카오뱅크", "카카오", "뱅크", "은행"],
            "035720": ["카카오", "카카오톡", "메신저", "플랫폼"],
            "051900": ["LG생활건강", "LG", "생활건강", "화장품"],
            "017670": ["SK텔레콤", "SK", "텔레콤", "통신"],
            "030200": ["KT", "KT", "통신", "텔레콤"],
            "032640": ["LG유플러스", "LG", "유플러스", "통신"],
            "051910": ["LG화학", "LG", "화학", "배터리"],
            "006400": ["삼성SDI", "삼성", "SDI", "배터리"],
            "373220": ["LG에너지솔루션", "LG", "에너지솔루션", "배터리"],
            "005380": ["현대자동차", "현대", "자동차", "차량"],
            "000270": ["기아", "기아", "자동차", "차량"],
            "005490": ["POSCO", "포스코", "철강", "제철"],
            "015760": ["한국전력", "한전", "전력", "전기"],
            "035250": ["강원랜드", "강원랜드", "카지노", "게임"],
            "068400": ["AJ렌터카", "AJ", "렌터카", "차량"],
            "035000": ["HS애드", "HS", "애드", "광고"],
            "035420": ["NAVER", "네이버", "검색", "포털"],
            "051910": ["LG화학", "LG", "화학", "배터리"],
            "006400": ["삼성SDI", "삼성", "SDI", "배터리"],
            "035720": ["카카오", "카카오톡", "메신저", "플랫폼"],
            "207940": ["삼성바이오로직스", "삼성", "바이오", "제약"],
            "068270": ["셀트리온", "셀트리온", "바이오", "제약"],
            "323410": ["카카오뱅크", "카카오", "뱅크", "은행"],
            "035720": ["카카오", "카카오톡", "메신저", "플랫폼"],
            "051900": ["LG생활건강", "LG", "생활건강", "화장품"],
            "017670": ["SK텔레콤", "SK", "텔레콤", "통신"],
            "030200": ["KT", "KT", "통신", "텔레콤"],
            "032640": ["LG유플러스", "LG", "유플러스", "통신"],
            "051910": ["LG화학", "LG", "화학", "배터리"],
            "006400": ["삼성SDI", "삼성", "SDI", "배터리"],
            "373220": ["LG에너지솔루션", "LG", "에너지솔루션", "배터리"],
            "005380": ["현대자동차", "현대", "자동차", "차량"],
            "000270": ["기아", "기아", "자동차", "차량"],
            "005490": ["POSCO", "포스코", "철강", "제철"],
            "015760": ["한국전력", "한전", "전력", "전기"],
            "035250": ["강원랜드", "강원랜드", "카지노", "게임"],
            "068400": ["AJ렌터카", "AJ", "렌터카", "차량"],
            "035000": ["HS애드", "HS", "애드", "광고"]
        }
        
        return stock_keywords
    
    def search_news(self, query: str, display: int = 100, start: int = 1, 
                   sort: str = "date") -> List[NewsItem]:
        """
        네이버 뉴스 검색
        
        Args:
            query: 검색어
            display: 검색 결과 개수 (최대 100)
            start: 검색 시작 위치
            sort: 정렬 방식 (date, sim)
            
        Returns:
            뉴스 아이템 리스트
        """
        params = {
            "query": query,
            "display": min(display, 100),
            "start": start,
            "sort": sort
        }
        
        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            for item in data.get("items", []):
                news_item = NewsItem(
                    title=self._clean_text(item.get("title", "")),
                    description=self._clean_text(item.get("description", "")),
                    link=item.get("link", ""),
                    pub_date=item.get("pubDate", ""),
                    source=item.get("originallink", ""),
                    keywords=self._extract_keywords(item.get("title", "") + " " + item.get("description", "")),
                    related_stocks=self._find_related_stocks(item.get("title", "") + " " + item.get("description", ""))
                )
                news_items.append(news_item)
            
            logger.info(f"'{query}' 검색 결과: {len(news_items)}개 뉴스 수집")
            return news_items
            
        except requests.exceptions.RequestException as e:
            logger.error(f"네이버 뉴스 API 요청 실패: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 정리
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        text = re.sub(r'&[#\d]+;', '', text)
        return text.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 주요 키워드 패턴
        keywords = []
        
        # 종목명 패턴
        stock_patterns = [
            r'삼성전자|삼성|갤럭시',
            r'SK하이닉스|SK|하이닉스',
            r'네이버|NAVER',
            r'카카오|카카오톡',
            r'LG화학|LG|화학',
            r'현대자동차|현대|자동차',
            r'기아|기아자동차',
            r'포스코|POSCO',
            r'한전|한국전력',
            r'셀트리온|바이오',
            r'카카오뱅크|뱅크',
            r'배터리|전기차',
            r'반도체|메모리',
            r'통신|텔레콤',
            r'제약|바이오',
            r'철강|제철',
            r'전력|전기',
            r'카지노|게임',
            r'렌터카|차량',
            r'광고|마케팅'
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        # 중복 제거 및 정리
        keywords = list(set(keywords))
        return keywords
    
    def _find_related_stocks(self, text: str) -> List[str]:
        """텍스트에서 관련 종목 코드 찾기"""
        related_stocks = []
        
        for stock_code, keywords in self.stock_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    related_stocks.append(stock_code)
                    break
        
        return list(set(related_stocks))
    
    def collect_daily_news(self, keywords: List[str] = None) -> List[NewsItem]:
        """
        당일 주요 뉴스 수집
        
        Args:
            keywords: 검색할 키워드 리스트 (None이면 기본 키워드 사용)
            
        Returns:
            수집된 뉴스 아이템 리스트
        """
        if keywords is None:
            keywords = [
                "주식", "증시", "코스피", "코스닥", "투자",
                "삼성전자", "SK하이닉스", "네이버", "카카오",
                "LG화학", "현대자동차", "기아", "포스코",
                "셀트리온", "카카오뱅크", "배터리", "반도체"
            ]
        
        all_news = []
        
        for keyword in keywords:
            logger.info(f"키워드 '{keyword}' 뉴스 수집 중...")
            news_items = self.search_news(keyword, display=50, sort="date")
            all_news.extend(news_items)
            
            # API 호출 제한 방지
            time.sleep(0.1)
        
        # 중복 제거 (제목 기준)
        unique_news = {}
        for news in all_news:
            if news.title not in unique_news:
                unique_news[news.title] = news
        
        result = list(unique_news.values())
        logger.info(f"총 {len(result)}개의 고유 뉴스 수집 완료")
        
        return result
    
    def save_news_to_csv(self, news_items: List[NewsItem], filename: str = None):
        """뉴스를 CSV 파일로 저장"""
        if filename is None:
            today = datetime.now().strftime("%Y%m%d")
            filename = f"news_{today}.csv"
        
        data = []
        for news in news_items:
            data.append({
                "title": news.title,
                "description": news.description,
                "link": news.link,
                "pub_date": news.pub_date,
                "source": news.source,
                "keywords": ", ".join(news.keywords),
                "related_stocks": ", ".join(news.related_stocks),
                "sentiment": news.sentiment
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"뉴스 데이터를 {filename}에 저장 완료")
    
    def get_stock_news_summary(self, news_items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
        """종목별 뉴스 요약"""
        stock_news = {}
        
        for news in news_items:
            for stock_code in news.related_stocks:
                if stock_code not in stock_news:
                    stock_news[stock_code] = []
                stock_news[stock_code].append(news)
        
        return stock_news

def main():
    """메인 함수 - 테스트용"""
    # 네이버 API 키 설정 (실제 키로 변경 필요)
    client_id = "your_naver_client_id"
    client_secret = "your_naver_client_secret"
    
    # 뉴스 수집기 초기화
    collector = NaverNewsCollector(client_id, client_secret)
    
    # 당일 뉴스 수집
    news_items = collector.collect_daily_news()
    
    # 결과 출력
    print(f"수집된 뉴스 개수: {len(news_items)}")
    
    for i, news in enumerate(news_items[:5], 1):
        print(f"\n{i}. {news.title}")
        print(f"   관련 종목: {', '.join(news.related_stocks)}")
        print(f"   키워드: {', '.join(news.keywords)}")
    
    # CSV 저장
    collector.save_news_to_csv(news_items)
    
    # 종목별 뉴스 요약
    stock_news = collector.get_stock_news_summary(news_items)
    print(f"\n종목별 뉴스 개수:")
    for stock_code, news_list in stock_news.items():
        print(f"  {stock_code}: {len(news_list)}개")

if __name__ == "__main__":
    main() 