#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 자동매매 시스템 실행 스크립트
키움 API 연결 테스트부터 실제 자동매매까지 모든 기능을 테스트합니다.
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import argparse

# 자동매매 시스템 모듈들
from integrated_auto_trader import IntegratedAutoTrader, TradeConfig, TradingMode, RiskLevel
from test_kiwoom_connection import KiwoomConnectionTester
from trading_strategy import create_default_strategies

class CompleteTradingSystem:
    """완전한 자동매매 시스템"""
    
    def __init__(self):
        self.trader = None
        self.tester = None
        self.is_running = False
        
        # 설정
        self.config = TradeConfig(
            trading_mode=TradingMode.PAPER_TRADING,
            risk_level=RiskLevel.MEDIUM,
            initial_capital=10000000,  # 1천만원
            max_position_size=1000000,  # 100만원
            daily_loss_limit=500000,   # 50만원
            max_positions=5,
            stop_loss_percentage=5.0,
            take_profit_percentage=10.0,
            min_confidence=0.6
        )
        
        logger.info("완전한 자동매매 시스템 초기화 완료")
    
    def run_connection_test(self) -> bool:
        """키움 API 연결 테스트 실행"""
        logger.info("=== 키움 API 연결 테스트 시작 ===")
        
        try:
            self.tester = KiwoomConnectionTester()
            results = self.tester.run_all_tests()
            
            # 테스트 결과 분석
            total_tests = len(results)
            successful_tests = sum(1 for result in results if result.success)
            
            logger.info(f"테스트 결과: {successful_tests}/{total_tests} 성공")
            
            if successful_tests >= total_tests * 0.8:  # 80% 이상 성공
                logger.info("✅ 키움 API 연결 테스트 통과")
                return True
            else:
                logger.error("❌ 키움 API 연결 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"연결 테스트 실행 오류: {e}")
            return False
    
    def run_strategy_test(self) -> bool:
        """트레이딩 전략 테스트 실행"""
        logger.info("=== 트레이딩 전략 테스트 시작 ===")
        
        try:
            # 전략 매니저 생성
            strategy_manager = create_default_strategies()
            
            # 샘플 가격 데이터 생성 (상승 추세)
            sample_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                           111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
            
            # 가격 데이터 업데이트
            for i, price in enumerate(sample_prices):
                strategy_manager.update_price(price, datetime.now() - timedelta(minutes=len(sample_prices)-i))
                time.sleep(0.1)
            
            # 신호 생성
            signals = strategy_manager.generate_signals()
            
            logger.info(f"생성된 신호 수: {len(signals)}")
            for signal in signals:
                logger.info(f"신호: {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
            
            # 성과 요약
            performance = strategy_manager.get_performance_summary()
            logger.info("전략 성과:")
            for name, stats in performance.items():
                logger.info(f"  {name}: {stats}")
            
            logger.info("✅ 트레이딩 전략 테스트 완료")
            return True
            
        except Exception as e:
            logger.error(f"전략 테스트 실행 오류: {e}")
            return False
    
    def run_paper_trading(self, duration_minutes: int = 10) -> bool:
        """페이퍼 트레이딩 실행"""
        logger.info(f"=== 페이퍼 트레이딩 시작 (지속시간: {duration_minutes}분) ===")
        
        try:
            # 자동매매 시스템 초기화
            self.trader = IntegratedAutoTrader(self.config)
            
            if not self.trader.initialize():
                logger.error("자동매매 시스템 초기화 실패")
                return False
            
            # 콜백 함수 설정
            def on_signal(signal):
                logger.info(f"신호 수신: {signal.code} - {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
            
            def on_trade(trade_data):
                logger.info(f"거래 실행: {trade_data}")
            
            self.trader.set_signal_callback(on_signal)
            self.trader.set_trade_callback(on_trade)
            
            # 페이퍼 트레이딩 시작
            if not self.trader.start_trading():
                logger.error("페이퍼 트레이딩 시작 실패")
                return False
            
            self.is_running = True
            start_time = datetime.now()
            
            # 모니터링 루프
            while self.is_running:
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds() / 60
                
                if elapsed >= duration_minutes:
                    logger.info("페이퍼 트레이딩 시간 종료")
                    break
                
                # 상태 출력 (1분마다)
                if int(elapsed) % 1 == 0 and elapsed > 0:
                    status = self.trader.get_status()
                    logger.info(f"상태 업데이트 ({elapsed:.1f}분): {status}")
                
                time.sleep(10)  # 10초 대기
            
            # 페이퍼 트레이딩 중지
            self.trader.stop_trading()
            self.is_running = False
            
            # 최종 결과 출력
            self._print_final_results()
            
            logger.info("✅ 페이퍼 트레이딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"페이퍼 트레이딩 실행 오류: {e}")
            if self.trader:
                self.trader.stop_trading()
            return False
    
    def run_real_trading(self) -> bool:
        """실제 거래 실행 (주의: 실제 돈이 거래됩니다)"""
        logger.warning("=== 실제 거래 실행 (주의: 실제 돈이 거래됩니다) ===")
        
        try:
            # 설정을 실제 거래 모드로 변경
            self.config.trading_mode = TradingMode.REAL_TRADING
            
            # 자동매매 시스템 초기화
            self.trader = IntegratedAutoTrader(self.config)
            
            if not self.trader.initialize():
                logger.error("자동매매 시스템 초기화 실패")
                return False
            
            # 키움 API 연결
            if not self.trader.connect():
                logger.error("키움 API 연결 실패")
                return False
            
            # 로그인
            try:
                with open("config/kiwoom_config.json", "r", encoding="utf-8") as f:
                    kiwoom_config = json.load(f)
                    login_info = kiwoom_config.get("login", {})
                    
                    if not self.trader.login(
                        login_info.get("user_id", ""),
                        login_info.get("password", ""),
                        login_info.get("account", "")
                    ):
                        logger.error("키움 API 로그인 실패")
                        return False
            except FileNotFoundError:
                logger.error("키움 설정 파일을 찾을 수 없습니다.")
                return False
            
            # 실제 거래 시작
            if not self.trader.start_trading():
                logger.error("실제 거래 시작 실패")
                return False
            
            self.is_running = True
            
            # 무한 루프 (Ctrl+C로 종료)
            try:
                while True:
                    time.sleep(60)  # 1분마다 상태 출력
                    
                    status = self.trader.get_status()
                    logger.info(f"실제 거래 상태: {status}")
                    
            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단됨")
            
            # 실제 거래 중지
            self.trader.stop_trading()
            self.is_running = False
            
            # 최종 결과 출력
            self._print_final_results()
            
            logger.info("✅ 실제 거래 완료")
            return True
            
        except Exception as e:
            logger.error(f"실제 거래 실행 오류: {e}")
            if self.trader:
                self.trader.stop_trading()
            return False
    
    def _print_final_results(self):
        """최종 결과 출력"""
        if not self.trader:
            return
        
        logger.info("=== 최종 거래 결과 ===")
        
        # 통계 정보
        stats = self.trader.get_statistics()
        logger.info(f"총 거래 수: {stats.get('total_trades', 0)}")
        logger.info(f"승리 거래: {stats.get('winning_trades', 0)}")
        logger.info(f"패배 거래: {stats.get('losing_trades', 0)}")
        logger.info(f"총 수익: {stats.get('total_profit', 0):,}원")
        logger.info(f"최대 낙폭: {stats.get('max_drawdown', 0):,}원")
        
        # 승률 계산
        if stats.get('total_trades', 0) > 0:
            win_rate = (stats.get('winning_trades', 0) / stats.get('total_trades', 0)) * 100
            logger.info(f"승률: {win_rate:.1f}%")
        
        # 포지션 정보
        positions = self.trader.get_positions()
        logger.info(f"현재 포지션 수: {len(positions)}")
        for code, position in positions.items():
            logger.info(f"  {code}: {position.quantity}주 (평균가: {position.avg_price:,}원, 손익: {position.profit_loss:,}원)")
        
        # 전략 성과
        strategy_performance = self.trader.get_strategy_performance()
        logger.info("전략별 성과:")
        for name, performance in strategy_performance.items():
            logger.info(f"  {name}: {performance}")
    
    def run_comprehensive_test(self) -> bool:
        """종합 테스트 실행"""
        logger.info("=== 종합 테스트 시작 ===")
        
        try:
            # 1. 연결 테스트
            if not self.run_connection_test():
                logger.error("연결 테스트 실패")
                return False
            
            # 2. 전략 테스트
            if not self.run_strategy_test():
                logger.error("전략 테스트 실패")
                return False
            
            # 3. 페이퍼 트레이딩 (5분)
            if not self.run_paper_trading(duration_minutes=5):
                logger.error("페이퍼 트레이딩 실패")
                return False
            
            logger.info("✅ 종합 테스트 완료")
            return True
            
        except Exception as e:
            logger.error(f"종합 테스트 실행 오류: {e}")
            return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="완전한 자동매매 시스템")
    parser.add_argument("--mode", choices=["test", "paper", "real", "comprehensive"], 
                       default="comprehensive", help="실행 모드")
    parser.add_argument("--duration", type=int, default=10, help="페이퍼 트레이딩 지속시간 (분)")
    parser.add_argument("--config", type=str, help="설정 파일 경로")
    
    args = parser.parse_args()
    
    logger.info("완전한 자동매매 시스템 시작")
    logger.info(f"실행 모드: {args.mode}")
    
    # 시스템 생성
    system = CompleteTradingSystem()
    
    # 설정 파일 로드 (있는 경우)
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                # 설정 적용 로직
                logger.info(f"설정 파일 로드: {args.config}")
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패: {e}")
    
    try:
        success = False
        
        if args.mode == "test":
            success = system.run_connection_test()
        elif args.mode == "paper":
            success = system.run_paper_trading(args.duration)
        elif args.mode == "real":
            success = system.run_real_trading()
        elif args.mode == "comprehensive":
            success = system.run_comprehensive_test()
        
        if success:
            logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
            return 0
        else:
            logger.error("❌ 일부 테스트가 실패했습니다.")
            return 1
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        if system.trader:
            system.trader.stop_trading()
        return 0
    except Exception as e:
        logger.error(f"시스템 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 