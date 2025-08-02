# 통합 WebSocket 실시간 시스템 가이드

## 📋 개요

이 가이드는 1단계부터 3단계까지 구현된 통합 WebSocket 실시간 시스템의 설치, 설정, 사용 방법을 설명합니다.

## 🚀 구현된 기능

### 1단계: WebSocket 실시간 통신 시스템
- **Flask-SocketIO 기반 WebSocket 서버**
- **실시간 양방향 통신**
- **룸 기반 클라이언트 관리**
- **종목별 구독 시스템**
- **실시간 대시보드**

### 2단계: 고급 알림 시스템
- **다중 채널 지원** (이메일, 슬랙, 텔레그램, 웹훅, 콘솔)
- **조건부 알림 규칙**
- **레이트 리밋 및 쿨다운**
- **알림 히스토리 관리**

### 3단계: 데이터베이스 시스템
- **PostgreSQL/TimescaleDB 지원**
- **시계열 데이터 최적화**
- **연결 풀링**
- **자동 데이터 정리**
- **성능 메트릭 저장**

## 📦 설치 및 설정

### 1. 의존성 설치

```bash
# 가상환경 활성화
source news_env/bin/activate

# WebSocket 시스템 의존성 설치
pip install -r requirements_websocket.txt
```

### 2. 데이터베이스 설정

#### PostgreSQL 설치 (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 사용자 생성 및 데이터베이스 생성
sudo -u postgres psql
CREATE USER trading_user WITH PASSWORD 'your_password';
CREATE DATABASE trading_data OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_data TO trading_user;
\q
```

#### TimescaleDB 설치 (선택사항)
```bash
# TimescaleDB 저장소 추가
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update

# TimescaleDB 설치
sudo apt install timescaledb-postgresql-13

# PostgreSQL 설정 최적화
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql
```

### 3. 알림 시스템 설정

#### 이메일 설정 (Gmail)
1. Gmail 계정에서 2단계 인증 활성화
2. 앱 비밀번호 생성
3. 설정 파일에 정보 입력

#### 슬랙 설정
1. 슬랙 워크스페이스에서 Incoming Webhook 생성
2. Webhook URL 복사
3. 설정 파일에 정보 입력

#### 텔레그램 설정
1. @BotFather에서 봇 생성
2. 봇 토큰 복사
3. 채팅 ID 확인 (@userinfobot 사용)
4. 설정 파일에 정보 입력

## ⚙️ 설정 파일

### 기본 설정 파일 생성
```bash
# 설정 파일 생성
cat > config.json << EOF
{
  "ws_port": 8084,
  "db_host": "localhost",
  "db_port": 5432,
  "db_name": "trading_data",
  "db_user": "trading_user",
  "db_password": "your_password",
  "notifications": {
    "email_enabled": false,
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "from_email": "your-email@gmail.com",
      "to_emails": ["recipient@example.com"]
    },
    "slack_enabled": false,
    "slack": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "channel": "#trading-alerts",
      "username": "Trading Bot"
    },
    "telegram_enabled": false,
    "telegram": {
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    }
  }
}
EOF
```

## 🚀 시스템 실행

### 1. 통합 시스템 실행
```bash
# 기본 설정으로 실행
python integrated_websocket_system.py

# 설정 파일로 실행
python integrated_websocket_system.py --config-file config.json

# 사용자 지정 포트로 실행
python integrated_websocket_system.py --ws-port 8085

# 특정 종목만 구독
python integrated_websocket_system.py --stocks 005930 000660 035420
```

### 2. 개별 컴포넌트 실행

#### WebSocket 서버만 실행
```bash
python websocket_server.py
```

#### 알림 시스템 테스트
```bash
python notification_system.py
```

#### 데이터베이스 테스트
```bash
python database_manager.py
```

## 📊 WebSocket 대시보드 사용법

### 1. 대시보드 접속
브라우저에서 `http://localhost:8084` 접속

### 2. WebSocket 연결
1. "연결" 버튼 클릭
2. 연결 상태 확인 (우상단 표시)

### 3. 종목 구독
1. "종목 구독" 섹션에서 종목 코드 입력
2. 쉼표로 구분하여 여러 종목 입력 (예: 005930,000660,035420)
3. "구독" 버튼 클릭

### 4. 실시간 데이터 확인
- 실시간 종목 데이터 테이블에서 업데이트 확인
- 실시간 차트에서 가격 변동 확인
- 통계 카드에서 시스템 상태 확인

## 🔔 알림 시스템 사용법

### 1. 알림 규칙 설정
기본 알림 규칙:
- **급등/급락 알림**: 등락률 5% 이상
- **거래량 급증 알림**: 평균 대비 3배 이상
- **시스템 오류 알림**: 오류 10개 이상

### 2. 커스텀 알림 규칙 추가
```python
from notification_system import AlertRule, AlertLevel, NotificationType

# 새로운 알림 규칙 정의
def custom_condition(data):
    return data.get('current_price', 0) > 100000

custom_rule = AlertRule(
    name="고가 종목 알림",
    condition=custom_condition,
    message_template="{name}({code}) 고가 종목: {current_price:,}원",
    level=AlertLevel.INFO,
    channels=[NotificationType.SLACK, NotificationType.TELEGRAM]
)

# 알림 시스템에 추가
notification_system.add_alert_rule(custom_rule)
```

## 🗄️ 데이터베이스 관리

### 1. 데이터 조회
```python
from database_manager import DatabaseManager

# 실시간 데이터 조회
data = db_manager.get_real_time_data(
    code="005930",
    start_time=datetime.now() - timedelta(hours=1),
    limit=1000
)

# 알림 히스토리 조회
alerts = db_manager.get_alert_history(
    rule_name="급등/급락 알림",
    start_time=datetime.now() - timedelta(days=1)
)

# 성능 메트릭 조회
metrics = db_manager.get_performance_metrics(
    metric_name="data_received",
    start_time=datetime.now() - timedelta(hours=24)
)
```

### 2. 데이터 내보내기
```python
# CSV로 내보내기
db_manager.export_to_csv('real_time_data', 'export_data.csv')

# 특정 조건으로 내보내기
db_manager.export_to_csv('alert_history', 'alerts.csv')
```

### 3. 데이터 정리
```python
# 30일 이전 데이터 정리
deleted_count = db_manager.cleanup_old_data(days=30)
print(f"삭제된 레코드: {deleted_count}개")
```

## 📈 성능 모니터링

### 1. 시스템 통계 확인
```python
# 데이터베이스 통계
stats = db_manager.get_data_statistics()
print(f"실시간 데이터: {stats['real_time_data_count']}개")
print(f"고유 종목: {stats['unique_stocks_count']}개")
print(f"알림 수: {stats['alert_count']}개")
```

### 2. 성능 메트릭 모니터링
- 데이터 수신률
- 처리 지연시간
- 오류 발생률
- 연결된 클라이언트 수

## 🔧 문제 해결

### 1. WebSocket 연결 실패
```bash
# 포트 확인
netstat -tulpn | grep 8084

# 방화벽 설정 확인
sudo ufw status
sudo ufw allow 8084
```

### 2. 데이터베이스 연결 오류
```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U trading_user -d trading_data
```

### 3. 알림 전송 실패
- 이메일: SMTP 설정 및 앱 비밀번호 확인
- 슬랙: Webhook URL 유효성 확인
- 텔레그램: 봇 토큰 및 채팅 ID 확인

### 4. 메모리 사용량 최적화
```python
# 데이터베이스 연결 풀 크기 조정
config.connection_pool_size = 5

# 캐시 크기 조정
config.cache_duration = 180  # 3분
```

## 📝 로그 확인

### 1. 시스템 로그
```bash
# 실시간 로그 확인
tail -f logs/system.log

# 오류 로그만 확인
grep "ERROR" logs/system.log
```

### 2. 데이터베이스 로그
```bash
# PostgreSQL 로그 확인
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

## 🔄 업그레이드 및 확장

### 1. 새로운 알림 채널 추가
```python
class DiscordNotifier:
    def __init__(self, config):
        self.webhook_url = config.get('webhook_url')
    
    def send(self, alert):
        # Discord Webhook 구현
        pass

# 알림 시스템에 추가
notification_system.add_notifier(NotificationType.DISCORD, discord_config)
```

### 2. 새로운 데이터 소스 추가
```python
# 새로운 데이터 수집기 구현
class CustomDataCollector:
    def collect_data(self):
        # 커스텀 데이터 수집 로직
        pass

# 통합 시스템에 추가
system.add_data_collector(CustomDataCollector())
```

## 📞 지원 및 문의

시스템 사용 중 문제가 발생하거나 개선 사항이 있으면 다음을 확인하세요:

1. **로그 파일**: `logs/` 디렉토리의 로그 파일 확인
2. **설정 파일**: `config.json` 설정 확인
3. **의존성**: `requirements_websocket.txt` 패키지 설치 확인
4. **데이터베이스**: PostgreSQL/TimescaleDB 연결 상태 확인

## 🎯 다음 단계

현재 구현된 시스템을 기반으로 다음과 같은 추가 기능을 고려할 수 있습니다:

1. **머신러닝 분석 엔진**: 가격 예측 모델 통합
2. **고급 차트 시스템**: TradingView 차트 위젯
3. **포트폴리오 관리**: 자산 배분 및 리스크 관리
4. **백테스팅 시스템**: 전략 성과 분석
5. **클라우드 배포**: Docker 및 Kubernetes 지원

---

**🚀 통합 WebSocket 실시간 시스템이 성공적으로 구현되었습니다!** 