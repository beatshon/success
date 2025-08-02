#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하이브리드 트레이딩 성능 분석 및 최적화
"""

import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
import os

def analyze_performance():
    """하이브리드 분석 성능 분석"""
    
    # 최신 분석 데이터 로드
    data_dir = "data/hybrid_analysis"
    files = [f for f in os.listdir(data_dir) if f.startswith('hybrid_analysis_') and f.endswith('.csv')]
    
    if not files:
        logger.error("분석 데이터를 찾을 수 없습니다")
        return
    
    latest_file = max(files)
    file_path = os.path.join(data_dir, latest_file)
    
    df = pd.read_csv(file_path)
    
    print("=" * 60)
    print("🔍 하이브리드 트레이딩 성능 분석")
    print("=" * 60)
    
    # 1. 기본 통계
    print("\n📊 기본 통계:")
    print(f"총 분석 종목: {len(df)}개")
    print(f"평균 종합 점수: {df['combined_score'].mean():.2f}")
    print(f"점수 표준편차: {df['combined_score'].std():.2f}")
    print(f"최고 점수: {df['combined_score'].max():.2f} ({df.loc[df['combined_score'].idxmax(), 'stock_name']})")
    print(f"최저 점수: {df['combined_score'].min():.2f} ({df.loc[df['combined_score'].idxmin(), 'stock_name']})")
    
    # 2. 신호 분포 분석
    print("\n📈 신호 분포:")
    signal_counts = df['final_signal'].value_counts()
    for signal, count in signal_counts.items():
        percentage = (count / len(df)) * 100
        print(f"• {signal}: {count}개 ({percentage:.1f}%)")
    
    # 3. 섹터별 분석
    print("\n🏢 섹터별 분석:")
    sector_analysis = df.groupby('sector').agg({
        'combined_score': ['mean', 'count'],
        'final_signal': lambda x: (x == '매수').sum()
    }).round(2)
    
    for sector in df['sector'].unique():
        sector_data = df[df['sector'] == sector]
        avg_score = sector_data['combined_score'].mean()
        buy_signals = (sector_data['final_signal'] == '매수').sum()
        total_stocks = len(sector_data)
        print(f"• {sector}: 평균점수 {avg_score:.1f}, 매수신호 {buy_signals}/{total_stocks}개")
    
    # 4. 뉴스 vs 기술적 분석 비교
    print("\n📰 뉴스 vs 기술적 분석:")
    news_avg = df['news_score'].mean()
    tech_avg = df['technical_score'].mean()
    print(f"• 뉴스 분석 평균: {news_avg:.1f}")
    print(f"• 기술적 분석 평균: {tech_avg:.1f}")
    print(f"• 뉴스-기술적 차이: {abs(news_avg - tech_avg):.1f}")
    
    # 5. 상위/하위 종목 분석
    print("\n🏆 상위 5개 종목:")
    top_5 = df.nlargest(5, 'combined_score')[['stock_name', 'combined_score', 'final_signal', 'news_score', 'technical_score']]
    for _, row in top_5.iterrows():
        print(f"• {row['stock_name']}: {row['combined_score']:.1f}점 ({row['final_signal']}) - 뉴스:{row['news_score']:.1f}, 기술:{row['technical_score']:.1f}")
    
    print("\n📉 하위 5개 종목:")
    bottom_5 = df.nsmallest(5, 'combined_score')[['stock_name', 'combined_score', 'final_signal', 'news_score', 'technical_score']]
    for _, row in bottom_5.iterrows():
        print(f"• {row['stock_name']}: {row['combined_score']:.1f}점 ({row['final_signal']}) - 뉴스:{row['news_score']:.1f}, 기술:{row['technical_score']:.1f}")
    
    # 6. 최적화 제안
    print("\n🔧 최적화 제안:")
    
    # 신호 임계값 최적화
    current_buy_threshold = 50
    current_sell_threshold = 30
    
    buy_candidates = df[df['combined_score'] >= 45]['final_signal'].value_counts()
    sell_candidates = df[df['combined_score'] <= 35]['final_signal'].value_counts()
    
    print(f"• 현재 매수 임계값: {current_buy_threshold}점")
    print(f"• 현재 매도 임계값: {current_sell_threshold}점")
    
    # 임계값 조정 제안
    if buy_candidates.get('관망', 0) > 3:
        print(f"• 매수 임계값을 45점으로 낮추면 {buy_candidates.get('관망', 0)}개 종목이 추가 매수 신호 생성")
    
    if sell_candidates.get('관망', 0) > 3:
        print(f"• 매도 임계값을 35점으로 높이면 {sell_candidates.get('관망', 0)}개 종목이 추가 매도 신호 생성")
    
    # 가중치 최적화 제안
    news_std = df['news_score'].std()
    tech_std = df['technical_score'].std()
    
    print(f"\n• 뉴스 분석 표준편차: {news_std:.1f}")
    print(f"• 기술적 분석 표준편차: {tech_std:.1f}")
    
    if news_std > tech_std * 1.5:
        print("• 뉴스 분석의 변동성이 크므로 뉴스 가중치를 낮추는 것을 고려")
    elif tech_std > news_std * 1.5:
        print("• 기술적 분석의 변동성이 크므로 기술적 가중치를 낮추는 것을 고려")
    else:
        print("• 뉴스와 기술적 분석의 변동성이 균형적임")
    
    # 7. 리스크 분석
    print("\n⚠️ 리스크 분석:")
    
    # 신뢰도 분석
    low_confidence = df[df['confidence'] < 40]
    if len(low_confidence) > 0:
        print(f"• 신뢰도 40% 미만 종목: {len(low_confidence)}개")
        for _, row in low_confidence.iterrows():
            print(f"  - {row['stock_name']}: {row['confidence']:.1f}%")
    
    # 극단적 점수 분석
    extreme_high = df[df['combined_score'] > 70]
    extreme_low = df[df['combined_score'] < 20]
    
    if len(extreme_high) > 0:
        print(f"• 극단적 고점수 종목: {len(extreme_high)}개 (과매수 가능성)")
    if len(extreme_low) > 0:
        print(f"• 극단적 저점수 종목: {len(extreme_low)}개 (과매도 가능성)")
    
    # 8. 개선 방안
    print("\n🚀 개선 방안:")
    
    # 1) 신호 다양성 개선
    if signal_counts.get('매수', 0) < 3:
        print("• 매수 신호가 부족하므로 임계값 조정 필요")
    if signal_counts.get('매도', 0) < 3:
        print("• 매도 신호가 부족하므로 임계값 조정 필요")
    
    # 2) 섹터 분산 개선
    sector_counts = df['sector'].value_counts()
    if sector_counts.max() > len(df) * 0.4:
        print("• 특정 섹터에 편중되어 있으므로 섹터 분산 필요")
    
    # 3) 점수 분포 개선
    score_std = df['combined_score'].std()
    if score_std < 10:
        print("• 점수 분포가 좁으므로 차별화 개선 필요")
    
    print("\n" + "=" * 60)
    print("✅ 성능 분석 완료")
    print("=" * 60)

if __name__ == "__main__":
    analyze_performance() 