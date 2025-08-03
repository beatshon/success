#!/usr/bin/env python3
"""
투자 관리 시스템 테스트
"""
from investment_manager import InvestmentManager

def test_investment_manager():
    """투자 관리 시스템 테스트"""
    print("💰 투자 관리 시스템 상세 테스트")
    print("=" * 60)
    
    # 투자 관리 시스템 생성
    manager = InvestmentManager()
    
    # 1. 일일 투자 현황 테스트
    print("\n1️⃣ 일일 투자 현황 테스트:")
    daily_status = manager.get_daily_investment_status()
    print(f"  - 날짜: {daily_status['date']}")
    print(f"  - 총 투자: {daily_status['total_invested']:,}원")
    print(f"  - 남은 한도: {daily_status['remaining_limit']:,}원")
    print(f"  - 사용률: {daily_status['limit_used_percent']:.1f}%")
    print(f"  - 투자 가능: {daily_status['can_invest']}")
    
    # 2. 샘플 종목 정보
    sample_stocks = [
        {
            'code': '005930',
            'name': '삼성전자',
            'sector': '전기전자',
            'score': 8.5,
            'strategy': '이동평균 크로스오버',
            'reason': '강한 상승 모멘텀'
        },
        {
            'code': '000660',
            'name': 'SK하이닉스',
            'sector': '전기전자',
            'score': 7.2,
            'strategy': 'RSI 전략',
            'reason': '과매도 구간 반등'
        },
        {
            'code': '035420',
            'name': 'NAVER',
            'sector': '서비스업',
            'score': 6.8,
            'strategy': '볼린저 밴드 전략',
            'reason': '밴드 하단 지지'
        }
    ]
    
    # 3. 투자 가능 여부 테스트
    print("\n2️⃣ 투자 가능 여부 테스트:")
    available_cash = 10000000  # 1천만원
    
    for stock in sample_stocks:
        test_amount = 300000  # 30만원
        can_invest, reason = manager.can_invest_in_stock(
            stock['code'], test_amount, stock
        )
        print(f"  - {stock['name']}({stock['code']}): {can_invest} - {reason}")
        
    # 4. 최적 투자 금액 계산 테스트
    print("\n3️⃣ 최적 투자 금액 계산 테스트:")
    for stock in sample_stocks:
        optimal_amount = manager.calculate_optimal_investment_amount(
            stock['code'], stock, available_cash
        )
        print(f"  - {stock['name']}: {optimal_amount:,}원 (점수: {stock['score']})")
        
    # 5. 투자 기록 테스트
    print("\n4️⃣ 투자 기록 테스트:")
    for i, stock in enumerate(sample_stocks):
        amount = 200000 + (i * 50000)  # 20만원, 25만원, 30만원
        manager.record_investment(stock['code'], amount, stock)
        print(f"  - {stock['name']} 투자 기록: {amount:,}원")
        
    # 6. 포트폴리오 요약 테스트
    print("\n5️⃣ 포트폴리오 요약 테스트:")
    portfolio_summary = manager.get_portfolio_summary()
    print(f"  - 총 투자: {portfolio_summary['total_investment']:,}원")
    print(f"  - 종목 수: {portfolio_summary['stock_count']}개")
    print(f"  - 섹터 수: {portfolio_summary['sector_count']}개")
    print(f"  - 분산 점수: {portfolio_summary['diversification_score']}/100")
    
    print("\n📊 섹터별 배분:")
    for sector, data in portfolio_summary['sector_allocation'].items():
        print(f"  - {sector}: {data['amount']:,}원 ({data['percentage']}%) - {data['stock_count']}개 종목")
        
    print("\n🏆 상위 투자 종목:")
    for stock in portfolio_summary['top_stocks']:
        print(f"  - {stock['name']}({stock['code']}): {stock['amount']:,}원 ({stock['percentage']}%)")
        
    # 7. 투자 추천 테스트
    print("\n6️⃣ 투자 추천 테스트:")
    recommendations = manager.get_investment_recommendations(available_cash)
    if recommendations:
        for rec in recommendations:
            priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
            print(f"  {priority_icon} {rec['message']}")
            print(f"     → {rec['action']}")
    else:
        print("  ✅ 투자 추천사항 없음")
        
    # 8. 투자 리포트 생성 테스트
    print("\n7️⃣ 투자 리포트 생성 테스트:")
    report = manager.generate_investment_report()
    print(report)
    
    print("\n" + "=" * 60)
    print("✅ 투자 관리 시스템 테스트 완료!")

if __name__ == "__main__":
    test_investment_manager() 