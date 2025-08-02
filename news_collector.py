#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 수집기
네이버 뉴스 API를 이용해서 뉴스를 수집하고 종목과 매칭하는 시스템
"""

import requests
import time
import json
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict
import re
from loguru import logger
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# NLTK 데이터 다운로드
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

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

class AIMatchingEngine:
    """AI 기반 종목 매칭 엔진"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.9
        )
        self.stock_vectors = None
        self.stock_names = []
        self.stock_codes = []
        self._initialize_stopwords()
    
    def _initialize_stopwords(self):
        """한국어 불용어 초기화"""
        self.korean_stopwords = set([
            '이', '그', '저', '것', '수', '등', '및', '또는', '그리고', '하지만', '그러나',
            '때', '곳', '사람', '일', '년', '월', '일', '시', '분', '초', '주', '개',
            '회', '번', '차', '대', '명', '개', '마리', '권', '장', '벌', '채', '줄',
            '그루', '송이', '포기', '마디', '상자', '사발', '잔', '컵', '통', '캔',
            '병', '박스', '봉지', '묶음', '세트', '켤레', '쌍', '벌', '자루', '개비',
            '알', '톨', '톨레', '톨트', '톨트', '톨트', '톨트', '톨트', '톨트', '톨트'
        ])
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 특수문자 제거
        text = re.sub(r'[^\w\s]', ' ', text)
        # 숫자 제거
        text = re.sub(r'\d+', '', text)
        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize_korean(self, text: str) -> List[str]:
        """한국어 토큰화"""
        # jieba로 한국어 토큰화
        tokens = jieba.lcut(text)
        # 불용어 제거
        tokens = [token for token in tokens if token not in self.korean_stopwords and len(token) > 1]
        return tokens
    
    def build_stock_corpus(self, stock_keywords: Dict[str, List[str]]):
        """종목별 코퍼스 구축"""
        self.stock_names = []
        self.stock_codes = []
        corpus = []
        
        for stock_code, keywords in stock_keywords.items():
            # 종목명과 키워드를 결합하여 문서 생성
            stock_name = keywords[0] if keywords else ""
            combined_text = f"{stock_name} {' '.join(keywords)}"
            
            # 전처리 및 토큰화
            processed_text = self.preprocess_text(combined_text)
            tokens = self.tokenize_korean(processed_text)
            document = ' '.join(tokens)
            
            corpus.append(document)
            self.stock_names.append(stock_name)
            self.stock_codes.append(stock_code)
        
        # TF-IDF 벡터화
        self.stock_vectors = self.vectorizer.fit_transform(corpus)
        logger.info(f"종목 코퍼스 구축 완료: {len(self.stock_codes)}개 종목")
    
    def calculate_similarity(self, news_text: str) -> List[tuple]:
        """뉴스 텍스트와 종목 간 유사도 계산"""
        if self.stock_vectors is None:
            return []
        
        # 뉴스 텍스트 전처리
        processed_text = self.preprocess_text(news_text)
        tokens = self.tokenize_korean(processed_text)
        news_document = ' '.join(tokens)
        
        # 뉴스 텍스트 벡터화
        news_vector = self.vectorizer.transform([news_document])
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(news_vector, self.stock_vectors).flatten()
        
        # 종목 코드와 유사도 점수를 튜플로 반환
        results = [(self.stock_codes[i], similarities[i], self.stock_names[i]) 
                  for i in range(len(similarities))]
        
        # 유사도 순으로 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_related_stocks_ai(self, news_text: str, threshold: float = 0.1) -> List[str]:
        """AI 기반 관련 종목 찾기"""
        similarities = self.calculate_similarity(news_text)
        
        # 임계값 이상의 종목만 선택
        related_stocks = []
        for stock_code, similarity, stock_name in similarities:
            if similarity >= threshold:
                related_stocks.append(stock_code)
                logger.debug(f"AI 매칭: {stock_name}({stock_code}) - 유사도: {similarity:.3f}")
        
        # 상위 3개 종목만 반환
        return related_stocks[:3]


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
        
        # AI 매칭 엔진 초기화
        self.ai_engine = AIMatchingEngine()
        self.ai_engine.build_stock_corpus(self.stock_keywords)
        
        logger.info("네이버 뉴스 수집기 초기화 완료")
    
    def _load_stock_keywords(self) -> Dict[str, List[str]]:
        """종목명과 키워드 매칭 데이터 로드 - 중복 제거 및 최적화"""
        # 주요 종목들의 키워드 매핑 (중복 제거 및 최적화)
        stock_keywords = {
            # 반도체/IT
            "005930": ["삼성전자", "갤럭시", "메모리", "반도체", "삼성전자주식"],
            "000660": ["SK하이닉스", "하이닉스", "메모리", "반도체", "SK하이닉스주식"],
            "035420": ["NAVER", "네이버", "검색", "포털", "네이버주식"],
            
            # 배터리/전기차
            "051910": ["LG화학", "LG화학주식", "배터리", "전기차배터리"],
            "006400": ["삼성SDI", "SDI", "배터리", "삼성SDI주식"],
            "373220": ["LG에너지솔루션", "에너지솔루션", "배터리", "LG에너지솔루션주식"],
            
            # IT/플랫폼
            "035720": ["카카오", "카카오톡", "메신저", "플랫폼", "카카오주식"],
            "323410": ["카카오뱅크", "카카오뱅크주식", "뱅크", "은행"],
            
            # 바이오/제약
            "207940": ["삼성바이오로직스", "바이오로직스", "바이오", "제약", "삼성바이오로직스주식"],
            "068270": ["셀트리온", "셀트리온주식", "바이오", "제약"],
            
            # 생활용품
            "051900": ["LG생활건강", "생활건강", "화장품", "LG생활건강주식"],
            
            # 통신
            "017670": ["SK텔레콤", "SK텔레콤주식", "텔레콤", "통신"],
            "030200": ["KT", "KT주식", "통신", "텔레콤"],
            "032640": ["LG유플러스", "유플러스", "통신", "LG유플러스주식"],
            
            # 자동차
            "005380": ["현대자동차", "현대", "자동차", "차량", "현대자동차주식"],
            "000270": ["기아", "기아자동차", "자동차", "차량", "기아주식"],
            
            # 철강/전력
            "005490": ["POSCO", "포스코", "철강", "제철", "포스코주식"],
            "015760": ["한국전력", "한전", "전력", "전기", "한국전력주식"],
            
            # 게임/엔터테인먼트
            "035250": ["강원랜드", "강원랜드주식", "카지노", "게임"],
            
            # 렌터카/광고
            "068400": ["AJ렌터카", "AJ렌터카주식", "렌터카", "차량"],
            "035000": ["HS애드", "HS애드주식", "애드", "광고", "마케팅"]
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
        """텍스트에서 관련 종목 코드 찾기 - AI 기반 하이브리드 매칭"""
        # 1. AI 기반 매칭 (의미적 유사도)
        ai_matches = self.ai_engine.find_related_stocks_ai(text, threshold=0.15)
        
        # 2. 기존 키워드 기반 매칭 (백업)
        keyword_matches = self._find_related_stocks_keyword(text)
        
        # 3. 하이브리드 결과 결합
        combined_matches = {}
        
        # AI 매칭 결과에 높은 가중치 부여
        for stock_code in ai_matches:
            combined_matches[stock_code] = combined_matches.get(stock_code, 0) + 10
        
        # 키워드 매칭 결과에 기본 가중치 부여
        for stock_code in keyword_matches:
            combined_matches[stock_code] = combined_matches.get(stock_code, 0) + 5
        
        # 점수 순으로 정렬
        sorted_matches = sorted(combined_matches.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 3개 종목 반환
        result = [stock_code for stock_code, score in sorted_matches[:3]]
        
        # 디버그 로깅
        if result:
            logger.debug(f"하이브리드 매칭 결과: {result}")
            for stock_code in result:
                stock_name = next((keywords[0] for code, keywords in self.stock_keywords.items() 
                                 if code == stock_code), "Unknown")
                logger.debug(f"  - {stock_name}({stock_code})")
        
        return result
    
    def _find_related_stocks_keyword(self, text: str) -> List[str]:
        """기존 키워드 기반 매칭 (백업용)"""
        text_lower = text.lower()
        stock_scores = {}
        
        for stock_code, keywords in self.stock_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text_lower:
                    # 키워드 우선순위에 따른 가중치 부여
                    if keyword_lower in [stock_code.lower() for stock_code in ["삼성전자", "SK하이닉스", "NAVER", "카카오"]]:
                        score += 10  # 주요 종목명은 높은 가중치
                    elif "주식" in keyword_lower:
                        score += 8   # "주식" 키워드는 높은 가중치
                    elif len(keyword) >= 4:
                        score += 5   # 긴 키워드는 중간 가중치
                    else:
                        score += 2   # 짧은 키워드는 낮은 가중치
                    
                    matched_keywords.append(keyword)
            
            # 최소 점수 이상일 때만 관련 종목으로 인정
            if score >= 3:
                stock_scores[stock_code] = {
                    'score': score,
                    'keywords': matched_keywords
                }
        
        # 점수 순으로 정렬하여 상위 종목들 반환
        sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # 상위 3개 종목만 반환 (중복 매칭 방지)
        result = []
        for stock_code, info in sorted_stocks[:3]:
            result.append(stock_code)
        
        return result
    
    def collect_daily_news(self, keywords: List[str] = None) -> List[NewsItem]:
        """
        당일 주요 뉴스 수집 - 키워드 최적화
        
        Args:
            keywords: 검색할 키워드 리스트 (None이면 최적화된 기본 키워드 사용)
            
        Returns:
            수집된 뉴스 아이템 리스트
        """
        if keywords is None:
            # 최적화된 키워드 리스트 - 관련성과 정확도 향상
            keywords = [
                # 시장 전체
                "주식시장", "증시동향", "코스피", "코스닥", "투자동향",
                
                # 주요 종목별 (정확한 매칭을 위해)
                "삼성전자 주식", "SK하이닉스 주식", "네이버 주식", "카카오 주식",
                "LG화학 주식", "현대자동차 주식", "기아 주식", "포스코 주식",
                "셀트리온 주식", "카카오뱅크 주식",
                
                # 섹터별 키워드
                "반도체 시장", "배터리 시장", "전기차 시장", "바이오 시장",
                "통신 시장", "자동차 시장", "철강 시장", "전력 시장"
            ]
        
        all_news = []
        
        for keyword in keywords:
            logger.info(f"키워드 '{keyword}' 뉴스 수집 중...")
            news_items = self.search_news(keyword, display=30, sort="date")  # 각 키워드당 30개로 조정
            all_news.extend(news_items)
            
            # API 호출 제한 방지
            time.sleep(0.2)  # 간격 증가
        
        # 중복 제거 (제목 기준) 및 품질 필터링
        unique_news = {}
        for news in all_news:
            if news.title not in unique_news:
                # 제목 길이가 너무 짧거나 긴 뉴스 제외
                if 10 <= len(news.title) <= 200:
                    unique_news[news.title] = news
        
        result = list(unique_news.values())
        logger.info(f"총 {len(result)}개의 고유 뉴스 수집 완료 (품질 필터링 적용)")
        
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