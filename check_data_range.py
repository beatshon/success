#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 데이터의 날짜 범위를 확인하는 스크립트
"""

import sys
import os
from datetime import datetime
from loguru import logger
import pandas as pd

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_stock_data_api import StockDataAPI

def check_data_range():
    """실제 데이터의 날짜 범위 확인"""
    logger.info("=== 실제 데이터 날짜 범위 확인 ===")
    
    # API 초기화
    api = StockDataAPI(data_source="yahoo")
    
    # 테스트 종목들
    test_codes = ["005930.KS", "000660.KS", "035420.KS"]
    
    for code in test_codes:
        logger.info(f"\n{code} 데이터 확인:")
        
        try:
            # 2023년 전체 데이터 가져오기
            data = api.get_stock_data(code, "2023-01-01", "2023-12-31")
            
            if data is not None and not data.data.empty:
                logger.info(f"  데이터 수: {len(data.data)}개")
                logger.info(f"  첫 번째 날짜: {data.data.index[0]}")
                logger.info(f"  마지막 날짜: {data.data.index[-1]}")
                logger.info(f"  실제 기간: {data.data.index[0].strftime('%Y-%m-%d')} ~ {data.data.index[-1].strftime('%Y-%m-%d')}")
                
                # 주중 데이터만 필터링
                weekday_data = data.data[data.data.index.weekday < 5]
                logger.info(f"  주중 데이터 수: {len(weekday_data)}개")
                
                if len(weekday_data) > 0:
                    logger.info(f"  주중 첫 날짜: {weekday_data.index[0]}")
                    logger.info(f"  주중 마지막 날짜: {weekday_data.index[-1]}")
                
                # 샘플 데이터 확인
                logger.info(f"  샘플 데이터 (처음 5개):")
                for i, (date, row) in enumerate(data.data.head().iterrows()):
                    logger.info(f"    {date.strftime('%Y-%m-%d')}: 종가 {row['close']:,.0f}원")
                
            else:
                logger.warning(f"  데이터 없음")
                
        except Exception as e:
            logger.error(f"  오류 발생: {e}")

def suggest_backtest_period():
    """백테스트 기간 제안"""
    logger.info("\n=== 백테스트 기간 제안 ===")
    
    # API 초기화
    api = StockDataAPI(data_source="yahoo")
    
    # 삼성전자 데이터로 기간 확인
    data = api.get_stock_data("005930.KS", "2023-01-01", "2023-12-31")
    
    if data is not None and not data.data.empty:
        # 주중 데이터만 필터링
        weekday_data = data.data[data.data.index.weekday < 5]
        
        if len(weekday_data) > 30:  # 최소 30일 이상의 데이터가 있는 경우
            start_date = weekday_data.index[30]  # 30일 후부터 시작 (충분한 데이터 확보)
            end_date = weekday_data.index[-1]
            
            logger.info(f"제안하는 백테스트 기간:")
            logger.info(f"  시작일: {start_date.strftime('%Y-%m-%d')}")
            logger.info(f"  종료일: {end_date.strftime('%Y-%m-%d')}")
            logger.info(f"  총 거래일: {len(weekday_data[weekday_data.index >= start_date])}일")
            
            return start_date, end_date
        else:
            logger.warning("충분한 데이터가 없습니다.")
            return None, None
    else:
        logger.error("데이터를 가져올 수 없습니다.")
        return None, None

def main():
    """메인 함수"""
    logger.info("실제 데이터 날짜 범위 확인 시작")
    
    # 1. 데이터 범위 확인
    check_data_range()
    
    # 2. 백테스트 기간 제안
    start_date, end_date = suggest_backtest_period()
    
    if start_date and end_date:
        logger.info(f"\n=== 개선된 백테스트 설정 제안 ===")
        logger.info(f"config = BacktestConfig(")
        logger.info(f"    mode=BacktestMode.SINGLE_STOCK,")
        logger.info(f"    start_date='{start_date.strftime('%Y-%m-%d')}',")
        logger.info(f"    end_date='{end_date.strftime('%Y-%m-%d')}',")
        logger.info(f"    initial_capital=10000000")
        logger.info(f")")
    
    logger.info("데이터 범위 확인 완료")

if __name__ == "__main__":
    main() 