#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 알림 시스템
다양한 채널을 통한 실시간 알림 시스템
"""

import smtplib
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

class NotificationType(Enum):
    """알림 타입"""
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    CONSOLE = "console"

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class NotificationConfig:
    """알림 설정"""
    type: NotificationType
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 5.0
    rate_limit: int = 10  # 분당 최대 알림 수
    cooldown: int = 300   # 동일 알림 재발송 대기 시간 (초)

@dataclass
class AlertRule:
    """알림 규칙"""
    name: str
    condition: Callable
    message_template: str
    level: AlertLevel
    channels: List[NotificationType]
    enabled: bool = True
    cooldown: int = 300  # 초

@dataclass
class Alert:
    """알림 정보"""
    id: str
    rule_name: str
    message: str
    level: AlertLevel
    timestamp: datetime
    data: Dict = None

class EmailNotifier:
    """이메일 알림기"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email')
        self.to_emails = config.get('to_emails', [])
        
    def send(self, alert: Alert) -> bool:
        """이메일 전송"""
        try:
            if not self.username or not self.password:
                logger.error("이메일 설정이 완료되지 않았습니다.")
                return False
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.rule_name}"
            
            # HTML 본문 생성
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .alert {{ padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .alert-info {{ background-color: #d1ecf1; border: 1px solid #bee5eb; }}
                    .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
                    .alert-error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
                    .alert-critical {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
                    .timestamp {{ color: #6c757d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="alert alert-{alert.level.value}">
                    <h3>{alert.rule_name}</h3>
                    <p>{alert.message}</p>
                    <div class="timestamp">
                        발생 시간: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"이메일 알림 전송 완료: {alert.rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False

class SlackNotifier:
    """슬랙 알림기"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#general')
        self.username = config.get('username', 'Trading Bot')
        
    def send(self, alert: Alert) -> bool:
        """슬랙 메시지 전송"""
        try:
            if not self.webhook_url:
                logger.error("슬랙 Webhook URL이 설정되지 않았습니다.")
                return False
            
            # 색상 설정
            color_map = {
                AlertLevel.INFO: '#36a64f',
                AlertLevel.WARNING: '#ffa500',
                AlertLevel.ERROR: '#ff0000',
                AlertLevel.CRITICAL: '#8b0000'
            }
            
            # 슬랙 메시지 생성
            message = {
                "channel": self.channel,
                "username": self.username,
                "attachments": [{
                    "color": color_map.get(alert.level, '#36a64f'),
                    "title": f"[{alert.level.value.upper()}] {alert.rule_name}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "발생 시간",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "Trading Bot",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            # Webhook으로 전송
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"슬랙 알림 전송 완료: {alert.rule_name}")
                return True
            else:
                logger.error(f"슬랙 전송 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"슬랙 전송 오류: {e}")
            return False

class TelegramNotifier:
    """텔레그램 알림기"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.bot_token = config.get('bot_token')
        self.chat_id = config.get('chat_id')
        
    def send(self, alert: Alert) -> bool:
        """텔레그램 메시지 전송"""
        try:
            if not self.bot_token or not self.chat_id:
                logger.error("텔레그램 설정이 완료되지 않았습니다.")
                return False
            
            # 메시지 생성
            message = f"""
🚨 *{alert.rule_name}*
{alert.message}

⏰ {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            # 텔레그램 API 호출
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"텔레그램 알림 전송 완료: {alert.rule_name}")
                return True
            else:
                logger.error(f"텔레그램 전송 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"텔레그램 전송 오류: {e}")
            return False

class WebhookNotifier:
    """웹훅 알림기"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        
    def send(self, alert: Alert) -> bool:
        """웹훅 전송"""
        try:
            if not self.webhook_url:
                logger.error("웹훅 URL이 설정되지 않았습니다.")
                return False
            
            # 웹훅 데이터 생성
            data = {
                'alert_id': alert.id,
                'rule_name': alert.rule_name,
                'message': alert.message,
                'level': alert.level.value,
                'timestamp': alert.timestamp.isoformat(),
                'data': alert.data or {}
            }
            
            # 웹훅 전송
            response = requests.post(
                self.webhook_url,
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"웹훅 알림 전송 완료: {alert.rule_name}")
                return True
            else:
                logger.error(f"웹훅 전송 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"웹훅 전송 오류: {e}")
            return False

class ConsoleNotifier:
    """콘솔 알림기"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
    def send(self, alert: Alert) -> bool:
        """콘솔 출력"""
        try:
            # 색상 코드
            colors = {
                AlertLevel.INFO: '\033[94m',      # 파란색
                AlertLevel.WARNING: '\033[93m',   # 노란색
                AlertLevel.ERROR: '\033[91m',     # 빨간색
                AlertLevel.CRITICAL: '\033[95m'   # 자주색
            }
            reset = '\033[0m'
            
            color = colors.get(alert.level, '')
            
            print(f"{color}[{alert.level.value.upper()}] {alert.rule_name}{reset}")
            print(f"  {alert.message}")
            print(f"  시간: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            return True
            
        except Exception as e:
            logger.error(f"콘솔 출력 오류: {e}")
            return False

class NotificationSystem:
    """고급 알림 시스템"""
    
    def __init__(self):
        self.notifiers = {}
        self.alert_rules = []
        self.sent_alerts = {}  # {alert_id: last_sent_time}
        self.rate_limit_counters = {}  # {notifier_type: {count: int, reset_time: datetime}}
        self.running = False
        self.alert_queue = []
        self.queue_lock = threading.Lock()
        
        # 알림 처리 스레드
        self.processing_thread = None
        
    def add_notifier(self, notifier_type: NotificationType, config: Dict):
        """알림기 추가"""
        try:
            if notifier_type == NotificationType.EMAIL:
                self.notifiers[notifier_type] = EmailNotifier(config)
            elif notifier_type == NotificationType.SLACK:
                self.notifiers[notifier_type] = SlackNotifier(config)
            elif notifier_type == NotificationType.TELEGRAM:
                self.notifiers[notifier_type] = TelegramNotifier(config)
            elif notifier_type == NotificationType.WEBHOOK:
                self.notifiers[notifier_type] = WebhookNotifier(config)
            elif notifier_type == NotificationType.CONSOLE:
                self.notifiers[notifier_type] = ConsoleNotifier(config)
            
            logger.info(f"알림기 추가 완료: {notifier_type.value}")
            
        except Exception as e:
            logger.error(f"알림기 추가 실패: {notifier_type.value} - {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        self.alert_rules.append(rule)
        logger.info(f"알림 규칙 추가: {rule.name}")
    
    def check_alerts(self, data: Dict):
        """알림 조건 확인"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            try:
                # 조건 확인
                if rule.condition(data):
                    # 알림 생성
                    alert = Alert(
                        id=f"{rule.name}_{int(time.time())}",
                        rule_name=rule.name,
                        message=rule.message_template.format(**data),
                        level=rule.level,
                        timestamp=datetime.now(),
                        data=data
                    )
                    
                    # 알림 큐에 추가
                    with self.queue_lock:
                        self.alert_queue.append(alert)
                    
            except Exception as e:
                logger.error(f"알림 규칙 실행 오류: {rule.name} - {e}")
    
    def start(self):
        """알림 시스템 시작"""
        if self.running:
            return
            
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.processing_thread.start()
        
        logger.info("알림 시스템 시작")
    
    def stop(self):
        """알림 시스템 중지"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        logger.info("알림 시스템 중지")
    
    def _process_alerts(self):
        """알림 처리 스레드"""
        while self.running:
            try:
                # 큐에서 알림 가져오기
                alert = None
                with self.queue_lock:
                    if self.alert_queue:
                        alert = self.alert_queue.pop(0)
                
                if alert:
                    self._send_alert(alert)
                
                time.sleep(1)  # 1초 대기
                
            except Exception as e:
                logger.error(f"알림 처리 오류: {e}")
                time.sleep(5)
    
    def _send_alert(self, alert: Alert):
        """알림 전송"""
        # 쿨다운 확인
        if not self._check_cooldown(alert):
            return
        
        # 각 채널로 전송
        for notifier_type, notifier in self.notifiers.items():
            try:
                # 레이트 리밋 확인
                if not self._check_rate_limit(notifier_type):
                    continue
                
                # 알림 전송
                success = notifier.send(alert)
                
                if success:
                    # 전송 성공 기록
                    self.sent_alerts[alert.id] = datetime.now()
                    self._update_rate_limit(notifier_type)
                    
            except Exception as e:
                logger.error(f"알림 전송 오류: {notifier_type.value} - {e}")
    
    def _check_cooldown(self, alert: Alert) -> bool:
        """쿨다운 확인"""
        if alert.id in self.sent_alerts:
            last_sent = self.sent_alerts[alert.id]
            cooldown_seconds = 300  # 기본 5분
            
            if (datetime.now() - last_sent).seconds < cooldown_seconds:
                return False
        
        return True
    
    def _check_rate_limit(self, notifier_type: NotificationType) -> bool:
        """레이트 리밋 확인"""
        if notifier_type not in self.rate_limit_counters:
            self.rate_limit_counters[notifier_type] = {
                'count': 0,
                'reset_time': datetime.now() + timedelta(minutes=1)
            }
        
        counter = self.rate_limit_counters[notifier_type]
        
        # 리셋 시간 확인
        if datetime.now() >= counter['reset_time']:
            counter['count'] = 0
            counter['reset_time'] = datetime.now() + timedelta(minutes=1)
        
        # 레이트 리밋 확인 (분당 10개)
        return counter['count'] < 10
    
    def _update_rate_limit(self, notifier_type: NotificationType):
        """레이트 리밋 업데이트"""
        if notifier_type in self.rate_limit_counters:
            self.rate_limit_counters[notifier_type]['count'] += 1

# 기본 알림 규칙들
def create_default_alert_rules():
    """기본 알림 규칙 생성"""
    rules = []
    
    # 급등/급락 알림
    def price_volatility_condition(data):
        return abs(data.get('change_rate', 0)) > 5.0
    
    rules.append(AlertRule(
        name="급등/급락 알림",
        condition=price_volatility_condition,
        message_template="{name}({code}) 급격한 가격 변동: {change_rate:+.2f}%",
        level=AlertLevel.WARNING,
        channels=[NotificationType.EMAIL, NotificationType.SLACK, NotificationType.TELEGRAM]
    ))
    
    # 거래량 급증 알림
    def volume_surge_condition(data):
        volume_ratio = data.get('volume_ratio', 1.0)
        return volume_ratio > 3.0
    
    rules.append(AlertRule(
        name="거래량 급증 알림",
        condition=volume_surge_condition,
        message_template="{name}({code}) 거래량 급증: 평균 대비 {volume_ratio:.1f}배",
        level=AlertLevel.INFO,
        channels=[NotificationType.SLACK, NotificationType.TELEGRAM]
    ))
    
    # 시스템 오류 알림
    def system_error_condition(data):
        return data.get('error_count', 0) > 10
    
    rules.append(AlertRule(
        name="시스템 오류 알림",
        condition=system_error_condition,
        message_template="시스템 오류 발생: {error_count}개 오류 감지",
        level=AlertLevel.ERROR,
        channels=[NotificationType.EMAIL, NotificationType.SLACK, NotificationType.TELEGRAM]
    ))
    
    return rules

def main():
    """테스트용 메인 함수"""
    # 알림 시스템 초기화
    notification_system = NotificationSystem()
    
    # 알림기 설정
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from_email': 'your-email@gmail.com',
        'to_emails': ['recipient@example.com']
    }
    
    slack_config = {
        'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
        'channel': '#trading-alerts',
        'username': 'Trading Bot'
    }
    
    telegram_config = {
        'bot_token': 'YOUR_BOT_TOKEN',
        'chat_id': 'YOUR_CHAT_ID'
    }
    
    # 알림기 추가
    notification_system.add_notifier(NotificationType.EMAIL, email_config)
    notification_system.add_notifier(NotificationType.SLACK, slack_config)
    notification_system.add_notifier(NotificationType.TELEGRAM, telegram_config)
    notification_system.add_notifier(NotificationType.CONSOLE, {})
    
    # 기본 알림 규칙 추가
    for rule in create_default_alert_rules():
        notification_system.add_alert_rule(rule)
    
    # 알림 시스템 시작
    notification_system.start()
    
    # 테스트 알림
    test_data = {
        'code': '005930',
        'name': '삼성전자',
        'change_rate': 7.5,
        'volume_ratio': 4.2,
        'error_count': 15
    }
    
    notification_system.check_alerts(test_data)
    
    # 10초 대기 후 종료
    time.sleep(10)
    notification_system.stop()

if __name__ == "__main__":
    main() 