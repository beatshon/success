#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포지션 사이즈 제한 테스트
1종목당 자본의 5~10% 제한 확인
"""

from auto_trading_system import AutoTradingSystem, IntegratedSignal, SignalStrength
from day_trading_config import DayTradingRiskLevel
from datetime import datetime

def test_position_sizing():
    """포지션 사이즈 제한 테스트"""
    print("🧪 포지션 사이즈 제한 테스트")
    print("=" * 60)
    
    try:
        # 자동 매매 시스템 초기화
        trading_system = AutoTradingSystem()
        
        # 테스트 신호 생성
        test_signals = [
            {
                'stock_code': '005930',
                'stock_name': '삼성전자',
                'signal_strength': SignalStrength.BUY,
                'confidence_score': 0.75,
                'trend_impact': 0.8,
                'technical_impact': 0.7,
                'market_impact': 0.6,
                'reasoning': ['반도체 수요 증가', 'AI 트렌드 긍정적'],
                'timestamp': datetime.now(),
                'price_target': 80000,
                'stop_loss': 78000,
                'take_profit': 84000,
                'risk_level': 'low'  # 보수적 (5%)
            },
            {
                'stock_code': '000660',
                'stock_name': 'SK하이닉스',
                'signal_strength': SignalStrength.STRONG_BUY,
                'confidence_score': 0.85,
                'trend_impact': 0.9,
                'technical_impact': 0.8,
                'market_impact': 0.7,
                'reasoning': ['메모리 가격 상승', 'AI 수요 급증'],
                'timestamp': datetime.now(),
                'price_target': 170000,
                'stop_loss': 165750,
                'take_profit': 178500,
                'risk_level': 'medium'  # 중간 (8%)
            },
            {
                'stock_code': '035420',
                'stock_name': '네이버',
                'signal_strength': SignalStrength.BUY,
                'confidence_score': 0.70,
                'trend_impact': 0.6,
                'technical_impact': 0.5,
                'market_impact': 0.4,
                'reasoning': ['AI 경쟁 심화', '수익성 압박'],
                'timestamp': datetime.now(),
                'price_target': 220000,
                'stop_loss': 213400,
                'take_profit': 218900,
                'risk_level': 'high'  # 공격적 (10%)
            }
        ]
        
        print("📊 포지션 사이즈 계산 결과:")
        print("-" * 60)
        
        for signal_data in test_signals:
            # IntegratedSignal 객체 생성
            signal = IntegratedSignal(**signal_data)
            
            # 포지션 크기 계산
            quantity = trading_system._calculate_position_size(signal)
            
            # 투자 금액 계산
            investment_amount = quantity * signal.price_target
            investment_ratio = (investment_amount / 10000000) * 100  # 1000만원 기준
            
            print(f"📈 {signal.stock_name} ({signal.stock_code})")
            print(f"   - 위험도: {signal.risk_level}")
            print(f"   - 목표가: {signal.price_target:,.0f}원")
            print(f"   - 주식 수량: {quantity}주")
            print(f"   - 투자 금액: {investment_amount:,.0f}원")
            print(f"   - 자본 대비 비율: {investment_ratio:.1f}%")
            
            # 제한 확인
            if signal.risk_level == 'low' and investment_ratio <= 5.0:
                print(f"   ✅ 보수적 제한 (5%) 준수")
            elif signal.risk_level == 'medium' and investment_ratio <= 8.0:
                print(f"   ✅ 중간 제한 (8%) 준수")
            elif signal.risk_level == 'high' and investment_ratio <= 10.0:
                print(f"   ✅ 공격적 제한 (10%) 준수")
            else:
                print(f"   ⚠️ 제한 초과!")
            
            print()
        
        print("=" * 60)
        print("📋 포지션 사이즈 제한 요약:")
        print("   - 보수적 (low): 최대 5% (500,000원)")
        print("   - 중간 (medium): 최대 8% (800,000원)")
        print("   - 공격적 (high): 최대 10% (1,000,000원)")
        print("   - 기본 자본: 10,000,000원")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_portfolio_diversification():
    """포트폴리오 분산 테스트"""
    print("\n🌐 포트폴리오 분산 테스트")
    print("=" * 60)
    
    try:
        trading_system = AutoTradingSystem()
        
        # 여러 종목 동시 투자 시나리오
        scenarios = [
            {
                'name': '보수적 포트폴리오',
                'stocks': [
                    ('005930', '삼성전자', 80000, 'low'),
                    ('000660', 'SK하이닉스', 170000, 'low'),
                    ('035420', '네이버', 220000, 'low')
                ]
            },
            {
                'name': '균형 포트폴리오',
                'stocks': [
                    ('005930', '삼성전자', 80000, 'medium'),
                    ('000660', 'SK하이닉스', 170000, 'medium'),
                    ('035420', '네이버', 220000, 'medium')
                ]
            },
            {
                'name': '공격적 포트폴리오',
                'stocks': [
                    ('005930', '삼성전자', 80000, 'high'),
                    ('000660', 'SK하이닉스', 170000, 'high'),
                    ('035420', '네이버', 220000, 'high')
                ]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📊 {scenario['name']}:")
            print("-" * 40)
            
            total_investment = 0
            
            for stock_code, stock_name, price, risk_level in scenario['stocks']:
                # 가상 신호 생성
                signal_data = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'signal_strength': SignalStrength.BUY,
                    'confidence_score': 0.75,
                    'trend_impact': 0.8,
                    'technical_impact': 0.7,
                    'market_impact': 0.6,
                    'reasoning': ['테스트 신호'],
                    'timestamp': datetime.now(),
                    'price_target': price,
                    'stop_loss': price * 0.975,
                    'take_profit': price * 1.05,
                    'risk_level': risk_level
                }
                
                signal = IntegratedSignal(**signal_data)
                quantity = trading_system._calculate_position_size(signal)
                investment = quantity * price
                total_investment += investment
                
                print(f"   {stock_name}: {quantity}주 × {price:,.0f}원 = {investment:,.0f}원")
            
            portfolio_ratio = (total_investment / 10000000) * 100
            print(f"   총 투자: {total_investment:,.0f}원 ({portfolio_ratio:.1f}%)")
            
            if portfolio_ratio <= 30:  # 최대 30% (3종목 × 10%)
                print(f"   ✅ 포트폴리오 분산 적절")
            else:
                print(f"   ⚠️ 포트폴리오 집중도 높음")
        
    except Exception as e:
        print(f"❌ 포트폴리오 테스트 실패: {e}")

if __name__ == "__main__":
    test_position_sizing()
    test_portfolio_diversification() 