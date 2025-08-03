#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매우 간단한 테스트
"""

print("=== 간단한 시스템 테스트 시작 ===")

# 1. 기본 모듈 테스트
print("1. 기본 모듈 테스트...")
try:
    import numpy as np
    import pandas as pd
    print("   ✅ numpy, pandas import 성공")
except Exception as e:
    print(f"   ❌ 기본 모듈 import 실패: {e}")

# 2. 향상된 리스크 관리 테스트
print("2. 향상된 리스크 관리 테스트...")
try:
    from enhanced_risk_management import EnhancedRiskManager
    risk_manager = EnhancedRiskManager()
    print("   ✅ 향상된 리스크 관리자 생성 성공")
    
    # 간단한 계산 테스트
    stop_loss, take_profit, risk_info = risk_manager.calculate_stop_loss_and_take_profit(
        current_price=68900,
        signal_strength='strong_buy',
        confidence_score=0.8,
        volatility=0.02,
        market_condition='bull_market',
        stock_volatility=0.025
    )
    print(f"   ✅ 손절가: {stop_loss:,.0f}원, 익절가: {take_profit:,.0f}원")
    
except Exception as e:
    print(f"   ❌ 향상된 리스크 관리 테스트 실패: {e}")

# 3. 통합 분석기 테스트
print("3. 통합 분석기 테스트...")
try:
    from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer
    analyzer = IntegratedTrendStockAnalyzer()
    print("   ✅ 통합 분석기 생성 성공")
except Exception as e:
    print(f"   ❌ 통합 분석기 테스트 실패: {e}")

# 4. 웹 서버 테스트
print("4. 웹 서버 테스트...")
try:
    from integrated_trend_stock_server import IntegratedTrendStockServer
    server = IntegratedTrendStockServer(port=8086)
    print("   ✅ 웹 서버 생성 성공")
except Exception as e:
    print(f"   ❌ 웹 서버 테스트 실패: {e}")

print("\n=== 테스트 완료 ===")
print("웹 서버를 시작하려면 다음 명령을 실행하세요:")
print("python start_integrated_server.py") 