#!/usr/bin/env python3
"""
하이브리드 자동매매 시스템
맥: 개발/테스트/모니터링
Windows: 실제 거래 실행
"""

import sys
import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from loguru import logger

# 로그 설정
logger.add("logs/hybrid_trading.log", rotation="1 day", retention="7 days")

class HybridTradingSystem:
    """하이브리드 자동매매 시스템"""
    
    def __init__(self, mode="mac"):
        self.mode = mode  # "mac" 또는 "windows"
        self.config = self.load_config()
        self.trading_status = "stopped"
        self.last_sync_time = None
        self.sync_enabled = True
        
        # 맥용 시뮬레이션 데이터
        self.mac_simulator = None
        if mode == "mac":
            from mac_deposit_test import MacDepositSimulator
            self.mac_simulator = MacDepositSimulator()
        
        # 거래 이력 및 상태
        self.trade_history = []
        self.current_positions = {}
        self.windows_connection_status = "disconnected"
        
        logger.info(f"하이브리드 시스템 초기화 완료 - 모드: {mode}")
    
    def load_config(self):
        """설정 파일 로드"""
        config_file = "config/hybrid_config.json"
        
        default_config = {
            "windows_server": {
                "host": "localhost",
                "port": 8080,
                "api_key": "your_api_key_here",
                "timeout": 30
            },
            "trading": {
                "max_positions": 5,
                "default_trade_amount": 100000,
                "update_interval": 60,
                "risk_management": {
                    "max_loss_per_trade": 0.02,  # 2%
                    "max_daily_loss": 0.05,      # 5%
                    "stop_loss": 0.03            # 3%
                }
            },
            "sync": {
                "enabled": True,
                "interval": 30,
                "auto_sync": True
            },
            "simulation": {
                "enabled": True,
                "realistic_mode": True,
                "demo_account": "1234567890"
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        
        return default_config
    
    def save_config(self):
        """설정 파일 저장"""
        config_file = "config/hybrid_config.json"
        os.makedirs("config", exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("설정 파일 저장 완료")
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
    
    def test_windows_connection(self):
        """Windows 서버 연결 테스트"""
        try:
            url = f"http://{self.config['windows_server']['host']}:{self.config['windows_server']['port']}/api/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.windows_connection_status = "connected"
                logger.info("Windows 서버 연결 성공")
                return True
            else:
                self.windows_connection_status = "error"
                logger.error(f"Windows 서버 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.windows_connection_status = "disconnected"
            logger.error(f"Windows 서버 연결 실패: {e}")
            return False
    
    def get_account_info(self):
        """계좌 정보 조회"""
        if self.mode == "mac":
            # 맥에서는 시뮬레이션 데이터 사용
            return self.mac_simulator.get_account_info()
        else:
            # Windows에서는 실제 API 사용
            from kiwoom_api import KiwoomAPI
            api = KiwoomAPI()
            return api.get_account_info()
    
    def get_deposit_info(self, account):
        """예수금 조회"""
        if self.mode == "mac":
            # 맥에서는 시뮬레이션 데이터 사용
            return self.mac_simulator.get_deposit_info(account)
        else:
            # Windows에서는 실제 API 사용
            from kiwoom_api import KiwoomAPI
            api = KiwoomAPI()
            return api.get_deposit_info(account)
    
    def get_windows_status(self):
        """Windows 서버 상태 조회"""
        if not self.test_windows_connection():
            return {"status": "disconnected", "message": "Windows 서버에 연결할 수 없습니다."}
        
        try:
            url = f"http://{self.config['windows_server']['host']}:{self.config['windows_server']['port']}/api/status"
            headers = {"Authorization": f"Bearer {self.config['windows_server']['api_key']}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"상태 조회 실패: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Windows 상태 조회 실패: {e}")
            return {"status": "error", "message": str(e)}
    
    def start_trading(self, strategy_config=None):
        """거래 시작"""
        if self.mode == "mac":
            # 맥에서는 시뮬레이션 거래 시작
            logger.info("맥에서 시뮬레이션 거래 시작")
            return self.start_mac_simulation(strategy_config)
        else:
            # Windows에서는 실제 거래 시작
            logger.info("Windows에서 실제 거래 시작")
            return self.start_windows_trading(strategy_config)
    
    def start_mac_simulation(self, strategy_config=None):
        """맥 시뮬레이션 거래 시작"""
        try:
            # 시뮬레이션 설정
            if not strategy_config:
                strategy_config = {
                    "type": "moving_average",
                    "short_period": 5,
                    "long_period": 20,
                    "trade_amount": self.config["trading"]["default_trade_amount"],
                    "watch_stocks": [
                        {"code": "005930", "name": "삼성전자"},
                        {"code": "000660", "name": "SK하이닉스"},
                        {"code": "035420", "name": "NAVER"}
                    ]
                }
            
            # 시뮬레이션 거래 시작
            from mac_demo_trading import MacDemoTrader, MacDemoStrategy
            
            self.mac_trader = MacDemoTrader()
            self.mac_strategy = MacDemoStrategy(self.mac_trader)
            
            # 모니터링 종목 추가
            for stock in strategy_config.get("watch_stocks", []):
                self.mac_trader.add_watch_stock(stock["code"], stock.get("name", ""))
            
            self.trading_status = "running"
            logger.info("맥 시뮬레이션 거래 시작 완료")
            
            # Windows 서버에 시뮬레이션 결과 전송
            if self.config["sync"]["enabled"] and self.test_windows_connection():
                self.sync_simulation_to_windows(strategy_config)
            
            return {"success": True, "message": "맥 시뮬레이션 거래가 시작되었습니다."}
            
        except Exception as e:
            logger.error(f"맥 시뮬레이션 거래 시작 실패: {e}")
            return {"success": False, "message": str(e)}
    
    def start_windows_trading(self, strategy_config=None):
        """Windows 실제 거래 시작"""
        if not self.test_windows_connection():
            return {"success": False, "message": "Windows 서버에 연결할 수 없습니다."}
        
        try:
            url = f"http://{self.config['windows_server']['host']}:{self.config['windows_server']['port']}/api/trading"
            headers = {
                "Authorization": f"Bearer {self.config['windows_server']['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "action": "start",
                "strategy_config": strategy_config or {}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.trading_status = "running"
                    logger.info("Windows 실제 거래 시작 완료")
                return result
            else:
                return {"success": False, "message": f"거래 시작 실패: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Windows 거래 시작 실패: {e}")
            return {"success": False, "message": str(e)}
    
    def sync_simulation_to_windows(self, strategy_config):
        """시뮬레이션 결과를 Windows 서버에 동기화"""
        try:
            if not self.test_windows_connection():
                return False
            
            # 시뮬레이션 데이터 수집
            sync_data = {
                "timestamp": datetime.now().isoformat(),
                "simulation_data": {
                    "account_info": self.mac_simulator.get_account_info(),
                    "deposit_info": self.mac_simulator.get_deposit_info(self.config["simulation"]["demo_account"]),
                    "strategy_config": strategy_config,
                    "trade_history": self.trade_history,
                    "current_positions": self.current_positions
                }
            }
            
            url = f"http://{self.config['windows_server']['host']}:{self.config['windows_server']['port']}/api/sync"
            headers = {
                "Authorization": f"Bearer {self.config['windows_server']['api_key']}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=sync_data, timeout=30)
            
            if response.status_code == 200:
                self.last_sync_time = datetime.now()
                logger.info("시뮬레이션 데이터 Windows 동기화 완료")
                return True
            else:
                logger.error(f"시뮬레이션 데이터 동기화 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 동기화 실패: {e}")
            return False
    
    def stop_trading(self):
        """거래 중지"""
        if self.mode == "mac":
            # 맥에서는 Windows 서버로 명령 전송
            command = {
                "action": "stop_trading",
                "timestamp": datetime.now().isoformat()
            }
            
            result = self.send_trading_command(command)
            if result:
                self.trading_status = "stopped"
                logger.info("거래 중지 명령 전송 완료")
                return True
            else:
                logger.error("거래 중지 명령 전송 실패")
                return False
        else:
            # Windows에서는 직접 거래 중지
            self.trading_status = "stopped"
            logger.info("거래 중지 완료")
            return True
    
    def get_trading_status(self):
        """거래 상태 조회"""
        if self.mode == "mac":
            # 맥에서는 Windows 서버 상태 조회
            windows_status = self.get_windows_status()
            return {
                "local_status": self.trading_status,
                "windows_status": windows_status,
                "mode": "mac"
            }
        else:
            # Windows에서는 로컬 상태 반환
            return {
                "local_status": self.trading_status,
                "mode": "windows"
            }
    
    def sync_with_windows(self):
        """Windows 서버와 동기화"""
        if self.mode != "mac":
            return True
        
        try:
            windows_status = self.get_windows_status()
            if windows_status["status"] == "running":
                self.last_sync_time = datetime.now()
                logger.info("Windows 서버와 동기화 완료")
                return True
            else:
                logger.warning(f"Windows 서버 연결 실패: {windows_status.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"동기화 오류: {e}")
            return False

class HybridTradingManager:
    """하이브리드 거래 관리자"""
    
    def __init__(self, mode="mac"):
        self.system = HybridTradingSystem(mode)
        self.monitoring = False
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.monitoring = True
        logger.info("하이브리드 모니터링 시작")
        
        try:
            while self.monitoring:
                # Windows 서버 상태 확인
                if self.system.mode == "mac":
                    self.system.sync_with_windows()
                
                # 거래 상태 출력
                status = self.system.get_trading_status()
                print(f"\n📊 하이브리드 거래 상태 - {datetime.now().strftime('%H:%M:%S')}")
                print(f"로컬 상태: {status['local_status']}")
                
                if self.system.mode == "mac":
                    print(f"Windows 상태: {status['windows_status']['status']}")
                
                # 계좌 정보 출력
                accounts = self.system.get_account_info()
                for account, info in accounts.items():
                    deposit_info = self.system.get_deposit_info(account)
                    if deposit_info:
                        print(f"계좌 {account}: {deposit_info.get('deposit', 0):,}원")
                
                time.sleep(self.system.config["sync"]["interval"])
                
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        logger.info("하이브리드 모니터링 중지")
    
    def run_demo(self):
        """데모 실행"""
        if self.system.mode == "mac":
            # 맥에서는 시뮬레이션 데모
            from mac_demo_trading import run_mac_demo
            run_mac_demo()
        else:
            # Windows에서는 실제 거래 데모
            logger.info("Windows에서 실제 거래 데모 실행")
            # 실제 거래 로직 구현

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="하이브리드 자동매매 시스템")
    parser.add_argument("--mode", choices=["mac", "windows"], default="mac", 
                       help="실행 모드 (mac 또는 windows)")
    parser.add_argument("--action", choices=["monitor", "demo", "start", "stop"], 
                       default="monitor", help="실행할 액션")
    parser.add_argument("--strategy", default="moving_average", 
                       help="사용할 전략")
    
    args = parser.parse_args()
    
    print(f"🚀 하이브리드 자동매매 시스템 시작")
    print(f"모드: {args.mode}")
    print(f"액션: {args.action}")
    print("=" * 60)
    
    manager = HybridTradingManager(args.mode)
    
    if args.action == "monitor":
        manager.start_monitoring()
    elif args.action == "demo":
        manager.run_demo()
    elif args.action == "start":
        strategy_config = {"type": args.strategy}
        manager.system.start_trading(strategy_config)
    elif args.action == "stop":
        manager.system.stop_trading()

if __name__ == "__main__":
    main() 