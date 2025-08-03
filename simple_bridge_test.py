#!/usr/bin/env python3
"""
간단한 키움 API 브리지 테스트 서버
"""

import sys
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request

# Flask 앱 초기화
app = Flask(__name__)

# 시뮬레이션 데이터
simulation_data = {
    'account_info': {
        'account_number': '1234567890',
        'balance': 10000000,
        'available_balance': 9500000,
        'total_profit': 500000
    },
    'positions': {
        '005930': {'quantity': 100, 'avg_price': 70000, 'current_price': 72000},
        '000660': {'quantity': 50, 'avg_price': 80000, 'current_price': 82000}
    },
    'order_history': []
}

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        'status': 'healthy',
        'kiwoom_connected': True,
        'timestamp': datetime.now().isoformat(),
        'server': 'simple_bridge_test'
    })

@app.route('/api/v1/connect', methods=['POST'])
def connect_kiwoom():
    """키움 API 연결 시뮬레이션"""
    return jsonify({
        'status': 'success',
        'message': '키움 API 연결 성공 (시뮬레이션)',
        'connected': True
    })

@app.route('/api/v1/account', methods=['GET'])
def get_account_info():
    """계좌 정보 조회"""
    return jsonify({
        'status': 'success',
        'account_info': simulation_data['account_info']
    })

@app.route('/api/v1/positions', methods=['GET'])
def get_positions():
    """보유 종목 조회"""
    return jsonify({
        'status': 'success',
        'positions': simulation_data['positions']
    })

@app.route('/api/v1/order', methods=['POST'])
def place_order():
    """주문 실행 시뮬레이션"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '005930')
        order_type = data.get('order_type', 'buy')
        quantity = data.get('quantity', 10)
        price = data.get('price', 0)
        
        order_result = {
            'order_id': f"ORDER_{int(time.time())}",
            'symbol': symbol,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        simulation_data['order_history'].append(order_result)
        
        print(f"주문 실행: {symbol} {order_type} {quantity}주 @ {price}")
        
        return jsonify({
            'status': 'success',
            'order_result': order_result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/v1/market_data', methods=['GET'])
def get_market_data():
    """시장 데이터 조회 시뮬레이션"""
    try:
        symbol = request.args.get('symbol', '005930')
        
        import random
        base_price = 10000 if symbol == '005930' else 80000
        
        market_data = {
            'symbol': symbol,
            'current_price': base_price + random.uniform(-500, 500),
            'open_price': base_price,
            'high_price': base_price + random.uniform(0, 1000),
            'low_price': base_price - random.uniform(0, 500),
            'volume': random.randint(1000000, 10000000),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'market_data': market_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/v1/status', methods=['GET'])
def get_status():
    """시스템 상태 조회"""
    return jsonify({
        'status': 'success',
        'system_info': {
            'name': 'Simple Kiwoom Bridge Test',
            'version': '1.0.0',
            'architecture': '32비트' if sys.maxsize <= 2**32 else '64비트',
            'python_version': sys.version,
            'uptime': datetime.now().isoformat()
        },
        'kiwoom_status': {
            'connected': True,
            'account_number': simulation_data['account_info']['account_number'],
            'balance': simulation_data['account_info']['balance']
        }
    })

if __name__ == "__main__":
    print("=== 간단한 키움 API 브리지 테스트 서버 ===")
    print(f"Python 아키텍처: {'32비트' if sys.maxsize <= 2**32 else '64비트'}")
    print(f"Python 버전: {sys.version}")
    print("서버 시작 중...")
    
    try:
        app.run(host='0.0.0.0', port=8001, debug=False)
    except KeyboardInterrupt:
        print("\n서버가 중지되었습니다.")
    except Exception as e:
        print(f"서버 실행 중 오류: {e}") 