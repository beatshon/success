# 키움 자동 주문 시스템 (Mac 버전)

이 프로젝트는 키움 API를 사용하여 자동으로 주식 주문을 실행하는 Python 스크립트입니다. Mac 환경에서 Windows 서버와 연동하여 작동합니다.

## 🍎 Mac 환경에서의 사용법

### 1. 필수 요구사항

- **Mac OS** (macOS 10.14 이상 권장)
- **Python 3.7 이상**
- **Windows 서버** (키움 Open API+ 실행용)
- **키움 증권 계좌**

### 2. 설치 및 설정

#### 2.1 Python 환경 설정
```bash
# Python 설치 확인
python3 --version

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 필요한 패키지 설치
pip install requests flask python-dotenv
```

#### 2.2 Windows 서버 설정
1. **Windows PC에서 키움 Open API+ 설치 및 실행**
2. **Windows 서버 스크립트 실행** (별도 제공)
3. **서버 URL 확인**: `http://localhost:8080`

#### 2.3 설정 파일 수정
`kiwoom_config_mac.py` 파일에서 계좌 정보를 수정하세요:
```python
ACCOUNT_NO = "YOUR_ACCOUNT_NUMBER"  # 실제 계좌번호
ACCOUNT_PW = "YOUR_ACCOUNT_PASSWORD"  # 실제 계좌비밀번호
```

### 3. 실행 방법

#### 3.1 기본 실행
```bash
# 가상환경 활성화
source venv/bin/activate

# 자동 주문 실행
python kiwoom_auto_order_mac.py
```

#### 3.2 테스트 실행
```bash
# 연결 테스트
python test_kiwoom_connection_mac.py

# 설치 상태 확인
python check_kiwoom_installation_mac.py
```

## 📁 파일 구조

```
kiwoom_trading/
├── kiwoom_auto_order_mac.py          # 메인 실행 파일 (Mac)
├── kiwoom_config_mac.py              # 설정 파일 (Mac)
├── test_kiwoom_connection_mac.py     # 연결 테스트 (Mac)
├── check_kiwoom_installation_mac.py  # 설치 확인 (Mac)
├── README_MAC.md                     # 이 파일
├── requirements.txt                  # Python 패키지 목록
└── logs/                            # 로그 디렉토리
```

## 🔧 주요 기능

### ✅ **Mac 환경 최적화**
- Windows 서버와 HTTP 통신
- Mac 네이티브 UI 지원
- 크로스 플랫폼 호환성

### ✅ **자동 주문 시스템**
- 키움 API를 통한 주식 주문
- 실시간 주문 상태 확인
- 에러 코드 자동 해석

### ✅ **로깅 시스템**
- 상세한 로그 기록
- 파일 및 콘솔 출력
- 에러 추적 및 디버깅

### ✅ **설정 관리**
- 계좌 정보, 주문 파라미터 등을 쉽게 수정
- 입력값 유효성 검사
- 안전장치 구현

## ⚙️ 설정 옵션

### 주문 설정
- `STOCK_CODE`: 종목코드 (6자리)
- `ORDER_QTY`: 주문 수량
- `ORDER_PRICE`: 주문 가격
- `ORDER_TYPE`: 주문 구분 ("00": 지정가, "03": 시장가)

### Mac 환경 설정
- `IS_MAC`: Mac 환경 여부 (True)
- `WINDOWS_SERVER_URL`: Windows 서버 URL

### 로깅 설정
- `LOG_LEVEL`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE`: 로그 파일 경로

## 🚀 빠른 시작

### 1단계: Windows 서버 준비
```bash
# Windows PC에서 키움 Open API+ 실행
# 서버 스크립트 실행
```

### 2단계: Mac에서 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd kiwoom_trading

# 가상환경 설정
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3단계: 설정 수정
```python
# kiwoom_config_mac.py 수정
ACCOUNT_NO = "실제계좌번호"
ACCOUNT_PW = "실제비밀번호"
```

### 4단계: 실행
```bash
python kiwoom_auto_order_mac.py
```

## ⚠️ 주의사항

### 🔒 **보안**
- 계좌 정보는 절대 공개하지 마세요
- 정기적으로 비밀번호를 변경하세요
- 안전한 환경에서만 사용하세요

### ⏰ **거래 시간**
- 주식 거래는 거래 시간에만 가능합니다
- 장 시작 전후 시간을 고려하세요

### 💻 **시스템 요구사항**
- Windows 서버가 실행 중이어야 합니다
- 인터넷 연결이 안정적이어야 합니다
- 방화벽 설정을 확인하세요

## 🐛 문제 해결

### 연결 실패 시:
1. Windows 서버가 실행 중인지 확인
2. 서버 URL이 올바른지 확인
3. 방화벽 설정 확인

### 주문 실패 시:
1. 계좌 정보가 올바른지 확인
2. 주문 수량과 가격이 적절한지 확인
3. 거래 시간인지 확인

## 📊 에러 코드

시스템에서 자동으로 에러 코드를 해석해드립니다:
- `0`: 성공
- `-100`: 사용자정보교환실패
- `-101`: 서버접속실패
- `-300`: 입력값오류
- `-301`: 계좌비밀번호없음

## 🔄 업데이트

시스템 업데이트 시 다음 사항을 확인하세요:

1. Windows 서버 버전 호환성
2. Python 패키지 버전
3. 설정 파일 변경사항

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. 로그 파일 확인
2. Windows 서버 상태 확인
3. 네트워크 연결 상태 확인

## 📄 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다. 실제 거래에 사용하기 전에 충분한 테스트를 진행하세요.

---

**⚠️ 투자 위험 고지**: 주식 투자는 원금 손실의 위험이 있습니다. 이 시스템을 사용한 거래 결과에 대해 개발자는 책임지지 않습니다. 