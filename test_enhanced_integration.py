#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
향상된 리스크 관리가 적용된 통합 분석기 테스트
"""

import asyncio
from datetime import datetime
from loguru import logger

# 프로젝트 모듈 import
from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer

async def test_enhanced_integration():
    """향상된 통합 분석기 테스트"""
    try:
        logger.info("=== 향상된 리스크 관리 통합 분석기 테스트 시작 ===")
        
        # 분석기 초기화
        logger.info("분석기 초기화 중...")
        analyzer = IntegratedTrendStockAnalyzer()
        
        # 가상 데이터 설정
        logger.info("가상 데이터 설정...")
        
        # 가상 주식 데이터
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
        
        # 가상 시장 데이터
        virtual_market_data = {
            'kospi_change_percent': 0.58,
            'market_volatility': 0.02
        }
        
        # 가상 트렌드 데이터
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
        
        # 향상된 리스크 관리 테스트
        logger.info("향상된 리스크 관리 테스트...")
        
        for stock_code in ['005930', '000660', '035420']:
            stock_data = virtual_stock_data.get(stock_code, {})
            trend_data = virtual_trend_data.get(stock_code, {})
            
            if stock_data and trend_data:
                # 상관관계 분석
                correlation = analyzer.analyze_stock_trend_correlation(
                    stock_code, stock_data, trend_data
                )
                
                if correlation:
                    # 향상된 리스크 관리 계산
                    enhanced_risk = analyzer._calculate_enhanced_risk_management(
                        stock_data, correlation, virtual_market_data
                    )
                    
                    logger.info(f"\n{stock_data.get('name', stock_code)} 분석:")
                    logger.info(f"  - 신호 강도: {correlation.get('signal_strength', 'N/A')}")
                    logger.info(f"  - 상관관계 점수: {correlation.get('correlation_score', 0):.3f}")
                    logger.info(f"  - 신뢰도: {correlation.get('confidence_score', 0):.3f}")
                    
                    if enhanced_risk:
                        logger.info(f"  - 위험도: {enhanced_risk.get('risk_level', 'N/A')}")
                        logger.info(f"  - 시장 변동성: {enhanced_risk.get('market_volatility', 'N/A')}")
                        logger.info(f"  - 손절가: {enhanced_risk.get('stop_loss', 0):,.0f}원 ({enhanced_risk.get('stop_loss_percent', 0):.1f}%)")
                        logger.info(f"  - 익절가: {enhanced_risk.get('take_profit', 0):,.0f}원 ({enhanced_risk.get('take_profit_percent', 0):.1f}%)")
                        logger.info(f"  - 포지션 크기: {enhanced_risk.get('position_size', 0):,.0f}원")
                        
                        risk_summary = enhanced_risk.get('risk_summary', {})
                        if risk_summary:
                            logger.info(f"  - 최대 손실: {risk_summary.get('max_loss', 0):,.0f}원")
                            logger.info(f"  - 예상 수익: {risk_summary.get('potential_profit', 0):,.0f}원")
                            logger.info(f"  - 리스크/리워드 비율: {risk_summary.get('risk_reward_ratio', 0):.2f}")
                    
                    logger.info(f"  - 투자 근거: {', '.join(correlation.get('reasoning', []))}")
        
        # 분석 요약 테스트
        logger.info("\n분석 요약 테스트...")
        summary = analyzer.get_analysis_summary()
        logger.info(f"분석 요약: {summary}")
        
        logger.info("\n=== 향상된 리스크 관리 통합 분석기 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_integration()) 