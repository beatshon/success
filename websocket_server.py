#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 실시간 통신 서버
Flask-SocketIO 기반 실시간 데이터 전송 시스템
"""

import sys
import time
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from loguru import logger

# 프로젝트 모듈 import
from real_time_data_collector import RealTimeDataCollector, RealTimeData
from error_handler import ErrorType, ErrorLevel, handle_error

class WebSocketServer:
    """WebSocket 실시간 통신 서버"""
    
    def __init__(self, port: int = 8084):
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'kiwoom_trading_websocket_secret'
        CORS(self.app)
        
        # SocketIO 초기화
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # 데이터 수집기
        self.collector = None
        self.running = False
        
        # 클라이언트 관리
        self.clients = {}  # {client_id: {'room': room, 'subscriptions': []}}
        self.rooms = {}    # {room: [client_ids]}
        
        # 라우트 및 이벤트 핸들러 설정
        self._setup_routes()
        self._setup_socket_events()
        
    def _setup_routes(self):
        """HTTP 라우트 설정"""
        
        @self.app.route('/')
        def index():
            return {'status': 'WebSocket Server Running', 'timestamp': datetime.now().isoformat()}
        
        @self.app.route('/health')
        def health_check():
            return {
                'status': 'healthy',
                'clients_count': len(self.clients),
                'rooms_count': len(self.rooms),
                'collector_running': self.collector.running if self.collector else False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _setup_socket_events(self):
        """SocketIO 이벤트 핸들러 설정"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """클라이언트 연결 처리"""
            client_id = request.sid
            logger.info(f"클라이언트 연결: {client_id}")
            
            # 클라이언트 정보 초기화
            self.clients[client_id] = {
                'room': None,
                'subscriptions': [],
                'connected_at': datetime.now()
            }
            
            # 연결 확인 메시지 전송
            emit('connected', {
                'client_id': client_id,
                'message': 'WebSocket 연결 성공',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """클라이언트 연결 해제 처리"""
            client_id = request.sid
            logger.info(f"클라이언트 연결 해제: {client_id}")
            
            # 클라이언트 정보 정리
            if client_id in self.clients:
                # 룸에서 제거
                room = self.clients[client_id].get('room')
                if room and room in self.rooms:
                    if client_id in self.rooms[room]:
                        self.rooms[room].remove(client_id)
                    if not self.rooms[room]:
                        del self.rooms[room]
                
                # 클라이언트 정보 삭제
                del self.clients[client_id]
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """룸 참가 처리"""
            client_id = request.sid
            room = data.get('room', 'default')
            
            logger.info(f"클라이언트 {client_id}가 룸 {room}에 참가")
            
            # 기존 룸에서 제거
            if client_id in self.clients:
                old_room = self.clients[client_id].get('room')
                if old_room and old_room in self.rooms:
                    if client_id in self.rooms[old_room]:
                        self.rooms[old_room].remove(client_id)
                    if not self.rooms[old_room]:
                        del self.rooms[old_room]
            
            # 새 룸에 추가
            join_room(room)
            self.clients[client_id]['room'] = room
            
            if room not in self.rooms:
                self.rooms[room] = []
            self.rooms[room].append(client_id)
            
            # 룸 참가 확인 메시지
            emit('room_joined', {
                'room': room,
                'message': f'룸 {room}에 참가했습니다',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """룸 나가기 처리"""
            client_id = request.sid
            room = data.get('room', 'default')
            
            logger.info(f"클라이언트 {client_id}가 룸 {room}에서 나감")
            
            leave_room(room)
            
            if client_id in self.clients:
                self.clients[client_id]['room'] = None
            
            if room in self.rooms and client_id in self.rooms[room]:
                self.rooms[room].remove(client_id)
                if not self.rooms[room]:
                    del self.rooms[room]
            
            emit('room_left', {
                'room': room,
                'message': f'룸 {room}에서 나갔습니다',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('subscribe_stocks')
        def handle_subscribe_stocks(data):
            """종목 구독 처리"""
            client_id = request.sid
            stocks = data.get('stocks', [])
            
            logger.info(f"클라이언트 {client_id}가 종목 {stocks} 구독")
            
            if client_id in self.clients:
                self.clients[client_id]['subscriptions'] = stocks
            
            # 데이터 수집기에 구독 요청
            if self.collector and stocks:
                self.collector.subscribe(stocks)
            
            emit('stocks_subscribed', {
                'stocks': stocks,
                'message': f'{len(stocks)}개 종목 구독 완료',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('unsubscribe_stocks')
        def handle_unsubscribe_stocks(data):
            """종목 구독 해제 처리"""
            client_id = request.sid
            stocks = data.get('stocks', [])
            
            logger.info(f"클라이언트 {client_id}가 종목 {stocks} 구독 해제")
            
            if client_id in self.clients:
                current_subscriptions = self.clients[client_id].get('subscriptions', [])
                self.clients[client_id]['subscriptions'] = [
                    s for s in current_subscriptions if s not in stocks
                ]
            
            # 데이터 수집기에서 구독 해제
            if self.collector and stocks:
                self.collector.unsubscribe(stocks)
            
            emit('stocks_unsubscribed', {
                'stocks': stocks,
                'message': f'{len(stocks)}개 종목 구독 해제 완료',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('request_data')
        def handle_request_data(data):
            """데이터 요청 처리"""
            client_id = request.sid
            data_type = data.get('type', 'all')
            
            logger.info(f"클라이언트 {client_id}가 {data_type} 데이터 요청")
            
            if not self.collector:
                emit('error', {'message': '데이터 수집기가 초기화되지 않았습니다'})
                return
            
            if data_type == 'all':
                all_data = self.collector.get_all_data()
                emit('data_response', {
                    'type': 'all',
                    'data': self._serialize_data(all_data),
                    'timestamp': datetime.now().isoformat()
                })
            elif data_type == 'stats':
                stats = self.collector.get_stats()
                emit('data_response', {
                    'type': 'stats',
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('ping')
        def handle_ping():
            """핑 요청 처리"""
            emit('pong', {
                'timestamp': datetime.now().isoformat()
            })
    
    def _serialize_data(self, data_dict: Dict) -> List[Dict]:
        """데이터 직렬화"""
        serialized = []
        for code, data in data_dict.items():
            if isinstance(data, RealTimeData):
                serialized.append({
                    'code': data.code,
                    'name': data.name,
                    'current_price': data.current_price,
                    'change_rate': data.change_rate,
                    'volume': data.volume,
                    'amount': data.amount,
                    'open_price': data.open_price,
                    'high_price': data.high_price,
                    'low_price': data.low_price,
                    'prev_close': data.prev_close,
                    'timestamp': data.timestamp.isoformat(),
                    'data_type': data.data_type
                })
        return serialized
    
    def broadcast_data(self, event: str, data: Dict, room: str = None):
        """데이터 브로드캐스트"""
        try:
            if room:
                self.socketio.emit(event, data, room=room)
            else:
                self.socketio.emit(event, data)
        except Exception as e:
            logger.error(f"데이터 브로드캐스트 오류: {e}")
    
    def broadcast_to_subscribers(self, stock_code: str, data: Dict):
        """특정 종목 구독자에게 데이터 전송"""
        try:
            subscribers = []
            for client_id, client_info in self.clients.items():
                if stock_code in client_info.get('subscriptions', []):
                    subscribers.append(client_id)
            
            if subscribers:
                self.socketio.emit('stock_update', {
                    'code': stock_code,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=None, include_self=False)
                
                # 구독자들에게만 전송
                for client_id in subscribers:
                    self.socketio.emit('stock_update', {
                        'code': stock_code,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }, room=client_id)
                    
        except Exception as e:
            logger.error(f"구독자 데이터 전송 오류: {e}")
    
    def set_collector(self, collector: RealTimeDataCollector):
        """데이터 수집기 설정"""
        self.collector = collector
        
        # 데이터 처리 콜백 등록
        def on_data_processed(data: RealTimeData, processed_data: Dict):
            try:
                # 실시간 데이터 브로드캐스트
                self.broadcast_to_subscribers(data.code, {
                    'current_price': data.current_price,
                    'change_rate': data.change_rate,
                    'volume': data.volume,
                    'timestamp': data.timestamp.isoformat()
                })
                
                # 전체 데이터 업데이트 (30초마다)
                if hasattr(self, '_last_broadcast_time'):
                    if (datetime.now() - self._last_broadcast_time).seconds >= 30:
                        all_data = self.collector.get_all_data()
                        self.broadcast_data('market_update', {
                            'data': self._serialize_data(all_data),
                            'timestamp': datetime.now().isoformat()
                        })
                        self._last_broadcast_time = datetime.now()
                else:
                    self._last_broadcast_time = datetime.now()
                    
            except Exception as e:
                logger.error(f"데이터 처리 콜백 오류: {e}")
        
        self.collector.add_callback('data_processed', on_data_processed)
    
    def start(self):
        """서버 시작"""
        try:
            logger.info(f"WebSocket 서버 시작: http://localhost:{self.port}")
            self.running = True
            self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False)
        except Exception as e:
            handle_error(
                ErrorType.INITIALIZATION,
                "WebSocket 서버 시작 실패",
                exception=e,
                error_level=ErrorLevel.CRITICAL
            )
            raise
    
    def stop(self):
        """서버 중지"""
        try:
            self.running = False
            logger.info("WebSocket 서버 중지")
        except Exception as e:
            logger.error(f"WebSocket 서버 중지 오류: {e}")

def main():
    """메인 함수"""
    try:
        # WebSocket 서버 초기화
        ws_server = WebSocketServer(port=8084)
        
        # 서버 시작
        ws_server.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ WebSocket 서버 중지")
        ws_server.stop()
    except Exception as e:
        logger.error(f"WebSocket 서버 실행 오류: {e}")
        ws_server.stop()

if __name__ == "__main__":
    main() 