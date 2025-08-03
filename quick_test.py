#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트
"""

print("=== 시스템 테스트 시작 ===")

try:
    # 기본 모듈 import 테스트
    print("1. 기본 모듈 import 테스트...")
    import numpy as np
    import pandas as pd
    from datetime import datetime
    print("   ✅ 기본 모듈 import 성공")
    
    # 향상된 리스크 관리 테스트
    print("2. 향상된 리스크 관리 테스트...")
    from enhanced_risk_management import EnhancedRiskManager, RiskLevel, MarketVolatility
    
    risk_manager = EnhancedRiskManager()
    
    # 간단한 손절/익절 계산 테스트
    stop_loss, take_profit, risk_info = risk_manager.calculate_stop_loss_and_take_profit(
        current_price=68900,
        signal_strength='strong_buy',
        confidence_score=0.8,
        volatility=0.02,
        market_condition='bull_market',
        stock_volatility=0.025
    )
    
    print(f"   ✅ 손절가: {stop_loss:,.0f}원")
    print(f"   ✅ 익절가: {take_profit:,.0f}원")
    print(f"   ✅ 위험도: {risk_info.get('risk_level', 'N/A')}")
    
    # 포지션 크기 계산 테스트
    position_size = risk_manager.calculate_position_size(
        available_capital=10000000,
        risk_level=RiskLevel.LOW,
        confidence_score=0.8,
        stock_volatility=0.025
    )
    
    print(f"   ✅ 포지션 크기: {position_size:,.0f}원")
    
    print("3. 통합 분석기 import 테스트...")
    from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer, SignalStrength, MarketCondition
    print("   ✅ 통합 분석기 import 성공")
    
    print("4. 웹 서버 import 테스트...")
    from integrated_trend_stock_server import IntegratedTrendStockServer
    print("   ✅ 웹 서버 import 성공")
    
    print("\n=== 모든 테스트 성공! ===")
    print("시스템이 정상적으로 작동합니다.")
    
except Exception as e:
    print(f"❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc() 