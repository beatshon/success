# 고급 트레이딩 시스템 배포 가이드

## 개요

이 가이드는 64비트 환경에서 딥러닝 기반 고급 트레이딩 시스템을 구축하고, 32비트 키움 API와 연동하는 방법을 설명합니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    64비트 메인 시스템                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   딥러닝 모델   │  │  고급 분석      │  │  웹 대시보드 │ │
│  │   (TensorFlow)  │  │  (감정분석)     │  │  (Flask)     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  32비트 키움 API 브리지                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   키움 API      │  │  브리지 서버    │  │  주문 실행   │ │
│  │   (ActiveX)     │  │  (Flask)        │  │  (실시간)    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 키움 Open API+
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    키움 모의증권/실거래                      │
└─────────────────────────────────────────────────────────────┘
```

## 시스템 요구사항

### 64비트 메인 시스템
- **OS**: Windows 10/11 64비트
- **Python**: 3.9+ 64비트
- **RAM**: 16GB+ (딥러닝 모델용)
- **GPU**: NVIDIA GPU (선택사항, TensorFlow GPU 지원)

### 32비트 키움 브리지
- **OS**: Windows 10/11 32비트 또는 64비트
- **Python**: 3.9+ 32비트
- **키움 Open API+**: 최신 버전
- **영웅문**: 키움 증권 프로그램

## 설치 단계

### 1. 64비트 메인 시스템 설치

```bash
# 1. Python 3.9+ 64비트 설치
# https://www.python.org/downloads/

# 2. 가상환경 생성
python -m venv venv_64bit
venv_64bit\Scripts\activate

# 3. 패키지 설치
pip install -r requirements_advanced.txt

# 4. 시스템 시작
python integrated_advanced_system.py
```

### 2. 32비트 키움 브리지 설치

```bash
# 1. Python 3.9+ 32비트 설치
# 별도 32비트 Python 설치 필요

# 2. 가상환경 생성
python -m venv venv_32bit
venv_32bit\Scripts\activate

# 3. 기본 패키지 설치
pip install flask requests

# 4. 키움 API 브리지 시작
python kiwoom_32bit_bridge.py
```

### 3. 키움 API 설정

1. **키움 증권 계정 생성**
   - 키움 증권 웹사이트에서 계정 생성
   - 모의증권 신청 (실거래 전 테스트용)

2. **영웅문 설치**
   - 키움 증권에서 영웅문 다운로드 및 설치
   - 로그인 및 기본 설정

3. **Open API+ 신청**
   - 영웅문에서 Open API+ 신청
   - 승인 후 API 키 발급

4. **API 키 설정**
   ```python
   # config/kiwoom_config.json
   {
     "api_key": "your_api_key_here",
     "user_id": "your_user_id",
     "password": "your_password",
     "cert_password": "your_cert_password"
   }
   ```

## 실행 방법

### 1. 키움 브리지 서버 시작 (32비트)

```bash
# 32비트 Python 환경에서
cd kiwoom_trading
python kiwoom_32bit_bridge.py
```

**예상 출력:**
```
2025-08-02 21:30:00 - __main__ - INFO - 키움 API 브리지 초기화 완료
2025-08-02 21:30:01 - __main__ - INFO - 키움 API 브리지 서버 시작: 0.0.0.0:8001
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8001
```

### 2. 메인 시스템 시작 (64비트)

```bash
# 64비트 Python 환경에서
cd kiwoom_trading
python integrated_advanced_system.py
```

**예상 출력:**
```
2025-08-02 21:30:05 - __main__ - INFO - 통합 고급 트레이딩 시스템 초기화 완료
2025-08-02 21:30:06 - __main__ - INFO - 통합 고급 트레이딩 시스템 시작
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
```

### 3. 시스템 테스트

```bash
# 64비트 환경에서
python kiwoom_client_64bit.py
```

## API 엔드포인트

### 메인 시스템 (포트 8000)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 시스템 상태 확인 |
| `/ready` | GET | 준비 상태 확인 |
| `/api/v1/status` | GET | 시스템 상태 조회 |
| `/api/v1/models/train` | POST | 모델 학습 |
| `/api/v1/analysis` | POST | 고급 분석 실행 |
| `/api/v1/portfolio` | GET | 포트폴리오 정보 |
| `/api/v1/trading/signals` | GET | 트레이딩 신호 |

### 키움 브리지 (포트 8001)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 브리지 상태 확인 |
| `/api/v1/connect` | POST | 키움 API 연결 |
| `/api/v1/account` | GET | 계좌 정보 조회 |
| `/api/v1/positions` | GET | 보유 종목 조회 |
| `/api/v1/order` | POST | 주문 실행 |
| `/api/v1/market_data` | GET | 시장 데이터 조회 |

## 모니터링 및 로깅

### 로그 파일 위치
- 메인 시스템: `logs/integrated_system.log`
- 키움 브리지: `logs/kiwoom_bridge.log`
- 테스트: `logs/test_system.log`

### 모니터링 대시보드
- URL: `http://localhost:8000`
- 실시간 시스템 상태 확인
- 포트폴리오 성과 분석
- 트레이딩 신호 모니터링

## 문제 해결

### 1. 키움 API 연결 실패
```bash
# 32비트 환경 확인
python -c "import sys; print('32비트' if sys.maxsize <= 2**32 else '64비트')"

# 키움 프로그램 실행 상태 확인
tasklist | findstr "OpenAPI"

# API 키 설정 확인
cat config/kiwoom_config.json
```

### 2. 브리지 서버 연결 실패
```bash
# 포트 확인
netstat -an | findstr :8001

# 방화벽 설정 확인
# Windows Defender에서 Python.exe 허용
```

### 3. 딥러닝 모델 학습 실패
```bash
# GPU 확인
nvidia-smi

# TensorFlow 버전 확인
python -c "import tensorflow as tf; print(tf.__version__)"

# 메모리 사용량 확인
tasklist | findstr "python"
```

## 성능 최적화

### 1. 메모리 최적화
- 배치 크기 조정: `config/system_config.json`에서 `batch_size` 수정
- 모델 복잡도 조정: LSTM 레이어 수 조정
- 데이터 캐싱: Redis 사용

### 2. GPU 가속
```bash
# TensorFlow GPU 설치
pip install tensorflow-gpu

# CUDA 및 cuDNN 설치
# NVIDIA 드라이버 업데이트
```

### 3. 네트워크 최적화
- 브리지 서버와 메인 시스템 간 HTTP/2 사용
- 연결 풀링 설정
- 타임아웃 조정

## 보안 고려사항

### 1. API 키 보안
- 환경 변수 사용: `set KIWOOM_API_KEY=your_key`
- 암호화 저장: `cryptography` 라이브러리 사용
- 정기적 키 로테이션

### 2. 네트워크 보안
- HTTPS 사용 (프로덕션 환경)
- API 인증 추가
- IP 화이트리스트 설정

### 3. 로그 보안
- 민감 정보 마스킹
- 로그 파일 암호화
- 정기적 로그 정리

## 확장 계획

### 1. 클라우드 배포
- Docker 컨테이너화
- Kubernetes 오케스트레이션
- AWS/GCP 클라우드 배포

### 2. 고도화
- 실시간 데이터 스트리밍
- 고빈도 트레이딩 (HFT)
- 멀티 시장 지원

### 3. 모니터링
- Prometheus 메트릭 수집
- Grafana 대시보드
- 알림 시스템 (Slack/Email)

## 지원 및 문의

- **기술 문서**: `docs/` 폴더
- **예제 코드**: `examples/` 폴더
- **테스트 스크립트**: `tests/` 폴더
- **로그 분석**: `logs/` 폴더

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 