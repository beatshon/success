#!/usr/bin/env python3
"""
맥용 하이브리드 제어 스크립트
맥에서 시뮬레이션하고 Windows 서버에 반영하여 QA 후 제어
"""

import sys
import os
import time
import json
import argparse
import requests
from datetime import datetime
from loguru import logger

# 로그 설정
logger.add("logs/mac_hybrid_controller.log", rotation="1 day", retention="7 days")

class MacHybridController:
    """맥용 하이브리드 제어 클래스"""
    
    def __init__(self):
        from hybrid_trading_system import HybridTradingSystem
        self.hybrid_system = HybridTradingSystem(mode="mac")
        self.is_running = False
        
        logger.info("맥 하이브리드 제어 시스템 초기화 완료")
    
    def start_simulation(self, strategy_config=None):
        """시뮬레이션 시작"""
        try:
            logger.info("🔵 맥 시뮬레이션 시작")
            
            # Windows 서버 연결 확인
            if not self.hybrid_system.test_windows_connection():
                logger.warning("⚠️ Windows 서버에 연결할 수 없습니다. 시뮬레이션만 실행합니다.")
            
            # 시뮬레이션 거래 시작
            result = self.hybrid_system.start_mac_simulation(strategy_config)
            
            if result.get("success"):
                self.is_running = True
                logger.info("✅ 맥 시뮬레이션 시작 완료")
                return True
            else:
                logger.error(f"❌ 맥 시뮬레이션 시작 실패: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 시뮬레이션 시작 오류: {e}")
            return False
    
    def stop_simulation(self):
        """시뮬레이션 중지"""
        try:
            logger.info("🔴 맥 시뮬레이션 중지")
            
            if hasattr(self.hybrid_system, 'mac_trader'):
                self.hybrid_system.mac_trader.stop_trading()
            
            self.is_running = False
            self.hybrid_system.trading_status = "stopped"
            
            logger.info("✅ 맥 시뮬레이션 중지 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 시뮬레이션 중지 오류: {e}")
            return False
    
    def sync_to_windows(self, strategy_config=None):
        """Windows 서버에 동기화"""
        try:
            logger.info("🔄 Windows 서버 동기화 시작")
            
            if not self.hybrid_system.test_windows_connection():
                logger.error("❌ Windows 서버에 연결할 수 없습니다.")
                return False
            
            # 시뮬레이션 데이터 동기화
            result = self.hybrid_system.sync_simulation_to_windows(strategy_config)
            
            if result:
                logger.info("✅ Windows 서버 동기화 완료")
                return True
            else:
                logger.error("❌ Windows 서버 동기화 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ Windows 동기화 오류: {e}")
            return False
    
    def start_windows_trading(self, strategy_config=None):
        """Windows에서 실제 거래 시작"""
        try:
            logger.info("🚀 Windows 실제 거래 시작")
            
            # Windows 서버 연결 확인
            if not self.hybrid_system.test_windows_connection():
                logger.error("❌ Windows 서버에 연결할 수 없습니다.")
                return False
            
            # Windows에서 실제 거래 시작
            result = self.hybrid_system.start_windows_trading(strategy_config)
            
            if result.get("success"):
                logger.info("✅ Windows 실제 거래 시작 완료")
                return True
            else:
                logger.error(f"❌ Windows 실제 거래 시작 실패: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Windows 거래 시작 오류: {e}")
            return False
    
    def stop_windows_trading(self):
        """Windows에서 실제 거래 중지"""
        try:
            logger.info("🛑 Windows 실제 거래 중지")
            
            if not self.hybrid_system.test_windows_connection():
                logger.error("❌ Windows 서버에 연결할 수 없습니다.")
                return False
            
            # Windows에서 실제 거래 중지
            url = f"http://{self.hybrid_system.config['windows_server']['host']}:{self.hybrid_system.config['windows_server']['port']}/api/trading"
            headers = {
                "Authorization": f"Bearer {self.hybrid_system.config['windows_server']['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {"action": "stop"}
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("✅ Windows 실제 거래 중지 완료")
                    return True
                else:
                    logger.error(f"❌ Windows 실제 거래 중지 실패: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ Windows 실제 거래 중지 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Windows 거래 중지 오류: {e}")
            return False
    
    def get_status(self):
        """현재 상태 조회"""
        try:
            status = {
                "mac_simulation": {
                    "running": self.is_running,
                    "status": self.hybrid_system.trading_status
                },
                "windows_connection": {
                    "status": self.hybrid_system.windows_connection_status,
                    "last_sync": self.hybrid_system.last_sync_time.isoformat() if self.hybrid_system.last_sync_time else None
                }
            }
            
            # Windows 서버 상태 조회
            if self.hybrid_system.test_windows_connection():
                windows_status = self.hybrid_system.get_windows_status()
                status["windows_server"] = windows_status
            
            return status
            
        except Exception as e:
            logger.error(f"상태 조회 오류: {e}")
            return {"error": str(e)}
    
    def analyze_simulation_results(self):
        """시뮬레이션 결과 분석"""
        try:
            if not hasattr(self.hybrid_system, 'mac_trader'):
                return {
                    "duration": "N/A",
                    "trade_count": 0,
                    "profit_rate": 0.0,
                    "max_loss": 0.0,
                    "trades": []
                }
            
            trader = self.hybrid_system.mac_trader
            
            # 거래 이력 분석
            trades = trader.trade_history if hasattr(trader, 'trade_history') else []
            trade_count = len(trades)
            
            # 수익률 계산
            total_profit = 0
            max_loss = 0
            initial_deposit = trader.deposit_info.get('deposit', 10000000)
            
            for trade in trades:
                if trade.get('action') == '매수':
                    total_profit -= trade.get('quantity', 0) * trade.get('price', 0)
                elif trade.get('action') == '매도':
                    total_profit += trade.get('quantity', 0) * trade.get('price', 0)
                
                # 최대 손실 계산
                current_loss = abs(total_profit) / initial_deposit * 100
                if current_loss > max_loss:
                    max_loss = current_loss
            
            profit_rate = (total_profit / initial_deposit) * 100 if initial_deposit > 0 else 0
            
            # 시뮬레이션 기간 계산
            duration = "N/A"
            if hasattr(trader, 'start_time'):
                duration = f"{int(time.time() - trader.start_time)}초"
            
            return {
                "duration": duration,
                "trade_count": trade_count,
                "profit_rate": profit_rate,
                "max_loss": max_loss,
                "trades": trades,
                "total_profit": total_profit,
                "initial_deposit": initial_deposit
            }
            
        except Exception as e:
            logger.error(f"시뮬레이션 결과 분석 오류: {e}")
            return {
                "duration": "N/A",
                "trade_count": 0,
                "profit_rate": 0.0,
                "max_loss": 0.0,
                "trades": []
            }
    
    def approve_all_trades(self, strategy_config=None):
        """전체 거래 승인"""
        try:
            logger.info("✅ 전체 거래 승인 시작")
            
            # Windows 서버에 전체 거래 승인 요청 전송
            if not self.hybrid_system.test_windows_connection():
                logger.error("❌ Windows 서버에 연결할 수 없습니다.")
                return False
            
            # 승인된 거래 데이터 준비
            approval_data = {
                "approval_type": "all_trades",
                "strategy_config": strategy_config,
                "simulation_results": self.analyze_simulation_results(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Windows 서버로 승인 요청 전송
            url = f"http://{self.hybrid_system.config['windows_server']['host']}:{self.hybrid_system.config['windows_server']['port']}/api/approve-trades"
            headers = {
                "Authorization": f"Bearer {self.hybrid_system.config['windows_server']['api_key']}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=approval_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("✅ 전체 거래 승인 완료")
                    return True
                else:
                    logger.error(f"❌ 전체 거래 승인 실패: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ 전체 거래 승인 요청 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 전체 거래 승인 오류: {e}")
            return False
    
    def approve_selected_trades(self, strategy_config=None):
        """선택적 거래 승인"""
        try:
            logger.info("✅ 선택적 거래 승인 시작")
            
            # 시뮬레이션 결과 분석
            simulation_results = self.analyze_simulation_results()
            trades = simulation_results.get('trades', [])
            
            if not trades:
                logger.warning("⚠️ 승인할 거래가 없습니다.")
                return True
            
            # 거래 목록 표시
            print("\n" + "="*80)
            print("📋 시뮬레이션 거래 목록")
            print("="*80)
            print(f"{'번호':<4} {'시간':<12} {'종목':<10} {'액션':<6} {'수량':<6} {'가격':<10} {'금액':<12}")
            print("-" * 80)
            
            selected_trades = []
            for i, trade in enumerate(trades, 1):
                timestamp = trade.get('timestamp', 'N/A')
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime("%H:%M:%S")
                
                code = trade.get('code', 'N/A')
                action = trade.get('action', 'N/A')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                amount = quantity * price
                
                print(f"{i:<4} {timestamp:<12} {code:<10} {action:<6} {quantity:<6} {price:<10,} {amount:<12,}")
            
            print("="*80)
            
            # 사용자 선택
            print("\n승인할 거래 번호를 입력하세요 (쉼표로 구분, 'all' = 전체 선택):")
            user_input = input("선택: ").strip()
            
            if user_input.lower() == 'all':
                selected_indices = list(range(1, len(trades) + 1))
            else:
                try:
                    selected_indices = [int(x.strip()) for x in user_input.split(',')]
                except ValueError:
                    logger.error("❌ 잘못된 입력 형식")
                    return False
            
            # 선택된 거래 필터링
            selected_trades = []
            for idx in selected_indices:
                if 1 <= idx <= len(trades):
                    selected_trades.append(trades[idx - 1])
                else:
                    logger.warning(f"⚠️ 잘못된 거래 번호: {idx}")
            
            if not selected_trades:
                logger.warning("⚠️ 선택된 거래가 없습니다.")
                return True
            
            # Windows 서버에 선택적 거래 승인 요청 전송
            if not self.hybrid_system.test_windows_connection():
                logger.error("❌ Windows 서버에 연결할 수 없습니다.")
                return False
            
            approval_data = {
                "approval_type": "selected_trades",
                "strategy_config": strategy_config,
                "selected_trades": selected_trades,
                "timestamp": datetime.now().isoformat()
            }
            
            url = f"http://{self.hybrid_system.config['windows_server']['host']}:{self.hybrid_system.config['windows_server']['port']}/api/approve-trades"
            headers = {
                "Authorization": f"Bearer {self.hybrid_system.config['windows_server']['api_key']}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=approval_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ 선택적 거래 승인 완료 ({len(selected_trades)}건)")
                    return True
                else:
                    logger.error(f"❌ 선택적 거래 승인 실패: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ 선택적 거래 승인 요청 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 선택적 거래 승인 오류: {e}")
            return False
    
    def run_qa_process(self, strategy_config=None):
        """QA 프로세스 실행"""
        try:
            logger.info("🧪 QA 프로세스 시작")
            
            # 1단계: 맥에서 시뮬레이션
            logger.info("1️⃣ 맥 시뮬레이션 실행")
            if not self.start_simulation(strategy_config):
                logger.error("❌ 맥 시뮬레이션 실패")
                return False
            
            # 시뮬레이션 실행 대기
            logger.info("⏳ 시뮬레이션 실행 중... (30초)")
            time.sleep(30)
            
            # 2단계: Windows 서버에 동기화
            logger.info("2️⃣ Windows 서버 동기화")
            if not self.sync_to_windows(strategy_config):
                logger.error("❌ Windows 동기화 실패")
                return False
            
            # 3단계: QA 검증 및 거래 승인
            logger.info("3️⃣ QA 검증 및 거래 승인")
            status = self.get_status()
            logger.info(f"현재 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            # 시뮬레이션 결과 분석
            simulation_results = self.analyze_simulation_results()
            
            # 사용자에게 상세한 정보 제공
            print("\n" + "="*60)
            print("🔍 QA 검증 결과")
            print("="*60)
            print(f"맥 시뮬레이션: {'실행 중' if status['mac_simulation']['running'] else '중지'}")
            print(f"Windows 연결: {status['windows_connection']['status']}")
            print(f"시뮬레이션 기간: {simulation_results.get('duration', 'N/A')}")
            print(f"거래 횟수: {simulation_results.get('trade_count', 0)}회")
            print(f"수익률: {simulation_results.get('profit_rate', 0):.2f}%")
            print(f"최대 손실: {simulation_results.get('max_loss', 0):.2f}%")
            print("="*60)
            
            # 거래 승인 옵션 제공
            print("\n거래 승인 옵션:")
            print("1) 전체 거래 승인 - 모든 시뮬레이션 거래를 실제로 실행")
            print("2) 선택적 거래 승인 - 승인할 거래를 선택")
            print("3) 거래 취소 - 실제 거래 실행하지 않음")
            print("4) 추가 시뮬레이션 - 더 오래 시뮬레이션 실행")
            
            user_choice = input("\n선택하세요 (1-4): ").strip()
            
            if user_choice == "1":
                # 전체 거래 승인
                logger.info("4️⃣ 전체 거래 승인 - Windows 실제 거래 시작")
                if not self.approve_all_trades(strategy_config):
                    logger.error("❌ 전체 거래 승인 실패")
                    return False
                logger.info("✅ QA 프로세스 완료 - 전체 거래 승인됨")
                return True
                
            elif user_choice == "2":
                # 선택적 거래 승인
                logger.info("4️⃣ 선택적 거래 승인")
                if not self.approve_selected_trades(strategy_config):
                    logger.error("❌ 선택적 거래 승인 실패")
                    return False
                logger.info("✅ QA 프로세스 완료 - 선택적 거래 승인됨")
                return True
                
            elif user_choice == "3":
                # 거래 취소
                logger.info("✅ QA 프로세스 완료 - 거래 취소됨")
                return True
                
            elif user_choice == "4":
                # 추가 시뮬레이션
                additional_time = input("추가 시뮬레이션 시간(초): ").strip()
                try:
                    additional_seconds = int(additional_time)
                    logger.info(f"⏳ 추가 시뮬레이션 실행 중... ({additional_seconds}초)")
                    time.sleep(additional_seconds)
                    
                    # 다시 QA 프로세스 실행
                    return self.run_qa_process(strategy_config)
                except ValueError:
                    logger.error("❌ 잘못된 시간 입력")
                    return False
            else:
                logger.error("❌ 잘못된 선택")
                return False
                
        except Exception as e:
            logger.error(f"❌ QA 프로세스 오류: {e}")
            return False

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="맥 하이브리드 제어 시스템")
    parser.add_argument("--action", choices=["simulation", "sync", "start-windows", "stop-windows", "qa", "status"], 
                       default="qa", help="실행할 액션")
    parser.add_argument("--config", help="전략 설정 파일 경로")
    parser.add_argument("--strategy", choices=["moving_average", "rsi", "bollinger"], 
                       default="moving_average", help="거래 전략")
    
    args = parser.parse_args()
    
    # 전략 설정 로드
    strategy_config = None
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                strategy_config = json.load(f)
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return
    
    if not strategy_config:
        strategy_config = {
            "type": args.strategy,
            "short_period": 5,
            "long_period": 20,
            "trade_amount": 100000,
            "watch_stocks": [
                {"code": "005930", "name": "삼성전자"},
                {"code": "000660", "name": "SK하이닉스"},
                {"code": "035420", "name": "NAVER"}
            ]
        }
    
    controller = MacHybridController()
    
    try:
        if args.action == "simulation":
            controller.start_simulation(strategy_config)
            
        elif args.action == "sync":
            controller.sync_to_windows(strategy_config)
            
        elif args.action == "start-windows":
            controller.start_windows_trading(strategy_config)
            
        elif args.action == "stop-windows":
            controller.stop_windows_trading()
            
        elif args.action == "qa":
            controller.run_qa_process(strategy_config)
            
        elif args.action == "status":
            status = controller.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        controller.stop_simulation()
    except Exception as e:
        logger.error(f"실행 오류: {e}")

if __name__ == "__main__":
    main() 