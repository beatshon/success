"""
실시간 데이터 시스템 테스트
"""

import asyncio
import json
import time
from datetime import datetime
from loguru import logger

from real_time_data_system import RealTimeDataSystem, VirtualDataGenerator


async def test_websocket_client():
    """WebSocket 클라이언트 테스트"""
    import websockets
    
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket 연결됨")
            
            # 구독 요청
            subscriptions = [
                {'type': 'subscribe', 'data_type': 'price'},
                {'type': 'subscribe', 'data_type': 'news'},
                {'type': 'subscribe', 'data_type': 'portfolio'},
                {'type': 'subscribe', 'data_type': 'signal'},
                {'type': 'subscribe', 'data_type': 'alert'}
            ]
            
            for sub in subscriptions:
                await websocket.send(json.dumps(sub))
                logger.info(f"구독 요청: {sub['data_type']}")
            
            # 메시지 수신
            count = 0
            while count < 50:  # 50개 메시지 수신 후 종료
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    logger.info(f"수신: {data['data_type']} - {len(data['data'])}개 항목")
                    
                    if data['data_type'] == 'price' and data['data']:
                        price = data['data'][0]
                        logger.info(f"  가격: {price['stock_name']} {price['current_price']:,}원")
                    
                    elif data['data_type'] == 'news' and data['data']:
                        news = data['data'][0]
                        logger.info(f"  뉴스: {news['title'][:50]}...")
                    
                    elif data['data_type'] == 'portfolio' and data['data']:
                        portfolio = data['data'][0]
                        logger.info(f"  포트폴리오: {portfolio['total_value']:,}원 ({portfolio['total_return_rate']:.2%})")
                    
                    elif data['data_type'] == 'signal' and data['data']:
                        signal = data['data'][0]
                        logger.info(f"  신호: {signal['stock_name']} {signal['signal_type']}")
                    
                    elif data['data_type'] == 'alert' and data['data']:
                        alert = data['data'][0]
                        logger.info(f"  알림: {alert['message']}")
                    
                    count += 1
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.error("WebSocket 연결이 끊어졌습니다.")
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket 클라이언트 오류: {e}")


def test_real_time_system():
    """실시간 데이터 시스템 테스트"""
    logger.info("실시간 데이터 시스템 테스트 시작")
    
    # 시스템 초기화
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
    
    # 콜백 등록
    def price_callback(price_data):
        logger.info(f"가격 콜백: {price_data.stock_name} {price_data.current_price:,}원")
    
    def news_callback(news_data):
        logger.info(f"뉴스 콜백: {news_data.title[:50]}...")
    
    def portfolio_callback(portfolio_data):
        logger.info(f"포트폴리오 콜백: {portfolio_data.total_value:,}원")
    
    def signal_callback(signal):
        logger.info(f"신호 콜백: {signal.stock_name} {signal.signal_type}")
    
    def alert_callback(alert):
        logger.warning(f"알림 콜백: {alert.message}")
    
    real_time_system.register_price_callback(price_callback)
    real_time_system.register_news_callback(news_callback)
    real_time_system.register_portfolio_callback(portfolio_callback)
    real_time_system.register_signal_callback(signal_callback)
    real_time_system.register_alert_callback(alert_callback)
    
    # 가상 데이터 생성기 시작
    data_generator = VirtualDataGenerator(real_time_system)
    data_generator.start_virtual_data_generation()
    
    # 시스템 시작
    real_time_system.start()
    
    try:
        # 30초간 테스트
        logger.info("30초간 테스트 실행...")
        time.sleep(30)
        
        # 시스템 상태 출력
        status = real_time_system.get_system_status()
        logger.info(f"시스템 상태: {status}")
        
    except KeyboardInterrupt:
        logger.info("테스트 중단됨")
    finally:
        # 정리
        data_generator.stop_virtual_data_generation()
        real_time_system.stop()
        logger.info("테스트 완료")


async def test_websocket_server():
    """WebSocket 서버 테스트"""
    logger.info("WebSocket 서버 테스트 시작")
    
    # 시스템 초기화
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
    
    # WebSocket 서버 시작
    await real_time_system.start_websocket_server()
    
    # 가상 데이터 생성기 시작
    data_generator = VirtualDataGenerator(real_time_system)
    data_generator.start_virtual_data_generation()
    
    # 시스템 시작
    real_time_system.start()
    
    try:
        # WebSocket 클라이언트 테스트
        await test_websocket_client()
        
    except KeyboardInterrupt:
        logger.info("테스트 중단됨")
    finally:
        # 정리
        data_generator.stop_virtual_data_generation()
        real_time_system.stop()
        logger.info("WebSocket 서버 테스트 완료")


def test_data_generation():
    """데이터 생성 테스트"""
    logger.info("데이터 생성 테스트 시작")
    
    # 시스템 초기화
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
    data_generator = VirtualDataGenerator(real_time_system)
    
    # 콜백 등록
    def price_callback(price_data):
        logger.info(f"가격: {price_data.stock_name} {price_data.current_price:,}원 ({price_data.change_rate:.2%})")
    
    def news_callback(news_data):
        logger.info(f"뉴스: {news_data.title} (감정: {news_data.sentiment_label})")
    
    def portfolio_callback(portfolio_data):
        logger.info(f"포트폴리오: {portfolio_data.total_value:,}원 (수익률: {portfolio_data.total_return_rate:.2%})")
    
    real_time_system.register_price_callback(price_callback)
    real_time_system.register_news_callback(news_callback)
    real_time_system.register_portfolio_callback(portfolio_callback)
    
    # 데이터 생성 시작
    data_generator.start_virtual_data_generation()
    
    try:
        # 20초간 테스트
        logger.info("20초간 데이터 생성 테스트...")
        time.sleep(20)
        
        # 캐시 상태 확인
        logger.info(f"가격 캐시: {len(real_time_system.price_cache)}개")
        logger.info(f"뉴스 캐시: {len(real_time_system.news_cache)}개")
        logger.info(f"포트폴리오 캐시: {len(real_time_system.portfolio_cache)}개")
        logger.info(f"신호 캐시: {len(real_time_system.signal_cache)}개")
        
    except KeyboardInterrupt:
        logger.info("테스트 중단됨")
    finally:
        data_generator.stop_virtual_data_generation()
        logger.info("데이터 생성 테스트 완료")


def main():
    """메인 테스트 함수"""
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "data"
    
    if test_type == "websocket":
        asyncio.run(test_websocket_server())
    elif test_type == "system":
        test_real_time_system()
    elif test_type == "data":
        test_data_generation()
    else:
        logger.error("알 수 없는 테스트 타입. 'websocket', 'system', 'data' 중 선택하세요.")


if __name__ == "__main__":
    main() 