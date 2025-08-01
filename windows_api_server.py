#!/usr/bin/env python3
"""
Windows API 서버
맥에서 전송하는 거래 명령을 받아 실제 키움 API로 실행
"""

import sys
import os
import time
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger

# 로그 설정
logger.add("logs/windows_api_server.log", rotation="1 day", retention="7 days")

app = Flask(__name__)
CORS(app)  # 맥에서 접근 허용

class WindowsTradingServer:
    """Windows 거래 서버"""
    
    def __init__(self):
        self.trading_status = "stopped"
        self.current_trader = None
        self.api_key = "your_api_key_here"  # 실제 사용시 변경
        
        # 키움 API 초기화
        self.kiwoom_api = None
        try:
            from kiwoom_api import KiwoomAPI
            self.kiwoom_api = KiwoomAPI()
            logger.info("키움 API 초기화 완료")
        except Exception as e:
            logger.error(f"키움 API 초기화 실패: {e}")
    
    def authenticate_request(self, request):
        """요청 인증"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return False
        
        try:
            token = auth_header.split(' ')[1]
            return token == self.api_key
        except:
            return False
    
    def start_trading(self, strategy_config):
        """거래 시작"""
        try:
            if self.trading_status == "running":
                return {"success": False, "message": "이미 거래가 실행 중입니다."}
            
            # 키움 API 로그인
            if not self.kiwoom_api or not self.kiwoom_api.login():
                return {"success": False, "message": "키움 API 로그인 실패"}
            
            # 자동매매 시스템 시작
            from auto_trader import AutoTrader
            
            strategy_type = strategy_config.get("type", "moving_average")
            self.current_trader = AutoTrader(strategy_type=strategy_type, **(strategy_config or {}))
            
            # 모니터링 종목 추가
            watch_stocks = strategy_config.get("watch_stocks", [])
            for stock in watch_stocks:
                self.current_trader.add_watch_stock(stock["code"], stock.get("name", ""))
            
            # 별도 스레드에서 거래 실행
            trading_thread = threading.Thread(target=self._run_trading)
            trading_thread.daemon = True
            trading_thread.start()
            
            self.trading_status = "running"
            logger.info("거래 시작 완료")
            
            return {"success": True, "message": "거래가 시작되었습니다."}
            
        except Exception as e:
            logger.error(f"거래 시작 실패: {e}")
            return {"success": False, "message": f"거래 시작 실패: {str(e)}"}
    
    def stop_trading(self):
        """거래 중지"""
        try:
            if self.trading_status == "stopped":
                return {"success": False, "message": "거래가 이미 중지되었습니다."}
            
            if self.current_trader:
                self.current_trader.stop_trading()
                self.current_trader = None
            
            self.trading_status = "stopped"
            logger.info("거래 중지 완료")
            
            return {"success": True, "message": "거래가 중지되었습니다."}
            
        except Exception as e:
            logger.error(f"거래 중지 실패: {e}")
            return {"success": False, "message": f"거래 중지 실패: {str(e)}"}
    
    def _run_trading(self):
        """거래 실행 (별도 스레드)"""
        try:
            if self.current_trader:
                self.current_trader.start_trading()
        except Exception as e:
            logger.error(f"거래 실행 중 오류: {e}")
            self.trading_status = "error"
    
    def get_status(self):
        """서버 상태 조회"""
        try:
            # 키움 API 연결 상태 확인
            api_status = "disconnected"
            if self.kiwoom_api:
                connect_state = self.kiwoom_api.GetConnectState()
                api_status = "connected" if connect_state == 1 else "disconnected"
            
            # 계좌 정보 조회
            account_info = {}
            if self.kiwoom_api and api_status == "connected":
                account_info = self.kiwoom_api.get_account_info()
            
            return {
                "server_status": "running",
                "trading_status": self.trading_status,
                "api_status": api_status,
                "account_count": len(account_info),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {
                "server_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_account_info(self):
        """계좌 정보 조회"""
        try:
            if not self.kiwoom_api:
                return {"success": False, "message": "키움 API가 초기화되지 않았습니다."}
            
            account_info = self.kiwoom_api.get_account_info()
            return {"success": True, "data": account_info}
            
        except Exception as e:
            logger.error(f"계좌 정보 조회 실패: {e}")
            return {"success": False, "message": str(e)}
    
    def get_deposit_info(self, account):
        """예수금 정보 조회"""
        try:
            if not self.kiwoom_api:
                return {"success": False, "message": "키움 API가 초기화되지 않았습니다."}
            
            deposit_info = self.kiwoom_api.get_deposit_info(account)
            return {"success": True, "data": deposit_info}
            
        except Exception as e:
            logger.error(f"예수금 정보 조회 실패: {e}")
            return {"success": False, "message": str(e)}
    
    def sync_simulation_data(self, simulation_data):
        """맥 시뮬레이션 데이터 동기화"""
        try:
            logger.info("맥 시뮬레이션 데이터 동기화 시작")
            
            # 시뮬레이션 데이터 검증
            if not simulation_data or "simulation_data" not in simulation_data:
                return {"success": False, "message": "유효하지 않은 시뮬레이션 데이터"}
            
            sim_data = simulation_data["simulation_data"]
            
            # 계좌 정보 동기화
            if "account_info" in sim_data:
                logger.info(f"계좌 정보 동기화: {sim_data['account_info']}")
            
            # 예수금 정보 동기화
            if "deposit_info" in sim_data:
                logger.info(f"예수금 정보 동기화: {sim_data['deposit_info']}")
            
            # 전략 설정 동기화
            if "strategy_config" in sim_data:
                logger.info(f"전략 설정 동기화: {sim_data['strategy_config']}")
            
            # 거래 이력 동기화
            if "trade_history" in sim_data:
                logger.info(f"거래 이력 동기화: {len(sim_data['trade_history'])}건")
            
            # 현재 포지션 동기화
            if "current_positions" in sim_data:
                logger.info(f"현재 포지션 동기화: {sim_data['current_positions']}")
            
            logger.info("맥 시뮬레이션 데이터 동기화 완료")
            return {"success": True, "message": "시뮬레이션 데이터 동기화 완료"}
            
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 동기화 실패: {e}")
            return {"success": False, "message": str(e)}
    
    def approve_trades(self, approval_data):
        """맥에서 승인된 거래 실행"""
        try:
            logger.info("맥에서 승인된 거래 실행 시작")
            
            # 승인 데이터 검증
            if not approval_data:
                return {"success": False, "message": "유효하지 않은 승인 데이터"}
            
            approval_type = approval_data.get("approval_type")
            strategy_config = approval_data.get("strategy_config", {})
            
            if approval_type == "all_trades":
                # 전체 거래 승인 - 자동매매 시스템 시작
                logger.info("전체 거래 승인 - 자동매매 시스템 시작")
                result = self.start_trading(strategy_config)
                return result
                
            elif approval_type == "selected_trades":
                # 선택적 거래 승인 - 개별 주문 실행
                selected_trades = approval_data.get("selected_trades", [])
                logger.info(f"선택적 거래 승인 - {len(selected_trades)}건 실행")
                
                if not self.kiwoom_api:
                    return {"success": False, "message": "키움 API가 초기화되지 않았습니다."}
                
                # 키움 API 로그인
                if not self.kiwoom_api.login():
                    return {"success": False, "message": "키움 API 로그인 실패"}
                
                # 계좌 정보 조회
                account_info = self.kiwoom_api.get_account_info()
                if not account_info:
                    return {"success": False, "message": "계좌 정보 조회 실패"}
                
                account = list(account_info.keys())[0]
                executed_trades = []
                failed_trades = []
                
                # 선택된 거래들을 실제로 실행
                for trade in selected_trades:
                    try:
                        code = trade.get("code")
                        action = trade.get("action")
                        quantity = trade.get("quantity", 0)
                        price = trade.get("price", 0)
                        
                        if action == "매수":
                            order_type = "신규매수"
                        elif action == "매도":
                            order_type = "신규매도"
                        else:
                            logger.warning(f"지원하지 않는 거래 유형: {action}")
                            failed_trades.append(trade)
                            continue
                        
                        # 실제 주문 실행
                        order_result = self.kiwoom_api.order_stock(
                            account=account,
                            code=code,
                            quantity=quantity,
                            price=price,
                            order_type=order_type
                        )
                        
                        if order_result:
                            executed_trades.append({
                                "trade": trade,
                                "order_result": order_result
                            })
                            logger.info(f"주문 실행 성공: {code} - {action} - {quantity}주")
                        else:
                            failed_trades.append(trade)
                            logger.error(f"주문 실행 실패: {code} - {action}")
                            
                    except Exception as e:
                        logger.error(f"거래 실행 오류: {trade} - {e}")
                        failed_trades.append(trade)
                
                # 실행 결과 반환
                result = {
                    "success": True,
                    "message": f"선택적 거래 실행 완료 - 성공: {len(executed_trades)}건, 실패: {len(failed_trades)}건",
                    "executed_trades": executed_trades,
                    "failed_trades": failed_trades
                }
                
                logger.info(f"선택적 거래 실행 완료: {result['message']}")
                return result
                
            else:
                return {"success": False, "message": f"지원하지 않는 승인 유형: {approval_type}"}
                
        except Exception as e:
            logger.error(f"거래 승인 실행 실패: {e}")
            return {"success": False, "message": str(e)}

# 전역 서버 인스턴스
trading_server = WindowsTradingServer()

@app.route('/api/status', methods=['GET'])
def get_status():
    """서버 상태 조회 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    status = trading_server.get_status()
    return jsonify(status)

@app.route('/api/trading', methods=['POST'])
def trading_command():
    """거래 명령 처리 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    try:
        data = request.get_json()
        action = data.get("action")
        
        if action == "start":
            strategy_config = data.get("strategy_config", {})
            result = trading_server.start_trading(strategy_config)
            return jsonify(result)
        
        elif action == "stop":
            result = trading_server.stop_trading()
            return jsonify(result)
        
        elif action == "start_trading":  # 이전 버전 호환성
            strategy_config = data.get("strategy_config", {})
            result = trading_server.start_trading(strategy_config)
            return jsonify(result)
        
        elif action == "stop_trading":  # 이전 버전 호환성
            result = trading_server.stop_trading()
            return jsonify(result)
        
        else:
            return jsonify({"success": False, "message": f"지원하지 않는 액션: {action}"}), 400
            
    except Exception as e:
        logger.error(f"거래 명령 처리 실패: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    """계좌 정보 조회 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    result = trading_server.get_account_info()
    return jsonify(result)

@app.route('/api/deposit/<account>', methods=['GET'])
def get_deposit(account):
    """예수금 정보 조회 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    result = trading_server.get_deposit_info(account)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크 API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/sync', methods=['POST'])
def sync_simulation():
    """맥 시뮬레이션 데이터 동기화 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    try:
        simulation_data = request.get_json()
        result = trading_server.sync_simulation_data(simulation_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"시뮬레이션 데이터 동기화 실패: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/approve-trades', methods=['POST'])
def approve_trades():
    """맥에서 승인된 거래 실행 API"""
    if not trading_server.authenticate_request(request):
        return jsonify({"error": "인증 실패"}), 401
    
    try:
        approval_data = request.get_json()
        result = trading_server.approve_trades(approval_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"거래 승인 실행 실패: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Windows API 서버")
    parser.add_argument("--host", default="localhost", help="서버 호스트")
    parser.add_argument("--port", type=int, default=8080, help="서버 포트")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    
    args = parser.parse_args()
    
    print("🚀 Windows API 서버 시작")
    print(f"호스트: {args.host}")
    print(f"포트: {args.port}")
    print("=" * 50)
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n⏹️ 서버 중지")
    except Exception as e:
        print(f"❌ 서버 실행 실패: {e}")

if __name__ == "__main__":
    main() 