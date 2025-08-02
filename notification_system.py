#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 알림 시스템
텔레그램, 이메일, 슬랙 등을 통한 거래 알림 및 시스템 모니터링
"""

import time
import threading
import queue
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

from error_handler import ErrorType, ErrorLevel, handle_error

class NotificationType(Enum):
    """알림 타입"""
    TRADE_EXECUTED = "거래 실행"
    POSITION_UPDATE = "포지션 업데이트"
    RISK_ALERT = "리스크 알림"
    SYSTEM_ERROR = "시스템 오류"
    PERFORMANCE_UPDATE = "성과 업데이트"
    MARKET_ALERT = "시장 알림"

class NotificationPriority(Enum):
    """알림 우선순위"""
    LOW = "낮음"
    MEDIUM = "보통"
    HIGH = "높음"
    CRITICAL = "긴급"

@dataclass
class NotificationMessage:
    """알림 메시지"""
    type: NotificationType
    priority: NotificationPriority
    title: str
    content: str
    timestamp: datetime
    metadata: Dict = None

@dataclass
class NotificationConfig:
    """알림 설정"""
    # 텔레그램 설정
    telegram_enabled: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # 이메일 설정
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    # 슬랙 설정
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#trading"
    
    # 알림 필터링
    min_priority: NotificationPriority = NotificationPriority.MEDIUM
    notification_types: List[NotificationType] = None
    quiet_hours: tuple = (22, 8)  # 22시~8시 조용한 시간
    
    # 알림 제한
    max_notifications_per_hour: int = 10
    cooldown_minutes: int = 5

class NotificationSystem:
    """실시간 알림 시스템"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.message_queue = queue.Queue()
        self.notification_history = []
        self.notification_count = 0
        self.last_notification_time = {}
        
        # 알림 스레드
        self.notification_thread = None
        self.is_running = False
        
        # 콜백 함수
        self.on_notification_sent = None
        
        logger.info("알림 시스템 초기화 완료")
    
    def start(self):
        """알림 시스템 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.notification_thread = threading.Thread(target=self._notification_loop, daemon=True)
        self.notification_thread.start()
        logger.info("알림 시스템 시작")
    
    def stop(self):
        """알림 시스템 중지"""
        self.is_running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=5)
        logger.info("알림 시스템 중지")
    
    def send_notification(self, notification_type: NotificationType, priority: NotificationPriority,
                         title: str, content: str, metadata: Dict = None):
        """알림 전송"""
        try:
            # 알림 필터링
            if not self._should_send_notification(notification_type, priority):
                return
            
            # 알림 메시지 생성
            message = NotificationMessage(
                type=notification_type,
                priority=priority,
                title=title,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # 큐에 추가
            self.message_queue.put(message)
            
        except Exception as e:
            handle_error(
                ErrorType.NOTIFICATION,
                "알림 전송 오류",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def send_trade_notification(self, code: str, action: str, quantity: int, price: float, 
                               profit_loss: float = 0.0):
        """거래 알림 전송"""
        title = f"거래 실행: {code}"
        content = f"""
🔔 거래 알림

종목: {code}
행동: {action}
수량: {quantity:,}주
가격: {price:,}원
수익/손실: {profit_loss:+,}원
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        priority = NotificationPriority.HIGH if abs(profit_loss) > 100000 else NotificationPriority.MEDIUM
        
        self.send_notification(
            NotificationType.TRADE_EXECUTED,
            priority,
            title,
            content,
            {
                'code': code,
                'action': action,
                'quantity': quantity,
                'price': price,
                'profit_loss': profit_loss
            }
        )
    
    def send_risk_alert(self, alert_type: str, message: str, risk_level: str = "보통"):
        """리스크 알림 전송"""
        title = f"리스크 알림: {alert_type}"
        content = f"""
⚠️ 리스크 알림

유형: {alert_type}
수준: {risk_level}
메시지: {message}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        priority_map = {
            "낮음": NotificationPriority.LOW,
            "보통": NotificationPriority.MEDIUM,
            "높음": NotificationPriority.HIGH,
            "매우 높음": NotificationPriority.CRITICAL
        }
        
        priority = priority_map.get(risk_level, NotificationPriority.MEDIUM)
        
        self.send_notification(
            NotificationType.RISK_ALERT,
            priority,
            title,
            content,
            {
                'alert_type': alert_type,
                'risk_level': risk_level,
                'message': message
            }
        )
    
    def send_performance_update(self, performance_data: Dict):
        """성과 업데이트 알림 전송"""
        title = "성과 업데이트"
        content = f"""
📊 성과 업데이트

총 수익률: {performance_data.get('total_return', 0):.2%}
일일 수익률: {performance_data.get('daily_return', 0):.2%}
승률: {performance_data.get('win_rate', 0):.2%}
총 거래 수: {performance_data.get('total_trades', 0)}
현재 포지션: {performance_data.get('current_positions', 0)}개
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        self.send_notification(
            NotificationType.PERFORMANCE_UPDATE,
            NotificationPriority.LOW,
            title,
            content,
            performance_data
        )
    
    def send_system_error(self, error_type: str, error_message: str, error_level: str = "보통"):
        """시스템 오류 알림 전송"""
        title = f"시스템 오류: {error_type}"
        content = f"""
🚨 시스템 오류

유형: {error_type}
수준: {error_level}
오류: {error_message}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        priority_map = {
            "낮음": NotificationPriority.LOW,
            "보통": NotificationPriority.MEDIUM,
            "높음": NotificationPriority.HIGH,
            "긴급": NotificationPriority.CRITICAL
        }
        
        priority = priority_map.get(error_level, NotificationPriority.MEDIUM)
        
        self.send_notification(
            NotificationType.SYSTEM_ERROR,
            priority,
            title,
            content,
            {
                'error_type': error_type,
                'error_level': error_level,
                'error_message': error_message
            }
        )
    
    def _notification_loop(self):
        """알림 처리 루프"""
        while self.is_running:
            try:
                # 큐에서 메시지 가져오기
                try:
                    message = self.message_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 알림 전송
                self._send_notification_message(message)
                
                # 히스토리에 추가
                self.notification_history.append(message)
                
                # 알림 카운트 증가
                self.notification_count += 1
                
                # 콜백 실행
                if self.on_notification_sent:
                    self.on_notification_sent(message)
                
            except Exception as e:
                handle_error(
                    ErrorType.NOTIFICATION,
                    "알림 처리 루프 오류",
                    exception=e,
                    error_level=ErrorLevel.MEDIUM
                )
                time.sleep(5)
    
    def _send_notification_message(self, message: NotificationMessage):
        """알림 메시지 전송"""
        try:
            # 텔레그램 전송
            if self.config.telegram_enabled:
                self._send_telegram_message(message)
            
            # 이메일 전송
            if self.config.email_enabled:
                self._send_email_message(message)
            
            # 슬랙 전송
            if self.config.slack_enabled:
                self._send_slack_message(message)
            
            logger.info(f"알림 전송 완료: {message.title}")
            
        except Exception as e:
            handle_error(
                ErrorType.NOTIFICATION,
                f"알림 메시지 전송 오류: {message.title}",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def _send_telegram_message(self, message: NotificationMessage):
        """텔레그램 메시지 전송"""
        try:
            if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
                return
            
            # 메시지 포맷팅
            formatted_message = self._format_telegram_message(message)
            
            # API 호출
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.config.telegram_chat_id,
                'text': formatted_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            handle_error(
                ErrorType.NOTIFICATION,
                "텔레그램 메시지 전송 오류",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def _send_email_message(self, message: NotificationMessage):
        """이메일 메시지 전송"""
        try:
            if not self.config.email_username or not self.config.email_password:
                return
            
            # 이메일 생성
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients or [])
            msg['Subject'] = f"[{message.priority.value}] {message.title}"
            
            # 메시지 본문
            body = self._format_email_message(message)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
        except Exception as e:
            handle_error(
                ErrorType.NOTIFICATION,
                "이메일 메시지 전송 오류",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def _send_slack_message(self, message: NotificationMessage):
        """슬랙 메시지 전송"""
        try:
            if not self.config.slack_webhook_url:
                return
            
            # 메시지 포맷팅
            slack_message = self._format_slack_message(message)
            
            # Webhook 호출
            response = requests.post(
                self.config.slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            handle_error(
                ErrorType.NOTIFICATION,
                "슬랙 메시지 전송 오류",
                exception=e,
                error_level=ErrorLevel.MEDIUM
            )
    
    def _format_telegram_message(self, message: NotificationMessage) -> str:
        """텔레그램 메시지 포맷팅"""
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🚨",
            NotificationPriority.CRITICAL: "🔥"
        }
        
        emoji = priority_emoji.get(message.priority, "ℹ️")
        
        return f"""
{emoji} <b>{message.title}</b>

{message.content}

📅 {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    def _format_email_message(self, message: NotificationMessage) -> str:
        """이메일 메시지 포맷팅"""
        return f"""
{message.title}

{message.content}

우선순위: {message.priority.value}
시간: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

---
자동매매 시스템 알림
        """.strip()
    
    def _format_slack_message(self, message: NotificationMessage) -> Dict:
        """슬랙 메시지 포맷팅"""
        priority_color = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.MEDIUM: "#ff9500",
            NotificationPriority.HIGH: "#ff0000",
            NotificationPriority.CRITICAL: "#8b0000"
        }
        
        color = priority_color.get(message.priority, "#36a64f")
        
        return {
            "channel": self.config.slack_channel,
            "attachments": [
                {
                    "color": color,
                    "title": message.title,
                    "text": message.content,
                    "footer": "자동매매 시스템",
                    "ts": int(message.timestamp.timestamp())
                }
            ]
        }
    
    def _should_send_notification(self, notification_type: NotificationType, 
                                 priority: NotificationPriority) -> bool:
        """알림 전송 여부 확인"""
        # 우선순위 체크
        if priority.value < self.config.min_priority.value:
            return False
        
        # 알림 타입 체크
        if (self.config.notification_types and 
            notification_type not in self.config.notification_types):
            return False
        
        # 조용한 시간 체크
        if self._is_quiet_hours():
            return False
        
        # 알림 제한 체크
        if not self._check_notification_limit(notification_type):
            return False
        
        return True
    
    def _is_quiet_hours(self) -> bool:
        """조용한 시간 여부 확인"""
        now = datetime.now()
        start_hour, end_hour = self.config.quiet_hours
        
        if start_hour > end_hour:  # 자정을 걸치는 경우
            return now.hour >= start_hour or now.hour < end_hour
        else:
            return start_hour <= now.hour < end_hour
    
    def _check_notification_limit(self, notification_type: NotificationType) -> bool:
        """알림 제한 체크"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # 시간당 알림 수 체크
        recent_notifications = [
            msg for msg in self.notification_history
            if msg.timestamp >= hour_ago
        ]
        
        if len(recent_notifications) >= self.config.max_notifications_per_hour:
            return False
        
        # 쿨다운 체크
        last_time = self.last_notification_time.get(notification_type)
        if last_time:
            time_diff = now - last_time
            if time_diff.total_seconds() < self.config.cooldown_minutes * 60:
                return False
        
        self.last_notification_time[notification_type] = now
        return True
    
    def get_notification_stats(self) -> Dict:
        """알림 통계 반환"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        hourly_count = len([msg for msg in self.notification_history if msg.timestamp >= hour_ago])
        daily_count = len([msg for msg in self.notification_history if msg.timestamp >= day_ago])
        
        type_counts = {}
        for msg in self.notification_history:
            msg_type = msg.type.value
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        return {
            'total_notifications': len(self.notification_history),
            'hourly_notifications': hourly_count,
            'daily_notifications': daily_count,
            'type_distribution': type_counts,
            'queue_size': self.message_queue.qsize()
        }
    
    def clear_notification_history(self):
        """알림 히스토리 초기화"""
        self.notification_history.clear()
        self.notification_count = 0
        self.last_notification_time.clear()
        logger.info("알림 히스토리 초기화")

def main():
    """테스트 함수"""
    # 알림 설정
    config = NotificationConfig(
        telegram_enabled=True,
        telegram_bot_token="YOUR_BOT_TOKEN",
        telegram_chat_id="YOUR_CHAT_ID",
        email_enabled=False,
        slack_enabled=False,
        min_priority=NotificationPriority.MEDIUM
    )
    
    # 알림 시스템 생성
    notification_system = NotificationSystem(config)
    
    # 알림 시스템 시작
    notification_system.start()
    
    # 테스트 알림 전송
    notification_system.send_trade_notification(
        "005930", "매수", 10, 70000, 50000
    )
    
    notification_system.send_risk_alert(
        "높은 손실률", "삼성전자 손실률이 10%를 초과했습니다.", "높음"
    )
    
    notification_system.send_performance_update({
        'total_return': 0.15,
        'daily_return': 0.02,
        'win_rate': 0.65,
        'total_trades': 25,
        'current_positions': 3
    })
    
    # 잠시 대기
    time.sleep(5)
    
    # 통계 출력
    stats = notification_system.get_notification_stats()
    logger.info(f"알림 통계: {stats}")
    
    # 알림 시스템 중지
    notification_system.stop()

if __name__ == "__main__":
    main() 