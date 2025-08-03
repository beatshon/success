#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
윈도우 서버에서 API 테스트를 위한 스크립트
맥에서 작업한 파일을 윈도우 서버에서 테스트할 때 사용
"""

import os
import sys
import json
import requests
import time
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 설정 파일 로드
try:
    from config.kiwoom_api_keys import *
    from config.kiwoom_config import *
except ImportError as e:
    print(f"설정 파일 로드 실패: {e}")
    print("config 폴더의 설정 파일을 확인해주세요.")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/windows_api_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WindowsAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.kiwoom_api_url = "http://localhost:8081"
        self.websocket_url = "ws://localhost:8082"
        
        # 테스트 결과 저장
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
    
    def test_kiwoom_connection(self):
        """Kiwoom API 연결 테스트"""
        logger.info("Kiwoom API 연결 테스트 시작")
        
        try:
            # Kiwoom API 서버 상태 확인
            response = requests.get(f"{self.kiwoom_api_url}/status", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Kiwoom API 서버 연결 성공")
                return True
            else:
                logger.error(f"❌ Kiwoom API 서버 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Kiwoom API 서버 연결 실패: {e}")
            return False
    
    def test_trading_system(self):
        """거래 시스템 API 테스트"""
        logger.info("거래 시스템 API 테스트 시작")
        
        test_cases = [
            {
                "name": "계좌 정보 조회",
                "endpoint": "/api/account/info",
                "method": "GET"
            },
            {
                "name": "주식 시세 조회",
                "endpoint": "/api/stock/price",
                "method": "GET",
                "params": {"code": "005930"}  # 삼성전자
            },
            {
                "name": "주문 가능 금액 조회",
                "endpoint": "/api/order/available",
                "method": "GET"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                if test_case["method"] == "GET":
                    if "params" in test_case:
                        response = requests.get(
                            f"{self.base_url}{test_case['endpoint']}", 
                            params=test_case["params"],
                            timeout=10
                        )
                    else:
                        response = requests.get(
                            f"{self.base_url}{test_case['endpoint']}", 
                            timeout=10
                        )
                
                if response.status_code == 200:
                    logger.info(f"✅ {test_case['name']} 성공")
                    results.append({
                        "test": test_case["name"],
                        "status": "success",
                        "response_code": response.status_code
                    })
                else:
                    logger.warning(f"⚠️ {test_case['name']} 응답 오류: {response.status_code}")
                    results.append({
                        "test": test_case["name"],
                        "status": "error",
                        "response_code": response.status_code
                    })
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ {test_case['name']} 실패: {e}")
                results.append({
                    "test": test_case["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def test_real_time_data(self):
        """실시간 데이터 API 테스트"""
        logger.info("실시간 데이터 API 테스트 시작")
        
        try:
            # 실시간 데이터 서버 상태 확인
            response = requests.get(f"{self.base_url}/api/realtime/status", timeout=10)
            if response.status_code == 200:
                logger.info("✅ 실시간 데이터 서버 연결 성공")
                return True
            else:
                logger.warning(f"⚠️ 실시간 데이터 서버 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 실시간 데이터 서버 연결 실패: {e}")
            return False
    
    def test_news_analysis(self):
        """뉴스 분석 API 테스트"""
        logger.info("뉴스 분석 API 테스트 시작")
        
        try:
            # 뉴스 분석 서버 상태 확인
            response = requests.get(f"{self.base_url}/api/news/status", timeout=10)
            if response.status_code == 200:
                logger.info("✅ 뉴스 분석 서버 연결 성공")
                return True
            else:
                logger.warning(f"⚠️ 뉴스 분석 서버 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 뉴스 분석 서버 연결 실패: {e}")
            return False
    
    def test_deep_learning_system(self):
        """딥러닝 시스템 API 테스트"""
        logger.info("딥러닝 시스템 API 테스트 시작")
        
        try:
            # 딥러닝 모델 상태 확인
            response = requests.get(f"{self.base_url}/api/ml/status", timeout=10)
            if response.status_code == 200:
                logger.info("✅ 딥러닝 시스템 연결 성공")
                return True
            else:
                logger.warning(f"⚠️ 딥러닝 시스템 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 딥러닝 시스템 연결 실패: {e}")
            return False
    
    def run_all_tests(self):
        """모든 API 테스트 실행"""
        logger.info("=" * 50)
        logger.info("윈도우 서버 API 테스트 시작")
        logger.info("=" * 50)
        
        # 1. Kiwoom 연결 테스트
        kiwoom_result = self.test_kiwoom_connection()
        self.test_results["tests"].append({
            "category": "kiwoom_connection",
            "result": kiwoom_result
        })
        
        # 2. 거래 시스템 테스트
        trading_results = self.test_trading_system()
        self.test_results["tests"].append({
            "category": "trading_system",
            "results": trading_results
        })
        
        # 3. 실시간 데이터 테스트
        realtime_result = self.test_real_time_data()
        self.test_results["tests"].append({
            "category": "real_time_data",
            "result": realtime_result
        })
        
        # 4. 뉴스 분석 테스트
        news_result = self.test_news_analysis()
        self.test_results["tests"].append({
            "category": "news_analysis",
            "result": news_result
        })
        
        # 5. 딥러닝 시스템 테스트
        ml_result = self.test_deep_learning_system()
        self.test_results["tests"].append({
            "category": "deep_learning",
            "result": ml_result
        })
        
        # 결과 저장
        self.save_test_results()
        
        logger.info("=" * 50)
        logger.info("API 테스트 완료")
        logger.info("=" * 50)
    
    def save_test_results(self):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/windows_api_test_results_{timestamp}.json"
        
        # logs 디렉토리 생성
        os.makedirs("logs", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"테스트 결과 저장: {filename}")
    
    def generate_report(self):
        """테스트 결과 리포트 생성"""
        logger.info("\n" + "=" * 60)
        logger.info("API 테스트 결과 리포트")
        logger.info("=" * 60)
        
        for test in self.test_results["tests"]:
            category = test["category"]
            logger.info(f"\n📋 {category.upper()}")
            
            if "result" in test:
                if test["result"]:
                    logger.info("   ✅ 성공")
                else:
                    logger.info("   ❌ 실패")
            elif "results" in test:
                for result in test["results"]:
                    if result["status"] == "success":
                        logger.info(f"   ✅ {result['test']}: 성공")
                    else:
                        logger.info(f"   ❌ {result['test']}: 실패")

def main():
    """메인 함수"""
    print("윈도우 서버 API 테스트 시작...")
    
    # API 테스터 생성
    tester = WindowsAPITester()
    
    # 모든 테스트 실행
    tester.run_all_tests()
    
    # 결과 리포트 생성
    tester.generate_report()
    
    print("\n테스트 완료! logs 폴더에서 상세 결과를 확인하세요.")

if __name__ == "__main__":
    main() 