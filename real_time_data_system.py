"""
실시간 데이터 연동 시스템
WebSocket 기반 실시간 가격 데이터, 뉴스 감정 분석, 포트폴리오 모니터링
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import aiohttp
import pandas as pd
import numpy as np
from loguru import logger
import queue
import uuid

# 고급 시스템은 선택적으로 import
try:
    from advanced_investment_signals import AdvancedInvestmentSignals, SignalType
    from portfolio_optimizer import PortfolioOptimizer, OptimizationMethod
    ADVANCED_SYSTEM_AVAILABLE = True
except ImportError:
    ADVANCED_SYSTEM_AVAILABLE = False
    # 기본 SignalType 정의
    from enum import Enum
    class SignalType(Enum):
        STRONG_BUY = "STRONG_BUY"
        BUY = "BUY"
        WEAK_BUY = "WEAK_BUY"
        HOLD = "HOLD"
        WEAK_SELL = "WEAK_SELL"
        SELL = "SELL"
        STRONG_SELL = "STRONG_SELL"


class DataType(Enum):
    """데이터 타입 정의"""
    PRICE = "price"
    NEWS = "news"
    SENTIMENT = "sentiment"
    PORTFOLIO = "portfolio"
    SIGNAL = "signal"
    ALERT = "alert"


@dataclass
class RealTimePrice:
    """실시간 가격 데이터"""
    stock_code: str
    stock_name: str
    current_price: float
    change: float
    change_rate: float
    volume: int
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    prev_close: float


@dataclass
class RealTimeNews:
    """실시간 뉴스 데이터"""
    news_id: str
    title: str
    content: str
    source: str
    published_at: datetime
    sentiment_score: float
    sentiment_label: str
    related_stocks: List[str]
    impact_score: float


@dataclass
class PortfolioUpdate:
    """포트폴리오 업데이트"""
    portfolio_id: str
    total_value: float
    total_return: float
    total_return_rate: float
    positions: List[Dict]
    timestamp: datetime
    risk_metrics: Dict[str, float]


@dataclass
class InvestmentSignal:
    """투자 신호"""
    stock_code: str
    stock_name: str
    signal_type: SignalType
    confidence: float
    target_price: float
    stop_loss: float
    estimated_holding_period: int
    reasoning: str
    timestamp: datetime


@dataclass
class Alert:
    """알림"""
    alert_id: str
    alert_type: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    data: Dict[str, Any]


class RealTimeDataSystem:
    """실시간 데이터 연동 시스템"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.websocket_server = None
        self.clients = set()
        self.data_queue = queue.Queue()
        self.running = False
        
        # 데이터 캐시
        self.price_cache = {}
        self.news_cache = {}
        self.portfolio_cache = {}
        self.signal_cache = {}
        
        # 콜백 함수들
        self.price_callbacks = []
        self.news_callbacks = []
        self.portfolio_callbacks = []
        self.signal_callbacks = []
        self.alert_callbacks = []
        
        # 고급 시스템 연동 (선택적)
        if ADVANCED_SYSTEM_AVAILABLE:
            self.advanced_signals = AdvancedInvestmentSignals()
            self.portfolio_optimizer = PortfolioOptimizer()
        else:
            self.advanced_signals = None
            self.portfolio_optimizer = None
        
        # 모니터링 설정
        self.monitoring_interval = self.config.get('monitoring_interval', 1.0)  # 초
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'price_change': 0.05,  # 5%
            'volume_spike': 3.0,   # 3배
            'sentiment_change': 0.3,
            'portfolio_loss': 0.02  # 2%
        })
        
        logger.info("실시간 데이터 시스템 초기화 완료")
    
    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """WebSocket 서버 시작"""
        try:
            self.websocket_server = await websockets.serve(
                self.handle_client, host, port
            )
            logger.info(f"WebSocket 서버 시작: ws://{host}:{port}")
            
            # 데이터 브로드캐스트 루프 시작
            asyncio.create_task(self.broadcast_loop())
            
            return True
        except Exception as e:
            logger.error(f"WebSocket 서버 시작 실패: {e}")
            return False
    
    async def handle_client(self, websocket, path):
        """클라이언트 연결 처리"""
        client_id = str(uuid.uuid4())
        self.clients.add(websocket)
        logger.info(f"클라이언트 연결: {client_id}")
        
        try:
            async for message in websocket:
                await self.process_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"클라이언트 연결 종료: {client_id}")
        finally:
            self.clients.remove(websocket)
    
    async def process_client_message(self, websocket, message):
        """클라이언트 메시지 처리"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self.handle_subscription(websocket, data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(websocket, data)
            elif message_type == 'request_data':
                await self.handle_data_request(websocket, data)
            else:
                logger.warning(f"알 수 없는 메시지 타입: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("잘못된 JSON 형식")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
    
    async def handle_subscription(self, websocket, data):
        """구독 처리"""
        data_type = data.get('data_type')
        filters = data.get('filters', {})
        
        # 구독 정보를 웹소켓에 저장
        if not hasattr(websocket, 'subscriptions'):
            websocket.subscriptions = {}
        
        websocket.subscriptions[data_type] = filters
        logger.info(f"구독 등록: {data_type}")
        
        # 즉시 현재 데이터 전송
        await self.send_current_data(websocket, data_type)
    
    async def handle_unsubscription(self, websocket, data):
        """구독 해제 처리"""
        data_type = data.get('data_type')
        
        if hasattr(websocket, 'subscriptions') and data_type in websocket.subscriptions:
            del websocket.subscriptions[data_type]
            logger.info(f"구독 해제: {data_type}")
    
    async def handle_data_request(self, websocket, data):
        """데이터 요청 처리"""
        data_type = data.get('data_type')
        params = data.get('params', {})
        
        response = await self.get_requested_data(data_type, params)
        await websocket.send(json.dumps({
            'type': 'data_response',
            'data_type': data_type,
            'data': response
        }))
    
    async def send_current_data(self, websocket, data_type):
        """현재 데이터 전송"""
        if data_type == DataType.PRICE.value:
            data = list(self.price_cache.values())
        elif data_type == DataType.NEWS.value:
            data = list(self.news_cache.values())
        elif data_type == DataType.PORTFOLIO.value:
            data = list(self.portfolio_cache.values())
        elif data_type == DataType.SIGNAL.value:
            data = list(self.signal_cache.values())
        else:
            return
        
        await websocket.send(json.dumps({
            'type': 'data_update',
            'data_type': data_type,
            'data': [asdict(item) for item in data],
            'timestamp': datetime.now().isoformat()
        }))
    
    async def broadcast_loop(self):
        """데이터 브로드캐스트 루프"""
        while self.running:
            try:
                # 큐에서 데이터 가져오기
                try:
                    data_item = self.data_queue.get_nowait()
                    await self.broadcast_data(data_item)
                except queue.Empty:
                    pass
                
                await asyncio.sleep(0.1)  # 100ms 간격
                
            except Exception as e:
                logger.error(f"브로드캐스트 루프 오류: {e}")
                await asyncio.sleep(1)
    
    async def broadcast_data(self, data_item):
        """데이터 브로드캐스트"""
        if not self.clients:
            return
        
        data_type = data_item.get('type')
        data = data_item.get('data')
        
        # 구독 중인 클라이언트들에게만 전송
        message = json.dumps({
            'type': 'data_update',
            'data_type': data_type,
            'data': asdict(data) if hasattr(data, '__dict__') else data,
            'timestamp': datetime.now().isoformat()
        })
        
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                if hasattr(client, 'subscriptions') and data_type in client.subscriptions:
                    await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"클라이언트 전송 오류: {e}")
                disconnected_clients.add(client)
        
        # 연결이 끊어진 클라이언트 제거
        self.clients -= disconnected_clients
    
    def add_price_data(self, price_data: RealTimePrice):
        """가격 데이터 추가"""
        self.price_cache[price_data.stock_code] = price_data
        
        # 큐에 추가
        self.data_queue.put({
            'type': DataType.PRICE.value,
            'data': price_data
        })
        
        # 콜백 실행
        for callback in self.price_callbacks:
            try:
                callback(price_data)
            except Exception as e:
                logger.error(f"가격 콜백 오류: {e}")
        
        # 알림 체크
        self.check_price_alerts(price_data)
    
    def add_news_data(self, news_data: RealTimeNews):
        """뉴스 데이터 추가"""
        self.news_cache[news_data.news_id] = news_data
        
        # 큐에 추가
        self.data_queue.put({
            'type': DataType.NEWS.value,
            'data': news_data
        })
        
        # 콜백 실행
        for callback in self.news_callbacks:
            try:
                callback(news_data)
            except Exception as e:
                logger.error(f"뉴스 콜백 오류: {e}")
        
        # 감정 분석 기반 신호 생성
        self.generate_news_based_signals(news_data)
    
    def add_portfolio_update(self, portfolio_data: PortfolioUpdate):
        """포트폴리오 업데이트 추가"""
        self.portfolio_cache[portfolio_data.portfolio_id] = portfolio_data
        
        # 큐에 추가
        self.data_queue.put({
            'type': DataType.PORTFOLIO.value,
            'data': portfolio_data
        })
        
        # 콜백 실행
        for callback in self.portfolio_callbacks:
            try:
                callback(portfolio_data)
            except Exception as e:
                logger.error(f"포트폴리오 콜백 오류: {e}")
        
        # 포트폴리오 알림 체크
        self.check_portfolio_alerts(portfolio_data)
    
    def add_investment_signal(self, signal: InvestmentSignal):
        """투자 신호 추가"""
        signal_key = f"{signal.stock_code}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}"
        self.signal_cache[signal_key] = signal
        
        # 큐에 추가
        self.data_queue.put({
            'type': DataType.SIGNAL.value,
            'data': signal
        })
        
        # 콜백 실행
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"신호 콜백 오류: {e}")
    
    def check_price_alerts(self, price_data: RealTimePrice):
        """가격 알림 체크"""
        if price_data.change_rate > self.alert_thresholds['price_change']:
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type="price_spike",
                message=f"{price_data.stock_name}({price_data.stock_code}) 급등: {price_data.change_rate:.2%}",
                severity="warning",
                timestamp=datetime.now(),
                data={
                    'stock_code': price_data.stock_code,
                    'change_rate': price_data.change_rate,
                    'current_price': price_data.current_price
                }
            )
            self.add_alert(alert)
    
    def check_portfolio_alerts(self, portfolio_data: PortfolioUpdate):
        """포트폴리오 알림 체크"""
        if portfolio_data.total_return_rate < -self.alert_thresholds['portfolio_loss']:
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type="portfolio_loss",
                message=f"포트폴리오 손실: {portfolio_data.total_return_rate:.2%}",
                severity="error",
                timestamp=datetime.now(),
                data={
                    'total_return_rate': portfolio_data.total_return_rate,
                    'total_value': portfolio_data.total_value
                }
            )
            self.add_alert(alert)
    
    def generate_news_based_signals(self, news_data: RealTimeNews):
        """뉴스 기반 신호 생성"""
        if news_data.impact_score > 0.7:  # 높은 영향도 뉴스만
            for stock_code in news_data.related_stocks:
                # 가격 데이터가 있으면 신호 생성
                if stock_code in self.price_cache:
                    price_data = self.price_cache[stock_code]
                    
                    # 간단한 뉴스 기반 신호 로직
                    if news_data.sentiment_score > 0.6:
                        signal_type = SignalType.BUY
                        confidence = min(news_data.impact_score * news_data.sentiment_score, 0.9)
                    elif news_data.sentiment_score < -0.6:
                        signal_type = SignalType.SELL
                        confidence = min(news_data.impact_score * abs(news_data.sentiment_score), 0.9)
                    else:
                        continue
                    
                    signal = InvestmentSignal(
                        stock_code=stock_code,
                        stock_name=price_data.stock_name,
                        signal_type=signal_type,
                        confidence=confidence,
                        target_price=price_data.current_price * (1 + 0.05 if signal_type == SignalType.BUY else -0.05),
                        stop_loss=price_data.current_price * (1 - 0.03 if signal_type == SignalType.BUY else 0.03),
                        estimated_holding_period=5,  # 5일
                        reasoning=f"뉴스 감정 분석 기반: {news_data.sentiment_label}",
                        timestamp=datetime.now()
                    )
                    
                    self.add_investment_signal(signal)
    
    def add_alert(self, alert: Alert):
        """알림 추가"""
        # 큐에 추가
        self.data_queue.put({
            'type': DataType.ALERT.value,
            'data': alert
        })
        
        # 콜백 실행
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"알림 콜백 오류: {e}")
        
        logger.info(f"알림 생성: {alert.alert_type} - {alert.message}")
    
    # 콜백 등록 메서드들
    def register_price_callback(self, callback: Callable[[RealTimePrice], None]):
        """가격 데이터 콜백 등록"""
        self.price_callbacks.append(callback)
    
    def register_news_callback(self, callback: Callable[[RealTimeNews], None]):
        """뉴스 데이터 콜백 등록"""
        self.news_callbacks.append(callback)
    
    def register_portfolio_callback(self, callback: Callable[[PortfolioUpdate], None]):
        """포트폴리오 콜백 등록"""
        self.portfolio_callbacks.append(callback)
    
    def register_signal_callback(self, callback: Callable[[InvestmentSignal], None]):
        """투자 신호 콜백 등록"""
        self.signal_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """알림 콜백 등록"""
        self.alert_callbacks.append(callback)
    
    async def get_requested_data(self, data_type: str, params: Dict) -> Dict:
        """요청된 데이터 반환"""
        if data_type == DataType.PRICE.value:
            stock_code = params.get('stock_code')
            if stock_code:
                return asdict(self.price_cache.get(stock_code, {}))
            return [asdict(price) for price in self.price_cache.values()]
        
        elif data_type == DataType.NEWS.value:
            limit = params.get('limit', 50)
            news_list = list(self.news_cache.values())
            news_list.sort(key=lambda x: x.published_at, reverse=True)
            return [asdict(news) for news in news_list[:limit]]
        
        elif data_type == DataType.PORTFOLIO.value:
            portfolio_id = params.get('portfolio_id')
            if portfolio_id:
                return asdict(self.portfolio_cache.get(portfolio_id, {}))
            return [asdict(portfolio) for portfolio in self.portfolio_cache.values()]
        
        elif data_type == DataType.SIGNAL.value:
            stock_code = params.get('stock_code')
            if stock_code:
                signals = [s for s in self.signal_cache.values() if s.stock_code == stock_code]
                return [asdict(signal) for signal in signals]
            return [asdict(signal) for signal in self.signal_cache.values()]
        
        return {}
    
    def start(self):
        """시스템 시작"""
        self.running = True
        logger.info("실시간 데이터 시스템 시작")
    
    def stop(self):
        """시스템 중지"""
        self.running = False
        logger.info("실시간 데이터 시스템 중지")
    
    def get_system_status(self) -> Dict:
        """시스템 상태 반환"""
        return {
            'running': self.running,
            'connected_clients': len(self.clients),
            'cache_sizes': {
                'price': len(self.price_cache),
                'news': len(self.news_cache),
                'portfolio': len(self.portfolio_cache),
                'signals': len(self.signal_cache)
            },
            'queue_size': self.data_queue.qsize(),
            'timestamp': datetime.now().isoformat()
        }


# 테스트용 가상 데이터 생성기
class VirtualDataGenerator:
    """가상 데이터 생성기 (테스트용)"""
    
    def __init__(self, real_time_system: RealTimeDataSystem):
        self.real_time_system = real_time_system
        self.running = False
        self.stock_codes = ['005930', '000660', '035420', '051910', '006400']  # 삼성전자, SK하이닉스, NAVER, LG화학, 삼성SDI
        self.stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '051910': 'LG화학',
            '006400': '삼성SDI'
        }
    
    def start_virtual_data_generation(self):
        """가상 데이터 생성 시작"""
        self.running = True
        threading.Thread(target=self._generate_price_data, daemon=True).start()
        threading.Thread(target=self._generate_news_data, daemon=True).start()
        threading.Thread(target=self._generate_portfolio_data, daemon=True).start()
        logger.info("가상 데이터 생성 시작")
    
    def stop_virtual_data_generation(self):
        """가상 데이터 생성 중지"""
        self.running = False
        logger.info("가상 데이터 생성 중지")
    
    def _generate_price_data(self):
        """가격 데이터 생성"""
        base_prices = {
            '005930': 70000,
            '000660': 120000,
            '035420': 200000,
            '051910': 500000,
            '006400': 400000
        }
        
        while self.running:
            for stock_code in self.stock_codes:
                base_price = base_prices[stock_code]
                
                # 랜덤 변동
                change_rate = np.random.normal(0, 0.02)  # 2% 표준편차
                current_price = base_price * (1 + change_rate)
                
                # OHLC 계산
                open_price = base_price
                high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
                low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
                prev_close = base_price
                
                change = current_price - prev_close
                change_rate = change / prev_close
                volume = int(np.random.uniform(1000000, 10000000))
                
                price_data = RealTimePrice(
                    stock_code=stock_code,
                    stock_name=self.stock_names[stock_code],
                    current_price=current_price,
                    change=change,
                    change_rate=change_rate,
                    volume=volume,
                    timestamp=datetime.now(),
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    prev_close=prev_close
                )
                
                self.real_time_system.add_price_data(price_data)
                
                # 다음 반복을 위해 기본 가격 업데이트
                base_prices[stock_code] = current_price
            
            time.sleep(2)  # 2초 간격
    
    def _generate_news_data(self):
        """뉴스 데이터 생성"""
        news_templates = [
            {
                'title': '{company} 실적 발표, 시장 예상치 상회',
                'sentiment': 0.8,
                'impact': 0.9
            },
            {
                'title': '{company} 신제품 출시, 시장 반응 긍정적',
                'sentiment': 0.7,
                'impact': 0.8
            },
            {
                'title': '{company} 경영진 교체, 불확실성 증가',
                'sentiment': -0.6,
                'impact': 0.7
            },
            {
                'title': '{company} 주가 조정, 매수 기회로 평가',
                'sentiment': 0.5,
                'impact': 0.6
            }
        ]
        
        while self.running:
            if np.random.random() < 0.3:  # 30% 확률로 뉴스 생성
                template = np.random.choice(news_templates)
                stock_code = np.random.choice(self.stock_codes)
                
                news_data = RealTimeNews(
                    news_id=str(uuid.uuid4()),
                    title=template['title'].format(company=self.stock_names[stock_code]),
                    content=f"{self.stock_names[stock_code]} 관련 뉴스 내용입니다.",
                    source="가상뉴스",
                    published_at=datetime.now(),
                    sentiment_score=template['sentiment'] + np.random.normal(0, 0.1),
                    sentiment_label="긍정" if template['sentiment'] > 0 else "부정",
                    related_stocks=[stock_code],
                    impact_score=template['impact'] + np.random.normal(0, 0.1)
                )
                
                self.real_time_system.add_news_data(news_data)
            
            time.sleep(10)  # 10초 간격
    
    def _generate_portfolio_data(self):
        """포트폴리오 데이터 생성"""
        while self.running:
            # 가상 포트폴리오 데이터
            positions = []
            total_value = 10000000  # 1000만원
            
            for stock_code in self.stock_codes:
                if stock_code in self.real_time_system.price_cache:
                    price_data = self.real_time_system.price_cache[stock_code]
                    quantity = int(np.random.uniform(10, 100))
                    position_value = price_data.current_price * quantity
                    
                    positions.append({
                        'stock_code': stock_code,
                        'stock_name': price_data.stock_name,
                        'quantity': quantity,
                        'current_price': price_data.current_price,
                        'position_value': position_value,
                        'return_rate': price_data.change_rate
                    })
            
            total_return = sum(pos['position_value'] * pos['return_rate'] for pos in positions)
            total_return_rate = total_return / total_value if total_value > 0 else 0
            
            portfolio_data = PortfolioUpdate(
                portfolio_id="virtual_portfolio",
                total_value=total_value,
                total_return=total_return,
                total_return_rate=total_return_rate,
                positions=positions,
                timestamp=datetime.now(),
                risk_metrics={
                    'var_95': -0.02,
                    'cvar_95': -0.03,
                    'max_drawdown': -0.05,
                    'sharpe_ratio': 1.2
                }
            )
            
            self.real_time_system.add_portfolio_update(portfolio_data)
            time.sleep(5)  # 5초 간격


# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    # 실시간 데이터 시스템 초기화
    config = {
        'monitoring_interval': 1.0,
        'alert_thresholds': {
            'price_change': 0.05,
            'volume_spike': 3.0,
            'sentiment_change': 0.3,
            'portfolio_loss': 0.02
        }
    }
    
    real_time_system = RealTimeDataSystem(config)
    
    # 콜백 등록 예시
    def price_callback(price_data):
        logger.info(f"가격 업데이트: {price_data.stock_name} {price_data.current_price:,}원")
    
    def alert_callback(alert):
        logger.warning(f"알림: {alert.message}")
    
    real_time_system.register_price_callback(price_callback)
    real_time_system.register_alert_callback(alert_callback)
    
    # WebSocket 서버 시작
    await real_time_system.start_websocket_server()
    
    # 가상 데이터 생성기 시작
    data_generator = VirtualDataGenerator(real_time_system)
    data_generator.start_virtual_data_generation()
    
    # 시스템 시작
    real_time_system.start()
    
    try:
        # 서버 유지
        await asyncio.Future()  # 무한 대기
    except KeyboardInterrupt:
        logger.info("시스템 종료 요청")
    finally:
        data_generator.stop_virtual_data_generation()
        real_time_system.stop()


if __name__ == "__main__":
    asyncio.run(main()) 