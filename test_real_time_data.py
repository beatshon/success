#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 데이터 수집 시스템 테스트 스크립트
"""

import sys
import time
import requests
import json
from datetime import datetime
from loguru import logger

def test_api_connection(base_url: str = "http://localhost:8083") -> bool:
    """API 서버 연결 테스트"""
    print("🔗 API 서버 연결 테스트...")
    
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 서버 연결 성공")
            print(f"   서버 상태: {'실행 중' if data.get('server_running') else '대기 중'}")
            print(f"   수집기 상태: {'실행 중' if data.get('collector_running') else '대기 중'}")
            return True
        else:
            print(f"❌ API 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ API 서버 연결 실패: {base_url}")
        print("   서버가 실행 중인지 확인해주세요.")
        return False
    except Exception as e:
        print(f"❌ API 연결 테스트 오류: {e}")
        return False

def test_data_collection(base_url: str = "http://localhost:8083") -> bool:
    """데이터 수집 테스트"""
    print("\n📊 데이터 수집 테스트...")
    
    try:
        # 수집 시작
        print("   데이터 수집 시작...")
        response = requests.post(f"{base_url}/api/start", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', '수집 시작됨')}")
        else:
            print(f"❌ 수집 시작 실패: {response.status_code}")
            return False
        
        # 잠시 대기
        print("   데이터 수집 대기 중... (10초)")
        time.sleep(10)
        
        # 데이터 조회
        print("   실시간 데이터 조회...")
        response = requests.get(f"{base_url}/api/data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_count = data.get('count', 0)
            print(f"✅ {stock_count}개 종목 데이터 수신")
            
            if stock_count > 0:
                # 첫 번째 종목 데이터 출력
                first_stock = data['data'][0]
                print(f"   샘플 데이터: {first_stock['code']} {first_stock['name']}")
                print(f"   현재가: {first_stock['current_price']:,}원 ({first_stock['change_rate']:+.2f}%)")
            
            return True
        else:
            print(f"❌ 데이터 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 데이터 수집 테스트 오류: {e}")
        return False

def test_market_analysis(base_url: str = "http://localhost:8083") -> bool:
    """시장 분석 테스트"""
    print("\n📈 시장 분석 테스트...")
    
    try:
        # 시장 추세 분석
        print("   시장 추세 분석...")
        response = requests.get(f"{base_url}/api/analysis/market-trend", timeout=10)
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', {})
            
            print(f"✅ 시장 추세 분석 완료")
            print(f"   상승 종목: {analysis.get('up_count', 0)}개")
            print(f"   하락 종목: {analysis.get('down_count', 0)}개")
            print(f"   보합 종목: {analysis.get('flat_count', 0)}개")
            print(f"   평균 등락률: {analysis.get('avg_change_rate', 0):+.2f}%")
            print(f"   시장 심리: {analysis.get('market_sentiment', 'unknown')}")
        else:
            print(f"❌ 시장 추세 분석 실패: {response.status_code}")
            return False
        
        # 급등/급락 종목 분석
        print("   급등/급락 종목 분석...")
        response = requests.get(f"{base_url}/api/analysis/hot-stocks?min_change_rate=2.0", timeout=10)
        if response.status_code == 200:
            data = response.json()
            hot_stocks = data.get('hot_stocks', [])
            
            print(f"✅ 급등/급락 종목 분석 완료")
            print(f"   급등/급락 종목: {len(hot_stocks)}개")
            
            if hot_stocks:
                print("   상위 3개 종목:")
                for i, stock in enumerate(hot_stocks[:3], 1):
                    print(f"     {i}. {stock['code']} {stock['name']}: {stock['change_rate']:+.2f}%")
        else:
            print(f"❌ 급등/급락 종목 분석 실패: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 시장 분석 테스트 오류: {e}")
        return False

def test_stock_subscription(base_url: str = "http://localhost:8083") -> bool:
    """종목 구독 테스트"""
    print("\n📡 종목 구독 테스트...")
    
    try:
        # 테스트 종목 구독
        test_codes = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
        print(f"   종목 구독: {', '.join(test_codes)}")
        
        response = requests.post(
            f"{base_url}/api/subscribe",
            json={'codes': test_codes},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', '구독 완료')}")
            
            # 잠시 대기 후 상태 확인
            time.sleep(5)
            
            # 상태 조회
            response = requests.get(f"{base_url}/api/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                collector_stats = data.get('collector_stats', {})
                subscribed_count = collector_stats.get('subscribed_count', 0)
                print(f"   현재 구독 종목 수: {subscribed_count}개")
            
            return True
        else:
            print(f"❌ 종목 구독 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 종목 구독 테스트 오류: {e}")
        return False

def test_data_export(base_url: str = "http://localhost:8083") -> bool:
    """데이터 내보내기 테스트"""
    print("\n💾 데이터 내보내기 테스트...")
    
    try:
        # CSV 내보내기
        print("   CSV 형식으로 내보내기...")
        response = requests.get(f"{base_url}/api/export?format=csv", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            filename = data.get('filename', 'unknown')
            print(f"✅ 데이터 내보내기 완료: {filename}")
            return True
        else:
            print(f"❌ 데이터 내보내기 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 데이터 내보내기 테스트 오류: {e}")
        return False

def test_performance_monitoring(base_url: str = "http://localhost:8083") -> bool:
    """성능 모니터링 테스트"""
    print("\n⚡ 성능 모니터링 테스트...")
    
    try:
        # 상세 통계 조회
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            collector_stats = data.get('collector_stats', {})
            server_stats = data.get('server_stats', {})
            
            print(f"✅ 성능 통계 조회 완료")
            print(f"   수신 데이터: {collector_stats.get('data_received', 0)}개")
            print(f"   처리 데이터: {collector_stats.get('data_processed', 0)}개")
            print(f"   오류 수: {collector_stats.get('errors', 0)}개")
            print(f"   큐 크기: {collector_stats.get('queue_size', 0)}개")
            print(f"   가동 시간: {server_stats.get('uptime', '00:00:00')}")
            
            # 캐시 통계
            cache_stats = collector_stats.get('cache_stats', {})
            print(f"   캐시 크기: {cache_stats.get('size', 0)}/{cache_stats.get('max_size', 0)}")
            
            return True
        else:
            print(f"❌ 성능 통계 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 성능 모니터링 테스트 오류: {e}")
        return False

def run_comprehensive_test(base_url: str = "http://localhost:8083"):
    """종합 테스트 실행"""
    print("=" * 60)
    print("🚀 실시간 데이터 수집 시스템 종합 테스트")
    print("=" * 60)
    print(f"테스트 대상: {base_url}")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # 1. API 연결 테스트
    test_results.append(("API 연결", test_api_connection(base_url)))
    
    # 2. 종목 구독 테스트
    test_results.append(("종목 구독", test_stock_subscription(base_url)))
    
    # 3. 데이터 수집 테스트
    test_results.append(("데이터 수집", test_data_collection(base_url)))
    
    # 4. 시장 분석 테스트
    test_results.append(("시장 분석", test_market_analysis(base_url)))
    
    # 5. 성능 모니터링 테스트
    test_results.append(("성능 모니터링", test_performance_monitoring(base_url)))
    
    # 6. 데이터 내보내기 테스트
    test_results.append(("데이터 내보내기", test_data_export(base_url)))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    return passed == total

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="실시간 데이터 수집 시스템 테스트")
    parser.add_argument("--url", default="http://localhost:8083", 
                       help="API 서버 URL (기본값: http://localhost:8083)")
    parser.add_argument("--test", choices=["connection", "collection", "analysis", "subscription", "export", "performance", "all"],
                       default="all", help="실행할 테스트 (기본값: all)")
    
    args = parser.parse_args()
    
    try:
        if args.test == "all":
            success = run_comprehensive_test(args.url)
        elif args.test == "connection":
            success = test_api_connection(args.url)
        elif args.test == "collection":
            success = test_data_collection(args.url)
        elif args.test == "analysis":
            success = test_market_analysis(args.url)
        elif args.test == "subscription":
            success = test_stock_subscription(args.url)
        elif args.test == "export":
            success = test_data_export(args.url)
        elif args.test == "performance":
            success = test_performance_monitoring(args.url)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"테스트 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 