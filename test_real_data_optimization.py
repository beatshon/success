#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 데이터 처리 최적화 테스트
키움 API의 최적화된 실시간 데이터 처리 기능을 테스트합니다.
"""

import sys
import time
import threading
from PyQt5.QtWidgets import QApplication
from kiwoom_api import KiwoomAPI, RealDataType
from loguru import logger

class RealDataTester:
    """실시간 데이터 테스터 클래스"""
    
    def __init__(self):
        self.kiwoom = None
        self.test_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        self.data_count = 0
        self.start_time = None
        
    def setup_kiwoom(self):
        """키움 API 설정"""
        app = QApplication(sys.argv)
        self.kiwoom = KiwoomAPI()
        
        # 로그인 콜백 설정
        def on_login(status):
            if status:
                logger.info("✅ 로그인 성공")
                self.run_real_data_tests()
            else:
                logger.error("❌ 로그인 실패")
        
        self.kiwoom.set_login_callback(on_login)
        
        # 실시간 데이터 콜백 설정
        def on_real_data(code, data):
            self.data_count += 1
            if self.data_count % 100 == 0:  # 100개마다 로그 출력
                elapsed = time.time() - self.start_time
                rate = self.data_count / elapsed if elapsed > 0 else 0
                logger.info(f"📊 데이터 처리: {self.data_count}건 - {rate:.1f}건/초")
        
        self.kiwoom.set_real_data_callback(on_real_data)
        
        return app
    
    def run_real_data_tests(self):
        """실시간 데이터 테스트 실행"""
        logger.info("🧪 실시간 데이터 최적화 테스트 시작")
        self.start_time = time.time()
        
        try:
            # 1. 설정 테스트
            self.test_configuration()
            
            # 2. 구독 테스트
            self.test_subscription()
            
            # 3. 캐시 테스트
            self.test_cache_functionality()
            
            # 4. 히스토리 테스트
            self.test_history_functionality()
            
            # 5. 통계 테스트
            self.test_statistics()
            
            # 6. 성능 테스트
            self.test_performance()
            
            # 7. 배치 처리 테스트
            self.test_batch_processing()
            
            # 8. 정리 테스트
            self.test_cleanup()
            
        except Exception as e:
            logger.error(f"❌ 테스트 오류: {e}")
    
    def test_configuration(self):
        """설정 테스트"""
        logger.info("1️⃣ 설정 테스트")
        
        # 기본 설정 확인
        config = self.kiwoom.real_data_config
        logger.info(f"기본 설정: {config}")
        
        # 설정 변경 테스트
        self.kiwoom.set_real_data_config(
            cache_ttl=2.0,
            batch_size=20,
            batch_interval=0.05
        )
        
        logger.info("✅ 설정 테스트 완료")
    
    def test_subscription(self):
        """구독 테스트"""
        logger.info("2️⃣ 구독 테스트")
        
        for code in self.test_codes:
            # 구독
            result = self.kiwoom.subscribe_real_data(code)
            if result:
                logger.info(f"구독 성공: {code}")
            else:
                logger.error(f"구독 실패: {code}")
            
            time.sleep(0.1)  # 구독 간격
        
        # 구독 상태 확인
        subscribed_codes = self.kiwoom.real_data_codes
        logger.info(f"구독 중인 종목: {subscribed_codes}")
        
        logger.info("✅ 구독 테스트 완료")
    
    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        logger.info("3️⃣ 캐시 기능 테스트")
        
        # 캐시 조회 테스트
        for code in self.test_codes:
            cache_data = self.kiwoom.get_real_data_cache(code)
            if cache_data:
                logger.info(f"캐시 데이터: {code} - {cache_data.get('current_price', 'N/A')}")
            else:
                logger.info(f"캐시 없음: {code}")
        
        # 전체 캐시 조회
        all_cache = self.kiwoom.get_real_data_cache()
        logger.info(f"전체 캐시 종목 수: {len(all_cache)}")
        
        logger.info("✅ 캐시 기능 테스트 완료")
    
    def test_history_functionality(self):
        """히스토리 기능 테스트"""
        logger.info("4️⃣ 히스토리 기능 테스트")
        
        # 잠시 대기하여 데이터 수집
        time.sleep(2)
        
        for code in self.test_codes:
            history = self.kiwoom.get_real_data_history(code, limit=10)
            logger.info(f"히스토리: {code} - {len(history)}건")
            
            if history:
                latest = history[-1]
                logger.info(f"최신 데이터: {code} - {latest.get('current_price', 'N/A')}")
        
        logger.info("✅ 히스토리 기능 테스트 완료")
    
    def test_statistics(self):
        """통계 기능 테스트"""
        logger.info("5️⃣ 통계 기능 테스트")
        
        # 전체 통계 조회
        all_stats = self.kiwoom.get_real_data_stats()
        logger.info(f"전체 통계: {len(all_stats)}종목")
        
        for code, stats in all_stats.items():
            if stats['update_count'] > 0:
                logger.info(f"통계: {code} - 업데이트: {stats['update_count']}, "
                          f"에러: {stats['error_count']}, "
                          f"평균처리시간: {stats['avg_processing_time']:.4f}초")
        
        logger.info("✅ 통계 기능 테스트 완료")
    
    def test_performance(self):
        """성능 테스트"""
        logger.info("6️⃣ 성능 테스트")
        
        # 10초간 데이터 수집
        start_time = time.time()
        initial_count = self.data_count
        
        logger.info("10초간 데이터 수집 중...")
        time.sleep(10)
        
        end_time = time.time()
        final_count = self.data_count
        elapsed = end_time - start_time
        
        total_data = final_count - initial_count
        data_rate = total_data / elapsed if elapsed > 0 else 0
        
        logger.info(f"성능 결과:")
        logger.info(f"  - 수집 시간: {elapsed:.2f}초")
        logger.info(f"  - 수집 데이터: {total_data}건")
        logger.info(f"  - 처리 속도: {data_rate:.1f}건/초")
        
        # 메모리 사용량 확인
        cache_size = len(self.kiwoom.real_data_cache)
        history_size = sum(len(h) for h in self.kiwoom.real_data_history.values())
        
        logger.info(f"  - 캐시 크기: {cache_size}")
        logger.info(f"  - 히스토리 크기: {history_size}")
        
        logger.info("✅ 성능 테스트 완료")
    
    def test_batch_processing(self):
        """배치 처리 테스트"""
        logger.info("7️⃣ 배치 처리 테스트")
        
        # 배치 설정 변경
        self.kiwoom.set_real_data_config(
            batch_size=5,
            batch_interval=0.2
        )
        
        logger.info("배치 처리 설정 변경 완료")
        time.sleep(2)
        
        logger.info("✅ 배치 처리 테스트 완료")
    
    def test_cleanup(self):
        """정리 테스트"""
        logger.info("8️⃣ 정리 테스트")
        
        # 구독 해제
        for code in self.test_codes:
            result = self.kiwoom.unsubscribe_real_data(code)
            if result:
                logger.info(f"구독 해제 성공: {code}")
            else:
                logger.error(f"구독 해제 실패: {code}")
        
        # 캐시 정리
        self.kiwoom.clear_real_data_cache()
        logger.info("캐시 정리 완료")
        
        # 최종 통계
        final_stats = self.kiwoom.get_real_data_stats()
        logger.info(f"최종 통계: {len(final_stats)}종목")
        
        logger.info("✅ 정리 테스트 완료")
    
    def run_stress_test(self):
        """스트레스 테스트"""
        logger.info("🔥 스트레스 테스트 시작")
        
        # 많은 종목 구독
        stress_codes = [f"00{str(i).zfill(4)}" for i in range(1000, 1010)]
        
        start_time = time.time()
        
        for code in stress_codes:
            self.kiwoom.subscribe_real_data(code)
        
        end_time = time.time()
        logger.info(f"스트레스 테스트 완료: {len(stress_codes)}종목 - {end_time - start_time:.2f}초")
        
        # 정리
        for code in stress_codes:
            self.kiwoom.unsubscribe_real_data(code)

def main():
    """메인 함수"""
    # 로그 설정
    logger.add("logs/real_data_test.log", rotation="1 day", retention="7 days")
    
    print("🚀 실시간 데이터 최적화 테스트")
    print("1. 기본 테스트")
    print("2. 스트레스 테스트")
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    tester = RealDataTester()
    app = tester.setup_kiwoom()
    
    if choice == "1":
        # 로그인
        logger.info("🔐 로그인 시도 중...")
        tester.kiwoom.login()
    elif choice == "2":
        # 로그인 후 스트레스 테스트
        def on_login_stress(status):
            if status:
                logger.info("✅ 로그인 성공")
                tester.run_stress_test()
            else:
                logger.error("❌ 로그인 실패")
        
        tester.kiwoom.set_login_callback(on_login_stress)
        logger.info("🔐 로그인 시도 중...")
        tester.kiwoom.login()
    else:
        print("잘못된 선택입니다.")
        return
    
    # 이벤트 루프 실행
    app.exec_()

if __name__ == "__main__":
    main() 