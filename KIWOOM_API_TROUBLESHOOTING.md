# 키움 Open API 연동 문제 해결 가이드

## 🚨 현재 문제 상황

키움 Open API 연동에서 문제가 발생하고 있습니다. 체계적으로 진단하고 해결해보겠습니다.

## 🔍 문제 진단 체크리스트

### 1. 기본 환경 확인
- [ ] Windows 운영체제 사용 중
- [ ] 키움 Open API+ 설치 완료
- [ ] Python 3.7 이상 설치
- [ ] PyQt5 설치 완료

### 2. 키움증권 계정 확인
- [ ] 키움증권 계정 보유
- [ ] Open API+ 사용 신청 완료
- [ ] 사용 승인 완료
- [ ] 계정 정보 정확

### 3. API 앱키 확인
- [ ] API 앱키 발급 완료
- [ ] 앱키 승인 완료
- [ ] 앱키 정보 정확히 입력

### 4. 네트워크 연결 확인
- [ ] 인터넷 연결 정상
- [ ] 키움증권 서버 접근 가능
- [ ] 방화벽 설정 확인

## 🛠️ 단계별 문제 해결

### 단계 1: 기본 환경 진단

#### 1.1 Windows 환경 확인
```cmd
# Windows 버전 확인
ver

# Python 설치 확인
python --version

# PyQt5 설치 확인
python -c "from PyQt5.QAxContainer import *; print('PyQt5 설치 완료')"
```

#### 1.2 키움 Open API+ 설치 확인
```cmd
# 설치 경로 확인
dir "C:\OpenAPI"
dir "C:\Program Files (x86)\Kiwoom\OpenAPI"

# OCX 파일 등록 확인
regsvr32 "C:\OpenAPI\KHOPENAPI.OCX"
```

### 단계 2: 키움증권 계정 진단

#### 2.1 Open API+ 사용 신청 상태 확인
1. 키움증권 홈페이지 로그인
2. "Open API+ 사용신청 현황" 확인
3. 승인 상태 확인

#### 2.2 계정 정보 확인
```python
# 계정 정보 테스트
KIWOOM_USER_ID = "your_user_id"
KIWOOM_PASSWORD = "your_password"
KIWOOM_ACCOUNT = "your_account_number"
```

### 단계 3: API 앱키 진단

#### 3.1 앱키 발급 상태 확인
1. 키움증권 API 포털 접속
2. 앱키 발급 현황 확인
3. 승인 상태 확인

#### 3.2 앱키 설정 확인
```python
# 앱키 설정 테스트
KIWOOM_APP_KEY = "your_app_key"
KIWOOM_APP_SECRET = "your_app_secret"
KIWOOM_ACCESS_TOKEN = "your_access_token"
```

### 단계 4: 네트워크 연결 진단

#### 4.1 기본 연결 테스트
```cmd
# 키움증권 서버 연결 테스트
ping www.kiwoom.com

# DNS 확인
nslookup www.kiwoom.com
```

#### 4.2 방화벽 설정 확인
1. Windows 방화벽 설정 확인
2. 키움 Open API+ 프로그램 허용
3. Python 프로그램 허용

## 🧪 진단 스크립트

### 기본 진단 스크립트
```python
#!/usr/bin/env python3
"""
키움 Open API 연동 진단 스크립트
"""

import sys
import os
from datetime import datetime

def check_environment():
    """환경 진단"""
    print("🔍 환경 진단 시작...")
    
    # Python 버전 확인
    print(f"Python 버전: {sys.version}")
    
    # PyQt5 설치 확인
    try:
        from PyQt5.QAxContainer import *
        print("✅ PyQt5 설치 완료")
    except ImportError:
        print("❌ PyQt5 설치 필요")
        return False
    
    # 키움 API 컨트롤 확인
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        print("✅ 키움 API 컨트롤 생성 성공")
    except Exception as e:
        print(f"❌ 키움 API 컨트롤 생성 실패: {e}")
        return False
    
    return True

def check_configuration():
    """설정 진단"""
    print("\n🔧 설정 진단 시작...")
    
    # 환경 변수 확인
    required_vars = [
        'KIWOOM_USER_ID',
        'KIWOOM_PASSWORD', 
        'KIWOOM_ACCOUNT',
        'KIWOOM_APP_KEY',
        'KIWOOM_APP_SECRET'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...")
        else:
            print(f"❌ {var}: 설정되지 않음")
    
    return True

def main():
    """메인 진단"""
    print("🚀 키움 Open API 연동 진단 시작")
    print("=" * 50)
    
    # 환경 진단
    env_ok = check_environment()
    
    # 설정 진단
    config_ok = check_configuration()
    
    # 결과 출력
    print("\n📊 진단 결과:")
    print(f"환경 설정: {'✅ 정상' if env_ok else '❌ 문제'}")
    print(f"계정 설정: {'✅ 정상' if config_ok else '❌ 문제'}")
    
    if env_ok and config_ok:
        print("\n🎉 모든 진단이 통과되었습니다!")
    else:
        print("\n⚠️ 문제가 발견되었습니다. 위의 해결 방법을 참조하세요.")

if __name__ == "__main__":
    main()
```

## 🔧 일반적인 문제 해결

### 문제 1: "KHOPENAPI.KHOpenAPICtrl.1" 등록 실패
```cmd
# 해결 방법
regsvr32 "C:\OpenAPI\KHOPENAPI.OCX"
```

### 문제 2: 로그인 실패
```python
# 해결 방법
# 1. 계정 정보 확인
# 2. Open API+ 사용 승인 확인
# 3. 공인인증서 상태 확인
```

### 문제 3: API 호출 실패
```python
# 해결 방법
# 1. 로그인 상태 확인
# 2. 파라미터 형식 확인
# 3. API 호출 제한 확인
```

### 문제 4: 네트워크 연결 실패
```cmd
# 해결 방법
# 1. 인터넷 연결 확인
# 2. 방화벽 설정 확인
# 3. DNS 설정 확인
```

## 📞 추가 지원

문제가 지속되면:

1. **로그 확인**: `logs/` 디렉토리의 로그 파일 확인
2. **키움증권 고객센터**: 1544-9000
3. **키움증권 API 포털**: https://www.kiwoom.com/h/customer/download/VOpenApiInfoView

---

**이 가이드를 따라 단계별로 진단하면 문제를 해결할 수 있습니다!** 🚀 