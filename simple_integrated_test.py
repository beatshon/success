#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 통합 분석 테스트
"""

import numpy as np
from datetime import datetime
from loguru import logger

def simple_correlation_test():
    """간단한 상관관계 분석 테스트"""
    try:
        logger.info("=== 간단한 통합 분석 테스트 시작 ===")
        
        # 테스트 데이터
        test_cases = [
            {
                'name': '삼성전자',
                'price_change': -1.85,
                'trend_value': 75.5,
                'sentiment': 0.6
            },
            {
                'name': 'SK하이닉스',
                'price_change': -3.01,
                'trend_value': 45.2,
                'sentiment': -0.3
            },
            {
                'name': '네이버',
                'price_change': -3.23,
                'trend_value': 82.1,
                'sentiment': 0.7
            }
        ]
        
        for case in test_cases:
            # 상관관계 점수 계산
            price_trend_corr = np.corrcoef([case['price_change']], [case['trend_value']])[0, 1]
            if np.isnan(price_trend_corr):
                price_trend_corr = 0
            
            # 종합 점수 계산
            sentiment_weight = 0.3
            trend_weight = 0.7
            correlation_score = (trend_weight * price_trend_corr + sentiment_weight * case['sentiment'])
            correlation_score = max(-1.0, min(1.0, correlation_score))
            
            # 신호 강도 결정
            score = (correlation_score * 0.4 + case['price_change'] * 0.3 + case['sentiment'] * 0.3)
            
            if score >= 0.7:
                signal = "강력 매수"
            elif score >= 0.3:
                signal = "매수"
            elif score >= -0.3:
                signal = "관망"
            elif score >= -0.7:
                signal = "매도"
            else:
                signal = "강력 매도"
            
            logger.info(f"{case['name']}:")
            logger.info(f"  - 가격 변화: {case['price_change']:.2f}%")
            logger.info(f"  - 트렌드 값: {case['trend_value']:.1f}")
            logger.info(f"  - 감정 점수: {case['sentiment']:.2f}")
            logger.info(f"  - 상관관계 점수: {correlation_score:.3f}")
            logger.info(f"  - 종합 점수: {score:.3f}")
            logger.info(f"  - 투자 신호: {signal}")
            logger.info("")
        
        logger.info("=== 간단한 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")

if __name__ == "__main__":
    simple_correlation_test() 