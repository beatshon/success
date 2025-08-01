# 하이브리드 자동매매 시스템 사용법

## 🎯 개요

하이브리드 자동매매 시스템은 맥에서 시뮬레이션하고 Windows 서버에 반영하여 QA 후 실제 거래를 제어하는 시스템입니다.

## 🏗️ 시스템 구조

```
맥 (개발/테스트) ←→ Windows (실제 거래)
     ↓                    ↓
시뮬레이션 환경      키움 API 서버
     ↓                    ↓
전략 테스트          실제 주문 실행
     ↓                    ↓
QA 검증              거래 결과 반영
```

## 🚀 시작하기

### 1. 시스템 시작

```bash
# 하이브리드 시스템 시작
./start_hybrid_system.sh
```

### 2. Windows 서버 설정

Windows 환경에서 다음 명령어로 API 서버를 시작합니다:

```bash
# Windows API 서버 시작
python windows_api_server.py --host 0.0.0.0 --port 8080
```

### 3. 설정 파일 구성

`config/hybrid_config.json` 파일을 생성하여 설정을 구성합니다:

```json
{
  "windows_server": {
    "host": "192.168.1.100",
    "port": 8080,
    "api_key": "your_api_key_here",
    "timeout": 30
  },
  "trading": {
    "max_positions": 5,
    "default_trade_amount": 100000,
    "update_interval": 60,
    "risk_management": {
      "max_loss_per_trade": 0.02,
      "max_daily_loss": 0.05,
      "stop_loss": 0.03
    }
  },
  "sync": {
    "enabled": true,
    "interval": 30,
    "auto_sync": true
  },
  "simulation": {
    "enabled": true,
    "realistic_mode": true,
    "demo_account": "1234567890"
  }
}
```

## 📋 사용법

### 기본 명령어

```bash
# QA 프로세스 실행 (권장)
python mac_hybrid_controller.py --action qa

# 맥 시뮬레이션만 실행
python mac_hybrid_controller.py --action simulation

# Windows 동기화만 실행
python mac_hybrid_controller.py --action sync

# Windows 실제 거래 시작
python mac_hybrid_controller.py --action start-windows

# Windows 실제 거래 중지
python mac_hybrid_controller.py --action stop-windows

# 상태 확인
python mac_hybrid_controller.py --action status
```

### 전략별 실행

```bash
# 이동평균 전략
python mac_hybrid_controller.py --action qa --strategy moving_average

# RSI 전략
python mac_hybrid_controller.py --action qa --strategy rsi

# 볼린저 밴드 전략
python mac_hybrid_controller.py --action qa --strategy bollinger
```

### 설정 파일 사용

```bash
# 커스텀 설정 파일 사용
python mac_hybrid_controller.py --action qa --config my_strategy.json
```

### 거래 승인 예시

QA 프로세스 실행 시 다음과 같은 옵션이 제공됩니다:

```
🔍 QA 검증 결과
============================================================
맥 시뮬레이션: 실행 중
Windows 연결: connected
시뮬레이션 기간: 30초
거래 횟수: 5회
수익률: 2.35%
최대 손실: 1.20%
============================================================

거래 승인 옵션:
1) 전체 거래 승인 - 모든 시뮬레이션 거래를 실제로 실행
2) 선택적 거래 승인 - 승인할 거래를 선택
3) 거래 취소 - 실제 거래 실행하지 않음
4) 추가 시뮬레이션 - 더 오래 시뮬레이션 실행

선택하세요 (1-4): 2

📋 시뮬레이션 거래 목록
================================================================================
번호 시간         종목       액션   수량   가격        금액
--------------------------------------------------------------------------------
1    14:30:15    005930     매수   1     70000      70,000
2    14:31:22    000660     매수   1     120000     120,000
3    14:32:45    005930     매도   1     70500      70,500
4    14:33:12    035420     매수   1     200000     200,000
5    14:34:30    000660     매도   1     121000     121,000
================================================================================

승인할 거래 번호를 입력하세요 (쉼표로 구분, 'all' = 전체 선택):
선택: 1,3,5
✅ 선택적 거래 승인 완료 (3건)
```

## 🔄 QA 프로세스

### 1단계: 맥 시뮬레이션
- 맥에서 시뮬레이션 환경으로 거래 전략 테스트
- 실제 시장 데이터와 유사한 환경에서 전략 검증
- 리스크 관리 및 성과 분석

### 2단계: Windows 동기화
- 시뮬레이션 결과를 Windows 서버에 전송
- 계좌 정보, 예수금, 전략 설정 동기화
- 거래 이력 및 포지션 정보 전달

### 3단계: QA 검증 및 거래 승인
- 시뮬레이션 결과 상세 분석
- 수익률, 거래 횟수, 최대 손실 등 성과 지표 확인
- Windows 서버 연결 상태 확인
- 거래 승인 옵션 선택

### 4단계: 거래 승인 및 실행 (선택사항)

#### 4-1. 전체 거래 승인
- 시뮬레이션에서 실행된 모든 거래를 실제로 승인
- Windows에서 자동매매 시스템 시작
- 키움 API를 통한 자동 주문 실행

#### 4-2. 선택적 거래 승인
- 시뮬레이션 거래 목록에서 승인할 거래 선택
- 개별 거래별로 매수/매도 주문 실행
- 승인되지 않은 거래는 실행하지 않음

#### 4-3. 거래 취소
- 실제 거래 실행하지 않음
- 시뮬레이션 결과만 확인

#### 4-4. 추가 시뮬레이션
- 더 오래 시뮬레이션 실행
- 추가 데이터로 전략 검증

## 📊 모니터링

### 상태 확인

```bash
# 전체 시스템 상태 확인
python mac_hybrid_controller.py --action status
```

출력 예시:
```json
{
  "mac_simulation": {
    "running": true,
    "status": "running"
  },
  "windows_connection": {
    "status": "connected",
    "last_sync": "2024-01-01T12:00:00"
  },
  "windows_server": {
    "status": "running",
    "trading_status": "stopped"
  }
}
```

### 로그 확인

```bash
# 맥 하이브리드 제어 로그
tail -f logs/mac_hybrid_controller.log

# 하이브리드 시스템 로그
tail -f logs/hybrid_trading.log

# Windows API 서버 로그 (Windows 환경)
tail -f logs/windows_api_server.log
```

## ⚙️ 고급 설정

### 리스크 관리

```json
{
  "risk_management": {
    "max_loss_per_trade": 0.02,    // 거래당 최대 손실 2%
    "max_daily_loss": 0.05,        // 일일 최대 손실 5%
    "stop_loss": 0.03,             // 손절 기준 3%
    "max_positions": 5,            // 최대 보유 종목 수
    "position_sizing": 0.1         // 포지션 크기 10%
  }
}
```

### 동기화 설정

```json
{
  "sync": {
    "enabled": true,
    "interval": 30,                // 동기화 주기 (초)
    "auto_sync": true,             // 자동 동기화
    "retry_count": 3,              // 재시도 횟수
    "timeout": 30                  // 타임아웃 (초)
  }
}
```

## 🔧 문제 해결

### Windows 서버 연결 실패

1. Windows 서버가 실행 중인지 확인
2. 네트워크 연결 상태 확인
3. 방화벽 설정 확인
4. API 키 설정 확인

```bash
# Windows 서버 상태 확인
curl http://192.168.1.100:8080/api/health
```

### 시뮬레이션 오류

1. Python 패키지 설치 확인
2. 로그 파일 확인
3. 설정 파일 유효성 검사

```bash
# 패키지 설치 확인
pip install -r requirements.txt

# 로그 확인
tail -f logs/mac_hybrid_controller.log
```

### 실제 거래 오류

1. 키움 API 로그인 상태 확인
2. 계좌 정보 및 예수금 확인
3. 주문 가능 시간 확인

## 📈 성능 최적화

### 시뮬레이션 성능

- 시뮬레이션 주기 조정
- 불필요한 로그 레벨 조정
- 메모리 사용량 모니터링

### 네트워크 성능

- 동기화 주기 최적화
- 데이터 압축 사용
- 연결 풀링 설정

## 🔒 보안 고려사항

1. **API 키 보안**: API 키를 안전하게 관리
2. **네트워크 보안**: HTTPS 사용 권장
3. **접근 제어**: IP 화이트리스트 설정
4. **로그 보안**: 민감한 정보 로그 제외

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. 로그 파일 확인
2. 네트워크 연결 상태 확인
3. 설정 파일 유효성 검사
4. Windows 서버 상태 확인

## 📄 라이선스

이 프로젝트는 교육 및 개인 투자 목적으로 제작되었습니다. 상업적 사용 시 관련 법규를 준수하시기 바랍니다.

---

**⚠️ 투자에 따른 손실은 본인의 책임입니다. 신중하게 투자하시기 바랍니다.** 