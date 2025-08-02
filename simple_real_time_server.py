"""
간단한 실시간 데이터 서버 (맥 최적화)
WebSocket 없이 HTTP API만으로 빠른 실행
"""

import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from loguru import logger

from real_time_data_system import RealTimeDataSystem, VirtualDataGenerator


# Flask 앱
app = Flask(__name__)
CORS(app)

# 실시간 데이터 시스템 인스턴스
real_time_system = None
data_generator = None


@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('real_time_dashboard.html')


@app.route('/api/status')
def get_system_status():
    """시스템 상태 조회"""
    if real_time_system:
        return jsonify(real_time_system.get_system_status())
    return jsonify({'error': '시스템이 초기화되지 않았습니다.'})


@app.route('/api/price-data')
def get_price_data():
    """가격 데이터 조회"""
    if not real_time_system:
        return jsonify({'error': '시스템이 초기화되지 않았습니다.'})
    
    stock_code = request.args.get('stock_code')
    if stock_code:
        price_data = real_time_system.price_cache.get(stock_code)
        return jsonify(price_data.__dict__ if price_data else {})
    
    return jsonify([price.__dict__ for price in real_time_system.price_cache.values()])


@app.route('/api/news-data')
def get_news_data():
    """뉴스 데이터 조회"""
    if not real_time_system:
        return jsonify({'error': '시스템이 초기화되지 않았습니다.'})
    
    limit = request.args.get('limit', 50, type=int)
    news_list = list(real_time_system.news_cache.values())
    news_list.sort(key=lambda x: x.published_at, reverse=True)
    
    return jsonify([news.__dict__ for news in news_list[:limit]])


@app.route('/api/portfolio-data')
def get_portfolio_data():
    """포트폴리오 데이터 조회"""
    if not real_time_system:
        return jsonify({'error': '시스템이 초기화되지 않았습니다.'})
    
    portfolio_id = request.args.get('portfolio_id')
    if portfolio_id:
        portfolio_data = real_time_system.portfolio_cache.get(portfolio_id)
        return jsonify(portfolio_data.__dict__ if portfolio_data else {})
    
    return jsonify([portfolio.__dict__ for portfolio in real_time_system.portfolio_cache.values()])


@app.route('/api/signals')
def get_signals():
    """투자 신호 조회"""
    if not real_time_system:
        return jsonify({'error': '시스템이 초기화되지 않았습니다.'})
    
    stock_code = request.args.get('stock_code')
    if stock_code:
        signals = [s for s in real_time_system.signal_cache.values() if s.stock_code == stock_code]
        return jsonify([signal.__dict__ for signal in signals])
    
    return jsonify([signal.__dict__ for signal in real_time_system.signal_cache.values()])


@app.route('/api/start-virtual-data')
def start_virtual_data():
    """가상 데이터 생성 시작"""
    global data_generator
    try:
        if data_generator:
            data_generator.start_virtual_data_generation()
            return jsonify({'message': '가상 데이터 생성이 시작되었습니다.'})
        else:
            return jsonify({'error': '데이터 생성기가 초기화되지 않았습니다.'})
    except Exception as e:
        logger.error(f"가상 데이터 시작 오류: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/stop-virtual-data')
def stop_virtual_data():
    """가상 데이터 생성 중지"""
    global data_generator
    try:
        if data_generator:
            data_generator.stop_virtual_data_generation()
            return jsonify({'message': '가상 데이터 생성이 중지되었습니다.'})
        else:
            return jsonify({'error': '데이터 생성기가 초기화되지 않았습니다.'})
    except Exception as e:
        logger.error(f"가상 데이터 중지 오류: {e}")
        return jsonify({'error': str(e)})


def initialize_system():
    """시스템 초기화"""
    global real_time_system, data_generator
    
    try:
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
        
        # 가상 데이터 생성기 초기화
        data_generator = VirtualDataGenerator(real_time_system)
        
        # 콜백 등록
        def price_callback(price_data):
            logger.info(f"가격 업데이트: {price_data.stock_name} {price_data.current_price:,}원")
        
        def alert_callback(alert):
            logger.warning(f"알림: {alert.message}")
        
        real_time_system.register_price_callback(price_callback)
        real_time_system.register_alert_callback(alert_callback)
        
        # 시스템 시작
        real_time_system.start()
        
        # 가상 데이터 생성 시작
        data_generator.start_virtual_data_generation()
        
        logger.info("실시간 데이터 시스템 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"시스템 초기화 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """메인 실행 함수"""
    logger.info("간단한 실시간 데이터 서버 시작 중...")
    
    # 시스템 초기화
    if not initialize_system():
        logger.error("시스템 초기화 실패")
        return
    
    # Flask 서버 실행
    try:
        logger.info("Flask 서버 시작 중... (포트 8081)")
        app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Flask 서버 실행 오류: {e}")
    finally:
        # 정리 작업
        if data_generator:
            data_generator.stop_virtual_data_generation()
        if real_time_system:
            real_time_system.stop()


if __name__ == "__main__":
    main() 