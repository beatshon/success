"""
키움증권 API 자동매매 프로그램 사용 예제
다양한 사용 시나리오를 보여주는 예제 코드
"""

import sys
import time
from datetime import datetime
from loguru import logger

# 프로젝트 모듈 import
from kiwoom_api import KiwoomAPI
from trading_strategy import MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy
from auto_trader import AutoTrader
from config import Config

def example_1_basic_usage():
    """예제 1: 기본 사용법"""
    print("=== 예제 1: 기본 사용법 ===")
    
    try:
        # 1. API 초기화 및 로그인
        api = KiwoomAPI()
        api.login()
        
        if not api.login_status:
            print("로그인 실패")
            return
        
        # 2. 계좌 정보 조회
        accounts = api.get_account_info()
        print(f"보유 계좌: {list(accounts.keys())}")
        
        # 3. 종목 정보 조회
        stock_code = "005930"  # 삼성전자
        stock_info = api.get_stock_basic_info(stock_code)
        print(f"종목 정보: {stock_info}")
        
        # 4. 현재가 조회
        current_price = api.get_current_price(stock_code)
        print(f"현재가: {current_price}")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def example_2_strategy_usage():
    """예제 2: 전략 사용법"""
    print("\n=== 예제 2: 전략 사용법 ===")
    
    try:
        # 1. API 및 전략 초기화
        api = KiwoomAPI()
        api.login()
        
        if not api.login_status:
            print("로그인 실패")
            return
        
        accounts = api.get_account_info()
        account = list(accounts.keys())[0]
        
        # 2. 이동평균 전략 사용
        ma_strategy = MovingAverageStrategy(api, account, short_period=5, long_period=20)
        
        # 3. 종목별 매매 신호 확인
        test_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        
        for code in test_stocks:
            current_price = api.get_current_price(code)
            if current_price:
                price = current_price.get('current_price', 0)
                
                # 매수 신호 확인
                if ma_strategy.should_buy(code, price):
                    print(f"{code}: 매수 신호 발생")
                
                # 매도 신호 확인
                if ma_strategy.should_sell(code, price):
                    print(f"{code}: 매도 신호 발생")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def example_3_auto_trader_usage():
    """예제 3: 자동매매 사용법"""
    print("\n=== 예제 3: 자동매매 사용법 ===")
    
    try:
        # 1. 자동매매 시스템 생성 (RSI 전략)
        trader = AutoTrader(
            strategy_type="rsi",
            period=14,
            oversold=30,
            overbought=70
        )
        
        # 2. 모니터링 종목 추가
        watch_stocks = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "035420",  # NAVER
            "051910",  # LG화학
            "006400"   # 삼성SDI
        ]
        
        for code in watch_stocks:
            trader.add_watch_stock(code)
        
        # 3. 거래 설정
        trader.trade_amount = 50000  # 5만원
        trader.max_positions = 3     # 최대 3개 종목
        
        # 4. 자동매매 시작 (30초마다 실행)
        print("자동매매 시작 (30초마다 실행)")
        print("Ctrl+C로 중지할 수 있습니다.")
        
        # 실제 실행 대신 시뮬레이션
        for i in range(3):  # 3번만 실행
            print(f"매매 사이클 {i+1} 실행 중...")
            trader.run_trading_cycle()
            time.sleep(5)  # 5초 대기
        
        # 5. 거래 요약 정보
        summary = trader.get_trade_summary()
        print(f"거래 요약: {summary}")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def example_4_custom_strategy():
    """예제 4: 커스텀 전략 구현"""
    print("\n=== 예제 4: 커스텀 전략 구현 ===")
    
    from trading_strategy import TradingStrategy
    
    class CustomVolumeStrategy(TradingStrategy):
        """거래량 기반 커스텀 전략"""
        
        def __init__(self, api, account, volume_threshold=1000000):
            super().__init__(api, account)
            self.volume_threshold = volume_threshold
            self.price_history = {}
        
        def update_price_history(self, code, price, volume):
            """가격 및 거래량 이력 업데이트"""
            if code not in self.price_history:
                self.price_history[code] = []
            
            self.price_history[code].append({
                'timestamp': datetime.now(),
                'price': price,
                'volume': volume
            })
            
            # 최근 20개 데이터만 유지
            if len(self.price_history[code]) > 20:
                self.price_history[code] = self.price_history[code][-20:]
        
        def should_buy(self, code, current_price, volume=0, **kwargs):
            """매수 조건: 거래량 급증 + 가격 상승"""
            self.update_price_history(code, current_price, volume)
            
            if code not in self.price_history or len(self.price_history[code]) < 5:
                return False
            
            # 최근 거래량이 임계값을 초과하고 가격이 상승하는 경우
            recent_data = self.price_history[code][-5:]
            avg_volume = sum(item['volume'] for item in recent_data) / len(recent_data)
            
            if (volume > self.volume_threshold and 
                volume > avg_volume * 1.5 and  # 거래량 50% 이상 증가
                current_price > recent_data[-2]['price']):  # 가격 상승
                
                print(f"거래량 급증 매수 신호: {code} - 거래량: {volume:,}")
                return True
            
            return False
        
        def should_sell(self, code, current_price, volume=0, **kwargs):
            """매도 조건: 거래량 급증 + 가격 하락"""
            self.update_price_history(code, current_price, volume)
            
            if code not in self.price_history or len(self.price_history[code]) < 5:
                return False
            
            # 최근 거래량이 임계값을 초과하고 가격이 하락하는 경우
            recent_data = self.price_history[code][-5:]
            avg_volume = sum(item['volume'] for item in recent_data) / len(recent_data)
            
            if (volume > self.volume_threshold and 
                volume > avg_volume * 1.5 and  # 거래량 50% 이상 증가
                current_price < recent_data[-2]['price']):  # 가격 하락
                
                print(f"거래량 급증 매도 신호: {code} - 거래량: {volume:,}")
                return True
            
            return False
    
    try:
        # 커스텀 전략 사용
        api = KiwoomAPI()
        api.login()
        
        if not api.login_status:
            print("로그인 실패")
            return
        
        accounts = api.get_account_info()
        account = list(accounts.keys())[0]
        
        # 커스텀 전략 생성
        custom_strategy = CustomVolumeStrategy(api, account, volume_threshold=500000)
        
        # 테스트
        test_code = "005930"
        current_price = api.get_current_price(test_code)
        
        if current_price:
            price = current_price.get('current_price', 0)
            volume = current_price.get('volume', 0)
            
            # 매매 신호 확인
            if custom_strategy.should_buy(test_code, price, volume):
                print(f"{test_code}: 커스텀 매수 신호")
            
            if custom_strategy.should_sell(test_code, price, volume):
                print(f"{test_code}: 커스텀 매도 신호")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def example_5_risk_management():
    """예제 5: 위험 관리 기능"""
    print("\n=== 예제 5: 위험 관리 기능 ===")
    
    try:
        # 설정에서 위험 관리 파라미터 가져오기
        risk_config = Config.RISK_MANAGEMENT
        
        print("위험 관리 설정:")
        print(f"- 일일 최대 손실: {risk_config['max_daily_loss']:,}원")
        print(f"- 단일 종목 최대 비중: {risk_config['max_position_size']*100}%")
        print(f"- 손절 기준: {risk_config['stop_loss_rate']*100}%")
        print(f"- 익절 기준: {risk_config['take_profit_rate']*100}%")
        print(f"- 일일 최대 거래 횟수: {risk_config['max_daily_trades']}회")
        
        # 장 시간 확인
        is_market_open = Config.is_market_open()
        print(f"\n현재 장 상태: {'개장' if is_market_open else '폐장'}")
        
        # 설정 유효성 검사
        errors = Config.validate_config()
        if errors:
            print("\n설정 오류:")
            for error in errors:
                print(f"- {error}")
        else:
            print("\n설정이 유효합니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def example_6_backtesting_simulation():
    """예제 6: 백테스팅 시뮬레이션"""
    print("\n=== 예제 6: 백테스팅 시뮬레이션 ===")
    
    try:
        # 간단한 백테스팅 시뮬레이션
        class BacktestSimulator:
            def __init__(self, strategy, initial_balance=1000000):
                self.strategy = strategy
                self.balance = initial_balance
                self.positions = {}
                self.trade_history = []
                self.initial_balance = initial_balance
            
            def simulate_trade(self, code, price, volume, timestamp):
                """거래 시뮬레이션"""
                # 매수 신호 확인
                if self.strategy.should_buy(code, price, volume):
                    if code not in self.positions and len(self.positions) < 5:
                        quantity = 100000 // price  # 10만원어치 매수
                        if quantity > 0 and self.balance >= quantity * price:
                            self.positions[code] = {
                                'quantity': quantity,
                                'avg_price': price,
                                'buy_time': timestamp
                            }
                            self.balance -= quantity * price
                            
                            self.trade_history.append({
                                'timestamp': timestamp,
                                'code': code,
                                'action': '매수',
                                'quantity': quantity,
                                'price': price
                            })
                            print(f"매수: {code} - {quantity}주 - {price:,}원")
                
                # 매도 신호 확인
                elif self.strategy.should_sell(code, price, volume):
                    if code in self.positions:
                        position = self.positions[code]
                        quantity = position['quantity']
                        self.balance += quantity * price
                        
                        # 수익률 계산
                        profit_rate = (price - position['avg_price']) / position['avg_price']
                        
                        self.trade_history.append({
                            'timestamp': timestamp,
                            'code': code,
                            'action': '매도',
                            'quantity': quantity,
                            'price': price,
                            'profit_rate': profit_rate
                        })
                        
                        del self.positions[code]
                        print(f"매도: {code} - {quantity}주 - {price:,}원 (수익률: {profit_rate*100:.1f}%)")
            
            def get_results(self):
                """백테스팅 결과 반환"""
                total_trades = len(self.trade_history)
                buy_trades = len([t for t in self.trade_history if t['action'] == '매수'])
                sell_trades = len([t for t in self.trade_history if t['action'] == '매도'])
                
                # 총 수익률 계산
                current_value = self.balance
                for code, position in self.positions.items():
                    # 현재가로 평가 (시뮬레이션이므로 마지막 거래가로 대체)
                    current_value += position['quantity'] * 50000  # 임시 가격
                
                total_return = (current_value - self.initial_balance) / self.initial_balance
                
                return {
                    'total_trades': total_trades,
                    'buy_trades': buy_trades,
                    'sell_trades': sell_trades,
                    'final_balance': current_value,
                    'total_return': total_return,
                    'remaining_positions': len(self.positions)
                }
        
        # 시뮬레이션 실행
        print("백테스팅 시뮬레이션 시작...")
        
        # 가상의 API 및 전략 생성
        class MockAPI:
            def get_current_price(self, code):
                return {'current_price': 50000, 'volume': 1000000}
        
        mock_api = MockAPI()
        strategy = MovingAverageStrategy(mock_api, "mock_account")
        
        # 백테스터 생성
        backtester = BacktestSimulator(strategy, initial_balance=1000000)
        
        # 가상 거래 데이터로 시뮬레이션
        test_data = [
            ("005930", 50000, 1000000, datetime.now()),
            ("005930", 52000, 1200000, datetime.now()),
            ("005930", 48000, 800000, datetime.now()),
            ("000660", 150000, 500000, datetime.now()),
            ("000660", 160000, 600000, datetime.now()),
        ]
        
        for code, price, volume, timestamp in test_data:
            backtester.simulate_trade(code, price, volume, timestamp)
        
        # 결과 출력
        results = backtester.get_results()
        print(f"\n백테스팅 결과:")
        print(f"- 총 거래: {results['total_trades']}회")
        print(f"- 매수: {results['buy_trades']}회")
        print(f"- 매도: {results['sell_trades']}회")
        print(f"- 최종 잔고: {results['final_balance']:,}원")
        print(f"- 총 수익률: {results['total_return']*100:.1f}%")
        print(f"- 보유 종목: {results['remaining_positions']}개")
        
    except Exception as e:
        print(f"오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("키움증권 API 자동매매 프로그램 사용 예제")
    print("=" * 50)
    
    # 로그 설정
    logger.add("logs/example_{time}.log", rotation="1 day", retention="7 days")
    
    try:
        # 예제 실행
        example_1_basic_usage()
        example_2_strategy_usage()
        example_3_auto_trader_usage()
        example_4_custom_strategy()
        example_5_risk_management()
        example_6_backtesting_simulation()
        
        print("\n" + "=" * 50)
        print("모든 예제 실행 완료!")
        print("\n주의사항:")
        print("- 실제 거래 전 충분한 테스트를 진행하세요")
        print("- 소액으로 시작하여 점진적으로 금액을 늘려가세요")
        print("- 투자 손실에 대한 책임은 본인에게 있습니다")
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"예제 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 