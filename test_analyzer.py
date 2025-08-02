#!/usr/bin/env python3
"""
네이버 트렌드 분석기 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from naver_trend_analyzer import NaverTrendAnalyzer
import json

def test_analyzer():
    """분석기 테스트"""
    try:
        print("네이버 트렌드 분석기 테스트 시작...")
        
        # 분석기 초기화
        analyzer = NaverTrendAnalyzer()
        print("✓ 분석기 초기화 완료")
        
        # 가상 데이터 생성
        analyzer._generate_virtual_trend_data()
        print(f"✓ 가상 데이터 생성 완료: {len(analyzer.trend_data)}개 키워드")
        
        # 트렌딩 키워드 테스트
        trending_keywords = analyzer.get_trending_keywords()
        print(f"✓ 트렌딩 키워드: {len(trending_keywords)}개")
        for kw in trending_keywords[:5]:
            print(f"  - {kw['keyword']}: {kw['change_rate']:.2%}")
        
        # 투자 신호 테스트
        signals = analyzer.get_investment_signals('005930')
        print(f"✓ 투자 신호: {signals['overall_signal']} (신뢰도: {signals['confidence']:.2f})")
        
        # 트렌드 요약 테스트
        summary = analyzer.get_trend_summary()
        print(f"✓ 트렌드 요약: {summary['total_keywords']}개 키워드, {summary['active_trends']}개 활성 트렌드")
        
        print("모든 테스트 완료!")
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_analyzer() 