#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래 전략 인터페이스 테스트
키움 API와 연동된 자동매매 전략을 테스트합니다.
"""

import sys
import time
import threading
from PyQt5.QtWidgets import QApplication
from kiwoom_api import KiwoomAPI
from trading_strategy import (
    StrategyManager, StrategyType, SignalType, TradingSignal,
    MovingAverageStrategy, RSIStrategy, create_strategy
)
from loguru import logger

class TradingStrategyTester:
    """거래 전략 테스터 클래스"""
    
    def __init__(self):
        self.kiwoom = None
        self.strategy_manager = None
        self.test_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        self.signal_count = 0
        self.start_time = None
        
    def setup_kiwoom(self):
        """키움 API 설정"""
        app = QApplication(sys.argv)
        self.kiwoom = KiwoomAPI()
        
        # 로그인 콜백 설정
        def on_login(status):
            if status:
                logger.info("✅ 로그인 성공")
                self.setup_strategy_manager()
                self.run_strategy_tests()
            else:
                logger.error("❌ 로그인 실패")
        
        self.kiwoom.set_login_callback(on_login)
        
        # 실시간 데이터 콜백 설정
        def on_real_data(code, data):
            logger.debug(f"실시간 데이터: {code} - {data.get('current_price', 0):,}원")
        
        self.kiwoom.set_real_data_callback(on_real_data)
        
        return app
    
    def setup_strategy_manager(self):
        """전략 매니저 설정"""
        self.strategy_manager = StrategyManager(self.kiwoom)
        
        # 전략 실행 콜백 설정
        def on_signal_executed(signal: TradingSignal):
            self.signal_count += 1
            logger.info(f"📊 신호 실행: {signal.code} - {signal.signal_type.value} - "
                       f"{signal.price:,}원 - 신뢰도: {signal.confidence:.2f}")
        
        self.strategy_manager.set_callback(on_signal_executed)
        
        # 실행 설정
        self.strategy_manager.update_execution_config(
            auto_execute=False,  # 테스트 중에는 자동 실행 비활성화
            min_confidence=0.5,
            max_position_size=5,
            check_interval=2.0
        )
    
    def run_strategy_tests(self):
        """전략 테스트 실행"""
        logger.info("🧪 거래 전략 인터페이스 테스트 시작")
        self.start_time = time.time()
        
        try:
            # 1. 전략 생성 테스트
            self.test_strategy_creation()
            
            # 2. 전략 추가/제거 테스트
            self.test_strategy_management()
            
            # 3. 전략 활성화/비활성화 테스트
            self.test_strategy_activation()
            
            # 4. 실시간 데이터 구독 테스트
            self.test_real_data_subscription()
            
            # 5. 전략 실행 테스트
            self.test_strategy_execution()
            
            # 6. 신호 생성 테스트
            self.test_signal_generation()
            
            # 7. 성능 모니터링 테스트
            self.test_performance_monitoring()
            
            # 8. 정리 테스트
            self.test_cleanup()
            
        except Exception as e:
            logger.error(f"❌ 전략 테스트 오류: {e}")
    
    def test_strategy_creation(self):
        """전략 생성 테스트"""
        logger.info("1️⃣ 전략 생성 테스트")
        
        # 팩토리 함수로 전략 생성
        ma_strategy = create_strategy(
            StrategyType.MOVING_AVERAGE,
            short_period=5,
            long_period=20
        )
        logger.info(f"이동평균 전략 생성: {ma_strategy.name}")
        
        rsi_strategy = create_strategy(
            StrategyType.RSI,
            period=14,
            oversold=30,
            overbought=70
        )
        logger.info(f"RSI 전략 생성: {rsi_strategy.name}")
        
        # 직접 생성
        custom_ma = MovingAverageStrategy(short_period=3, long_period=10)
        custom_ma.name = "커스텀 이동평균"
        logger.info(f"커스텀 전략 생성: {custom_ma.name}")
        
        logger.info("✅ 전략 생성 테스트 완료")
    
    def test_strategy_management(self):
        """전략 관리 테스트"""
        logger.info("2️⃣ 전략 관리 테스트")
        
        # 전략 추가
        ma_strategy = MovingAverageStrategy(short_period=5, long_period=20)
        rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        self.strategy_manager.add_strategy(ma_strategy)
        self.strategy_manager.add_strategy(rsi_strategy)
        
        # 전략 목록 확인
        strategies = self.strategy_manager.strategies
        logger.info(f"등록된 전략: {list(strategies.keys())}")
        
        # 전략 제거
        self.strategy_manager.remove_strategy("RSI 전략")
        logger.info(f"전략 제거 후: {list(self.strategy_manager.strategies.keys())}")
        
        logger.info("✅ 전략 관리 테스트 완료")
    
    def test_strategy_activation(self):
        """전략 활성화/비활성화 테스트"""
        logger.info("3️⃣ 전략 활성화/비활성화 테스트")
        
        # 전략 추가
        ma_strategy = MovingAverageStrategy(short_period=5, long_period=20)
        rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        self.strategy_manager.add_strategy(ma_strategy)
        self.strategy_manager.add_strategy(rsi_strategy)
        
        # 활성화
        self.strategy_manager.activate_strategy("이동평균 전략")
        self.strategy_manager.activate_strategy("RSI 전략")
        
        # 상태 확인
        for name, strategy in self.strategy_manager.strategies.items():
            logger.info(f"전략 상태: {name} - 활성화: {strategy.is_active}")
        
        # 비활성화
        self.strategy_manager.deactivate_strategy("RSI 전략")
        
        logger.info("✅ 전략 활성화/비활성화 테스트 완료")
    
    def test_real_data_subscription(self):
        """실시간 데이터 구독 테스트"""
        logger.info("4️⃣ 실시간 데이터 구독 테스트")
        
        for code in self.test_codes:
            result = self.kiwoom.subscribe_real_data(code)
            if result:
                logger.info(f"실시간 데이터 구독 성공: {code}")
            else:
                logger.error(f"실시간 데이터 구독 실패: {code}")
        
        # 구독 상태 확인
        subscribed_codes = self.kiwoom.real_data_codes
        logger.info(f"구독 중인 종목: {subscribed_codes}")
        
        logger.info("✅ 실시간 데이터 구독 테스트 완료")
    
    def test_strategy_execution(self):
        """전략 실행 테스트"""
        logger.info("5️⃣ 전략 실행 테스트")
        
        # 전략 매니저 시작
        self.strategy_manager.start()
        logger.info("전략 매니저 시작됨")
        
        # 10초간 실행
        logger.info("10초간 전략 실행 중...")
        time.sleep(10)
        
        # 전략 매니저 중지
        self.strategy_manager.stop()
        logger.info("전략 매니저 중지됨")
        
        logger.info("✅ 전략 실행 테스트 완료")
    
    def test_signal_generation(self):
        """신호 생성 테스트"""
        logger.info("6️⃣ 신호 생성 테스트")
        
        # 테스트 데이터로 신호 생성
        test_data = {
            'code': '005930',
            'current_price': 50000,
            'volume': 1000,
            'change': 500,
            'change_rate': 1.0
        }
        
        # 이동평균 전략으로 신호 생성
        ma_strategy = MovingAverageStrategy(short_period=3, long_period=5)
        
        # 가격 히스토리 시뮬레이션
        prices = [48000, 49000, 50000, 51000, 52000, 53000, 54000, 55000, 56000, 57000]
        for price in prices:
            test_data['current_price'] = price
            signal = ma_strategy.generate_signal(test_data)
            if signal:
                logger.info(f"신호 생성: {signal.signal_type.value} - {signal.price:,}원 - {signal.reason}")
        
        # RSI 전략으로 신호 생성
        rsi_strategy = RSIStrategy(period=5, oversold=30, overbought=70)
        
        # RSI 테스트 데이터
        rsi_prices = [50000, 49000, 48000, 47000, 46000, 45000, 44000, 43000, 42000, 41000]
        for price in rsi_prices:
            test_data['current_price'] = price
            signal = rsi_strategy.generate_signal(test_data)
            if signal:
                logger.info(f"RSI 신호: {signal.signal_type.value} - {signal.price:,}원 - {signal.reason}")
        
        logger.info("✅ 신호 생성 테스트 완료")
    
    def test_performance_monitoring(self):
        """성능 모니터링 테스트"""
        logger.info("7️⃣ 성능 모니터링 테스트")
        
        # 전략 성능 조회
        performance = self.strategy_manager.get_strategy_performance()
        for name, perf in performance.items():
            logger.info(f"전략 성능 - {name}:")
            logger.info(f"  타입: {perf['type']}")
            logger.info(f"  활성화: {perf['is_active']}")
            logger.info(f"  총 신호: {perf['total_signals']}")
            logger.info(f"  현재 포지션: {perf['current_positions']}")
        
        # 실행 설정 확인
        config = self.strategy_manager.execution_config
        logger.info(f"실행 설정: {config}")
        
        # 설정 변경 테스트
        self.strategy_manager.update_execution_config(
            min_confidence=0.7,
            max_position_size=3
        )
        
        logger.info("✅ 성능 모니터링 테스트 완료")
    
    def test_cleanup(self):
        """정리 테스트"""
        logger.info("8️⃣ 정리 테스트")
        
        # 전략 매니저 중지
        if self.strategy_manager.is_running:
            self.strategy_manager.stop()
        
        # 실시간 데이터 구독 해제
        for code in self.test_codes:
            self.kiwoom.unsubscribe_real_data(code)
        
        # 전략 제거
        strategy_names = list(self.strategy_manager.strategies.keys())
        for name in strategy_names:
            self.strategy_manager.remove_strategy(name)
        
        # 최종 통계
        elapsed = time.time() - self.start_time
        logger.info(f"테스트 완료 - 소요시간: {elapsed:.2f}초, 생성된 신호: {self.signal_count}건")
        
        logger.info("✅ 정리 테스트 완료")
    
    def run_backtest(self):
        """백테스트 실행"""
        logger.info("📊 백테스트 실행")
        
        # 백테스트용 전략 생성
        ma_strategy = MovingAverageStrategy(short_period=5, long_period=20)
        rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        # 시뮬레이션 데이터
        test_prices = [
            50000, 51000, 52000, 53000, 54000, 55000, 56000, 57000, 58000, 59000,
            60000, 59000, 58000, 57000, 56000, 55000, 54000, 53000, 52000, 51000,
            50000, 49000, 48000, 47000, 46000, 45000, 44000, 43000, 42000, 41000
        ]
        
        # 이동평균 백테스트
        logger.info("이동평균 전략 백테스트:")
        ma_signals = []
        for i, price in enumerate(test_prices):
            data = {'code': '005930', 'current_price': price}
            signal = ma_strategy.generate_signal(data)
            if signal:
                ma_signals.append(signal)
                logger.info(f"  {i+1}일차: {signal.signal_type.value} - {signal.price:,}원")
        
        # RSI 백테스트
        logger.info("RSI 전략 백테스트:")
        rsi_signals = []
        for i, price in enumerate(test_prices):
            data = {'code': '005930', 'current_price': price}
            signal = rsi_strategy.generate_signal(data)
            if signal:
                rsi_signals.append(signal)
                logger.info(f"  {i+1}일차: {signal.signal_type.value} - {signal.price:,}원")
        
        logger.info(f"백테스트 완료 - 이동평균: {len(ma_signals)}건, RSI: {len(rsi_signals)}건")

def main():
    """메인 함수"""
    # 로그 설정
    logger.add("logs/trading_strategy_test.log", rotation="1 day", retention="7 days")
    
    print("🚀 거래 전략 인터페이스 테스트")
    print("1. 기본 전략 테스트")
    print("2. 백테스트")
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    tester = TradingStrategyTester()
    app = tester.setup_kiwoom()
    
    if choice == "1":
        # 로그인
        logger.info("🔐 로그인 시도 중...")
        tester.kiwoom.login()
    elif choice == "2":
        # 백테스트만 실행
        tester.run_backtest()
        return
    else:
        print("잘못된 선택입니다.")
        return
    
    # 이벤트 루프 실행
    app.exec_()

if __name__ == "__main__":
    main() 