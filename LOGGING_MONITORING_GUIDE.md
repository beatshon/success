# 📊 로그 & 모니터링 시스템 가이드

## 🎯 개요

크로스 플랫폼 트레이딩 시스템의 로그 & 모니터링 기능을 통해 매매 활동을 추적하고 시스템 상태를 모니터링할 수 있습니다.

## 📁 로그 파일 구조

```
logs/
└── 2025-08-03/                    # 날짜별 폴더
    ├── buy_log.csv               # 매수 로그
    ├── sell_log.csv              # 매도 로그
    └── error_log.csv             # 오류 로그
```

## 📋 로그 파일 상세

### 1. 매수 로그 (buy_log.csv)
| 필드 | 설명 | 예시 |
|------|------|------|
| 시간 | 매수 실행 시간 | 2025-08-03 18:56:18 |
| 종목코드 | 매수한 종목 코드 | 005930.KS |
| 수량 | 매수 수량 | 8 |
| 가격 | 매수 가격 | 126018 |
| 총액 | 매수 총액 | 1008144 |
| 예수금 | 매수 후 예수금 | 8991856 |
| 보유종목수 | 매수 후 보유 종목 수 | 1 |

### 2. 매도 로그 (sell_log.csv)
| 필드 | 설명 | 예시 |
|------|------|------|
| 시간 | 매도 실행 시간 | 2025-08-03 18:57:46 |
| 종목코드 | 매도한 종목 코드 | 005930.KS |
| 수량 | 매도 수량 | 3 |
| 가격 | 매도 가격 | 84023 |
| 총액 | 매도 총액 | 252069 |
| 수익률 | 매도 수익률 | +0.00% |
| 매도사유 | 매도 사유 | 익절/손절/기술적매도/비상정지 |
| 예수금 | 매도 후 예수금 | 10252069 |
| 보유종목수 | 매도 후 보유 종목 수 | 0 |

### 3. 오류 로그 (error_log.csv)
| 필드 | 설명 | 예시 |
|------|------|------|
| 시간 | 오류 발생 시간 | 2025-08-03 18:57:46 |
| 오류유형 | 오류 종류 | 매수주문실패/API연결오류/비상정지 |
| 오류메시지 | 상세 오류 내용 | 주문 실패: 잔고 부족 |
| 상태 | 오류 상태 | 발생/실패/해결 |

## 🧹 로그 정리 시스템

### 1. 수동 로그 정리
```bash
# DRY RUN 모드 (삭제할 항목만 확인)
python log_cleanup.py --dry-run

# 30일 보관으로 정리
python log_cleanup.py 30

# 60일 보관으로 정리
python log_cleanup.py 60
```

### 2. 자동 로그 정리 스케줄러
```bash
# 스케줄러 시작 (매일 오전 2시 정리, 오후 6시 일일 요약)
python auto_log_cleanup.py

# 즉시 실행
python auto_log_cleanup.py --run-once

# 60일 보관으로 스케줄러 시작
python auto_log_cleanup.py 60

# 오전 3시에 정리하도록 설정
python auto_log_cleanup.py 30 3
```

**스케줄러 기능:**
- **매일 오전 2시**: 로그 파일 정리 (30일 이상 된 파일 삭제)
- **매일 오후 6시**: 일일 매매 요약 리포트 전송
- **매주 일요일 오전 3시**: 주간 통계 리포트 생성

### 3. 로그 정리 기능
- **자동 백업**: 중요한 오류 로그는 `logs_backup/` 폴더에 자동 백업
- **크기 계산**: 삭제 전후 디스크 사용량 표시
- **안전한 삭제**: 날짜 형식 검증 후 삭제
- **주간 리포트**: 매주 일요일 오전 3시에 통계 리포트 생성

## 📱 텔레그램 알림 설정

### 1. 봇 생성
1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어로 새 봇 생성
3. 봇 이름과 사용자명 설정
4. 봇 토큰 복사

### 2. 채팅 ID 확인
1. 생성한 봇과 대화 시작
2. `@userinfobot` 검색하여 대화
3. 개인 채팅 ID 확인

### 3. 설정 적용
```python
# cross_platform_trader.py 파일에서 설정
TELEGRAM_TOKEN = "YOUR_ACTUAL_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_ACTUAL_CHAT_ID"
TELEGRAM_ENABLED = True
```

### 4. 알림 종류
- 🟢 **매수 알림**: `🟢 [매수] 005930.KS 10주 @ 126,018원 | 예수금 8,739,820원`
- 🔴 **익절 알림**: `🔴 [익절] 005930.KS 10주 @ 135,000원 (+7.13%)`
- 🔴 **손절 알림**: `🔴 [손절] 005930.KS 10주 @ 115,000원 (-8.73%)`
- ⚠️ **오류 알림**: `⚠️ [비상정지] 이유: API 연결 오류`
- 🚨 **비상정지 리포트**: `🚨 비상정지 리포트\n총자산: 10,000,000원\n예수금: 9,507,754원\n보유종목: 1개\n\n보유종목 상세:\n• 005930.KS: 6주 @ 82,041원 (+0.00%)`
- 📊 **일일 요약**: `📊 2025-08-03 매매 요약\n🟢 매수: 2건, 총 1,351,360원\n🔴 매도: 없음\n⚠️ 오류: 없음\n💰 현재 예수금: 8,121,175원\n📈 보유종목: 2개`
- 🚀 **시스템 시작**: `🚀 [시스템시작] 크로스 플랫폼 트레이딩 시스템`

## 🚨 비상정지 시스템

### 1. 비상정지 조건
- 트레이딩 루프 오류 발생
- API 연결 실패
- 메모리 부족
- 수동 비상정지 실행
- **하루 손실 상한선 초과**

### 2. 비상정지 동작
1. **즉시 매매 중단**: 모든 매수/매도 주문 중단
2. **비상정지 리포트**: 현재 자산 현황 상세 리포트 전송
3. **포지션 청산**: 보유 중인 모든 종목 자동 매도
4. **오류 로깅**: 비상정지 사유를 오류 로그에 기록
5. **텔레그램 알림**: 비상정지 알림 전송
6. **시스템 종료**: 안전하게 시스템 종료

### 3. 비상정지 테스트
```bash
python test_emergency_stop.py
```

## 📉 하루 손실 상한선 시스템

### 1. 기능 설명
- **일일 손실 한도 설정**: 기본 -3% (설정 가능)
- **실시간 모니터링**: 매 트레이딩 루프마다 손실률 체크
- **자동 리셋**: 자정 기준으로 손실 상한선 초기화
- **즉시 비상정지**: 한도 초과 시 모든 포지션 청산

### 2. 설정 방법
```python
# 기본 설정 (-3%)
trader = RealtimeTrader(api, account)

# 사용자 정의 설정 (-1%)
trader = RealtimeTrader(api, account, daily_loss_limit=-1.0)

# 보수적 설정 (-5%)
trader = RealtimeTrader(api, account, daily_loss_limit=-5.0)
```

### 3. 동작 원리
1. **기준 잔고 설정**: 트레이딩 시작 시점의 총 자산
2. **실시간 계산**: 현재 총 자산과 기준 잔고 비교
3. **손실률 계산**: `(현재총자산 - 기준잔고) / 기준잔고 * 100`
4. **한도 체크**: 설정된 손실 한도와 비교
5. **자동 리셋**: 자정 넘어가면 새로운 기준 잔고 설정

### 4. 테스트 방법
```bash
# 기본 테스트
python cross_platform_trader.py --daily-loss-test

# 상세 테스트
python test_daily_loss_limit.py
```

## 🔧 로그 분석 도구

### 1. CSV 파일 분석
```python
import pandas as pd

# 매수 로그 분석
buy_df = pd.read_csv('logs/2025-08-03/buy_log.csv')
print(f"총 매수 횟수: {len(buy_df)}")
print(f"총 매수 금액: {buy_df['총액'].sum():,}원")

# 매도 로그 분석
sell_df = pd.read_csv('logs/2025-08-03/sell_log.csv')
print(f"총 매도 횟수: {len(sell_df)}")
print(f"평균 수익률: {sell_df['수익률'].mean():.2f}%")
```

### 2. 오류 분석
```python
# 오류 로그 분석
error_df = pd.read_csv('logs/2025-08-03/error_log.csv')
error_counts = error_df['오류유형'].value_counts()
print("오류 발생 빈도:")
for error_type, count in error_counts.items():
    print(f"  {error_type}: {count}회")
```

## 📊 모니터링 대시보드

### 1. 실시간 통계
- 총 자산 현황
- 보유 종목 수
- 예수금 잔고
- 당일 매매 횟수

### 2. 성과 지표
- 총 수익률
- 승률 (익절/손절 비율)
- 평균 보유 기간
- 최대 손실폭

## 🛠️ 유지보수

### 1. 로그 파일 관리
- **자동 정리**: 30일 이상 된 로그 파일 자동 삭제
- **백업**: 중요 로그 파일 클라우드 백업
- **압축**: 오래된 로그 파일 압축 저장

### 2. 성능 최적화
- **로그 레벨 조정**: 운영 시 INFO 레벨 사용
- **파일 크기 제한**: 로그 파일당 최대 100MB
- **비동기 로깅**: 성능 향상을 위한 비동기 처리

## 🔍 문제 해결

### 1. 텔레그램 알림이 오지 않는 경우
- 봇 토큰과 채팅 ID 확인
- 봇과 대화 시작 여부 확인
- 네트워크 연결 상태 확인

### 2. 로그 파일이 생성되지 않는 경우
- logs 디렉토리 권한 확인
- 디스크 공간 확인
- 파일 쓰기 권한 확인

### 3. 비상정지가 작동하지 않는 경우
- 오류 처리 로직 확인
- 텔레그램 알림 설정 확인
- 시스템 리소스 상태 확인

### 4. 로그 정리가 작동하지 않는 경우
- schedule 라이브러리 설치 확인
- 파일 권한 확인
- 백업 디렉토리 생성 권한 확인

## 📈 향후 개선 계획

### 1. 고급 모니터링
- 실시간 차트 대시보드
- 포트폴리오 분석 리포트
- 리스크 관리 지표

### 2. 알림 기능 확장
- 이메일 알림 추가
- 슬랙/디스코드 연동
- 푸시 알림 지원

### 3. 로그 분석 고도화
- 머신러닝 기반 이상 탐지
- 자동 리포트 생성
- 성과 예측 모델

---

## 🎯 사용 예시

### 1. 일일 매매 현황 확인
```bash
# 로그 파일 확인
ls -la logs/$(date +%Y-%m-%d)/

# 매수/매도 통계 확인
python -c "
import pandas as pd
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
buy_df = pd.read_csv(f'logs/{today}/buy_log.csv')
sell_df = pd.read_csv(f'logs/{today}/sell_log.csv')

print(f'📊 {today} 매매 현황')
print(f'매수: {len(buy_df)}건, 총 {buy_df["총액"].sum():,}원')
print(f'매도: {len(sell_df)}건, 평균 수익률 {sell_df["수익률"].mean():.2f}%')
"
```

### 2. 텔레그램 알림 테스트
```bash
python test_telegram.py
```
테스트 항목:
- 시스템 시작 알림
- 매매 알림
- 오류 알림
- 비상정지 리포트
- 일일 요약 리포트

### 3. 비상정지 시스템 테스트
```bash
python test_emergency_stop.py
```

### 4. 일일 요약 리포트 테스트
```bash
python test_daily_summary.py
```

### 5. 독립 실행 일일 요약
```bash
# 오늘 날짜 요약
python daily_summary_standalone.py

# 특정 날짜 요약
python daily_summary_standalone.py 2025-08-03
```

### 6. 명령행 옵션
```bash
# 일일 요약만 실행
python cross_platform_trader.py --daily-summary

# 비상정지 테스트
python cross_platform_trader.py --emergency-stop

# 하루 손실 상한선 테스트
python cross_platform_trader.py --daily-loss-test

# 테스트 모드 (5회 반복)
python cross_platform_trader.py --test

# 도움말
python cross_platform_trader.py --help
```

### 7. Windows 자동 실행 설정

#### 7.1 배치 파일 실행
```batch
# daily_summary.bat 실행
daily_summary.bat

# 또는 직접 실행
python cross_platform_trader.py --daily-summary
```

#### 7.2 PowerShell 스크립트 실행
```powershell
# daily_summary.ps1 실행
.\daily_summary.ps1

# 로그와 함께 실행
.\daily_summary.ps1 -Log -LogFile "daily_summary.log"
```

#### 7.3 작업 스케줄러 설정
1. **Windows 키 + R** → `taskschd.msc` 입력
2. **기본 작업 만들기** → **일일 요약 리포트**
3. **트리거**: 매일 오후 11:50
4. **동작**: `daily_summary.bat` 실행

자세한 설정 방법은 `WINDOWS_SCHEDULER_SETUP.md` 참조

### 4. 로그 정리 테스트
```bash
# DRY RUN으로 삭제할 항목 확인
python log_cleanup.py --dry-run

# 즉시 로그 정리 실행
python auto_log_cleanup.py --run-once

# 자동 스케줄러 시작
python auto_log_cleanup.py
```

### 5. 주간 리포트 확인
```bash
# 주간 리포트 파일 확인
ls -la logs/weekly_report_*.txt

# 최신 리포트 내용 확인
cat logs/weekly_report_$(date +%Y%m%d).txt
```

---

## 📋 시스템 요구사항

### 1. 필수 라이브러리
```bash
pip install schedule pandas requests
```

### 2. 권한 설정
```bash
# logs 디렉토리 생성 권한
mkdir -p logs
chmod 755 logs

# 백업 디렉토리 생성 권한
mkdir -p logs_backup
chmod 755 logs_backup
```

### 3. 크론 작업 설정 (선택사항)
```bash
# 매일 오전 2시에 자동 로그 정리
0 2 * * * cd /path/to/kiwoom_trading && python auto_log_cleanup.py --run-once

# 매주 일요일 오전 3시에 주간 리포트 생성
0 3 * * 0 cd /path/to/kiwoom_trading && python auto_log_cleanup.py --weekly-report
```

---

**📞 지원**: 문제가 발생하면 로그 파일을 확인하고 오류 내용을 공유해주세요. 