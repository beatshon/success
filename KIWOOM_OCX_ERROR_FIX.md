# 키움 OpenAPI OCX 파일 등록 오류 해결 가이드

## 🚨 문제 상황
RegSvr32에서 다음과 같은 오류가 발생했습니다:
```
모듈 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"을(를) 로드하지 못했습니다.
지정된 모듈을 찾을 수 없습니다.
```

## 🔍 원인 분석
이 오류는 다음과 같은 이유로 발생합니다:
1. **키움 OpenAPI가 제대로 설치되지 않음**
2. **OCX 파일이 손상되었거나 누락됨**
3. **관리자 권한 부족**
4. **의존성 DLL 파일 누락**
5. **32비트/64비트 호환성 문제**

## 🔧 해결 방법

### 1단계: 키움 OpenAPI 재설치

#### 1.1 기존 설치 제거
```cmd
# 제어판 > 프로그램 및 기능에서 제거
# 또는 다음 명령어로 제거
wmic product where "name like 'Kiwoom%'" call uninstall /nointeractive
```

#### 1.2 새로 설치
1. **키움증권 공식 사이트 방문**
   - https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
   - 최신 버전 다운로드

2. **관리자 권한으로 설치**
   - 설치 파일을 우클릭
   - "관리자 권한으로 실행" 선택

3. **설치 경로 확인**
   - 기본 경로: `C:\Program Files (x86)\Kiwoom OpenAPI\`
   - 파일 존재 확인: `KHOPENAPI.OCX`

### 2단계: OCX 파일 수동 등록

#### 2.1 관리자 권한으로 명령 프롬프트 실행
```cmd
# 시작 메뉴에서 "cmd" 검색
# 우클릭 후 "관리자 권한으로 실행"
```

#### 2.2 OCX 파일 등록
```cmd
# 32비트 시스템용
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 64비트 시스템용 (32비트 호환성)
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
```

#### 2.3 성공 메시지 확인
```
DllRegisterServer in C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX succeeded.
```

### 3단계: 의존성 파일 확인

#### 3.1 필요한 DLL 파일들
```cmd
# 다음 파일들이 존재하는지 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\*.dll"
dir "C:\Program Files (x86)\Kiwoom OpenAPI\*.ocx"
```

#### 3.2 누락된 파일 복사
```cmd
# Windows System32에서 필요한 파일 복사
copy "C:\Windows\System32\msvcp140.dll" "C:\Program Files (x86)\Kiwoom OpenAPI\"
copy "C:\Windows\System32\vcruntime140.dll" "C:\Program Files (x86)\Kiwoom OpenAPI\"
```

### 4단계: Visual C++ 재배포 패키지 설치

#### 4.1 Microsoft Visual C++ 재배포 패키지 설치
1. **Microsoft 공식 사이트 방문**
   - https://aka.ms/vs/17/release/vc_redist.x86.exe (32비트)
   - https://aka.ms/vs/17/release/vc_redist.x64.exe (64비트)

2. **관리자 권한으로 설치**
   - 다운로드한 파일을 우클릭
   - "관리자 권한으로 실행" 선택

### 5단계: 레지스트리 정리

#### 5.1 기존 등록 정보 제거
```cmd
# 레지스트리 편집기 실행
regedit

# 다음 경로에서 키움 관련 항목 삭제
HKEY_CLASSES_ROOT\KHOPENAPI
HKEY_CLASSES_ROOT\KHOPENAPI.OCX
```

#### 5.2 새로 등록
```cmd
# OCX 파일 다시 등록
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
```

### 6단계: 시스템 재부팅

#### 6.1 완전 재부팅
```cmd
# 시스템 재부팅
shutdown /r /t 0
```

#### 6.2 재부팅 후 확인
```cmd
# OCX 파일 등록 상태 확인
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
```

## 🧪 테스트 방법

### 1. Python으로 테스트
```python
# test_ocx_registration.py
import sys
import os

try:
    # PyQt5 임포트 테스트
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QAxContainer import QAxWidget
    
    app = QApplication(sys.argv)
    ax_widget = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
    print("✅ OCX 등록 성공!")
    
except Exception as e:
    print(f"❌ OCX 등록 실패: {e}")
```

### 2. 배치 파일로 테스트
```cmd
# test_ocx.bat
@echo off
echo OCX 등록 테스트 중...
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
if %ERRORLEVEL% EQU 0 (
    echo ✅ OCX 등록 성공!
) else (
    echo ❌ OCX 등록 실패!
)
pause
```

## 🔍 문제 진단

### 파일 존재 확인
```cmd
# OCX 파일 존재 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 전체 파일 목록 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\"
```

### 권한 확인
```cmd
# 파일 권한 확인
icacls "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 관리자 권한으로 실행 중인지 확인
whoami /groups | findstr "Administrators"
```

### 레지스트리 확인
```cmd
# 레지스트리에서 등록 정보 확인
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1"
```

## ⚠️ 주의사항

1. **관리자 권한 필수**: 모든 작업은 관리자 권한으로 실행
2. **백업 권장**: 레지스트리 수정 전 백업
3. **안티바이러스**: 일시적으로 비활성화 후 설치
4. **방화벽**: 키움 API 접근 허용
5. **네트워크**: 인터넷 연결 필수

## 🆘 추가 지원

### 문제가 지속되는 경우:
1. **키움증권 고객센터**: 1544-9000
2. **시스템 로그 확인**: 이벤트 뷰어에서 오류 확인
3. **다른 PC에서 테스트**: 동일한 환경에서 재현 여부 확인
4. **가상머신 사용**: 깨끗한 환경에서 테스트

### 대안 방법:
1. **키움 OpenAPI+ 모바일**: 모바일 앱 사용
2. **웹 API**: 키움증권 웹 API 사용
3. **다른 증권사**: 다른 증권사의 API 사용

---

**이 가이드를 단계별로 따라하면 OCX 등록 오류를 해결할 수 있습니다!** 🚀 