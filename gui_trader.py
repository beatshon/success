"""
GUI 기반 자동매매 프로그램
PyQt5를 사용한 사용자 친화적인 인터페이스
"""

import sys
import time
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from loguru import logger
import pandas as pd

from kiwoom_api import KiwoomAPI
from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy
from auto_trader import AutoTrader

class TradingGUI(QMainWindow):
    """자동매매 GUI 클래스"""
    
    def __init__(self):
        super().__init__()
        self.trader = None
        self.api = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle('키움증권 자동매매 시스템')
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QHBoxLayout()
        central_widget.setLayout(layout)
        
        # 왼쪽 패널 (설정)
        left_panel = self.create_left_panel()
        layout.addWidget(left_panel, 1)
        
        # 오른쪽 패널 (모니터링)
        right_panel = self.create_right_panel()
        layout.addWidget(right_panel, 2)
        
        # 상태바
        self.statusBar().showMessage('시스템 준비')
        
    def create_left_panel(self):
        """왼쪽 설정 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # 로그인 그룹
        login_group = QGroupBox("로그인")
        login_layout = QVBoxLayout()
        
        self.login_btn = QPushButton("로그인")
        self.login_btn.clicked.connect(self.login)
        login_layout.addWidget(self.login_btn)
        
        self.login_status_label = QLabel("로그인 상태: 미로그인")
        login_layout.addWidget(self.login_status_label)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # 전략 설정 그룹
        strategy_group = QGroupBox("매매 전략")
        strategy_layout = QVBoxLayout()
        
        # 전략 선택
        strategy_layout.addWidget(QLabel("전략 선택:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["이동평균", "RSI", "볼린저밴드"])
        strategy_layout.addWidget(self.strategy_combo)
        
        # 전략 파라미터
        self.param_widget = QWidget()
        self.param_layout = QFormLayout()
        self.param_widget.setLayout(self.param_layout)
        strategy_layout.addWidget(self.param_widget)
        
        self.update_strategy_params()
        self.strategy_combo.currentTextChanged.connect(self.update_strategy_params)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        # 거래 설정 그룹
        trade_group = QGroupBox("거래 설정")
        trade_layout = QFormLayout()
        
        self.trade_amount_edit = QLineEdit("100000")
        trade_layout.addRow("거래 금액 (원):", self.trade_amount_edit)
        
        self.max_positions_edit = QLineEdit("5")
        trade_layout.addRow("최대 보유 종목:", self.max_positions_edit)
        
        self.interval_edit = QLineEdit("60")
        trade_layout.addRow("실행 주기 (초):", self.interval_edit)
        
        trade_group.setLayout(trade_layout)
        layout.addWidget(trade_group)
        
        # 종목 관리 그룹
        stock_group = QGroupBox("종목 관리")
        stock_layout = QVBoxLayout()
        
        # 종목 추가
        add_layout = QHBoxLayout()
        self.stock_code_edit = QLineEdit()
        self.stock_code_edit.setPlaceholderText("종목코드 (예: 005930)")
        add_layout.addWidget(self.stock_code_edit)
        
        self.add_stock_btn = QPushButton("추가")
        self.add_stock_btn.clicked.connect(self.add_watch_stock)
        add_layout.addWidget(self.add_stock_btn)
        
        stock_layout.addLayout(add_layout)
        
        # 종목 리스트
        self.stock_list = QListWidget()
        stock_layout.addWidget(self.stock_list)
        
        # 종목 제거
        self.remove_stock_btn = QPushButton("선택 종목 제거")
        self.remove_stock_btn.clicked.connect(self.remove_watch_stock)
        stock_layout.addWidget(self.remove_stock_btn)
        
        stock_group.setLayout(stock_layout)
        layout.addWidget(stock_group)
        
        # 제어 버튼
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("자동매매 시작")
        self.start_btn.clicked.connect(self.start_trading)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("자동매매 중지")
        self.stop_btn.clicked.connect(self.stop_trading)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self):
        """오른쪽 모니터링 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # 탭 위젯
        tab_widget = QTabWidget()
        
        # 실시간 모니터링 탭
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout()
        
        # 종목별 정보 테이블
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "현재가", "등락률", "거래량", "상태"
        ])
        monitor_layout.addWidget(self.stock_table)
        
        monitor_tab.setLayout(monitor_layout)
        tab_widget.addTab(monitor_tab, "실시간 모니터링")
        
        # 거래 내역 탭
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "시간", "종목코드", "종목명", "매매구분", "수량", "가격", "주문번호"
        ])
        history_layout.addWidget(self.history_table)
        
        history_tab.setLayout(history_layout)
        tab_widget.addTab(history_tab, "거래 내역")
        
        # 로그 탭
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_tab.setLayout(log_layout)
        tab_widget.addTab(log_tab, "로그")
        
        layout.addWidget(tab_widget)
        
        # 상태 정보
        status_layout = QHBoxLayout()
        
        self.total_trades_label = QLabel("총 거래: 0")
        status_layout.addWidget(self.total_trades_label)
        
        self.buy_trades_label = QLabel("매수: 0")
        status_layout.addWidget(self.buy_trades_label)
        
        self.sell_trades_label = QLabel("매도: 0")
        status_layout.addWidget(self.sell_trades_label)
        
        self.positions_label = QLabel("보유종목: 0")
        status_layout.addWidget(self.positions_label)
        
        layout.addLayout(status_layout)
        
        return panel
    
    def update_strategy_params(self):
        """전략 파라미터 UI 업데이트"""
        # 기존 위젯들 제거
        for i in reversed(range(self.param_layout.count())):
            self.param_layout.itemAt(i).widget().setParent(None)
        
        strategy = self.strategy_combo.currentText()
        
        if strategy == "이동평균":
            self.short_period_edit = QLineEdit("5")
            self.long_period_edit = QLineEdit("20")
            self.param_layout.addRow("단기 기간:", self.short_period_edit)
            self.param_layout.addRow("장기 기간:", self.long_period_edit)
            
        elif strategy == "RSI":
            self.rsi_period_edit = QLineEdit("14")
            self.oversold_edit = QLineEdit("30")
            self.overbought_edit = QLineEdit("70")
            self.param_layout.addRow("RSI 기간:", self.rsi_period_edit)
            self.param_layout.addRow("과매도 기준:", self.oversold_edit)
            self.param_layout.addRow("과매수 기준:", self.overbought_edit)
            
        elif strategy == "볼린저밴드":
            self.bb_period_edit = QLineEdit("20")
            self.std_dev_edit = QLineEdit("2")
            self.param_layout.addRow("기간:", self.bb_period_edit)
            self.param_layout.addRow("표준편차:", self.std_dev_edit)
    
    def login(self):
        """로그인"""
        try:
            self.api = KiwoomAPI()
            
            # 콜백 함수 설정
            self.api.set_login_callback(self.on_login_complete)
            self.api.set_real_data_callback(self.on_real_data_received)
            self.api.set_order_callback(self.on_order_complete)
            
            # 로그인 시도
            if self.api.login(timeout=30):
                self.log_message("로그인 성공")
            else:
                self.log_message("로그인 실패")
                
        except Exception as e:
            self.log_message(f"로그인 오류: {e}")
    
    def on_login_complete(self, success):
        """로그인 완료 콜백"""
        if success:
            self.login_status_label.setText("로그인 상태: 로그인됨")
            self.start_btn.setEnabled(True)
            self.statusBar().showMessage('로그인 성공')
            self.log_message("로그인 성공")
            
            # 계좌 정보 조회
            try:
                account_info = self.api.get_account_info()
                if account_info:
                    self.log_message(f"계좌 정보 조회 완료: {len(account_info)}개")
                    # 첫 번째 계좌를 기본 계좌로 설정
                    self.default_account = list(account_info.keys())[0]
                    self.log_message(f"기본 계좌: {self.default_account}")
            except Exception as e:
                self.log_message(f"계좌 정보 조회 오류: {e}")
        else:
            self.login_status_label.setText("로그인 상태: 실패")
            self.statusBar().showMessage('로그인 실패')
            self.log_message("로그인 실패")
    
    def on_real_data_received(self, code, data):
        """실시간 데이터 수신 콜백"""
        try:
            # GUI 업데이트 (메인 스레드에서 실행)
            QMetaObject.invokeMethod(self, "update_real_data", 
                                   Qt.QueuedConnection,
                                   Q_ARG(str, code),
                                   Q_ARG(dict, data))
        except Exception as e:
            self.log_message(f"실시간 데이터 처리 오류: {e}")
    
    def update_real_data(self, code, data):
        """실시간 데이터 GUI 업데이트"""
        try:
            # 종목 테이블에서 해당 종목 찾기
            for i in range(self.stock_table.rowCount()):
                if self.stock_table.item(i, 0).text() == code:
                    # 현재가 업데이트
                    price = data.get('current_price', 0)
                    self.stock_table.setItem(i, 2, QTableWidgetItem(f"{price:,}" if price else "-"))
                    
                    # 등락률 업데이트
                    change_rate = data.get('change_rate', 0)
                    change_rate_text = f"{change_rate:+.2f}%" if change_rate else "-"
                    self.stock_table.setItem(i, 3, QTableWidgetItem(change_rate_text))
                    
                    # 거래량 업데이트
                    volume = data.get('volume', 0)
                    self.stock_table.setItem(i, 4, QTableWidgetItem(f"{volume:,}" if volume else "-"))
                    break
        except Exception as e:
            self.log_message(f"실시간 데이터 GUI 업데이트 오류: {e}")
    
    def on_order_complete(self, order_info):
        """주문 완료 콜백"""
        try:
            code = order_info.get('code', '')
            order_type = order_info.get('order_type', '')
            quantity = order_info.get('quantity', 0)
            price = order_info.get('price', 0)
            status = order_info.get('status', '')
            
            self.log_message(f"주문 완료: {code} - {order_type} - {quantity}주 - {price:,}원 - {status}")
            
            # 거래 내역 테이블 업데이트
            self.update_history_table()
            
        except Exception as e:
            self.log_message(f"주문 완료 처리 오류: {e}")
    
    def add_watch_stock(self):
        """모니터링 종목 추가"""
        code = self.stock_code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "경고", "종목코드를 입력하세요.")
            return
        
        try:
            if self.api:
                stock_info = self.api.get_stock_basic_info(code)
                item_text = f"{code} - {stock_info['name']}"
                self.stock_list.addItem(item_text)
                self.stock_code_edit.clear()
                self.log_message(f"모니터링 종목 추가: {item_text}")
            else:
                QMessageBox.warning(self, "경고", "먼저 로그인하세요.")
        except Exception as e:
            self.log_message(f"종목 추가 오류: {e}")
    
    def remove_watch_stock(self):
        """모니터링 종목 제거"""
        current_item = self.stock_list.currentItem()
        if current_item:
            self.stock_list.takeItem(self.stock_list.row(current_item))
            self.log_message(f"모니터링 종목 제거: {current_item.text()}")
    
    def start_trading(self):
        """자동매매 시작"""
        try:
            if not self.api or not self.api.login_status:
                QMessageBox.warning(self, "경고", "먼저 로그인하세요.")
                return
            
            # 설정값 가져오기
            strategy_map = {
                "이동평균": "moving_average",
                "RSI": "rsi",
                "볼린저밴드": "bollinger"
            }
            
            strategy_type = strategy_map[self.strategy_combo.currentText()]
            
            # 파라미터 설정
            strategy_params = {}
            if strategy_type == "moving_average":
                strategy_params = {
                    'short_period': int(self.short_period_edit.text()),
                    'long_period': int(self.long_period_edit.text())
                }
            elif strategy_type == "rsi":
                strategy_params = {
                    'period': int(self.rsi_period_edit.text()),
                    'oversold': int(self.oversold_edit.text()),
                    'overbought': int(self.overbought_edit.text())
                }
            elif strategy_type == "bollinger":
                strategy_params = {
                    'period': int(self.bb_period_edit.text()),
                    'std_dev': float(self.std_dev_edit.text())
                }
            
            # 자동매매 시스템 생성
            self.trader = AutoTrader(strategy_type, **strategy_params)
            self.trader.api = self.api  # API 연결
            
            # 모니터링 종목 추가 및 실시간 데이터 구독
            watch_codes = []
            for i in range(self.stock_list.count()):
                item = self.stock_list.item(i)
                code = item.text().split(' - ')[0]
                watch_codes.append(code)
                
                # 실시간 데이터 구독
                try:
                    self.api.subscribe_real_data(code)
                    self.log_message(f"실시간 데이터 구독: {code}")
                except Exception as e:
                    self.log_message(f"실시간 데이터 구독 실패: {code} - {e}")
            
            self.trader.watch_list = watch_codes
            
            # 거래 설정
            self.trader.trade_amount = int(self.trade_amount_edit.text())
            self.trader.max_positions = int(self.max_positions_edit.text())
            
            # 타이머 설정
            interval = int(self.interval_edit.text())
            self.trader.timer.timeout.connect(self.update_monitoring)
            
            # 자동매매 시작
            self.trader.timer.start(interval * 1000)
            
            # UI 상태 변경
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.login_btn.setEnabled(False)
            
            self.statusBar().showMessage('자동매매 시작')
            self.log_message("자동매매 시작")
            
        except Exception as e:
            self.log_message(f"자동매매 시작 오류: {e}")
            QMessageBox.critical(self, "오류", f"자동매매 시작 중 오류가 발생했습니다: {e}")
    
    def stop_trading(self):
        """자동매매 중지"""
        try:
            if self.trader:
                # 실시간 데이터 구독 해제
                for code in self.trader.watch_list:
                    try:
                        self.api.unsubscribe_real_data(code)
                        self.log_message(f"실시간 데이터 구독 해제: {code}")
                    except Exception as e:
                        self.log_message(f"실시간 데이터 구독 해제 실패: {code} - {e}")
                
                # 타이머 중지
                self.trader.timer.stop()
                self.trader.stop_trading()
                
                # UI 상태 변경
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.login_btn.setEnabled(True)
                
                self.statusBar().showMessage('자동매매 중지')
                self.log_message("자동매매 중지")
                
        except Exception as e:
            self.log_message(f"자동매매 중지 오류: {e}")
    
    def update_monitoring(self):
        """모니터링 정보 업데이트"""
        if not self.trader:
            return
        
        # 종목 테이블 업데이트
        self.update_stock_table()
        
        # 거래 내역 업데이트
        self.update_history_table()
        
        # 상태 정보 업데이트
        self.update_status_info()
    
    def update_stock_table(self):
        """종목 테이블 업데이트"""
        if not self.trader:
            return
        
        self.stock_table.setRowCount(len(self.trader.watch_list))
        
        for i, stock in enumerate(self.trader.watch_list):
            code = stock['code']
            name = stock['name']
            
            # 현재가 정보 가져오기
            current_price = self.trader.api.stock_info.get(code, {})
            price = current_price.get('current_price', 0)
            
            self.stock_table.setItem(i, 0, QTableWidgetItem(code))
            self.stock_table.setItem(i, 1, QTableWidgetItem(name))
            self.stock_table.setItem(i, 2, QTableWidgetItem(f"{price:,}" if price else "-"))
            self.stock_table.setItem(i, 3, QTableWidgetItem("-"))
            self.stock_table.setItem(i, 4, QTableWidgetItem("-"))
            
            # 보유 상태 표시
            positions = self.trader.get_current_positions()
            if code in positions:
                self.stock_table.setItem(i, 5, QTableWidgetItem("보유"))
            else:
                self.stock_table.setItem(i, 5, QTableWidgetItem("관찰"))
    
    def update_history_table(self):
        """거래 내역 테이블 업데이트"""
        if not self.trader:
            return
        
        history = self.trader.strategy.trade_history
        self.history_table.setRowCount(len(history))
        
        for i, trade in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(trade['timestamp'].strftime("%H:%M:%S")))
            self.history_table.setItem(i, 1, QTableWidgetItem(trade['code']))
            self.history_table.setItem(i, 2, QTableWidgetItem("-"))
            self.history_table.setItem(i, 3, QTableWidgetItem(trade['action']))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(trade['quantity'])))
            self.history_table.setItem(i, 5, QTableWidgetItem(f"{trade['price']:,}"))
            self.history_table.setItem(i, 6, QTableWidgetItem(str(trade['order_no'])))
    
    def update_status_info(self):
        """상태 정보 업데이트"""
        if not self.trader:
            return
        
        summary = self.trader.get_trade_summary()
        
        self.total_trades_label.setText(f"총 거래: {summary['total_trades']}")
        self.buy_trades_label.setText(f"매수: {summary['buy_trades']}")
        self.sell_trades_label.setText(f"매도: {summary['sell_trades']}")
        self.positions_label.setText(f"보유종목: {summary['current_positions']}")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 스타일 설정
    app.setStyle('Fusion')
    
    # GUI 실행
    gui = TradingGUI()
    gui.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 