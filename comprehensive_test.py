#!/usr/bin/env python3
"""
종합 테스트 스크립트
Windows 서버에서 모든 기능을 체계적으로 테스트
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

class ComprehensiveTester:
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
    def log_test(self, test_name, success, message=""):
        """테스트 결과 기록"""
        self.test_results[test_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {test_name}")
        if message:
            print(f"  └─ {message}")
        print()
    
    def test_environment(self):
        """환경 테스트"""
        print("🔍 환경 테스트 시작...")
        
        # Python 버전 확인
        try:
            version = sys.version
            self.log_test("Python 버전", True, f"버전: {version}")
        except Exception as e:
            self.log_test("Python 버전", False, str(e))
        
        # 운영체제 확인
        try:
            os_name = os.name
            self.log_test("운영체제", True, f"OS: {os_name}")
        except Exception as e:
            self.log_test("운영체제", False, str(e))
        
        # 현재 디렉토리 확인
        try:
            current_dir = os.getcwd()
            self.log_test("작업 디렉토리", True, f"경로: {current_dir}")
        except Exception as e:
            self.log_test("작업 디렉토리", False, str(e))
    
    def test_dependencies(self):
        """의존성 패키지 테스트"""
        print("📦 의존성 패키지 테스트 시작...")
        
        required_packages = [
            'PyQt5',
            'pandas',
            'numpy',
            'matplotlib',
            'requests',
            'python-dotenv',
            'schedule',
            'loguru'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log_test(f"패키지: {package}", True)
            except ImportError:
                self.log_test(f"패키지: {package}", False, "설치 필요")
    
    def test_kiwoom_api(self):
        """키움 API 테스트"""
        print("🔗 키움 API 테스트 시작...")
        
        try:
            from PyQt5.QAxContainer import *
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import *
            
            # QApplication 생성
            app = QApplication(sys.argv)
            
            # 키움 API 객체 생성
            kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            
            if kiwoom.isNull():
                self.log_test("키움 API 객체 생성", False, "API 객체 생성 실패")
                return
            
            self.log_test("키움 API 객체 생성", True)
            
            # 연결 상태 확인
            connect_state = kiwoom.GetConnectState()
            if connect_state == 1:
                self.log_test("키움 API 연결", True, "연결됨")
            else:
                self.log_test("키움 API 연결", False, "연결되지 않음 - 영웅문 실행 필요")
            
        except ImportError:
            self.log_test("키움 API 테스트", False, "PyQt5 설치 필요")
        except Exception as e:
            self.log_test("키움 API 테스트", False, str(e))
    
    def test_strategy_modules(self):
        """전략 모듈 테스트"""
        print("📊 전략 모듈 테스트 시작...")
        
        try:
            from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy
            
            # Mock API 클래스
            class MockAPI:
                def order_stock(self, account, code, quantity, price, order_type):
                    return "TEST_ORDER_001"
            
            mock_api = MockAPI()
            
            # 각 전략 테스트
            strategies = [
                ("이동평균 전략", MovingAverageStrategy(mock_api, "TEST_ACCOUNT")),
                ("RSI 전략", RSIStrategy(mock_api, "TEST_ACCOUNT")),
                ("볼린저밴드 전략", BollingerBandsStrategy(mock_api, "TEST_ACCOUNT"))
            ]
            
            for name, strategy in strategies:
                try:
                    # 기본 매수/매도 조건 테스트
                    result = strategy.should_buy("005930", 1000)
                    result = strategy.should_sell("005930", 1000)
                    self.log_test(f"전략: {name}", True)
                except Exception as e:
                    self.log_test(f"전략: {name}", False, str(e))
                    
        except Exception as e:
            self.log_test("전략 모듈 테스트", False, str(e))
    
    def test_configuration(self):
        """설정 파일 테스트"""
        print("⚙️ 설정 파일 테스트 시작...")
        
        try:
            from config import KIWOOM_CONFIG, TRADING_CONFIG, LOGGING_CONFIG
            
            # 설정 유효성 검사
            if KIWOOM_CONFIG['app_key'] == 'YOUR_APP_KEY_HERE':
                self.log_test("API 키 설정", False, "API 키를 설정해주세요")
            else:
                self.log_test("API 키 설정", True)
            
            self.log_test("거래 설정", True, f"기본 거래 금액: {TRADING_CONFIG['default_trade_amount']:,}원")
            self.log_test("로깅 설정", True, f"로그 레벨: {LOGGING_CONFIG['log_level']}")
            
        except Exception as e:
            self.log_test("설정 파일 테스트", False, str(e))
    
    def test_file_structure(self):
        """파일 구조 테스트"""
        print("📁 파일 구조 테스트 시작...")
        
        required_files = [
            'kiwoom_api.py',
            'trading_strategy.py',
            'config.py',
            'gui_trader.py',
            'auto_trader.py',
            'requirements.txt',
            'README.md'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                self.log_test(f"파일: {file}", True)
            else:
                self.log_test(f"파일: {file}", False, "파일 없음")
        
        # 디렉토리 확인
        required_dirs = ['logs', 'data', 'config']
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                self.log_test(f"디렉토리: {dir_name}", True)
            else:
                self.log_test(f"디렉토리: {dir_name}", False, "디렉토리 없음")
    
    def test_logging(self):
        """로깅 시스템 테스트"""
        print("📝 로깅 시스템 테스트 시작...")
        
        try:
            from loguru import logger
            
            # 로그 디렉토리 생성
            os.makedirs('logs', exist_ok=True)
            
            # 테스트 로그 작성
            logger.info("테스트 로그 메시지")
            logger.warning("테스트 경고 메시지")
            logger.error("테스트 오류 메시지")
            
            self.log_test("로깅 시스템", True, "로그 파일 생성됨")
            
        except Exception as e:
            self.log_test("로깅 시스템", False, str(e))
    
    def generate_report(self):
        """테스트 리포트 생성"""
        print("\n" + "=" * 60)
        print("📊 종합 테스트 리포트")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n테스트 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 실패한 테스트 목록
        if failed_tests > 0:
            print(f"\n❌ 실패한 테스트:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"  - {test_name}: {result['message']}")
        
        # 리포트 파일 저장
        report_file = f"logs/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 리포트 저장: {report_file}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 종합 테스트 시작")
        print("=" * 60)
        print(f"테스트 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 각 테스트 실행
        self.test_environment()
        self.test_dependencies()
        self.test_kiwoom_api()
        self.test_strategy_modules()
        self.test_configuration()
        self.test_file_structure()
        self.test_logging()
        
        # 리포트 생성
        success = self.generate_report()
        
        if success:
            print("\n🎉 모든 테스트가 성공했습니다!")
            print("자동매매 시스템을 실행할 준비가 완료되었습니다.")
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다.")
            print("실패한 항목을 확인하고 수정해주세요.")
        
        return success

def main():
    tester = ComprehensiveTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 