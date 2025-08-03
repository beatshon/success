"""
크로스 플랫폼 실시간 데이 트레이딩 시스템
Windows: 실제 키움 API 사용
Mac: Mock API 시뮬레이션
"""

import platform
import sys
import time
import logging
import random
import numpy as np
import csv
import os
import requests
from datetime import datetime
from typing import List, Dict
from loguru import logger

# 로깅 설정 (INFO 레벨로 변경하여 깔끔한 출력)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# 텔레그램 설정 (실제 사용 시 토큰과 채팅 ID 입력 필요)
TELEGRAM_TOKEN = "7836338625:AAGYUMdBZF2gkqa2gEiVMkOVB-Ex1_wiZfM"
TELEGRAM_CHAT_ID = "8461829055"
TELEGRAM_ENABLED = True  # 텔레그램 알림 활성화

if platform.system() == "Windows":
    try:
        from PyQt5.QAxContainer import QAxWidget
        from PyQt5.QtWidgets import QApplication
        WINDOWS_ENV = True
    except ImportError:
        logging.error("PyQt5.QAxContainer 모듈을 찾을 수 없습니다. Windows 환경에서 설치하세요.")
        sys.exit(1)
else:
    WINDOWS_ENV = False

    class MockQAxWidget:
        def __init__(self):
            self.stock_data = self._generate_sample_data()
            
        def _generate_sample_data(self):
            """샘플 주식 데이터 생성"""
            sample_stocks = [
                "005930.KS", "000660.KS", "035420.KS", "051910.KS", "006400.KS",
                "035720.KS", "068270.KS", "323410.KQ", "096770.KQ", "090430.KQ",
                "028260.KQ", "251270.KQ", "034220.KS", "011170.KS", "005380.KS"
            ]
            data = {}
            for stock in sample_stocks:
                base_price = random.randint(20000, 150000)
                data[stock] = {
                    "현재가": base_price,
                    "거래량": random.randint(1000, 100000),
                    "전일대비": random.uniform(-5.0, 5.0),
                    "시가": base_price * 0.98,
                    "고가": base_price * 1.05,
                    "저가": base_price * 0.95
                }
            return data
            
        def dynamicCall(self, func, args=None):
            if args is None:
                args = []
            if isinstance(args, (list, tuple)):
                logging.debug(f"[Mock 실행] dynamicCall 호출: {func} | 인자 수: {len(args)}개, 값: {args}")
                if "SendOrder" in func and len(args) == 8:
                    # 매수/매도 주문 시뮬레이션
                    order_type = args[3]  # 1: 매수, 2: 매도
                    stock_code = args[4]
                    quantity = args[5]
                    price = args[6]
                    
                    if order_type == 1:
                        logging.info(f"[Mock 매수] {stock_code} {quantity}주 @ {price:,}원")
                    else:
                        logging.info(f"[Mock 매도] {stock_code} {quantity}주 @ {price:,}원")
                    
                    return 0  # 성공
                elif "SendOrder" in func:
                    logging.error(f"[Mock ERROR] SendOrder 인수 부족: {len(args)}개, 필요: 8개")
                    return -1
                elif "GetMasterLastPrice" in func and len(args) == 1:
                    stock_code = args[0]
                    if stock_code in self.stock_data:
                        # 가격 변동 시뮬레이션 (더 큰 변동으로 매도 테스트)
                        current_price = self.stock_data[stock_code]["현재가"]
                        change = random.uniform(-0.10, 0.10)  # -10% ~ +10% 변동
                        new_price = current_price * (1 + change)
                        self.stock_data[stock_code]["현재가"] = new_price
                        return new_price
                    return random.randint(20000, 150000)
                else:
                    return None
            else:
                logging.error(f"[Mock ERROR] dynamicCall 인자가 리스트/튜플 아님: {args}")
                return -1

    class QApplication:
        def __init__(self, args):
            logging.info("[Mock 실행] QApplication 초기화")

        def exec_(self):
            logging.info("[Mock 실행] QApplication 루프 생략")
            return 0

    QAxWidget = MockQAxWidget


class TelegramNotifier:
    """텔레그램 알림 클래스"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.enabled = TELEGRAM_ENABLED and token != "YOUR_TELEGRAM_BOT_TOKEN"
        
    def send_message(self, message: str) -> bool:
        """텔레그램 메시지 전송"""
        if not self.enabled:
            logging.debug(f"[텔레그램] 비활성화됨: {message}")
            return True
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"[텔레그램] 메시지 전송 성공: {message[:50]}...")
                return True
            else:
                logging.error(f"[텔레그램] 메시지 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"[텔레그램] 메시지 전송 오류: {e}")
            return False
    
    def send_trade_notification(self, trade_type: str, stock_code: str, quantity: int, price: int, profit_rate: float = 0.0, balance: int = None):
        """매매 알림 전송"""
        if trade_type == "매수":
            if balance is not None:
                message = f"🟢 [매수] {stock_code} {quantity}주 @ {price:,}원 | 예수금 {balance:,}원"
            else:
                message = f"🟢 [매수] {stock_code} {quantity}주 @ {price:,}원"
        elif trade_type == "매도":
            if profit_rate > 0:
                message = f"🔴 [익절] {stock_code} {quantity}주 @ {price:,}원 (+{profit_rate:.2f}%)"
            elif profit_rate < 0:
                message = f"🔴 [손절] {stock_code} {quantity}주 @ {price:,}원 ({profit_rate:.2f}%)"
            else:
                message = f"🔴 [매도] {stock_code} {quantity}주 @ {price:,}원"
        else:
            message = f"📊 [{trade_type}] {stock_code} {quantity}주 @ {price:,}원"
            
        self.send_message(message)
    
    def send_error_notification(self, error_msg: str):
        """오류 알림 전송"""
        message = f"⚠️ [비상정지] 이유: {error_msg}"
        self.send_message(message)


class TradeLogger:
    """매매 로그 관리 클래스"""
    
    def __init__(self):
        self.log_dir = self._create_log_directory()
        self.buy_log_file = os.path.join(self.log_dir, "buy_log.csv")
        self.sell_log_file = os.path.join(self.log_dir, "sell_log.csv")
        self.error_log_file = os.path.join(self.log_dir, "error_log.csv")
        
        # CSV 헤더 초기화
        self._init_csv_files()
        
    def _create_log_directory(self) -> str:
        """날짜별 로그 디렉토리 생성"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_dir = os.path.join("logs", today)
        os.makedirs(log_dir, exist_ok=True)
        logging.info(f"로그 디렉토리 생성: {log_dir}")
        return log_dir
    
    def _init_csv_files(self):
        """CSV 파일 헤더 초기화"""
        # 매수 로그 헤더
        buy_headers = ["시간", "종목코드", "수량", "가격", "총액", "예수금", "보유종목수"]
        with open(self.buy_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(buy_headers)
        
        # 매도 로그 헤더
        sell_headers = ["시간", "종목코드", "수량", "가격", "총액", "수익률", "매도사유", "예수금", "보유종목수"]
        with open(self.sell_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(sell_headers)
        
        # 오류 로그 헤더
        error_headers = ["시간", "오류유형", "오류메시지", "상태"]
        with open(self.error_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(error_headers)
    
    def log_buy(self, stock_code: str, quantity: int, price: int, total_cost: int, 
                deposit: int, position_count: int):
        """매수 로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, stock_code, quantity, price, total_cost, deposit, position_count]
        
        with open(self.buy_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        logging.info(f"[매수로그] {stock_code} {quantity}주 @ {price:,}원 기록 완료")
    
    def log_sell(self, stock_code: str, quantity: int, price: int, total_revenue: int,
                 profit_rate: float, sell_reason: str, deposit: int, position_count: int):
        """매도 로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, stock_code, quantity, price, total_revenue, profit_rate, 
               sell_reason, deposit, position_count]
        
        with open(self.sell_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        logging.info(f"[매도로그] {stock_code} {quantity}주 @ {price:,}원 ({profit_rate:+.2f}%) 기록 완료")
    
    def log_error(self, error_type: str, error_message: str, status: str = "발생"):
        """오류 로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, error_type, error_message, status]
        
        with open(self.error_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        logging.error(f"[오류로그] {error_type}: {error_message} 기록 완료")


class KiwoomAPI:
    def __init__(self):
        if WINDOWS_ENV:
            self.app = QApplication(sys.argv)
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            self.is_connected = False
            logging.info("Windows 환경: 키움 API 컨트롤러 연결 완료")
        else:
            self.app = QApplication([])
            self.ocx = QAxWidget()
            self.is_connected = True
            logging.info("Mac 환경: Mock API 컨트롤러 사용")

    def login(self):
        if WINDOWS_ENV:
            ret = self.ocx.dynamicCall("CommConnect()")
            logging.info("Windows 환경: 로그인 요청 완료")
            time.sleep(2)  # 로그인 대기
            self.is_connected = True
        else:
            logging.info("[Mock 실행] 로그인 요청 시뮬레이션")
            self.is_connected = True

    def get_account_info(self):
        if WINDOWS_ENV and self.is_connected:
            acc_num = self.ocx.dynamicCall("GetLoginInfo(QString)", ["ACCNO"])
            user_id = self.ocx.dynamicCall("GetLoginInfo(QString)", ["USER_ID"])
            user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", ["USER_NAME"])
            logging.info(f"계좌번호: {acc_num}")
            return {
                "계좌번호": acc_num,
                "사용자ID": user_id,
                "사용자명": user_name
            }
        else:
            logging.info("[Mock 실행] 계좌정보 조회 시뮬레이션")
            return {
                "계좌번호": "1234567890",
                "사용자ID": "test_user",
                "사용자명": "테스트사용자"
            }

    def get_current_price(self, stock_code):
        """현재가 조회"""
        if WINDOWS_ENV and self.is_connected:
            price = self.ocx.dynamicCall("GetMasterLastPrice(QString)", [stock_code])
            return price
        else:
            if hasattr(self.ocx, 'stock_data') and stock_code in self.ocx.stock_data:
                return self.ocx.stock_data[stock_code]["현재가"]
            return random.randint(20000, 150000)

    def send_order(self, rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb):
        args = [rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb]
        return self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString)", args
        )


class AdvancedTradingStrategy:
    """고급 매매 전략 클래스"""
    
    def __init__(self):
        self.price_history = {}  # 종목별 가격 히스토리
        self.volume_history = {}  # 종목별 거래량 히스토리
        
    def update_price_history(self, stock_code: str, price: float, volume: int):
        """가격 및 거래량 히스토리 업데이트"""
        if stock_code not in self.price_history:
            self.price_history[stock_code] = []
            self.volume_history[stock_code] = []
            
        self.price_history[stock_code].append(price)
        self.volume_history[stock_code].append(volume)
        
        # 최대 50개 데이터 유지
        if len(self.price_history[stock_code]) > 50:
            self.price_history[stock_code] = self.price_history[stock_code][-50:]
            self.volume_history[stock_code] = self.volume_history[stock_code][-50:]
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_moving_averages(self, prices: List[float]) -> Dict[str, float]:
        """이동평균선 계산"""
        if len(prices) < 20:
            return {"ma5": prices[-1], "ma10": prices[-1], "ma20": prices[-1]}
            
        return {
            "ma5": sum(prices[-5:]) / 5,
            "ma10": sum(prices[-10:]) / 10,
            "ma20": sum(prices[-20:]) / 20
        }
    
    def calculate_volume_ratio(self, volumes: List[int]) -> float:
        """거래량 비율 계산 (최근 5일 평균 대비)"""
        if len(volumes) < 10:
            return 1.0
            
        recent_avg = sum(volumes[-5:]) / 5
        past_avg = sum(volumes[-10:-5]) / 5
        
        if past_avg == 0:
            return 1.0
            
        return recent_avg / past_avg
    
    def calculate_price_change(self, prices: List[float]) -> float:
        """가격 변화율 계산 (최근 5일 대비)"""
        if len(prices) < 6:
            return 1.0
            
        current_price = prices[-1]
        past_price = prices[-6]
        
        if past_price == 0:
            return 1.0
            
        return current_price / past_price
    
    def check_buy_signal(self, stock_code: str, current_price: float, current_volume: int) -> bool:
        """고급 매수 신호 확인"""
        try:
            # 히스토리 업데이트
            self.update_price_history(stock_code, current_price, current_volume)
            
            prices = self.price_history[stock_code]
            volumes = self.volume_history[stock_code]
            
            if len(prices) < 10:  # 20개에서 10개로 줄임
                return False
            
            # 기술적 지표 계산
            rsi = self.calculate_rsi(prices)
            ma_data = self.calculate_moving_averages(prices)
            volume_ratio = self.calculate_volume_ratio(volumes)
            price_change = self.calculate_price_change(prices)
            
            # 매수 조건 체크 (조건 완화)
            buy_conditions = [
                rsi >= 20 and rsi <= 80,  # RSI 20-80 범위로 확대
                current_price > ma_data["ma5"] * 0.98,  # 5일 이동평균선 근처
                volume_ratio >= 1.0,  # 거래량 조건 완화
                price_change >= 0.98,  # 가격 조건 완화
                current_price >= 10000  # 최소 가격 조건 완화
            ]
            
            # 조건 만족도 로깅
            logging.debug(f"매수 조건 체크: {stock_code}")
            logging.debug(f"  RSI: {rsi:.1f} (조건: 20-80), MA5: {ma_data['ma5']:.0f}")
            logging.debug(f"  거래량비: {volume_ratio:.2f} (조건: >=1.0), 가격변화: {price_change:.3f} (조건: >=0.98)")
            
            # 모든 조건 만족 시 매수 신호
            if all(buy_conditions):
                logging.info(f"매수 신호 발생: {stock_code}")
                logging.info(f"  RSI: {rsi:.1f}, MA5: {ma_data['ma5']:.0f}, MA10: {ma_data['ma10']:.0f}")
                logging.info(f"  거래량비: {volume_ratio:.2f}, 가격변화: {price_change:.3f}")
                return True
                
        except Exception as e:
            logging.error(f"매수 신호 확인 중 오류: {e}")
            
        return False
    
    def check_sell_signal(self, stock_code: str, current_price: float, avg_price: float) -> str:
        """매도 신호 확인"""
        try:
            profit_rate = ((current_price - avg_price) / avg_price) * 100
            
            # 매도 조건 로깅
            logging.debug(f"매도 조건 체크: {stock_code}, 수익률: {profit_rate:.2f}%")
            
            # 익절 조건 (3% 이상으로 완화)
            if profit_rate >= 3.0:
                logging.info(f"익절 신호: {stock_code}, 수익률: {profit_rate:.2f}%")
                return "익절"
            
            # 손절 조건 (-2% 이하로 완화)
            elif profit_rate <= -2.0:
                logging.info(f"손절 신호: {stock_code}, 수익률: {profit_rate:.2f}%")
                return "손절"
            
            # 추가 매도 조건 체크
            if stock_code in self.price_history:
                prices = self.price_history[stock_code]
                if len(prices) >= 10:
                    rsi = self.calculate_rsi(prices)
                    ma_data = self.calculate_moving_averages(prices)
                    
                    # RSI 과매수 (75 이상) 또는 이동평균선 하향 돌파
                    if rsi >= 75 or current_price < ma_data["ma5"] * 0.95:
                        logging.info(f"기술적 매도 신호: {stock_code}, RSI: {rsi:.1f}")
                        return "기술적매도"
            
        except Exception as e:
            logging.error(f"매도 신호 확인 중 오류: {e}")
            
        return ""


class RealtimeTrader:
    def __init__(self, api: KiwoomAPI, account: str):
        self.api = api
        self.account = account
        self.positions = {}  # 보유 종목
        self.account_info = {"예수금": 10000000}  # 초기 자금 1000만원
        self.running = False
        self.strategy = AdvancedTradingStrategy()
        
        # 로깅 및 알림 시스템 초기화
        self.logger = TradeLogger()
        self.telegram = TelegramNotifier(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        
        # 비상정지 플래그
        self.emergency_stop = False
        
    def initialize(self):
        """초기화"""
        account_info = self.api.get_account_info()
        logging.info(f"계좌 정보: {account_info}")
        logging.info(f"계좌 잔고: {self.account_info['예수금']:,}원")
        logging.info(f"보유 종목: {len(self.positions)}개")
        
        # 텔레그램 테스트 메시지 전송
        if self.telegram.enabled:
            self.telegram.send_message("🚀 크로스 플랫폼 트레이딩 시스템 시작\n"
                                     f"환경: {'Windows' if WINDOWS_ENV else 'Mac'}\n"
                                     f"계좌: {account_info['계좌번호']}\n"
                                     f"초기자금: {self.account_info['예수금']:,}원")
        
    def emergency_stop_trading(self, error_msg: str):
        """비상정지 실행"""
        logging.error(f"🚨 비상정지 실행: {error_msg}")
        self.emergency_stop = True
        
        # 오류 로그 기록
        self.logger.log_error("비상정지", error_msg, "실행")
        
        # 비상정지 리포트 전송
        self.emergency_report()
        
        # 텔레그램 알림 전송
        self.telegram.send_error_notification(f"비상정지 실행\n사유: {error_msg}")
        
        # 모든 포지션 청산
        self._close_all_positions("비상정지")
        
        logging.info("🚨 모든 포지션 청산 완료 및 시스템 종료")
        
    def emergency_report(self):
        """비상정지 리포트 생성 및 전송"""
        try:
            # 총 자산 계산
            total_value = self.account_info["예수금"]
            position_details = []
            
            for code, pos in self.positions.items():
                current_price = self.api.get_current_price(code)
                position_value = pos["shares"] * current_price
                total_value += position_value
                
                # 수익률 계산
                avg_price = pos["avg_price"]
                profit_rate = ((current_price - avg_price) / avg_price) * 100
                
                position_details.append(f"• {code}: {pos['shares']}주 @ {current_price:,}원 ({profit_rate:+.2f}%)")
            
            # 리포트 메시지 구성
            message = f"🚨 비상정지 리포트\n"
            message += f"총자산: {total_value:,}원\n"
            message += f"예수금: {self.account_info['예수금']:,}원\n"
            message += f"보유종목: {len(self.positions)}개\n"
            
            if position_details:
                message += f"\n보유종목 상세:\n"
                message += "\n".join(position_details)
            
            # 텔레그램 전송
            self.telegram.send_message(message)
            logging.info("비상정지 리포트 전송 완료")
            
        except Exception as e:
            logging.error(f"비상정지 리포트 생성 중 오류: {e}")
            # 간단한 리포트라도 전송
            try:
                simple_message = f"🚨 비상정지 리포트\n총자산: {self.account_info['예수금']:,}원\n보유종목: {len(self.positions)}개"
                self.telegram.send_message(simple_message)
            except:
                logging.error("간단한 비상정지 리포트 전송도 실패")
        
    def _close_all_positions(self, reason: str):
        """모든 포지션 청산"""
        for stock_code in list(self.positions.keys()):
            try:
                current_price = self.api.get_current_price(stock_code)
                quantity = self.positions[stock_code]["shares"]
                
                # 매도 주문
                result = self.api.send_order(
                    "매도", "0101", self.account, 2, 
                    stock_code, quantity, current_price, "00"
                )
                
                if result == 0:
                    # 매도 성공 시 포지션 업데이트
                    revenue = quantity * current_price
                    self.account_info["예수금"] += revenue
                    
                    # 수익률 계산
                    avg_price = self.positions[stock_code]["avg_price"]
                    profit_rate = ((current_price - avg_price) / avg_price) * 100
                    
                    logging.info(f"[{reason}] {stock_code} {quantity}주 @ {current_price:,}원 ({profit_rate:+.2f}%)")
                    
                    # 로그 기록
                    self.logger.log_sell(stock_code, quantity, current_price, revenue,
                                       profit_rate, reason, self.account_info["예수금"], len(self.positions))
                    
                    # 텔레그램 알림
                    self.telegram.send_trade_notification("매도", stock_code, quantity, current_price, profit_rate)
                    
                    del self.positions[stock_code]
                    
            except Exception as e:
                logging.error(f"포지션 청산 중 오류 ({stock_code}): {e}")
                self.logger.log_error("포지션청산", f"{stock_code}: {e}", "실패")
        
    def execute_buy(self, stock_code: str):
        """매수 실행"""
        try:
            if self.emergency_stop:
                return False
                
            current_price = self.api.get_current_price(stock_code)
            available_money = self.account_info["예수금"]
            
            # 최대 매수 가능 수량 계산 (수수료 고려)
            max_quantity = int(available_money * 0.95 / current_price)
            
            if max_quantity > 0:
                # 매수 수량 결정 (1-10주)
                quantity = min(max_quantity, random.randint(1, 10))
                
                # 매수 주문
                result = self.api.send_order(
                    "매수", "0101", self.account, 1, 
                    stock_code, quantity, current_price, "00"
                )
                
                if result == 0:
                    # 매수 성공 시 포지션 업데이트
                    cost = quantity * current_price
                    self.account_info["예수금"] -= cost
                    
                    if stock_code not in self.positions:
                        self.positions[stock_code] = {"shares": 0, "avg_price": 0}
                    
                    # 평균 매수가 계산
                    total_shares = self.positions[stock_code]["shares"] + quantity
                    total_cost = (self.positions[stock_code]["shares"] * self.positions[stock_code]["avg_price"]) + cost
                    self.positions[stock_code]["avg_price"] = total_cost / total_shares
                    self.positions[stock_code]["shares"] = total_shares
                    
                    logging.info(f"[매수] {stock_code} {quantity}주 @ {current_price:,}원")
                    
                    # 로그 기록
                    self.logger.log_buy(stock_code, quantity, current_price, cost,
                                      self.account_info["예수금"], len(self.positions))
                    
                    # 텔레그램 알림
                    self.telegram.send_trade_notification("매수", stock_code, quantity, current_price, balance=self.account_info["예수금"])
                    
                    return True
                else:
                    logging.error(f"매수 주문 실패: {stock_code}")
                    self.logger.log_error("매수주문실패", f"{stock_code}: 주문 실패", "실패")
                    
        except Exception as e:
            logging.error(f"매수 실행 중 오류: {e}")
            self.logger.log_error("매수실행오류", f"{stock_code}: {e}", "발생")
            
        return False
        
    def execute_sell(self, stock_code: str, reason: str = "익절"):
        """매도 실행"""
        try:
            if self.emergency_stop:
                return False
                
            if stock_code in self.positions and self.positions[stock_code]["shares"] > 0:
                current_price = self.api.get_current_price(stock_code)
                quantity = self.positions[stock_code]["shares"]
                
                # 매도 주문
                result = self.api.send_order(
                    "매도", "0101", self.account, 2, 
                    stock_code, quantity, current_price, "00"
                )
                
                if result == 0:
                    # 매도 성공 시 포지션 업데이트
                    revenue = quantity * current_price
                    self.account_info["예수금"] += revenue
                    
                    # 수익률 계산
                    avg_price = self.positions[stock_code]["avg_price"]
                    profit_rate = ((current_price - avg_price) / avg_price) * 100
                    
                    logging.info(f"[{reason}] {stock_code} {quantity}주 @ {current_price:,}원 ({profit_rate:+.2f}%)")
                    
                    # 로그 기록
                    self.logger.log_sell(stock_code, quantity, current_price, revenue,
                                       profit_rate, reason, self.account_info["예수금"], len(self.positions))
                    
                    # 텔레그램 알림
                    self.telegram.send_trade_notification("매도", stock_code, quantity, current_price, profit_rate)
                    
                    del self.positions[stock_code]
                    return True
                else:
                    logging.error(f"매도 주문 실패: {stock_code}")
                    self.logger.log_error("매도주문실패", f"{stock_code}: 주문 실패", "실패")
                    
        except Exception as e:
            logging.error(f"매도 실행 중 오류: {e}")
            self.logger.log_error("매도실행오류", f"{stock_code}: {e}", "발생")
            
        return False
        
    def trading_loop(self, max_iterations=20):
        """트레이딩 루프"""
        iteration = 0
        while self.running and not self.emergency_stop:
            iteration += 1

            try:
                # 매수 신호 확인 (고급 전략 사용)
                for stock_code in ["005930.KS", "000660.KS", "035420.KS"]:
                    if self.emergency_stop:
                        break
                        
                    if stock_code not in self.positions:  # 보유하지 않은 종목만
                        current_price = self.api.get_current_price(stock_code)
                        current_volume = random.randint(1000, 100000)  # Mock 거래량
                        
                        if self.strategy.check_buy_signal(stock_code, current_price, current_volume):
                            self.execute_buy(stock_code)
                            break

                # 보유 종목 매도 검토 (고급 전략 사용)
                for stock_code in list(self.positions.keys()):
                    if self.emergency_stop:
                        break
                        
                    current_price = self.api.get_current_price(stock_code)
                    avg_price = self.positions[stock_code]["avg_price"]
                    
                    # 매도 신호 확인
                    sell_reason = self.strategy.check_sell_signal(stock_code, current_price, avg_price)
                    if sell_reason:
                        self.execute_sell(stock_code, sell_reason)

                if iteration % 5 == 0:
                    self._print_stats()

                # Mock 환경 반복 제한
                if not WINDOWS_ENV and iteration >= max_iterations:
                    logging.info("[Mock 실행] 테스트 반복 종료")
                    break

                time.sleep(0.1 if not WINDOWS_ENV else 1)

            except Exception as e:
                logging.error(f"트레이딩 루프 오류: {e}")
                self.logger.log_error("트레이딩루프오류", str(e), "발생")
                self.emergency_stop_trading(f"트레이딩 루프 오류: {e}")
                break
                
    def _print_stats(self):
        """통계 출력"""
        total_value = self.account_info["예수금"]
        for stock_code, position in self.positions.items():
            current_price = self.api.get_current_price(stock_code)
            total_value += position["shares"] * current_price
            
        logging.info(f"총 자산: {total_value:,}원 | 보유 종목: {len(self.positions)}개 | 예수금: {self.account_info['예수금']:,}원")
        
    def start(self):
        """트레이딩 시작"""
        self.running = True
        logging.info("크로스 플랫폼 실시간 트레이딩 시작")
        self.trading_loop()
        
    def stop(self):
        """트레이딩 중지"""
        self.running = False
        logging.info("크로스 플랫폼 실시간 트레이딩 중지")

    def daily_summary(self):
        """일일 매매 요약 리포트 생성 및 전송"""
        try:
            from datetime import datetime
            import pandas as pd
            
            today = datetime.now().strftime('%Y-%m-%d')
            folder = f'logs/{today}'
            
            # 로그 폴더가 없으면 매매 내역 없음 메시지 전송
            if not os.path.exists(folder):
                self.telegram.send_message(f"📊 {today} 매매 내역 없음")
                logging.info("매매 내역 없음 - 일일 요약 전송 완료")
                return
            
            summary_msg = [f"📊 {today} 매매 요약"]
            
            # 매수 로그 분석
            buy_file = os.path.join(folder, "buy_log.csv")
            if os.path.exists(buy_file):
                buy_df = pd.read_csv(buy_file)
                summary_msg.append(f"🟢 매수: {len(buy_df)}건, 총 {buy_df['총액'].sum():,}원")
            else:
                summary_msg.append("🟢 매수: 없음")
            
            # 매도 로그 분석
            sell_file = os.path.join(folder, "sell_log.csv")
            if os.path.exists(sell_file):
                sell_df = pd.read_csv(sell_file)
                if not sell_df.empty:
                    avg_profit = sell_df['수익률'].mean()
                    summary_msg.append(f"🔴 매도: {len(sell_df)}건, 평균 수익률 {avg_profit:.2f}%")
                else:
                    summary_msg.append("🔴 매도: 없음")
            else:
                summary_msg.append("🔴 매도: 없음")
            
            # 오류 로그 분석
            error_file = os.path.join(folder, "error_log.csv")
            if os.path.exists(error_file):
                error_df = pd.read_csv(error_file)
                summary_msg.append(f"⚠️ 오류: {len(error_df)}건 발생")
            else:
                summary_msg.append("⚠️ 오류: 없음")
            
            # 현재 자산 현황 추가
            current_balance = self.account_info["예수금"]
            total_positions = len(self.positions)
            summary_msg.append(f"💰 현재 예수금: {current_balance:,}원")
            summary_msg.append(f"📈 보유종목: {total_positions}개")
            
            # 텔레그램 전송
            final_message = "\n".join(summary_msg)
            self.telegram.send_message(final_message)
            logging.info("일일 요약 리포트 전송 완료")
            
        except Exception as e:
            logging.error(f"일일 요약 리포트 생성 중 오류: {e}")
            # 간단한 요약이라도 전송
            try:
                simple_summary = f"📊 {datetime.now().strftime('%Y-%m-%d')} 일일 요약\n매수: {buy_count if 'buy_count' in locals() else 0}건\n매도: {sell_count if 'sell_count' in locals() else 0}건\n예수금: {self.account_info['예수금']:,}원"
                self.telegram.send_message(simple_summary)
            except:
                logging.error("간단한 일일 요약 전송도 실패")


def main():
    """메인 함수"""
    import argparse
    
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='크로스 플랫폼 트레이딩 시스템')
    parser.add_argument('--daily-summary', action='store_true', 
                       help='일일 요약 리포트만 생성하고 종료')
    parser.add_argument('--emergency-stop', action='store_true',
                       help='비상정지 테스트 실행')
    parser.add_argument('--test', action='store_true',
                       help='테스트 모드로 실행')
    
    args = parser.parse_args()
    
    # 일일 요약만 실행
    if args.daily_summary:
        print("📊 일일 요약 리포트 생성")
        print("=" * 50)
        
        try:
            # API 초기화
            api = KiwoomAPI()
            api.login()
            
            # 계좌 정보 조회
            account_info = api.get_account_info()
            account = account_info["계좌번호"]
            
            # 트레이더 초기화
            trader = RealtimeTrader(api, account)
            trader.initialize()
            
            # 일일 요약 생성 및 전송
            trader.daily_summary()
            
            print("✅ 일일 요약 리포트 전송 완료!")
            
        except Exception as e:
            logging.error(f"일일 요약 실행 중 오류: {e}")
            print(f"❌ 일일 요약 실행 실패: {e}")
        
        return
    
    # 비상정지 테스트
    if args.emergency_stop:
        print("🚨 비상정지 테스트 실행")
        print("=" * 50)
        
        try:
            # API 초기화
            api = KiwoomAPI()
            api.login()
            
            # 계좌 정보 조회
            account_info = api.get_account_info()
            account = account_info["계좌번호"]
            
            # 트레이더 초기화
            trader = RealtimeTrader(api, account)
            trader.initialize()
            
            # 비상정지 테스트
            trader.emergency_stop_trading("테스트용 비상정지")
            
            print("✅ 비상정지 테스트 완료!")
            
        except Exception as e:
            logging.error(f"비상정지 테스트 중 오류: {e}")
            print(f"❌ 비상정지 테스트 실패: {e}")
        
        return
    
    # 일반 트레이딩 실행
    print("🚀 크로스 플랫폼 트레이딩 시스템 시작")
    print("=" * 50)
    
    try:
        # API 초기화
        api = KiwoomAPI()
        api.login()
        
        # 계좌 정보 조회
        account_info = api.get_account_info()
        account = account_info["계좌번호"]
        
        # 트레이더 초기화 및 실행
        trader = RealtimeTrader(api, account)
        trader.initialize()
        
        if args.test:
            print("🧪 테스트 모드로 실행")
            trader.trading_loop(max_iterations=5)
        else:
            trader.trading_loop()
            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중지됨")
    except Exception as e:
        logging.error(f"트레이딩 시스템 실행 중 오류: {e}")
        print(f"❌ 시스템 오류: {e}")


if __name__ == "__main__":
    main() 