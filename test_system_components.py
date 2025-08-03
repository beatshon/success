#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 컴포넌트 개별 테스트
"""

def test_enhanced_risk_management():
    """향상된 리스크 관리 테스트"""
    print("=== 향상된 리스크 관리 테스트 ===")
    
    try:
        from enhanced_risk_management import EnhancedRiskManager, RiskLevel, MarketVolatility
        
        risk_manager = EnhancedRiskManager()
        
        # 테스트 케이스
        test_cases = [
            {
                'name': '삼성전자 (강력 매수)',
                'current_price': 68900,
                'signal_strength': 'strong_buy',
                'confidence_score': 0.8,
                'volatility': 0.02,
                'market_condition': 'bull_market',
                'stock_volatility': 0.025
            },
            {
                'name': 'SK하이닉스 (매도)',
                'current_price': 258000,
                'signal_strength': 'sell',
                'confidence_score': 0.6,
                'volatility': 0.03,
                'market_condition': 'volatile',
                'stock_volatility': 0.035
            }
        ]
        
        for case in test_cases:
            print(f"\n{case['name']}:")
            
            # 손절/익절 계산
            stop_loss, take_profit, risk_info = risk_manager.calculate_stop_loss_and_take_profit(
                case['current_price'],
                case['signal_strength'],
                case['confidence_score'],
                case['volatility'],
                case['market_condition'],
                case['stock_volatility']
            )
            
            print(f"  현재가: {case['current_price']:,}원")
            print(f"  손절가: {stop_loss:,.0f}원")
            print(f"  익절가: {take_profit:,.0f}원")
            print(f"  위험도: {risk_info.get('risk_level', 'N/A')}")
            print(f"  시장 변동성: {risk_info.get('market_volatility', 'N/A')}")
            
            # 포지션 크기 계산
            risk_level = RiskLevel(risk_info.get('risk_level', 'medium'))
            position_size = risk_manager.calculate_position_size(
                10000000,  # 1000만원
                risk_level,
                case['confidence_score'],
                case['stock_volatility']
            )
            
            print(f"  포지션 크기: {position_size:,.0f}원")
        
        print("\n✅ 향상된 리스크 관리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 향상된 리스크 관리 테스트 실패: {e}")
        return False

def test_integrated_analyzer():
    """통합 분석기 테스트"""
    print("\n=== 통합 분석기 테스트 ===")
    
    try:
        from integrated_trend_stock_analyzer import IntegratedTrendStockAnalyzer, SignalStrength, MarketCondition
        
        # 분석기 초기화
        analyzer = IntegratedTrendStockAnalyzer()
        
        # 가상 데이터 설정
        virtual_stock_data = {
            '005930': {
                'name': '삼성전자',
                'current_price': 68900,
                'price_change_percent': -1.85,
                'volume': 1000000
            }
        }
        
        virtual_trend_data = {
            '005930': {
                'value': 75.5,
                'momentum': 0.3,
                'sentiment_score': 0.6
            }
        }
        
        # 분석기에 가상 데이터 설정
        analyzer.stock_api.cache = virtual_stock_data
        
        # 상관관계 분석 테스트
        stock_code = '005930'
        stock_data = virtual_stock_data[stock_code]
        trend_data = virtual_trend_data[stock_code]
        
        correlation = analyzer.analyze_stock_trend_correlation(
            stock_code, stock_data, trend_data
        )
        
        print(f"상관관계 분석 결과:")
        print(f"  신호 강도: {correlation.get('signal_strength', 'N/A')}")
        print(f"  상관관계 점수: {correlation.get('correlation_score', 0):.3f}")
        print(f"  신뢰도: {correlation.get('confidence_score', 0):.3f}")
        print(f"  투자 근거: {', '.join(correlation.get('reasoning', []))}")
        
        # 향상된 리스크 관리 테스트
        enhanced_risk = analyzer._calculate_enhanced_risk_management(
            stock_data, correlation
        )
        
        if enhanced_risk:
            print(f"향상된 리스크 관리 결과:")
            print(f"  손절가: {enhanced_risk.get('stop_loss', 0):,.0f}원")
            print(f"  익절가: {enhanced_risk.get('take_profit', 0):,.0f}원")
            print(f"  포지션 크기: {enhanced_risk.get('position_size', 0):,.0f}원")
            print(f"  위험도: {enhanced_risk.get('risk_level', 'N/A')}")
        
        print("\n✅ 통합 분석기 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 통합 분석기 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_server():
    """웹 서버 테스트"""
    print("\n=== 웹 서버 테스트 ===")
    
    try:
        from integrated_trend_stock_server import IntegratedTrendStockServer
        
        # 서버 인스턴스 생성 (실제 시작하지 않음)
        server = IntegratedTrendStockServer(port=8086)
        
        print("서버 인스턴스 생성 성공")
        print("라우트 설정 확인:")
        
        # 라우트 확인
        routes = []
        for rule in server.app.url_map.iter_rules():
            routes.append(f"  {rule.rule} -> {rule.endpoint}")
        
        for route in routes[:10]:  # 처음 10개만 표시
            print(route)
        
        print("\n✅ 웹 서버 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 웹 서버 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 시스템 컴포넌트 테스트 시작")
    
    results = []
    
    # 각 컴포넌트 테스트
    results.append(test_enhanced_risk_management())
    results.append(test_integrated_analyzer())
    results.append(test_web_server())
    
    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)
    
    test_names = [
        "향상된 리스크 관리",
        "통합 분석기", 
        "웹 서버"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n전체 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다!")
        print("시스템이 정상적으로 작동합니다.")
    else:
        print("⚠️  일부 테스트에 실패했습니다.")
        print("문제를 해결한 후 다시 테스트해주세요.")

if __name__ == "__main__":
    main() 