#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 트렌드-주식 분석기 빠른 테스트
"""

import asyncio
import time
from datetime import datetime
from loguru import logger

# 프로젝트 모듈 import
from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer

async def quick_test():
    """빠른 테스트"""
    try:
        logger.info("=== 통합 트렌드-주식 분석기 빠른 테스트 시작 ===")
        
        # 분석기 초기화
        logger.info("분석기 초기화 중...")
        analyzer = IntegratedTrendStockAnalyzer()
        
        # 가상 데이터로 빠른 테스트
        logger.info("가상 데이터로 신호 생성 테스트...")
        
        # 가상 주식 데이터 생성
        virtual_stock_data = {
            '005930': {
                'name': '삼성전자',
                'current_price': 68900,
                'price_change_percent': -1.85,
                'volume': 1000000
            },
            '000660': {
                'name': 'SK하이닉스',
                'current_price': 258000,
                'price_change_percent': -3.01,
                'volume': 500000
            },
            '035420': {
                'name': '네이버',
                'current_price': 225000,
                'price_change_percent': -3.23,
                'volume': 300000
            }
        }
        
        # 가상 트렌드 데이터 생성
        virtual_trend_data = {
            '005930': {
                'value': 75.5,
                'momentum': 0.3,
                'sentiment_score': 0.6
            },
            '000660': {
                'value': 45.2,
                'momentum': -0.2,
                'sentiment_score': -0.3
            },
            '035420': {
                'value': 82.1,
                'momentum': 0.5,
                'sentiment_score': 0.7
            }
        }
        
        # 분석기에 가상 데이터 설정
        analyzer.stock_api.cache = virtual_stock_data
        
        # 신호 생성 테스트
        logger.info("신호 생성 테스트...")
        for stock_code in ['005930', '000660', '035420']:
            stock_data = virtual_stock_data.get(stock_code, {})
            trend_data = virtual_trend_data.get(stock_code, {})
            
            if stock_data and trend_data:
                correlation = analyzer.analyze_stock_trend_correlation(
                    stock_code, stock_data, trend_data
                )
                
                if correlation:
                    logger.info(f"{stock_data.get('name', stock_code)}:")
                    logger.info(f"  - 신호 강도: {correlation.get('signal_strength', 'N/A')}")
                    logger.info(f"  - 상관관계 점수: {correlation.get('correlation_score', 0):.3f}")
                    logger.info(f"  - 신뢰도: {correlation.get('confidence_score', 0):.3f}")
                    logger.info(f"  - 투자 근거: {', '.join(correlation.get('reasoning', []))}")
                    logger.info("")
        
        # 분석 요약 테스트
        logger.info("분석 요약 테스트...")
        summary = analyzer.get_analysis_summary()
        logger.info(f"분석 요약: {summary}")
        
        logger.info("=== 빠른 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"빠른 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test()) 