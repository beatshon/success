#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_integrated_dashboard():
    """통합 대시보드 API를 테스트합니다."""
    
    base_url = "http://localhost:8080"
    
    # 1. 메인 페이지 테스트
    try:
        response = requests.get(f"{base_url}/")
        print(f"메인 페이지 상태: {response.status_code}")
    except Exception as e:
        print(f"메인 페이지 접속 실패: {e}")
        return
    
    # 2. 개요 데이터 API 테스트
    try:
        response = requests.get(f"{base_url}/api/overview")
        if response.status_code == 200:
            data = response.json()
            print("✅ 개요 데이터 API 성공")
            print(f"   - 마지막 업데이트: {data.get('last_updated', 'N/A')}")
            if 'hybrid_analysis' in data:
                hybrid = data['hybrid_analysis']
                print(f"   - 하이브리드 분석: {hybrid.get('total_stocks', 0)}개 종목")
                print(f"   - 매수 신호: {hybrid.get('buy_signals', 0)}개")
                print(f"   - 매도 신호: {hybrid.get('sell_signals', 0)}개")
                print(f"   - 관망 신호: {hybrid.get('hold_signals', 0)}개")
            if 'simulation' in data:
                sim = data['simulation']
                print(f"   - 시뮬레이션 수익률: {sim.get('total_return', 0)}%")
                print(f"   - 승률: {sim.get('win_rate', 0)}%")
                print(f"   - 총 거래 수: {sim.get('total_trades', 0)}건")
                print(f"   - 최대 낙폭: {sim.get('max_drawdown', 0)}%")
                print(f"   - 샤프 비율: {sim.get('sharpe_ratio', 0)}")
        else:
            print(f"❌ 개요 데이터 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 개요 데이터 API 오류: {e}")
    
    # 3. 빠른 통계 API 테스트
    try:
        response = requests.get(f"{base_url}/api/quick-stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ 빠른 통계 API 성공")
            if 'top_performers' in data:
                print(f"   - 상위 성과 종목: {len(data['top_performers'])}개")
        else:
            print(f"❌ 빠른 통계 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 빠른 통계 API 오류: {e}")
    
    # 4. 최근 활동 API 테스트
    try:
        response = requests.get(f"{base_url}/api/recent-activity")
        if response.status_code == 200:
            data = response.json()
            print("✅ 최근 활동 API 성공")
            if 'activities' in data:
                print(f"   - 최근 활동: {len(data['activities'])}개")
        else:
            print(f"❌ 최근 활동 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 최근 활동 API 오류: {e}")
    
    # 5. 차트 데이터 API 테스트
    chart_types = ['performance-trend', 'signal-distribution', 'portfolio-growth']
    
    for chart_type in chart_types:
        try:
            response = requests.get(f"{base_url}/api/chart-data/{chart_type}")
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    print(f"✅ {chart_type} 차트 API 성공")
                else:
                    print(f"⚠️ {chart_type} 차트 API 오류: {data['error']}")
            else:
                print(f"❌ {chart_type} 차트 API 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ {chart_type} 차트 API 오류: {e}")
    
    # 6. 시스템 상태 API 테스트
    try:
        response = requests.get(f"{base_url}/api/system-status")
        if response.status_code == 200:
            data = response.json()
            print("✅ 시스템 상태 API 성공")
            if 'hybrid_data' in data:
                print(f"   - 하이브리드 데이터: {'사용 가능' if data['hybrid_data']['available'] else '사용 불가'}")
            if 'simulation_data' in data:
                print(f"   - 시뮬레이션 데이터: {'사용 가능' if data['simulation_data']['available'] else '사용 불가'}")
        else:
            print(f"❌ 시스템 상태 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 상태 API 오류: {e}")

if __name__ == "__main__":
    print("🔍 통합 대시보드 테스트 시작...")
    test_integrated_dashboard()
    print("🏁 테스트 완료") 