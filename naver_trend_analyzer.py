#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 트렌드 분석기
검색 패턴과 쇼핑 패턴을 주식 투자에 반영하는 시스템
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import os

# 프로젝트 모듈 import
from error_handler import ErrorType, ErrorLevel, handle_error

class TrendType(Enum):
    """트렌드 타입"""
    SEARCH = "search"
    SHOPPING = "shopping"
    NEWS = "news"
    BLOG = "blog"
    REAL_TIME = "real_time"

@dataclass
class TrendData:
    """트렌드 데이터"""
    keyword: str
    trend_type: TrendType
    value: float
    timestamp: datetime
    related_stocks: List[str] = None
    sentiment_score: float = 0.0
    volume_change: float = 0.0
    momentum_score: float = 0.0
    volatility: float = 0.0

@dataclass
class StockTrendCorrelation:
    """주식-트렌드 상관관계"""
    stock_code: str
    stock_name: str
    keyword: str
    correlation_score: float
    trend_direction: str  # "positive", "negative", "neutral"
    confidence_level: float
    last_updated: datetime
    impact_score: float = 0.0
    prediction_accuracy: float = 0.0

class NaverTrendAnalyzer:
    """네이버 트렌드 분석기"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1"
        
        # 헤더 설정
        self.headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret,
            'Content-Type': 'application/json'
        }
        
        # 키워드-주식 매핑 확장
        self.keyword_stock_mapping = self._load_keyword_mapping()
        
        # 트렌드 데이터 저장소
        self.trend_data = {}
        self.correlation_data = {}
        self.historical_data = {}
        
        # 분석 설정
        self.analysis_interval = 1800  # 30분마다 분석
        self.correlation_threshold = 0.25  # 상관관계 임계값
        self.momentum_window = 24  # 24시간 모멘텀 계산
        
        # 실행 상태
        self.running = False
        self.analysis_thread = None
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 실시간 모니터링 키워드
        self.monitoring_keywords = [
            "삼성전자", "SK하이닉스", "네이버", "카카오", "현대차", "기아",
            "LG화학", "삼성SDI", "테슬라", "전기차", "배터리", "AI", "반도체",
            "부동산", "금리", "인플레이션", "달러", "원화", "코로나", "백신"
        ]
        
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            self.db_path = "data/naver_trends.db"
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 트렌드 데이터 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trend_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    trend_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    sentiment_score REAL DEFAULT 0.0,
                    volume_change REAL DEFAULT 0.0,
                    momentum_score REAL DEFAULT 0.0,
                    volatility REAL DEFAULT 0.0
                )
            ''')
            
            # 상관관계 데이터 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS correlation_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    correlation_score REAL NOT NULL,
                    trend_direction TEXT NOT NULL,
                    confidence_level REAL NOT NULL,
                    impact_score REAL DEFAULT 0.0,
                    prediction_accuracy REAL DEFAULT 0.0,
                    last_updated DATETIME NOT NULL
                )
            ''')
            
            # 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trend_keyword_time ON trend_data(keyword, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_corr_stock_keyword ON correlation_data(stock_code, keyword)')
            
            conn.commit()
            conn.close()
            logger.info("네이버 트렌드 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            handle_error(ErrorType.DATABASE_ERROR, ErrorLevel.ERROR, f"데이터베이스 초기화 실패: {e}")
        
    def _load_keyword_mapping(self) -> Dict[str, List[str]]:
        """키워드-주식 매핑 로드 (확장 버전)"""
        return {
            # 기술 관련
            "삼성전자": ["005930"],
            "SK하이닉스": ["000660"],
            "네이버": ["035420"],
            "카카오": ["035720"],
            "LG화학": ["051910"],
            "삼성SDI": ["006400"],
            "LG전자": ["066570"],
            "현대모비스": ["012330"],
            "POSCO홀딩스": ["005490"],
            "삼성바이오로직스": ["207940"],
            "셀트리온": ["068270"],
            "아모레퍼시픽": ["090430"],
            "LG생활건강": ["051900"],
            "신세계": ["004170"],
            "롯데쇼핑": ["023530"],
            
            # 자동차 관련
            "현대차": ["005380"],
            "기아": ["000270"],
            "테슬라": ["TSLA"],
            "전기차": ["005380", "000270", "051910", "006400"],
            "배터리": ["051910", "006400", "373220"],
            "자율주행": ["005380", "000270", "012330"],
            "수소차": ["005380", "000270", "051910"],
            
            # 쇼핑 관련
            "쿠팡": ["CPNG"],
            "배달": ["035420", "035720"],
            "온라인쇼핑": ["004170", "023530"],
            "이커머스": ["035420", "035720", "004170"],
            
            # 금융 관련
            "KB금융": ["105560"],
            "신한지주": ["055550"],
            "하나금융지주": ["086790"],
            "우리금융지주": ["316140"],
            "금리": ["105560", "055550", "086790", "316140"],
            "부동산": ["004170", "023530"],
            
            # 에너지 관련
            "SK이노베이션": ["096770"],
            "GS": ["078930"],
            "S-OIL": ["010950"],
            "에너지": ["096770", "078930", "010950"],
            
            # 바이오/제약
            "삼성바이오로직스": ["207940"],
            "셀트리온": ["068270"],
            "한미약품": ["128940"],
            "유한양행": ["000100"],
            "바이오": ["207940", "068270", "128940", "000100"],
            
            # 게임/엔터테인먼트
            "넥슨": ["225570"],
            "넷마블": ["251270"],
            "NC소프트": ["036570"],
            "게임": ["225570", "251270", "036570"],
            
            # 통신
            "SK텔레콤": ["017670"],
            "KT": ["030200"],
            "LG유플러스": ["032640"],
            "5G": ["017670", "030200", "032640"],
            
            # 건설
            "현대건설": ["000720"],
            "GS건설": ["006360"],
            "포스코건설": ["047050"],
            "건설": ["000720", "006360", "047050"],
            
            # 화학
            "LG화학": ["051910"],
            "롯데케미칼": ["011170"],
            "한화솔루션": ["009830"],
            "화학": ["051910", "011170", "009830"],
            
            # 철강
            "POSCO": ["005490"],
            "현대제철": ["004020"],
            "철강": ["005490", "004020"],
            
            # 해운
            "현대상선": ["011200"],
            "한진해운": ["003160"],
            "해운": ["011200", "003160"],
            
            # 항공
            "대한항공": ["003490"],
            "아시아나항공": ["020560"],
            "항공": ["003490", "020560"],
            
            # 마케팅 키워드
            "AI": ["005930", "000660", "035420", "035720"],
            "반도체": ["005930", "000660"],
            "메모리": ["005930", "000660"],
            "디스플레이": ["005930", "066570"],
            "스마트폰": ["005930", "066570"],
            "클라우드": ["035420", "035720"],
            "빅데이터": ["035420", "035720"],
            "블록체인": ["035420", "035720"],
            "가상현실": ["035420", "035720"],
            "증강현실": ["035420", "035720"],
            "사물인터넷": ["005930", "066570"],
            "자율주행": ["005380", "000270"],
            "전기차": ["005380", "000270", "051910", "006400"],
            "수소차": ["005380", "000270"],
            "친환경": ["051910", "006400"],
            "신재생에너지": ["051910", "006400"],
            "태양광": ["051910", "006400"],
            "풍력": ["051910", "006400"],
            "배터리": ["051910", "006400"],
            "충전소": ["005380", "000270"],
            "모빌리티": ["005380", "000270"],
            "공유경제": ["035420", "035720"],
            "핀테크": ["035420", "035720"],
            "암호화폐": ["035420", "035720"],
            "NFT": ["035420", "035720"],
            "메타버스": ["035420", "035720"],
            "웹3": ["035420", "035720"],
            "디지털화": ["035420", "035720"],
            "디지털전환": ["035420", "035720"],
            "ESG": ["005930", "000660", "051910"],
            "탄소중립": ["051910", "006400"],
            "지속가능": ["005930", "000660", "051910"],
            "인플레이션": ["105560", "055550", "086790"],
            "금리": ["105560", "055550", "086790"],
            "원화": ["005930", "000660"],
            "달러": ["005930", "000660"],
            "환율": ["005930", "000660"],
            "부동산": ["004170", "023530"],
            "아파트": ["004170", "023530"],
            "재건축": ["004170", "023530"],
            "재개발": ["004170", "023530"],
            "코로나": ["207940", "068270"],
            "백신": ["207940", "068270"],
            "팬데믹": ["207940", "068270"],
            "마스크": ["090430", "051900"],
            "방역": ["090430", "051900"],
            "원격근무": ["035420", "035720"],
            "비대면": ["035420", "035720"],
            "온라인교육": ["035420", "035720"],
            "배달음식": ["035420", "035720"],
            "홈쇼핑": ["004170", "023530"],
            "온라인쇼핑": ["004170", "023530"],
            "이커머스": ["004170", "023530"],
            "모바일결제": ["035420", "035720"],
            "간편결제": ["035420", "035720"],
            "QR코드": ["035420", "035720"],
            "스마트폰": ["005930", "066570"],
            "태블릿": ["005930", "066570"],
            "노트북": ["005930", "066570"],
            "게이밍": ["225570", "251270", "036570"],
            "스트리밍": ["035420", "035720"],
            "OTT": ["035420", "035720"],
            "넷플릭스": ["035420", "035720"],
            "유튜브": ["035420", "035720"],
            "소셜미디어": ["035420", "035720"],
            "인플루언서": ["035420", "035720"],
            "라이브커머스": ["004170", "023530"],
            "중고거래": ["035420", "035720"],
            "공동구매": ["035420", "035720"],
            "구독서비스": ["035420", "035720"],
            "클라우드게임": ["225570", "251270", "036570"],
            "VR게임": ["225570", "251270", "036570"],
            "모바일게임": ["225570", "251270", "036570"],
            "PC게임": ["225570", "251270", "036570"],
            "콘솔게임": ["225570", "251270", "036570"],
            "e스포츠": ["225570", "251270", "036570"],
            "스포츠": ["225570", "251270", "036570"],
            "K리그": ["225570", "251270", "036570"],
            "야구": ["225570", "251270", "036570"],
            "축구": ["225570", "251270", "036570"],
            "농구": ["225570", "251270", "036570"],
            "골프": ["225570", "251270", "036570"],
            "테니스": ["225570", "251270", "036570"],
            "스키": ["225570", "251270", "036570"],
            "스노보드": ["225570", "251270", "036570"],
            "등산": ["225570", "251270", "036570"],
            "캠핑": ["225570", "251270", "036570"],
            "여행": ["225570", "251270", "036570"],
            "해외여행": ["225570", "251270", "036570"],
            "국내여행": ["225570", "251270", "036570"],
            "크루즈": ["225570", "251270", "036570"],
            "항공권": ["003490", "020560"],
            "호텔": ["004170", "023530"],
            "리조트": ["004170", "023530"],
            "펜션": ["004170", "023530"],
            "게스트하우스": ["004170", "023530"],
            "민박": ["004170", "023530"],
            "에어비앤비": ["004170", "023530"],
            "공유숙박": ["004170", "023530"],
            "공유주방": ["004170", "023530"],
            "공유오피스": ["004170", "023530"],
            "공유주차": ["004170", "023530"],
            "공유자전거": ["004170", "023530"],
            "공유킥보드": ["004170", "023530"],
            "공유전동킥보드": ["004170", "023530"],
            "공유전동휠": ["004170", "023530"],
            "공유전동보드": ["004170", "023530"],
            "공유전동스쿠터": ["004170", "023530"],
            "공유전동자전거": ["004170", "023530"],
            "공유전동삼륜차": ["004170", "023530"],
            "공유전동사륜차": ["004170", "023530"],
            "공유전동오륜차": ["004170", "023530"],
            "공유전동육륜차": ["004170", "023530"],
            "공유전동칠륜차": ["004170", "023530"],
            "공유전동팔륜차": ["004170", "023530"],
            "공유전동구륜차": ["004170", "023530"],
            "공유전동십륜차": ["004170", "023530"]
        }
    
    def get_search_trend(self, keyword: str, period: str = "1month") -> Dict:
        """검색 트렌드 조회"""
        try:
            url = f"{self.base_url}/datalab/search"
            
            # 요청 데이터
            data = {
                "startDate": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "endDate": datetime.now().strftime("%Y-%m-%d"),
                "timeUnit": "date",
                "keywordGroups": [
                    {
                        "groupName": keyword,
                        "keywords": [keyword]
                    }
                ]
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            logger.error(f"검색 트렌드 조회 실패: {keyword} - {e}")
            return None
    
    def get_shopping_trend(self, keyword: str) -> Dict:
        """쇼핑 트렌드 조회"""
        try:
            url = f"{self.base_url}/datalab/shopping/categories"
            
            # 요청 데이터
            data = {
                "startDate": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "endDate": datetime.now().strftime("%Y-%m-%d"),
                "timeUnit": "date",
                "category": keyword,
                "device": "pc",
                "gender": "",
                "ages": []
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            logger.error(f"쇼핑 트렌드 조회 실패: {keyword} - {e}")
            return None
    
    def get_news_sentiment(self, keyword: str) -> float:
        """뉴스 감정 분석"""
        try:
            url = f"{self.base_url}/search/news.json"
            
            params = {
                'query': keyword,
                'display': 10,
                'start': 1,
                'sort': 'date'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # 간단한 감정 분석 (키워드 기반)
            positive_words = ['상승', '급등', '호재', '성장', '돌파', '신기록', '수익', '이익']
            negative_words = ['하락', '급락', '악재', '손실', '폭락', '위험', '부실', '실패']
            
            sentiment_score = 0.0
            total_articles = len(result.get('items', []))
            
            for item in result.get('items', []):
                title = item.get('title', '')
                description = item.get('description', '')
                content = f"{title} {description}"
                
                # 긍정/부정 키워드 카운트
                positive_count = sum(1 for word in positive_words if word in content)
                negative_count = sum(1 for word in negative_words if word in content)
                
                if positive_count > negative_count:
                    sentiment_score += 1
                elif negative_count > positive_count:
                    sentiment_score -= 1
            
            # 정규화 (-1 ~ 1)
            if total_articles > 0:
                sentiment_score = sentiment_score / total_articles
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"뉴스 감정 분석 실패: {keyword} - {e}")
            return 0.0
    
    def analyze_trend_correlation(self, keyword: str, stock_data: Dict) -> StockTrendCorrelation:
        """트렌드-주식 상관관계 분석"""
        try:
            # 검색 트렌드 데이터
            search_trend = self.get_search_trend(keyword)
            if not search_trend:
                return None
            
            # 트렌드 데이터 추출
            trend_values = []
            dates = []
            
            for item in search_trend.get('results', [{}])[0].get('data', []):
                trend_values.append(item.get('ratio', 0))
                dates.append(item.get('period', ''))
            
            # 주식 데이터와 상관관계 계산
            stock_prices = []
            for date in dates:
                if date in stock_data:
                    stock_prices.append(stock_data[date])
                else:
                    stock_prices.append(0)
            
            if len(trend_values) < 2 or len(stock_prices) < 2:
                return None
            
            # 상관계수 계산
            correlation = np.corrcoef(trend_values, stock_prices)[0, 1]
            
            if np.isnan(correlation):
                correlation = 0.0
            
            # 트렌드 방향 결정
            if correlation > self.correlation_threshold:
                trend_direction = "positive"
            elif correlation < -self.correlation_threshold:
                trend_direction = "negative"
            else:
                trend_direction = "neutral"
            
            # 신뢰도 계산
            confidence = min(abs(correlation), 1.0)
            
            return StockTrendCorrelation(
                stock_code=stock_data.get('code', ''),
                stock_name=stock_data.get('name', ''),
                keyword=keyword,
                correlation_score=correlation,
                trend_direction=trend_direction,
                confidence_level=confidence,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"상관관계 분석 실패: {keyword} - {e}")
            return None
    
    def get_investment_signals(self, stock_code: str) -> Dict:
        """투자 신호 생성"""
        try:
            signals = {
                'stock_code': stock_code,
                'signals': [],
                'overall_score': 0.0,
                'recommendation': 'HOLD',
                'timestamp': datetime.now()
            }
            
            # 관련 키워드 찾기
            related_keywords = []
            for keyword, stocks in self.keyword_stock_mapping.items():
                if stock_code in stocks:
                    related_keywords.append(keyword)
            
            total_score = 0.0
            signal_count = 0
            
            for keyword in related_keywords:
                # 검색 트렌드 분석
                search_trend = self.get_search_trend(keyword)
                if search_trend:
                    trend_data = search_trend.get('results', [{}])[0].get('data', [])
                    if trend_data:
                        recent_trend = trend_data[-1].get('ratio', 0)
                        prev_trend = trend_data[-2].get('ratio', 0) if len(trend_data) > 1 else 0
                        
                        trend_change = recent_trend - prev_trend
                        
                        if trend_change > 10:  # 10% 이상 증가
                            signals['signals'].append({
                                'type': 'SEARCH_TREND_UP',
                                'keyword': keyword,
                                'value': trend_change,
                                'message': f'"{keyword}" 검색량 급증 (+{trend_change:.1f}%)'
                            })
                            total_score += 0.3
                            signal_count += 1
                        elif trend_change < -10:  # 10% 이상 감소
                            signals['signals'].append({
                                'type': 'SEARCH_TREND_DOWN',
                                'keyword': keyword,
                                'value': trend_change,
                                'message': f'"{keyword}" 검색량 감소 ({trend_change:.1f}%)'
                            })
                            total_score -= 0.3
                            signal_count += 1
                
                # 뉴스 감정 분석
                sentiment = self.get_news_sentiment(keyword)
                if abs(sentiment) > 0.2:
                    if sentiment > 0:
                        signals['signals'].append({
                            'type': 'POSITIVE_SENTIMENT',
                            'keyword': keyword,
                            'value': sentiment,
                            'message': f'"{keyword}" 관련 긍정적 뉴스'
                        })
                        total_score += 0.2
                    else:
                        signals['signals'].append({
                            'type': 'NEGATIVE_SENTIMENT',
                            'keyword': keyword,
                            'value': sentiment,
                            'message': f'"{keyword}" 관련 부정적 뉴스'
                        })
                        total_score -= 0.2
                    signal_count += 1
            
            # 전체 점수 계산
            if signal_count > 0:
                signals['overall_score'] = total_score / signal_count
            
            # 투자 추천 결정
            if signals['overall_score'] > 0.3:
                signals['recommendation'] = 'BUY'
            elif signals['overall_score'] < -0.3:
                signals['recommendation'] = 'SELL'
            else:
                signals['recommendation'] = 'HOLD'
            
            return signals
            
        except Exception as e:
            logger.error(f"투자 신호 생성 실패: {stock_code} - {e}")
            return None
    
    def get_market_sentiment(self) -> Dict:
        """전체 시장 감정 분석"""
        try:
            market_keywords = [
                "주식", "투자", "증시", "코스피", "코스닥",
                "경제", "금리", "인플레이션", "달러", "원화"
            ]
            
            sentiment_scores = []
            
            for keyword in market_keywords:
                sentiment = self.get_news_sentiment(keyword)
                sentiment_scores.append(sentiment)
            
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            return {
                'market_sentiment': avg_sentiment,
                'sentiment_level': self._get_sentiment_level(avg_sentiment),
                'keywords_analyzed': market_keywords,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"시장 감정 분석 실패: {e}")
            return None
    
    def _get_sentiment_level(self, score: float) -> str:
        """감정 점수 레벨 반환"""
        if score > 0.3:
            return "매우 긍정적"
        elif score > 0.1:
            return "긍정적"
        elif score > -0.1:
            return "중립"
        elif score > -0.3:
            return "부정적"
        else:
            return "매우 부정적"
    
    def start_continuous_analysis(self):
        """연속 분석 시작"""
        if self.running:
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()
        
        logger.info("네이버 트렌드 연속 분석 시작")
    
    def stop_continuous_analysis(self):
        """연속 분석 중지"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        
        logger.info("네이버 트렌드 연속 분석 중지")
    
    def _analysis_worker(self):
        """분석 워커 스레드"""
        while self.running:
            try:
                # 주요 종목들에 대한 투자 신호 생성
                major_stocks = ["005930", "000660", "035420", "035720", "051910"]
                
                for stock_code in major_stocks:
                    signals = self.get_investment_signals(stock_code)
                    if signals:
                        self.trend_data[stock_code] = signals
                        logger.info(f"투자 신호 생성: {stock_code} - {signals['recommendation']}")
                
                # 시장 감정 분석
                market_sentiment = self.get_market_sentiment()
                if market_sentiment:
                    self.trend_data['market'] = market_sentiment
                    logger.info(f"시장 감정: {market_sentiment['sentiment_level']}")
                
                # 분석 간격 대기
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"트렌드 분석 오류: {e}")
                time.sleep(300)  # 5분 대기 후 재시도
    
    def get_trend_summary(self) -> Dict:
        """트렌드 요약 반환"""
        try:
            summary = {
                'total_stocks_analyzed': len([k for k in self.trend_data.keys() if k != 'market']),
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'market_sentiment': None,
                'top_keywords': [],
                'last_updated': datetime.now()
            }
            
            # 신호 통계
            for stock_code, data in self.trend_data.items():
                if stock_code != 'market' and isinstance(data, dict):
                    recommendation = data.get('recommendation', 'HOLD')
                    if recommendation == 'BUY':
                        summary['buy_signals'] += 1
                    elif recommendation == 'SELL':
                        summary['sell_signals'] += 1
                    else:
                        summary['hold_signals'] += 1
            
            # 시장 감정
            if 'market' in self.trend_data:
                summary['market_sentiment'] = self.trend_data['market']
            
            return summary
            
        except Exception as e:
            logger.error(f"트렌드 요약 생성 실패: {e}")
            return {}

def main():
    """테스트용 메인 함수"""
    # 네이버 API 키 설정
    client_id = "YOUR_NAVER_CLIENT_ID"
    client_secret = "YOUR_NAVER_CLIENT_SECRET"
    
    try:
        # 트렌드 분석기 초기화
        analyzer = NaverTrendAnalyzer(client_id, client_secret)
        
        # 연속 분석 시작
        analyzer.start_continuous_analysis()
        
        # 10초 대기 후 결과 확인
        time.sleep(10)
        
        # 트렌드 요약 출력
        summary = analyzer.get_trend_summary()
        print(f"트렌드 분석 요약: {summary}")
        
        # 특정 종목 분석
        signals = analyzer.get_investment_signals("005930")
        if signals:
            print(f"삼성전자 투자 신호: {signals}")
        
        # 시장 감정 분석
        market_sentiment = analyzer.get_market_sentiment()
        if market_sentiment:
            print(f"시장 감정: {market_sentiment}")
        
        # 30초 대기 후 종료
        time.sleep(30)
        analyzer.stop_continuous_analysis()
        
    except Exception as e:
        logger.error(f"트렌드 분석 테스트 실패: {e}")

if __name__ == "__main__":
    main() 