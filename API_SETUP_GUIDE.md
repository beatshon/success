# 키움 API 연동 성공 가이드

## 현재 상황 분석

### ✅ 완료된 항목
- API 키 설정 완료
- 32비트 Python 설치 완료
- PyQt5 설치 완료
- 모의 거래 시스템 작동 확인

### ❌ 문제점
- 키움 Open API+ ActiveX 컨트롤 설치 안됨
- REST API 연결 실패 (404 오류)

## 해결 방법

### 1단계: 키움 Open API+ 정식 설치

#### 1.1 키움증권 홈페이지에서 다운로드
1. https://www.kiwoom.com/h/customer/download/VOpenApiInfoView
2. "Open API+" 다운로드
3. **관리자 권한으로 실행**하여 설치

#### 1.2 설치 확인
```powershell
# 키움 폴더 확인
dir "C:\Program Files (x86)\Kiwoom\OpenAPI"

# ActiveX 컨트롤 등록
regsvr32 "C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.OCX"
```

### 2단계: 키움 Open API+ 신청 및 승인

#### 2.1 API 신청
1. 키움증권 홈페이지 로그인
2. "Open API+" 메뉴 접속
3. "API 신청" 클릭
4. 필요한 정보 입력 및 제출

#### 2.2 승인 대기
- 일반적으로 1-2일 소요
- 승인 완료 시 이메일 또는 SMS 발송

### 3단계: 영웅문 설정

#### 3.1 영웅문 실행
1. 키움 영웅문 실행
2. 계정 로그인
3. **모의투자** 계정으로 로그인 권장

#### 3.2 API 설정
1. 영웅문 메뉴 → "설정" → "API 설정"
2. "Open API 사용" 체크
3. "실시간 조회" 체크
4. 설정 저장

### 4단계: Python 환경 설정

#### 4.1 32비트 Python 확인
```powershell
python -c "import platform; print(platform.architecture())"
# 결과: ('32bit', 'WindowsPE') 여야 함
```

#### 4.2 필요한 패키지 설치
```powershell
pip install PyQt5 requests pandas loguru
```

### 5단계: API 테스트

#### 5.1 ActiveX 방식 테스트
```powershell
python simple_api_test.py
```

#### 5.2 REST API 방식 테스트
```powershell
python test_rest_api.py
```

#### 5.3 모의 거래 시스템 테스트
```powershell
python demo_trading_system.py
```

## 대안 방법

### 방법 1: 모의 거래 시스템 사용
- 키움 API 없이도 거래 로직 테스트 가능
- 실제 거래는 하지 않지만 전략 검증 가능

### 방법 2: 다른 증권사 API 고려
- 대신증권 API
- 한국투자증권 API
- NH투자증권 API

### 방법 3: 웹 스크래핑 방식
- 키움 웹사이트에서 데이터 수집
- 제한적이지만 기본적인 시세 정보 획득 가능

## 문제 해결 체크리스트

### ActiveX 오류 해결
- [ ] 32비트 Python 사용
- [ ] 관리자 권한으로 실행
- [ ] 키움 Open API+ 정식 설치
- [ ] ActiveX 컨트롤 등록
- [ ] 영웅문 실행 및 로그인

### REST API 오류 해결
- [ ] API 키 정확성 확인
- [ ] API 신청 및 승인 완료
- [ ] 네트워크 연결 확인
- [ ] 방화벽 설정 확인

### 일반적인 문제
- [ ] 영웅문이 실행 중인지 확인
- [ ] 계정 로그인 상태 확인
- [ ] 모의투자 계정 사용 권장
- [ ] 방화벽에서 키움 프로그램 허용

## 성공 확인 방법

### 1. ActiveX 연결 성공 시
```
✅ 키움 API 객체 생성 성공
📊 연결 상태: 1
📊 로그인 결과: 0
📊 계좌 개수: 1
```

### 2. REST API 연결 성공 시
```
✅ 액세스 토큰 발급 성공!
✅ 주식 정보 조회 성공!
✅ 계좌 정보 조회 성공!
```

### 3. 모의 거래 시스템 성공 시
```
✅ 모의 거래 시스템 테스트 완료!
💰 현금 잔고: 10,000,000원
📊 보유 종목 수: 1개
```

## 다음 단계

1. **키움 Open API+ 정식 설치** (가장 중요)
2. **API 신청 및 승인** 대기
3. **영웅문 설정** 완료
4. **실제 API 테스트** 진행
5. **거래 전략 구현** 및 테스트

## 문의 및 지원

- 키움증권 고객센터: 1544-9000
- 키움증권 API 문의: https://www.kiwoom.com/h/customer/download/VOpenApiInfoView
- 기술 문서: 키움증권 Open API+ 개발가이드

---

**참고**: 키움 API는 ActiveX 기반으로 32비트 환경에서만 작동합니다. 64비트 Python을 사용하면 반드시 오류가 발생합니다. 