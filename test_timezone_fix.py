#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시간대 문제 해결 테스트
"""

import sys
import os
from datetime import datetime
from loguru import logger
import pandas as pd

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_stock_data_api import StockDataAPI

def test_timezone_fix():
    """시간대 문제 해결 테스트"""
    logger.info("=== 시간대 문제 해결 테스트 ===")
    
    # API 초기화
    api = StockDataAPI(data_source="yahoo")
    
    # 테스트 종목
    test_code = "005930.KS"
    
    try:
        # 데이터 로드
        logger.info(f"{test_code} 데이터 로드 중...")
        data = api.get_stock_data(test_code, "2023-02-15", "2023-02-20")
        
        if data is not None and not data.data.empty:
            logger.info(f"데이터 로드 성공: {len(data.data)}개")
            
            # 시간대 정보 확인
            logger.info(f"인덱스 시간대 정보: {data.data.index.tz}")
            
            # 샘플 데이터 확인
            logger.info("샘플 데이터:")
            for i, (date, row) in enumerate(data.data.head().iterrows()):
                logger.info(f"  {date}: 종가 {row['close']:,.0f}원")
            
            # 날짜 비교 테스트
            test_date = datetime(2023, 2, 15)
            logger.info(f"테스트 날짜: {test_date}")
            logger.info(f"테스트 날짜 시간대: {test_date.tzinfo}")
            
            # 날짜가 데이터에 있는지 확인
            if test_date in data.data.index:
                logger.info("✅ 날짜 비교 성공!")
                price = data.data.loc[test_date, 'close']
                logger.info(f"해당 날짜 종가: {price:,.0f}원")
            else:
                logger.warning("⚠️ 날짜 비교 실패")
                logger.info(f"사용 가능한 날짜들: {list(data.data.index[:5])}")
            
            return True
        else:
            logger.error("데이터 로드 실패")
            return False
            
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """메인 함수"""
    logger.info("시간대 문제 해결 테스트 시작")
    
    success = test_timezone_fix()
    
    if success:
        logger.info("✅ 시간대 문제 해결 테스트 성공")
    else:
        logger.error("❌ 시간대 문제 해결 테스트 실패")
    
    logger.info("테스트 완료")

if __name__ == "__main__":
    main() 