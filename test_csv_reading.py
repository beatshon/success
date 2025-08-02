#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 파일 읽기 테스트 스크립트
"""

import os
import pandas as pd
from datetime import datetime

def test_csv_reading():
    """CSV 파일 읽기 테스트"""
    print("🔍 CSV 파일 읽기 테스트")
    print("="*50)
    
    # 분석 디렉토리 확인
    analysis_dir = "data/news_analysis"
    if not os.path.exists(analysis_dir):
        print(f"❌ 디렉토리가 없습니다: {analysis_dir}")
        return
    
    # 파일 목록 확인
    files = [f for f in os.listdir(analysis_dir) if f.startswith("stock_analysis_")]
    print(f"📁 발견된 분석 파일: {len(files)}개")
    
    for file in files:
        print(f"  - {file}")
    
    if not files:
        print("❌ 분석 파일이 없습니다.")
        return
    
    # 가장 최신 파일 찾기
    latest_file = max(files)
    file_path = os.path.join(analysis_dir, latest_file)
    print(f"\n📄 최신 파일: {latest_file}")
    print(f"📂 전체 경로: {file_path}")
    
    # 파일 내용 확인
    print(f"\n📋 파일 내용 (처음 10줄):")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f, 1):
                if i <= 10:
                    print(f"  {i:2d}: {line.strip()}")
                else:
                    break
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return
    
    # pandas로 읽기 테스트
    print(f"\n🐼 Pandas 읽기 테스트:")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"✅ 성공: {len(df)}행, {len(df.columns)}열")
        print(f"📊 컬럼: {list(df.columns)}")
        print(f"📈 데이터:")
        print(df.head())
    except Exception as e:
        print(f"❌ Pandas 읽기 실패: {e}")
        
        # 다른 인코딩 시도
        for encoding in ['utf-8', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"✅ {encoding} 인코딩으로 성공: {len(df)}행")
                break
            except Exception as e2:
                print(f"❌ {encoding} 인코딩 실패: {e2}")
    
    # 대시보드 로직 테스트
    print(f"\n🎯 대시보드 로직 테스트:")
    try:
        # 대시보드와 동일한 로직
        analysis_results = []
        for _, row in df.iterrows():
            analysis_results.append({
                "stock_code": str(row["stock_code"]),
                "stock_name": str(row["stock_name"]),
                "news_count": int(row["news_count"]),
                "investment_score": float(row["investment_score"]),
                "sentiment_score": float(row["sentiment_score"]),
                "recommendation": str(row["recommendation"]),
                "risk_level": str(row["risk_level"])
            })
        
        print(f"✅ 데이터 변환 성공: {len(analysis_results)}개 종목")
        for result in analysis_results:
            print(f"  - {result['stock_name']} ({result['stock_code']}): {result['investment_score']}점")
            
    except Exception as e:
        print(f"❌ 데이터 변환 실패: {e}")

if __name__ == "__main__":
    test_csv_reading() 