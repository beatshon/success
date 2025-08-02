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
        
        # 주가지수 관련 설정
        self.market_indices = {
            'KOSPI': '코스피',
            'KOSDAQ': '코스닥',
            'KOSPI200': '코스피200',
            'KOSDAQ150': '코스닥150'
        }
        
        # 시장 상황별 투자 전략 설정
        self.market_strategies = {
            'BULL_MARKET': {
                'high_correlation_threshold': 0.6,  # 높은 상관관계 종목 임계값
                'low_correlation_threshold': 0.3,   # 낮은 상관관계 종목 임계값
                'high_correlation_weight': 0.7,     # 높은 상관관계 종목 가중치
                'low_correlation_weight': 0.3       # 낮은 상관관계 종목 가중치
            },
            'BEAR_MARKET': {
                'high_correlation_threshold': 0.6,
                'low_correlation_threshold': 0.3,
                'high_correlation_weight': 0.2,     # 하락장에서는 높은 상관관계 종목 비중 감소
                'low_correlation_weight': 0.8       # 하락장에서는 낮은 상관관계 종목 비중 증가
            },
            'SIDEWAYS_MARKET': {
                'high_correlation_threshold': 0.6,
                'low_correlation_threshold': 0.3,
                'high_correlation_weight': 0.5,     # 횡보장에서는 균형
                'low_correlation_weight': 0.5
            }
        }
        
        # 시장 상황 판단 임계값
        self.market_trend_thresholds = {
            'BULL_MARKET': 0.05,    # 5% 이상 상승 시 상승장
            'BEAR_MARKET': -0.05,   # 5% 이상 하락 시 하락장
            'SIDEWAYS_MARKET': 0.02 # ±2% 범위 시 횡보장
        }
        
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
        """네이버 검색 트렌드 조회"""
        try:
            url = f"{self.base_url}/datalab/search"
            
            # 기간 설정
            end_date = datetime.now()
            if period == "1week":
                start_date = end_date - timedelta(days=7)
            elif period == "1month":
                start_date = end_date - timedelta(days=30)
            elif period == "3months":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            data = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
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
            
            # 데이터 정제 및 저장
            trend_data = self._process_trend_data(result, keyword, TrendType.SEARCH)
            self._save_trend_data(trend_data)
            
            return result
            
        except Exception as e:
            logger.error(f"검색 트렌드 조회 실패 ({keyword}): {e}")
            handle_error(ErrorType.API_ERROR, ErrorLevel.WARNING, f"네이버 검색 트렌드 조회 실패: {e}")
            return {"error": str(e)}

    def get_shopping_trend(self, keyword: str) -> Dict:
        """네이버 쇼핑 트렌드 조회"""
        try:
            url = f"{self.base_url}/datalab/shopping/categories"
            
            # 쇼핑 카테고리 매핑
            category_mapping = {
                "전기차": "50000000",  # 자동차
                "스마트폰": "50000002",  # 디지털/가전
                "노트북": "50000002",  # 디지털/가전
                "게임": "50000003",  # 도서/문구
                "의류": "50000001",  # 패션의류
                "화장품": "50000004",  # 뷰티
                "식품": "50000005",  # 식품
                "가구": "50000006",  # 가구/인테리어
                "스포츠": "50000007",  # 스포츠/레저
                "유아용품": "50000008",  # 유아동/출산
                "반려동물": "50000009",  # 반려동물용품
            }
            
            category_id = category_mapping.get(keyword, "50000000")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            data = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": "date",
                "category": category_id,
                "device": "pc",
                "gender": "",
                "ages": []
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # 데이터 정제 및 저장
            trend_data = self._process_trend_data(result, keyword, TrendType.SHOPPING)
            self._save_trend_data(trend_data)
            
            return result
            
        except Exception as e:
            logger.error(f"쇼핑 트렌드 조회 실패 ({keyword}): {e}")
            handle_error(ErrorType.API_ERROR, ErrorLevel.WARNING, f"네이버 쇼핑 트렌드 조회 실패: {e}")
            return {"error": str(e)}

    def get_news_sentiment(self, keyword: str) -> float:
        """뉴스 감정 분석"""
        try:
            url = f"{self.base_url}/search/news.json"
            
            params = {
                'query': keyword,
                'display': 100,
                'start': 1,
                'sort': 'date'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if 'items' not in result:
                return 0.0
            
            # 감정 분석 키워드
            positive_words = [
                '상승', '급등', '호재', '성장', '확대', '증가', '개발', '성공',
                '돌파', '상향', '긍정', '낙관', '기대', '희망', '강세', '상향조정'
            ]
            
            negative_words = [
                '하락', '급락', '악재', '감소', '축소', '실패', '위험', '부정',
                '하향', '비관', '우려', '절망', '약세', '하향조정', '손실', '폭락'
            ]
            
            total_score = 0.0
            article_count = 0
            
            for item in result['items']:
                title = item.get('title', '')
                description = item.get('description', '')
                content = f"{title} {description}"
                
                # 감정 점수 계산
                positive_count = sum(1 for word in positive_words if word in content)
                negative_count = sum(1 for word in negative_words if word in content)
                
                if positive_count > 0 or negative_count > 0:
                    score = (positive_count - negative_count) / (positive_count + negative_count)
                    total_score += score
                    article_count += 1
            
            sentiment_score = total_score / article_count if article_count > 0 else 0.0
            
            # 데이터베이스에 저장
            trend_data = TrendData(
                keyword=keyword,
                trend_type=TrendType.NEWS,
                value=sentiment_score,
                timestamp=datetime.now(),
                sentiment_score=sentiment_score
            )
            self._save_trend_data(trend_data)
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"뉴스 감정 분석 실패 ({keyword}): {e}")
            handle_error(ErrorType.API_ERROR, ErrorLevel.WARNING, f"뉴스 감정 분석 실패: {e}")
            return 0.0

    def _process_trend_data(self, api_result: Dict, keyword: str, trend_type: TrendType) -> TrendData:
        """API 결과를 TrendData로 변환"""
        try:
            if 'results' not in api_result or not api_result['results']:
                return None
            
            data_points = api_result['results'][0]['data']
            
            if not data_points:
                return None
            
            # 최신 값과 이전 값 비교
            current_value = data_points[-1]['ratio']
            previous_value = data_points[-2]['ratio'] if len(data_points) > 1 else current_value
            
            # 변화율 계산
            volume_change = ((current_value - previous_value) / previous_value * 100) if previous_value > 0 else 0
            
            # 모멘텀 계산 (최근 7일)
            recent_values = [point['ratio'] for point in data_points[-7:]]
            momentum_score = self._calculate_momentum(recent_values)
            
            # 변동성 계산
            volatility = self._calculate_volatility(recent_values)
            
            # 감정 점수 (간접적 계산)
            sentiment_score = 0.0
            if volume_change > 0:
                sentiment_score = min(volume_change / 10, 1.0)  # 최대 1.0
            elif volume_change < 0:
                sentiment_score = max(volume_change / 10, -1.0)  # 최소 -1.0
            
            return TrendData(
                keyword=keyword,
                trend_type=trend_type,
                value=current_value,
                timestamp=datetime.now(),
                related_stocks=self.keyword_stock_mapping.get(keyword, []),
                sentiment_score=sentiment_score,
                volume_change=volume_change,
                momentum_score=momentum_score,
                volatility=volatility
            )
            
        except Exception as e:
            logger.error(f"트렌드 데이터 처리 실패: {e}")
            return None

    def _calculate_momentum(self, values: List[float]) -> float:
        """모멘텀 점수 계산"""
        if len(values) < 2:
            return 0.0
        
        # 선형 회귀를 통한 기울기 계산
        x = np.arange(len(values))
        y = np.array(values)
        
        # 기울기 계산
        slope = np.polyfit(x, y, 1)[0]
        
        # 정규화 (0~1 범위로)
        max_value = max(values) if values else 1
        normalized_slope = slope / max_value if max_value > 0 else 0
        
        return min(max(normalized_slope, -1), 1)  # -1 ~ 1 범위로 제한

    def _calculate_volatility(self, values: List[float]) -> float:
        """변동성 계산"""
        if len(values) < 2:
            return 0.0
        
        # 표준편차 계산
        std_dev = np.std(values)
        mean_value = np.mean(values)
        
        # 변동계수 (CV) 계산
        cv = std_dev / mean_value if mean_value > 0 else 0
        
        return cv

    def _save_trend_data(self, trend_data: TrendData):
        """트렌드 데이터를 데이터베이스에 저장"""
        if not trend_data:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trend_data 
                (keyword, trend_type, value, timestamp, sentiment_score, volume_change, momentum_score, volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trend_data.keyword,
                trend_data.trend_type.value,
                trend_data.value,
                trend_data.timestamp.isoformat(),
                trend_data.sentiment_score,
                trend_data.volume_change,
                trend_data.momentum_score,
                trend_data.volatility
            ))
            
            conn.commit()
            conn.close()
            
            # 메모리에도 저장
            if trend_data.keyword not in self.trend_data:
                self.trend_data[trend_data.keyword] = []
            self.trend_data[trend_data.keyword].append(trend_data)
            
        except Exception as e:
            logger.error(f"트렌드 데이터 저장 실패: {e}")

    def get_historical_trend_data(self, keyword: str, days: int = 30) -> List[TrendData]:
        """과거 트렌드 데이터 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            cursor.execute('''
                SELECT keyword, trend_type, value, timestamp, sentiment_score, 
                       volume_change, momentum_score, volatility
                FROM trend_data 
                WHERE keyword = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (keyword, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            trend_data_list = []
            for row in rows:
                trend_data = TrendData(
                    keyword=row[0],
                    trend_type=TrendType(row[1]),
                    value=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    sentiment_score=row[4],
                    volume_change=row[5],
                    momentum_score=row[6],
                    volatility=row[7]
                )
                trend_data_list.append(trend_data)
            
            return trend_data_list
            
        except Exception as e:
            logger.error(f"과거 트렌드 데이터 조회 실패: {e}")
            return []

    async def collect_real_time_data(self):
        """실시간 데이터 수집"""
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                
                for keyword in self.monitoring_keywords:
                    # 검색 트렌드 수집
                    task1 = self._collect_search_trend_async(session, keyword)
                    tasks.append(task1)
                    
                    # 뉴스 감정 분석
                    task2 = self._collect_news_sentiment_async(session, keyword)
                    tasks.append(task2)
                
                # 병렬 실행
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 결과 처리
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"실시간 데이터 수집 실패: {result}")
                    elif result:
                        self._save_trend_data(result)
                
                logger.info(f"실시간 데이터 수집 완료: {len(self.monitoring_keywords)}개 키워드")
                
        except Exception as e:
            logger.error(f"실시간 데이터 수집 실패: {e}")

    async def _collect_search_trend_async(self, session: aiohttp.ClientSession, keyword: str):
        """비동기 검색 트렌드 수집"""
        try:
            url = f"{self.base_url}/datalab/search"
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # 최근 7일
            
            data = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": "date",
                "keywordGroups": [
                    {
                        "groupName": keyword,
                        "keywords": [keyword]
                    }
                ]
            }
            
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._process_trend_data(result, keyword, TrendType.SEARCH)
                else:
                    logger.warning(f"검색 트렌드 API 오류 ({keyword}): {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"비동기 검색 트렌드 수집 실패 ({keyword}): {e}")
            return None

    async def _collect_news_sentiment_async(self, session: aiohttp.ClientSession, keyword: str):
        """비동기 뉴스 감정 분석 수집"""
        try:
            url = f"{self.base_url}/search/news.json"
            params = {
                'query': keyword,
                'display': 50,
                'start': 1,
                'sort': 'date'
            }
            
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if 'items' in result and result['items']:
                        # 간단한 감정 분석
                        positive_words = ['상승', '급등', '호재', '성장', '확대', '증가']
                        negative_words = ['하락', '급락', '악재', '감소', '축소', '실패']
                        
                        total_score = 0.0
                        article_count = 0
                        
                        for item in result['items']:
                            content = f"{item.get('title', '')} {item.get('description', '')}"
                            
                            positive_count = sum(1 for word in positive_words if word in content)
                            negative_count = sum(1 for word in negative_words if word in content)
                            
                            if positive_count > 0 or negative_count > 0:
                                score = (positive_count - negative_count) / (positive_count + negative_count)
                                total_score += score
                                article_count += 1
                        
                        sentiment_score = total_score / article_count if article_count > 0 else 0.0
                        
                        return TrendData(
                            keyword=keyword,
                            trend_type=TrendType.NEWS,
                            value=sentiment_score,
                            timestamp=datetime.now(),
                            sentiment_score=sentiment_score
                        )
                else:
                    logger.warning(f"뉴스 API 오류 ({keyword}): {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"비동기 뉴스 감정 분석 실패 ({keyword}): {e}")
            return None
    
    def analyze_trend_correlation(self, keyword: str, stock_data: Dict) -> StockTrendCorrelation:
        """트렌드-주식 상관관계 분석"""
        try:
            # 과거 트렌드 데이터 조회
            trend_history = self.get_historical_trend_data(keyword, days=30)
            
            if not trend_history or not stock_data:
                return None
            
            # 주식 데이터와 트렌드 데이터 정렬
            trend_values = [t.value for t in trend_history]
            stock_prices = stock_data.get('prices', [])
            
            if len(trend_values) < 10 or len(stock_prices) < 10:
                return None
            
            # 상관관계 계산
            min_length = min(len(trend_values), len(stock_prices))
            trend_values = trend_values[-min_length:]
            stock_prices = stock_prices[-min_length:]
            
            # 피어슨 상관계수 계산
            correlation = np.corrcoef(trend_values, stock_prices)[0, 1]
            
            if np.isnan(correlation):
                correlation = 0.0
            
            # 트렌드 방향 결정
            recent_trend = trend_values[-1] - trend_values[0] if len(trend_values) > 1 else 0
            if recent_trend > 0:
                trend_direction = "positive"
            elif recent_trend < 0:
                trend_direction = "negative"
            else:
                trend_direction = "neutral"
            
            # 신뢰도 계산 (데이터 품질 기반)
            confidence_level = min(abs(correlation), 1.0)
            
            # 영향도 점수 계산
            impact_score = abs(correlation) * (len(trend_values) / 30)  # 데이터 양 고려
            
            # 예측 정확도 (과거 데이터 기반)
            prediction_accuracy = self._calculate_prediction_accuracy(trend_history, stock_data)
            
            # 관련 주식 코드들
            related_stocks = self.keyword_stock_mapping.get(keyword, [])
            
            correlation_data = StockTrendCorrelation(
                stock_code=related_stocks[0] if related_stocks else "",
                stock_name=keyword,
                keyword=keyword,
                correlation_score=correlation,
                trend_direction=trend_direction,
                confidence_level=confidence_level,
                last_updated=datetime.now(),
                impact_score=impact_score,
                prediction_accuracy=prediction_accuracy
            )
            
            # 데이터베이스에 저장
            self._save_correlation_data(correlation_data)
            
            return correlation_data
            
        except Exception as e:
            logger.error(f"트렌드 상관관계 분석 실패 ({keyword}): {e}")
            return None

    def _calculate_prediction_accuracy(self, trend_history: List[TrendData], stock_data: Dict) -> float:
        """예측 정확도 계산"""
        try:
            if len(trend_history) < 10:
                return 0.0
            
            # 트렌드 변화율과 주식 가격 변화율 비교
            trend_changes = []
            stock_changes = []
            
            for i in range(1, len(trend_history)):
                trend_change = (trend_history[i].value - trend_history[i-1].value) / trend_history[i-1].value
                trend_changes.append(trend_change)
            
            stock_prices = stock_data.get('prices', [])
            for i in range(1, len(stock_prices)):
                stock_change = (stock_prices[i] - stock_prices[i-1]) / stock_prices[i-1]
                stock_changes.append(stock_change)
            
            # 방향 일치도 계산
            correct_predictions = 0
            total_predictions = 0
            
            min_length = min(len(trend_changes), len(stock_changes))
            for i in range(min_length):
                if (trend_changes[i] > 0 and stock_changes[i] > 0) or \
                   (trend_changes[i] < 0 and stock_changes[i] < 0):
                    correct_predictions += 1
                total_predictions += 1
            
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
            return accuracy
            
        except Exception as e:
            logger.error(f"예측 정확도 계산 실패: {e}")
            return 0.0

    def _save_correlation_data(self, correlation_data: StockTrendCorrelation):
        """상관관계 데이터를 데이터베이스에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO correlation_data 
                (stock_code, stock_name, keyword, correlation_score, trend_direction, 
                 confidence_level, impact_score, prediction_accuracy, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                correlation_data.stock_code,
                correlation_data.stock_name,
                correlation_data.keyword,
                correlation_data.correlation_score,
                correlation_data.trend_direction,
                correlation_data.confidence_level,
                correlation_data.impact_score,
                correlation_data.prediction_accuracy,
                correlation_data.last_updated.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # 메모리에도 저장
            key = f"{correlation_data.stock_code}_{correlation_data.keyword}"
            self.correlation_data[key] = correlation_data
            
        except Exception as e:
            logger.error(f"상관관계 데이터 저장 실패: {e}")

    def get_investment_signals(self, stock_code: str) -> Dict:
        """투자 신호 생성"""
        try:
            signals = {
                'stock_code': stock_code,
                'signals': [],
                'overall_signal': 'HOLD',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
            
            # 해당 주식과 관련된 키워드들 찾기
            related_keywords = []
            for keyword, stock_codes in self.keyword_stock_mapping.items():
                if stock_code in stock_codes:
                    related_keywords.append(keyword)
            
            if not related_keywords:
                return signals
            
            total_score = 0.0
            signal_count = 0
            
            for keyword in related_keywords:
                # 최신 트렌드 데이터 조회
                recent_trends = self.get_historical_trend_data(keyword, days=7)
                
                if not recent_trends:
                    continue
                
                latest_trend = recent_trends[0]
                
                # 신호 점수 계산
                signal_score = self._calculate_signal_score(latest_trend)
                
                # 신호 생성
                if signal_score > 0.3:
                    signal_type = 'BUY'
                elif signal_score < -0.3:
                    signal_type = 'SELL'
                else:
                    signal_type = 'HOLD'
                
                signal = {
                    'keyword': keyword,
                    'signal_type': signal_type,
                    'score': signal_score,
                    'trend_value': latest_trend.value,
                    'sentiment': latest_trend.sentiment_score,
                    'momentum': latest_trend.momentum_score,
                    'volatility': latest_trend.volatility,
                    'timestamp': latest_trend.timestamp.isoformat()
                }
                
                signals['signals'].append(signal)
                total_score += signal_score
                signal_count += 1
            
            # 전체 신호 결정
            if signal_count > 0:
                avg_score = total_score / signal_count
                signals['confidence'] = min(abs(avg_score), 1.0)
                
                if avg_score > 0.2:
                    signals['overall_signal'] = 'BUY'
                elif avg_score < -0.2:
                    signals['overall_signal'] = 'SELL'
                else:
                    signals['overall_signal'] = 'HOLD'
            
            return signals
            
        except Exception as e:
            logger.error(f"투자 신호 생성 실패 ({stock_code}): {e}")
            return {'error': str(e)}

    def _calculate_signal_score(self, trend_data: TrendData) -> float:
        """신호 점수 계산"""
        try:
            # 가중 평균 계산
            weights = {
                'sentiment': 0.3,
                'momentum': 0.3,
                'volume_change': 0.2,
                'volatility': 0.2
            }
            
            # 감정 점수 (-1 ~ 1)
            sentiment_score = trend_data.sentiment_score
            
            # 모멘텀 점수 (-1 ~ 1)
            momentum_score = trend_data.momentum_score
            
            # 거래량 변화 점수 (-1 ~ 1)
            volume_score = min(max(trend_data.volume_change / 50, -1), 1)
            
            # 변동성 점수 (낮을수록 좋음, -1 ~ 1)
            volatility_score = -min(trend_data.volatility, 1.0)
            
            # 가중 평균
            final_score = (
                sentiment_score * weights['sentiment'] +
                momentum_score * weights['momentum'] +
                volume_score * weights['volume_change'] +
                volatility_score * weights['volatility']
            )
            
            return min(max(final_score, -1), 1)  # -1 ~ 1 범위로 제한
            
        except Exception as e:
            logger.error(f"신호 점수 계산 실패: {e}")
            return 0.0

    def get_market_sentiment(self) -> Dict:
        """전체 시장 감정 분석"""
        try:
            market_sentiment = {
                'overall_sentiment': 0.0,
                'sector_sentiments': {},
                'trending_keywords': [],
                'risk_level': 'MEDIUM',
                'timestamp': datetime.now().isoformat()
            }
            
            # 섹터별 감정 분석
            sectors = {
                'technology': ['삼성전자', 'SK하이닉스', '네이버', '카카오', 'LG전자'],
                'automotive': ['현대차', '기아', 'LG화학', '삼성SDI'],
                'finance': ['KB금융', '신한지주', '하나금융지주', '우리금융지주'],
                'biotech': ['삼성바이오로직스', '셀트리온', '한미약품', '유한양행'],
                'retail': ['신세계', '롯데쇼핑', '아모레퍼시픽', 'LG생활건강']
            }
            
            sector_scores = {}
            
            for sector, keywords in sectors.items():
                sector_score = 0.0
                keyword_count = 0
                
                for keyword in keywords:
                    recent_trends = self.get_historical_trend_data(keyword, days=3)
                    if recent_trends:
                        latest_trend = recent_trends[0]
                        sector_score += latest_trend.sentiment_score
                        keyword_count += 1
                
                if keyword_count > 0:
                    avg_score = sector_score / keyword_count
                    sector_scores[sector] = avg_score
                    market_sentiment['sector_sentiments'][sector] = {
                        'score': avg_score,
                        'level': self._get_sentiment_level(avg_score)
                    }
            
            # 전체 감정 점수
            if sector_scores:
                market_sentiment['overall_sentiment'] = sum(sector_scores.values()) / len(sector_scores)
            
            # 트렌딩 키워드 찾기
            trending_keywords = self._find_trending_keywords()
            market_sentiment['trending_keywords'] = trending_keywords
            
            # 리스크 레벨 결정
            overall_sentiment = market_sentiment['overall_sentiment']
            if overall_sentiment > 0.3:
                market_sentiment['risk_level'] = 'LOW'
            elif overall_sentiment < -0.3:
                market_sentiment['risk_level'] = 'HIGH'
            else:
                market_sentiment['risk_level'] = 'MEDIUM'
            
            return market_sentiment
            
        except Exception as e:
            logger.error(f"시장 감정 분석 실패: {e}")
            return {'error': str(e)}

    def _find_trending_keywords(self) -> List[Dict]:
        """트렌딩 키워드 찾기"""
        try:
            trending_keywords = []
            
            for keyword in self.monitoring_keywords:
                recent_trends = self.get_historical_trend_data(keyword, days=3)
                
                if len(recent_trends) >= 2:
                    latest = recent_trends[0]
                    previous = recent_trends[1]
                    
                    # 변화율 계산
                    change_rate = ((latest.value - previous.value) / previous.value * 100) if previous.value > 0 else 0
                    
                    # 트렌딩 기준: 변화율이 10% 이상
                    if abs(change_rate) >= 10:
                        trending_keywords.append({
                            'keyword': keyword,
                            'change_rate': change_rate,
                            'trend': 'up' if change_rate > 0 else 'down',
                            'sentiment': latest.sentiment_score,
                            'value': latest.value
                        })
            
            # 변화율 기준으로 정렬
            trending_keywords.sort(key=lambda x: abs(x['change_rate']), reverse=True)
            
            return trending_keywords[:10]  # 상위 10개만 반환
            
        except Exception as e:
            logger.error(f"트렌딩 키워드 찾기 실패: {e}")
            return []

    def _get_sentiment_level(self, score: float) -> str:
        """감정 수준 판단"""
        if score > 0.3:
            return 'POSITIVE'
        elif score < -0.3:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'

    def start_continuous_analysis(self):
        """연속 분석 시작"""
        if self.running:
            logger.warning("이미 분석이 실행 중입니다.")
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        logger.info("네이버 트렌드 연속 분석이 시작되었습니다.")

    def stop_continuous_analysis(self):
        """연속 분석 중지"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        logger.info("네이버 트렌드 연속 분석이 중지되었습니다.")

    def _analysis_worker(self):
        """분석 워커 스레드"""
        while self.running:
            try:
                # 실시간 데이터 수집
                asyncio.run(self.collect_real_time_data())
                
                # 상관관계 분석 업데이트
                self._update_correlations()
                
                # 잠시 대기
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"분석 워커 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기

    def _update_correlations(self):
        """상관관계 데이터 업데이트"""
        try:
            # 주요 키워드들에 대해 상관관계 분석 수행
            for keyword in self.monitoring_keywords[:10]:  # 상위 10개만
                # 가상의 주식 데이터 (실제로는 주식 API에서 가져와야 함)
                stock_data = {
                    'prices': [100 + i * 0.5 + np.random.normal(0, 1) for i in range(30)]
                }
                
                correlation = self.analyze_trend_correlation(keyword, stock_data)
                if correlation:
                    logger.debug(f"상관관계 업데이트: {keyword} - {correlation.correlation_score:.3f}")
                    
        except Exception as e:
            logger.error(f"상관관계 업데이트 실패: {e}")

    def get_trend_summary(self) -> Dict:
        """트렌드 요약 정보"""
        try:
            summary = {
                'total_keywords': len(self.monitoring_keywords),
                'active_trends': 0,
                'positive_trends': 0,
                'negative_trends': 0,
                'neutral_trends': 0,
                'top_trending': [],
                'market_sentiment': 'NEUTRAL',
                'last_updated': datetime.now().isoformat()
            }
            
            # 최근 트렌드 분석
            for keyword in self.monitoring_keywords:
                recent_trends = self.get_historical_trend_data(keyword, days=1)
                
                if recent_trends:
                    latest_trend = recent_trends[0]
                    summary['active_trends'] += 1
                    
                    if latest_trend.sentiment_score > 0.2:
                        summary['positive_trends'] += 1
                    elif latest_trend.sentiment_score < -0.2:
                        summary['negative_trends'] += 1
                    else:
                        summary['neutral_trends'] += 1
            
            # 상위 트렌딩 키워드
            trending_keywords = self._find_trending_keywords()
            summary['top_trending'] = trending_keywords[:5]
            
            # 전체 시장 감정
            if summary['positive_trends'] > summary['negative_trends']:
                summary['market_sentiment'] = 'POSITIVE'
            elif summary['negative_trends'] > summary['positive_trends']:
                summary['market_sentiment'] = 'NEGATIVE'
            else:
                summary['market_sentiment'] = 'NEUTRAL'
            
            return summary
            
        except Exception as e:
            logger.error(f"트렌드 요약 생성 실패: {e}")
            return {'error': str(e)}

def main():
    """메인 함수"""
    try:
        # 환경 변수에서 API 키 로드
        client_id = os.getenv('NAVER_CLIENT_ID', 'YOUR_NAVER_CLIENT_ID')
        client_secret = os.getenv('NAVER_CLIENT_SECRET', 'YOUR_NAVER_CLIENT_SECRET')
        
        # 분석기 초기화
        analyzer = NaverTrendAnalyzer(client_id, client_secret)
        
        # 연속 분석 시작
        analyzer.start_continuous_analysis()
        
        # 무한 루프로 실행
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("프로그램 종료 요청됨")
        finally:
            analyzer.stop_continuous_analysis()
            
    except Exception as e:
        logger.error(f"메인 함수 오류: {e}")
        handle_error(ErrorType.SYSTEM_ERROR, ErrorLevel.ERROR, f"네이버 트렌드 분석기 오류: {e}")

if __name__ == "__main__":
    main() 