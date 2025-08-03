#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 주식 데이터 API
야후 파이낸스, 한국투자증권 API 등을 통해 실제 주식 데이터를 가져옵니다.
"""

import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import yfinance as yf

# 한국투자증권 API 관련
try:
    from kiwoom_api import KiwoomAPI
except ImportError:
    KiwoomAPI = None

@dataclass
class StockData:
    """주식 데이터 클래스"""
    code: str
    name: str
    data: pd.DataFrame
    last_updated: datetime

class StockDataAPI:
    """주식 데이터 API 클래스"""
    
    def __init__(self, data_source: str = "yahoo"):
        self.data_source = data_source
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        
        # 한국투자증권 API 초기화
        self.kiwoom_api = None
        if KiwoomAPI and data_source == "kiwoom":
            try:
                self.kiwoom_api = KiwoomAPI()
                logger.info("한국투자증권 API 초기화 완료")
            except Exception as e:
                logger.warning(f"한국투자증권 API 초기화 실패: {e}")
        
        logger.info(f"주식 데이터 API 초기화 완료 (소스: {data_source})")
    
    def get_stock_data(self, code: str, start_date: str, end_date: str, 
                      interval: str = "1d") -> Optional[StockData]:
        """주식 데이터 가져오기"""
        try:
            # 캐시 확인
            cache_key = f"{code}_{start_date}_{end_date}_{interval}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now() - cached_data.last_updated < self.cache_duration:
                    logger.info(f"캐시된 데이터 사용: {code}")
                    return cached_data
            
            # 데이터 소스별 처리
            if self.data_source == "yahoo":
                data = self._get_yahoo_data(code, start_date, end_date, interval)
            elif self.data_source == "kiwoom":
                data = self._get_kiwoom_data(code, start_date, end_date, interval)
            else:
                logger.error(f"지원하지 않는 데이터 소스: {self.data_source}")
                return None
            
            if data is None or data.empty:
                logger.warning(f"데이터 없음: {code}")
                return None
            
            # StockData 객체 생성
            stock_data = StockData(
                code=code,
                name=self._get_stock_name(code),
                data=data,
                last_updated=datetime.now()
            )
            
            # 데이터 정리 (시간대 정보 제거 포함)
            stock_data = self.clean_data(stock_data)
            
            # 캐시에 저장
            self.cache[cache_key] = stock_data
            
            logger.info(f"데이터 로드 완료: {code} ({len(stock_data.data)}개 데이터)")
            return stock_data
            
        except Exception as e:
            logger.error(f"데이터 가져오기 오류 ({code}): {e}")
            return None
    
    def _get_yahoo_data(self, code: str, start_date: str, end_date: str, 
                       interval: str) -> Optional[pd.DataFrame]:
        """야후 파이낸스에서 데이터 가져오기"""
        try:
            # 한국 주식 코드 변환 (예: 005930 -> 005930.KS)
            if code.isdigit() and len(code) == 6:
                yahoo_code = f"{code}.KS"
            else:
                yahoo_code = code
            
            # 데이터 다운로드
            ticker = yf.Ticker(yahoo_code)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                return None
            
            # 컬럼명 정규화
            data.columns = [col.lower() for col in data.columns]
            
            # 필요한 컬럼만 선택
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    data[col] = 0
            
            return data[required_columns]
            
        except Exception as e:
            logger.error(f"야후 데이터 가져오기 오류: {e}")
            return None
    
    def _get_kiwoom_data(self, code: str, start_date: str, end_date: str, 
                        interval: str) -> Optional[pd.DataFrame]:
        """한국투자증권 API에서 데이터 가져오기"""
        if not self.kiwoom_api:
            logger.error("한국투자증권 API가 초기화되지 않았습니다.")
            return None
        
        try:
            # 일별 데이터 요청
            data = self.kiwoom_api.get_daily_data(code, start_date, end_date)
            
            if not data:
                return None
            
            # DataFrame으로 변환
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 컬럼명 정규화
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"한국투자증권 데이터 가져오기 오류: {e}")
            return None
    
    def _get_stock_name(self, code: str) -> str:
        """주식 종목명 가져오기"""
        # 주요 종목 매핑
        stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI',
            '207940': '삼성바이오로직스',
            '068270': '셀트리온',
            '323410': '카카오뱅크',
            '373220': 'LG에너지솔루션'
        }
        
        return stock_names.get(code, f"종목{code}")
    
    def get_multiple_stocks(self, codes: List[str], start_date: str, end_date: str,
                          interval: str = "1d") -> Dict[str, StockData]:
        """여러 종목 데이터 가져오기"""
        results = {}
        
        logger.info(f"다중 종목 데이터 로드 시작: {len(codes)}개 종목")
        
        for code in codes:
            try:
                data = self.get_stock_data(code, start_date, end_date, interval)
                if data:
                    results[code] = data
                
                # API 호출 제한 방지
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"종목 {code} 데이터 로드 실패: {e}")
        
        logger.info(f"다중 종목 데이터 로드 완료: {len(results)}개 성공")
        return results
    
    def get_market_data(self, market: str = "KOSPI", start_date: str = None, 
                       end_date: str = None) -> Dict[str, StockData]:
        """시장 전체 데이터 가져오기"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 주요 종목 리스트
        if market == "KOSPI":
            codes = [
                '005930', '000660', '035420', '035720', '051910',
                '006400', '207940', '068270', '323410', '373220'
            ]
        elif market == "KOSDAQ":
            codes = [
                '091990', '035420', '035720', '323410', '068270',
                '207940', '051910', '006400', '373220', '005930'
            ]
        else:
            logger.error(f"지원하지 않는 시장: {market}")
            return {}
        
        return self.get_multiple_stocks(codes, start_date, end_date)
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> Optional[StockData]:
        """지수 데이터 가져오기"""
        try:
            # 지수 코드 매핑
            index_mapping = {
                'KOSPI': '^KS11',
                'KOSDAQ': '^KQ11',
                'KOSPI200': '^KS200'
            }
            
            yahoo_code = index_mapping.get(index_code, index_code)
            data = self._get_yahoo_data(yahoo_code, start_date, end_date, "1d")
            
            if data is None:
                return None
            
            return StockData(
                code=index_code,
                name=f"{index_code} 지수",
                data=data,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"지수 데이터 가져오기 오류: {e}")
            return None
    
    def validate_data(self, df: pd.DataFrame, code: str) -> bool:
        """데이터 검증 - 완화된 기준"""
        try:
            if df.empty:
                logger.warning(f"빈 데이터: {code}")
                return False
            
            # 실제 컬럼명 확인 (디버깅)
            logger.info(f"데이터 컬럼 확인: {code} - {list(df.columns)}")
            
            # 기본 검증 - 대소문자 구분 없이 확인
            required_columns_lower = ['open', 'high', 'low', 'close', 'volume']
            df_columns_lower = [col.lower() for col in df.columns]
            
            missing_columns = []
            for req_col in required_columns_lower:
                if req_col not in df_columns_lower:
                    missing_columns.append(req_col)
            
            if missing_columns:
                logger.warning(f"필수 컬럼 누락: {code} - {missing_columns}")
                return False
            
            # 데이터 수량 검증 (완화)
            if len(df) < 10:  # 최소 10개 데이터만 있으면 OK
                logger.warning(f"데이터 부족: {code} ({len(df)}개)")
                return False
            
            # OHLC 관계 검증 (완화)
            invalid_count = 0
            for idx, row in df.iterrows():
                # 컬럼명을 소문자로 변환하여 접근
                high = row.get('High', row.get('high', 0))
                low = row.get('Low', row.get('low', 0))
                open_price = row.get('Open', row.get('open', 0))
                close_price = row.get('Close', row.get('close', 0))
                
                # High >= Low 검증
                if high < low:
                    invalid_count += 1
                
                # High >= Open, Close 검증
                if high < max(open_price, close_price):
                    invalid_count += 1
                
                # Low <= Open, Close 검증
                if low > min(open_price, close_price):
                    invalid_count += 1
            
            # 오류 비율이 10% 이하면 허용 (완화)
            error_ratio = invalid_count / len(df)
            if error_ratio > 0.1:
                logger.warning(f"OHLC 관계 오류 발견: {code} (오류율: {error_ratio:.2%})")
                return False
            
            # 가격 범위 검증 (완화)
            close_col = 'Close' if 'Close' in df.columns else 'close'
            if df[close_col].min() <= 0 or df[close_col].max() > 1000000:  # 100만원 이하
                logger.warning(f"가격 범위 오류: {code}")
                return False
            
            logger.info(f"데이터 검증 통과: {code}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 검증 오류: {code} - {e}")
            return False
    
    def clean_data(self, data: StockData) -> StockData:
        """데이터 정리"""
        try:
            df = data.data.copy()
            
            # 결측값 처리
            df = df.ffill()  # 전일 데이터로 채우기
            df = df.bfill()  # 다음 데이터로 채우기
            
            # 이상값 처리 (가격이 0인 경우)
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].replace(0, np.nan)
                df[col] = df[col].ffill()
            
            # 거래량 0 처리
            df['volume'] = df['volume'].fillna(0)
            
            # 시간대 정보 제거 (백테스팅 호환성을 위해)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # 정리된 데이터로 새로운 StockData 생성
            cleaned_data = StockData(
                code=data.code,
                name=data.name,
                data=df,
                last_updated=datetime.now()
            )
            
            logger.info(f"데이터 정리 완료: {data.code}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"데이터 정리 오류: {e}")
            return data

class DataManager:
    """데이터 관리자"""
    
    def __init__(self, api: StockDataAPI):
        self.api = api
        self.data_cache = {}
    
    def get_backtest_data(self, codes: List[str], start_date: str, end_date: str,
                         validate: bool = True, clean: bool = True) -> Dict[str, StockData]:
        """백테스트용 데이터 준비"""
        logger.info("백테스트 데이터 준비 시작")
        
        # 데이터 가져오기
        stock_data = self.api.get_multiple_stocks(codes, start_date, end_date)
        
        if not stock_data:
            logger.error("데이터를 가져올 수 없습니다.")
            return {}
        
        # 데이터 검증 및 정리
        valid_data = {}
        for code, data in stock_data.items():
            try:
                # 검증
                if validate and not self.api.validate_data(data.data, code):
                    logger.warning(f"데이터 검증 실패: {code}")
                    continue
                
                # 정리
                if clean:
                    data = self.api.clean_data(data)
                
                valid_data[code] = data
                
            except Exception as e:
                logger.error(f"데이터 처리 오류 ({code}): {e}")
        
        logger.info(f"백테스트 데이터 준비 완료: {len(valid_data)}개 종목")
        return valid_data
    
    def get_benchmark_data(self, benchmark: str, start_date: str, end_date: str) -> Optional[StockData]:
        """벤치마크 데이터 가져오기"""
        return self.api.get_index_data(benchmark, start_date, end_date)
    
    def export_data(self, data: Dict[str, StockData], format: str = "csv", 
                   output_dir: str = "data") -> bool:
        """데이터 내보내기"""
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for code, stock_data in data.items():
                filename = f"{output_dir}/{code}_{format}.{format}"
                
                if format == "csv":
                    stock_data.data.to_csv(filename)
                elif format == "json":
                    stock_data.data.to_json(filename)
                elif format == "excel":
                    stock_data.data.to_excel(filename)
                
                logger.info(f"데이터 내보내기: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"데이터 내보내기 오류: {e}")
            return False

def main():
    """테스트 함수"""
    logger.info("주식 데이터 API 테스트 시작")
    
    # API 초기화
    api = StockDataAPI(data_source="yahoo")
    
    # 테스트 데이터 가져오기
    codes = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    try:
        # 개별 종목 데이터
        for code in codes:
            data = api.get_stock_data(code, start_date, end_date)
            if data:
                print(f"{data.name} ({data.code}): {len(data.data)}개 데이터")
                print(f"최근 종가: {data.data['close'].iloc[-1]:,.0f}원")
                print()
        
        # 다중 종목 데이터
        all_data = api.get_multiple_stocks(codes, start_date, end_date)
        print(f"총 {len(all_data)}개 종목 데이터 로드 완료")
        
        # 데이터 관리자 테스트
        manager = DataManager(api)
        backtest_data = manager.get_backtest_data(codes, start_date, end_date)
        print(f"백테스트 데이터 준비 완료: {len(backtest_data)}개 종목")
        
        # 벤치마크 데이터
        benchmark = manager.get_benchmark_data("KOSPI", start_date, end_date)
        if benchmark:
            print(f"벤치마크 데이터 로드 완료: {benchmark.name}")
        
        logger.info("주식 데이터 API 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 오류: {e}")

if __name__ == "__main__":
    main() 