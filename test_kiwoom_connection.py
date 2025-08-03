#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키움 API 연결 테스트 시스템
실제 키움 API 연결 및 기본 기능 테스트
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
import pandas as pd

# 키움 API 모듈들
from kiwoom_mac_compatible import KiwoomMacAPI
from error_handler import ErrorType, ErrorLevel, handle_error, retry_operation

@dataclass
class TestResult:
    """테스트 결과"""
    test_name: str
    success: bool
    message: str
    duration: float
    timestamp: datetime
    details: Dict = None

class KiwoomConnectionTester:
    """키움 API 연결 테스터"""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url
        self.kiwoom_api = KiwoomMacAPI(server_url)
        self.test_results = []
        self.is_testing = False
        
        # 테스트 설정
        self.test_config = {
            "connection_timeout": 30,
            "login_timeout": 60,
            "data_timeout": 10,
            "retry_count": 3,
            "test_stocks": ["005930", "000660", "035420"],  # 삼성전자, SK하이닉스, NAVER
        }
        
        # 콜백 설정
        self.kiwoom_api.set_login_callback(self._on_login)
        self.kiwoom_api.set_real_data_callback(self._on_real_data)
        self.kiwoom_api.set_order_callback(self._on_order)
        
    def _on_login(self, result: Dict):
        """로그인 콜백"""
        logger.info(f"로그인 결과: {result}")
        
    def _on_real_data(self, data: Dict):
        """실시간 데이터 콜백"""
        logger.info(f"실시간 데이터: {data}")
        
    def _on_order(self, data: Dict):
        """주문 콜백"""
        logger.info(f"주문 결과: {data}")
        
    def run_all_tests(self) -> List[TestResult]:
        """모든 테스트 실행"""
        logger.info("키움 API 연결 테스트 시작")
        self.is_testing = True
        self.test_results = []
        
        try:
            # 1. 서버 연결 테스트
            self._test_server_connection()
            
            # 2. 로그인 테스트
            self._test_login()
            
            # 3. 계좌 정보 조회 테스트
            self._test_account_info()
            
            # 4. 예수금 조회 테스트
            self._test_deposit_info()
            
            # 5. 현재가 조회 테스트
            self._test_current_price()
            
            # 6. 실시간 데이터 구독 테스트
            self._test_real_data_subscription()
            
            # 7. 포지션 정보 조회 테스트
            self._test_position_info()
            
            # 8. 주문 이력 조회 테스트
            self._test_order_history()
            
            # 9. 연결 안정성 테스트
            self._test_connection_stability()
            
        except Exception as e:
            logger.error(f"테스트 중 오류 발생: {e}")
            self._add_test_result("전체 테스트", False, f"테스트 중 오류: {e}", 0)
        
        finally:
            self.is_testing = False
            self.kiwoom_api.disconnect()
            
        return self.test_results
    
    def _test_server_connection(self):
        """서버 연결 테스트"""
        start_time = time.time()
        
        try:
            logger.info("서버 연결 테스트 시작")
            success = self.kiwoom_api.connect(self.test_config["connection_timeout"])
            
            duration = time.time() - start_time
            if success:
                self._add_test_result("서버 연결", True, "서버에 성공적으로 연결됨", duration)
            else:
                self._add_test_result("서버 연결", False, "서버 연결 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("서버 연결", False, f"연결 오류: {e}", duration)
    
    def _test_login(self):
        """로그인 테스트"""
        start_time = time.time()
        
        try:
            logger.info("로그인 테스트 시작")
            
            # 설정 파일에서 로그인 정보 읽기
            login_info = self._load_login_config()
            if not login_info:
                self._add_test_result("로그인", False, "로그인 설정 파일을 찾을 수 없음", 0)
                return
            
            success = self.kiwoom_api.login(
                login_info["user_id"],
                login_info["password"], 
                login_info["account"],
                self.test_config["login_timeout"]
            )
            
            duration = time.time() - start_time
            if success:
                self._add_test_result("로그인", True, "로그인 성공", duration)
            else:
                self._add_test_result("로그인", False, "로그인 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("로그인", False, f"로그인 오류: {e}", duration)
    
    def _test_account_info(self):
        """계좌 정보 조회 테스트"""
        start_time = time.time()
        
        try:
            logger.info("계좌 정보 조회 테스트 시작")
            account_info = self.kiwoom_api.get_account_info()
            
            duration = time.time() - start_time
            if account_info and "accounts" in account_info:
                self._add_test_result("계좌 정보 조회", True, 
                                    f"계좌 {len(account_info['accounts'])}개 조회 성공", duration,
                                    {"account_count": len(account_info["accounts"])})
            else:
                self._add_test_result("계좌 정보 조회", False, "계좌 정보 조회 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("계좌 정보 조회", False, f"조회 오류: {e}", duration)
    
    def _test_deposit_info(self):
        """예수금 조회 테스트"""
        start_time = time.time()
        
        try:
            logger.info("예수금 조회 테스트 시작")
            
            login_info = self._load_login_config()
            if not login_info:
                self._add_test_result("예수금 조회", False, "로그인 설정 파일을 찾을 수 없음", 0)
                return
            
            deposit_info = self.kiwoom_api.get_deposit_info(login_info["account"])
            
            duration = time.time() - start_time
            if deposit_info and "available_amount" in deposit_info:
                self._add_test_result("예수금 조회", True, 
                                    f"예수금 조회 성공: {deposit_info['available_amount']:,}원", duration,
                                    {"available_amount": deposit_info["available_amount"]})
            else:
                self._add_test_result("예수금 조회", False, "예수금 조회 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("예수금 조회", False, f"조회 오류: {e}", duration)
    
    def _test_current_price(self):
        """현재가 조회 테스트"""
        start_time = time.time()
        
        try:
            logger.info("현재가 조회 테스트 시작")
            
            success_count = 0
            for stock_code in self.test_config["test_stocks"]:
                price = self.kiwoom_api.get_current_price(stock_code)
                if price and price > 0:
                    success_count += 1
                    logger.info(f"{stock_code}: {price:,}원")
                else:
                    logger.warning(f"{stock_code}: 가격 조회 실패")
            
            duration = time.time() - start_time
            if success_count > 0:
                self._add_test_result("현재가 조회", True, 
                                    f"{success_count}/{len(self.test_config['test_stocks'])} 종목 조회 성공", duration,
                                    {"success_count": success_count, "total_count": len(self.test_config["test_stocks"])})
            else:
                self._add_test_result("현재가 조회", False, "모든 종목 가격 조회 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("현재가 조회", False, f"조회 오류: {e}", duration)
    
    def _test_real_data_subscription(self):
        """실시간 데이터 구독 테스트"""
        start_time = time.time()
        
        try:
            logger.info("실시간 데이터 구독 테스트 시작")
            
            success_count = 0
            for stock_code in self.test_config["test_stocks"][:1]:  # 첫 번째 종목만 테스트
                success = self.kiwoom_api.subscribe_real_data(stock_code, "주식체결")
                if success:
                    success_count += 1
                    logger.info(f"{stock_code} 실시간 구독 성공")
                else:
                    logger.warning(f"{stock_code} 실시간 구독 실패")
            
            # 잠시 대기하여 데이터 수신 확인
            time.sleep(3)
            
            # 실시간 데이터 캐시 확인
            cache_data = self.kiwoom_api.get_real_data_cache()
            
            duration = time.time() - start_time
            if success_count > 0 and cache_data:
                self._add_test_result("실시간 데이터 구독", True, 
                                    f"{success_count}개 종목 구독 성공", duration,
                                    {"subscription_count": success_count, "cache_data_count": len(cache_data)})
            else:
                self._add_test_result("실시간 데이터 구독", False, "실시간 데이터 구독 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("실시간 데이터 구독", False, f"구독 오류: {e}", duration)
    
    def _test_position_info(self):
        """포지션 정보 조회 테스트"""
        start_time = time.time()
        
        try:
            logger.info("포지션 정보 조회 테스트 시작")
            
            login_info = self._load_login_config()
            if not login_info:
                self._add_test_result("포지션 정보 조회", False, "로그인 설정 파일을 찾을 수 없음", 0)
                return
            
            position_info = self.kiwoom_api.get_position_info(login_info["account"])
            
            duration = time.time() - start_time
            if position_info and "positions" in position_info:
                self._add_test_result("포지션 정보 조회", True, 
                                    f"포지션 {len(position_info['positions'])}개 조회 성공", duration,
                                    {"position_count": len(position_info["positions"])})
            else:
                self._add_test_result("포지션 정보 조회", True, "포지션 없음", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("포지션 정보 조회", False, f"조회 오류: {e}", duration)
    
    def _test_order_history(self):
        """주문 이력 조회 테스트"""
        start_time = time.time()
        
        try:
            logger.info("주문 이력 조회 테스트 시작")
            
            login_info = self._load_login_config()
            if not login_info:
                self._add_test_result("주문 이력 조회", False, "로그인 설정 파일을 찾을 수 없음", 0)
                return
            
            order_history = self.kiwoom_api.get_order_history(login_info["account"])
            
            duration = time.time() - start_time
            if order_history is not None:
                self._add_test_result("주문 이력 조회", True, 
                                    f"주문 이력 {len(order_history)}개 조회 성공", duration,
                                    {"order_count": len(order_history)})
            else:
                self._add_test_result("주문 이력 조회", False, "주문 이력 조회 실패", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("주문 이력 조회", False, f"조회 오류: {e}", duration)
    
    def _test_connection_stability(self):
        """연결 안정성 테스트"""
        start_time = time.time()
        
        try:
            logger.info("연결 안정성 테스트 시작")
            
            # 10초 동안 연결 상태 모니터링
            test_duration = 10
            check_interval = 1
            checks = 0
            successful_checks = 0
            
            for i in range(test_duration):
                if self.kiwoom_api.is_connected:
                    successful_checks += 1
                checks += 1
                time.sleep(check_interval)
            
            duration = time.time() - start_time
            stability_rate = (successful_checks / checks) * 100 if checks > 0 else 0
            
            if stability_rate >= 90:
                self._add_test_result("연결 안정성", True, 
                                    f"연결 안정성 {stability_rate:.1f}%", duration,
                                    {"stability_rate": stability_rate})
            else:
                self._add_test_result("연결 안정성", False, 
                                    f"연결 안정성 {stability_rate:.1f}% (목표: 90% 이상)", duration,
                                    {"stability_rate": stability_rate})
                
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result("연결 안정성", False, f"테스트 오류: {e}", duration)
    
    def _load_login_config(self) -> Optional[Dict]:
        """로그인 설정 파일 로드"""
        try:
            with open("config/kiwoom_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("login", {})
        except FileNotFoundError:
            logger.warning("로그인 설정 파일을 찾을 수 없습니다.")
            return None
        except Exception as e:
            logger.error(f"설정 파일 로드 오류: {e}")
            return None
    
    def _add_test_result(self, test_name: str, success: bool, message: str, duration: float, details: Dict = None):
        """테스트 결과 추가"""
        result = TestResult(
            test_name=test_name,
            success=success,
            message=message,
            duration=duration,
            timestamp=datetime.now(),
            details=details or {}
        )
        self.test_results.append(result)
        
        status = "✅ 성공" if success else "❌ 실패"
        logger.info(f"[{status}] {test_name}: {message} ({duration:.2f}초)")
    
    def generate_report(self) -> str:
        """테스트 리포트 생성"""
        if not self.test_results:
            return "테스트 결과가 없습니다."
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        total_duration = sum(result.duration for result in self.test_results)
        
        report = f"""
=== 키움 API 연결 테스트 리포트 ===
테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
총 테스트: {total_tests}개
성공: {successful_tests}개
실패: {failed_tests}개
성공률: {(successful_tests/total_tests)*100:.1f}%
총 소요시간: {total_duration:.2f}초

=== 상세 결과 ===
"""
        
        for result in self.test_results:
            status = "✅" if result.success else "❌"
            report += f"{status} {result.test_name}: {result.message} ({result.duration:.2f}초)\n"
            
            if result.details:
                for key, value in result.details.items():
                    report += f"    - {key}: {value}\n"
        
        # 권장사항
        if failed_tests > 0:
            report += f"\n=== 권장사항 ===\n"
            report += "실패한 테스트를 확인하고 다음을 점검하세요:\n"
            report += "1. Windows 서버가 실행 중인지 확인\n"
            report += "2. 키움 API가 정상적으로 설치되어 있는지 확인\n"
            report += "3. 로그인 정보가 올바른지 확인\n"
            report += "4. 네트워크 연결 상태 확인\n"
        else:
            report += f"\n=== 결론 ===\n"
            report += "모든 테스트가 성공적으로 완료되었습니다! 🎉\n"
            report += "키움 API 시스템이 정상적으로 작동하고 있습니다.\n"
        
        return report

def main():
    """메인 함수"""
    logger.info("키움 API 연결 테스트 시작")
    
    # 테스터 생성
    tester = KiwoomConnectionTester()
    
    try:
        # 모든 테스트 실행
        results = tester.run_all_tests()
        
        # 리포트 생성 및 출력
        report = tester.generate_report()
        print(report)
        
        # 리포트 파일 저장
        with open("logs/kiwoom_test_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("테스트 완료. 리포트가 logs/kiwoom_test_report.txt에 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 