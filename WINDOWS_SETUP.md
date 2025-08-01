# Windows 서버 키움 자동매매 시스템 설정 가이드

## 🖥️ Windows 서버 환경 설정

### 1. 필수 요구사항

- **Windows 10/11** (64비트 권장)
- **Python 3.7 이상** 설치
- **키움증권 영웅문** 설치 및 로그인
- **키움 Open API+** 사용 신청 및 승인

### 2. 키움증권 설정

#### 2.1 영웅문 설치
1. [키움증권 홈페이지](https://www.kiwoom.com) 접속
2. "영웅문" 다운로드 및 설치
3. 계정으로 로그인

#### 2.2 Open API+ 신청
1. 영웅문에서 "Open API+" 메뉴 선택
2. 사용 신청서 작성 및 제출
3. 승인 대기 (보통 1-2일 소요)

#### 2.3 API 설정
1. 영웅문에서 "Open API+" → "설정"
2. "실시간 조회" 활성화
3. "자동주문" 설정 (필요시)

### 3. Python 환경 설정

#### 3.1 Python 설치 확인
```cmd
python --version
```

#### 3.2 가상환경 생성 (권장)
```cmd
python -m venv venv
venv\Scripts\activate
```

#### 3.3 필요한 패키지 설치
```cmd
pip install -r requirements.txt
```

### 4. 시스템 실행

#### 4.1 테스트 실행
```cmd
# 방법 1: 배치 파일 사용
windows_test.bat

# 방법 2: 직접 실행
python windows_test.py
```

#### 4.2 자동매매 시작
```cmd
# 방법 1: 배치 파일 사용
start_trading.bat

# 방법 2: 직접 실행
python gui_trader.py
```

### 5. 문제 해결

#### 5.1 키움 API 연결 실패
- **원인**: 영웅문이 실행되지 않음
- **해결**: 영웅문을 먼저 실행하고 로그인

#### 5.2 PyQt5 오류
- **원인**: PyQt5 설치 실패
- **해결**: 
  ```cmd
  pip uninstall PyQt5
  pip install PyQt5==5.15.9
  ```

#### 5.3 권한 오류
- **원인**: 관리자 권한 필요
- **해결**: 명령 프롬프트를 관리자 권한으로 실행

### 6. 로그 확인

#### 6.1 로그 파일 위치
- `logs/kiwoom_trading.log`: 메인 로그
- `logs/server_YYYYMMDD.log`: 서버 로그

#### 6.2 로그 레벨 설정
`config.py`에서 로그 레벨 조정:
```python
LOGGING_CONFIG = {
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_file': 'logs/kiwoom_trading.log',
}
```

### 7. 자동 실행 설정

#### 7.1 Windows 작업 스케줄러 설정
1. "작업 스케줄러" 실행
2. "기본 작업 만들기" 선택
3. 트리거 설정 (예: 시스템 시작 시)
4. 동작 설정: `start_trading.bat` 실행

#### 7.2 시작 프로그램 등록
1. `Win + R` → `shell:startup` 입력
2. `start_trading.bat` 바로가기 복사

### 8. 모니터링

#### 8.1 실시간 모니터링
- GUI에서 실시간 차트 및 거래 내역 확인
- 로그 파일 실시간 확인

#### 8.2 성과 분석
- 거래 내역 CSV 파일 생성
- 수익률 계산 및 분석

### 9. 보안 주의사항

#### 9.1 계정 보안
- 강력한 비밀번호 사용
- 2단계 인증 활성화
- 정기적인 비밀번호 변경

#### 9.2 시스템 보안
- 방화벽 설정
- 안티바이러스 업데이트
- 정기적인 시스템 업데이트

### 10. 지원 및 문의

#### 10.1 문제 발생 시
1. 로그 파일 확인
2. 키움증권 고객센터 문의
3. GitHub Issues 등록

#### 10.2 연락처
- 키움증권 고객센터: 1544-9000
- 기술 지원: GitHub Issues

---

**⚠️ 주의사항**
- 자동매매는 투자 손실의 위험이 있습니다
- 충분한 테스트 후 실제 거래를 시작하세요
- 투자 손실에 대한 책임은 사용자에게 있습니다 