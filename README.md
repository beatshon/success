# 키움증권 API 자동매매 시스템

키움증권 Open API+를 활용한 자동매매 프로그램입니다. 다양한 기술적 분석 전략을 기반으로 자동으로 주식 매매를 수행합니다.

## 🚀 주요 기능

- **다양한 매매 전략 지원**
  - 이동평균 크로스오버 전략
  - RSI (상대강도지수) 전략
  - 볼린저 밴드 전략

- **실시간 모니터링**
  - 종목별 실시간 가격 정보
  - 거래 내역 실시간 업데이트
  - 시스템 로그 모니터링

- **사용자 친화적 GUI**
  - 직관적인 설정 인터페이스
  - 실시간 차트 및 테이블
  - 원클릭 자동매매 시작/중지

## 📋 시스템 요구사항

### 필수 요구사항
- **Windows 운영체제** (키움 API는 Windows에서만 작동)
- Python 3.7 이상
- 키움증권 계좌 및 Open API+ 사용 신청
- 키움 Open API+ 모듈 설치

### 권장 사양
- Windows 10/11
- Python 3.8+
- 8GB RAM 이상
- 안정적인 인터넷 연결

## 🛠️ 설치 방법

### 1. 키움증권 Open API+ 설치
1. [키움증권 Open API+](https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView) 다운로드
2. 설치 후 키움증권 계정으로 로그인
3. Open API+ 사용 신청 및 승인 대기

### 2. Python 환경 설정
```bash
# 프로젝트 클론 또는 다운로드
cd kiwoom_trading

# 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate  # Windows

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 설정
```bash
# logs 디렉토리 생성
mkdir logs
```

## 🎯 사용 방법

### 1. GUI 모드 실행
```bash
python gui_trader.py
```

### 2. 콘솔 모드 실행
```bash
python auto_trader.py
```

### 3. GUI 사용법

#### 로그인
1. "로그인" 버튼 클릭
2. 키움증권 계정 정보 입력
3. 로그인 성공 확인

#### 전략 설정
1. **전략 선택**: 이동평균, RSI, 볼린저밴드 중 선택
2. **파라미터 설정**: 각 전략에 맞는 파라미터 입력
   - 이동평균: 단기/장기 기간 설정
   - RSI: 기간, 과매도/과매수 기준 설정
   - 볼린저밴드: 기간, 표준편차 설정

#### 거래 설정
- **거래 금액**: 1회 매수/매도 시 사용할 금액
- **최대 보유 종목**: 동시에 보유할 수 있는 최대 종목 수
- **실행 주기**: 매매 조건 확인 주기 (초 단위)

#### 종목 관리
1. **종목 추가**: 종목코드 입력 후 "추가" 버튼 클릭
2. **종목 제거**: 리스트에서 선택 후 "제거" 버튼 클릭

#### 자동매매 시작/중지
- **시작**: "자동매매 시작" 버튼 클릭
- **중지**: "자동매매 중지" 버튼 클릭

## 📊 매매 전략 설명

### 1. 이동평균 크로스오버 전략
- **매수 조건**: 단기 이동평균이 장기 이동평균을 상향 돌파 (골든크로스)
- **매도 조건**: 단기 이동평균이 장기 이동평균을 하향 돌파 (데드크로스)
- **적용**: 추세 추종형 전략

### 2. RSI 전략
- **매수 조건**: RSI가 과매도 구간(30 이하)에서 반등
- **매도 조건**: RSI가 과매수 구간(70 이상)에서 하락
- **적용**: 반등 매매 전략

### 3. 볼린저 밴드 전략
- **매수 조건**: 가격이 하단 밴드에 닿았을 때
- **매도 조건**: 가격이 상단 밴드에 닿았을 때
- **적용**: 변동성 기반 전략

## ⚠️ 주의사항

### 투자 위험 고지
- **자동매매는 투자 손실의 위험이 있습니다**
- **실제 거래 전 충분한 백테스팅을 권장합니다**
- **소액으로 시작하여 점진적으로 금액을 늘려가세요**

### 기술적 주의사항
- 키움 API는 Windows 환경에서만 작동합니다
- 장 시간 외에는 실시간 데이터가 제한될 수 있습니다
- API 호출 제한이 있으므로 과도한 요청을 피하세요
- 네트워크 연결이 불안정할 경우 거래가 지연될 수 있습니다

### 법적 고지사항
- 자동매매 프로그램 사용 시 관련 법규를 준수하세요
- 키움증권의 이용약관을 확인하고 준수하세요
- 투자 손실에 대한 책임은 사용자에게 있습니다

## 🚨 문제 해결

### OCX 파일 등록 오류 해결

키움 OpenAPI 사용 시 다음과 같은 오류가 발생할 수 있습니다:
```
모듈 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"을(를) 로드하지 못했습니다.
지정된 모듈을 찾을 수 없습니다.
```

#### 자동 해결 방법
```cmd
# 관리자 권한으로 실행
fix_ocx_registration.bat
```

#### 수동 해결 방법
1. **키움 OpenAPI 재설치**
   - https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
   - 관리자 권한으로 설치

2. **OCX 파일 수동 등록**
   ```cmd
   # 관리자 권한으로 명령 프롬프트 실행
   regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
   ```

3. **Visual C++ 재배포 패키지 설치**
   - https://aka.ms/vs/17/release/vc_redist.x86.exe

4. **Python 테스트**
   ```cmd
   python test_ocx_registration.py
   ```

#### 상세 가이드
- [OCX 오류 해결 가이드](KIWOOM_OCX_ERROR_FIX.md)
- [키움 API 설정 가이드](KIWOOM_API_SETUP_GUIDE.md)

### 기타 일반적인 문제들

#### 1. Python 패키지 설치 오류
```bash
# PyQt5 설치 오류 시
pip install --upgrade pip
pip install PyQt5==5.15.9

# 기타 의존성 패키지
pip install -r requirements.txt
```

#### 2. 키움 API 연결 실패
- 키움증권 계정으로 로그인 확인
- Open API+ 사용 신청 승인 상태 확인
- 방화벽에서 키움 API 접근 허용

#### 3. 실시간 데이터 수신 오류
- 네트워크 연결 상태 확인
- 키움 API 서버 상태 확인
- 장 시간 내에 실행하는지 확인

#### 4. 주문 실행 실패
- 계좌 잔고 확인
- 주문 가능 시간 확인 (장 시간)
- 종목코드 정확성 확인

## 🔧 고급 설정

### 로그 설정
```python
# loguru 설정 커스터마이징
logger.add("logs/custom_{time}.log", 
           rotation="1 day", 
           retention="30 days",
           level="INFO")
```

### 전략 커스터마이징
```python
# 새로운 전략 클래스 생성
class CustomStrategy(TradingStrategy):
    def should_buy(self, code, current_price, **kwargs):
        # 커스텀 매수 로직 구현
        pass
    
    def should_sell(self, code, current_price, **kwargs):
        # 커스텀 매도 로직 구현
        pass
```

### 백테스팅
```python
# 과거 데이터로 전략 성능 테스트
def backtest_strategy(strategy, historical_data):
    # 백테스팅 로직 구현
    pass
```

## 📞 지원 및 문의

### 문제 해결
1. **로그인 실패**: 키움증권 계정 정보 확인
2. **API 연결 오류**: 키움 Open API+ 재설치
3. **거래 실행 실패**: 계좌 잔고 및 주문 가능 시간 확인

### 추가 기능 요청
- GitHub Issues를 통해 기능 요청 및 버그 리포트
- 코드 기여 환영

## 📄 라이선스

이 프로젝트는 교육 및 개인 투자 목적으로 제작되었습니다. 상업적 사용 시 관련 법규를 준수하시기 바랍니다.

## 🔄 업데이트 내역

### v1.0.0 (2024-01-01)
- 초기 버전 릴리즈
- 기본 매매 전략 3가지 구현
- GUI 인터페이스 제공
- 실시간 모니터링 기능

---

**⚠️ 투자에 따른 손실은 본인의 책임입니다. 신중하게 투자하시기 바랍니다.** # Test sync Sat Aug  2 01:24:07 KST 2025
