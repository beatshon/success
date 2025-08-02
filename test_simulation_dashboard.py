#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_simulation_dashboard():
    """시뮬레이션 대시보드 API를 테스트합니다."""
    
    base_url = "http://localhost:8083"
    
    # 1. 메인 페이지 테스트
    try:
        response = requests.get(f"{base_url}/")
        print(f"메인 페이지 상태: {response.status_code}")
    except Exception as e:
        print(f"메인 페이지 접속 실패: {e}")
        return
    
    # 2. 시뮬레이션 데이터 API 테스트
    try:
        response = requests.get(f"{base_url}/api/simulation-data")
        if response.status_code == 200:
            data = response.json()
            print("✅ 시뮬레이션 데이터 API 성공")
            print(f"   - 마지막 업데이트: {data.get('last_updated', 'N/A')}")
            if 'summary' in data:
                summary = data['summary']
                print(f"   - 총 수익률: {summary.get('total_return', 'N/A')}")
                print(f"   - 승률: {summary.get('win_rate', 'N/A')}")
        else:
            print(f"❌ 시뮬레이션 데이터 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시뮬레이션 데이터 API 오류: {e}")
    
    # 3. 차트 데이터 API 테스트
    chart_types = ['portfolio_value', 'returns_distribution', 'drawdown_analysis', 'trade_analysis']
    
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
    
    # 4. 거래 상세 데이터 API 테스트
    try:
        response = requests.get(f"{base_url}/api/trade-details")
        if response.status_code == 200:
            data = response.json()
            print("✅ 거래 상세 데이터 API 성공")
            if 'trades' in data:
                print(f"   - 총 거래 수: {len(data['trades'])}")
        else:
            print(f"❌ 거래 상세 데이터 API 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 거래 상세 데이터 API 오류: {e}")

if __name__ == "__main__":
    print("🔍 시뮬레이션 대시보드 테스트 시작...")
    test_simulation_dashboard()
    print("🏁 테스트 완료") 